# CSE Static Pilot Runbook

## Purpose

This is the single operator procedure for Blueback, Raider, Wheat, and Fran.
Run it once per system to move one reviewed Spack 1.2 environment through the
complete static-pilot sequence:

```text
operator-controlled tools and source
  -> reviewed profile.yaml
  -> render-static catalog
  -> restricted CSE build workspace
  -> concretize and build from source
  -> exercise each lane on the target system
  -> private CSE build cache
  -> separate shared CSE publication workspace
  -> same approved lockfiles
  -> cache-only installation
  -> published views and modules
```

The restricted build and shared publication are two installations of the same
approved concrete DAG. Publication is not a second independent solve or source
build. The validated `spack.lock` files cross the boundary, and the publication
install uses `--only-concrete --use-buildcache=only`. A missing binary stops
promotion.

This is the current pre-v1 static workflow. There is no parallel legacy
procedure. `render-static` creates reusable platform scopes; it does not create
a complete environment. `init-workspace` combines an exact catalog selection
with the CSE pilot blueprint to create the build or publication workspace.

This runbook does not change the full `render` lifecycle. Apply this sequence
to the static pilot first; update the full-render workflow after it is proven on
the target systems.

## What the current direction establishes

The current working direction establishes the workflow, not a frozen package
or version roster:

- build in a restricted CSE Spack environment;
- exercise a lane on its target system before calling it complete;
- push only approved binaries to a private CSE build cache;
- install the final shared CSE release from that cache;
- use Spack 1.2 for the pilot;
- register selected platform components as externals when policy says the
  platform owns them;
- keep module naming and layout work moving without treating unfinished polish
  as permission to skip runtime validation.

The active package list remains
`stack-content/pilots/cse-pilot/roster.yaml`. Provider and version choices come
from the reviewed profile, static catalog, and pilot values. Do not copy the
provisional package or version list from an email into generated files.

## Pilot order

| Order | System | Known family | System delta |
|---:|---|---|---|
| 1 | Blueback | Cray PE, Slurm, ROCm | `stack-content/systems/blueback/runbook-notes.md` |
| 2 | Raider | Generic Linux, Slurm, CUDA | `stack-content/systems/raider/runbook-notes.md` |
| 3 | Wheat | Generic Linux, PBS | Create from the system-note template |
| 4 | Fran | Cray PE; scheduled later | Create from the system-note template |

The table selects the platform checklist, not provider versions. Every
compiler, MPI, GPU, prefix, and module value must come from the live system's
reviewed profile and generated catalog.

## Pilot storage and control policy

Keep tools, source, raw probes, and editable inputs under the pilot operator's
control. Put reviewed build products in a restricted CSE tree and user-facing
release products in a distinct published CSE tree.

```text
$HOME/STACK_TESTING/                         # operator-controlled
  cluster-inspector/                         # source + built binary
  stack-composer/                            # source + built pyz/spack-build
  stack-content/                             # editable pilot inputs
  stack-planning/                            # current runbook/design
  spack/<version>/                           # optional pinned Spack checkout
  probe-work/<system>/<catalog-release>/     # raw fragments/transcripts

<cse-pilot-root>/                            # shared filesystem; CSE group
  restricted/                                # builders only during pilot
    catalogs/<system>/static/<catalog-release>/
    workspaces/<system>/cse-pilot/<pilot-release>/
    releases/<system>/<pilot-release>/
      spack/opt/                              # source-build install tree
      views/                                  # validation views
      modules/                                # validation package modules
    cache/{source,misc}/
    buildcache/<system>/<pilot-release>/      # approved binaries only
    evidence/<system>/<pilot-release>/
  published/                                 # final shared CSE consumption
    workspaces/<system>/cse-pilot/<pilot-release>/
    releases/<system>/<pilot-release>/
      spack/opt/                              # populated from build cache only
      views/                                  # user-facing views
      modules/                                # user-facing package modules
      evidence/

<node-local-or-site-scratch>/
  <user>/<system>/<pilot-release>/{build,publish}-stage/
```

