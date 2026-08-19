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
  operator-sessions/<system>/<trial>/         # sourceable pre-workspace resume state
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
  every profiled build/runtime node type, including GPU-bearing nodes.
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
| Selected build node is unavailable, but the other recorded context can run the same locked target | Enter the same workspace through `./cse-build login` or `./cse-build compute`. The selector chooses an executable stage for that context; keep the existing locks and install tree. |
| Source build failure caused by a transient host/tool problem | Retry the failed lane after recording the log; earlier validated lanes remain valid. |
| Package recipe, patch, variant, compiler, MPI, or Spack version/commit change is required | Create a new trial release, reconcretize, and revalidate every affected lane. |
| Selected Spack checkout is dirty or does not match the pinned source/tag/commit | Stop. Replace the selected root with a clean checkout of the approved identity. Do not pull, switch branches, or run `spack isolate` in place. |
| Cluster Inspector fact or external module/prefix is wrong | Regenerate the profile, create a new catalog release and trial release, and restart at checkpoint 1. |
| Static catalog scope or toolchain is wrong | Fix the owning profile/catalog logic, create new catalog and trial releases, and restart at checkpoint 2. |
| Restricted workspace template or values are wrong | Before installation, unaccepted diagnostic locks from the current checkpoint may be discarded together and the working release reinitialized. After a lock has been accepted, installed, or promoted, create a new trial release. |
| A later lane fails while earlier lane locks and inputs remain unchanged | Keep the earlier evidence and retry only the failed lane. If a shared upstream hash changes, reconcretize and revalidate every dependent lane in a new release. |
| Build-cache push, index, or signing operation is interrupted | Retry the cache operation from the installed restricted specs; do not rebuild. |
| Publication reports a cache miss for an exact approved hash | Return to the restricted workspace, build and validate that exact locked hash, push it, and retry only the failed publication environment. If producing it requires a changed hash, create a new release. |
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
session generator is available. Use a lowercase system name: `blueback`,
`raider`, `wheat`, or `fran`.

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
  --spack-mode "<shared-or-local>"

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

Build Cluster Inspector with Go 1.22 or newer:

```bash
cd "$INSPECTOR"
make build
./cluster-inspector --help >/dev/null
git -C "$INSPECTOR" rev-parse HEAD \
  > "$CSE_TOOL_STATE_ROOT/cluster-inspector.commit"
```

Build Stack Composer in its repository-local Python environment:

```bash
cd "$COMPOSER"
test -x "$CSE_BOOTSTRAP_PYTHON"
"$CSE_BOOTSTRAP_PYTHON" -c \
  'import sys; assert sys.version_info >= (3, 9), sys.version'
"$CSE_BOOTSTRAP_PYTHON" -m venv .venv
test -x "$CSE_PYTHON"
"$CSE_PYTHON" -m pip install --upgrade \
  pip \
  "setuptools>=77" \
  "wheel>=0.44,<1" \
  "build>=1.2,<2"
"$CSE_PYTHON" -m pip install -e '.[dev]'
PYTHON="$CSE_PYTHON" bash scripts/build-pyz.sh
"$CSE_PYTHON" "$STACK_COMPOSER" --help >/dev/null

git -C "$COMPOSER" rev-parse HEAD \
  > "$CSE_TOOL_STATE_ROOT/stack-composer.commit"
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
compiler/MPI, and job count. The standard context keys are `login` and
`cpu_compute`; set the optional login/compute node-type overrides only when the
catalog uses different names. The second command reloads both the fixed session
values and the reviewed provider selections. Every later login gets the same
selections by sourcing only `activate.sh`; do not retype them into the shell.

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

The helper records two build contexts from exact keys under the catalog
manifest's `profile_facts.node_types`: `login` and `cpu_compute` by default. If
a site uses different keys, set `CSE_LOGIN_NODE_TYPE` or
`CSE_COMPUTE_NODE_TYPE` before generating the values. For each context the
helper records inspected writable candidates, temporary/node-local storage
first, other scratch paths next, and a context-specific `${WORKDIR}` fallback
last. At workspace entry, `cse-build` performs an actual execution probe and
selects the first usable path. Every path is namespaced by the Spack user,
system, trial release, and context. Do not replace these lists with one manual
stage path.

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
| build contexts/stages | reviewed login and compute profile node types; separate generated temp, scratch, then `${WORKDIR}` fallback lists selected by an execution probe |
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

The selected surface compiler and portable CPU target are applied to built
Open MPI and its payload through the surface language-provider preferences and
the common target preference. Do not append a blanket `%compiler` or
`target=...` constraint to the Open MPI producer or MPI payload roots. In Spack
1.2.2 those root constraints can propagate into dependency externals and
incorrectly require the site Slurm or UCX installation to claim the CSE
compiler and source-build target. The lock verifier is the enforcement point:
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
cat "$BUILD_WORKSPACE/env/select-build-context.sh"
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
well. Compiler, Foundation, Core, and build-tool producer roots carry their
explicit surface compiler/target bindings. MPI producers and payload roots
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
For a workspace recorded against the shared Spack checkout, the first entry is:

```bash
: "${WORKDIR:?WORKDIR must be set by the site environment}"

