# Spack 1.2.2 build-orchestration semantics (v1)

| Document control | |
|---|---|
| Date | 2026-08-13 |
| Status | Research note for CSE initial conversion trials |
| Scope | Spack `v1.2.2` only |
| Method | Primary sources only: the official `spack/spack` documentation and source at tag `v1.2.2` |

## Initial Conversion Trials build-stage change assessment

- **Requested change:** replace the pilot's manually entered single build-stage
  path with an ordered Spack fallback list derived from the reviewed build node.
- **Design source:** the profile contract already records per-node-type stage
  candidates, and this note documents Spack 1.2.2 fallback semantics. The
  common runbook owns the trial procedure.
- **Ownership:** Cluster Inspector owns observed candidate writability and mount
  facts. The operator owns the selected build node type and `WORKDIR`. The
  Initial Conversion Trials helper owns the temporary pilot translation into
  `config.yaml`; Stack Composer still does not probe the host.
- **Scope:** required trial hardening. It does not change the production
  `render-static` product into a deployment planner and does not add a new
  production mode.
- **Seam:** preserve `node_types` as provenance in the static-catalog manifest,
  then resolve the ordered list in `create-build-values.py` before invoking the
  existing initializer.
- **Risks:** stale profile facts, `noexec` paths, an unset or relative `WORKDIR`,
  and accidentally merging lower-scope Spack defaults ahead of the reviewed
  list.
- **Decision:** implement directly before v1; fail on an absent node type or
  invalid `WORKDIR`, exclude known unusable candidates, and emit
  `build_stage::` so the rendered list is complete.

## Initial Conversion Trials CPU-target change assessment

- **Requested change:** build one portable CPU architecture per system rather
  than allowing each compiler surface or concretization host to select a
  native target.
- **Design source:** the trial policy already names a portable baseline and the
  profile contract records detected, preferred, and compatible alternate CPU
  targets for each node type.
- **Ownership:** Cluster Inspector owns observed node compatibility. Trial
  policy owns the allowed portable baseline family. The values helper resolves
  one system-wide target. Generated Spack configuration enforces it, and the
  lock verifier checks the resulting concrete DAGs.
- **Scope:** every CPU-only Initial Conversion Trials environment, including
  both GCC and platform-compiler surfaces. GPU work remains out of scope.
- **Seam:** write the resolved target into the values file, constrain every
  source-built root group explicitly, use `packages:all:prefer: target=...` as
  the dependency default, give architecture-specific prebuilt distributions a
  reviewed generic-family target, and reject any other non-external lockfile
  node whose target differs.
- **Risks:** native concretization silently varies with the node that runs it;
  separately resolved compiler surfaces produce incompatible hashes; and a
  target chosen from only one node class may not run on another trial node.
- **Decision:** select the highest target common to all profiled CPU-only
  build/runtime node types, capped at `x86_64_v3`. The ordered candidates are
  `x86_64_v3`, `x86_64_v2`, then `x86_64`. Do not select `x86_64_v4`, `zen*`,
  or another native microarchitecture for these trials. A lower explicit
  override is valid only when every relevant node type reports support.
  Spack 1.2.2 testing showed that an `all` requirement alone is insufficient
  for roots with their own package-specific `require` entries, so the rendered
  root constraints and lock verifier are mandatory parts of this decision.
  It also showed that a generic `miniforge3 target=x86_64` root conflicts with
  `packages:all:require target=x86_64_v3`, while the same root concretizes with
  `packages:all:prefer`; Miniforge is therefore the named generic-target
  exception.

## Conclusions for the pilot

1. `group`/`needs` orders concretization and forces reuse **inside one
   environment**. It is not a cross-environment or cross-process scheduler.
2. A compiler installed by Spack in the shared store is already a compiler
   candidate. It does **not** need to be exposed through a view or rediscovered
   as an external. External compilers do need a `packages.yaml` record with
   their compiler executables and, where needed, module setup.
3. Separate `spack install` processes can share one install tree safely when
   locking is enabled and the filesystem implements the required locking
   semantics. For the same concrete prefix, one process builds while the
   others wait and then skip/reuse the completed installation.
