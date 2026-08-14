# CSE Initial Conversion Trials Runbook

## Purpose

This is the single operator procedure for Blueback, Raider, Wheat, and Fran.
Run it once per system to move one reviewed Spack 1.2 workspace through the
complete sequence:

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

`render-static` creates reusable platform scopes. A package manager may include
those scopes from a hand-authored `spack.yaml`. `init-workspace` is the CSE
trial convenience that combines an exact catalog selection with the authored
Initial Conversion Trials blueprint; it is not required to consume the static
catalog.

## What the current direction establishes

The current working direction establishes the workflow, not a frozen package
or version roster:

- build in a restricted CSE Spack environment;
- exercise a lane on its target system before calling it complete;
- push only approved binaries to a private CSE build cache;
- install the final shared CSE release from that cache;
- use Spack 1.2.2 for the initial trials;
- register selected platform components as externals when policy says the
  platform owns them;
- keep module naming and layout work moving without treating unfinished polish
  as permission to skip runtime validation.

The active package list remains
`stack-content/pilots/cse-pilot/roster.yaml`. Provider and version choices come
from the reviewed profile, static catalog, and trial values. Do not copy the
provisional package or version list from an email into generated files.

## System order

| Order | System | Known family | System delta |
|---:|---|---|---|
| 1 | Blueback | Cray PE, Slurm | `stack-content/systems/blueback/runbook-notes.md` |
| 2 | Raider | Generic Linux, Slurm | `stack-content/systems/raider/runbook-notes.md` |
| 3 | Wheat | Generic Linux, PBS | `stack-content/systems/wheat/runbook-notes.md` |
| 4 | Fran | Cray PE | `stack-content/systems/fran/runbook-notes.md` |

The table selects the platform checklist, not provider versions. Every
compiler, MPI, prefix, and module value must come from the live system's
reviewed profile and generated catalog.

Take Blueback through profile review, static catalog generation, and workspace
initialization first. Then repeat those three checkpoints on Raider, Wheat, and
Fran. This establishes all four work trees without making their build results
depend on each other. After the work trees are reviewed, return to Blueback for
the first full concretization/build and use the result to refine the common
procedure before building the other systems.

## Storage and control policy

Keep tools, source, raw probes, and editable inputs under the trial operator's
control. Put reviewed build products in a restricted CSE tree and user-facing
release products in a distinct published CSE tree.

```text
$HOME/STACK_TESTING/                         # operator-controlled
  cluster-inspector/                         # source + built binary
  stack-composer/                            # source + built pyz/spack-build
  stack-content/                             # editable trial inputs
  stack-planning/                            # current runbook/design
  spack/<version>/                           # optional pinned Spack checkout
  probe-work/<system>/<catalog-release>/     # raw fragments/transcripts

<cse-trial-root>/                            # shared filesystem; CSE group
  restricted/                                # builders only during trials
    catalogs/<system>/static/<catalog-release>/
    workspaces/<system>/initial-conversion-trials/<trial-release>/
    releases/<system>/<trial-release>/
      spack/opt/                              # source-build install tree
      views/                                  # validation views
      modules/                                # validation package modules
    cache/{source,misc}/
    buildcache/<system>/<trial-release>/      # approved binaries only
    evidence/<system>/<trial-release>/
  published/                                 # final shared CSE consumption
    workspaces/<system>/initial-conversion-trials/<trial-release>/
    releases/<system>/<trial-release>/
      spack/opt/                              # populated from build cache only
      views/                                  # user-facing views
      modules/                                # user-facing package modules
      evidence/

<node-local-or-site-scratch>/
  <user>/<system>/<trial-release>/{build,publish}-stage/
```

The Unix group is lowercase `cse` on every trial system. During the
operator-controlled trials, the operator owns writes and the `cse` group has
read/execute access. Use
`permissions.group: cse`, `permissions.read: group`, and
`permissions.write: user`. Change the write or read audience only through an
approved release-policy decision.

The private build cache is private because of filesystem or service access
controls. Spack's `buildcache push --private` option concerns redistribution of
non-redistributable packages; it is not an access-control mechanism.

Generate catalogs and workspaces directly at their final paths. The initialized
workspace snapshots the static catalog configuration it consumes and uses
relative `include::` paths for its catalog and workspace-owned scopes. The whole
workspace can therefore be handed to another builder or archived without
depending on the original catalog path. Deployment paths inside `config.yaml`
remain deliberate absolute paths and must still name the approved shared trees.
Build stages are disposable and belong on node-local or site scratch.

The catalog becomes read-only after review. The restricted workspace stays
operator-writable through lock generation and evidence capture. The published
workspace is initialized separately and is never allowed to build from source.