export CSE_HANDOFF_WORKSPACE="<absolute-shared-workspace-path>"
test -d "$CSE_HANDOFF_WORKSPACE"
test -r "$CSE_HANDOFF_WORKSPACE/workspace-manifest.yaml"
test -x "$CSE_HANDOFF_WORKSPACE/cse-build"

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

### One-time adoption of an existing Blueback workspace

Use this once when Blueback already has a static catalog, initialized workspace,
and lockfiles from the earlier environment-variable workflow but has no saved
operator-session file. Creating the session records the existing selections; it
does not probe Blueback, render a catalog, replace the workspace, or change a
lockfile.

This procedure is complete only after all three parts below pass. Part A saves
the operator session, Part B deliberately refreshes the generated workspace to
the current design, and Part C proves the workspace is ready to resume.

#### A. Record the existing Blueback workspace in an operator session

Start from a clean Bash shell with the site-provided `WORKDIR` set. The current
Blueback trial and shared-tools roots are recorded below; verify that they still
name the directories that directly contain `restricted/` and `published/`, and
`spack/1.2.2`, respectively. Fill in the bootstrap Python with the same reviewed
Python 3.9-or-newer executable used to build Stack Composer. Do not use the
repository `.venv` as its own bootstrap interpreter.

```bash
: "${WORKDIR:?WORKDIR must be set by the site environment}"

export WORK_ROOT="$HOME/STACK_TESTING"
export CONTENT="$WORK_ROOT/stack-content"
export STACK_BRANCH="codex/simplified-render-plan"
export CSE_BOOTSTRAP_PYTHON="<absolute-path-to-reviewed-python>"

# Existing Blueback trial layout. Verify these paths before continuing.
export BLUEBACK_TRIAL_ROOT="/p/app/CSE/initial-conversion-trials"
export BLUEBACK_TOOLS_ROOT="/p/app/CSE/tools"
export BLUEBACK_SPACK_MODE="shared"
export BLUEBACK_CATALOG_RELEASE="blueback-catalog-001"
export BLUEBACK_TRIAL_RELEASE="blueback-trial-001"

export BLUEBACK_EXISTING_CATALOG="$BLUEBACK_TRIAL_ROOT/restricted/catalogs/blueback/static/$BLUEBACK_CATALOG_RELEASE"
export BLUEBACK_EXISTING_WORKSPACE="$BLUEBACK_TRIAL_ROOT/restricted/workspaces/blueback/initial-conversion-trials/$BLUEBACK_TRIAL_RELEASE"
export BLUEBACK_SESSION_FILE="$WORK_ROOT/operator-sessions/blueback/$BLUEBACK_TRIAL_RELEASE/activate.sh"

test -x "$CSE_BOOTSTRAP_PYTHON"
test -d "$BLUEBACK_EXISTING_CATALOG"
test -f "$BLUEBACK_EXISTING_CATALOG/manifest.yaml"
test -d "$BLUEBACK_EXISTING_WORKSPACE"
test -f "$BLUEBACK_EXISTING_WORKSPACE/workspace-manifest.yaml"
if [ -f "$BLUEBACK_EXISTING_WORKSPACE/env/setup-build-env.sh" ]; then
  echo "Blueback setup-build-env.sh is present"
else
  echo "Blueback setup-build-env.sh is absent; the guarded workspace refresh will add it"
fi
BLUEBACK_LOCK_COUNT="$(
  find "$BLUEBACK_EXISTING_WORKSPACE/environments" \
    -mindepth 3 -maxdepth 3 -type f -name spack.lock -print |
    tee /dev/stderr |
    wc -l |
    tr -d '[:space:]'
)"
test "$BLUEBACK_LOCK_COUNT" -eq 8
test ! -e "$BLUEBACK_SESSION_FILE"
```

The lock listing must show the already reviewed Blueback lockfiles. If any
derived path above is wrong, correct the selected root or release value before
continuing. Do not create a second workspace to compensate for a wrong path.

Update only Stack Content first so the current session generator is available:

```bash
test -d "$CONTENT/.git"
git -C "$CONTENT" status --short --branch
```

The status review may show the already reviewed local Blueback profile, values,
or notes. Preserve those inputs. Stop for any unexplained change; do not stash,
discard, or overwrite it merely to make the pull clean. When the local changes
are all understood, continue:

```bash
git -C "$CONTENT" fetch origin
git -C "$CONTENT" switch "$STACK_BRANCH"
git -C "$CONTENT" pull --ff-only

"$CSE_BOOTSTRAP_PYTHON" \
  "$CONTENT/pilots/cse-pilot/scripts/create-operator-session.py" \
  --system blueback \
  --work-root "$WORK_ROOT" \
  --trial-root "$BLUEBACK_TRIAL_ROOT" \
  --tools-root "$BLUEBACK_TOOLS_ROOT" \
  --bootstrap-python "$CSE_BOOTSTRAP_PYTHON" \
  --spack-mode "$BLUEBACK_SPACK_MODE" \
  --catalog-release "$BLUEBACK_CATALOG_RELEASE" \
  --trial-release "$BLUEBACK_TRIAL_RELEASE"

source "$BLUEBACK_SESSION_FILE"
test "$CATALOG" = "$BLUEBACK_EXISTING_CATALOG"
test "$BUILD_WORKSPACE" = "$BLUEBACK_EXISTING_WORKSPACE"
cse_session_status
```

A fast-forward pull that would overlap a local file stops without replacing
that file.

Do not pass `--overwrite`. The generated `provider-selections.sh` may remain at
its commented template for this workspace refresh because the live workspace's
recorded build-values file remains authoritative. Review and populate provider
selections only when preparing a later workspace.

Stack Content is now current. Synchronize the remaining three repositories so
all four are on the same branch. Because this existing workspace has no saved
tool-build record, rebuild Stack Composer once and record its current commit
before running Part B. Cluster Inspector does not need to be rebuilt solely to
refresh the workspace; rebuild it before the next probe if
`cse_session_status` reports it stale.

```bash
for repo in cluster-inspector stack-composer stack-content stack-planning; do
  git -C "$WORK_ROOT/$repo" status --short --branch
done

for repo in cluster-inspector stack-composer stack-planning; do
  git -C "$WORK_ROOT/$repo" fetch origin
  git -C "$WORK_ROOT/$repo" switch "$STACK_BRANCH"
  git -C "$WORK_ROOT/$repo" pull --ff-only
done

source "$CSE_OPERATOR_SESSION_FILE"

cd "$COMPOSER"
"$CSE_BOOTSTRAP_PYTHON" -m venv .venv
test -x "$CSE_PYTHON"
"$CSE_PYTHON" -m pip install --upgrade \
  pip \
  "setuptools>=77" \
  "wheel>=0.44,<1" \
  "build>=1.2,<2"
"$CSE_PYTHON" -m pip install -e '.[dev]'
PYTHON="$CSE_PYTHON" bash scripts/build-pyz.sh
"$CSE_PYTHON" "$STACK_COMPOSER" --help >/dev/null
git -C "$COMPOSER" rev-parse HEAD \
  > "$CSE_TOOL_STATE_ROOT/stack-composer.commit"

cse_session_status
```

#### B. Refresh Blueback to the current workspace design

The operator session now points to the existing Blueback workspace, but Part A
does not update that workspace. Blueback's recorded values and lockfiles
predate required parts of the current design: the generic binary target, MPI
provider constraints, pinned Spack runtime metadata, group-write policy, and
current build-stage spelling. They also predate current environment and lock
verification rules. Do not copy only `cse-build` into that older workspace;
the current verifier is intentionally not valid for its older concrete DAG.

Prepare a temporary current values copy from the recorded selections and
render a temporary workspace for review. The helper does not modify the
recorded values. It derives only deterministic fields, records the Spack
runtime selected by the operator session, changes build-workspace permissions
to CSE group write, and changes the old `$user` build-stage token to `${USER}`.

Applying this refresh deliberately replaces the generated Blueback workspace,
including its eight old lockfiles. It does not remove packages already present
in the shared restricted Spack install tree or alter the static catalog. The
new workspace must be concretized and verified before any installation starts.

With the Blueback operator session and current tools loaded from Part A, run
the complete guarded block. Review the displayed environment and configuration
diffs. Type the exact confirmation only when the changes match the current
trial design.

