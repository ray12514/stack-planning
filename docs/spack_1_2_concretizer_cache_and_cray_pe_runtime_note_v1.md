# Spack 1.2 Concretizer Cache and Cray PE Runtime Note v1

Date: 2026-08-25
Status: Current technical note for the Initial Conversion Trials

## 1. Purpose

This note answers two implementation questions for the CSE Spack 1.2.2
workspaces:

1. what Spack caches during concretization, when that cache is reused, and
   whether the current CSE launcher preserves it; and
2. what must be present for an external Cray MPICH toolchain in a clean build
   shell, including the roles of modules, wrappers, `PE_ENV`, libfabric, PMI,
   and the selected CPE release.

The note separates upstream facts, CSE-specific inferences, and CSE policy. The
builder-partitioned shared-root cache policy described below is implemented in
the generated Initial Conversion Trial workspace controls.

## 2. Executive answer

Spack 1.2.2 enables its concretization cache by default. It stores the complete
solver result for an exact ASP solver input. A repeated identical root solve can
skip Clingo, but a slightly different solve does not reuse part of the old
solver state. With `unify: false`, roots are solved separately, so an unchanged
root can hit the cache even when a different root needs a new solve.

The CSE configuration places `misc_cache` in a persistent builder-named
partition below the shared restricted misc-cache root. It is reused by that
builder's login/compute contexts and surfaces. The launcher recursively assigns
the partition to the CSE group before and after Spack because entries created
through `mkstemp` can initially have mode `0600`. Different builders retain
different mutable index partitions.

For Cray PE, loading a `PrgEnv-*` or `cray-mpich` module is not intrinsically
required by Spack when an exact compiler-flavor prefix, the Cray MPICH wrappers,
and every runtime dependency are modeled explicitly. HPE's Spack guidance shows
this driverless form. The current renderer carries a selected external
libfabric prefix into the Cray MPICH environment and records the selected Cray
PMI external. It does not yet prove that those independently selected runtime
facts form the exact compiler/MPI/CPE tuple validated by the site. It is
therefore not yet safe for CSE to remove the verified Cray MPI runtime module
chain. Matching a libfabric SONAME is not sufficient evidence for that binding.

## 3. Concretization cache

### 3.1 Upstream facts