The Unix group is CSE. Use the site's exact CSE Unix group name; do not invent a
different group label. During the operator-controlled pilot, the operator owns
writes and the CSE group has read/execute access. Use
`permissions.group: <CSE Unix group>`, `permissions.read: group`, and
`permissions.write: user`. Change the write or read audience only through an
approved release-policy decision.

The private build cache is private because of filesystem or service access
controls. Spack's `buildcache push --private` option concerns redistribution of
non-redistributable packages; it is not an access-control mechanism.

Generate catalogs and workspaces directly at their final paths. Their manifests
and `include::` entries contain absolute paths, so moving them afterward breaks
the workspace. Build stages are disposable and belong on node-local or site
scratch.

The catalog becomes read-only after review. The restricted workspace stays
operator-writable through lock generation and evidence capture. The published
workspace is initialized separately and is never allowed to build from source.

## Build and promotion gates

Do not advance past a failed gate.

- [ ] All four repositories are synchronized on
  `codex/simplified-render-plan`.
- [ ] Fresh Cluster Inspector and Stack Composer artifacts run.
- [ ] The selected Spack is version 1.2 or newer.
- [ ] `profile.yaml` verifies and matches the live system.
- [ ] The static catalog contains one compatible compiler/MPI/GPU tuple.
- [ ] The restricted values file names only real catalog scopes and approved
  restricted paths.
- [ ] The restricted workspace generates five environments and five native
  `modules.yaml` files.
- [ ] All five restricted environments concretize and their lockfiles pass
  review.
- [ ] Every lane builds and passes its target runtime checks.
- [ ] Only approved concrete specs are pushed to the private CSE build cache.
- [ ] The publication values preserve the same package/provider intent and
  change only the workspace role and deployment paths.
- [ ] The approved lockfiles are copied into the publication workspace.
- [ ] The shared release installs with `--only-concrete
  --use-buildcache=only`; no source fallback occurs.
- [ ] Published hashes match the restricted build hashes, and user-facing views
  and modules pass from a clean session.

## 1. Set the system values

Start a clean Bash shell on the target system. Use a lowercase system name:
`blueback`, `raider`, `wheat`, or `fran`.

```bash
export WORK_ROOT="$HOME/STACK_TESTING"
export SYSTEM_NAME="<system>"
export STACK_BRANCH="codex/simplified-render-plan"
export CATALOG_RELEASE="<system>-catalog-001"
export PILOT_RELEASE="<system>-pilot-001"
export CSE_GROUP="<approved-cse-unix-group>"
export CSE_PILOT_ROOT="<approved-shared-cse-path>/cse-pilot"

export INSPECTOR="$WORK_ROOT/cluster-inspector"
export COMPOSER="$WORK_ROOT/stack-composer"
export CONTENT="$WORK_ROOT/stack-content"
export PLANNING="$WORK_ROOT/stack-planning"
export SYSTEM_DIR="$CONTENT/systems/$SYSTEM_NAME"
export PROBE_DIR="$WORK_ROOT/probe-work/$SYSTEM_NAME/$CATALOG_RELEASE"
export STACK_COMPOSER="$COMPOSER/dist/stack-composer.pyz"

export CSE_RESTRICTED_ROOT="$CSE_PILOT_ROOT/restricted"
export CSE_PUBLISHED_ROOT="$CSE_PILOT_ROOT/published"
export STATIC_ROOT="$CSE_RESTRICTED_ROOT/catalogs"
export CATALOG="$STATIC_ROOT/$SYSTEM_NAME/static/$CATALOG_RELEASE"
export BUILD_WORKSPACE="$CSE_RESTRICTED_ROOT/workspaces/$SYSTEM_NAME/cse-pilot/$PILOT_RELEASE"
export PUBLISH_WORKSPACE="$CSE_PUBLISHED_ROOT/workspaces/$SYSTEM_NAME/cse-pilot/$PILOT_RELEASE"
export BUILD_RELEASE_ROOT="$CSE_RESTRICTED_ROOT/releases/$SYSTEM_NAME/$PILOT_RELEASE"
export PUBLISH_RELEASE_ROOT="$CSE_PUBLISHED_ROOT/releases/$SYSTEM_NAME/$PILOT_RELEASE"
export BUILDCACHE_ROOT="$CSE_RESTRICTED_ROOT/buildcache/$SYSTEM_NAME/$PILOT_RELEASE"
export BUILDCACHE_URL="file://$BUILDCACHE_ROOT"
export BUILD_EVIDENCE="$CSE_RESTRICTED_ROOT/evidence/$SYSTEM_NAME/$PILOT_RELEASE"
export PUBLISH_EVIDENCE="$PUBLISH_RELEASE_ROOT/evidence"
export BUILD_VALUES="$SYSTEM_DIR/cse-pilot-build-values.yaml"
export PUBLISH_VALUES="$SYSTEM_DIR/cse-pilot-publish-values.yaml"

mkdir -p "$WORK_ROOT" "$PROBE_DIR"
```