```bash
(
  set -euo pipefail
  CONTROL_REFRESH_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/cse-control-refresh.XXXXXX")"
  trap 'rm -rf "$CONTROL_REFRESH_ROOT"' EXIT
  CONTROL_REFRESH_WORKSPACE="$CONTROL_REFRESH_ROOT/workspace"
  CONTROL_REFRESH_VALUES="$CONTROL_REFRESH_ROOT/cse-trials-build-values.yaml"

  if [ -f "$BUILD_WORKSPACE/inputs/cse-trials-build-values.yaml" ]; then
    CONTROL_REFRESH_SOURCE_VALUES="${BUILD_WORKSPACE}/inputs/cse-trials-build-values.yaml"
  elif [ -n "${BUILD_VALUES:-}" ] && [ -f "$BUILD_VALUES" ]; then
    CONTROL_REFRESH_SOURCE_VALUES="$BUILD_VALUES"
  else
    echo "recorded build values file is unavailable" >&2
    exit 1
  fi

  "$CSE_PYTHON" \
    "$CONTENT/pilots/cse-pilot/scripts/prepare-existing-workspace-values.py" \
    --source "$CONTROL_REFRESH_SOURCE_VALUES" \
    --output "$CONTROL_REFRESH_VALUES" \
    --spack-source "$SPACK_SOURCE" \
    --spack-version "$SPACK_VERSION" \
    --spack-tag "$SPACK_TAG" \
    --spack-commit "$SPACK_COMMIT" \
    --spack-mode "$SPACK_RUNTIME_MODE" \
    --shared-spack-root "$CSE_TOOLS_ROOT/spack/$SPACK_VERSION" \
    --initial-spack-root "$SPACK_ROOT"

  "$CSE_PYTHON" "$STACK_COMPOSER" init-workspace \
    --blueprint "$CONTENT/pilots/cse-pilot" \
    --catalog "$CATALOG" \
    --values "$CONTROL_REFRESH_VALUES" \
    --output "$CONTROL_REFRESH_WORKSPACE"

  echo "Review environment changes:"
  diff -ru --exclude=spack.lock \
    "$BUILD_WORKSPACE/environments" \
    "$CONTROL_REFRESH_WORKSPACE/environments" || true
  echo "Review configuration changes:"
  diff -ru \
    "$BUILD_WORKSPACE/configs" \
    "$CONTROL_REFRESH_WORKSPACE/configs" || true

  printf '%s' \
    "Type refresh-blueback to replace the workspace and old lockfiles: "
  read -r confirmation
  test "$confirmation" = "refresh-blueback"

  "$CSE_PYTHON" "$STACK_COMPOSER" init-workspace \
    --blueprint "$CONTENT/pilots/cse-pilot" \
    --catalog "$CATALOG" \
    --values "$CONTROL_REFRESH_VALUES" \
    --output "$BUILD_WORKSPACE" \
    --overwrite

  cd "$BUILD_WORKSPACE"
  test -x ./cse-build
  test -z "$(find environments -type f -name spack.lock -print -quit)"
  ./cse-build login concretize
  ./cse-build login verify
)
```

The temporary values copy exists only below `CONTROL_REFRESH_ROOT` and is
removed when the subshell exits. The initialized workspace records its own copy
under `inputs/`. Do not restore the superseded lockfiles after the refresh.

#### C. Verify and resume Blueback

Part B is complete only when `cse-build` exists, all eight current environments
have fresh lockfiles, and the generated verifier passes. Check the entry point
and its recorded workspace state:

```bash
source "$HOME/STACK_TESTING/operator-sessions/blueback/blueback-trial-001/activate.sh"
cd "$BUILD_WORKSPACE"

test -x ./cse-build
./cse-build login status
./cse-build login verify
```

Blueback is then current. On every later login, resume the same workspace with:

```bash
source "$HOME/STACK_TESTING/operator-sessions/blueback/blueback-trial-001/activate.sh"
cd "$BUILD_WORKSPACE"
./cse-build login
```

The final command enters or reattaches Blueback's prepared tmux session. From
there, use `./cse-build login fetch`. From a compute allocation, use
`./cse-build compute install`, a compute surface install, or a selected
bare-Spack environment command as described in Step 10. Do not rerun Parts A or
B on normal logins.

### Pre-install control refresh

Use this procedure when the profile/catalog selections remain valid but the
current trial blueprint, GCC producer constraint, runtime-support scope, or
workspace entry scripts changed before package installation was accepted. It
replaces the generated workspace and its unaccepted lockfiles. It does not
delete the static catalog, shared Spack install tree, source cache, or build
cache.

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

If any install was attempted, retain the current locks under the evidence root
before replacement. Do not remove installed prefixes merely because the
control workspace is being refreshed:

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

Review `lockfiles.list` before continuing. If package installation was already
accepted, stop and use the release recovery policy instead of this pre-install
refresh.

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

A Cray MPICH flavor-baseline correction changes observed provider facts, not
only workspace templates. For that correction on Blueback or Fran, rerun the
Step 4 system-fragment/merge/verify sequence and Step 6 `render-static` before
this refresh. Raider and Wheat do not repeat their probes for that Cray-only
change. A oneAPI platform surface on Wheat must include the reviewed GCC seed
scope that supplies `gcc-runtime`; use the same seed scope selected to build
GCC 12.5.0, not an arbitrary latest external GCC.

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
host Python. The generated verifier therefore supports Raider's Python 3.6
floor; do not replace it with syntax accepted only by the operator bootstrap
Python.

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