## Build and promotion gates

Do not advance past a failed gate.

- [ ] All four repositories are synchronized on
  `codex/simplified-render-plan`.
- [ ] Fresh Cluster Inspector and Stack Composer artifacts run.
- [ ] The selected Spack is version 1.2.2.
- [ ] `profile.yaml` verifies and matches the live system.
- [ ] The static catalog contains the selected platform compiler and compatible
  MPI scopes.
- [ ] The restricted values file names only real catalog scopes and approved
  restricted paths.
- [ ] The restricted values file selects one portable CPU target supported by
  every profiled CPU-only build/runtime node type.
- [ ] The restricted workspace generates eight environments and eight native
  `modules.yaml` files.
- [ ] All eight restricted environments concretize and their lockfiles pass
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

## Resume and recovery policy

Every run is a sequence of durable checkpoints. Record the last successful
checkpoint in the system notes before starting the next one.

| Checkpoint | State | Durable evidence |
|---:|---|---|
| 1 | Profile verified | reviewed `profile.yaml` and probe evidence |
| 2 | Catalog reviewed | static manifest, plan, and selected scopes |
| 3 | Restricted workspace initialized | build values, workspace manifest, configs, and modules |
| 4 | Locks reviewed | eight approved restricted `spack.lock` files |
| 5 | Lanes validated | per-lane build logs and target runtime results |
| 6 | Cache complete | signed binaries, verified index, and approved hashes |
| 7 | Cache-only publication complete | copied locks, published prefixes, and matching hashes |
| 8 | Release accepted | clean-shell module/runtime evidence and owner approval |

### Same release or new release

Resume the same release only when all of these are true:

- the profile, catalog, semantic provider/package values, roster,
  package-recipe pin, Spack version, and repository commits are unchanged;
- the affected lockfile and concrete hashes are unchanged;
- the failure was operational, such as a scheduler timeout, node loss, network
  interruption, quota exhaustion, or interrupted cache transfer;
- no approved published artifact would be edited in place.

The selected build node type, its ordered stage roots, and `build_jobs` are
operational settings. They may change within the same trial release when the
environment YAML, lockfiles, install tree, and concrete hashes remain
unchanged. Preserve the original locked workspace and create a sibling
operational workspace for the replacement node; do not overwrite the locked
workspace.

Create a new catalog release and a new trial release when observed system facts
or reusable static scopes change. Create a new trial release when the compiler,
MPI, toolchain, specs, variants, values, roster, package recipes, Spack
version, or any lockfile changes. A module or view correction made after a
release is accepted also gets a new trial release, even when package hashes stay
the same.

A new release does not imply rebuilding every package. It may reuse compatible
approved binaries already present in the private CSE build cache. The rule is
about preserving provenance and immutable release records, not discarding safe
cache reuse.

Use `--overwrite` only before the first lockfile exists and before anything has
been pushed or published. Once a run reaches checkpoint 4, preserve the failed
workspace and evidence. Derive a new release for semantic input changes instead
of deleting or rewriting the old record.

### Recovery matrix

| Failure or change | Resume action |
|---|---|
| Scheduler timeout, node failure, temporary network failure, or resolved quota problem with unchanged inputs | Retry only the failed command or environment in the same release. |
| Selected build node is unavailable, but another profiled node can build the same locked target | Create a sibling operational workspace for the replacement node, verify every environment YAML is unchanged, transfer the same locks, and continue the same release against the same install tree. |
| Source build failure caused by a transient host/tool problem | Retry the failed lane after recording the log; earlier validated lanes remain valid. |
| Package recipe, patch, variant, compiler, MPI, or Spack change is required | Create a new trial release, reconcretize, and revalidate every affected lane. |
| Cluster Inspector fact or external module/prefix is wrong | Regenerate the profile, create a new catalog release and trial release, and restart at checkpoint 1. |
| Static catalog scope or toolchain is wrong | Fix the owning profile/catalog logic, create new catalog and trial releases, and restart at checkpoint 2. |
| Restricted workspace template or values are wrong before locks exist | Reinitialize the working release; after locks exist, create a new trial release. |
| A later lane fails while earlier lane locks and inputs remain unchanged | Keep the earlier evidence and retry only the failed lane. If a shared upstream hash changes, reconcretize and revalidate every dependent lane in a new release. |
| Build-cache push, index, or signing operation is interrupted | Retry the cache operation from the installed restricted specs; do not rebuild. |
| Publication reports a cache miss for an exact approved hash | Return to the restricted workspace, build and validate that exact locked hash, push it, and retry only the failed publication environment. If producing it requires a changed hash, create a new release. |
| View or module refresh fails before release acceptance and the DAG is unchanged | Correct and rerun only view/module generation, then repeat clean-shell checks. |
| Published module/view content needs correction after acceptance | Create a new trial release; do not edit the accepted release in place. |
| Platform upgrade changes CPE, compiler, MPI, fabric, OS, or runtime ABI facts | Hold publication and restart with a fresh profile, catalog, locks, and runtime validation. |