Do not create repository-owned files until the repositories exist. Step 5
creates the shared CSE roots after the filesystem owner confirms the path and
group.

## 2. Acquire and synchronize the repositories

Clone missing repositories as siblings. HTTPS is the default on HPC login
nodes because SSH keys may not be installed there.

```bash
if [ ! -d "$INSPECTOR/.git" ]; then
  git clone https://github.com/ray12514/cluster-inspector.git "$INSPECTOR"
fi
if [ ! -d "$COMPOSER/.git" ]; then
  git clone https://github.com/ray12514/stack-composer.git "$COMPOSER"
fi
if [ ! -d "$CONTENT/.git" ]; then
  git clone https://github.com/ray12514/stack-content.git "$CONTENT"
fi
if [ ! -d "$PLANNING/.git" ]; then
  git clone https://github.com/ray12514/stack-planning.git "$PLANNING"
fi
```

Review local state before switching branches:

```bash
for repo in cluster-inspector stack-composer stack-content stack-planning; do
  git -C "$WORK_ROOT/$repo" status --short --branch
done
```

Stop if a repository contains unreviewed work. Then synchronize all four:

```bash
for repo in cluster-inspector stack-composer stack-content stack-planning; do
  git -C "$WORK_ROOT/$repo" fetch origin
  git -C "$WORK_ROOT/$repo" switch "$STACK_BRANCH"
  git -C "$WORK_ROOT/$repo" pull --ff-only
done
```

Create the system note from the template when needed:

```bash
mkdir -p "$SYSTEM_DIR"
if [ ! -f "$SYSTEM_DIR/runbook-notes.md" ]; then
  cp "$CONTENT/systems/_template/runbook-notes.md" "$SYSTEM_DIR/runbook-notes.md"
fi
```

## 3. Build and verify the tools

Build Cluster Inspector with Go 1.22 or newer:

```bash
cd "$INSPECTOR"
make build
./cluster-inspector --help >/dev/null
```

Build Stack Composer in its repository-local Python environment:

```bash
cd "$COMPOSER"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
PYTHON=.venv/bin/python bash scripts/build-pyz.sh
python "$STACK_COMPOSER" --help >/dev/null
deactivate
```

Activate the exact Spack checkout selected for the pilot:

```bash
source /path/to/spack/share/spack/setup-env.sh
: "${SPACK_ROOT:?SPACK_ROOT is not set}"
spack --version
```

The pilot workspace uses Spack 1.2 `group` and `needs`; stop if Spack is older
than 1.2. The Spack tool may live under `$WORK_ROOT/spack/<version>` or come
from a site module. It is distinct from both Spack install trees.

Record the tool versions and repository commits in the system notes.

## 4. Generate and review `profile.yaml`

Use the fragment workflow for the first run on a system. It makes the node that
produced each fact explicit.

On the login node:

```bash
cd "$PROBE_DIR"
HINTS_OPTION=()
if [ -f "$SYSTEM_DIR/inspector-hints.yaml" ]; then
  HINTS_OPTION=(--hints "$SYSTEM_DIR/inspector-hints.yaml")
fi

"$INSPECTOR/cluster-inspector" probe-system \
  --system "$SYSTEM_NAME" \
  "${HINTS_OPTION[@]}" \
  --record "$PROBE_DIR/system-probe-transcript.yaml" \
  --output "$PROBE_DIR/system.frag.yaml"

"$INSPECTOR/cluster-inspector" probe-node \
  --node-type login \
  --role both \
  --runner this \
  --output "$PROBE_DIR/login.frag.yaml"
```

Allocate or log into each distinct compute, GPU, and build node type. Run this
on the allocated node, changing the name and role to match reality:

```bash
"$INSPECTOR/cluster-inspector" probe-node \
  --node-type <node-type-name> \
  --role <runtime|build_host|both> \
  --runner this \
  --output <node-type-name>.frag.yaml
```

Copy every node fragment back to `$PROBE_DIR`. Wheat uses PBS rather than
Slurm, but `--runner this` is unchanged after entering the allocation.

Merge the system fragment and every unique node fragment. Adjust this example
to the node types that exist:

```bash
"$INSPECTOR/cluster-inspector" merge \
  --system-fragment "$PROBE_DIR/system.frag.yaml" \
  --node "$PROBE_DIR/login.frag.yaml" \
  --node "$PROBE_DIR/compute.frag.yaml" \
  --node "$PROBE_DIR/gpu.frag.yaml" \
  --output "$PROBE_DIR/profile.yaml"

"$INSPECTOR/cluster-inspector" verify "$PROBE_DIR/profile.yaml"
```

Review compiler, MPI, GPU, fabric, runtime, prefix, module, compatibility, and
node-role facts against the live machine. On Cray systems, select one coherent
CPE/compiler/Cray MPICH/GPU runtime set. On generic Linux systems, prove the
compiler pairing for the selected MPI. Preserve incorrect discovery evidence,
fix the inspector or hints, and regenerate. Do not hand-enter a guess as a
durable fact.

Copy only the verified fact sheet into the editable Stack Content checkout:

```bash
cp "$PROBE_DIR/profile.yaml" "$SYSTEM_DIR/profile.yaml"
```

Gate: the profile verifies and the system notes identify the reviewed tuple.

## 5. Create the restricted and published CSE roots

Confirm the exact CSE group and shared path with the filesystem owner. Use an
operator-write/group-read umask and setgid directories so new artifacts inherit
the CSE group without granting group write:

```bash
umask 0027

install -d -m 2750 -g "$CSE_GROUP" \
  "$CSE_PILOT_ROOT" \
  "$CSE_RESTRICTED_ROOT" \
  "$STATIC_ROOT" \
  "$CSE_RESTRICTED_ROOT/workspaces" \
  "$BUILD_RELEASE_ROOT/spack/opt" \
  "$BUILD_RELEASE_ROOT/views" \
  "$BUILD_RELEASE_ROOT/modules" \
  "$CSE_RESTRICTED_ROOT/cache/source" \
  "$CSE_RESTRICTED_ROOT/cache/misc" \
  "$BUILDCACHE_ROOT" \
  "$BUILD_EVIDENCE" \
  "$CSE_PUBLISHED_ROOT" \
  "$CSE_PUBLISHED_ROOT/workspaces" \
  "$PUBLISH_RELEASE_ROOT/spack/opt" \
  "$PUBLISH_RELEASE_ROOT/cache/misc" \
  "$PUBLISH_RELEASE_ROOT/views" \
  "$PUBLISH_RELEASE_ROOT/modules" \
  "$PUBLISH_EVIDENCE"
```

Do not recursively change ownership or permissions on an existing shared tree.
If the top-level path is site-owned, ask its owner to create the dedicated roots.