### Restricted-network source transfer

Do not move individual Spack stage directories or source archives by hand. For
a target such as Fran whose login and compute nodes cannot reach every source,
create one cumulative Spack source mirror on a connected staging system and
copy it into Fran's generated `config:source_cache`.

Use the sequence below after all eight Fran environments have been concretized
and `./cse-build login verify` passes. The original locked workspace remains on
Fran.
Only a temporary copy goes to the connected system, and only the resulting
source bundle comes back. Do not copy the connected system's workspace back
over the original Fran workspace.

#### A. Package the locked workspace on Fran

Source Fran's saved operator session, then create a private transfer area under
the site-provided work filesystem. `FRAN_TRANSFER_ROOT` is the one path that
must be carried into the transfer commands on the other system.

```bash
source "$HOME/STACK_TESTING/operator-sessions/fran/fran-trial-001/activate.sh"

cd "$BUILD_WORKSPACE"
./cse-build login verify

export FRAN_TRANSFER_ROOT="$WORKDIR/$USER/cse-fran-transfer/$TRIAL_RELEASE"
export FRAN_WORKSPACE_ARCHIVE="$FRAN_TRANSFER_ROOT/${TRIAL_RELEASE}-workspace.tar.gz"
export FRAN_WORKSPACE_DIGEST="$FRAN_WORKSPACE_ARCHIVE.sha256"

umask 0077
install -d -m 0700 "$FRAN_TRANSFER_ROOT"
tar -C "$(dirname "$BUILD_WORKSPACE")" -czf "$FRAN_WORKSPACE_ARCHIVE" \
  "$(basename "$BUILD_WORKSPACE")"
(
  cd "$FRAN_TRANSFER_ROOT"
  sha256sum "$(basename "$FRAN_WORKSPACE_ARCHIVE")" \
    > "$(basename "$FRAN_WORKSPACE_DIGEST")"
  sha256sum -c "$(basename "$FRAN_WORKSPACE_DIGEST")"
)

printf 'FRAN_TRANSFER_ROOT=%s\n' "$FRAN_TRANSFER_ROOT"
printf 'FRAN_WORKSPACE_ARCHIVE=%s\n' "$FRAN_WORKSPACE_ARCHIVE"
printf 'FRAN_WORKSPACE_DIGEST=%s\n' "$FRAN_WORKSPACE_DIGEST"
```

The archive contains the complete workspace so relative `include::` paths from
each environment to `configs/` and the catalog snapshot remain valid. It does
not contain the restricted Spack install tree, views, modules, build stages, or
build cache.

#### B. Copy and unpack the workspace on a connected system

First create the receiving directory on the connected staging system. Its path
is temporary per-user work space; it is not a CSE tools root, package install
tree, or build cache.

```bash
: "${WORKDIR:?WORKDIR must be set on the connected system}"
: "${USER:?USER must be set on the connected system}"

export TRIAL_RELEASE="fran-trial-001"
export CONNECTED_TRANSFER_ROOT="$WORKDIR/$USER/cse-fran-transfer/$TRIAL_RELEASE"
export CONNECTED_WORKSPACE_ARCHIVE="$CONNECTED_TRANSFER_ROOT/${TRIAL_RELEASE}-workspace.tar.gz"
export CONNECTED_WORKSPACE_DIGEST="$CONNECTED_WORKSPACE_ARCHIVE.sha256"
export FRAN_WORKSPACE="$CONNECTED_TRANSFER_ROOT/$TRIAL_RELEASE"

umask 0077
install -d -m 0700 "$CONNECTED_TRANSFER_ROOT"
printf 'CONNECTED_TRANSFER_ROOT=%s\n' "$CONNECTED_TRANSFER_ROOT"
```

Use one transfer route, not both.

For a direct connection, stay on the connected system, fill in the Fran login
endpoint, paste the exact `FRAN_TRANSFER_ROOT` printed on Fran, and pull the two
files:

```bash
export FRAN_SSH="<fran-user>@<fran-login-host>"
export FRAN_TRANSFER_ROOT="<exact-FRAN_TRANSFER_ROOT-printed-on-fran>"

rsync -av --partial --progress \
  "$FRAN_SSH:$FRAN_TRANSFER_ROOT/${TRIAL_RELEASE}-workspace.tar.gz" \
  "$CONNECTED_WORKSPACE_ARCHIVE"
rsync -av --partial --progress \
  "$FRAN_SSH:$FRAN_TRANSFER_ROOT/${TRIAL_RELEASE}-workspace.tar.gz.sha256" \
  "$CONNECTED_WORKSPACE_DIGEST"
```

