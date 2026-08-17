# Stack Build Handoff Note v1

This note records the pre-v1 decision for where `stack-composer` stops and how
the build half is handed off:

1. `stack-composer` renders a Spack workspace **tree**; the per-lane `spack.yaml`
   environments plus the `configs/**` scopes they include are the handoff.
2. Build and concretize are a **co-equal downstream choice**: `spacktools`
   (a separate build/concretize tool), the in-house `spack-build` script,
   Ansible, or bare Spack, not `stack-composer`'s job.
3. The source content render consumes lives in a hosted **stack-content**
   directory; see `pre_v1_hosting_and_external_inventory_note_v1.md`.

No v1 stack release has been deployed yet. If the current shape is wrong, change
it directly before v1 rather than preserving unused alpha behavior.

## Decision: Stack Composer is a spec/workspace generator

`stack-composer` validates inputs, resolves stack intent against profile facts
and the site defaults (defaults.yaml), and renders normal Spack input. It is **not** a
package manager, a concretizer, or a build orchestrator. It must stay
adoptable: a site should be able to take its rendered output and build with
whatever tool it already trusts.

This complements `stack_generation_structure_v1.md`, which defines the current
declarative render model. This note governs the *downstream* build seam and the
*upstream* source directory.

Render is one mechanical
seam between source-of-truth inputs and a runnable Spack workspace. The build is
a separate, swappable step.

## The handoff is a workspace tree, not a single file

`stack-composer render` writes a tree and **places files, it does not flatten**:

```text
<shared-fs-or-render-dir>/<system>/<stack>/<release>/
  configs/
    common/            # config.yaml, concretizer.yaml, packages.yaml, mirrors.yaml, modules.yaml, ...
    os/<os>/
    target/<target>/
    vendor/<vendor>/
    mpi/<provider>/
    gpu/<toolkit>/
  environments/
    <compiler>/<lane>/spack.yaml   # the "spec" Spack builds
  release-manifest.yaml
```

Each lane `spack.yaml` references its Spack component yamls through one
`include::` list. In the default delivery mode those are **relative** paths:

```yaml
spack:
  include::
    - ../../../configs/common
    - ../../../configs/mpi/cray-mpich
    - ../../../configs/target/zen3
  specs:
    - hdf5@1.14.6+mpi+fortran %cce1701_craympich8129
```

Contract consequence: a lone `spack.yaml` is **not** self-contained. The build
consumer must root the **whole tree** where Spack can read the included scopes.
The `include::` list, not ambient `~/.spack`, site, or system scopes, is the
production isolation boundary, so the tree must travel intact.

The build shell also sets `SPACK_DISABLE_LOCAL_CONFIG=true`. In Spack 1.2.2
that disables user and system configuration; `include::` supplies the stronger
environment boundary that also overrides checkout-local site policy. The build
path verifies the result with `spack config scopes -vp` and
`spack -e <environment> config scopes -vp`; an unexpected active user, system,
or site scope is a failed preflight, not an informational warning.

The CSE Initial Conversion Trials initializer applies the same rule to a
workspace assembled from `render-static`. It snapshots the static catalog tree
under `catalog/` and emits relative paths from each environment to
`catalog/scopes/...` and `configs/...`. The source catalog path remains in the
workspace manifest as provenance, but it is not a runtime dependency of the
initialized build handoff. For this temporary initializer only, the static
manifest also preserves the profile's node-type stage facts so a reviewed build
node choice can become an ordered `build_stage::` list without probing the host
or manually retyping scratch paths.

The initializer's generated `cse-build` command also prevents an ambient
selected provider module from crossing the handoff boundary. Before Spack is
activated, the command unloads any exact external compiler or MPI module named
by the workspace when it is already present in `LOADEDMODULES`. This is scoped
to the command process, preserves unrelated site/startup modules, and lets
Spack 1.2.2 perform the recorded module activation itself. It does not change
the parent login shell.

Before that workspace exists, the CSE operator uses a separate operator-local
session entry point under
`$HOME/STACK_TESTING/operator-sessions/<system>/<trial>/activate.sh`. It records
the exact system/catalog/trial tuple plus operator-selected roots, Spack mode,
and bootstrap Python, then derives the preparation paths and functions used by
the runbook. Sourcing it restores state only; it does not update repositories,
rebuild tools, probe a host, render a catalog, or initialize a workspace. It is
not part of the rendered handoff and is not required by the receiving builder.

That temporary CSE workspace also renders a downstream `cse-build` entry point
at its root. It is part of the handed-off workspace, not a new Stack Composer
production mode. It reads the already rendered system, release, toolchain,
path, environment, and Spack-runtime values; creates per-builder mutable state;
and invokes bare Spack for status, missing-lock concretization, verification,
fetch, or sequential installation. Its default action creates or reattaches a
tmux session for the system and release. `shell` provides the same prepared
shell without tmux, and the default falls back to it when tmux is unavailable.
The receiving builder supplies no replacement render inputs.