Spack 1.2.2 defines `concretizer:concretization_cache:enable: true` in its
defaults. The upstream comment states that the cache is keyed by the solver
input hash and that a hit still runs setup but skips solving. See the
[Spack 1.2.2 concretizer defaults](https://github.com/spack/spack/blob/v1.2.2/etc/spack/defaults/base/concretizer.yaml)
and the [Spack 1.2.2 release](https://github.com/spack/spack/releases/tag/v1.2.2).

The implementation stores a gzip-compressed JSON representation of the solver
`Result` and solver statistics. Its key is derived from:

- the complete generated ASP problem, sorted and stripped of comments and
  empty lines; and
- the contents of the Clingo control files used for that solve.

The default location is:

```text
<config:misc_cache>/concretization/v1
```

An explicit `concretizer:concretization_cache:url` overrides that location. The
default entry limit is 1,000. When pruning is needed, Spack uses file modification
time as an LRU indicator and removes the oldest half of the configured limit.
These behaviors are implemented in
[`ConcretizationCache`](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/solver/asp.py).

This is an exact-result cache, not an incremental solver cache. A cache hit
restores the answer for the complete problem. Spack does not combine fragments
of prior answers to solve a changed problem.

Spack performs package-dependent post-processing on both fresh and cached
answers. This includes reinjecting patches, resolving external paths, assigning
the current package hashes, and finalizing DAG hashes. The upstream cache tests
specifically verify patch reinjection after a cache hit. See
[`post_process_concretization_result`](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/solver/asp.py)
and the
[Spack concretization cache tests](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/test/concretization/core.py).

When `unify: false`, Spack sends the roots through `concretize_separately`.
Each unresolved root is an independent solver problem. On Linux, Spack may
solve those roots in parallel up to the configured job count. See
[`concretize_separately`](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/concretize.py).

Concretization may still appear to build software before the first solve. If
the Python environment cannot import Clingo, Spack bootstraps the solver and its
dependencies first. The concretization cache does not replace or cache that
bootstrap installation.

### 3.2 What causes hits and misses

| Change | Expected cache effect | Reason |
|---|---|---|
| Repeat the same root with the same repositories, requirements, externals, compilers, target policy, and reuse candidates | Hit | The complete ASP problem and control files are identical. |
| Change a version, variant, dependency rule, provider rule, compiler, external, target constraint, package requirement, or eligible reuse input | Miss when the change alters emitted solver facts | The generated ASP problem changes. |
| Change Spack's solver control files | Miss | Control-file contents are part of the key. |
| Change package build implementation without changing solver facts | The solver result may hit | Build method bodies are not themselves the solver input. Current package hashes are recomputed after the hit, so final DAG hashes can still change. |
| Change a package patch | A prior solver result may hit | Patches are reinjected during post-processing and package/DAG hashes are finalized from the current package state. |
| Change a non-solver setting such as build stage or source-cache location | Normally no effect | It does not change the solver problem. |
| Change only one root under `unify: false` | Changed root misses; unchanged roots may hit | Roots are solved as independent problems. |

Recipe, repository, and configuration changes therefore do not have one blanket
invalidation rule. The deciding question is whether the change alters the ASP
problem or the solver control files. Post-processing protects package and DAG
identity from being frozen at the time the solver answer was cached.

`spack concretize --fresh` disables reuse of already installed or build-cache
specs for the solve. It does not disable the concretization result cache. In the
CSE command, `-j 1` serializes separate root solves for predictable output; it
does not turn off cache lookup.

### 3.3 CSE-specific facts and inference

The Initial Conversion Trials workspace renders:

```yaml
concretizer:
  unify: false
  reuse: true
```

and renders `config:misc_cache` from a prepared-shell variable:

```text
SPACK_MISC_CACHE_PATH=<restricted-root>/cache/misc/<builder>
```

See the current
[concretizer template](../../stack-content/pilots/cse-pilot/templates/configs/common/concretizer.yaml.j2),
[config template](../../stack-content/pilots/cse-pilot/templates/configs/common/config.yaml.j2),
and
[build-values generator](../../stack-content/pilots/cse-pilot/scripts/create-build-values.py).

The generated `cse-build` launcher separately sets:

```text
SPACK_USER_CACHE_PATH=<per-user-state>/cache/<login-or-compute>/<surface>
SPACK_MISC_CACHE_PATH=<restricted-root>/cache/misc/<builder>
```

That variable isolates ordinary per-user cache data by node context and surface,
while `SPACK_MISC_CACHE_PATH` keeps the concretization and provider indexes
persistent across those contexts and surfaces for one builder. The generated
permission helper recursively restores CSE group ownership and access before
and after Spack. See the
[CSE build launcher](../../stack-content/pilots/cse-pilot/templates/cse-build.j2).

The resulting behavior is:

- workspace control refresh does not remove the concretization cache;
- changing between login and compute contexts does not remove it;
- changing surfaces does not remove it;
- changing builders selects a different cache partition;
- removing and regenerating a lockfile can reuse an exact prior solver result;
  and
- an existing lockfile avoids a new solve altogether unless the environment is
  explicitly reconcretized.

This partition-and-normalize design fixes a multi-user limitation in the
earlier workspace configuration. Spack writes each cache entry using Python's
`tempfile.mkstemp` and atomically renames it into place. `mkstemp` normally
creates a `0600` file. A group-writable parent alone is therefore insufficient.
The launcher repairs files owned by the active builder recursively, and the
builder suffix prevents a second user from replacing that same live index.

### 3.4 CSE recommendation

Use one persistent concretization cache partition per builder, reused by that
builder's login and compute contexts and by the surfaces that should reuse
identical solves. Keep it outside generated workspaces but below the
deployment-owned shared restricted cache root. The generated launcher uses:

```text
<restricted-root>/cache/misc/${USER}/concretization/v1
```

The exact parent directory follows the approved CSE permissions policy. The
active builder owns its entries, the CSE group can traverse/read/write them,
the path persists, and both node contexts can reach it. Directories are `2770`
and ordinary files are `0660` on the target Linux systems after normalization.

Continue sharing the immutable source cache and the Spack install tree under
their existing group and locking rules. The recursive permission step makes
cache evidence available to the CSE group; it does not make two builders use
one live mutable solver index. Cross-builder solver-result reuse would require
a separate publication/locking design and validation against pinned Spack.

For timing comparisons, distinguish these cases:

1. existing lockfile: no solve;
2. no lockfile plus exact cache hit: solver setup, but no Clingo solve;
3. changed solver problem: full solve;
4. missing Clingo bootstrap: bootstrap work before any of the above solves.

## 4. External Cray MPICH and Cray PE state

### 4.1 Upstream facts: two valid usage models

HPE documents two different operating models.

The normal CPE module workflow loads the `cray-mpich` module before compiling
and linking. HPE also documents the PrgEnv modules as meta-modules. For example,
`PrgEnv-cray` sets `PE_ENV=CRAY` and loads `craype`, `cray-mpich`, and LibSci.
See the
[HPE Cray MPI introduction](https://cpe.ext.hpe.com/docs/latest/mpt/mpich/intro_mpi.html)
and the
[HPE CPE General User Guide](https://cpe.ext.hpe.com/docs/latest/getting_started/CPE-General-User-Guide-CSM.html).

HPE's Spack-specific guidance recommends a driverless configuration. Its
examples register CCE and GCC by direct compiler paths with `modules: []`, and
register Cray MPICH as a non-buildable external at its exact compiler-flavor
prefix. The Cray MPICH example also uses `+wrappers`. See
[HPE's Using Spack with CPE documentation](https://cpe.ext.hpe.com/docs/latest/craype/spack.html).

These models are not contradictory. A module is one way to establish compiler,
wrapper, and runtime state. A module-less external is valid only when that state
is represented by the selected prefix, wrapper executables, dependencies, and
runtime environment instead.

The pinned Spack package supports the driverless model. The 2026.06 Cray MPICH
recipe is external-only, depends on `cray-pmi` and `libfabric`, supports a
`+wrappers` variant, and uses wrapper paths for dependent builds. It can discover
a prefix from a module, but a fully specified external prefix does not require
module discovery. See the official
[Cray MPICH package recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/cray_mpich/package.py)
and
[Cray PMI package recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/cray_pmi/package.py).

### 4.2 `PE_ENV` and compiler selection

`PE_ENV` is not merely an MPI location. It marks the selected Cray programming
environment. The CSE trials already demonstrated that an ambient
`PE_ENV=CRAY` can make a GCC build select CCE-specific flags. The generated
launcher therefore unloads reviewed ambient modules and unsets `PE_ENV` before
Spack activates the selected external chain. See
[module-state preparation](../../stack-content/pilots/cse-pilot/templates/env/prepare-module-state.sh.j2)
and finding ICT-006 in
[initial conversion trial build findings](initial_conversion_trials_build_findings_v1.md).

The safe interpretation is lane-specific:

- the shared CSE GCC lane must not use an ambient or umbrella `PrgEnv-*` module
  to choose its compiler; and
- the current CCE lane should retain its exact, reviewed PrgEnv/CCE chain until
  a direct-path CCE configuration passes the same compile, link, and runtime
  tests.

The first rule prevents CCE state from leaking into GCC builds. The second rule
preserves the CCE configuration that is currently understood and testable. HPE's
driverless model provides a future simplification path, but it is not evidence
that the current CSE CCE chain can be removed without validation.

### 4.3 Cray MPICH runtime closure

An exact Cray MPICH prefix is compiler-flavor-specific, for example an
`ofi/gnu/<compiler-version>` directory. The version at the end identifies the
compiler flavor represented by that product subtree; it is not a universal
statement that only that compiler release can use the MPI installation.

The prefix and MPI wrappers are necessary, but the runtime closure also matters.
Depending on the CPE release and site configuration, that closure includes:

- the matching Cray PMI/PALS components;
- the matching libfabric and provider, including the Slingshot `cxi` provider;
- optional XPMEM and huge-page link state used by the wrappers; and
- the runtime library search policy selected by `CRAY_LD_LIBRARY_PATH`,
  `PE_LD_LIBRARY_PATH`, embedded RPATHs, or an equivalent explicit mechanism.

HPE documents wrapper handling for MPI compile/link and optional XPMEM and
huge-page flags. HPE also warns that swapping MPI versions does not necessarily
switch all runtime libraries through `ld.so.cache`; the corresponding Cray
library path must be selected. See the
[Cray MPI wrapper documentation](https://cpe.ext.hpe.com/docs/latest/mpt/mpich/intro_mpi.html)
and the
[CPE runtime-library guidance](https://cpe.ext.hpe.com/docs/latest/getting_started/CPE-General-User-Guide-CSM.html).

For Cray MPICH 9.1.0, HPE's release notes describe libfabric ABI and API minimums
and list CPE component prerequisites. They also document runtime failures caused
by selecting the wrong PMI through runtime paths. See the
[HPE CPE release notes](https://cpe.ext.hpe.com/docs/latest/release_notes/sles_15_6_release_notes.html).

libfabric release compatibility and its ABI numbering are defined separately
from the libfabric release number. See the official
[libfabric API manual](https://ofiwg.github.io/libfabric/v1.20.2/man/fabric.7.html).
Even when two installations expose the same shared-library SONAME, that alone
does not prove that the selected provider plugins, PMI/PALS interaction, CPE
packaging, or launcher behavior matches the Cray MPICH installation. SONAME
compatibility is one necessary library-loader check, not a complete CPE
compatibility proof.

### 4.4 CSE-specific inference: current renderer gap

The current renderer's `selected_platform_runtime_userspace` groups observed
runtime entries by package name and selects the newest eligible Cray-prefixed
entry. The rendered Cray MPICH scope then carries the selected external
libfabric prefix through `LD_LIBRARY_PATH`, and the platform scope records the
selected Cray PMI external. Those are implemented runtime-closure controls,
but the selections are still independent. They are not bound to the exact Cray
MPICH flavor, compiler subtree, or CPE release. See
[runtime selection](../../stack-composer/src/stack_composer/render/fabric.py)
and its use in
[scope rendering](../../stack-composer/src/stack_composer/render/scopes.py).

This is a real multi-CPE gap. A profile containing multiple libfabric or other
runtime installations can produce a plausible newest entry that is not the
runtime delivered and validated with the selected Cray MPICH external. The
renderer must eventually select a reviewed component tuple, not independently
select the newest version of each runtime package.

### 4.5 CSE recommendation: safe minimum policy

For the Initial Conversion Trials:

1. Start each build process from the generated clean module-state preparation.
   Do not inherit a login-node `PrgEnv-*`, `PE_ENV`, MPI wrapper, or library-path
   selection.
2. For the shared GCC lane, select the CSE-built GCC directly. Do not use a
   `PrgEnv-*` meta-module as the compiler selector.
3. Select the exact Cray MPICH compiler-flavor prefix and keep `+wrappers`.
4. Retain the explicit, verified Cray MPI/runtime module chain for the shared
   GCC lane until the equivalent prefix-only runtime closure has passed the
   validation gates below. The chain may include `cray-mpich`, network/libfabric,
   PMI/PALS, XPMEM, and huge-page components as required by the system. This is
   not a request to load `PrgEnv-gnu` around the GCC payload build.
5. For the CCE lane, retain the exact reviewed PrgEnv/CCE/Cray MPICH chain.
6. Record and select Cray MPICH, compiler flavor, CPE release, libfabric/provider,
   PMI/PALS, and optional runtime helpers as one compatibility tuple.
7. Do not approve a tuple from matching version text, a prefix naming pattern,
   or a libfabric SONAME alone.

A prefix-only Cray MPICH external can replace the runtime module chain only
after it passes all of these gates in a clean shell:

- `mpicc`, `mpicxx`, and `mpifort` resolve from the intended prefix and report
  the intended underlying compiler and link flags;
- C, C++, Fortran `use mpi`, and Fortran `use mpi_f08` programs compile and
  link;
- `readelf`/`ldd` inspection resolves `libmpich`, libfabric, PMI, and provider
  libraries from the intended CPE tuple, with no accidental `ld.so.cache`
  fallback to a different release;
- `fi_info -p cxi` or the site-equivalent provider check succeeds where the CXI
  provider is required;
- single-rank, multi-rank, and multi-node jobs run inside an actual scheduler
  allocation; and
- representative collectives, thread support, and the site's required
  XPMEM/huge-page behavior are exercised on compute nodes.

Passing only concretization or link tests is insufficient. The approval record
must include the exact component versions, prefixes, modules or explicit
environment, scheduler context, and runtime evidence.

## 5. Decisions for the current work

- Preserve solver caching with the implemented persistent builder partition
  below the shared restricted `misc_cache`; it spans login and compute contexts
  and compiler surfaces and is recursively CSE-group-accessible.
- Treat `unify: false` cache reuse as exact per-root answer reuse, not partial or
  incremental solving.
- Keep the shared GCC build free of `PrgEnv-*` compiler selection.
- Do not remove the current Cray MPI/runtime module chain until a complete,
  exact CPE runtime tuple can be rendered and passes clean-shell allocated-node
  validation.
- Correct the renderer's newest-runtime selection before claiming multi-CPE
  support.