When the connected system cannot reach Fran directly, run the following on an
approved relay workstation. Fill in both SSH endpoints, paste the exact Fran
and connected transfer roots printed by the earlier blocks, and keep the relay
directory private:

```bash
export TRIAL_RELEASE="fran-trial-001"
export FRAN_SSH="<fran-user>@<fran-login-host>"
export CONNECTED_SSH="<connected-user>@<connected-login-host>"
export FRAN_TRANSFER_ROOT="<exact-FRAN_TRANSFER_ROOT-printed-on-fran>"
export CONNECTED_TRANSFER_ROOT="<exact-CONNECTED_TRANSFER_ROOT-printed-on-connected-system>"
export RELAY_TRANSFER_ROOT="$HOME/cse-fran-relay/$TRIAL_RELEASE"

umask 0077
install -d -m 0700 "$RELAY_TRANSFER_ROOT"
rsync -av --partial --progress \
  "$FRAN_SSH:$FRAN_TRANSFER_ROOT/${TRIAL_RELEASE}-workspace.tar.gz" \
  "$RELAY_TRANSFER_ROOT/"
rsync -av --partial --progress \
  "$FRAN_SSH:$FRAN_TRANSFER_ROOT/${TRIAL_RELEASE}-workspace.tar.gz.sha256" \
  "$RELAY_TRANSFER_ROOT/"

(
  cd "$RELAY_TRANSFER_ROOT"
  sha256sum -c "${TRIAL_RELEASE}-workspace.tar.gz.sha256"
)

ssh "$CONNECTED_SSH" \
  "umask 0077 && install -d -m 0700 '$CONNECTED_TRANSFER_ROOT'"
rsync -av --partial --progress \
  "$RELAY_TRANSFER_ROOT/${TRIAL_RELEASE}-workspace.tar.gz" \
  "$CONNECTED_SSH:$CONNECTED_TRANSFER_ROOT/"
rsync -av --partial --progress \
  "$RELAY_TRANSFER_ROOT/${TRIAL_RELEASE}-workspace.tar.gz.sha256" \
  "$CONNECTED_SSH:$CONNECTED_TRANSFER_ROOT/"
```

After either route, return to the connected system. Restore the variables from
the first block in this subsection if this is a new shell, then verify and
unpack the transferred workspace:

```bash
test -f "$CONNECTED_WORKSPACE_ARCHIVE"
test -f "$CONNECTED_WORKSPACE_DIGEST"

(
  cd "$CONNECTED_TRANSFER_ROOT"
  sha256sum -c "$(basename "$CONNECTED_WORKSPACE_DIGEST")"
)
test ! -e "$FRAN_WORKSPACE"
tar -C "$CONNECTED_TRANSFER_ROOT" -xzf "$CONNECTED_WORKSPACE_ARCHIVE"
test -f "$FRAN_WORKSPACE/workspace-manifest.yaml"
test -x "$FRAN_WORKSPACE/cse-build"

FRAN_LOCK_COUNT="$(
  find "$FRAN_WORKSPACE/environments" \
    -mindepth 3 -maxdepth 3 -type f -name spack.lock -print |
    tee /dev/stderr |
    wc -l |
    tr -d '[:space:]'
)"
test "$FRAN_LOCK_COUNT" -eq 8
```

#### C. Create the cumulative source bundle on the connected system

Activate the same pinned Spack version, tag, commit, and package-recipe state
used for the trial. A matching CPU is not required because this operation reads
the locks and fetches source artifacts; it does not concretize or build them.

