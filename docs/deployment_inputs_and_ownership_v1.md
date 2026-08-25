# Deployment Inputs And Input Ownership v1

This note records two things:

1. who owns each decision in a typical package-manager + install workflow, and
2. the **deployment overlay** (`deployment.yaml`) that carries the
   installer-chosen, site-specific values that must never be auto-derived.

No v1 stack release has been deployed yet. The `deployment.yaml` shape below is
the current pre-v1 schema in `schemas/deployment-v1.json`. Because this is
pre-v1, change it directly when first-system evidence shows the shape is wrong;
do not add compatibility paths for unused alpha shapes.

## The core principle: auto vs. explicit

The framework's job is to spare a user the backend grind, not to decide where
their software lives or how it is exposed.

| Auto: the framework's job (from profile facts + defaults policy) | Explicit: the installer/user chooses (profile offers candidates only) |
|---|---|
| Which externals exist → `packages.yaml` content | **Install tree location** |
| Compiler / MPI / GPU provider wiring | **Build stage, source/build caches** |
| CPU target / optimization | **View & module roots** |
| Module file *syntax / format* | **Module exposure mode + layout, `publish_root`** |
| The deterministic workspace | The specs / package-sets; which Spack |

**The install tree is never auto-derived.** `profile.filesystem.install_tree_candidates`
are *candidates*; the profile cannot know where this particular install should
land. The installer chooses. Likewise module exposure is a deliberate choice, not
a silent default.

Where the framework can help on the explicit values: a **fact-based check**:
if the chosen install tree is not writable or is too small per profile facts,
flag it. The framework validates the choice; it never makes it. No Spack runs.

## Input ownership: who, where, when

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
| Shared-filesystem collaboration group and access audience | **Installer / release owner** | `deployment.yaml.access` | Stage 0 setup / publish |
| Which Spack version (floor/pin) **and where the Spack tool root lives** | Template maintainer (floor), package manager (pin), installer (shared default), builder (approved local override) | `defaults.spack.floor`, `stack.yaml.spack.version`, `deployment.yaml.spack.root` or build-time `SPACK_ROOT` | curate/author/install |

In practice the package manager, the installer, and the template maintainer are
often the **same person**. The ownership split is therefore mostly about *which
file* a value belongs in: portable `stack.yaml` intent versus site-specific
`deployment.yaml` paths, not about org boundaries.

## The deployment overlay (`deployment.yaml`)

A per-system overlay holding the installer-chosen, non-portable values. It is
kept **out of** the portable `stack.yaml` so the same stack intent renders on any
system. Current shape:

```yaml
# systems/<system>/deployment.yaml — installer-owned; never auto-derived
schema_version: 1
system: example-cray                  # must match profile.system.name

access:
  group: cse                          # REQUIRED — Unix group owning shared stack artifacts
  read: group                         # REQUIRED — group or world
  write: group                        # REQUIRED — user or group

install_tree:
  root: /shared/stack/opt             # REQUIRED — chosen from profile candidates, not derived
  padded_length: 128                  # optional

build_stage:
  default: /scratch/${USER}/spack-stage
  by_node_type:                       # optional per-node-type overrides
    build: /scratch/${USER}/stage

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
  root: /shared/cse/tools/spack/1.2.2 # optional shared default; a builder may select an identity-equivalent local checkout
```

Where it lives and how it is consumed:

- **Lives** at `systems/<system>/deployment.yaml` in `stack-content`, next to
  `profile.yaml`, but it is *installer-owned* (chosen), where `profile.yaml` is
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

## Shared access and permissions

The selected install, cache, view, module, buildcache, and publication roots
normally live on a shared filesystem. Their access policy is a deployment
decision. It is not a profile fact. Cluster Inspector must not inspect group
membership or change modes. The production Stack Composer render records the
chosen policy and does not modify deployment roots. The temporary CSE
`init-workspace` helper is narrower: while creating a new initialized workspace,
it applies that workspace's declared read/write modes to the files and
directories it just generated. It does not change group ownership or recurse
outside the new workspace. The setgid parent remains responsible for assigning
the CSE group.

For the initial deployment, `deployment.yaml.access` records:

- the site runbook names one CSE collaboration group;
- working roots are owned by that group, use setgid directories, and are
  group-readable/writable/executable while a release is assembled;
- a group-friendly/private umask (`0007`) or an equivalent default ACL keeps
  new files in the collaboration model without granting access to others;
- promoted release content is readable/executable by the approved consumer
  audience and is not edited in place; for the current shared HPC deployment,
  that audience is represented by `read: world`;
- consumers outside the collaboration group receive no write access;
- the module front door, views needed at runtime, install tree, and `current`
  pointer are verified from both login and compute nodes using a clean session
  owned by another group member.

Spack already owns the package-prefix portion of this policy. Spack 1.1.1 and
newer accept package permissions in `packages.yaml`:

```yaml
packages:
  all:
    permissions:
      read: group
      write: group
      group: <site-cse-group>
```

That example is the restricted build policy. Publication changes the package
policy to `read: world`, `write: user`, and the same CSE owner group. The
publisher owns writes while assembling the release; consumers receive
read/execute only. The build/publish adapter applies the same role-specific
intent to views, modules, workspaces, and release roots, then removes
group/other write when it freezes an accepted release.

This applies the group and read/write policy to packages installed in the Spack
store, including setgid inheritance within each package prefix. It does not
govern the top-level install root, source and misc caches, build stage,
buildcache files, views, generated modulefiles, release manifests, or the
`current` pointer. The build/publish adapter still owns those paths.

Setgid inheritance and default ACL support vary by filesystem and site policy.
The build/publish adapter therefore owns the concrete POSIX/ACL operations.
Do not recursively change an existing shared tree until the filesystem owner
has confirmed that the tree is dedicated to this stack.

The deployment schema intentionally keeps this interface small: collaboration
group, read audience, and write audience. Stack Composer maps it to
`packages:all:permissions`; the build/publish adapter applies the same intent to
the remaining shared roots. Numeric mode bits remain adapter details unless
real systems require them as portable inputs.

## Spack tool root vs. package install tree

Two different locations, easily confused:

- **Spack tool root**: where the pinned Spack executable/code checkout lives.
  Only the build path needs it. The CSE managed workflow may source an
  installer-provisioned shared root or a builder-local root at
  `<root>/share/spack/setup-env.sh`. It verifies the same exact version, tag,
  commit, and clean state in either location.
- **Spack package install tree**: where Spack installs concrete package
  prefixes and keeps the shared store database and prefix locks. It is the
  `install_tree` above: a separate installer-chosen path that is deliberately
  writable during restricted builds.

`stack-composer` needs neither: render is Spack-free; the tool root and package
install tree matter only after a build path starts. The generated workspace may
record the package install tree, but it never embeds or modifies the Spack tool
root.

### Pinned Spack policy for CSE managed builds

One Spack runtime identity is approved per release: source repository,
version/tag, and commit. A builder may select either:

- an installer-provisioned shared root such as `tools/spack/1.2.2/`; or
- a builder-local root such as `$HOME/STACK_TESTING/spack/1.2.2/`.

The selected path must be visible from the login and build nodes used by that
builder. The shared root is read-only to builders. A local checkout is owned by
the builder but remains clean and unchanged while the release is active.
Builders do not run `spack isolate`, modify `$SPACK_ROOT/etc/spack`, pull,
switch branches, or replace the selected checkout in place during a build.

Changing only the selected root path is operational when both roots have the
same verified runtime identity. A changed Spack version or commit is a
release/DAG-significant input.

Mutable state remains outside the shared tool root:

- `SPACK_DISABLE_LOCAL_CONFIG=true` disables ambient user and system config;
- `SPACK_USER_CACHE_PATH` names a per-user work/scratch cache and state root;
- `SPACK_GNUPGHOME` names a private per-user or site-approved signing/trust
  keyring, because Spack 1.2.2 otherwise defaults that keyring below the tool
  root;
- `PYTHONDONTWRITEBYTECODE=1` prevents Python bytecode caches in the selected
  checkout;
- generated environment `include::` scopes remain the configuration boundary;
- build stages remain per-user or node-local; and
- the shared package install tree, database, and locks remain deployment-owned.

`SPACK_DISABLE_LOCAL_CONFIG` does not by itself disable the checkout-local
`site` scope in Spack 1.2.2. For generated environments, `include::` overrides
that scope. The build path must retain `spack config scopes -vp` evidence and
fail if an unexpected active user, system, or site policy scope appears.

The Initial Conversion Trial workspace currently applies a narrower
build-path override: its generated launcher resolves Spack's mutable
`config:misc_cache` through a persistent builder-private
`SPACK_MISC_CACHE_PATH`, because real Spack provider and concretization indexes
were observed with user-only file modes. That trial evidence is a required
input to the later full-render cache design; it does not change the current
`deployment.yaml` schema in this note.

## Status and open questions

The schema exists now; first-system testing still needs to confirm the final
field set:

1. Final `deployment.yaml` field set and which keys are required vs. defaulted.
2. Whether `modules.publish_root` stays in deployment permanently; the
   portability split says it belongs with installer-owned paths.
3. Whether build-stage and caches need per-node-type granularity in practice.
4. How site defaults seeded at Stage 0 interact with build-time overrides
   (precedence, and how the chosen values are recorded in the release manifest).
5. The fact-based path checks worth running (writable, free space, on a shared
   filesystem visible to compute nodes).
6. Which build/publish adapter applies group ownership, setgid/default ACL
   behavior, and release hardening outside Spack package prefixes.