### Optional recovery: switch to another profiled build node

Use this procedure only when the planned build node changes. It is not part of
the normal Step 8 to Step 9 path.

Before lockfiles exist, set `CSE_BUILD_NODE_TYPE` to the replacement node key,
regenerate `$BUILD_VALUES`, and deliberately reinitialize the current workspace
with `--overwrite`. The static catalog does not need to be rerendered when it
already contains current facts for both node types.

After lockfiles exist or installation has started, preserve the original
workspace. Generate a sibling workspace that keeps the same `TRIAL_RELEASE`,
install tree, caches, provider selections, package inputs, and Spack version:

```bash
export ORIGINAL_BUILD_WORKSPACE="$BUILD_WORKSPACE"
export CSE_BUILD_NODE_TYPE="login"
export BUILD_VALUES="$SYSTEM_DIR/cse-trials-build-values.login.yaml"
export BUILD_WORKSPACE="${ORIGINAL_BUILD_WORKSPACE}.login"

"$COMPOSER/.venv/bin/python" \
  "$CONTENT/pilots/cse-pilot/scripts/create-build-values.py"

python "$STACK_COMPOSER" init-workspace \
  --blueprint "$CONTENT/pilots/cse-pilot" \
  --catalog "$CATALOG" \
  --values "$BUILD_VALUES" \
  --output "$BUILD_WORKSPACE"

source "$SPACK_ROOT/share/spack/setup-env.sh"
test "$(spack --version)" = "$SPACK_VERSION"
source "$BUILD_WORKSPACE/env/setup-build-env.sh"
ENVIRONMENTS=(
  "$SHARED_COMPILER_NAME/core"
  "$SHARED_COMPILER_NAME/common"
  "$SHARED_COMPILER_NAME/serial"
  "$SHARED_COMPILER_NAME/mpi-$SHARED_MPI_NAME"
  "$PLATFORM_COMPILER_NAME/core"
  "$PLATFORM_COMPILER_NAME/common"
  "$PLATFORM_COMPILER_NAME/serial"
  "$PLATFORM_COMPILER_NAME/mpi-$PLATFORM_MPI_NAME"
)

for environment in "${ENVIRONMENTS[@]}"; do
  cmp \
    "$ORIGINAL_BUILD_WORKSPACE/environments/$environment/spack.yaml" \
    "$BUILD_WORKSPACE/environments/$environment/spack.yaml" || exit 1
  cp \
    "$ORIGINAL_BUILD_WORKSPACE/environments/$environment/spack.lock" \
    "$BUILD_WORKSPACE/environments/$environment/spack.lock" || exit 1
done

python3 "$BUILD_WORKSPACE/scripts/verify-lockfiles.py"
```

Do not reconcretize. Confirm that the replacement node is permitted for builds,
can load every recorded compiler/external module, and can execute the target
architecture already recorded in the locks. The regenerated values file must
show the same `architecture.target`; only `build.node_type` and stage paths may
change. Continue with `spack install --only-concrete`; successful prefixes in
the shared install tree are reused, while an unfinished package is restaged
under the new node's stage root. Do not use `--dont-restage`, delete shared
prefix locks, or run a broad failure-marker cleanup.

### Failure procedure

When a command fails:

1. Stop at that checkpoint. Do not advance the failed lane or its dependents.
2. Record the exact command, exit status, log/evidence path, last successful
   checkpoint, and whether any input changed.
3. Classify the failure as operational, input/DAG-changing, cache promotion, or
   publication/module exposure.
4. Fix the owning source: Cluster Inspector facts, static catalog logic, CSE
   values/roster/blueprint, package recipe, or this process document. Never fix
   generated `spack.yaml` or `spack.lock` files by hand.
5. Record `resume same release` or `new release`, the earliest invalid
   checkpoint, and the exact next command in the system notes.
6. Preserve the failed workspace and evidence until the replacement release is
   accepted.

## 1. Set the system values

Start a clean Bash shell on the target system. Use a lowercase system name:
`blueback`, `raider`, `wheat`, or `fran`.