```bash
export FRAN_SOURCE_BUNDLE="$CONNECTED_TRANSFER_ROOT/${TRIAL_RELEASE}-source-mirror"
export CONNECTED_FETCH_STAGE="$CONNECTED_TRANSFER_ROOT/fetch-stage"
export CONNECTED_FETCH_CACHE="$CONNECTED_TRANSFER_ROOT/download-cache"
export SPACK_USER_CACHE_PATH="$CONNECTED_TRANSFER_ROOT/spack-user-cache"
export SPACK_DISABLE_LOCAL_CONFIG=true
export SPACK_VERSION="1.2.2"
export SPACK_TAG="v$SPACK_VERSION"
export SPACK_COMMIT="3e19345b6e12f5ff1b874f4059622fc6a1fd804a"
export SPACK_ROOT="<absolute-path-to-matching-pinned-spack-checkout>"

source "$SPACK_ROOT/share/spack/setup-env.sh"
SPACK_VERSION_OUTPUT="$(spack --version)"
test "${SPACK_VERSION_OUTPUT%% *}" = "$SPACK_VERSION"
test "$(git -C "$SPACK_ROOT" rev-parse HEAD)" = "$SPACK_COMMIT"
test "$(git -C "$SPACK_ROOT" rev-parse "${SPACK_TAG}^{commit}")" = \
  "$SPACK_COMMIT"
test -z "$(git -C "$SPACK_ROOT" status --porcelain --untracked-files=all)"

mkdir -p \
  "$FRAN_SOURCE_BUNDLE" \
  "$CONNECTED_FETCH_STAGE" \
  "$CONNECTED_FETCH_CACHE" \
  "$SPACK_USER_CACHE_PATH"

FRAN_ENVIRONMENT_COUNT=0
for environment_dir in "$FRAN_WORKSPACE"/environments/*/*; do
  test -f "$environment_dir/spack.lock" || {
    echo "missing lockfile: $environment_dir/spack.lock" >&2
    exit 1
  }
  spack \
    -c "config:build_stage:[$CONNECTED_FETCH_STAGE]" \
    -c "config:source_cache:$CONNECTED_FETCH_CACHE" \
    -e "$environment_dir" \
    mirror create -a -d "$FRAN_SOURCE_BUNDLE" || exit 1
  FRAN_ENVIRONMENT_COUNT=$((FRAN_ENVIRONMENT_COUNT + 1))
done
test "$FRAN_ENVIRONMENT_COUNT" -eq 8
```

The command may be rerun against the same bundle; Spack retains existing
archives and adds missing ones. Review any skipped or failed fetch, especially
license-restricted sources. Do not use `--private` unless storage and transfer
of those sources has been explicitly approved.

Package the completed source bundle and record its digest:

```bash
export FRAN_BUNDLE_ARCHIVE="$CONNECTED_TRANSFER_ROOT/${TRIAL_RELEASE}-source-mirror.tar"
export FRAN_BUNDLE_DIGEST="$FRAN_BUNDLE_ARCHIVE.sha256"

tar -C "$CONNECTED_TRANSFER_ROOT" -cf "$FRAN_BUNDLE_ARCHIVE" \
  "$(basename "$FRAN_SOURCE_BUNDLE")"
(
  cd "$CONNECTED_TRANSFER_ROOT"
  sha256sum "$(basename "$FRAN_BUNDLE_ARCHIVE")" \
    > "$(basename "$FRAN_BUNDLE_DIGEST")"
  sha256sum -c "$(basename "$FRAN_BUNDLE_DIGEST")"
)

printf 'FRAN_BUNDLE_ARCHIVE=%s\n' "$FRAN_BUNDLE_ARCHIVE"
printf 'FRAN_BUNDLE_DIGEST=%s\n' "$FRAN_BUNDLE_DIGEST"
```

Source archives are normally already compressed, so the returned bundle uses
an uncompressed tar container. Use one return route, not both.

For a direct connection, stay on the connected system, restore the Fran
endpoint and exact Fran transfer root if necessary, and push both files:

```bash
export FRAN_SSH="<fran-user>@<fran-login-host>"
export FRAN_TRANSFER_ROOT="<exact-FRAN_TRANSFER_ROOT-printed-on-fran>"

rsync -av --partial --progress \
  "$FRAN_BUNDLE_ARCHIVE" \
  "$FRAN_SSH:$FRAN_TRANSFER_ROOT/"
rsync -av --partial --progress \
  "$FRAN_BUNDLE_DIGEST" \
  "$FRAN_SSH:$FRAN_TRANSFER_ROOT/"
```

When a relay is required, run the following on the approved relay workstation.
It pulls the finished bundle from the connected system, verifies it, and then
pushes the same two files to Fran:

```bash
export TRIAL_RELEASE="fran-trial-001"
export CONNECTED_SSH="<connected-user>@<connected-login-host>"
export FRAN_SSH="<fran-user>@<fran-login-host>"
export CONNECTED_TRANSFER_ROOT="<exact-CONNECTED_TRANSFER_ROOT-printed-on-connected-system>"
export FRAN_TRANSFER_ROOT="<exact-FRAN_TRANSFER_ROOT-printed-on-fran>"
export RELAY_TRANSFER_ROOT="$HOME/cse-fran-relay/$TRIAL_RELEASE"

umask 0077
install -d -m 0700 "$RELAY_TRANSFER_ROOT"
rsync -av --partial --progress \
  "$CONNECTED_SSH:$CONNECTED_TRANSFER_ROOT/${TRIAL_RELEASE}-source-mirror.tar" \
  "$RELAY_TRANSFER_ROOT/"
rsync -av --partial --progress \
  "$CONNECTED_SSH:$CONNECTED_TRANSFER_ROOT/${TRIAL_RELEASE}-source-mirror.tar.sha256" \
  "$RELAY_TRANSFER_ROOT/"

(
  cd "$RELAY_TRANSFER_ROOT"
  sha256sum -c "${TRIAL_RELEASE}-source-mirror.tar.sha256"
)

rsync -av --partial --progress \
  "$RELAY_TRANSFER_ROOT/${TRIAL_RELEASE}-source-mirror.tar" \
  "$FRAN_SSH:$FRAN_TRANSFER_ROOT/"
rsync -av --partial --progress \
  "$RELAY_TRANSFER_ROOT/${TRIAL_RELEASE}-source-mirror.tar.sha256" \
  "$FRAN_SSH:$FRAN_TRANSFER_ROOT/"
```

