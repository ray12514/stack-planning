# Deployment Inputs And Input Ownership v1

This note records two things:

1. who owns each decision in a typical package-manager + install workflow, and
2. the **deployment overlay** (`deployment.yaml`) that carries the
   installer-chosen, site-specific values that must never be auto-derived.

No v1 stack release has been deployed yet. The `deployment.yaml` shape below is
**provisional** — design it from first-system evidence before committing a
`deployment-v1.json` schema, the same way system-external fields are deferred in
`pre_v1_hosting_and_external_inventory_note_v1.md`.

## The core principle: auto vs. explicit

The framework's job is to spare a user the backend grind — not to decide where
their software lives or how it is exposed.

| Auto — the framework's job (from profile facts + defaults policy) | Explicit — the installer/user chooses (profile offers candidates only) |
|---|---|
| Which externals exist → `packages.yaml` content | **Install tree location** |
| Compiler / MPI / GPU provider wiring | **Build stage, source/build caches** |
| CPU target / optimization | **View & module roots** |
| Module file *syntax / format* | **Module exposure mode + layout, `publish_root`** |
| The deterministic workspace | The specs / package-sets; which Spack |

**The install tree is never auto-derived.** `profile.filesystem.install_tree_candidates`
are *candidates* — the profile cannot know where this particular install should
land. The installer chooses. Likewise module exposure is a deliberate choice, not
a silent default.

Where the framework can help on the explicit values: a **fact-based check** —
if the chosen install tree is not writable or is too small per profile facts,
flag it. The framework validates the choice; it never makes it. No Spack runs.

## Input ownership — who, where, when

| Decision | Owner | Where | When (stage) |
|---|---|---|---|
| Which software (specs) | Package manager | `stack.yaml` specs / `package-sets/` | author (3) |
| `kind` / compiler narrowing (optional) | Package manager | `stack.yaml` | author (3) |
| Module exposure **mode** (front_door/direct), namespace | Package manager / stack author | `stack.yaml` `modules.*` | author (3) |
| Which of the profile's compilers/MPI/GPU to build (selection) | Template maintainer; user may override | `defaults.yaml` (`compilers`/`mpi`/`gpu`/`target`) + per-build override | curate/author |
| Default policy (externals posture, buildcache, release) | Template maintainer; user may override | `defaults.yaml` + `stack.yaml` | curate/author |
| System facts (what exists) | System owner / `cluster-inspector` | `profile.yaml` | probe (1) |
| Externals/`packages.yaml`, provider wiring, target, module syntax | **Framework (auto)** | rendered `configs/**` | render (5) |
| **Install tree, build stage, caches, view/module roots, `publish_root`, buildcache destinations** | **Installer** | `deployment.yaml` (or build-time flags) | Stage 0 setup / install |
| Which Spack version (floor/pin) **and where Spack lives** | Template maintainer (floor), package manager (pin), installer (exact + location) | `defaults.spack.floor`, `stack.yaml.spack.version`, `deployment.yaml.spack.root` / `$PATH` | curate/author/install |

In practice the package manager, the installer, and the template maintainer are
often the **same person**. The ownership split is therefore mostly about *which
file* a value belongs in — portable `stack.yaml` intent versus site-specific
`deployment.yaml` paths — not about org boundaries.

## The deployment overlay (`deployment.yaml`)

A per-system overlay holding the installer-chosen, non-portable values. It is
kept **out of** the portable `stack.yaml` so the same stack intent renders on any
system. Provisional shape:

```yaml
# systems/<system>/deployment.yaml — installer-owned; never auto-derived
schema_version: 1
system: example-cray                  # must match profile.system.name

install_tree:
  root: /shared/stack/opt             # REQUIRED — chosen from profile candidates, not derived
  padded_length: 128                  # optional

build_stage:
  default: /scratch/$user/spack-stage
  by_node_type:                       # optional per-node-type overrides
    build: /scratch/$user/stage

caches:
  source: /shared/stack/cache/source
  misc: /shared/stack/cache/misc

roots:
  views: /shared/stack/views
  modules: /shared/stack/modules

modules:
  publish_root: /apps/modulefiles     # MODULEPATH location for published modules; null if already on MODULEPATH

buildcache:
  destinations:
    - { name: payload, url: "file:///shared/stack/buildcache/payload" }

spack:
  root: /opt/spack                    # optional — Spack the build path sources (<root>/share/spack/setup-env.sh); omit to use $PATH (e.g. a site `module load spack`)
```

Where it lives and how it is consumed:

- **Lives** at `systems/<system>/deployment.yaml` in `stack-content`, next to
  `profile.yaml` — but it is *installer-owned* (chosen), where `profile.yaml` is
  *inspector-owned* (observed). Keeping them adjacent keeps the per-system inputs
  together and reviewable.
- **Seeded at Stage 0.** When a site already knows its standard install/cache
  locations, those defaults can be written during stack-directory setup.
- **Consumed by render** to produce `configs/common/config.yaml` (install tree,
  build stage, caches) and the lane view/module roots, and to drive module
  `publish_root`. This is the Phase 7 `config.yaml` render, now sourced from
  `deployment.yaml` rather than guessed.
- **Overridable at build time.** A developer doing an ad-hoc install from their
  home directory can point the install tree elsewhere via build-path flags
  without editing or committing a `deployment.yaml`. Both paths are supported.

`stack-composer` still never runs Spack: it renders the chosen paths into Spack
config or fails fast with a clear error when a required path (the install tree)
is absent.

## Spack root vs. install tree

Two different locations, easily confused:

- **Spack root** — where the Spack *tool* lives on disk (a clone or a site
  module). Pure operator concern; the stack source never names it. Only the
  **build path** needs it, and it finds Spack one of two ways: a site module on
  `$PATH` (`module load spack/<v>`), or an explicit root it sources
  (`<root>/share/spack/setup-env.sh`) — recorded as `deployment.yaml.spack.root`
  or passed as `spack-build --spack-root`. The build path enforces floor + pin
  against that install's `spack --version`.
- **Install tree** — where Spack *installs built packages* (the `install_tree`
  above). A different path, also installer-chosen.

`stack-composer` needs neither — render is Spack-free; Spack location only
matters once a build path starts. See v6 § Three-Layer Version Model and
§ Acquiring And Installing Spack for the floor/pin/root split and the
site-module vs per-version-clone patterns. How `stack tools` locates Spack is
part of its contract (open question in `stack_build_handoff_note_v1.md`).

## Status and open questions

The shape is provisional; confirm during first-system testing, then add
`deployment-v1.json`:

1. Final `deployment.yaml` field set and which keys are required vs. defaulted.
2. Whether `modules.publish_root` moves here permanently (it is currently in
   `stack.yaml` `modules`); the portability split says it should, but the move
   waits for the deployment schema.
3. Whether build-stage and caches need per-node-type granularity in practice.
4. How site defaults seeded at Stage 0 interact with build-time overrides
   (precedence, and how the chosen values are recorded in the release manifest).
5. The fact-based path checks worth running (writable, free space, on a shared
   filesystem visible to compute nodes).