4. `config:build_stage` is a real ordered fallback list. Spack selects the
   first readable/writable existing directory, or the first path it can create,
   and fails only after all candidates fail.
5. `config:build_jobs` is CPU-aware but not memory-aware. With the default new
   installer it is a global job cap across concurrently building packages.
   Memory-per-job policy must be selected outside Spack.
6. A locally editable package recipe belongs in a registered, workspace-owned
   package repository ahead of `builtin`. After changing a recipe, the affected
   environment must be re-concretized and its lockfile reviewed before another
   install attempt.

These conclusions distinguish Spack mechanisms from CSE operating policy.
Spack makes concurrent fan-out technically safe, but a deliberate compiler
checkpoint can still be useful for early failure isolation and handoff review.

## 1. What `group` and `needs` actually coordinate

Spec groups are entries in one environment's `spack.yaml`. For a group with
`needs: [compiler]`, Spack orders the `compiler` group before the dependent
group during **that environment's concretization**, and makes the needed
group's specs mandatory reuse candidates for the dependent group. The official
example is explicitly described as “building and using a compiler in a single
environment”
([environment groups](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L925-L963)).
The implementation reads needed specs from the same `Environment` object's
already-concretized groups and places them in a mandatory reuse filter
([reuse factory](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/environment/environment.py#L2600-L2639));
it topologically orders only the groups declared by that environment's
manifest
([group ordering](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/environment/environment.py#L2693-L2804)).

Therefore:

- `needs` cannot name a group in another `spack.yaml`;
- it does not wait for a different environment or a different process;
- it does not express scheduler placement or install-host ordering;
- eight independent environments require an external driver if CSE wants a
  strict “compiler environment finishes before payload environments begin”
  gate.

Spack has a separate mechanism for combining already concrete environments:
an environment can include other environments' `spack.lock` files. That copies
their concrete information into a combined lock, and changes propagate only
after concretizing the source environment and then the combined environment
([including concrete environments](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L494-L542)).
That is composition of concrete specs, not cross-process execution control.
Unlike `needs`, included-environment specs are subject to the consumer's
`concretizer:reuse` policy rather than being mandatory reuse candidates
([reuse-factory distinction](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/environment/environment.py#L2612-L2645)).

### CSE implication

There are two valid pilot shapes:

- **Ordered checkpoint:** concretize/install the GCC producer first, verify it,
  then concretize the independent payload environments with local-store reuse
  enabled. This is operationally clearest.
- **Concrete-lock fan-out:** concretize the GCC producer, include that producer
  `spack.lock` in each consumer, keep reuse enabled, and constrain the consumer
  toolchain to GCC 12.5.0. After verifying that every consumer selected the
  producer's exact language-provider hash, run the installs concurrently.
  Prefix locking ensures only one process installs that exact GCC prefix.

The second shape does not require the first process to “announce” GCC through
a view. It does require the independent concretizations to select the **same
concrete GCC DAG**. Merely writing `gcc@12.5.0` is not proof of identical hashes
if environment configuration, targets, variants, package-repository commits,
or dependency constraints differ. Including the producer lock only makes the
spec available for reuse; if a consumer sets `reuse: false`, inclusion does not
bind its payload to that compiler. Lockfile comparison of the `c`, `cxx`, and
`fortran` provider hashes is the proof.

## 2. Compiler producers, language providers, and views

In Spack 1.2, `c`, `cxx`, and `fortran` are virtual packages provided by
compiler packages such as `gcc`, `llvm`, and `intel-oneapi-compilers`.
Language dependencies become build dependencies on those compiler packages
([language dependencies](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L2073-L2092)).
Spack says compilers can be supplied in three ways: as externals in
`packages.yaml`, as installations in the current Spack store, or from a build
cache
([compiler sources](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuring_compilers.rst#L12-L22)).

For a Spack-built compiler, the documented workflow is simply:

```console
spack install gcc@14
spack install hdf5~mpi %gcc@14
```

Spack explicitly says the installed compiler is usable “without additional
configuration”
([build your own compiler](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuring_compilers.rst#L264-L279)).
With `concretizer:reuse` enabled, installed packages in the local store are
reuse candidates; reuse can be restricted to the local store and filtered by
spec when desired
([reuse configuration](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/build_settings.rst#L40-L85)).

An environment view is not the compiler registration mechanism. A view links
installed files into a conventional `bin`/`lib`/`include` tree and environment
activation adds its `bin` to `PATH`
([view purpose](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L1055-L1072)).
The official groups example can deliberately create an applications-only view
that excludes the compiler group while the applications still build with that
compiler
([group-filtered view](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L1204-L1238)).

Consequently, a fixed GCC view may still be useful as:

- a stable human-facing `PATH` for manual compiler commands;
- an integration point for a non-Spack build driver that expects compiler
  executables on `PATH`;
- a discovery location if someone intentionally re-registers that compiler as
  an external in a different Spack configuration.

It is not needed for a Spack 1.2.2 DAG to use a GCC package already installed
in the same configured store. Registering that installation again as an
external would also discard the cleaner “Spack-built” provenance.

If the pilot instead records the compiler view as a `packages.yaml` external,
that changes the dependency semantics: the external prefix is assumed to
already exist and Spack does not own installing it as part of the consumer
DAG. In that design the GCC-first checkpoint is mandatory. A view-plus-external
record is therefore an available compatibility seam, not an equivalent way to
get concurrent producer/consumer synchronization.

External CCE, AOCC, Intel, or system GCC is different. External compiler
entries record a prefix and `extra_attributes:compilers` paths keyed by
language; module-backed compilers should also record their required modules
([manual external compiler configuration](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuring_compilers.rst#L131-L159),
[compiler modules](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuring_compilers.rst#L208-L258)).
That external record, not a view alone, tells the concretizer which language
provider exists and tells the build environment how to invoke it.

### Adding AOCC, Intel, or another full compiler surface

The mechanism is already generic: add another compiler provider spec and fan
out the desired serial/MPI/GPU environments for it. The provider may be a
Spack-built compiler package, an installed compiler in the shared store, a
build-cache compiler, or an external compiler entry. The CSE generator should
therefore model a list of compiler surfaces rather than special fields for
only “shared GCC” and “platform compiler.” GCC 12.5.0 can remain the selected
common baseline for the present trial without making that two-compiler shape a
permanent limit.

## 3. Concurrent installs into one shared store

Spack 1.2.2 documents that multiple `spack install` processes can run safely on
one machine or across cluster nodes sharing a filesystem. It acquires an
exclusive lock per install prefix; if another process holds the lock, the
process waits, and if the prefix becomes installed it skips that installation
([multi-process installs](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/installing.rst#L106-L114)).
The installer implementation requeues work that is in progress in another
process, rechecks the resulting state, and marks an already installed package
complete instead of rebuilding it
([lock acquisition and requeue](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/installer.py#L2285-L2342)).

This guarantee has important boundaries:

- It is **per concrete prefix**. Different DAG hashes are different prefixes
  and may build concurrently even when both display as `gcc@12.5.0`.
- `config:locks` must remain `true`. Spack warns that concurrent processes must
  not run when locks are disabled
  ([lock setting](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/config_yaml.rst#L157-L162)).
- The shared filesystem must support the required `flock` semantics. Spack
  calls out local filesystems and recent NFS, notes that some parallel/NFS
  configurations lack support, and warns of database corruption if concurrent
  operation is attempted without locks
  ([filesystem requirements](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/advanced_topics.rst#L91-L124)).
- All processes must resolve the same install tree and database. Sharing only a
  visible directory while using different store configuration is not the
  documented case.
- This conclusion covers the Spack store/database. It does not establish that
  arbitrary external scripts or a separately managed build-cache publisher are
  safe for concurrent writes.

Thus, “whoever starts GCC first builds it and the others wait” is correct only
when every lockfile contains the exact same GCC hash and the shared filesystem
passes the locking prerequisite. A failed GCC build is propagated as failed
dependency state rather than silently being treated as installed; the
installer coordinates failure files as well as prefix locks
([installer concurrency design](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/installer.py#L4-L24)).

## 4. `build_stage` fallback behavior

`config:build_stage` accepts an ordered list. Spack uses the first directory to
which it has write access and fails if none is usable
([build-stage configuration](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/config_yaml.rst#L70-L104)).
The implementation tests existing candidates for read and write access; for a
missing candidate it attempts to create the path, catches an `OSError`, and
continues to the next candidate
([candidate selection](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/stage.py#L139-L155),
[stage-root selection](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/stage.py#L193-L208)).
If the username is not already a path component, Spack appends a per-user
component before selection
([path resolution](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/stage.py#L158-L186)).

Environment variables such as `$WORKDIR` are supported in configuration paths
([config variables](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst#L503-L555)).
The Initial Conversion Trials use the following ordered policy:

```yaml
config:
  build_stage::
  - $tempdir/${USER}/spack-stage
  - /reviewed/node-scratch/${USER}/spack-stage
  - ${WORKDIR}/cse-spack-stage
```

The operator approves the build node type, not one manually typed stage path.
The pilot values helper reads that node type's Cluster Inspector facts, retains
only candidates that were writable on that node and are not known `noexec`
mounts, orders temporary storage before other inspected scratch candidates,
and adds the builder's absolute `WORKDIR` as the last fallback. It namespaces
every candidate by system and trial release. The generated setup script fails
early unless `WORKDIR` exists and is absolute, writable, and searchable. The
variable remains in the rendered path so the same initialized workspace can be
handed to another builder without hard-coding the first operator's personal
directory.

The v1.2.2 implementation expands environment variables and then makes a
remaining relative path absolute relative to its configuration source/current
directory; an unexpanded `$WORKDIR` is not defined as “skip this candidate”
([path substitution](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/util/path.py#L198-L203),
[canonicalization](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/util/path.py#L245-L299)).

Use the `build_stage::` override spelling when the rendered list must be the
complete list. Without `::`, a higher-precedence list is prepended to lower
scope defaults, so the effective list can contain more candidates than the
rendered file shows
([list merge and override](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst#L430-L500)).

Spack's accessibility check is not a performance or capacity policy. It does
not select using free space, free inodes, throughput, node visibility, or
`noexec`; those facts must be validated before rendering or in the build setup.
In particular, the underlying `can_access` test checks read/write access only
([access check](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/llnl/util/filesystem.py#L1398-L1402)).

## 5. Jobs, cores, and memory

With the v1.2.2 default **new installer**, `build_jobs` is the global maximum
number of jobs across all packages, and `concurrent_packages` limits how many
packages a single Spack process builds simultaneously. The shipped default is
`build_jobs: 16`; fewer available CPUs reduce the effective value, while `-j`
overrides it
([shipped defaults](https://github.com/spack/spack/blob/v1.2.2/etc/spack/defaults/base/config.yaml#L155-L171)).
The installer uses a POSIX jobserver so `-j16` bounds the combined build jobs
across concurrent package builds within that Spack process; `-p` separately
bounds active packages
([parallelism](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/installing.rst#L59-L92)).

Absent a command-line override, Spack computes:

```text
min(CPUs available to this process, config:build_jobs)
```

Packages marked non-parallel get one job. A command-line `-j` wins without the
CPU cap
([job calculation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/config.py#L2226-L2256)).
On Linux, “CPUs available” comes from `sched_getaffinity(0)`, which normally
honors Slurm/container CPU restrictions; the fallback is the machine CPU count
([CPU discovery](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/util/cpus.py#L9-L19)).

There is no memory input in this calculation. “Use as many cores as memory
allows” must be a CSE/build-driver rule, for example a conservative cap based
on the scheduler allocation and an operator-selected memory-per-job allowance:

```text
jobs = min(allocated CPUs, floor(allocated memory / memory per job), site cap)
```

That formula is policy, not Spack behavior, and the memory-per-job value varies
materially by package/compiler. The profile should record CPU and memory facts
per node type; the build driver should calculate and print the chosen `-j` and
`-p` for the actual allocation. Because multiple independent Spack processes
each enforce their own jobserver, a multi-process driver must also budget the
sum across processes rather than give every process the full node count.

## 6. Safe local package-repository changes after handoff

Spack package repositories are designed to hold local, proprietary, or
experimental recipes and to override builtin packages. Search order is
configuration order, and the first repository providing an unqualified package
name wins
([repository purpose](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/repositories.rst#L12-L20),
[search order](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/repositories.rst#L364-L403)).
For the CSE handoff, keep a workspace-owned overlay repository in the handed-off
tree and list it before `builtin`. Do not patch the Spack checkout, an automatic
cache clone, or `.spack-env/repos`.

`.spack-env/repos` is generated provenance: environment writes copy the package
files for newly concretized specs there, and the top-level `--use-env-repo`
option explicitly selects that snapshot
([environment repository update](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/environment/environment.py#L2487-L2552),
[`--use-env-repo`](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/main.py#L470-L491)).
It is not the editable source repository.

The safe adjustment loop is:

1. Activate/select the affected independent environment and source the
   workspace build setup.
2. Edit the version-controlled overlay recipe, for example
   `package-repos/cse/spack_repo/cse/packages/cce/package.py`.
3. Run `spack repo list` and `spack spec -N <affected-root>` to verify that the
   CSE namespace wins before `builtin`. `spack repo list` reports the resolved
   repository path, namespace, and usability
   ([repository inspection](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/repositories.rst#L420-L455)).
4. Re-concretize every environment whose DAG contains the changed package.
   `spack concretize` preserves already concrete roots; `spack concretize -f`
   forces all roots in that environment to be solved again
   ([forced reconcretization](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L301-L324)).
5. Review the `spack.lock` diff, including compiler/provider identities and DAG
   hashes, before resuming `spack install`.
6. Commit/record the overlay recipe change and hand off the updated overlay and
   lockfile together.

Keep the experimental concretization cache disabled while iterating on local
recipes. The v1.2 release changelog says it is off by default and records a bug
where cached solve results may not reflect `package_hash` changes
([concretization-cache warning](https://github.com/spack/spack/blob/v1.2.2/CHANGELOG.md#L441-L450)).

A recipe change can change the package hash and therefore the DAG/install
prefix; Spack includes the canonical `package.py` recipe hash in package hashes
([hash inputs](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L1805-L1819)).
Reconcretization is therefore part of the update, not an optional recovery
step.

For Git-backed package repositories, pin a commit for a reproducible handoff.
`spack repo update` makes the checkout match a configured commit/tag, or pulls
the latest branch state when branch-pinned/unpinned
([repo pin/update semantics](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/repositories.rst#L165-L182)).
Path-based overlay repositories are edited directly and are not updated by
`spack repo update`.

## Recommended pilot posture

- Keep GCC 12.5.0 as the current common compiler producer, but represent
  compiler surfaces as a list so AOCC, Intel, another CCE, or a newer GCC can
  be added without changing the workflow shape.
- Keep the GCC producer as an explicit first checkpoint for the initial trials.
  This is an operational choice, not a requirement imposed by Spack's store.
- For independent consumers, include the concrete producer lock, keep a
  narrowly controlled reuse policy enabled, and fail validation unless each
  consumer's language-provider hash equals the producer GCC hash.
- Do not make a compiler view a correctness dependency. Verify compiler reuse
  by the GCC DAG hash in every lockfile and by `spack spec -I`/`spack find`, not
  by whether `gcc` appears on ambient `PATH`.
- Permit concurrent payload installs only after lockfile comparison proves the
  intended shared compiler hashes and the shared install filesystem's locks
  have been validated.
- Render an ordered build-stage list for one reviewed build node type: writable
  temporary storage first, other inspected writable scratch candidates second,
  and the absolute operator `WORKDIR` last. Exclude known `noexec` candidates,
  namespace every root by user/system/release, and use setup-time checks for
  capacity and executable mounts.
- Record node-type CPU and memory facts, but let the build driver choose the
  allocation-aware `-j`/`-p` values. Spack will not derive a safe memory cap.
- Ship the editable package-repository overlay inside the workspace and make
  “edit recipe -> force affected reconcretization -> review lock -> retry” part
  of the coworker handoff.