```bash
export WORK_ROOT="$HOME/STACK_TESTING"
export SYSTEM_NAME="<system>"
export STACK_BRANCH="codex/simplified-render-plan"
export CATALOG_RELEASE="<system>-catalog-001"
export TRIAL_RELEASE="<system>-trial-001"
export CSE_GROUP="cse"
export CSE_TRIAL_ROOT="<approved-shared-cse-path>/initial-conversion-trials"

export INSPECTOR="$WORK_ROOT/cluster-inspector"
export COMPOSER="$WORK_ROOT/stack-composer"
export CONTENT="$WORK_ROOT/stack-content"
export PLANNING="$WORK_ROOT/stack-planning"
export SPACK_VERSION="1.2.2"
export SPACK_ROOT="$WORK_ROOT/spack/$SPACK_VERSION"
export SYSTEM_DIR="$CONTENT/systems/$SYSTEM_NAME"
export PROBE_DIR="$WORK_ROOT/probe-work/$SYSTEM_NAME/$CATALOG_RELEASE"
export STACK_COMPOSER="$COMPOSER/dist/stack-composer.pyz"

export CSE_RESTRICTED_ROOT="$CSE_TRIAL_ROOT/restricted"
export CSE_PUBLISHED_ROOT="$CSE_TRIAL_ROOT/published"
export STATIC_ROOT="$CSE_RESTRICTED_ROOT/catalogs"
export CATALOG="$STATIC_ROOT/$SYSTEM_NAME/static/$CATALOG_RELEASE"
export BUILD_WORKSPACE="$CSE_RESTRICTED_ROOT/workspaces/$SYSTEM_NAME/initial-conversion-trials/$TRIAL_RELEASE"
export PUBLISH_WORKSPACE="$CSE_PUBLISHED_ROOT/workspaces/$SYSTEM_NAME/initial-conversion-trials/$TRIAL_RELEASE"
export BUILD_RELEASE_ROOT="$CSE_RESTRICTED_ROOT/releases/$SYSTEM_NAME/$TRIAL_RELEASE"
export PUBLISH_RELEASE_ROOT="$CSE_PUBLISHED_ROOT/releases/$SYSTEM_NAME/$TRIAL_RELEASE"
export BUILDCACHE_ROOT="$CSE_RESTRICTED_ROOT/buildcache/$SYSTEM_NAME/$TRIAL_RELEASE"
export BUILDCACHE_URL="file://$BUILDCACHE_ROOT"
export BUILD_EVIDENCE="$CSE_RESTRICTED_ROOT/evidence/$SYSTEM_NAME/$TRIAL_RELEASE"
export PUBLISH_EVIDENCE="$PUBLISH_RELEASE_ROOT/evidence"
export BUILD_VALUES="$SYSTEM_DIR/cse-trials-build-values.yaml"
export PUBLISH_VALUES="$SYSTEM_DIR/cse-trials-publish-values.yaml"

: "${WORKDIR:?WORKDIR must be set by the site environment}"
case "$WORKDIR" in
  /*) ;;
  *) echo "WORKDIR must be absolute: $WORKDIR" >&2; return 2 2>/dev/null || exit 2 ;;
esac

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
if [ ! -d "$SPACK_ROOT/.git" ]; then
  mkdir -p "$(dirname "$SPACK_ROOT")"
  git clone --branch "v$SPACK_VERSION" --depth 1 \
    https://github.com/spack/spack.git "$SPACK_ROOT"
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

Verify and activate the pinned Spack checkout selected for the trials:

```bash
git -C "$SPACK_ROOT" status --short --branch
test "$(git -C "$SPACK_ROOT" describe --tags --exact-match)" = "v$SPACK_VERSION"
source "$SPACK_ROOT/share/spack/setup-env.sh"
spack --version
```

Spack activation is local to the current shell. Repeat it after opening a new
shell. Steps 8 and 9 repeat the activation at the workspace execution boundary.

The trial workspace uses Spack 1.2 `group`, `needs`, and toolchains. Use Spack
1.2.2 for these trials. The Spack tool may live under
`$WORK_ROOT/spack/<version>` or come
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

Review compiler, MPI, accelerator, fabric, runtime, prefix, module,
compatibility, and node-role facts against the live machine. Accelerator facts
remain part of the system profile, but GPU builds are outside these trials. On
Cray systems, select one coherent CPE/compiler/Cray MPICH set. On generic Linux
systems, prove the
compiler pairing for the selected MPI. Preserve incorrect discovery evidence,
fix the inspector or hints, and regenerate. Do not hand-enter a guess as a
durable fact.

For Cray MPICH, retain the complete observed product-tree flavor map. A path
such as `ofi/gnu/12.3` records the GNU family and its minimum compiler baseline;
it does not require an installed `gcc@12.3` provider and it is not an exact pin
for the lane compiler. A platform or CSE-built compiler may use that flavor
only when it is the same family and its selected version is at or above the
baseline. The currently loaded/default PrgEnv is evidence to review, not a rule
that removes the other observed combinations.

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
  "$CSE_TRIAL_ROOT" \
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
Confirm external specs, prefixes, modules, compiler stamps, and MPI
requirements against the reviewed profile.

Gate: the catalog contains the exact compatible compiler, MPI, common, and
platform scopes needed by the trials. Fix the profile or catalog logic when a
scope is missing; do not type a nonexistent path into a values file.

On Cray systems, the common scope must contain the inspected platform
`libfabric` external. Each Cray MPICH scope must contain the selected
`cray-mpich` external and the inspected `cray-pmi` external. The pinned
`cray-mpich` recipe depends on both packages. Stop if either is absent; do not
allow Spack to substitute a source-built runtime for the active CPE.
`reports/static-plan.yaml` must show an empty `missing_mpi_dependencies` list.

### Static-catalog handoff without `init-workspace`

The catalog is already usable at this gate. A package manager can create an
ordinary Spack environment by including the exact generated scopes and writing
normal Spack specs. For example:

```yaml
spack:
  include::
    - /absolute/catalog/path/scopes/common
    - /absolute/catalog/path/scopes/compilers/<provider>/<version>
    - /absolute/catalog/path/scopes/mpi/<provider>/<version>/<compiler-axis>

  concretizer:
    unify: false

  specs:
    - hdf5@1.10.6+mpi %<compiler-plus-mpi-toolchain>