## 6. Generate and inspect the static catalog

```bash
python "$STACK_COMPOSER" render-static \
  --profile "$SYSTEM_DIR/profile.yaml" \
  --templates "$CONTENT/templates" \
  --template-set v6 \
  --output-root "$STATIC_ROOT" \
  --release "$CATALOG_RELEASE" \
  --rendered-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --source-repo "stack-content" \
  --source-commit "$(git -C "$CONTENT" rev-parse HEAD)"
```

Add `--source-dirty` when reviewed system inputs are not committed. Use
`--overwrite` only when deliberately regenerating the same catalog release.

Inspect the generated catalog:

```bash
cat "$CATALOG/README.md"
sed -n '1,260p' "$CATALOG/manifest.yaml"
sed -n '1,320p' "$CATALOG/reports/static-plan.yaml"
find "$CATALOG/scopes" -type f | sort
```

For the intended tuple, inspect every `packages.yaml` and `toolchains.yaml`.
Confirm external specs, prefixes, modules, compiler stamps, MPI requirements,
and GPU packages against the reviewed profile.

Gate: the catalog contains the exact compatible compiler, MPI, GPU, common, and
platform scopes needed by the pilot. Fix the profile or catalog logic when a
scope is missing; do not type a nonexistent path into a values file.

## 7. Create the restricted build values

```bash
cp "$CONTENT/pilots/cse-pilot/site-values.example.yaml" "$BUILD_VALUES"
```

Edit the copy. Use only the current profile, catalog, approved paths, and active
pilot roster.

| Values | Restricted build setting |
|---|---|
| `workspace.role` | `build` |
| system/release | current profile/catalog plus `PILOT_RELEASE` |
| compiler/MPI/GPU | exact selected tuple and modules |
| `catalog_scopes.*` | exact relative paths below `$CATALOG` |
| install tree | `$BUILD_RELEASE_ROOT/spack/opt` |
| build stage | approved build scratch path |
| source/misc caches | `$CSE_RESTRICTED_ROOT/cache/{source,misc}` |
| views/modules roots | `$BUILD_RELEASE_ROOT/{views,modules}` |
| build-cache name | `cse-pilot` |
| build-cache URL | `$BUILDCACHE_URL` expanded to an absolute `file:///...` URL |
| permissions | CSE group, group read, user write |
| package repository | reviewed pilot recipe pin |

Toolchain names may contain only letters, digits, and underscores. Their
versions must match the catalog tuple. Use `source: external` for the first
platform surface unless a reviewed experiment explicitly builds that provider.
Do not insert dummy catalog scopes.

Record the selected tuple, roots, cache URL, and values path in the system
notes.

## 8. Initialize and inspect the restricted build workspace

```bash
python "$STACK_COMPOSER" init-workspace \
  --blueprint "$CONTENT/pilots/cse-pilot" \
  --catalog "$CATALOG" \
  --values "$BUILD_VALUES" \
  --output "$BUILD_WORKSPACE"
```

Use `--overwrite` only after reviewing and deliberately replacing the existing
workspace.

```bash
cat "$BUILD_WORKSPACE/README.md"
sed -n '1,260p' "$BUILD_WORKSPACE/workspace-manifest.yaml"
find "$BUILD_WORKSPACE/environments" -name spack.yaml -print | sort
find "$BUILD_WORKSPACE/configs/environments" -name modules.yaml -print | sort
find "$BUILD_WORKSPACE/modulefiles" -type f -print | sort
cat "$BUILD_WORKSPACE/configs/common/mirrors.yaml"
```

Verify every include path, provider selection, deployment path, native
`modules.yaml`, and private build-cache URL. Serial must contain no MPI scope;
MPI and GPU must share the selected compatible MPI tuple.

Snapshot the reviewed inputs and tool identities:

```bash
mkdir -p "$BUILD_WORKSPACE/inputs"
cp "$SYSTEM_DIR/profile.yaml" "$BUILD_WORKSPACE/inputs/profile.yaml"
cp "$BUILD_VALUES" "$BUILD_WORKSPACE/inputs/cse-pilot-build-values.yaml"
cp "$CATALOG/manifest.yaml" "$BUILD_WORKSPACE/inputs/catalog-manifest.yaml"
cp "$CATALOG/reports/static-plan.yaml" "$BUILD_WORKSPACE/inputs/static-plan.yaml"
git -C "$INSPECTOR" rev-parse HEAD > "$BUILD_WORKSPACE/inputs/cluster-inspector.commit"
git -C "$COMPOSER" rev-parse HEAD > "$BUILD_WORKSPACE/inputs/stack-composer.commit"
git -C "$CONTENT" rev-parse HEAD > "$BUILD_WORKSPACE/inputs/stack-content.commit"
spack --version > "$BUILD_WORKSPACE/inputs/spack.version"
```

## 9. Concretize and review the restricted environments

Set the exact names from the build values file:

```bash
export COMPILER_NAME="<compiler-name>"
export MPI_NAME="<mpi-name>"
export GPU_LANE_SUFFIX="<gpu-lane-suffix>"

ENVIRONMENTS=(
  "$COMPILER_NAME/core"
  "$COMPILER_NAME/common"
  "$COMPILER_NAME/serial"
  "$COMPILER_NAME/mpi-$MPI_NAME"
  "$COMPILER_NAME/gpu-$MPI_NAME-$GPU_LANE_SUFFIX"
)
```

Concretize every restricted environment:

```bash
for environment in "${ENVIRONMENTS[@]}"; do
  echo "Concretizing $environment"
  spack -e "$BUILD_WORKSPACE/environments/$environment" \
    concretize --force -j 1 || break
done
```

Review every lock:

```bash
for environment in "${ENVIRONMENTS[@]}"; do
  test -f "$BUILD_WORKSPACE/environments/$environment/spack.lock" || break
  spack -e "$BUILD_WORKSPACE/environments/$environment" find -lv
done
```

Confirm that externals remain external, producer groups exist only where
intended, Serial contains no MPI, MPI/GPU preserve the selected toolchain, and
version-paired package roots preserve their pairings. Save solver output and fix
the owning profile, catalog, values, roster, or blueprint. Never patch a lock.

Gate: all five restricted lockfiles exist and pass review.

## 10. Build and exercise every restricted lane

Build Core, Common, Serial, MPI, then GPU:

```bash
export BUILD_JOBS="<approved-job-count>"

for environment in "${ENVIRONMENTS[@]}"; do
  echo "Building $environment"
  spack -e "$BUILD_WORKSPACE/environments/$environment" fetch -D || break
  spack -e "$BUILD_WORKSPACE/environments/$environment" \
    install -j "$BUILD_JOBS" --fail-fast || break
  spack -e "$BUILD_WORKSPACE/environments/$environment" \
    env view regenerate || break
  spack -e "$BUILD_WORKSPACE/environments/$environment" \
    module tcl refresh --delete-tree -y || break
done
```

Apply the platform checklist after installation. A lane is not approved merely
because compilation finished. Exercise its compiler/wrappers, representative
libraries, module exposure, and applicable single-node, multi-node, GPU, and
GPU-aware MPI behavior on the target system.

Record each lane as `built`, `runtime-passed`, or `held` in the system notes.
Only `runtime-passed` lanes may enter the build cache.

Capture the concrete hashes before promotion:

```bash
mkdir -p "$BUILD_EVIDENCE/hashes"
for environment in "${ENVIRONMENTS[@]}"; do
  label="${environment//\//-}"
  spack -e "$BUILD_WORKSPACE/environments/$environment" \
    find --format '{hash}' | sort > "$BUILD_EVIDENCE/hashes/$label.build.txt"
done
```

## 11. Push approved specs to the private CSE build cache

Configure the site-approved signing key before pushing. The commands below
assume a signed cache. If cache signing is not ready, stop with a validated
restricted build; do not silently publish unsigned binaries to users.