The default installation remains sequential. After all eight lockfiles pass
verification and the real shared install tree passes a cross-node prefix-lock
test, one active builder may split the work across two nodes: the shared GCC
surface with `cse-build install --surface shared`, and the selected platform
compiler surface with `cse-build install --surface platform`. Each surface is
still processed sequentially. Both commands use the same locked workspace,
store, and database; their view and module roots are disjoint. Do not run two
commands for the same surface. The surface selector does not weaken the global
eight-lock verification gate.

The generated lock verifier is invoked through `spack python`, so it must remain
compatible with the oldest host Python supported by the pinned Spack runtime.
For the current trials that includes Python 3.6 on Raider. Generator or operator
Python features newer than that floor must not be used in the generated
verifier.

For the CPU-only trials, the handoff also owns one explicit portable CPU target
for the entire initialized workspace. The values helper intersects compatible
CPU targets from all profiled build/runtime node types, including GPU-bearing
nodes, and caps selection at `x86_64_v3`. Compiler, Foundation, Core, and
build-tool producers carry explicit surface bindings. At the MPI and payload
boundary, surface language-provider preferences and `packages:all:prefer`
select the compiler and target without propagating blanket root constraints
into machine-owned dependency externals such as Slurm or UCX. The lock
verifier proves the resulting bindings. Architecture-specific prebuilt
distributions are explicit exceptions: Miniforge is constrained to the
generic `x86_64` family target and the lock verifier permits only that named
difference. Build-stage or build-node changes are operational and do not
select another architecture.

## Co-equal build paths

The render step ends at the workspace. The build half (concretize, fetch,
install, smoke/verify, and optionally buildcache push) has four supported
paths. None is "the default"; a site picks one.

| Path | Use when | Owns |
|---|---|---|
| `spacktools` | A site already runs the coworker's build/concretize tool. | Concretize, install, cache, verify, from the rendered tree. |
| `spack-build` | Local / single-machine builds; the in-house reference script shipped with `stack-composer`. | Per-lane Spack invocation, reports, version-floor check. |
| Ansible | Multi-host production clusters. | Per-host orchestration; may call `spack-build` or replicate its loop. |
| Bare Spack | Manual fallback, debugging; always available with no helper installed. | The operator runs `spack concretize`/`install` by hand. |

`stack-composer` itself never calls Spack and never reads host state during
render. Each build path owns *how* Spack is invoked. Do not rename `spack-build`;
it is the descriptive name for the Spack-driving helper.

## Build-time locations

A build cannot run until Spack knows the install tree, caches, build stage, and
view/module roots. These are **deployment-owned**, not facts. The handoff
supports **both** mechanisms, and they compose:

- **From the deployment overlay**: the installer's chosen roots in
  `systems/<system>/deployment.yaml` are rendered into
  `configs/common/config.yaml`. They are *chosen*, never auto-derived from the
  profile (which only offers install-tree candidates). See
  `deployment_inputs_and_ownership_v1.md`.
- **Build-time override**: the build path may supply or override
  install/view/module/cache roots when it invokes Spack, without re-rendering.

Inline environment config and the include order still apply: a build-time
override wins over a rendered scope when both set the same key.

## Pinned Spack tool runtime

The CSE managed build path uses one exact Spack runtime identity: source,
version/tag, and commit. Each builder may source either an
installer-provisioned shared checkout or a builder-local checkout through
`$SPACK_ROOT/share/spack/setup-env.sh`. The root paths may differ. Their
verified runtime identities may not.

A new Spack version receives a sibling directory and is reviewed as a
release/DAG-significant change. Moving between identity-equivalent shared and
local roots is an operational handoff and does not change the concrete DAG.

The Spack tool root is not part of the rendered workspace and is not the Spack
package install tree. It contains no build workspace, stage, source/misc cache,
buildcache, installed package prefix, view, or generated module tree.

The shared checkout is read-only to builders. A local checkout is
builder-owned but remains effectively immutable during the release. The build
path verifies the expected tag/commit and clean Git state before use. It does
not run `spack isolate`, modify `$SPACK_ROOT/etc/spack`, pull, or switch
branches. Mutable state is separated:

- `SPACK_USER_CACHE_PATH` is absolute and unique to the builder;
- `SPACK_GNUPGHOME` is a private per-builder or site-approved keyring outside
  the checkout;
- `PYTHONDONTWRITEBYTECODE=1` prevents Python bytecode caches in the checkout;
- build stages are per-user or node-local; and
- installed package prefixes and their database/locks live in the shared
  restricted package install tree.