```

Use the toolchain name from the selected scope's `toolchains.yaml`; do not
retype compiler, MPI, external-prefix, or module policy in the environment.
For a Serial environment, omit the MPI scope and use the compiler-only
toolchain. This is the production purpose of `render-static`: its output is
independent of the CSE trial initializer.

## 7. Create the restricted build values

Set the small provider tuple selected during catalog review. The common runbook
does not infer this policy from the machine. The system note gives the exact
exports for the current trial selection.

Review the available node-type keys and their stage facts before selecting the
build node:

```bash
sed -n '/^  node_types:/,/^template_set:/p' "$CATALOG/manifest.yaml"
```

`shared` means the CSE-standard compiler surface within this system's
workspace. GCC 12.5.0 is standardized across the four systems, but the selected
MPI provider is system-specific: normally external Cray MPICH on Cray systems
and build-sourced OpenMPI on non-Cray systems. It does not mean that one binary
installation or one MPI provider is shared across all systems.

```bash
export CSE_SHARED_COMPILER_REF="gcc@12.5.0"
export CSE_SHARED_COMPILER_PUBLIC_NAME="<module-front-door-name>"
export CSE_SHARED_MPI_REF="<provider>@<version>"
export CSE_SHARED_MPI_SOURCE="<external|build>"
export CSE_PLATFORM_COMPILER_REF="<observed-provider>@<version>"
export CSE_PLATFORM_COMPILER_PUBLIC_NAME="<module-front-door-name>"
export CSE_PLATFORM_MPI_REF="<provider>@<version>"
export CSE_PLATFORM_MPI_SOURCE="<external|build>"
export CSE_BUILD_NODE_TYPE="<reviewed-profile-node-type>"
export BUILD_JOBS="<approved-job-count>"
```

Do not normally set `CSE_CPU_TARGET`. The helper selects the highest common
portable target, capped at `x86_64_v3`. Set it only when the team deliberately
chooses the lower `x86_64_v2` or `x86_64` baseline after reviewing the profile.

Generate the complete values file from those selections, the static catalog,
and the roots already exported in Step 1:

```bash
"$COMPOSER/.venv/bin/python" \
  "$CONTENT/pilots/cse-pilot/scripts/create-build-values.py"