Push one approved environment at a time. With an active concrete environment
and no explicit spec arguments, Spack selects its concrete roots and their
dependencies:

```bash
for environment in "${ENVIRONMENTS[@]}"; do
  echo "Publishing approved binaries for $environment"
  spack -e "$BUILD_WORKSPACE/environments/$environment" \
    buildcache push --signed --update-index --fail-fast "$BUILDCACHE_URL" \
    || break
done

spack buildcache update-index --keys "$BUILDCACHE_URL"
spack buildcache check-index --verify all "$BUILDCACHE_URL"
spack -e "$BUILD_WORKSPACE/environments/${ENVIRONMENTS[0]}" buildcache list
```

The cache is a promotion boundary, not a general scratch mirror. Do not push a
held lane, overwrite an approved binary, or expand the package set without a
new reviewed release record.

Gate: the index verifies and every approved root/dependency needed by the five
lockfiles is available to the publication install.

## 12. Create and initialize the publication workspace

Derive the publication values from the reviewed build values so provider and
package intent cannot drift:

```bash
cp "$BUILD_VALUES" "$PUBLISH_VALUES"
```

Edit only these fields:

| Values | Publication setting |
|---|---|
| `workspace.role` | `publish` |
| install tree | `$PUBLISH_RELEASE_ROOT/spack/opt` |
| build stage | approved publication scratch path |
| misc cache | a publication-specific cache below `$PUBLISH_RELEASE_ROOT` |
| views/modules roots | `$PUBLISH_RELEASE_ROOT/{views,modules}` |

Keep the system, release, package/provider data, catalog scopes, package recipe
pin, permissions, and private build-cache URL identical.

```bash
python "$STACK_COMPOSER" init-workspace \
  --blueprint "$CONTENT/pilots/cse-pilot" \
  --catalog "$CATALOG" \
  --values "$PUBLISH_VALUES" \
  --output "$PUBLISH_WORKSPACE"
```

Inspect the publication README, manifest, configs, modules, and mirror. Confirm
that all deployment paths are published paths and that the mirror still points
to the approved private CSE build cache.

## 13. Transfer the approved locks

Do not concretize the publication workspace. Copy the reviewed lockfile for
each matching environment:

```bash
for environment in "${ENVIRONMENTS[@]}"; do
  cp "$BUILD_WORKSPACE/environments/$environment/spack.lock" \
    "$PUBLISH_WORKSPACE/environments/$environment/spack.lock" || break
done
```

Prove Spack can read the copied locks without changing them:

```bash
for environment in "${ENVIRONMENTS[@]}"; do
  spack -e "$PUBLISH_WORKSPACE/environments/$environment" find -lv || break
done
```

Gate: the publication workspace has the same five concrete DAGs as the
restricted build workspace.

## 14. Install the shared release from the build cache only

Import and trust the approved cache signing key through the site's key policy:

```bash
spack -e "$PUBLISH_WORKSPACE/environments/${ENVIRONMENTS[0]}" \
  buildcache keys --install --trust "$BUILDCACHE_URL"
```

Install from the copied locks. These flags are mandatory:

```bash
for environment in "${ENVIRONMENTS[@]}"; do
  echo "Installing approved binaries for $environment"
  spack -e "$PUBLISH_WORKSPACE/environments/$environment" \
    install --only-concrete --use-buildcache=only --fail-fast || break
done
```

Do not run `concretize`, `fetch -D`, or a normal source-capable `install` in the
publication workspace. A cache miss is a promotion failure. Return to the
restricted workspace, build and validate the missing exact hash, push it, and
rerun the cache-only installation.

Regenerate user-facing views and package modules only after all cache-only
installs succeed:

```bash
for environment in "${ENVIRONMENTS[@]}"; do
  spack -e "$PUBLISH_WORKSPACE/environments/$environment" \
    env view regenerate || break
  spack -e "$PUBLISH_WORKSPACE/environments/$environment" \
    module tcl refresh --delete-tree -y || break
done
```

