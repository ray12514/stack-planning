# CSE Initial Conversion Trials Runbook

## Purpose

Use the [shared Spack procedure](software_stack_sop_v1.md) for common operating
steps and the [CSE SOP](cse_software_stack_sop_v1.md) for CSE policy, review, and
acceptance choices. This runbook supplies the Initial Conversion Trials tool
commands, orchestration, and recovery details within those gates. Source
mirrors and delivery to systems with limited or no external network access use
the shared procedure's
[mirror](software_stack_sop_v1.md#procedure-source-mirrors) and
[transfer](software_stack_sop_v1.md#procedure-disconnected-transfer) sections;
system notes identify the applicable paths and approved transfer route.

For deciding whether a failure requires a variant/configuration change, a
recipe overlay, or operational recovery, use the
[package correction and lifecycle map](package_overlay_operating_model_v1.md).
It connects shared SOP Section 7.6 and CSE SOP Section 7.3 to the authored and
deployed paths, evidence requirements, and outstanding acceptance gates.
The [failure/recovery and test matrix](stack_failure_recovery_and_test_matrix_v1.md)
identifies the SOP stage to revisit after variant/version/recipe changes or
build/publication failures, and distinguishes tested controls from missing
end-to-end recovery coverage across all three preparation paths.

For a manual package correction during an unfinished trial, start with the
[offline overlay quickstart in Stack Content](../../stack-content/pilots/cse-pilot/templates/PACKAGE-OVERLAY-QUICKSTART.md).
It covers finding the pinned original `package.py`, the deployed overlay,
inputs for an on-site agent or human, a direct Spack retry, and copying a
validated correction to another workspace without Git. The
[detailed overlay workflow](../../stack-content/pilots/cse-pilot/PACKAGE-OVERLAY-WORKFLOW.md)
also gives commands for bringing only the guide into an existing workspace.
These links assume sibling `stack-planning` and `stack-content` checkouts.
The generated workspace carries its own `PACKAGE-OVERLAY-QUICKSTART.md` for
offline use; a healthy existing workspace can receive that file by manual copy.
The guide's common procedure is package- and system-independent; Blueback CCE
netlib-lapack is a worked example. Its opening update table identifies the
destination for documentation, a package overlay, or generated controls.
Copying an overlay also requires checking recipe selection, recovering affected
candidate locks, and testing on the receiving system; a source-repository pull
alone does not update a generated workspace.

The quickstart corrects the same unfinished workspace. Preserve the previous
inputs and selected lock in a recovery record; invalidate and repeat the affected
checkpoint-4 lock review after reconcretization. Follow
[Same release or new release](#same-release-or-new-release) to preserve accepted
or published releases.
For a partially completed workspace, preserve completed environments and
limit recovery to the declared failing candidate and reviewed dependency
impact. A documentation, overlay, or generated-control refresh is not an
instruction to rerender or reconcretize all environments. The
[active-trial boundary](package_overlay_operating_model_v1.md#active-trial-boundary-finish-the-two-remaining-cce-systems)
records the current focus on the two unfinished CCE systems and separates
those corrections from later production improvements.

Stack Planning owns this overall process and its release boundaries. The
operational recipe guide lives in Stack Content beside the recipes and
workspace templates it describes. The guide separates manual commands from
optional helpers; changing a package does not require running the full
`cse-build` installation loop.

This is the system-neutral operator procedure for moving one reviewed Spack
1.2 workspace through the complete sequence:

```text
operator-controlled tools and source
  -> reviewed profile.yaml
  -> restricted render-static catalog
  -> restricted CSE build workspace
  -> approved lockfiles
  -> concretize and build from source in the restricted release
  -> exercise each lane on the target system
  -> private CSE build cache
  -> publish the retained static catalog for non-CSE consumers
  -> create a separate CSE publication workspace from the restricted catalog
  -> copy the same approved lockfiles
  -> cache-only installation
  -> published views and modules
```

The restricted build and shared publication are two installations of the same
approved concrete DAG. Publication is not a second independent solve or source
build. The validated `spack.lock` files cross the boundary, and the publication
install uses `--only-concrete --use-buildcache=only`. A missing binary stops
promotion.

Both CSE workspaces use the retained restricted catalog. The public static
catalog is a separate configuration release for package managers outside CSE.
It is not substituted into the CSE build or publication workspace. Promoting
the CSE stack means carrying the approved lockfiles across the seam and
installing their exact binaries from the private build cache; it does not mean
copying the mutable restricted workspace into the public release.

`render-static` creates reusable platform scopes. A package manager may include
those scopes from a hand-authored `spack.yaml`. `init-workspace` is the CSE
trial convenience that combines an exact catalog selection with the authored
Initial Conversion Trials blueprint; it is not required to consume the static
catalog.

The rationale for the eight-environment layout, hash-sharing rules, parallel
install boundary, generated lock verifier, and shared-builder permission
contract is recorded in
`initial_conversion_trials_build_execution_model_v1.md`.

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

## System-specific inputs

Before starting, read `stack-content/systems/<system>/runbook-notes.md` for the
selected system. That file owns provider selections, site paths, scheduler and
network constraints, recovery state, and platform acceptance deltas. This
common procedure does not prescribe a system order or duplicate those values.

Every compiler, MPI, prefix, and module value must come from the live system's
reviewed profile, generated catalog, and system notes. Workspaces on different
systems are independent unless an approved binary-transfer procedure says
otherwise.

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
  operator-sessions/<system>/<trial>/         # sourceable pre-workspace resume state
  probe-work/<system>/<catalog-release>/     # raw fragments/transcripts

<shared-cse-tools-root>/                     # installer/site controlled
  spack/<version>/                           # optional pinned, read-only shared Spack tool root

<cse-trial-root>/                            # shared filesystem; recorded CSE group
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
    catalogs/<system>/static/<catalog-release>/ # approved, world-readable config release
    catalogs/<system>/static/current         # optional discovery pointer
    workspaces/<system>/initial-conversion-trials/<trial-release>/
    releases/<system>/<trial-release>/
      spack/opt/                              # populated from build cache only
      views/                                  # user-facing views
      modules/                                # user-facing package modules
      evidence/

<node-local-or-site-scratch>/
  <user>/<system>/<trial-release>/{build,publish}-stage/
```

The installer explicitly records the CSE Unix group for each trial system;
the current value is `cse`, and the tooling does not supply a default. During
the restricted trials, all assigned builders need read/write access. Use that
recorded group with `permissions.read: group` and `permissions.write: group`.
Publication values use `read: world` and `write: group`. CSE package managers
retain read, write, and execute access; consumers outside the CSE group receive
read and execute access without write access. Change the group or the
read/write audience only through an approved release-policy decision.

The private build cache is private because of filesystem or service access
controls. Spack's `buildcache push --private` option concerns redistribution of
non-redistributable packages; it is not an access-control mechanism.

Generate catalogs and workspaces directly at their final paths. Both CSE
workspaces are initialized from the reviewed restricted catalog. Each
initialized workspace snapshots that catalog configuration and uses relative
`include::` paths for its catalog and workspace-owned scopes. The whole
workspace can therefore be handed to another builder or archived without
depending on the original catalog path. Deployment paths inside `config.yaml`
remain deliberate absolute paths and must still name the approved shared trees.
Build stages are disposable and belong on node-local or site scratch.

The selected Spack tool root is not part of either package installation. A
builder may use the approved shared checkout or an identity-equivalent checkout
under that builder's home directory. Both use the same pinned version, tag,
commit, and clean source tree. Mutable builder cache/state and the GPG keyring
remain outside the selected checkout.

The restricted catalog becomes read-only after review and remains the retained
CSE source for workspace initialization. The restricted workspace stays
operator-writable through lock generation and evidence capture. The publication
workspace is initialized separately from the same restricted catalog and is
never allowed to build from source. Public static-catalog publication does not
replace or remove the restricted catalog.

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
  every profiled build/runtime node type, including GPU-bearing nodes.
- [ ] The restricted workspace generates eight environments and eight native
  `modules.yaml` files.
- [ ] All eight restricted environments concretize and their lockfiles pass
  review.
- [ ] Every lane builds and passes its target runtime checks.
- [ ] Only approved concrete specs are pushed to the private CSE build cache.
- [ ] Both CSE workspaces identify the same retained restricted catalog release.
- [ ] The separately published static catalog matches the restricted reviewed
  bytes and is readable by a non-CSE consumer.
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

For a cross-builder `PermissionError`, inaccessible generated file, or a tree
damaged by recursive `chmod 660`, go directly to
[Shared generated-content permission recovery](#shared-generated-content-permission-recovery).
That procedure is system-neutral and applies to every Initial Conversion Trials
system. The selected system note records only its exact workspace state and any
system-specific root/group check; it must not carry a different permission
contract.

| Checkpoint | State | Durable evidence |
|---:|---|---|
| 1 | Profile verified | reviewed `profile.yaml` and probe evidence |
| 2 | Catalog reviewed | static manifest, plan, and selected scopes |
| 3 | Restricted workspace initialized | build values, workspace manifest, configs, and modules |
| 4 | Locks reviewed | eight approved restricted `spack.lock` files |
| 5 | Lanes validated | per-lane build logs and target runtime results |
| 6 | Cache complete | signed binaries, verified index, and approved hashes |
| 7 | Publication complete | public static catalog, copied locks, published prefixes, and matching hashes |
| 8 | Release accepted | clean-shell module/runtime evidence and owner approval |

### Same release or new release

For an operational retry with unchanged inputs, resume the same release when:

- the profile, catalog, semantic provider/package values, roster,
  package-recipe pin, Spack version and commit, and repository commits are
  unchanged;
- the affected lockfile and concrete hashes are unchanged;
- the failure was operational, such as a scheduler timeout, node loss, network
  interruption, quota exhaustion, or interrupted cache transfer;
- no approved published artifact would be edited in place.

The selected login/compute context, its executable build stage, and
`build_jobs` are operational settings. They may change within the same trial
release when the environment YAML, lockfiles, install tree, and concrete hashes
remain unchanged. Use the generated `cse-build` context selector in the same
workspace; do not generate a sibling workspace or copy lockfiles merely to move
between login and compute nodes.

The Spack tool-root path is also operational. One builder may use the shared
root and another a builder-local root without changing the release when both
roots pass the same version, tag, commit, clean-tree, and scope checks. Record
the selected path with each builder's evidence.

An unfinished trial can correct a package recipe, patch, spec, version, or
variant in its existing workspace. Retain before/after inputs and selected
locks, reconcretize only explicitly selected environments, and resume from those
locks. Reuse installed hashes that remain unchanged. Earlier installation does
not require a replacement workspace. Report all affected locks; repeat their
lock review and build checks when each is selected, before release acceptance.

Create a new catalog and trial release when observed system facts or reusable
static scopes change. Compiler, MPI, toolchain, roster, or Spack identity changes
also require a new trial release. Once a release is accepted or published, any
semantic input, lock, module, or view correction gets a new release record.

A new release does not imply rebuilding every package. It may reuse compatible
approved binaries already present in the private CSE build cache. The rule is
about preserving provenance and immutable release records, not discarding safe
cache reuse.

Use `--overwrite` only before the first lockfile exists and before anything has
been pushed or published. Later corrections use the existing workspace and
retained recovery records. Never overwrite the workspace to deliver an overlay.
An affected checkpoint-4 review must be repeated after its lock changes; its
earlier evidence remains in the recovery record.

### Catalog correction and replacement

Do not repair a restricted or published catalog by editing its generated files
in place. CSE group write access exists so any authorized CSE package manager
can administer the release lifecycle; it does not replace the versioned release
procedure.

For every catalog correction, including a minor metadata or permission-related
correction:

1. Select a new `CATALOG_RELEASE`. Select a new `TRIAL_RELEASE` as well when an
   initialized workspace, lockfile, or release consumed the prior catalog.
2. Correct the owning profile, hint, template, or renderer input. Run
   `render-static` into the new restricted versioned directory. Do not copy and
   edit the previous generated catalog and do not pass `--overwrite` for the
   retained release.
3. Review the new restricted `manifest.yaml`, static plan, profile snapshot,
   scopes, examples, and source provenance as a complete release.
4. Run `publish-static` against that exact reviewed restricted directory. The
   command creates the new public version, `publication.yaml`, and
   `SHA256SUMS`; do not author or repair those publication files by hand.
5. Verify the checksum inventory, CSE group ownership and write access, outside
   consumer read access, and denied outside write. Move `current` only after the
   new version passes review and acceptance.
6. Record that the new release supersedes the old release. Retain the old
   version for the required audit and rollback period. Remove or withdraw it
   only through the recorded retention procedure after confirming that no
   supported environment still pins that versioned path.

The restricted and public directory names, both manifests, approval record,
checksum inventory, reviewer, release authority, validation evidence, pointer
change, and eventual retirement decision form the replacement log. No manual
content edit is part of this procedure.

### Recovery matrix

| Failure or change | Resume action |
|---|---|
| Scheduler timeout, node failure, temporary network failure, or resolved quota problem with unchanged inputs | Retry only the failed command or environment in the same release. |
| Selected build node is unavailable, but the other recorded context can run the same locked target | Enter the same workspace through `./cse-build login` or `./cse-build compute`. The selector chooses an executable stage for that context; keep the existing locks and install tree. |
| Source build failure caused by a transient host/tool problem | Retry the failed lane after recording the log; earlier validated lanes remain valid. |
| Package recipe, patch, spec, version, or variant correction in an unfinished trial | Apply in the same workspace, retain the old lock, explicitly reconcretize the selected environment, and resume. Report other affected locks and repeat their reviews before later builds. |
| Compiler, MPI, or Spack version/commit change, or a semantic change to an accepted/published release | Create a new trial release, reconcretize, and revalidate every affected lane. |
| Selected Spack checkout is dirty or does not match the pinned source/tag/commit | Stop. Replace the selected root with a clean checkout of the approved identity. Do not pull, switch branches, or run `spack isolate` in place. |
| Cluster Inspector fact or external module/prefix is wrong | Regenerate the profile, create a new catalog release and trial release, and restart at checkpoint 1. |
| Static catalog scope or toolchain is wrong | Fix the owning profile/catalog logic, create new catalog and trial releases, and restart at checkpoint 2. |
| Restricted workspace template or values are wrong | Before installation, unaccepted diagnostic locks from the current checkpoint may be discarded together and the working release reinitialized. After a lock has been accepted, installed, or promoted, create a new trial release. |
| A later lane fails while earlier lane locks and inputs remain unchanged | Keep earlier locks, prefixes, and evidence; retry the failed lane. If a shared upstream hash changes, report dependent lanes and explicitly reconcretize/revalidate each affected lane before accepting the unfinished trial. |
| Build-cache push, index, or signing operation is interrupted | Retry the cache operation from the installed restricted specs; do not rebuild. |
| Publication reports a cache miss for an exact approved hash | Return to the restricted workspace, build and validate that exact locked hash, push it, and retry only the failed publication environment. If producing it requires a changed hash, create a new release. |
| Another builder cannot traverse, read, or replace generated workspace/cache/view/module/build-cache content | Stop processes using the affected tree, refresh the common generated controls, and follow [Shared generated-content permission recovery](#shared-generated-content-permission-recovery). Each owner repairs that owner's entries; do not recursively chmod the install tree or a broad shared parent. |
| View or module refresh fails before release acceptance and the DAG is unchanged | Correct and rerun only view/module generation, then repeat clean-shell checks. |
| Published module/view content needs correction after acceptance | Create a new trial release; do not edit the accepted release in place. |
| Platform upgrade changes CPE, compiler, MPI, fabric, OS, or runtime ABI facts | Hold publication and restart with a fresh profile, catalog, locks, and runtime validation. |

### Recovery: replace an unaccepted workspace after a blueprint correction

Use this only when concretization exposed a blueprint or values-helper defect,
no package installation or build-cache promotion has started, and the existing
locks are unaccepted diagnostic output. The reviewed profile and static
catalog do not need to be regenerated when their machine facts and external
records are correct.

Synchronize the project repositories through Step 2, reload the operator
session, and check whether either built tool actually changed. A
`stack-content`-only correction does not require rebuilding Cluster Inspector
or Stack Composer.

Regenerate the values file because it is part of the current blueprint
contract, then replace the unaccepted workspace as one unit:

```bash
source "$CSE_OPERATOR_SESSION_FILE"
cse_session_status

"$CSE_PYTHON" \
  "$CONTENT/pilots/cse-pilot/scripts/create-build-values.py"

"$CSE_PYTHON" "$STACK_COMPOSER" init-workspace \
  --blueprint "$CONTENT/pilots/cse-pilot" \
  --catalog "$CATALOG" \
  --values "$BUILD_VALUES" \
  --output "$BUILD_WORKSPACE" \
  --overwrite

cd "$BUILD_WORKSPACE"
./cse-build login concretize
```

This deliberately replaces every diagnostic lock in that workspace. Do not
copy previously generated locks into the replacement: the corrected
compiler/MPI boundary is DAG-significant, so all eight environments must be
concretized and verified together. If installation or promotion already
started, preserve the original evidence and use a new trial release instead.

### Switch between login and compute contexts

The initialized workspace records both reviewed contexts. Switching contexts is
a normal runtime operation and does not regenerate the workspace, change a
lockfile, or select another CPU target:

```bash
cd "$BUILD_WORKSPACE"

# Connected node: bootstrap Spack, concretize, verify, and fetch sources.
./cse-build login
./cse-build login concretize
./cse-build login fetch

# Compute allocation: install the same locked DAGs.
./cse-build compute
./cse-build compute install
```

The commands may run in separate tmux panes or at different times. Each context
has its own tmux session, executable build-stage candidates, and mutable command
cache. Both use the same per-builder Spack bootstrap store, workspace,
lockfiles, source cache, install tree, views, modules, and pinned Spack identity.
Concretize once through `login` before entering a network-restricted compute
node so Clingo bootstrap artifacts are already available. The selector creates
and executes a small probe in each stage candidate before Spack starts, so a
writable `noexec` or policy-restricted temporary directory is skipped.
`${WORKDIR}` supplies a separate final fallback for each context.

On the first concretization for a builder, Spack may install solver support such
as `re2c`, `gmake`, `cmake`, `python-venv`, and `gcc-runtime` below that
builder's bootstrap store. This is Spack bootstrapping its concretizer; it is
not the CSE `core-independent` group and it does not install the CSE package
roster. It normally happens once for the selected Spack identity and per-user
cache, then the remaining environments reuse it. Changing Spack versions or
the user-cache/bootstrap location, or clearing that store, can trigger it again.

Confirm that the node can see the shared workspace and store and can load every
recorded external module. Do not reconcretize merely because the context or
stage changed. If neither context has an executable stage, correct the site
`WORKDIR` or profile facts before continuing.

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
mkdir -p "$CSE_TOOLS_ROOT" "$CSE_TOOLS_ROOT/spack"
chgrp "$CSE_GROUP" "$CSE_TOOLS_ROOT" "$CSE_TOOLS_ROOT/spack"
chmod 2770 "$CSE_TOOLS_ROOT" "$CSE_TOOLS_ROOT/spack"
git clone --branch "$SPACK_TAG" --depth 1 \
  "$SPACK_SOURCE" "$SPACK_ROOT"
test "$(git -C "$SPACK_ROOT" rev-parse HEAD)" = "$SPACK_COMMIT"
test "$(git -C "$SPACK_ROOT" rev-parse "${SPACK_TAG}^{commit}")" = \
  "$SPACK_COMMIT"
test -z "$(git -C "$SPACK_ROOT" status --porcelain --untracked-files=all)"
test -z "$(git -C "$SPACK_ROOT" \
  ls-files --others --ignored --exclude-standard)"
chgrp -R "$CSE_GROUP" "$SPACK_ROOT"
chmod -R u+rX,g+rX,o-rwx,a-w "$SPACK_ROOT"
find "$SPACK_ROOT" -xdev -type d -exec chmod g-s {} +
test -z "$(find "$SPACK_ROOT" -xdev -perm /222 -print -quit)"
test -z "$(find "$SPACK_ROOT" -xdev -type d -perm -2000 -print -quit)"
```

The writable parent directories and the immutable checkout have deliberately
different modes:

| Path kind | Expected mode | Purpose |
|---|---:|---|
| `$CSE_TOOLS_ROOT` and `$CSE_TOOLS_ROOT/spack` | `2770` (`drwxrws---`) | Owner and CSE group may provision a new sibling Spack version; setgid preserves CSE group inheritance. |
| Directories and executable files inside `$SPACK_ROOT` | `0550` (`r-xr-x---`) | Owner and CSE group may run and traverse the pinned checkout; neither may modify it. |
| Ordinary files inside `$SPACK_ROOT` | `0440` (`r--r-----`) | Owner and CSE group may read the pinned checkout; neither may modify it. |

In symbolic modes, `g+rX` gives the group read access plus search access on
directories and execute access only on files that were already executable.
`a-w` removes write access from owner, group, and others. A lowercase `s` in
the group-execute position is expected only on the two writable parent
directories. An uppercase `S` means group execute/search is missing and is not
valid here. The immutable version checkout contains neither `s` nor `S`.

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

## 1. Create or resume the operator session

The operator session is the resume boundary before a restricted workspace
exists. It records the exact system, catalog release, trial release, repository
branch, shared roots, Spack identity/mode, and reviewed bootstrap Python once.
Sourcing it restores every derived path and the verification helpers used by
the later steps. It does not pull repositories, rebuild either tool, rerun a
probe, rerender a catalog, or change a workspace.

It is deliberately operator-local:

```text
$HOME/STACK_TESTING/operator-sessions/<system>/<trial-release>/
  activate.sh                 # source this after each login
  provider-selections.sh      # reviewed Step 7 selections, loaded when present
```

This is not the shared builder handoff. After Step 8 initializes
`$BUILD_WORKSPACE`, its generated `./cse-build` command is the portable resume
entry point for either builder.

### First login for a system/release

Start a clean Bash shell. Bootstrap only the Stack Content checkout so the
session generator is available. Use the exact lowercase system key represented
by `stack-content/systems/<system>/`.

```bash
export WORK_ROOT="$HOME/STACK_TESTING"
export CONTENT="$WORK_ROOT/stack-content"
export STACK_BRANCH="codex/simplified-render-plan"
export CSE_BOOTSTRAP_PYTHON="<absolute-path-to-reviewed-python-3.9-or-newer>"

test -x "$CSE_BOOTSTRAP_PYTHON"
mkdir -p "$WORK_ROOT"
if [ ! -d "$CONTENT/.git" ]; then
  git clone https://github.com/ray12514/stack-content.git "$CONTENT"
fi
git -C "$CONTENT" status --short --branch
```

Stop if that checkout contains unreviewed work. Then select the current branch
and create the saved session. The default release names are
`<system>-catalog-001` and `<system>-trial-001`:

```bash
git -C "$CONTENT" fetch origin
git -C "$CONTENT" switch "$STACK_BRANCH"
git -C "$CONTENT" pull --ff-only

"$CSE_BOOTSTRAP_PYTHON" \
  "$CONTENT/pilots/cse-pilot/scripts/create-operator-session.py" \
  --system "<system>" \
  --trial-root "<approved-shared-cse-path>/initial-conversion-trials" \
  --tools-root "<installer-selected-shared-cse-tools-root>" \
  --bootstrap-python "$CSE_BOOTSTRAP_PYTHON" \
  --spack-mode "<shared-or-local>" \
  --group "cse"

source "$WORK_ROOT/operator-sessions/<system>/<system>-trial-001/activate.sh"
```

The session fails immediately unless `CSE_TRIAL_ROOT` ends in
`/initial-conversion-trials`. After sourcing it, verify the derived roots
before creating any shared directory:

```bash
test "$CSE_RESTRICTED_ROOT" = "$CSE_TRIAL_ROOT/restricted"
test "$CSE_PUBLISHED_ROOT" = "$CSE_TRIAL_ROOT/published"
printf 'trial=%s\nrestricted=%s\npublished=%s\n' \
  "$CSE_TRIAL_ROOT" "$CSE_RESTRICTED_ROOT" "$CSE_PUBLISHED_ROOT"
```

If an earlier session points at the parent CSE directory, stop. Do not move a
Spack install tree or edit generated manifests in place. First inventory the
wrongly rooted catalog, workspaces, locks, and install database. When no
packages were installed, create a correctly rooted session and regenerate the
catalog/workspace from the owning inputs. If packages were installed, preserve
the tree and review recovery before changing any path because installed
prefixes and Spack database records are not safely relocatable.

Use `--catalog-release` and `--trial-release` when the release names are not
the defaults. Do not overwrite a saved session after its catalog, workspace,
or lockfiles become durable. A changed profile capability, such as the newly
recorded Slurm MPI-launch facts, gets a new catalog release and trial release,
and therefore a new operator session.

### Every later login

Open or reattach the operator's tmux session, then run one command:

```bash
source "$HOME/STACK_TESTING/operator-sessions/<system>/<trial-release>/activate.sh"
```

The command prints the selected catalog/workspace and whether the current
Cluster Inspector and Stack Composer artifacts already exist. Existing tools
are reused. Pull and rebuild them only when their reviewed source or build
dependencies changed. Use `cse_session_status` to print the summary again and
`cse_session_use_spack` when an operator-side step explicitly needs the pinned
Spack command. The generated workspace's `cse-build` command activates Spack
for downstream builder actions itself.

The state-root example is both user- and system-specific. A site may choose a
different approved work or scratch root, but the result must be absolute,
unique to `$USER`, writable by that builder, and outside the shared tool and
package trees. Keep the GPG home private (`0700`) and persistent for as long as
the release signing/trust record is needed. `SPACK_USER_CACHE_PATH` does not
relocate Spack's GPG keyring, so `SPACK_GNUPGHOME` is required separately.
The generated builder entry point keeps `SPACK_MISC_CACHE_PATH` in a persistent
builder-named partition below the shared restricted misc-cache root. It
recursively restores CSE-group access before and after Spack; separate builder
partitions prevent concurrent users from replacing one mutable index.
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

# Reload the saved values through the just-synchronized session implementation.
source "$CSE_OPERATOR_SESSION_FILE"
```

Create the system note from the template when needed:

```bash
mkdir -p "$SYSTEM_DIR"
if [ ! -f "$SYSTEM_DIR/runbook-notes.md" ]; then
  cp "$CONTENT/systems/_template/runbook-notes.md" "$SYSTEM_DIR/runbook-notes.md"
fi
```

## 3. Build and verify the tools

Run the applicable subsection on the first setup and whenever Step 2 changes
that tool's reviewed commit. It is not a daily-login step.
`cse_session_status` compares each artifact's recorded build commit with the
current checkout and reports which tool, if any, requires a rebuild.

The synchronized operator-session implementation supplies guarded build
functions. Build both tools with:

```bash
source "$CSE_OPERATOR_SESSION_FILE"
cse_rebuild_tools all
```

Use `cse_rebuild_tools inspector` or `cse_rebuild_tools composer` when only one
checkout changed. The `all` form attempts both builds and returns failure if
either one fails. Cluster Inspector requires Go 1.22 or newer. Stack Composer
uses the reviewed bootstrap Python to create or update its repository-local
environment and release artifact.

Each function verifies a clean checkout, builds the tool, runs its help smoke
test, and only then atomically records the successful source commit. Never
write either file below by hand:

```text
$CSE_TOOL_STATE_ROOT/cluster-inspector.commit
$CSE_TOOL_STATE_ROOT/stack-composer.commit
```

If Go, Python, a dependency, compilation, packaging, or the smoke test fails,
the corresponding recorded commit remains at its previous successful value.
An older executable may remain on disk, but `cse_session_status` continues to
report `build/rebuild required` for the changed checkout:

```bash
cse_session_status
```

`CSE_BOOTSTRAP_PYTHON` is the reviewed site- or module-provided interpreter
used only to create the virtual environment. From this point onward, invoke
every project Python command through the absolute `CSE_PYTHON` path. Do not
depend on whichever `python` or `python3` happens to be first on `PATH`. In a
new shell, Step 1 restores the same path. Rebuild the virtual environment only
when its bootstrap interpreter or Stack Composer dependencies must change.
The explicit build-tool upgrade is required even for a newly created virtual
environment. Recreating `.venv` without that upgrade can restore an older
`setuptools` that rejects Stack Composer's SPDX license metadata during the
non-isolated wheel build.

### Existing restricted catalogs, workspaces, and installations

Rebuilding Cluster Inspector or Stack Composer does not modify an existing
restricted catalog, initialized workspace, lockfile, install prefix, view,
module tree, cache, or evidence record. When those artifacts are already valid,
leave them in place. Do not rerun `render-static`, `init-workspace`, concretize,
or install merely because a tool executable was refreshed.

After synchronizing the repositories, source the existing activation file and
run the guarded builds:

```bash
source "$CSE_OPERATOR_SESSION_FILE"
cse_session_status
cse_rebuild_tools all
```

The existing activation file sources the current Stack Content
`operator-session.sh`, so it receives the guarded build functions after the
repository update; the saved activation file does not need to be regenerated.

Classify the change after the tools build:

- A Cluster Inspector implementation change does not alter an already reviewed
  profile or catalog. Rerun the affected probe only when producing a new profile
  or when the change corrects a fact or validation result used by that profile.
- A Stack Composer implementation change does not rewrite prior output. Use the
  rebuilt artifact for the next render, workspace initialization, controls-only
  refresh, or publication command that requires the changed behavior.
- A Stack Content control-template change affects an existing initialized
  workspace only when the owning system procedure explicitly selects the
  controls-only refresh. That refresh preserves environment YAML, lockfiles,
  installed prefixes, views, caches, and build evidence.

For the current permission correction, the restricted build workspace and its
completed environments do not need to be regenerated. Rebuild Stack Composer
before the next `publish-static` operation. Source the refreshed activation
implementation so future tool builds cannot advance their recorded commits
after a failed build.

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
and from each builder's `SPACK_USER_CACHE_PATH`, `SPACK_MISC_CACHE_PATH`, and
`SPACK_GNUPGHOME`.

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

Copy every node fragment back to `$PROBE_DIR`. After entering an allocation,
`--runner this` is unchanged whether the site scheduler is Slurm or PBS.

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

"$CSE_PYTHON" "$STACK_COMPOSER" show \
  --profile "$PROBE_DIR/profile.yaml"
```

Review compiler, MPI, accelerator, fabric, runtime, prefix, module,
compatibility, and node-role facts against the live machine. Accelerator facts
remain part of the system profile, but GPU builds are outside these trials. On
Cray systems, select one coherent CPE/compiler/Cray MPICH set. On generic Linux
systems, prove the
compiler pairing for the selected MPI. Preserve incorrect discovery evidence,
fix the inspector or hints, and regenerate. Do not hand-enter a guess as a
durable fact.

Before selecting the trial compiler, compare the profile's complete verified
compiler inventory with the site's visible compiler and `PrgEnv-*` modules.
The inventory is a fact report; it may contain AOCC, GNU, Intel, and CCE even
when the trial selects only one platform compiler. If an expected compiler is
missing, inspect the recorded discovery and the system fragment before changing
policy:

```bash
grep -nE 'aocc|PrgEnv-aocc|compiler' \
  "$PROBE_DIR/system-probe-transcript.yaml" \
  "$PROBE_DIR/system.frag.yaml"
```

The transcript distinguishes a module that was never enumerated from a module
that was found but could not be activated or verified. A compiler-looking
directory under a Cray MPICH or LibSci product tree is compatibility/flavor
evidence, not proof that the compiler provider is installed. Also confirm that
the probe used the rebuilt current inspector and that the merge consumed the
new `system.frag.yaml`. Use `inspector-hints.yaml` only to expose a reviewed
module that the normal module inventory cannot reach; do not add a compiler
provider by hand.

A directly observed non-Ethernet fabric may legitimately have an empty driver
inventory when no separate driver package, module version, or installation
prefix is queryable. Cluster Inspector retains the observed fabric with
`drivers: []`; it does not invent a driver identity. If schema verification
passes but an older inspector rejects the profile because the non-Ethernet
fabric has no driver, update and rebuild Cluster Inspector, then verify the
existing merged profile again. That validator-only correction does not require
rerunning the probes or merge.

The `show` MPI section is the compact review surface. Every MPI row must name
its exact compiler reference, prefix, and module evidence. A verified MPI
identity that lacks an exact compiler relationship remains failed-candidate
evidence in the system fragment and is not admitted to `mpi_providers`. Review
that evidence without assigning a compiler by guess. If several module
observations resolve to the same MPI name, version, and physical prefix, the
profile should contain only the canonical paired observation, not a synthetic
list of alternative module aliases.

An application module that exposes its private MPI dependency is not an MPI
provider. Reject entries where the module names an application but the emitted
MPI version came from that application's version while the verified MPI prefix
or command reports something else. A structurally valid MPI module in an
unsupported site test/private namespace is a different case: add that reviewed
namespace to `mpi.exclude_patterns` in `inspector-hints.yaml`, then rerun the
system probe. Do not encode site namespace names in generic discovery logic.
The same exclusion list filters modules recorded inside MPI activation chains,
including per-compiler platform flavors. A slash-free pattern matches any
module path segment; use a pattern containing `/` when the complete module path
must match.

An MPI module may identify its build compiler with a suite release rather than
the compiler product version. For example, an `intel-2024.2.1` suffix may map
to a verified classic Intel compiler product such as `intel@2021.13.1`. Review
that the MPI `compiler` and `compatibility.compilers` fields name the observed
compiler product reference, not the suite-release label.

On a Slurm system, review the verified `slurm` entry under
`system_externals`. When `srun --mpi=list` succeeds during the system probe,
the entry must contain `capabilities.mpi_launch.plugins` and a separate
`development_interfaces` list. Direct `srun` support requires the selected
plugin to appear in both lists. Do not run an extra manual scheduler command or
infer build support from the presence of `srun` alone.

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

### Required two-builder setup for every system

Run this setup on every new trial system before generating the static catalog
or workspace. It is the common collaboration contract for Blueback, Wheat,
Fran, Raider, and every later system; system notes must not replace it with a
different permission procedure.

Record both assigned builders and prove both are members of the deployment's
explicit collaboration group. The current CSE group is `cse`; the tools do not
silently supply that name:

```bash
source "$CSE_OPERATOR_SESSION_FILE"

test "$CSE_GROUP" = "cse"
CSE_BUILDERS=("<first-builder>" "<second-builder>")
test "${#CSE_BUILDERS[@]}" -eq 2
CSE_MEMBER_FAILURES=0

for builder in "${CSE_BUILDERS[@]}"; do
  if ! id "$builder"; then
    CSE_MEMBER_FAILURES=1
  elif ! id -nG "$builder" | tr ' ' '\n' | grep -Fx "$CSE_GROUP"; then
    printf '%s is not in %s\n' "$builder" "$CSE_GROUP" >&2
    CSE_MEMBER_FAILURES=1
  fi
done
test "$CSE_MEMBER_FAILURES" -eq 0
unset builder CSE_BUILDERS CSE_MEMBER_FAILURES
```

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
  "$CSE_PUBLISHED_ROOT/catalogs" \
  "$CSE_PUBLISHED_ROOT/catalogs/$SYSTEM_NAME" \
  "$CSE_PUBLISHED_ROOT/catalogs/$SYSTEM_NAME/static" \
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

Where the filesystem supports POSIX default ACLs, apply the equivalent default
to the dedicated restricted working roots. This strengthens ordinary file
creation but does not replace the generated permission helper because Spack may
explicitly create `0600` files and `0700` directories:

```bash
if command -v setfacl >/dev/null 2>&1; then
  setfacl -m "g:${CSE_GROUP}:rwx,m::rwx,o::---" \
    "$CSE_RESTRICTED_ROOT" \
    "$STATIC_ROOT" \
    "$CSE_RESTRICTED_ROOT/workspaces" \
    "$BUILD_RELEASE_ROOT" \
    "$CSE_RESTRICTED_ROOT/cache/source" \
    "$CSE_RESTRICTED_ROOT/cache/misc" \
    "$BUILDCACHE_ROOT" \
    "$BUILD_EVIDENCE"
  setfacl -d -m "u::rwx,g::rwx,g:${CSE_GROUP}:rwx,m::rwx,o::---" \
    "$CSE_RESTRICTED_ROOT" \
    "$STATIC_ROOT" \
    "$CSE_RESTRICTED_ROOT/workspaces" \
    "$BUILD_RELEASE_ROOT" \
    "$CSE_RESTRICTED_ROOT/cache/source" \
    "$CSE_RESTRICTED_ROOT/cache/misc" \
    "$BUILDCACHE_ROOT" \
    "$BUILD_EVIDENCE"
fi
```

Verify the newly prepared restricted roots before continuing:

```bash
for shared_root in \
  "$CSE_RESTRICTED_ROOT" \
  "$STATIC_ROOT" \
  "$CSE_RESTRICTED_ROOT/workspaces" \
  "$BUILD_RELEASE_ROOT" \
  "$CSE_RESTRICTED_ROOT/cache/source" \
  "$CSE_RESTRICTED_ROOT/cache/misc" \
  "$BUILDCACHE_ROOT" \
  "$BUILD_EVIDENCE"; do
  test -d "$shared_root"
  test -g "$shared_root"
  test "$(stat -c %G "$shared_root")" = "$CSE_GROUP"
  test -z "$(find "$shared_root" -maxdepth 0 \
    \( ! -perm -0770 -o -perm -0007 \) -print)"
done
```

This root setup is only the first half of the guarantee. After Step 8 creates
the workspace, every builder must use its refreshed generated `cse-build`. On
entry and exit it restores owner/`cse` parity for workspace/lock content,
source cache, that builder's misc-cache partition, views, modules, and a
file-backed build cache. Rendered `packages:all:permissions` applies the same
group policy to every Spack-created install prefix. `./cse-build login status`
verifies every declared shared surface before handoff.

The build stage, `SPACK_USER_CACHE_PATH`, bootstrap state, and GPG home remain
private per builder and are recreated for the receiving builder. They are not
inside the shared collaboration contract. With those intentional exceptions,
no generated restricted-build content may be placed in a shared CSE path
without the recorded group and its required access.

Do not recursively change ownership or permissions on an existing shared tree.
If the top-level path is site-owned, ask its owner to create the dedicated roots.
The lowercase `s` shown in the group-execute position of these writable
directory modes is setgid: it provides group inheritance and retains group
search access. Uppercase `S` would mean group search access is missing and is
not valid. Do not add the sticky bit inside the restricted workspace, Spack
store, caches, build cache, views, or module roots. Spack and the handoff
scripts must be able to rename and clean entries created by either builder.
Protect against accidental deletion with the restricted/published boundary,
release snapshots, evidence, and backups instead.

If a dedicated trial tree was previously created with group read-only modes,
stop all Spack processes and have its owner or filesystem administrator repair
only that confirmed tree. Set the recorded `$CSE_GROUP`, add group
read/write/search, remove access for others, and restore setgid on every
directory. Use a default ACL for the recorded group when the filesystem
supports it; otherwise every builder must keep `umask 0007`. Do not apply a
recursive command to the parent of `$CSE_TRIAL_ROOT` or another shared parent
containing unrelated releases.

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

Add `--source-dirty` only when reviewed system inputs are not committed. If any
catalog content must change after this restricted release is generated, select
a new catalog release identifier and follow
[Catalog correction and replacement](#catalog-correction-and-replacement).
Do not regenerate the retained version in place.

Inspect the generated catalog:

```bash
cat "$CATALOG/README.md"
cmp "$SYSTEM_DIR/profile.yaml" "$CATALOG/profile.yaml"
sed -n '1,260p' "$CATALOG/manifest.yaml"
sed -n '1,320p' "$CATALOG/reports/static-plan.yaml"
find "$CATALOG/scopes" -type f | sort
```

For the intended tuple, inspect every `packages.yaml` and `toolchains.yaml`.
Confirm external specs, prefixes, modules, compiler stamps, and MPI
requirements against the reviewed profile.

Every MPI installation admitted to the catalog must have one exact compiler
pairing supported by wrapper, module, or platform evidence. Cluster Inspector
retains an unresolved candidate as failed-pairing evidence but does not emit it
in `profile.mpi_providers`. `cluster-inspector verify` and `render-static`
remain defensive against a hand-written or malformed unpaired provider. No
`unpaired` MPI scope is generated. Correct the discovery evidence or exclude a
reviewed private/test/application module in `inspector-hints.yaml` when it is
useful to reduce probe noise. Never assign a compiler by hand merely to make
the catalog render.

The catalog manifest preserves `profile_facts.system_externals`, including
Slurm MPI-launch capabilities. On a Slurm system selected for a source-built
Open MPI lane, verify that the manifest contains the reviewed launch-capability
record. When `pmi2` appears in both the plugin and development-interface lists,
the helper enables direct launch. When it does not, the helper retains an
mpirun-only root instead of guessing.

Gate: the catalog contains the exact compatible compiler, paired MPI, common,
and platform scopes needed by the trials, and contains no unresolved MPI
inventory. A common Spack external must come from a
development-verified `profile.system_externals` entry. A
`profile.fabric.userspace` observation remains visible in the manifest and
plan, but it is not sufficient to populate `packages.yaml`. Fix the profile or
catalog logic when a scope is missing; do not type a nonexistent path into a
values file.

On Cray systems, the static plan must retain the inspected platform libfabric
runtime observation. It belongs in the common Spack scope only when Cluster
Inspector also verified its headers and libraries as a `system_externals`
entry. Each Cray MPICH scope must contain the selected `cray-mpich` external
and the inspected `cray-pmi` external. These records preserve and validate the
active CPE runtime inventory. The selected Cray MPICH external itself remains
a platform leaf: do not add compiler, target, `libfabric`, or `cray-pmi`
dependency constraints to its external spec. Stop if the required Cray runtime
record is absent; do not allow Spack to substitute a source-built runtime for
the active CPE.
`reports/static-plan.yaml` must show an empty `missing_mpi_dependencies` list.

After review, retain `$CATALOG` at its versioned restricted path and use that
exact path when creating the restricted build workspace. Do not publish or
switch catalog inputs as part of workspace initialization. The independent
public static-catalog release is created in Step 12 after the restricted build,
runtime validation, and build-cache gate.

### Static-catalog handoff without `init-workspace`

The catalog is already usable by CSE-authorized package managers at this gate.
After Step 12 publishes the reviewed copy, non-CSE package managers use the
versioned public path. In either case, a package manager can create an ordinary
Spack environment by including the exact generated scopes and writing normal
Spack specs. For example:

```yaml
spack:
  include::
    - <catalog-root>/scopes/common
    - <catalog-root>/scopes/compilers/<provider>/<version>
    - <catalog-root>/scopes/mpi/<provider>/<version>/<compiler-axis>

  concretizer:
    unify: false

  specs:
    - hdf5@1.10.6+mpi %<compiler-plus-mpi-toolchain>
```

Use the toolchain name from the selected MPI scope's `toolchains.yaml`; do not
retype compiler, MPI, external-prefix, or module policy in the environment.
Compiler scopes contain `packages.yaml` only. For a Serial environment, omit
the MPI scope and constrain roots directly with the selected compiler, such as
`%gcc@12.5.0`; there is no compiler-only toolchain. This is the production
purpose of `render-static`: its output is independent of the CSE trial
initializer.

## 7. Create the restricted build values

Set the small provider tuple selected during catalog review. The common runbook
does not infer this policy from the machine. The system note gives the exact
exports for the current trial selection.

Review the available node-type keys and stage facts for both runtime contexts:

```bash
sed -n '/^  node_types:/,/^template_set:/p' "$CATALOG/manifest.yaml"
```

`shared` means the CSE-standard compiler surface within this system's
workspace. GCC 12.5.0 is standardized across the four systems, but the selected
MPI provider is system-specific: normally external Cray MPICH on Cray systems
and build-sourced OpenMPI on non-Cray systems. It does not mean that one binary
installation or one MPI provider is shared across all systems.

Record those selections once in the operator session's prepared file:

```bash
vi "$CSE_PROVIDER_SELECTIONS"
source "$CSE_OPERATOR_SESSION_FILE"
```

Uncomment and fill the required exports for the shared compiler/MPI, platform
compiler/MPI, and job count. Also review the active `CSE_LOGIN_NODE_TYPE` and
`CSE_COMPUTE_NODE_TYPE` selections. They start as `login` and `cpu_compute`,
but must match exact keys in the current catalog manifest. The second command
reloads both the fixed session values and the reviewed provider selections.
Every later login gets the same selections by sourcing only `activate.sh`; do
not retype them into the shell.

`provider-selections.sh` is operator-local setup state, not the shared handoff
or an additional renderer input. The helper resolves it into the tracked build
values and the initialized workspace records the resulting provider paths,
specs, modules, and roots. Create a new operator session rather than carrying
this file into a different catalog or trial release.

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
It intersects the detected, preferred, and alternate CPU targets of every
build/runtime node type, then selects `x86_64_v3`, `x86_64_v2`, or `x86_64` in
that order. A node remains part of this CPU compatibility check when it also
has a GPU; the trial does not render GPU package environments. This target is
architecture policy; it is independent of the active login or compute context,
and changing contexts does not change it. The helper rejects a requested target
that any relevant node type cannot run. It also records the generic `x86_64`
family target for architecture-specific prebuilt distributions such as
Miniforge.

The helper requires two reviewed build-context selections and resolves them as
exact keys under the catalog manifest's `profile_facts.node_types`. The
generated provider-selection file starts with `CSE_LOGIN_NODE_TYPE=login` and
`CSE_COMPUTE_NODE_TYPE=cpu_compute`; replace either value when the catalog uses
a different key. For each context the helper records inspected writable
candidates, temporary/node-local storage
first, other scratch paths next, and a context-specific `${WORKDIR}` fallback
last. At workspace entry, `cse-build` performs an actual execution probe and
selects the first usable path. Every path is namespaced by the Spack user,
system, trial release, and context. Do not replace these lists with one manual
stage path.

| Values | Restricted build setting |
|---|---|
| `workspace.role` | `build` |
| system/release | current profile/catalog plus `TRIAL_RELEASE` |
| `shared.compiler` | GCC 12.5.0 `+binutils`, `source: build`, plus the verified older compiler selected to build the GCC producer |
| compiler public names | generated CSE front-door names such as `init-GCC` and `init-CCE`; these do not replace the platform module chains copied from the catalog |
| `shared.mpi` | OpenMPI 4.1.8 built with GCC, or the selected compatible external MPI |
| `platform.compiler` | use the catalog manifest's observed provider name and exact version; the helper copies its Spack package name, module chain, and compiler scope path |
| `platform.mpi` | use the catalog manifest's Spack `package` name; build OpenMPI 4.1.8 on non-Cray systems, or select the matching external Cray MPICH 9.x/Intel MPI scope |
| `catalog_scopes.*` | exact relative paths below `$CATALOG` |
| install tree | `$BUILD_RELEASE_ROOT/spack/opt` |
| build contexts/stages | reviewed login and compute profile node types; separate generated temp, scratch, then `${WORKDIR}` fallback lists selected by an execution probe |
| CPU architecture | one system-wide portable target for source-built roots on both compiler surfaces and all lanes; highest common support capped at `x86_64_v3`; inspected platform externals retain their own architecture |
| source cache | `$CSE_RESTRICTED_ROOT/cache/source` (shared) |
| misc/concretization cache | `$CSE_RESTRICTED_ROOT/cache/misc/$USER` (builder-partitioned, recursively CSE-group-accessible, persistent across contexts and surfaces) |
| views/modules roots | `$BUILD_RELEASE_ROOT/{views,modules}` |
| build-cache name | `cse-initial-conversion-trials` |
| build-cache URL | `$BUILDCACHE_URL` expanded to an absolute `file:///...` URL |
| permissions | CSE group read/write in both trees; publication adds consumer read/execute while retaining no other write, then is version-frozen after acceptance |
| package repository | reviewed trial recipe pin |

The roster installs CMake 3.31.12 and 4.4.2. CMake 3.31.12 is the preferred
build tool and is an explicit dependency of the CMake-built trial roots. CMake
4.4.2 is the second public version. Both versions come from the rendered local
recipe extension layered over `spack-packages v2026.06.0`.

The helper selects the newest verified older GCC compiler scope as the compiler
that builds the GCC 12.5.0 producer. Set `CSE_SHARED_COMPILER_SEED_REF` only to
choose a different reviewed compiler from the catalog. This is a compiler
dependency inside each GCC environment, not a separate preparatory environment
or user-facing surface. Every GCC producer root explicitly enables `+binutils`.
Downstream groups order and expose that producer through `needs: [compiler]`
and select it through the conditional `%cse_shared` toolchain. `needs` alone is
not a compiler selector. All four GCC lockfiles must record the same compiler
hash.

For build-sourced Open MPI, the helper combines verified common-scope facts
with `stack-content/pilots/cse-pilot/openmpi-policy.yaml`. The current trial
policy is Open MPI 4.1.8 with verified `ucx+thread_multiple`, at most one
verified scheduler (`slurm` or `pbs`), and retained `mpirun`/`mpiexec` support.
When neither scheduler is present, the helper emits `schedulers=none +rsh` and
does not add a scheduler dependency. This is the standard launcher path; it
does not provide direct `srun` or PBS/TM integration. On Slurm,
the helper emits `+legacylaunchers` and enables direct `srun --mpi=pmi2` with
`+pmi` only when the static manifest records both an advertised `pmi2` launch
plugin and a verified PMI2 development interface. Otherwise it emits `~pmi`
and keeps the mpirun path. It disables CUDA and Lustre and keeps ROMIO without
a Lustre filesystem plugin. The generated root includes an exact
`^ucx@...+thread_multiple` constraint and, when a scheduler is selected, its
exact dependency constraint. A detected
Lustre filesystem or external does not change that spec. Do not depend on
ambient configure detection or run a separate scheduler probe while creating
values.

The selected surface compiler and MPI provider are applied to built Open MPI
and its payload through a conditional toolchain; the portable CPU target stays
a common preference at this boundary. Do not append a blanket `target=...`
constraint to the Open MPI producer or MPI payload roots. In Spack 1.2.2 that
root constraint can propagate into dependency externals and incorrectly require
the site Slurm or UCX installation to claim the source-build target. The lock
verifier is the final enforcement point:
Open MPI and every source-built payload must resolve to the selected surface
compiler and portable target, while site Slurm and UCX remain external with
their inspected architecture.

Do not work around an external solve failure by building a private Slurm, PBS,
or UCX. When a verified scheduler external is selected, the trial integrates
with that site scheduler and the selected fabric runtime. When no scheduler is
available, use the explicit schedulerless launcher configuration instead. A
separately built scheduler is not the site's controller/client runtime, and
replacing the reviewed UCX changes the fabric integration being tested.

Use `source: external` for the platform compiler and for platform-provided MPI.
Use `source: build` only for the selected MPI implementation that CSE will
build, such as OpenMPI on a non-Cray system. Do not insert dummy catalog scopes.

Observed provider names and Spack package names can differ. Classic Intel is
reported as `intel` under `scopes/compilers/intel/...`, but the values file uses
`intel-oneapi-compilers-classic`. Intel MPI is reported under
`scopes/mpi/intel-mpi/...`, but the values file uses `intel-oneapi-mpi`.
LLVM-based Intel is reported as `oneapi` when the verified drivers are `icx`,
`icpx`, and `ifx`; do not relabel that compiler as Classic Intel because its
module suite is named `intel`. A oneAPI build environment must also include a
verified GCC compiler scope because `intel-oneapi-runtime` links against
`gcc-runtime`. That supporting GCC registration does not change the compiler
selected for the platform roots.

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
original `$CATALOG` path after initialization. The Initial Conversion Trials
workspace blueprint also
normalizes only the newly generated workspace to the declared access policy.
For restricted build values, directories are `2770`, ordinary files are
`0660`, and executable entry points are `0770`. The dedicated setgid parent
supplies the recorded `$CSE_GROUP`; no sticky bit is used.

Use `--overwrite` only after reviewing and deliberately replacing the existing
workspace.

```bash
cat "$BUILD_WORKSPACE/README.md"
cmp "$SYSTEM_DIR/profile.yaml" "$BUILD_WORKSPACE/catalog/profile.yaml"
sed -n '1,260p' "$BUILD_WORKSPACE/workspace-manifest.yaml"
find "$BUILD_WORKSPACE/environments" -name spack.yaml -print | sort
find "$BUILD_WORKSPACE/catalog/scopes" -type f -print | sort
find "$BUILD_WORKSPACE/configs/environments" -name modules.yaml -print | sort
find "$BUILD_WORKSPACE/modulefiles" -type f -print | sort
cat "$BUILD_WORKSPACE/env/setup-build-env.sh"
cat "$BUILD_WORKSPACE/env/select-build-context.sh"
cat "$BUILD_WORKSPACE/configs/common/config.yaml"
cat "$BUILD_WORKSPACE/configs/common/mirrors.yaml"
test -x "$BUILD_WORKSPACE/cse-build"
test -r "$BUILD_WORKSPACE/BUILDER-HANDOFF.md"
"$CSE_PYTHON" \
  "$BUILD_WORKSPACE/scripts/verify-lockfiles.py" --workspace-only
test -w "$BUILD_WORKSPACE"
test "$(stat -c %G "$BUILD_WORKSPACE")" = "$CSE_GROUP"
test "$(stat -c %a "$BUILD_WORKSPACE")" = 2770
test "$(stat -c %a "$BUILD_WORKSPACE/cse-build")" = 770
test "$(stat -c %a "$BUILD_WORKSPACE/README.md")" = 660
test "$(stat -c %a "$BUILD_WORKSPACE/BUILDER-HANDOFF.md")" = 660
```

The workspace-input check verifies the generated `cse_trials` package
repository before any solve or build. It currently confirms that the Dakota
6.23.0/6.24.0 Boost.System compatibility overlay is present and complete. The
check is independent of the selected system, compiler, and MPI provider; the
same overlay is used by both compiler surfaces on Blueback, Fran, Raider, and
Wheat. Generated `cse-build` entry points repeat this check before every
action, so an incomplete workspace fails before concretization or installation
instead of later in Dakota's CMake configuration.

Pulling `stack-content` does not modify a workspace that was already rendered.
Before package installation starts, replace an unaccepted older workspace with
the current blueprint by following **Recovery: replace an unaccepted workspace
after a blueprint correction**. If installation has started in an unfinished trial, keep the same
workspace and evidence, apply the complete recipe correction, and use
`concretize --environment COMPILER/LANE --reconcretize` followed by
`resume --environment COMPILER/LANE`. These helpers retain the old selected
lock and solve afresh so a corrected dependency cannot be silently reused.
An accepted/published release remains immutable.

If this exact dedicated workspace was initialized by an older checkout and
already contains lockfiles or partial installs, do not use `--overwrite` merely
to repair access. Stop every process using the workspace, confirm the guarded
path and manifest below, then have the workspace owner or filesystem
administrator repair that tree in place. These commands preserve all files and
lockfiles:

```bash
case "$BUILD_WORKSPACE" in
  "$CSE_RESTRICTED_ROOT"/workspaces/*) ;;
  *) printf 'refusing unexpected workspace: %s\n' "$BUILD_WORKSPACE" >&2; exit 1 ;;
esac
test -f "$BUILD_WORKSPACE/workspace-manifest.yaml"

chgrp -R "$CSE_GROUP" "$BUILD_WORKSPACE"
find "$BUILD_WORKSPACE" -type d -exec chmod 2770 {} +
find "$BUILD_WORKSPACE" -type f -perm /111 -exec chmod 0770 {} +
find "$BUILD_WORKSPACE" -type f ! -perm /111 -exec chmod 0660 {} +

# Backfill the review copy only when this workspace predates profile snapshots.
if [ ! -f "$BUILD_WORKSPACE/catalog/profile.yaml" ]; then
  install -m 0660 -g "$CSE_GROUP" \
    "$SYSTEM_DIR/profile.yaml" "$BUILD_WORKSPACE/catalog/profile.yaml"
fi
cmp "$SYSTEM_DIR/profile.yaml" "$BUILD_WORKSPACE/catalog/profile.yaml"
```

Run the access checks above as the operator, then repeat the read, execute, and
workspace-write checks from the receiving builder's login before resuming.

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
well. Compiler, Foundation, Core, and build-tool producer roots carry their
explicit surface compiler/target bindings, and every GCC producer root contains
`+binutils`. MPI producers and payload roots
deliberately do not append blanket compiler/target constraints; their
environment includes `configs/surfaces/<surface>/compiler.yaml`, which selects
the surface's `c`, `cxx`, and `fortran` providers, while the common target
preference selects the portable target for built nodes. The Miniforge
Core-independent root must use the generic binary target. Lock verification,
not the presence of `%compiler target=...` text on every root, proves the
resulting compiler and architecture bindings.

For an external MPI provider, inspect the applicable surface
`packages.yaml`. Its virtual `mpi:require` entry must select only the provider
and version, for example `cray-mpich@9.1.0`; it must not append the portable
source-build target. The platform external keeps the architecture Spack assigns
to its inspected installation. For build-sourced Open MPI, `mpi:require`
contains the exact provider variants but no `%compiler`, `target=...`, or
machine-external dependency constraints. The separate MPI producer root owns
the exact `^ucx` and scheduler dependencies.

For a non-Cray Open MPI environment, also inspect the generated MPI root. It
must contain `fabrics=ucx`, the scheduler variant, `~cuda`, `~lustre`, `+romio`,
`romio-filesystem=none`, and exact UCX and scheduler dependency constraints. A
Slurm environment must also contain `+legacylaunchers` and must use `+pmi` only
for a verified PMI2 path; otherwise it contains `~pmi`. A PBS environment uses
`~pmi` under the current trial policy.

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

There is one shared build workspace for a system and trial release, not one
workspace per builder. `init-workspace` creates that workspace once. A
receiving builder does not run `init-workspace`, copy the workspace into a home
directory, or recreate the generating tools. The receiving builder enters and
resumes the same shared workspace.

If the shared workspace has not been initialized, the handoff is not ready.
The operator must first complete Step 8, including generation of `cse-build`.
`cse-build` cannot create a workspace from only a Spack checkout or a static
catalog.

The handoff is the absolute path to the complete shared workspace plus its
current checkpoint. It is not a copy of one `spack.yaml`. Before another
builder takes over, record:

- whether the handoff stops before concretization, after lock verification, in
  the middle of installation, or after lane validation;
- the last environment attempted and its result;
- the exact workspace and evidence paths;
- the approved Spack version, tag, and commit from `inputs/spack.*`;
- the selected Spack runtime mode and root, plus the shared root when one is
  available; and
- whether the receiving builder is authorized to sign and push build-cache
  content.

Before sending the path, the operator verifies that it names an initialized
handoff:

```bash
test -d "$BUILD_WORKSPACE"
test -r "$BUILD_WORKSPACE/workspace-manifest.yaml"
test -x "$BUILD_WORKSPACE/cse-build"
printf 'CSE workspace: %s\n' "$BUILD_WORKSPACE"
```

The receiving builder needs only that printed absolute path, membership in the
`cse` group, and the site-provided absolute writable `WORKDIR`. The builder
does not source the operator-session file and does not activate Spack first.
`cse-build` is executable Bash. A default `tcsh` login runs it directly through
its shebang; the builder does not source it and does not need to change the
login shell. The exact reviewed raw facts are available for inspection at
`catalog/profile.yaml`, but the builder does not edit or pass that file to
Spack.
For a workspace recorded against the shared Spack checkout, the first entry is:

```bash
: "${WORKDIR:?WORKDIR must be set by the site environment}"

export CSE_HANDOFF_WORKSPACE="<absolute-shared-workspace-path>"
test -d "$CSE_HANDOFF_WORKSPACE"
test -r "$CSE_HANDOFF_WORKSPACE/workspace-manifest.yaml"
test -x "$CSE_HANDOFF_WORKSPACE/cse-build"
test -w "$CSE_HANDOFF_WORKSPACE"

cd "$CSE_HANDOFF_WORKSPACE"
./cse-build login status --spack-mode shared
```

Follow the checkpoint reported by `status`. If every lockfile already exists,
verify it before building:

```bash
./cse-build login verify --spack-mode shared
```

If lockfiles are missing, create only the missing locks instead:

```bash
./cse-build login concretize --spack-mode shared
```

Then create or reattach the prepared build session:

```bash
./cse-build login --spack-mode shared
```

No system, release, compiler, MPI, catalog, install-tree, view, module, or
environment values are entered. The generated entry point reads the recorded
workspace data, selects or provisions the exact approved shared or local Spack
checkout, creates private cache/keyring paths for the current builder,
activates the generated configuration, reports the lock checkpoint, and
creates or reattaches a context-specific tmux session for this system and
release. Running the same command after a disconnect reattaches on the same
host. Use `./cse-build login shell` to bypass tmux. From a compute allocation,
use `./cse-build compute` or `./cse-build compute shell`. If tmux is unavailable,
the command falls back to the prepared shell.

On later logins, the receiving builder repeats only the `WORKDIR` check, goes
to the same absolute workspace path, and runs
`./cse-build login --spack-mode shared`. `cse-build` derives the workspace identity
from its own location and recreates that builder's private Spack cache and
keyring paths as needed.

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

Normal path: continue directly to Step 9. Switching between login and compute
uses the same workspace and does not require a recovery procedure.

### Shared generated-content permission recovery

The restricted build contract is owner/group parity: directories are `2770`,
ordinary files are `0660`, executable files are `0770`, every entry carries the
recorded CSE group, and no access is granted to others. It applies to the shared
workspace and lockfiles, source cache, builder-partitioned misc cache, views,
modules, and a file-backed build cache. Installed package prefixes use the same
policy through Spack `packages:all:permissions`; do not recursively chmod the
install tree around Spack's database and prefix locks.

This is the complete all-system contract, not a misc-cache-only policy:

| Path class | How owner/`cse` group parity is maintained |
|---|---|
| Restricted workspace, included catalog snapshot, environment YAML, lockfiles, reports, and generated controls | Workspace initialization applies `2770`/`0660`/`0770`; the generated launcher normalizes owner-created entries on entry and exit and verifies the entire workspace for handoff. |
| Shared source cache | The generated launcher recursively normalizes owner-created entries and verifies the complete cache tree. |
| Misc/provider/concretization cache | Each builder uses `cache/misc/$USER`; the generated launcher recursively normalizes that partition and verifies it. Other builders use their own partitions. |
| Views and generated module trees | The generated launcher recursively normalizes owner-created entries after Spack and verifies the complete trees. |
| File-backed build cache | The generated launcher recursively normalizes owner-created entries after Spack and verifies the complete tree. |
| Spack package install prefixes | Rendered `packages:all:permissions` assigns the recorded group and group read/write policy as Spack creates each prefix. The launcher verifies/prepares only the install-tree root and never recursively chmods Spack's database, locks, or prefixes. |
| Static-catalog and evidence roots outside the workspace | Step 5 creates dedicated setgid roots for the recorded group and the operator session uses `umask 0007`; the reviewed catalog is frozen. The workspace carries its own catalog snapshot for builder handoff. |
| Build stage, `SPACK_USER_CACHE_PATH`, bootstrap state, and GPG home | Intentionally private per builder. A receiving builder gets new private paths; these are not shared or repaired for handoff. |

Every assigned builder must be a member of the recorded `cse` group and enter
through the refreshed `cse-build` or its prepared shell. Each builder can
normalize entries that builder owns. Group modes then allow another `cse`
member to traverse, read, update, rename, and continue the shared work. If
verification finds an entry owned by someone else that was never normalized,
that owner or the filesystem administrator must correct it once.

Use this procedure when another builder receives `PermissionError`, cannot
search a directory, or cannot read/replace generated content on any of those
surfaces. Spack and other tools may explicitly create `0600` files or `0700`
directories; setgid, `umask 0007`, and a group-writable parent cannot correct
those entries by themselves. A recursive `chmod 660` is also invalid because a
directory needs execute/search permission.

The corrected generated config keeps downloads in the shared source cache but
sets `config:misc_cache` to `${SPACK_MISC_CACHE_PATH}`. `cse-build` exports
that variable as a builder-named partition below the shared restricted root:

```text
$CSE_RESTRICTED_ROOT/cache/misc/$USER
```

Stop processes using the affected workspace and follow the complete
[existing-trial maintenance procedure](../../stack-content/pilots/cse-pilot/CONTROL-REFRESH.md).
It restores the saved login/session paths, selects reviewed tools, and prepares
`REFRESH_VALUES` as a separate copy of the recorded values when current render
fields are needed. The earlier shortcut that regenerated `BUILD_VALUES` from
current discovery and refreshed the default `all` scope is superseded.

A permission-helper or operational-config correction is a separately reviewed
`--scope controls` change. Verify its prerequisite inventory/helper admission
and the new launcher's graph policy against the retained inputs before applying
it. For entrance/lane files alone, choose `--scope presentation`; package-module
policy and generated package modules are separate operations in the guide.
Keep an older prepared launcher when its replacement has not been qualified.

After the reviewed controls operation, inspect the existing workspace:

```bash
grep -F 'misc_cache: ${SPACK_MISC_CACHE_PATH}' \
  "$BUILD_WORKSPACE/configs/common/config.yaml"

cd "$BUILD_WORKSPACE"
./cse-build login status
./cse-build login verify
```

This maintenance path does not concretize. If an unfinished environment still
needs its first lock, return to Step 9 deliberately; a permission or module
correction is not a reason to change existing locks. Current qualified controls
normalize entries owned by the active builder across generated handoff surfaces
and verify the group/no-world contract. Use `status` as the cross-user handoff
gate after parallel actions stop. A prepared interactive shell normalizes its
builder's entries when it exits. Each builder receives a separate recorded
misc-cache partition; current controls also bind that partition to the reviewed
overlay inventory.

#### One-time misc-cache traversal repair after accidental `chmod 660`

The permanent controls above apply to all shared handoff surfaces. The manual
commands below are narrower only because they repair the specific misc-cache
tree that was accidentally changed to `660`; they are not the general
permission implementation.

If the missing directory search bit prevents `cse-build` from reaching that
misc tree, stop all processes using the tree and have the owning builder repair
only the exact affected root. On the affected system, set `BROKEN_ROOT` to the
reported misc root; do not point it at the release root, install tree, or a
broad shared parent:

```bash
export BROKEN_ROOT="$CSE_RESTRICTED_ROOT/cache/misc"
export CSE_GROUP="<recorded-cse-collaboration-group>"
test -d "$BROKEN_ROOT"
: "${CSE_GROUP:?CSE_GROUP must name the collaboration group}"

# Restore traversal in preorder so find can descend into nested 0660 dirs.
chmod 0770 "$BROKEN_ROOT"
find "$BROKEN_ROOT" -xdev -user "$USER" -type d \
  -exec chmod 0770 {} \;

find "$BROKEN_ROOT" -xdev -user "$USER" -type d \
  -exec chgrp "$CSE_GROUP" {} +
find "$BROKEN_ROOT" -xdev -user "$USER" -type f \
  -exec chgrp "$CSE_GROUP" {} +
find "$BROKEN_ROOT" -xdev -user "$USER" -type d \
  -exec chmod 2770 {} +
find "$BROKEN_ROOT" -xdev -user "$USER" -type f -perm -0100 \
  -exec chmod 0770 {} +
find "$BROKEN_ROOT" -xdev -user "$USER" -type f ! -perm -0100 \
  -exec chmod 0660 {} +
```

Then run `./cse-build login status` as that owner. If it reports an entry owned
by someone else, stop: that owner or the filesystem administrator must repair
it. Do not use `sudo chmod -R` as a substitute for resolving mixed ownership.

Every builder must enter through the refreshed `cse-build` or a prepared shell
launched by it. Before a handoff, the originating builder exits the prepared
shell and runs `./cse-build login status`; the receiving builder runs the same
command. The former
unpartitioned entries directly below `cache/misc` and the earlier private
`$WORKDIR/$USER/.../misc` tree are no longer consulted. Retain or remove those
obsolete entries only under the filesystem owner's normal recovery policy.

### Pre-install workspace refresh

Use this procedure when the profile/catalog selections remain valid but the
current trial blueprint, GCC producer constraint, runtime-support scope, or
workspace entry scripts changed before package installation was accepted. It
replaces the generated workspace and its unaccepted lockfiles. It does not
delete the static catalog, shared Spack install tree, source cache, or build
cache.

When GCC 12.5.0 appears without `+binutils`, check the policy source, rendered
inputs, and locks before replacing anything. The complete compiler policy is
owned by the Stack Content blueprint; updating Cluster Inspector, Stack
Composer, or the static catalog alone does not change it. The policy requires
`+binutils` on the producer, a conditional `%cse_shared` language/MPI
toolchain on downstream roots, and `needs: [compiler]` on downstream build
groups. The older seed compiler remains usable only to build the managed
producer:

```bash
source "$CSE_OPERATOR_SESSION_FILE"

git -C "$CONTENT" pull --ff-only origin codex/simplified-render-plan
git -C "$CONTENT" log -1 --oneline

grep -R -n --include=spack.yaml \
  "gcc@12.5.0+binutils languages='c,c++,fortran'" \
  "$BUILD_WORKSPACE/environments/gcc"

grep -R -n --include=spack.yaml \
  '%cse_shared' \
  "$BUILD_WORKSPACE/environments/gcc"

grep -n '%c=gcc@12.5.0+binutils' \
  "$BUILD_WORKSPACE/configs/surfaces/shared/toolchains.yaml"

"$CSE_PYTHON" \
  "$BUILD_WORKSPACE/scripts/verify-lockfiles.py" \
  --workspace-only

cd "$BUILD_WORKSPACE"
./cse-build login verify
```

The first `grep` must show one producer in each GCC environment. The second
must show the conditional selector on every downstream root group, and the
third must show the generated per-language binding. The workspace-only gate
checks the producer, every required `needs` relationship, and the toolchain
before a solve. After concretization, `verify` also requires every downstream
GCC-surface root to use the exact same concrete hash as the single
`gcc@12.5.0+binutils` producer.

Missing `needs` relationships, `%cse_shared` selectors, or the shared
toolchain file mean the workspace was generated from an older blueprint or the
session points at a different workspace. A downstream-hash mismatch means the
locks were created from older inputs. A controls-only refresh cannot repair either case
because it deliberately preserves environment YAML and lockfiles.
The replacement procedure below is retained for the historical pre-install
compiler-policy repair only: no installation or build-cache promotion may have
started, and its locks must remain unaccepted diagnostic output. If any package
installation was attempted, preserve that workspace and use a separate candidate
release instead. For completed-build module/control maintenance, use
[CONTROL-REFRESH.md](../../stack-content/pilots/cse-pilot/CONTROL-REFRESH.md).
A blueprint-only compiler-policy correction does not require new observed
machine facts when the recorded static catalog remains correct.

First stop every process using the workspace, synchronize the four repositories
in Step 2, rebuild Stack Composer when `cse_session_status` reports it stale,
and reload the operator session. Then verify the selected roots and regenerate
the values from the saved provider selections:

```bash
source "$CSE_OPERATOR_SESSION_FILE"
test "$CSE_RESTRICTED_ROOT" = "$CSE_TRIAL_ROOT/restricted"
test "$CSE_PUBLISHED_ROOT" = "$CSE_TRIAL_ROOT/published"
cse_session_status

"$CSE_PYTHON" \
  "$CONTENT/pilots/cse-pilot/scripts/create-build-values.py"
```

Before this eligible pre-install replacement, retain its diagnostic locks under
the evidence root. If installation was attempted, stop this procedure and keep
the entire workspace and installed prefixes for the separate candidate path:

```bash
REFRESH_EVIDENCE="$BUILD_EVIDENCE/pre-install-control-refresh"
install -d -m 2770 -g "$CSE_GROUP" "$REFRESH_EVIDENCE"
find "$BUILD_WORKSPACE/environments" -type f -name spack.lock -print > \
  "$REFRESH_EVIDENCE/lockfiles.list"
while IFS= read -r lockfile; do
  relative_lock="${lockfile#"$BUILD_WORKSPACE/environments/"}"
  destination="$REFRESH_EVIDENCE/locks/${relative_lock%/spack.lock}"
  install -d -m 2770 -g "$CSE_GROUP" "$destination"
  cp -p "$lockfile" "$destination/spack.lock"
done < "$REFRESH_EVIDENCE/lockfiles.list"
```

Review `lockfiles.list` before continuing. An accepted lock, any installation
attempt or build-cache promotion excludes this pre-install replacement; use the
release recovery policy instead.

Render the current workspace in place, then recreate and verify all eight
locks through the login context:

```bash
"$CSE_PYTHON" "$STACK_COMPOSER" init-workspace \
  --blueprint "$CONTENT/pilots/cse-pilot" \
  --catalog "$CATALOG" \
  --values "$BUILD_VALUES" \
  --output "$BUILD_WORKSPACE" \
  --overwrite

cd "$BUILD_WORKSPACE"
./cse-build login concretize
./cse-build login verify
```

When a correction changes observed provider facts rather than only workspace
templates, rerun the Step 4 system-fragment/merge/verify sequence and Step 6
`render-static` before this refresh. The selected system notes identify any
provider-specific seed scope or compatibility check that must also be retained.

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
./cse-build login concretize
```

This creates only missing lockfiles, preserves locks already handed over, and
runs the lock verifier when all eight exist. The explicit commands below are
the operator inspection and troubleshooting form of the same process.

The generated wrapper also controls the selected external-module boundary.
Before activating Spack, it unloads an exact selected compiler or MPI module
when that module is already present in `LOADEDMODULES`. Spack 1.2.2 otherwise
compares `LOADEDMODULES` before and after `module load` and incorrectly reports
an already-loaded module as a failed load. This cleanup occurs only in the
`cse-build` process: it does not purge unrelated site/startup modules or alter
the caller's parent shell. Spack then loads the recorded external module when
the concrete DAG requires it.

Start from the site's normal clean shell. Do not manually load the selected
`PrgEnv-*`, compiler, Cray MPICH, Intel MPI, or Open MPI modules before running
`cse-build`. The exact module arrays in the catalog's external `packages.yaml`
records are the durable source of truth. If that array is incomplete, correct
the profile/catalog and regenerate the workspace; do not compensate with an
ambient module load. On Cray, a GNU flavor suffix such as `ofi/gnu/12.3` is a
same-family compiler floor and does not authorize loading a different GNU
programming environment in the parent shell.

Activate the pinned Spack checkout first. The generated workspace setup script
loads workspace values; it does not activate Spack.

```bash
verify_spack_tool_root
source "$SPACK_ROOT/share/spack/setup-env.sh"
SPACK_VERSION_OUTPUT="$(spack --version)"
test "${SPACK_VERSION_OUTPUT%% *}" = "$SPACK_VERSION"
verify_spack_tool_root

source "$BUILD_WORKSPACE/env/select-build-context.sh"
cse_select_build_context login
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

cd "$BUILD_WORKSPACE"
./cse-build login verify
```

The wrapper deliberately runs the verifier through the pinned Spack runtime's
host Python. The generated verifier therefore supports the oldest host Python
recorded by the selected system; do not replace it with syntax accepted only by
the operator bootstrap Python.

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
Confirm that no fourth Python appears as a build dependency: Ninja and Dakota
must reuse Python 3.12.13. In each MPI environment, Dakota must reuse the
direct Boost 1.90 MPI root, netlib-lapack 3.12.1, CMake 3.31.12, and the lane's
single MPI provider. A matching name and version with a different hash is a
failed gate.

Gate: all eight restricted lockfiles exist and pass review.

After this gate, the teammate builds the approved lockfiles without
reconcretizing them. A package build failure does not by itself authorize a new
solve. Diagnose and retry the same lock first. Reconcretize only when an owned
input or approved package/provider choice must change; then retain the failed
evidence, regenerate the affected locks, rerun lock verification, and follow
the same-release/new-release rule in the recovery section.

When a package recipe, source patch, or external-provider record changes after
the affected roots are already present in `spack.lock`, force only that
environment to regenerate its roots while reusing unchanged dependencies:

```bash
ENVIRONMENT_PATH="$BUILD_WORKSPACE/environments/<compiler>/<lane>"

spack -e "$ENVIRONMENT_PATH" find -cl
spack -e "$ENVIRONMENT_PATH" concretize -f --reuse-deps -j 1
spack -e "$ENVIRONMENT_PATH" find -cl

cd "$BUILD_WORKSPACE"
./cse-build login verify
```

`--fresh` alone is not a recipe-change recovery command. It changes reuse
policy but preserves roots already recorded in the lock, which can produce
`No new specs to concretize` while leaving the old package hash in place. The
affected root hash must change; hashes for dependencies whose inputs did not
change should remain identical. Do not edit the lock or broadly clean already
installed prefixes.

## 10. Build and exercise every restricted lane

The generated Spack environment is the unit of build execution. `cse-build` is
an inspectable convenience entry point for resuming a prepared workspace; it is
not the build scheduler and is not required to launch an install. After the
eight-lock gate and shared-filesystem lock test pass, the operator may run the
environments sequentially or distribute distinct environments across available
build nodes.

Before any concurrent install, confirm all of the following:

- `./cse-build login verify` passes for all eight lockfiles;
- every process uses this same workspace, restricted install tree, Spack
  database, and exact pinned Spack identity;
- `config:locks:true` remains active; and
- the selected shared filesystem has passed the cross-node prefix-lock test.

Exact concrete hashes are coordinated at install time by Spack's shared
prefix/database locks. When two processes reach the same hash, one builds it
while the other waits; after a successful install, the waiting process reuses
the installed prefix. Different hashes may build concurrently. The lockfiles
define the concrete DAGs but do not schedule processes. If the process building
a shared hash fails, record the failure and retry the same locked install; do
not reconcretize unless an approved input must change.

On a login node with outbound network access, prefetch all locked sources:

```bash
cd "$BUILD_WORKSPACE"
./cse-build login fetch
```

### Restricted-network source handling

Run `./cse-build login fetch` before moving to a network-restricted build
context. If the target cannot reach every source from any approved connected
node, use the transfer procedure recorded in that system's
`stack-content/systems/<system>/runbook-notes.md`. Preserve the original
workspace and lockfiles; transfer only an approved source mirror into the
generated `config:source_cache`.

### Supported build execution choices

The simplest choice is one sequential wrapper process. On the selected build
node, enter or reattach the release tmux session and run:

```bash
cd "$BUILD_WORKSPACE"
./cse-build compute
./cse-build compute install
```

The wrapper processes the eight environments in their generated order. This is
useful for the first full trial pass, but it is not a required ordering once the
concurrency prerequisites above pass.

A second choice is the two-node compiler-surface split:

```bash
# Node 1: four GCC environments, sequential within this process
cd "$BUILD_WORKSPACE"
./cse-build compute install --surface shared

# Node 2: four platform-compiler environments, sequential within this process
cd "$BUILD_WORKSPACE"
./cse-build compute install --surface platform
```

The surface commands provide separate mutable per-user cache directories. Do
not start the same surface command twice.

A third choice is one selected environment through bare Spack. Start with the
generated shell so the approved runtime, module boundary, and workspace values
are active, then choose the environment explicitly:

```bash
cd "$BUILD_WORKSPACE"
./cse-build compute shell

environment="$SHARED_COMPILER_NAME/mpi-$SHARED_MPI_NAME"
environment_key="${environment//\//-}"
export SPACK_USER_CACHE_PATH="$SPACK_USER_STATE_ROOT/cache/$environment_key"
install -d -m 0700 "$SPACK_USER_CACHE_PATH"

spack -e "$CSE_BUILD_WORKSPACE/environments/$environment" \
  install --only-concrete -j "$BUILD_JOBS" --fail-fast
spack -e "$CSE_BUILD_WORKSPACE/environments/$environment" \
  env view regenerate
spack -e "$CSE_BUILD_WORKSPACE/environments/$environment" \
  module tcl refresh --delete-tree -y
```

A fourth choice is arbitrary environment fan-out. Open one prepared process per
distinct environment and run the bare-Spack block above with a unique
`environment` value and `SPACK_USER_CACHE_PATH`. These processes may be placed
on one node or distributed across several nodes. For example, the four GCC
environments may run independently on one compute node while the four platform
environments run independently on another. Do not launch the same environment
twice: its view and generated module root are owned by that one environment
process.

#### Two-node, eight-environment fast path

Use this optional fast path for an approved rebuild or when the trial needs to
exercise maximum environment-level concurrency. It starts one Spack process per
distinct environment: four shared/GCC workers on one compute node and four
platform-compiler workers on a second compute node. The normal sequential
wrapper remains the default for a first diagnosis because its output is easier
to follow.

Run the lock verification and connected-node fetch once before either compute
allocation starts:

```bash
cd "$BUILD_WORKSPACE"
./cse-build login verify
./cse-build login fetch
```

On each compute node, enter that node's generated tmux session and prepared
shell:

```bash
cd "$BUILD_WORKSPACE"
./cse-build compute
```

Define the launcher below once in each prepared shell. Each worker receives a
private user-cache directory and a separate log. Worker output is suppressed in
the launch window and remains available through the shared log path. The exit
file is written only after install, view regeneration, and module refresh have
finished.

```bash
export JOBS_PER_WORKER=16
export PARALLEL_RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
export LOG_ROOT="${BUILD_EVIDENCE:-$WORKDIR/$USER/cse-spack-logs/$CSE_SYSTEM_NAME/$CSE_TRIAL_RELEASE}/parallel-$(hostname -s)/$PARALLEL_RUN_ID"
mkdir -p "$LOG_ROOT"
chmod 0770 "$LOG_ROOT"

launch_environment() {
  local environment="$1"
  local environment_key="${environment//\//-}"
  local environment_dir="$CSE_BUILD_WORKSPACE/environments/$environment"
  local log="$LOG_ROOT/$environment_key.log"
  local exit_file="$LOG_ROOT/$environment_key.exit"

  test -r "$environment_dir/spack.yaml" || {
    echo "missing environment: $environment_dir" >&2
    return 2
  }
  test -r "$environment_dir/spack.lock" || {
    echo "missing lock: $environment_dir/spack.lock" >&2
    return 2
  }

  (
    export SPACK_USER_CACHE_PATH="$SPACK_USER_STATE_ROOT/cache/compute/$environment_key"
    install -d -m 0700 "$SPACK_USER_CACHE_PATH"

    set -o pipefail
    {
      echo "Starting $environment on $(hostname) at $(date -u)"
      spack -e "$environment_dir" \
        install --only-concrete -j "$JOBS_PER_WORKER" --fail-fast &&
      spack -e "$environment_dir" env view regenerate &&
      spack -e "$environment_dir" \
        module tcl refresh --delete-tree -y
    } 2>&1 | tee "$log" >/dev/null

    status="$?"
    printf '%s\n' "$status" > "$exit_file"
    exit "$status"
  ) &

  printf '%s  %s  %s\n' "$!" "$environment" "$log"
}
```

On the shared/GCC compute node, launch exactly these four workers:

```bash
SHARED_ENVIRONMENTS=(
  "$SHARED_COMPILER_NAME/core"
  "$SHARED_COMPILER_NAME/common"
  "$SHARED_COMPILER_NAME/serial"
  "$SHARED_COMPILER_NAME/mpi-$SHARED_MPI_NAME"
)

for environment in "${SHARED_ENVIRONMENTS[@]}"; do
  launch_environment "$environment"
done
jobs -l
```

On the platform-compiler compute node, launch exactly these four workers:

```bash
PLATFORM_ENVIRONMENTS=(
  "$PLATFORM_COMPILER_NAME/core"
  "$PLATFORM_COMPILER_NAME/common"
  "$PLATFORM_COMPILER_NAME/serial"
  "$PLATFORM_COMPILER_NAME/mpi-$PLATFORM_MPI_NAME"
)

for environment in "${PLATFORM_ENVIRONMENTS[@]}"; do
  launch_environment "$environment"
done
jobs -l
```

Keep each compute-node tmux session alive. Detaching with `Ctrl-b d` does not
stop its workers. A tmux session is normally node-local, so use one terminal or
scheduler attachment per compute node. The logs are stored on the shared
filesystem and may also be inspected from the login node.

List the logs and follow one worker at a time:

```bash
ls -lh "$LOG_ROOT"
tail -F "$LOG_ROOT/<environment-key>.log"
```

Within tmux, use `Ctrl-b c` to open a monitoring window, `Ctrl-b n` or
`Ctrl-b p` to move between windows, and `Ctrl-b [` to enter scrollback. Stop
`tail -F` with `Ctrl-c`; that does not stop the worker. After the processes
finish, every exit file must contain `0`:

```bash
for exit_file in "$LOG_ROOT"/*.exit; do
  printf '%s: ' "$exit_file"
  cat "$exit_file"
done
```

There is no node-wide Spack job server coordinating these processes.
`JOBS_PER_WORKER` is passed independently to every `spack install`. Four
workers at `-j 16` request up to roughly 64 compile jobs on that node; four at
`-j 24` request up to roughly 96. Therefore, `16` is a conservative four-worker
setting on a 92-core node, while `24` is reasonable on a 192-core node when
memory and site usage policy allow it. Leave CPU and memory headroom for Spack,
linkers, compression, and the operating system. Reduce the worker count or
`JOBS_PER_WORKER` when package memory use is high.

`BUILD_JOBS` (or `-j`) is a per-Spack-process build-job budget, not a node-wide
allocation. When several processes share one node, their budgets add together.
Choose per-process values whose total fits the allocated CPU cores and memory.
There is no automatic cross-process memory budget.

The explicit loop below is the inspection form of the sequential wrapper path:

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

### Restricted module presentation and team-review checkpoint

A completed package build does not by itself establish module readiness; older
workspaces may need current module settings or their first module generation.
Follow the [existing-trial maintenance procedure](../../stack-content/pilots/cse-pilot/CONTROL-REFRESH.md)
to check installed coverage, preserve recorded values and locks, select a
reviewed module-policy candidate when needed, and regenerate/test only the
required view and package-module output. Back up those external output roots
separately before regeneration.

The workspace `modulefiles/` tree contains the CSE compiler front doors and lane
selectors. Update those with `--scope presentation`; adopting newer controls or
a verifier is a separate qualification. Follow the guide's older-launcher route
if the retained `cse-build` lacks module actions. A newer verifier is not a
reason to edit old specs or locks.

After consumer checks pass and the build values still identify the restricted
module root, the qualified launcher can copy the ready presentation modules:

```bash
cd "$BUILD_WORKSPACE"
./cse-build login verify
./cse-build login publish-modules
```

Despite the action name, this is not public stack publication when the current
values are the restricted build values. It does not write under
`$CSE_PUBLISHED_ROOT`, run `publish-static`, create the cache-only publication
workspace, change permissions for users outside CSE, rebuild a package, or
reconcretize an environment. It creates the restricted module presentation for
CSE team review.

The corrected publisher writes compiler entrances into
`<recorded-module-root>/entrances/cse/`. In a clean team session, use only
`module use <recorded-module-root>/entrances`, then load the compiler entrance
and its lane. The entrance must expose the lanes automatically. Do not register
the parent package-module tree, whose recursive discovery exposes backing
modules before compiler/lane selection. Existing launchers need the reviewed
controls refresh before this publisher layout is available; existing login
registration changes remain a separate deliberate step.

Review the ready compiler front doors, lane selectors, dependency autoloads,
conflicts, and package-module visibility from clean login and compute sessions.
For CSE GCC plus external Cray MPICH, generate the private module preview from
the workspace's candidate presentation, load its compiler entrance and MPI
selector, and complete the native multi-node check recorded in the system
runbook. That selector remains outside
the restricted release module root until its gate passes.

After the platform and package checks below are complete, return to this
checkpoint for the team decision. Do not begin Step 11 before the review. The
outcomes are:

1. Accept the presentation. Record each accepted lane as `runtime-passed`, then
   continue to Step 11 for private build-cache promotion and Step 12 for public
   static-catalog and cache-only stack publication.
2. Change presentation controls only. Update the owning template or reviewed
   render-only values, preview/apply `--scope presentation`, and repeat this
   checkpoint without rebuilding or reconcretizing.
3. Change a Spack module projection without changing the DAG. Adopt the reviewed
   module-policy candidate when needed, regenerate only the affected output,
   then repeat the clean-session review.
4. Change a package, dependency, compiler, MPI provider, external, or concrete
   hash. Follow the DAG-changing recovery rule and do not reuse the old review
   result.

Apply the platform checklist after installation. A lane is not approved merely
because compilation finished. Exercise its compiler/wrappers, representative
libraries, module exposure, and applicable single-node and multi-node MPI
behavior on the target system.

For each build-sourced Open MPI surface on Slurm, compile one small MPI smoke
program with that surface's wrapper and run the same binary both ways from an
allocation:

```bash
mpirun -n 2 <mpi-smoke-program>
srun --mpi=pmi2 -n 2 <mpi-smoke-program>
```

The first command validates the retained Open MPI launcher. The second
validates direct Slurm launch through the PMI2 interface that Cluster Inspector
proved and the generated root selected. Record both results. On a PBS system,
exercise the reviewed `mpirun`/TM path instead; do not substitute an `srun`
test.

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

## 12. Publish the static catalog and initialize the publication workspace

Publish the retained restricted catalog as a separate configuration release
for package managers outside CSE. This promotion copies the reviewed bytes; it
does not rerun `render-static` and does not change `$CATALOG`:

```bash
PUBLISHED_AT="<reviewed-utc-publication-time>"
CATALOG_REVIEWER="<reviewer-name-or-role>"
CATALOG_APPROVER="<release-authority-name-or-role>"

"$CSE_PYTHON" "$STACK_COMPOSER" publish-static \
  --catalog "$CATALOG" \
  --output-root "$CSE_PUBLISHED_ROOT/catalogs" \
  --published-at "$PUBLISHED_AT" \
  --reviewed-by "$CATALOG_REVIEWER" \
  --approved-by "$CATALOG_APPROVER" \
  --group "$CSE_GROUP" \
  --set-current

PUBLISHED_CATALOG="$CSE_PUBLISHED_ROOT/catalogs/$SYSTEM_NAME/static/$CATALOG_RELEASE"
test -r "$PUBLISHED_CATALOG/publication.yaml"
(cd "$PUBLISHED_CATALOG" && sha256sum -c SHA256SUMS)
test -z "$(find "$PUBLISHED_CATALOG" -type d ! -perm 2775 -print -quit)"
test -z "$(find "$PUBLISHED_CATALOG" -type f -perm /111 ! -perm 0775 -print -quit)"
test -z "$(find "$PUBLISHED_CATALOG" -type f ! -perm /111 ! -perm 0664 -print -quit)"
test -z "$(find "$PUBLISHED_CATALOG" -perm -0002 -print -quit)"
test -z "$(find "$PUBLISHED_CATALOG" ! -group "$CSE_GROUP" -print -quit)"
```

The publication command rejects a non-relocatable catalog, unresolved MPI
dependencies, symlinked content, and an existing versioned public release. A
non-CSE package-manager environment pins `$PUBLISHED_CATALOG`. The optional
`current` pointer is for discovery only. The published namespace remains owned
by the CSE group. Versioned release directories are `2775`, executable files
are `0775`, and ordinary catalog files are `0664`. Every CSE package manager can
administer the tree; users outside CSE receive read/traverse access and no
released path grants `o+w`. The command still rejects an existing destination.
A correction uses a new versioned release rather than an in-place edit.

The static catalog publication and the CSE stack publication are separate
outputs. The static catalog contains reusable platform YAML. The stack release
contains prefixes, views, modules, evidence, and the approved workspace record.
The private build cache transports approved package binaries; it does not
contain the catalog, workspace, or lockfiles.

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
| `permissions.write` | `group`; CSE package managers can maintain installed prefixes while other users cannot write |

Keep the system, release, package/provider data, catalog scopes, package recipe
pin, collaboration group, and private build-cache URL identical. Permission
audience is the deliberate exception: restricted values are private to the CSE
group, whereas publication values add read and execute access for users outside
that group without granting them write access.

Initialize the publication workspace from the same retained restricted
`$CATALOG` used for the build workspace. Do not substitute
`$PUBLISHED_CATALOG`. The public catalog serves independent package-manager
consumers and is not a CSE build input.

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

First test the publication workspace's presentation with the
[private-preview procedure](../../stack-content/pilots/cse-pilot/MODULE-PRESENTATION.md).
After its required checks pass, copy ready entrances and lanes in the new
publication workspace using its qualified launcher:

```bash
cd "$PUBLISH_WORKSPACE"
./cse-build login publish-modules
```

Exercise that module hierarchy from clean sessions. Use the absolute entrance
path printed by the publisher; it must be below the module root recorded for
this publication workspace, not the restricted build root:

```bash
module use "/absolute/path/to/published/module-root/entrances"
module avail
module load "cse/<Compiler-public-name>"
module avail
```

Initially only CSE compiler entrances should be visible from this tree. Loading
one exposes its Core/Common modules and Serial/MPI selectors automatically;
do not add a lane path manually. Confirm the compiler front door did not select a payload lane and that its
recorded commands resolve:

```bash
test -z "${CSE_LANE:-}"
command -v "$CSE_CC" "$CSE_CXX" "$CSE_FC"
```

Load `Serial` and verify that only the Serial package-module root becomes
visible. Start another clean session and repeat for `MPI`. For CSE-built MPI,
the selector must load the
exact generated provider module. For platform Cray MPI, the selected PrgEnv
must already supply the reviewed Cray MPICH module and the selector must fail
if that exact prerequisite is absent. In either case verify:

```bash
module load MPI
module list
command -v "$CSE_MPICC" "$CSE_MPICXX" "$CSE_MPIFC"
```

Loading a conflicting second lane must fail. Load a version-sensitive package
such as NetCDF-C, confirm that its exact public HDF5 dependency is also loaded,
and confirm that an alternate HDF5 version is rejected.
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
run them against `$CSE_PUBLISHED_ROOT`, the parent of `$CSE_TRIAL_ROOT`, or
another shared parent:

```bash
for root in "$PUBLISH_WORKSPACE" "$PUBLISH_RELEASE_ROOT"; do
  test -n "$root" && test -d "$root" || exit 1
  case "$root" in
    "$CSE_PUBLISHED_ROOT"/*) ;;
    *) echo "refusing unexpected publication root: $root" >&2; exit 1 ;;
  esac
  test -z "$(find "$root" -xdev ! -group "$CSE_GROUP" -print -quit)" || {
    echo "publication content is not owned by group $CSE_GROUP: $root" >&2
    exit 1
  }
  find "$root" -xdev -type d -exec chmod 2775 {} + || exit 1
  find "$root" -xdev -type f -perm /111 -exec chmod 0775 {} + || exit 1
  find "$root" -xdev -type f ! -perm /111 -exec chmod 0664 {} + || exit 1
  test -z "$(find "$root" -xdev -type d ! -perm 2775 -print -quit)" || exit 1
  test -z "$(find "$root" -xdev -type f -perm /111 ! -perm 0775 -print -quit)" || exit 1
  test -z "$(find "$root" -xdev -type f ! -perm /111 ! -perm 0664 -print -quit)" || exit 1
  test -z "$(find "$root" -xdev -perm -0002 -print -quit)" || exit 1
done
```

This produces `2775` directories, `0775` executable files, and `0664` ordinary
files. The leading `2` on a directory is setgid, not sticky: new entries inherit
the directory's CSE group. Sticky is the leading `1` bit and is not used here.
Every path remains in the CSE group, CSE package managers retain write access,
and users outside the group cannot write. The release remains version-frozen by
procedure; make changes through controlled CSE maintenance or a new release,
not as an unrecorded in-place edit. Confirm the modes from both a second CSE
package-manager account and a non-CSE test account before exposing the module
front door.

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
| Static catalog | Restricted CSE review tree plus an immutable, versioned, world-readable release under `published/catalogs/<system>/static/<catalog-release>/` |
| Restricted workspace and lockfiles | Restricted CSE tree; source-build and validation record |
| Restricted install tree/views/modules | Restricted CSE tree; never user-facing |
| Private build cache | Restricted CSE tree; approved binaries only |
| Publication workspace and copied lockfiles | Published CSE tree; cache-only consumer |
| Published install tree/views/modules | Published CSE tree; user-facing after approval |
| Build and publication stages | Node-local or site scratch; disposable |
| Logs, hashes, runtime, and module evidence | Matching restricted/published evidence roots |

## System and platform details

System-specific commands, recovery state, provider selections, network
handling, and acceptance deltas live only in
`stack-content/systems/<system>/runbook-notes.md`. New system notes start from
`stack-content/systems/_template/runbook-notes.md`. Deployment-path ownership
remains defined by `deployment_inputs_and_ownership_v1.md`.