sed -n '1,260p' "$BUILD_VALUES"
```

The helper expands `BUILD_RELEASE_ROOT`, `CSE_RESTRICTED_ROOT`, and
`BUILDCACHE_URL` into literal durable values. `${WORKDIR}` remains only in the
last build-stage fallback so the handoff uses the current builder's site work
directory; the generated setup script validates it before Spack runs.
It resolves the observed provider names to the catalog's Spack package names,
selects the compatible compiler/MPI scope, copies exact module prerequisites,
and fails if the named scope is absent. Do not type a guessed scope path into
the generated file.

The helper independently resolves one CPU target for all eight environments.
It intersects the detected, preferred, and alternate targets of every
CPU-only build/runtime node type, then selects `x86_64_v3`, `x86_64_v2`, or
`x86_64` in that order. This target is architecture policy; it is not derived
from `CSE_BUILD_NODE_TYPE`, and changing from a compute node to a login node
does not change it. The helper rejects a requested target that any relevant
node type cannot run. It also records the generic `x86_64` family target for
architecture-specific prebuilt distributions such as Miniforge.

`CSE_BUILD_NODE_TYPE` is the node class on which the builds will run, such as
`cpu_compute`. It must be an exact key under the catalog manifest's
`profile_facts.node_types`. The helper converts that reviewed choice into the
complete ordered `paths.build_stage` list. It keeps inspected writable,
executable candidates, puts temporary/node-local storage first, then other
inspected scratch paths, and adds `${WORKDIR}` last. Every path is namespaced
by the Spack user, system, and trial release. Do not type or approve one manual
stage path in place of this list.

| Values | Restricted build setting |
|---|---|
| `workspace.role` | `build` |
| system/release | current profile/catalog plus `TRIAL_RELEASE` |
| `shared.compiler` | GCC 12.5.0, `source: build`, plus the verified older compiler selected to build the GCC producer |
| compiler public names | generated CSE front-door names such as `init-GCC` and `init-CCE`; these do not replace the platform module chains copied from the catalog |
| `shared.mpi` | OpenMPI 4.1.8 built with GCC, or the selected compatible external MPI |
| `platform.compiler` | use the catalog manifest's observed provider name and exact version; the helper copies its Spack package name, module chain, and compiler scope path |
| `platform.mpi` | use the catalog manifest's Spack `package` name; build OpenMPI 4.1.8 on non-Cray systems, or select the matching external Cray MPICH 9.x/Intel MPI scope |
| `catalog_scopes.*` | exact relative paths below `$CATALOG` |
| install tree | `$BUILD_RELEASE_ROOT/spack/opt` |
| build node/stages | reviewed profile node type; generated temp, scratch, then `${WORKDIR}` fallback list |
| CPU architecture | one system-wide portable target for both compiler surfaces and all lanes; highest common support capped at `x86_64_v3` |
| source/misc caches | `$CSE_RESTRICTED_ROOT/cache/{source,misc}` |
| views/modules roots | `$BUILD_RELEASE_ROOT/{views,modules}` |
| build-cache name | `cse-initial-conversion-trials` |
| build-cache URL | `$BUILDCACHE_URL` expanded to an absolute `file:///...` URL |
| permissions | CSE group, group read, user write |
| package repository | reviewed trial recipe pin |

The roster installs CMake 3.31.12 and 4.4.2. CMake 3.31.12 is the preferred
build tool and is an explicit dependency of the CMake-built trial roots. CMake
4.4.2 is the second public version. Both versions come from the rendered local
recipe extension layered over `spack-packages v2026.06.0`.

The helper selects the newest verified older GCC compiler scope as the compiler
that builds the GCC 12.5.0 producer. Set `CSE_SHARED_COMPILER_SEED_REF` only to
choose a different reviewed compiler from the catalog. This is a compiler
dependency inside each GCC environment, not a separate preparatory environment
or user-facing surface. Every GCC producer root is the same explicit spec, so
all four GCC lockfiles must record the same hash.

For build-sourced OpenMPI, the helper converts verified common-scope facts into
one explicit spec. It selects UCX only when the catalog contains
`ucx+thread_multiple`; otherwise it selects verified libfabric/OFI. It selects
exactly one verified scheduler (`slurm` or `pbs`), enables Lustre/ROMIO only
when the Lustre development external is present, and never uses
`fabrics=auto`. Resolve an ambiguity with the documented `CSE_OPENMPI_*`
exports; do not depend on ambient configure detection.

Use `source: external` for the platform compiler and for platform-provided MPI.
Use `source: build` only for the selected MPI implementation that CSE will
build, such as OpenMPI on a non-Cray system. Do not insert dummy catalog scopes.

Observed provider names and Spack package names can differ. Classic Intel is
reported as `intel` under `scopes/compilers/intel/...`, but the values file uses
`intel-oneapi-compilers-classic`. Intel MPI is reported under
`scopes/mpi/intel-mpi/...`, but the values file uses `intel-oneapi-mpi`.

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

Initialization copies the rendered static catalog into
`$BUILD_WORKSPACE/catalog` and renders relative include paths. The resulting
workspace is the complete Spack build handoff; it does not depend on the
original `$CATALOG` path after initialization.

Use `--overwrite` only after reviewing and deliberately replacing the existing
workspace.