Compare the concrete hashes:

```bash
mkdir -p "$PUBLISH_EVIDENCE/hashes"
for environment in "${ENVIRONMENTS[@]}"; do
  label="${environment//\//-}"
  spack -e "$PUBLISH_WORKSPACE/environments/$environment" \
    find --format '{hash}' | sort > "$PUBLISH_EVIDENCE/hashes/$label.published.txt"
  diff -u \
    "$BUILD_EVIDENCE/hashes/$label.build.txt" \
    "$PUBLISH_EVIDENCE/hashes/$label.published.txt" || break
done
```

Gate: all hashes match and no source build occurred below the published root.

## 15. Validate modules and freeze the release record

Exercise the publication module hierarchy from clean sessions:

```bash
module use "$PUBLISH_WORKSPACE/modulefiles"
module load "cse/<Compiler-public-name>"
module avail
module load Serial
```

Repeat separately for `MPI` and `GPU`. Loading a conflicting second lane must
fail. Verify package-module visibility after installation, view regeneration,
and module refresh. Apply `cray_pe_acceptance_checklist_v1.md` on Cray PE and
`generic_linux_acceptance_checklist_v1.md` on generic Linux.

Snapshot the publication inputs and provenance:

```bash
mkdir -p "$PUBLISH_WORKSPACE/inputs"
cp "$PUBLISH_VALUES" "$PUBLISH_WORKSPACE/inputs/cse-pilot-publish-values.yaml"
cp "$BUILD_VALUES" "$PUBLISH_WORKSPACE/inputs/cse-pilot-build-values.yaml"
cp "$CATALOG/manifest.yaml" "$PUBLISH_WORKSPACE/inputs/catalog-manifest.yaml"
cp "$CATALOG/reports/static-plan.yaml" "$PUBLISH_WORKSPACE/inputs/static-plan.yaml"
git -C "$COMPOSER" rev-parse HEAD > "$PUBLISH_WORKSPACE/inputs/stack-composer.commit"
git -C "$CONTENT" rev-parse HEAD > "$PUBLISH_WORKSPACE/inputs/stack-content.commit"
spack --version > "$PUBLISH_WORKSPACE/inputs/spack.version"
```

The release becomes user-facing only after the build-cache-only install, hash
comparison, clean-shell module checks, target runtime checks, permission check,
and release-owner approval all pass. Freeze the approved release instead of
editing it in place. A later `current` pointer or wider audience is a release
operation, not part of `render-static` or `init-workspace`.

## Artifact ownership

| Artifact | Location and treatment |
|---|---|
| Tool/source checkouts and built executables | Operator home; mutable and operator-controlled |
| Raw probe fragments/transcripts | Operator home under `probe-work`; review before sharing |
| Editable profiles, values, and system notes | Operator Stack Content checkout |
| Static catalog | Restricted CSE tree; versioned and read-only after review |
| Restricted workspace and lockfiles | Restricted CSE tree; source-build and validation record |
| Restricted install tree/views/modules | Restricted CSE tree; never user-facing |
| Private build cache | Restricted CSE tree; approved binaries only |
| Publication workspace and copied lockfiles | Published CSE tree; cache-only consumer |
| Published install tree/views/modules | Published CSE tree; user-facing after approval |
| Build and publication stages | Node-local or site scratch; disposable |
| Logs, hashes, runtime, and module evidence | Matching restricted/published evidence roots |

The intentionally untracked planning email draft is unrelated to this workflow
and must not be published during a system run.

## System and platform details

Use the following only for system-specific deltas after following this runbook:

- `stack-content/systems/blueback/runbook-notes.md`
- `stack-content/systems/raider/runbook-notes.md`
- `stack-content/systems/_template/runbook-notes.md`
- `cray_pe_acceptance_checklist_v1.md`
- `generic_linux_acceptance_checklist_v1.md`
- `deployment_inputs_and_ownership_v1.md`