If `rsync` is unavailable on one approved transfer leg, use `scp -p` for that
same source file and destination directory, then run the same SHA-256 check at
the receiving endpoint. Do not return the copied workspace archive as a
replacement for Fran's original workspace.

#### D. Install the source bundle into Fran's generated source cache

Back on Fran, source the saved operator session again and verify the returned
bundle before extracting it:

```bash
source "$HOME/STACK_TESTING/operator-sessions/fran/fran-trial-001/activate.sh"

export FRAN_TRANSFER_ROOT="$WORKDIR/$USER/cse-fran-transfer/$TRIAL_RELEASE"
export FRAN_BUNDLE_ARCHIVE="$FRAN_TRANSFER_ROOT/${TRIAL_RELEASE}-source-mirror.tar"
export FRAN_BUNDLE_DIGEST="$FRAN_BUNDLE_ARCHIVE.sha256"
export FRAN_SOURCE_BUNDLE="$FRAN_TRANSFER_ROOT/${TRIAL_RELEASE}-source-mirror"

(
  cd "$FRAN_TRANSFER_ROOT"
  sha256sum -c "$(basename "$FRAN_BUNDLE_DIGEST")"
)
test ! -e "$FRAN_SOURCE_BUNDLE"
tar -C "$FRAN_TRANSFER_ROOT" -xf "$FRAN_BUNDLE_ARCHIVE"
test -d "$FRAN_SOURCE_BUNDLE"
```

Read the source-cache destination through an actual generated environment and
confirm that it is the restricted cache selected for this operator session.
Do not type or infer the destination path independently:

```bash
verify_spack_tool_root
source "$SPACK_ROOT/share/spack/setup-env.sh"
source "$BUILD_WORKSPACE/env/select-build-context.sh"
cse_select_build_context login
source "$BUILD_WORKSPACE/env/setup-build-env.sh"

export FRAN_REFERENCE_ENV="$BUILD_WORKSPACE/environments/$SHARED_COMPILER_NAME/core"
export FRAN_SOURCE_CACHE="$(
  spack -e "$FRAN_REFERENCE_ENV" python -c \
    'import spack.config; print(spack.config.get("config:source_cache"))'
)"

test -n "$FRAN_SOURCE_CACHE"
test "$FRAN_SOURCE_CACHE" = "$CSE_RESTRICTED_ROOT/cache/source"
printf 'FRAN_SOURCE_CACHE=%s\n' "$FRAN_SOURCE_CACHE"
```

Merge only the source mirror's contents into that generated cache while
preserving the CSE group/setgid policy. Spack's mirror and `source_cache` use
the same cache-relative archive layout, so the trailing slashes below are
intentional:

```bash
umask 0007
install -d -m 2770 -g "$CSE_GROUP" "$FRAN_SOURCE_CACHE"
rsync -a --no-owner --no-group --checksum \
  "$FRAN_SOURCE_BUNDLE/" "$FRAN_SOURCE_CACHE/"

chgrp -R "$CSE_GROUP" "$FRAN_SOURCE_CACHE"
find "$FRAN_SOURCE_CACHE" -type d -exec chmod g+rws,o-rwx {} +
find "$FRAN_SOURCE_CACHE" -type f -exec chmod g+rw,o-rwx {} +
```

Finally, use the original Fran workspace and its existing lockfiles to prove
that every environment can fetch its complete dependency closure from the
populated cache. This command may attempt an outbound URL only when an artifact
is still missing; on Fran that attempt fails and identifies the gap to add to
the bundle.

```bash
cd "$BUILD_WORKSPACE"
./cse-build login verify
./cse-build login fetch
```

Gate: `./cse-build login fetch` succeeds for all eight original Fran
environments.
Retain both transfer archives and their digest files until the first complete
Fran build succeeds; they are recovery evidence for the same locked release.
The source bundle is not the signed CSE binary build cache and does not change
any `spack.lock`. If the Spack runtime itself must be bootstrapped without
network access, prepare a separate Spack bootstrap mirror; do not mix bootstrap
artifacts into this source bundle.

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