```bash
cat "$BUILD_WORKSPACE/README.md"
sed -n '1,260p' "$BUILD_WORKSPACE/workspace-manifest.yaml"
find "$BUILD_WORKSPACE/environments" -name spack.yaml -print | sort
find "$BUILD_WORKSPACE/catalog/scopes" -type f -print | sort
find "$BUILD_WORKSPACE/configs/environments" -name modules.yaml -print | sort
find "$BUILD_WORKSPACE/modulefiles" -type f -print | sort
cat "$BUILD_WORKSPACE/env/setup-build-env.sh"
cat "$BUILD_WORKSPACE/configs/common/config.yaml"
cat "$BUILD_WORKSPACE/configs/common/mirrors.yaml"
```

Verify every include path, provider selection, deployment path, native
`modules.yaml`, and private build-cache URL. Serial must contain no MPI scope.
Each MPI environment must use the MPI provider paired with its compiler
surface. Confirm `config.yaml` uses `build_stage::` in the intended order and
sets `locks: true`. Confirm it sets `deprecated: true`; this is required only
because the approved Python 3.8.20 root is marked deprecated in the pinned
package recipe.
Confirm `configs/common/packages.yaml` contains a `packages:all:prefer` entry
for the selected `target=...` and a `miniforge3:require` entry for generic
`target=x86_64`. No environment may replace either with a native or
compiler-specific CPU target. Inspect representative environment roots as
well: every source-built compiler, Foundation, Core/build-tool, MPI, and
payload root constraint must include the portable target. The Miniforge
Core-independent root must use the generic binary target. The explicit root
constraints prevent package-specific requirements from falling back to the
concretization host's native architecture.

The one workspace contains eight independent Spack environments:

1. GCC Core;
2. GCC Common;
3. GCC Serial;
4. GCC MPI;
5. platform-compiler Core;
6. platform-compiler Common;
7. platform-compiler Serial; and
8. platform-compiler MPI.

Common, Serial, and MPI are separate solves for each compiler surface. The
shared install tree and matching concrete hashes allow them to reuse the GCC,
Foundation, and build-tool producers without combining the two compiler
surfaces into one environment.

Checkpoint for the four-system work-tree pass: stop here after the workspace
and its eight environment/module files have been reviewed. Concretization,
installation, cache promotion, and publication are later checkpoints. A system
does not need to wait for another system's build before reaching this point.

This is also the no-build teammate handoff point. Copy or grant access to the
entire workspace, not an individual `spack.yaml`. A builder needs the pinned
Spack checkout, the platform module chain recorded in the workspace, and write
access to the approved restricted install/cache/stage paths. The builder does
not need Cluster Inspector, Stack Composer, Stack Content, or the original
static-catalog directory to execute the rendered handoff. The builder must have
an absolute writable `WORKDIR`; the generated setup script checks it before
Spack reads the final fallback path.

Snapshot the reviewed inputs and tool identities:

```bash
source "$SPACK_ROOT/share/spack/setup-env.sh"
test "$(spack --version)" = "$SPACK_VERSION"

mkdir -p "$BUILD_WORKSPACE/inputs"
cp "$SYSTEM_DIR/profile.yaml" "$BUILD_WORKSPACE/inputs/profile.yaml"
cp "$BUILD_VALUES" "$BUILD_WORKSPACE/inputs/cse-trials-build-values.yaml"
cp "$CATALOG/manifest.yaml" "$BUILD_WORKSPACE/inputs/catalog-manifest.yaml"
cp "$CATALOG/reports/static-plan.yaml" "$BUILD_WORKSPACE/inputs/static-plan.yaml"
git -C "$INSPECTOR" rev-parse HEAD > "$BUILD_WORKSPACE/inputs/cluster-inspector.commit"
git -C "$COMPOSER" rev-parse HEAD > "$BUILD_WORKSPACE/inputs/stack-composer.commit"
git -C "$CONTENT" rev-parse HEAD > "$BUILD_WORKSPACE/inputs/stack-content.commit"
spack --version > "$BUILD_WORKSPACE/inputs/spack.version"
```

Normal path: continue directly to Step 9. Use the optional build-node recovery
procedure only when changing the selected build node.

## 9. Concretize and review the restricted environments

There are two supported ownership choices:

- hand off at Step 8 and let the builder perform this entire step; or
- generate and review all eight locks, then hand the locked workspace to the
  builder for package installation.

Concretizing all eight environments does not install GCC first. Each GCC
environment repeats the same GCC 12.5 producer group and uses `needs` to bind
its Foundation, build-tool, and payload roots to that concrete language
provider. Exact matching specs produce exact matching hashes across the four
independent lockfiles.

Load the exact environment names generated from the reviewed values file:

Activate the pinned Spack checkout first. The generated workspace setup script
loads workspace values; it does not activate Spack.