The two builders may target that same restricted package install tree. Spack
locking coordinates identical concrete prefixes only when locking remains
enabled and the shared filesystem provides working lock semantics. CSE
setgid/group/ACL policy controls ownership and access; it is independent of
configuration isolation.

## Config delivery modes

How the build consumer reads the config scopes is a **user choice**:

| Mode | `include::` targets | Sync needed | Notes |
|---|---|---|---|
| A: synced tree | Relative local paths (`../../../configs/...`) | Yes: tree on the shared filesystem | Default. Tree must stay intact. |
| B: GitLab-direct | Remote GitLab URLs | No local sync | Spack reads the config yaml directly from GitLab. |

Mode B requires a Spack release that supports URL/remote config includes.
**Validate the exact remote-include syntax against the pinned Spack floor**
(current floor: 1.1.1 or newer) before committing it to a template set. Do not
assume the syntax from this note; prove it with the deployed Spack first.

Both modes deliver the same logical workspace; only the include targets and the
sync requirement differ. The chosen mode is a render option / template-set
default setting, not a fork in the model.

## Stack-content directory (the upstream source)

Render consumes a hosted **stack-content** directory, the human-authored source
of truth, distinct from the three tool repos:

```text
stack-content/
  systems/<system>/profile.yaml                 # per-system observed facts
  stacks/<stack>/stack.yaml                       # package intent
  package-sets/*.yaml                             # curated Spack spec sets
  package-repos/<name>/                           # optional package repositories
  templates/<set>/
    defaults.yaml                                  # site policy (selection + conventions)
    configs/                                       # Spack component yamls (.j2)
    environments/
```

It is a new (4th) GitLab repo in the same group as `cluster-inspector`,
`stack-composer`, and `stack-planning`, **synced onto each target's shared
filesystem** where render and build run. See
`pre_v1_hosting_and_external_inventory_note_v1.md` for the repository-layout
recommendation. There may be more than one stack-content repo (per team or
per stack family); the pattern is the same. For how render is driven across
systems and when to re-render, see `stack_generation_orchestration_note_v1.md`.

## spacktools integration boundary

| Concern | Owner |
|---|---|
| Validate inputs, resolve intent, render the workspace tree | `stack-composer` |
| Choose install tree / caches / view & module roots | **Installer** via `deployment.yaml` (or build-time flags); profile offers candidates only, never auto |
| Provision the shared Spack tool root | **Installer/site owner or authorized CSE builder**; consumers verify and source it read-only |
| Provision a builder-local Spack tool root | **Builder**; exact approved identity, clean and unchanged during the release |
| Provide per-builder Spack cache/keyring paths | **Build path/operator**; never inside the shared tool root or package tree |
| Concretize, fetch, install, smoke/verify | `spacktools` (or `spack-build` / Ansible / bare Spack) |
| Buildcache push | The build path, per stack policy |

`spacktools` is an external peer. `stack-planning` owns the rendered-workspace
contract it consumes; it does not own `spacktools`' internals.

## Open questions

Confirm with first-system testing and bring evidence back here:

1. Does `spacktools` consume the **whole tree** intact (relative `include::`),
   or want absolute include paths, a flattened single `spack.yaml`, or a
   different root?
2. Does it honor the rendered `config.yaml` roots, or supply its own
   install/view/module/cache roots at build time?
3. Does it fetch stack-content by **cloning GitLab** or by reading the
   **shared-FS** synced copy?
4. Who owns **concretizer policy** (`unify`/`reuse`) and **Spack version-floor**
   enforcement: `spacktools` or us?
5. Does `spacktools` also cover **multi-host** orchestration (overlap with
   Ansible), or single-host build only?
6. Who owns **buildcache push** destinations?
7. Does `spacktools` run a Spack that supports remote/URL `include::` (config
   delivery mode B), or only local workspace trees?

## Definition of done for the handoff

The handoff is v1-ready when:

- the rendered workspace tree builds under at least `spacktools` and
  `spack-build` from the same inputs;
- the install tree, caches, and view/module roots are resolvable either from a
  rendered `config.yaml` or a build-time override, with a clear error when
  neither supplies them;
- the selected shared or local Spack tool root matches the approved
  version/tag/commit, has a clean checkout, and receives no mutable builder
  state;
- the CSE trial workspace entry point can resume from zero, partial, or complete
  lockfile checkpoints without requiring the receiving builder to reconstruct
  render values;
- global and per-environment scope evidence proves that no unexpected user,
  system, or site policy affects the build;
- both config delivery modes (synced tree and GitLab-direct) are validated
  against the pinned Spack release;
- a package manager can render and hand off without learning a `stack-composer`
  build language: they author normal Spack specs and pick a build path.
