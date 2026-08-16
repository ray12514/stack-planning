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
  spack/<version>/                            # optional pinned builder-local Spack tool root
  probe-work/<system>/<catalog-release>/     # raw fragments/transcripts

<shared-cse-tools-root>/                     # installer/site controlled
  spack/<version>/                           # optional pinned, read-only shared Spack tool root

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

The Unix group is lowercase `cse` on every trial system. During the restricted
trials, both assigned builders need read/write access. Use
`permissions.group: cse`, `permissions.read: group`, and
`permissions.write: group`. Publication values instead use `read: world` and
`write: user`; after promotion and acceptance, consumers have read/execute but
no write access. Change the write or read audience only through an approved
release-policy decision.

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

The selected Spack tool root is not part of either package installation. A
builder may use the approved shared checkout or an identity-equivalent checkout
under that builder's home directory. Both use the same pinned version, tag,
commit, and clean source tree. Mutable builder cache/state and the GPG keyring
remain outside the selected checkout.

The catalog becomes read-only after review. The restricted workspace stays
operator-writable through lock generation and evidence capture. The published
workspace is initialized separately and is never allowed to build from source.

## Build and promotion gates

Do not advance past a failed gate.

- [ ] All four repositories are synchronized on
  `codex/simplified-render-plan`.
- [ ] Fresh Cluster Inspector and Stack Composer artifacts run.
- [ ] The selected shared or builder-local Spack tool root is the clean,
  expected Spack 1.2.2 tag and commit.
- [ ] Global and per-environment configuration-scope checks show no active
  unexpected user, system, or site policy.
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
  package-recipe pin, Spack version and commit, and repository commits are
  unchanged;
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

The Spack tool-root path is also operational. One builder may use the shared
root and another a builder-local root without changing the release when both
roots pass the same version, tag, commit, clean-tree, and scope checks. Record
the selected path with each builder's evidence.

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
| Package recipe, patch, variant, compiler, MPI, or Spack version/commit change is required | Create a new trial release, reconcretize, and revalidate every affected lane. |
| Selected Spack checkout is dirty or does not match the pinned source/tag/commit | Stop. Replace the selected root with a clean checkout of the approved identity. Do not pull, switch branches, or run `spack isolate` in place. |
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

"$CSE_PYTHON" \
  "$CONTENT/pilots/cse-pilot/scripts/create-build-values.py"

"$CSE_PYTHON" "$STACK_COMPOSER" init-workspace \
  --blueprint "$CONTENT/pilots/cse-pilot" \
  --catalog "$CATALOG" \
  --values "$BUILD_VALUES" \
  --output "$BUILD_WORKSPACE"

verify_spack_tool_root
source "$SPACK_ROOT/share/spack/setup-env.sh"
SPACK_VERSION_OUTPUT="$(spack --version)"
test "${SPACK_VERSION_OUTPUT%% *}" = "$SPACK_VERSION"
verify_spack_tool_root
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

"$CSE_PYTHON" "$BUILD_WORKSPACE/scripts/verify-lockfiles.py"
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

## Spack runtime options

The trial has one approved Spack runtime identity. For Spack 1.2.2, the
approved upstream tag resolves to commit
`3e19345b6e12f5ff1b874f4059622fc6a1fd804a`.

A builder may use either:

1. a shared checkout under an installer-selected CSE tools root; or
2. a builder-local checkout under `$HOME/STACK_TESTING/spack/1.2.2`.

The path may differ between builders. The version, tag, commit, and clean
source tree may not. Switching paths without changing that identity is an
operational change and does not require new lockfiles.

### Option A: provision the shared checkout

This is a separate setup operation. The installer/site owner or an authorized
CSE builder provisions one clean checkout for each approved Spack version.
Builders need read and execute access during normal builds. The selected root
must be visible at the same path from every login and build/compute node used on
that system.

A provisioning example is:

```bash
export CSE_TOOLS_ROOT="<installer-selected-shared-cse-tools-root>"
export CSE_GROUP="cse"
export SPACK_SOURCE="https://github.com/spack/spack.git"
export SPACK_VERSION="1.2.2"
export SPACK_TAG="v$SPACK_VERSION"
export SPACK_COMMIT="3e19345b6e12f5ff1b874f4059622fc6a1fd804a"
export SPACK_ROOT="$CSE_TOOLS_ROOT/spack/$SPACK_VERSION"

test ! -e "$SPACK_ROOT"
mkdir -p "$(dirname "$SPACK_ROOT")"
chgrp "$CSE_GROUP" "$(dirname "$SPACK_ROOT")"
chmod 2775 "$(dirname "$SPACK_ROOT")"
git clone --branch "$SPACK_TAG" --depth 1 \
  "$SPACK_SOURCE" "$SPACK_ROOT"
test "$(git -C "$SPACK_ROOT" rev-parse HEAD)" = "$SPACK_COMMIT"
test "$(git -C "$SPACK_ROOT" rev-parse "${SPACK_TAG}^{commit}")" = \
  "$SPACK_COMMIT"
test -z "$(git -C "$SPACK_ROOT" status --porcelain --untracked-files=all)"
test -z "$(git -C "$SPACK_ROOT" \
  ls-files --others --ignored --exclude-standard)"
chgrp -R "$CSE_GROUP" "$SPACK_ROOT"
chmod -R g+rX,o-rwx "$SPACK_ROOT"
chmod -R a-w "$SPACK_ROOT"
```

Record the root, tag, commit, source URL, owner, and provisioning date. Do not
run `spack isolate`, change `$SPACK_ROOT/etc/spack`, pull, switch branches, or
install another Spack version over this directory. Provision a sibling such as
`spack/1.3.x` and review it as a release/DAG-significant change.

### Option B: provision a builder-local checkout

Each builder may instead provision the same approved identity under that
builder's home directory:

```bash
export WORK_ROOT="$HOME/STACK_TESTING"
export SPACK_SOURCE="https://github.com/spack/spack.git"
export SPACK_VERSION="1.2.2"
export SPACK_TAG="v$SPACK_VERSION"
export SPACK_COMMIT="3e19345b6e12f5ff1b874f4059622fc6a1fd804a"
export SPACK_ROOT="$WORK_ROOT/spack/$SPACK_VERSION"

test ! -e "$SPACK_ROOT"
mkdir -p "$(dirname "$SPACK_ROOT")"
git clone --branch "$SPACK_TAG" --depth 1 \
  "$SPACK_SOURCE" "$SPACK_ROOT"
test "$(git -C "$SPACK_ROOT" rev-parse HEAD)" = "$SPACK_COMMIT"
test "$(git -C "$SPACK_ROOT" rev-parse "${SPACK_TAG}^{commit}")" = \
  "$SPACK_COMMIT"
test -z "$(git -C "$SPACK_ROOT" status --porcelain --untracked-files=all)"
test -z "$(git -C "$SPACK_ROOT" \
  ls-files --others --ignored --exclude-standard)"
```

The local checkout remains writable by its owner, but do not edit, pull,
switch, or add configuration to it while the trial release is active. A
different builder may use a different local path only when the identity checks
above match.

Neither tool-root option is the restricted package install tree, the published
package install tree, a workspace, a build stage, a cache/buildcache, a view,
or a module root.

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
export SPACK_RUNTIME_MODE="<shared-or-local>"
export CSE_TOOLS_ROOT="<installer-selected-shared-cse-tools-root>" # recorded for both modes

export INSPECTOR="$WORK_ROOT/cluster-inspector"
export COMPOSER="$WORK_ROOT/stack-composer"
export CONTENT="$WORK_ROOT/stack-content"
export PLANNING="$WORK_ROOT/stack-planning"
export SPACK_SOURCE="https://github.com/spack/spack.git"
export SPACK_VERSION="1.2.2"
export SPACK_TAG="v$SPACK_VERSION"
export SPACK_COMMIT="3e19345b6e12f5ff1b874f4059622fc6a1fd804a"
case "$SPACK_RUNTIME_MODE" in
  shared) export SPACK_ROOT="$CSE_TOOLS_ROOT/spack/$SPACK_VERSION" ;;
  local)  export SPACK_ROOT="$WORK_ROOT/spack/$SPACK_VERSION" ;;
  *) echo "SPACK_RUNTIME_MODE must be shared or local" >&2; return 2 2>/dev/null || exit 2 ;;