```bash
source "$SPACK_ROOT/share/spack/setup-env.sh"
test "$(spack --version)" = "$SPACK_VERSION"

source "$BUILD_WORKSPACE/env/setup-build-env.sh"

ENVIRONMENTS=(
  "$SHARED_COMPILER_NAME/core"
  "$SHARED_COMPILER_NAME/common"
  "$SHARED_COMPILER_NAME/serial"
  "$SHARED_COMPILER_NAME/mpi-$SHARED_MPI_NAME"
  "$PLATFORM_COMPILER_NAME/core"
  "$PLATFORM_COMPILER_NAME/common"
  "$PLATFORM_COMPILER_NAME/serial"
  "$PLATFORM_COMPILER_NAME/mpi-$PLATFORM_MPI_NAME"
)
```

Concretize all restricted environments:

```bash
for environment in "${ENVIRONMENTS[@]}"; do
  echo "Concretizing $environment"
  spack -e "$BUILD_WORKSPACE/environments/$environment" \
    concretize --fresh -j 1 || break
done
```

Review every lock:

```bash
for environment in "${ENVIRONMENTS[@]}"; do
  test -f "$BUILD_WORKSPACE/environments/$environment/spack.lock" || break
  spack -e "$BUILD_WORKSPACE/environments/$environment" find -lv
done

python3 "$BUILD_WORKSPACE/scripts/verify-lockfiles.py"
```

Confirm that externals remain external, producer groups exist only where
intended, Serial contains no MPI, MPI preserves the selected toolchain, and
version-paired package roots preserve their pairings. Save solver output and fix
the owning profile, catalog, values, roster, or blueprint. Never patch a lock.

Confirm that the GCC producer, Foundation, and build-tool hashes are identical
across the four GCC lockfiles. Confirm that every CMake dependency selected for
the trial payload is CMake 3.31.12; CMake 4.4.2 should appear only as its
explicit public root. Confirm that Python 3.8.20, 3.10.20, and 3.12.13 are all
explicit Core roots. Miniforge is a compiler-independent Core root because its
Spack package declares no compiler-language dependency and installs a prebuilt
architecture-family binary. Do not force `%compiler` or the source-build
microarchitecture onto it; its concrete target must be generic `x86_64`.

Gate: all eight restricted lockfiles exist and pass review.

After this gate, the teammate builds the approved lockfiles without
reconcretizing them. A package build failure does not by itself authorize a new
solve. Diagnose and retry the same lock first. Reconcretize only when an owned
input or approved package/provider choice must change; then retain the failed
evidence, regenerate the affected locks, rerun lock verification, and follow
the same-release/new-release rule in the recovery section.

## 10. Build and exercise every restricted lane

Build in the listed order. GCC Core installs the repeated GCC, Foundation, and
Core roots first. Later GCC environments find the identical concrete hashes in
the shared install tree and reuse them. Platform Core establishes that
surface's Foundation and Core roots before its payload environments.

```bash
for environment in "${ENVIRONMENTS[@]}"; do
  echo "Building $environment"
  spack -e "$BUILD_WORKSPACE/environments/$environment" fetch -D || break
  spack -e "$BUILD_WORKSPACE/environments/$environment" \
    install --only-concrete -j "$BUILD_JOBS" --fail-fast || break
  spack -e "$BUILD_WORKSPACE/environments/$environment" \
    env view regenerate || break
  spack -e "$BUILD_WORKSPACE/environments/$environment" \
    module tcl refresh --delete-tree -y || break
done
```

Use sequential installation for the first pass. Concurrent Spack processes may
wait on and reuse the same concrete prefix only when they use the same store and
database, `config:locks:true`, and the actual shared filesystem honors `flock`.
Validate that behavior on the selected install root before enabling concurrent
lane installs; concurrent job counts are cumulative across Spack processes.

Apply the platform checklist after installation. A lane is not approved merely
because compilation finished. Exercise its compiler/wrappers, representative
libraries, module exposure, and applicable single-node and multi-node MPI
behavior on the target system.

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

Gate: the index verifies and every approved root/dependency needed by the eight
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

Gate: the publication workspace has the same eight concrete DAGs as the
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

Repeat separately for `MPI`. Loading a conflicting second lane must fail.
Verify package-module visibility after installation, view regeneration,
and module refresh. Apply `cray_pe_acceptance_checklist_v1.md` on Cray PE and
`generic_linux_acceptance_checklist_v1.md` on generic Linux.

Snapshot the publication inputs and provenance:

```bash
mkdir -p "$PUBLISH_WORKSPACE/inputs"
cp "$PUBLISH_VALUES" "$PUBLISH_WORKSPACE/inputs/cse-trials-publish-values.yaml"
cp "$BUILD_VALUES" "$PUBLISH_WORKSPACE/inputs/cse-trials-build-values.yaml"
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