esac
export SPACK_DISABLE_LOCAL_CONFIG=true
export PYTHONDONTWRITEBYTECODE=1
export SYSTEM_DIR="$CONTENT/systems/$SYSTEM_NAME"
export PROBE_DIR="$WORK_ROOT/probe-work/$SYSTEM_NAME/$CATALOG_RELEASE"
export STACK_COMPOSER="$COMPOSER/dist/stack-composer.pyz"
export CSE_BOOTSTRAP_PYTHON="<absolute-path-to-reviewed-python-3.9-or-newer>"
export CSE_PYTHON="$COMPOSER/.venv/bin/python"

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

if [ -n "${SPACK_ENV:-}" ]; then
  echo "start from a shell with no active Spack environment: $SPACK_ENV" >&2
  return 2 2>/dev/null || exit 2
fi

: "${WORKDIR:?WORKDIR must be set by the site environment}"
: "${USER:?USER must be set}"
case "$WORKDIR" in
  /*) ;;
  *) echo "WORKDIR must be absolute: $WORKDIR" >&2; return 2 2>/dev/null || exit 2 ;;
esac

export SPACK_USER_STATE_ROOT="$WORKDIR/$USER/cse-spack/$SYSTEM_NAME/$SPACK_VERSION"
export SPACK_USER_CACHE_PATH="$SPACK_USER_STATE_ROOT/cache"
export SPACK_GNUPGHOME="$SPACK_USER_STATE_ROOT/gpg"

for forbidden_root in \
  "$SPACK_ROOT" \
  "$BUILD_RELEASE_ROOT/spack/opt" \
  "$PUBLISH_RELEASE_ROOT/spack/opt"; do
  case "$SPACK_USER_STATE_ROOT" in
    "$forbidden_root"|"$forbidden_root"/*)
      echo "per-user Spack state is inside a forbidden root: $forbidden_root" >&2
      return 2 2>/dev/null || exit 2
      ;;
  esac
done

verify_shared_spack_root_read_only() {
  local path
  while IFS= read -r -d '' path; do
    if [ -w "$path" ]; then
      echo "shared Spack tool root is writable: $path" >&2
      return 1
    fi
  done < <(find "$SPACK_ROOT" -xdev -print0)
}

verify_spack_tool_root() {
  test -d "$SPACK_ROOT/.git" || return 1
  test "$(git -C "$SPACK_ROOT" remote get-url origin)" = \
    "$SPACK_SOURCE" || return 1
  test "$(git -C "$SPACK_ROOT" rev-parse HEAD)" = "$SPACK_COMMIT" || return 1
  test "$(git -C "$SPACK_ROOT" rev-parse "${SPACK_TAG}^{commit}")" = \
    "$SPACK_COMMIT" || return 1
  test -z "$(GIT_OPTIONAL_LOCKS=0 git -C "$SPACK_ROOT" \
    status --porcelain --untracked-files=all)" || return 1
  test -z "$(git -C "$SPACK_ROOT" \
    ls-files --others --ignored --exclude-standard)" || return 1
  if [ "$SPACK_RUNTIME_MODE" = shared ]; then
    verify_shared_spack_root_read_only
  fi
}

verify_workspace_scopes() {
  local workspace="$1"
  local evidence_root="$2"
  local environment_dir label evidence scope_output scope_path
  local generated_scope_count environment_count=0

  mkdir -p "$evidence_root"
  scope_output="$(COLUMNS=512 spack config scopes -vp)" || return 1
  printf '%s\n' "$scope_output" | tee "$evidence_root/global.txt"
  if grep -Eq \
    '^(user|system)[[:space:]]+[^[:space:]]+[[:space:]]+active([[:space:]]|$)' \
    "$evidence_root/global.txt"; then
    echo "unexpected active user/system Spack configuration scope" >&2
    return 1
  fi

  for environment_dir in "$workspace"/environments/*/*; do
    test -f "$environment_dir/spack.yaml" || continue
    environment_count=$((environment_count + 1))
    label="${environment_dir#"$workspace/environments/"}"
    label="${label//\//-}"
    evidence="$evidence_root/$label.txt"

    scope_output="$(COLUMNS=512 spack -e "$environment_dir" \
      config scopes -vp)" || return 1
    printf '%s\n' "$scope_output" | tee "$evidence"

    if grep -Eq \
      '^(user|system|site)[[:space:]]+[^[:space:]]+[[:space:]]+active([[:space:]]|$)' \
      "$evidence"; then
      echo "unexpected active ambient scope in $environment_dir" >&2
      return 1
    fi

    generated_scope_count="$(awk -v root="$workspace/" \
      '$2 ~ /include/ && $3 == "active" && index($4, root) == 1 {count++} \
       END {print count + 0}' "$evidence")"
    test "$generated_scope_count" -gt 0 || {
      echo "no active workspace include scope in $environment_dir" >&2
      return 1
    }

    while IFS= read -r scope_path; do
      case "$scope_path" in
        "$workspace"/*|"$SPACK_ROOT"/etc/spack/defaults/*) ;;
        *)
          echo "unexpected active include path in $environment_dir: $scope_path" >&2
          return 1
          ;;
      esac
    done < <(awk '$2 ~ /include/ && $3 == "active" {print $4}' "$evidence")
  done

  test "$environment_count" -gt 0 || {
    echo "no Spack environments found under $workspace" >&2
    return 1
  }
}

install -d -m 0700 "$SPACK_USER_CACHE_PATH" "$SPACK_GNUPGHOME"
mkdir -p "$WORK_ROOT" "$PROBE_DIR"
```

The state-root example is both user- and system-specific. A site may choose a
different approved work or scratch root, but the result must be absolute,
unique to `$USER`, writable by that builder, and outside the shared tool and
package trees. Keep the GPG home private (`0700`) and persistent for as long as
the release signing/trust record is needed. `SPACK_USER_CACHE_PATH` does not
relocate Spack's GPG keyring, so `SPACK_GNUPGHOME` is required separately.
`PYTHONDONTWRITEBYTECODE=1` also prevents Python from attempting to create
ignored bytecode caches inside the selected checkout.

If the selected root does not exist, provision it with Option A or Option B
above before Step 3. Do not fall back to another Spack found on `PATH`.

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

Do not update Spack while synchronizing the four project repositories. The
selected shared or local tool root is provisioned separately under the runtime
options above. Stop if it is missing or fails identity verification.

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
test -x "$CSE_BOOTSTRAP_PYTHON"
"$CSE_BOOTSTRAP_PYTHON" -c \
  'import sys; assert sys.version_info >= (3, 9), sys.version'
"$CSE_BOOTSTRAP_PYTHON" -m venv .venv
test -x "$CSE_PYTHON"
"$CSE_PYTHON" -m pip install --upgrade pip
"$CSE_PYTHON" -m pip install -e '.[dev]'
PYTHON="$CSE_PYTHON" bash scripts/build-pyz.sh
"$CSE_PYTHON" "$STACK_COMPOSER" --help >/dev/null
```

`CSE_BOOTSTRAP_PYTHON` is the reviewed site- or module-provided interpreter
used only to create the virtual environment. From this point onward, invoke
every project Python command through the absolute `CSE_PYTHON` path. Do not
depend on whichever `python` or `python3` happens to be first on `PATH`. In a
new shell, Step 1 restores the same path. Rebuild the virtual environment only
when its bootstrap interpreter or Stack Composer dependencies must change.

Verify and activate the pinned Spack checkout selected for the trials:

```bash
verify_spack_tool_root
source "$SPACK_ROOT/share/spack/setup-env.sh"
SPACK_VERSION_OUTPUT="$(spack --version)"
test "${SPACK_VERSION_OUTPUT%% *}" = "$SPACK_VERSION"
verify_spack_tool_root

COLUMNS=512 spack config scopes -vp | tee "$PROBE_DIR/spack-scopes.global.txt"
if grep -Eq \
  '^(user|system)[[:space:]]+[^[:space:]]+[[:space:]]+active([[:space:]]|$)' \
  "$PROBE_DIR/spack-scopes.global.txt"; then
  echo "unexpected active user/system Spack configuration scope" >&2
  return 2 2>/dev/null || exit 2
fi
```

Spack activation is local to the current shell. Repeat it after opening a new
shell. Steps 8 and 9 repeat the activation at the workspace execution boundary.

The global scope listing still shows the stock checkout-local `site` scope.
The clean pinned checkout proves it contains no added site policy, and each
generated environment's `include::` boundary overrides it. Step 8 verifies the
environment-scoped result and fails if `user`, `system`, or `site` is active.
The tool-root check examines ignored as well as ordinary untracked files;
Spack's upstream `.gitignore` otherwise hides local `etc/spack` configuration
and runtime caches from a normal clean-status check.

The trial workspace uses Spack 1.2 `group`, `needs`, and toolchains. Use Spack
1.2.2 at the approved commit for these trials. Builders may source different
shared/local paths only when `verify_spack_tool_root` proves the same runtime
identity. The selected root is distinct from both Spack package install trees
and from each builder's `SPACK_USER_CACHE_PATH` and `SPACK_GNUPGHOME`.

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

Confirm the exact CSE group and shared path with the filesystem owner. Use a
group-collaborative umask and setgid directories so new artifacts inherit the
CSE group and both assigned builders can update them:

```bash
umask 0007

install -d -m 2770 -g "$CSE_GROUP" \
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
  "$BUILD_EVIDENCE"

# Consumers may traverse published namespaces, but only CSE may add releases.
install -d -m 2775 -g "$CSE_GROUP" \
  "$CSE_PUBLISHED_ROOT" \
  "$CSE_PUBLISHED_ROOT/workspaces" \
  "$CSE_PUBLISHED_ROOT/workspaces/$SYSTEM_NAME" \
  "$CSE_PUBLISHED_ROOT/workspaces/$SYSTEM_NAME/initial-conversion-trials" \
  "$CSE_PUBLISHED_ROOT/releases" \
  "$CSE_PUBLISHED_ROOT/releases/$SYSTEM_NAME"

# Publication assembly remains private until validation and the final freeze.
install -d -m 2770 -g "$CSE_GROUP" \
  "$PUBLISH_RELEASE_ROOT" \
  "$PUBLISH_RELEASE_ROOT/spack/opt" \
  "$PUBLISH_RELEASE_ROOT/cache/misc" \
  "$PUBLISH_RELEASE_ROOT/views" \
  "$PUBLISH_RELEASE_ROOT/modules" \
  "$PUBLISH_EVIDENCE"
```

Do not recursively change ownership or permissions on an existing shared tree.
If the top-level path is site-owned, ask its owner to create the dedicated roots.
The `s` shown in a directory mode is setgid: it provides group inheritance but
does not provide group write permission. Do not add the sticky bit inside the
restricted workspace, Spack store, caches, build cache, views, or module roots.
Spack and the handoff scripts must be able to rename and clean entries created
by either builder. Protect against accidental deletion with the restricted/
published boundary, release snapshots, evidence, and backups instead.

If a dedicated trial tree was previously created with group read-only modes,
stop all Spack processes and have its owner or filesystem administrator repair
only that confirmed tree. Set group `cse`, add group read/write/search, remove
access for others, and restore setgid on every directory. Use a default ACL for
group `cse` when the filesystem supports it; otherwise every builder must keep
`umask 0007`. Do not apply a recursive command to `/p/app/CSE` or another
shared parent containing unrelated releases.

## 6. Generate and inspect the static catalog

```bash
"$CSE_PYTHON" "$STACK_COMPOSER" render-static \
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
`cray-mpich` external and the inspected `cray-pmi` external. These records
preserve and validate the active CPE runtime inventory. The selected Cray MPICH
external itself remains a platform leaf: do not add compiler, target,
`libfabric`, or `cray-pmi` dependency constraints to its external spec. Stop if
either runtime record is absent; do not allow Spack to substitute a
source-built runtime for the active CPE.
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
"$CSE_PYTHON" \
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

The helper independently resolves one CPU target for all source-built roots in
the eight environments.
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
| CPU architecture | one system-wide portable target for source-built roots on both compiler surfaces and all lanes; highest common support capped at `x86_64_v3`; inspected platform externals retain their own architecture |
| source/misc caches | `$CSE_RESTRICTED_ROOT/cache/{source,misc}` |
| views/modules roots | `$BUILD_RELEASE_ROOT/{views,modules}` |
| build-cache name | `cse-initial-conversion-trials` |
| build-cache URL | `$BUILDCACHE_URL` expanded to an absolute `file:///...` URL |
| permissions | CSE group read/write in the restricted tree; publication values change to consumer read/execute with no group/other write and are frozen after acceptance |
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
"$CSE_PYTHON" "$STACK_COMPOSER" init-workspace \
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
test -x "$BUILD_WORKSPACE/cse-build"
test -r "$BUILD_WORKSPACE/BUILDER-HANDOFF.md"
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

For an external MPI provider, inspect the applicable surface
`packages.yaml`. Its virtual `mpi:require` entry must select only the provider
and version, for example `cray-mpich@9.1.0`; it must not append the portable
source-build target. The platform external keeps the architecture Spack assigns
to its inspected installation. A build-sourced provider such as OpenMPI does
include the portable target.

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

This is the earliest builder handoff point. The same handoff procedure also
applies after concretization or partway through installation. Copy or grant
access to the entire workspace, not an individual `spack.yaml`. A builder needs
the approved Spack runtime, the platform module chain recorded in the
workspace, and write access to the approved restricted install/cache/stage
paths. The builder does not need Cluster Inspector, Stack Composer, Stack
Content, or the original static-catalog directory to execute the rendered
handoff. The builder must have an absolute writable `WORKDIR`; the generated
setup script checks it before Spack reads the final fallback path.

Snapshot the reviewed inputs and tool identities:

```bash
verify_spack_tool_root
source "$SPACK_ROOT/share/spack/setup-env.sh"
SPACK_VERSION_OUTPUT="$(spack --version)"
test "${SPACK_VERSION_OUTPUT%% *}" = "$SPACK_VERSION"
verify_spack_tool_root

verify_workspace_scopes \
  "$BUILD_WORKSPACE" \
  "$BUILD_EVIDENCE/config-scopes"

mkdir -p "$BUILD_WORKSPACE/inputs"
cp "$SYSTEM_DIR/profile.yaml" "$BUILD_WORKSPACE/inputs/profile.yaml"
cp "$BUILD_VALUES" "$BUILD_WORKSPACE/inputs/cse-trials-build-values.yaml"
cp "$CATALOG/manifest.yaml" "$BUILD_WORKSPACE/inputs/catalog-manifest.yaml"
cp "$CATALOG/reports/static-plan.yaml" "$BUILD_WORKSPACE/inputs/static-plan.yaml"
git -C "$INSPECTOR" rev-parse HEAD > "$BUILD_WORKSPACE/inputs/cluster-inspector.commit"
git -C "$COMPOSER" rev-parse HEAD > "$BUILD_WORKSPACE/inputs/stack-composer.commit"
git -C "$CONTENT" rev-parse HEAD > "$BUILD_WORKSPACE/inputs/stack-content.commit"
spack --version > "$BUILD_WORKSPACE/inputs/spack.version"
printf '%s\n' "$SPACK_SOURCE" \
  > "$BUILD_WORKSPACE/inputs/spack.source"
printf '%s\n' "$SPACK_TAG" \
  > "$BUILD_WORKSPACE/inputs/spack.tag"
git -C "$SPACK_ROOT" rev-parse HEAD \
  > "$BUILD_WORKSPACE/inputs/spack.commit"
printf '%s\n' "$SPACK_RUNTIME_MODE" \
  > "$BUILD_WORKSPACE/inputs/spack.concretizer-runtime-mode"
printf '%s\n' "$SPACK_ROOT" \
  > "$BUILD_WORKSPACE/inputs/spack.concretizer-root"
```

In Spack 1.2.2, `SPACK_DISABLE_LOCAL_CONFIG` removes the `user` and `system`
scopes. It does not by itself remove the checkout-local `site` scope. The
generated `include::` list overrides that scope for each environment. The
checks above prove the combined boundary: no ambient user/system/site scope is
active, and every active include path is either workspace-owned or a stock
Spack defaults scope. The structural `spack` scope and `_builtin` scope remain
visible and are expected for a clean pinned checkout.

Gate: every environment passes the configuration-scope check, and the scope
evidence is retained with the restricted build evidence.

### Builder resume handoff

The handoff is the complete shared workspace plus its current checkpoint. It is
not a copy of one `spack.yaml`, and it does not require the receiving builder to
recreate the generating tools. Before another builder takes over, record:

- whether the handoff stops before concretization, after lock verification, in
  the middle of installation, or after lane validation;
- the last environment attempted and its result;
- the exact workspace and evidence paths;
- the approved Spack version, tag, and commit from `inputs/spack.*`;
- the selected Spack runtime mode and root, plus the shared root when one is
  available; and
- whether the receiving builder is authorized to sign and push build-cache
  content.

The receiving builder goes to the workspace root and runs:

```bash
./cse-build
```

No system, release, compiler, MPI, catalog, install-tree, view, module, or
environment values are entered. The generated entry point reads the recorded
workspace data, selects or provisions the exact approved shared or local Spack
checkout, creates private cache/keyring paths for the current builder,
activates the generated configuration, reports the lock checkpoint, and
creates or reattaches a tmux session for this system and release. Running the
same command after a disconnect reattaches on the same host. Use
`./cse-build shell` to bypass tmux. If tmux is unavailable, the command falls
back to the prepared shell.

When the locks already exist, the receiving builder does not need Cluster
Inspector, Stack Composer, Stack Content, Stack Planning, or the original
catalog location. The catalog snapshot, configuration scopes, environment YAML,
lockfiles, deployment paths, module policy, and build-cache URL are inside the
workspace. The builder supplies only the site-provided absolute `WORKDIR` and
may explicitly choose `--spack-mode shared` or `--spack-mode local`; otherwise
the recorded automatic policy selects the runtime. Per-user cache and keyring
locations are derived automatically.

Rerunning `spack install --only-concrete` is the normal resume operation.
Already installed hashes are reused from the shared restricted store. An
unfinished package is staged under the receiving builder's stage path. Do not
reconcretize merely because the builder or Spack root path changed.

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

The normal builder path is:

```bash
cd "$BUILD_WORKSPACE"
./cse-build concretize
```

This creates only missing lockfiles, preserves locks already handed over, and
runs the lock verifier when all eight exist. The explicit commands below are
the operator inspection and troubleshooting form of the same process.

Activate the pinned Spack checkout first. The generated workspace setup script
loads workspace values; it does not activate Spack.

```bash
verify_spack_tool_root
source "$SPACK_ROOT/share/spack/setup-env.sh"
SPACK_VERSION_OUTPUT="$(spack --version)"
test "${SPACK_VERSION_OUTPUT%% *}" = "$SPACK_VERSION"
verify_spack_tool_root

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

"$CSE_PYTHON" "$BUILD_WORKSPACE/scripts/verify-lockfiles.py"
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

On a login node with outbound network access, prefetch all locked sources:

```bash
cd "$BUILD_WORKSPACE"
./cse-build fetch
```

On the selected build node, enter or reattach the release tmux session and run
the installation action:

```bash
cd "$BUILD_WORKSPACE"
./cse-build
./cse-build install
```

The explicit loop below is the operator inspection and troubleshooting form of
the same sequential installation.

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
| `permissions.read` | `world` so authenticated system users can consume the release |
| `permissions.write` | `user`; consumers and the CSE group cannot modify installed prefixes |

Keep the system, release, package/provider data, catalog scopes, package recipe
pin, collaboration group, and private build-cache URL identical. Permission
audience is the deliberate exception: restricted values are group-writable,
whereas publication values are consumer-readable and owner-writable.

```bash
"$CSE_PYTHON" "$STACK_COMPOSER" init-workspace \
  --blueprint "$CONTENT/pilots/cse-pilot" \
  --catalog "$CATALOG" \
  --values "$PUBLISH_VALUES" \
  --output "$PUBLISH_WORKSPACE"
```

Inspect the publication README, manifest, configs, modules, and mirror. Confirm
that all deployment paths are published paths and that the mirror still points
to the approved private CSE build cache.

Verify the same configuration boundary before copying locks or installing:

```bash
verify_spack_tool_root
source "$SPACK_ROOT/share/spack/setup-env.sh"
SPACK_VERSION_OUTPUT="$(spack --version)"
test "${SPACK_VERSION_OUTPUT%% *}" = "$SPACK_VERSION"
verify_spack_tool_root
verify_workspace_scopes \
  "$PUBLISH_WORKSPACE" \
  "$PUBLISH_EVIDENCE/config-scopes"
```

Gate: every publication environment has only the expected workspace/defaults
configuration boundary. Retain the scope listings with publication evidence.

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
printf '%s\n' "$SPACK_TAG" \
  > "$PUBLISH_WORKSPACE/inputs/spack.tag"
git -C "$SPACK_ROOT" rev-parse HEAD \
  > "$PUBLISH_WORKSPACE/inputs/spack.commit"
```

After every validation passes, freeze the exact publication workspace and
release. These commands apply only to the resolved publication targets; never
run them against `$CSE_PUBLISHED_ROOT`, `/p/app/CSE`, or another shared parent:

```bash
for root in "$PUBLISH_WORKSPACE" "$PUBLISH_RELEASE_ROOT"; do
  test -n "$root" && test -d "$root" || exit 1
  case "$root" in
    "$CSE_PUBLISHED_ROOT"/*) ;;
    *) echo "refusing unexpected publication root: $root" >&2; exit 1 ;;
  esac
  find "$root" -xdev -type d \
    -exec chmod u+rwx,go+rx,go-w {} + || exit 1
  find "$root" -xdev -type f \
    -exec chmod u+rw,go+r,go-w {} + || exit 1
done
```

This preserves execute bits already present on programs, makes ordinary files
readable, gives users search access to directories, and removes group/other
write. The release owner retains write for administrative removal or
deprecation, but policy forbids editing an accepted version in place. Confirm
the modes from a non-CSE test account before exposing the module front door.

The release becomes user-facing only after the build-cache-only install, hash
comparison, clean-shell module checks, target runtime checks, permission check,
and release-owner approval all pass. Freeze the approved release instead of
editing it in place. A later `current` pointer or wider audience is a release
operation, not part of `render-static` or `init-workspace`.

## Artifact ownership

| Artifact | Location and treatment |
|---|---|
| Cluster Inspector, Stack Composer, Stack Content, and Stack Planning checkouts and built executables | Operator home; mutable and operator-controlled |
| Shared pinned Spack tool root | Optional installer-selected shared tools tree; exact tag/commit; read/execute for builders; no build outputs or mutable builder state |
| Builder-local pinned Spack tool root | Optional builder-owned home checkout; same exact tag/commit; clean and unchanged during the active release |
| Per-builder Spack cache and GPG home | Approved user-specific work/scratch path outside the selected Spack tool and package trees; private and mutable |
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
