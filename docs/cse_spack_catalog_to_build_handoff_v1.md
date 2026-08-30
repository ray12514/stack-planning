# Bare Spack Guide for the CSE Build Workspace

| Document control | |
|---|---|
| Date | 2026-08-20 |
| Status | Working teammate handoff guide |
| Spack version | 1.2.2 |

## Purpose

This guide starts after the workspace already exists. It explains how to
navigate that workspace and use normal Spack commands to inspect configuration,
select one environment, concretize it when needed, fetch sources, install its
locked software, and look at the resulting build state.

You do not need to know how the workspace was produced. Everything Spack needs
is already present in the workspace: native `spack.yaml` files, configuration
scopes, platform externals, package-repository settings, install/cache paths,
views, and module configuration.

The normal command pattern throughout this guide is:

```bash
spack -e "$ENV_DIR" <command>
```

Using `-e` makes the target environment explicit on every command. This is
safer for a shared workspace than relying on whichever environment happens to
be activated in the current shell. Spack documents `-e` as the non-activating
way to run any environment-aware command against a named or directory
environment in its [environment guide](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L288-L300).

## Per-system handoff sheet: fill this in first

The receiving builder should not have to discover site paths. Before handing
over a workspace, fill in the **Actual value** column with absolute paths for
that system. Values marked **workspace-recorded** are already present in the
workspace, but writing them here makes the handoff auditable and gives the
builder a quick reference.

| Item | Shell/config name | Actual value | Source |
|---|---|---|---|
| Restricted build workspace | `WORKSPACE` | `<absolute path>` | handoff owner supplies |
| Builder's writable work root | `WORKDIR` | `<absolute path>` | site supplies; may differ by builder |
| Shared, read-only Spack checkout | `CSE_SPACK_SHARED_ROOT`, then `SPACK_ROOT` | `<absolute path>` | workspace-recorded; owner confirms it exists |
| Login-node stage candidates | `CSE_LOGIN_STAGE_CANDIDATES` | `<absolute path(s)>` | workspace-recorded; owner confirms one is executable |
| Compute-node stage candidates | `CSE_COMPUTE_STAGE_CANDIDATES` | `<absolute path(s)>` | workspace-recorded; owner confirms one is executable |
| Default starting environment | `DEFAULT_ENVIRONMENT` | `<for example, gcc/serial>` | handoff owner chooses |
| Default parallel build jobs | `BUILD_JOBS` | `<integer>` | workspace-recorded; owner may approve an override |
| System and release | `CSE_SYSTEM_NAME`, `CSE_TRIAL_RELEASE` | `<names>` | workspace-recorded |
| Required Unix group | `CSE_GROUP` | `<group>` | workspace-recorded |
| Approved Spack identity | `CSE_SPACK_VERSION`, `CSE_SPACK_TAG`, `CSE_SPACK_COMMIT` | `<version, tag, commit>` | workspace-recorded |
| Restricted install tree | `config:install_tree:root` | `<absolute path>` | encoded in workspace config; verify only |
| Shared source cache | `config:source_cache` | `<absolute path>` | encoded in workspace config; verify only |
| Shared misc-cache root and builder partition | `CSE_SHARED_MISC_CACHE_ROOT`, `config:misc_cache`, `SPACK_MISC_CACHE_PATH` | `<restricted-root>/cache/misc/<builder>` | workspace-recorded root plus generated prepared shell; recursively CSE-group-accessible |
| Private build-cache mirror | `mirrors` | `<absolute path or URL>` | encoded in workspace config; verify only |
| View and module roots | `view`, `modules` | `<absolute paths>` | encoded per environment; verify only |

There are three categories of shell variables in this guide:

| Category | Variables | What to do |
|---|---|---|
| Owner/site inputs | `WORKSPACE`, `WORKDIR`, `DEFAULT_ENVIRONMENT` | Fill these in with values for the target system. They are the normal handoff inputs. |
| Workspace-recorded values | `CSE_GROUP`, `CSE_SHARED_MISC_CACHE_ROOT`, `CSE_CPU_TARGET`, `CSE_SYSTEM_NAME`, `CSE_TRIAL_RELEASE`, `CSE_SPACK_*`, compiler/MPI names, default `BUILD_JOBS`, and stage candidates | Read them by sourcing the scripts under `env/`; do not retype them for each builder. |
| Session selections or derived values | `CSE_NODE_CONTEXT`, `CSE_BUILD_NODE_TYPE`, `CSE_BUILD_STAGE`, `ENVIRONMENT`, `ENV_DIR`, `ENV_KEY`, `SPACK_ROOT`, `SPACK_USER_STATE_ROOT`, `SPACK_BOOTSTRAP_ROOT`, `SPACK_USER_CACHE_PATH`, `SPACK_MISC_CACHE_PATH`, `SPACK_GNUPGHOME`, `SPACK_DISABLE_LOCAL_CONFIG`, and `PYTHONDONTWRITEBYTECODE` | Select or derive these when preparing the shell. |

### Start the recorded shared Spack instance

The workspace contains shell data under `env/` that records its system,
release, compiler/provider names, exact Spack identity, shared Spack root, job
default, and approved stage candidates. These files set shell variables; they
do not concretize or install anything.

This is the complete login-shell startup sequence. Replace only the first
three placeholders with the values from the handoff sheet:

```bash
umask 0007

export WORKSPACE="<absolute-restricted-workspace-path>"
export WORKDIR="<absolute-writable-work-directory>"
export DEFAULT_ENVIRONMENT="<for-example-gcc/serial>"

test -f "$WORKSPACE/workspace-manifest.yaml"
test -d "$WORKDIR" && test -w "$WORKDIR" && test -x "$WORKDIR"
test -f "$WORKSPACE/env/select-build-context.sh"
test -f "$WORKSPACE/env/setup-build-env.sh"
test -f "$WORKSPACE/env/prepare-module-state.sh"
test -f "$WORKSPACE/env/share-generated-permissions.sh"

# Select login-node stage and node type from the recorded candidates.
export CSE_NODE_CONTEXT="login"
source "$WORKSPACE/env/select-build-context.sh"
cse_select_build_context "$CSE_NODE_CONTEXT"

# Load the system/release identity and recorded shared-Spack values.
source "$WORKSPACE/env/setup-build-env.sh"
export SPACK_ROOT="$CSE_SPACK_SHARED_ROOT"

# Select one of the populated environments.
export ENVIRONMENT="$DEFAULT_ENVIRONMENT"
export ENV_DIR="$WORKSPACE/environments/$ENVIRONMENT"
ENV_KEY="${ENVIRONMENT//\//-}"
export ENV_KEY

# Keep mutable per-builder state outside the read-only shared checkout.
export SPACK_DISABLE_LOCAL_CONFIG=true
export PYTHONDONTWRITEBYTECODE=1
export SPACK_USER_STATE_ROOT="$WORKDIR/$USER/cse-spack/$CSE_SYSTEM_NAME/$CSE_SPACK_VERSION"
export SPACK_BOOTSTRAP_ROOT="$SPACK_USER_STATE_ROOT/bootstrap"
export SPACK_USER_CACHE_PATH="$SPACK_USER_STATE_ROOT/cache/$CSE_NODE_CONTEXT/$ENV_KEY"
export SPACK_MISC_CACHE_PATH="$CSE_SHARED_MISC_CACHE_ROOT/$USER"
export SPACK_GNUPGHOME="$SPACK_USER_STATE_ROOT/gnupg"

test -f "$SPACK_ROOT/share/spack/setup-env.sh"
test -f "$ENV_DIR/spack.yaml"
install -d -m 0700 \
  "$SPACK_BOOTSTRAP_ROOT" \
  "$SPACK_USER_CACHE_PATH" \
  "$SPACK_GNUPGHOME" \
  "$CSE_BUILD_STAGE"

export CSE_BUILD_WORKSPACE="$WORKSPACE"
source "$WORKSPACE/env/share-generated-permissions.sh"
cse_normalize_shared_generated_content "$CSE_GROUP"
cse_manual_shared_content_on_exit() {
  status=$?
  trap - EXIT
  if ! cse_normalize_shared_generated_content "$CSE_GROUP"; then
    [ "$status" -ne 0 ] || status=2
  fi
  exit "$status"
}
trap cse_manual_shared_content_on_exit EXIT

# Clear only a selected external compiler/MPI module that is already loaded.
source "$WORKSPACE/env/prepare-module-state.sh"
cse_prepare_module_state

source "$SPACK_ROOT/share/spack/setup-env.sh"
test "${CSE_SPACK_VERSION}" = "$(spack --version | awk '{print $1}')"
test "$(git -C "$SPACK_ROOT" rev-parse HEAD)" = "$CSE_SPACK_COMMIT"
test "$(git -C "$SPACK_ROOT" rev-parse "${CSE_SPACK_TAG}^{commit}")" = "$CSE_SPACK_COMMIT"

printf 'system:       %s\n' "$CSE_SYSTEM_NAME"
printf 'release:      %s\n' "$CSE_TRIAL_RELEASE"
printf 'workspace:    %s\n' "$WORKSPACE"
printf 'Spack root:   %s\n' "$SPACK_ROOT"
printf 'environment:  %s\n' "$ENVIRONMENT"
printf 'build stage:  %s\n' "$CSE_BUILD_STAGE"
printf 'build jobs:   %s\n' "$BUILD_JOBS"
spack -e "$ENV_DIR" env status
```

That `source "$SPACK_ROOT/share/spack/setup-env.sh"` line starts the shared
Spack command in the current shell. The checkout itself stays read-only;
bootstrap software, user cache data, keys, and build stages go to the mutable
paths shown above.

For a compute shell, run the same sequence with
`CSE_NODE_CONTEXT="compute"`. The context selector chooses and tests a compute
stage, while the same workspace, lockfile, shared Spack checkout, bootstrap
root, and install tree remain in use.

## 1. Shared filesystem layout

The site supplies the actual value of `<cse-shared-root>`. The working layout
under it is:

```text
<cse-shared-root>/
  restricted/
    catalogs/<system>/static/<catalog-release>/
    workspaces/<system>/initial-conversion-trials/<trial-release>/
    releases/<system>/<trial-release>/
      spack/opt/                    Spack install tree and database
      views/                        generated environment views
      modules/                      generated package modules
    cache/
      source/                       downloaded source archives
    buildcache/<system>/<trial-release>/
    evidence/<system>/<trial-release>/

  published/
    catalogs/<system>/static/<catalog-release>/
    catalogs/<system>/static/current
    workspaces/<system>/initial-conversion-trials/<trial-release>/
    releases/<system>/<trial-release>/
      spack/opt/
      views/
      modules/
      evidence/
```

Mutable provider and concretization indexes are deliberately absent from the
shared tree. The prepared shell places them below each builder's
`$SPACK_USER_STATE_ROOT/misc` so Spack's user-only cache files cannot block a
coworker.

The restricted side is where source builds occur. The published side is the
user-facing release area and is not the place to experiment, concretize, or
build from source. This guide operates only on the restricted workspace and
restricted install tree.

The versioned published catalog is readable by all authenticated system users
and is not writable by consumers. Package-manager environments pin that
versioned path. The optional `current` pointer is for discovery only.

`stack-composer publish-static` creates the published copy from the reviewed
restricted catalog. It does not run `render-static` again. The CSE restricted
build workspace and the later cache-only publication workspace both use the
retained restricted catalog. The public copy is for package managers outside
CSE and is not an input to this build handoff.

Build stages are separate from both trees. They normally live in node-local or
site work storage because stages are temporary and can be much larger and more
write-intensive than the workspace itself.

## 2. The handed-off workspace

The path you receive should be the complete workspace, not one copied
`spack.yaml`:

```text
<workspace>/
  README.md
  BUILDER-HANDOFF.md
  workspace-manifest.yaml

  catalog/
    README.md
    manifest.yaml
    profile.yaml
    scopes/
      common/
        packages.yaml
      compilers/<provider>/<version>/
        packages.yaml
      mpi/<provider>/<version>/<compiler-axis>/
        packages.yaml
        toolchains.yaml
      gpu/<toolkit>/<version>/
        packages.yaml
    reports/static-plan.yaml

  configs/
    common/
      bootstrap.yaml
      concretizer.yaml
      config.yaml
      mirrors.yaml
      packages.yaml
      repos.yaml
    surfaces/
      shared/
        compiler.yaml
        packages.yaml
      platform/
        compiler.yaml
        packages.yaml
    environments/<compiler>/<environment>/
      modules.yaml

  environments/
    <shared-compiler>/
      core/spack.yaml
      common/spack.yaml
      serial/spack.yaml
      mpi-<shared-mpi>/spack.yaml
    <platform-compiler>/
      core/spack.yaml
      common/spack.yaml
      serial/spack.yaml
      mpi-<platform-mpi>/spack.yaml

  package-repos/
    spack_repo/...
  env/
    setup-build-env.sh             recorded system/release/build values
    select-build-context.sh        login/compute stage candidates and selector
    prepare-module-state.sh        selected external-module cleanup helper
    workspace-shell.rc             optional prepared-shell prompt/state
  modulefiles/
  scripts/
  inputs/

  cse-build                         optional convenience command
```

After concretization, each environment directory also contains `spack.lock`.
Spack calls `spack.yaml` the manifest - the requested roots and configuration - and
`spack.lock` the fully concrete dependency graph. The lock is created by
concretization and is what preserves exact versions, variants, providers,
targets, and hashes. See Spack's
[manifest-and-lock description](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L39-L47).

### The eight current environments

There are two compiler surfaces. Each surface has four independently
concretized environments:

| Environment | Contains |
|---|---|
| `core` | compiler producer where applicable, Foundation libraries, build tools, Python, and other Core roots |
| `common` | compiler-dependent packages reused by payload environments |
| `serial` | payload packages built explicitly without MPI |
| `mpi-<provider>` | MPI provider where built, plus MPI-enabled payload packages |

The split is intentional. Core and Common producer packages can be reused by
more than one payload environment, while Serial and MPI remain separate solves
so MPI requirements cannot leak into Serial. Each lock stays small enough to
inspect independently, and the shared content-addressed install tree still
deduplicates any exact hashes selected by more than one environment.

The concrete names are intentionally read from the workspace rather than
assumed. List them with:

```bash
find "$WORKSPACE/environments" -type f -name spack.yaml -print | sort
```

An environment is the unit you concretize, inspect, build, resume, and hand to
another builder. The eight environments may reuse identical package hashes in
the same shared install tree, but each has its own `spack.yaml` and
`spack.lock`.

## 3. How an environment consumes the workspace

A generated environment is ordinary Spack YAML. A representative MPI manifest
has this shape:

```yaml
spack:
  include::
    - ../../../configs/surfaces/shared/compiler.yaml
    - ../../../configs/surfaces/shared/toolchains.yaml
    - ../../../catalog/scopes/common
    - ../../../catalog/scopes/compilers/gcc/<seed-version>
    - ../../../configs/common
    - ../../../configs/surfaces/shared/packages.yaml
    - ../../../configs/environments/gcc/mpi-openmpi

  definitions:
    - foundation:
        - zlib@<version>
        - xz@<version>
    - payload:
        - hdf5@<version>+mpi+fortran
        - netcdf-c@<version>+mpi

  specs:
    - group: compiler
      specs:
        - gcc@<version>
    - group: foundation
      needs: [compiler]
      specs:
        - matrix:
            - [$foundation]
            - ['target=<portable-target> %cse_shared']
    - group: payload
      needs: [compiler, foundation]
      specs:
        - matrix:
            - [$payload]
            - ['%cse_shared']

  view:
    cse_modules:
      root: <restricted-view-root>
      group: payload
      projections:
        all: '{name}/{version}'
```

The exact roots and constraints in the handed-off file are authoritative. The
example above is only a map of the sections.

### What each included scope contributes

| Scope or file | What Spack gets from it |
|---|---|
| `catalog/scopes/common` | reviewed system externals such as OpenSSL, curl, fabric, or scheduler components |
| `catalog/scopes/compilers/...` | external compiler prefix, executable paths, and any module chain |
| `catalog/scopes/mpi/...` | external MPI prefix/modules and, where applicable, named compiler–MPI toolchains |
| `configs/common/config.yaml` | install tree, build stage, caches, job default, locking, and other build settings |
| `configs/common/concretizer.yaml` | `unify` and reuse behavior |
| `configs/common/packages.yaml` | package pins, target preference, permissions, and global requirements |
| `configs/common/repos.yaml` | package repositories and recipe versions |
| `configs/common/mirrors.yaml` | private build-cache location |
| `configs/common/bootstrap.yaml` | where Spack stores bootstrap software such as the concretizer |
| `configs/surfaces/.../compiler.yaml` | preferred C, C++, and Fortran language provider for the surface |
| `configs/surfaces/.../toolchains.yaml` | conditional compiler/MPI binding applied to each root on the surface |
| `configs/surfaces/.../packages.yaml` | surface-specific provider requirements, especially MPI |
| `configs/environments/.../modules.yaml` | module-generation rules for this one environment |
| inline `definitions`, `specs`, and `view` | this environment's roots, group ordering, and exposure paths |

An included directory is a Spack configuration scope. Spack reads the
recognized configuration YAML files inside it; the files are not pasted into
`spack.yaml` as text.

`include::` has two colons deliberately. It replaces the normal built-in
include set, leaving Spack's required defaults plus the scopes named by the
environment. In a clean pinned checkout, a structural `spack` scope may still
be listed, but its `site` include is overridden and user/system policy is
disabled. This keeps an unrelated `~/.spack/packages.yaml` or site preference
from changing the solve. Always confirm the actual result with `config scopes
-vp`. Spack documents the underlying isolation behavior in
[Overriding built-in scopes with `include::`](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/include_yaml.rst#L278-L311).

Within the include list, an earlier entry has higher precedence than a later
entry. Values written directly in `spack.yaml` have higher precedence than its
included scopes. Spack explains both rules in its
[include precedence documentation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/include_yaml.rst#L122-L143)
and [configuration precedence documentation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst#L279-L293).

Relative include paths are resolved relative to the file containing them. That
is why the entire workspace tree must remain together.

### Groups and `needs`

`group` names a set of roots. `needs` says that another group must be
concretized first and its concrete specs must be available for reuse while the
dependent group is solved. This is how one environment can build a compiler
and then bind later roots to that compiler. `needs` operates only inside that
one `spack.yaml`; it does not schedule another environment or another process.
See Spack's [spec-group documentation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L925-L963).

## 4. Prepare or reconstruct a bare-Spack shell

Use Bash for the examples below. If you ran **Start the recorded shared Spack
instance**, the shell is already prepared. These checks make the required
state explicit and are useful after reconnecting or when diagnosing a handoff:

```bash
: "${WORKSPACE:?set the absolute restricted workspace path}"
: "${WORKDIR:?set the absolute writable builder work root}"
: "${CSE_NODE_CONTEXT:?select login or compute}"
: "${CSE_BUILD_NODE_TYPE:?source the workspace context selector}"
: "${CSE_BUILD_STAGE:?source the workspace context selector}"
: "${CSE_SYSTEM_NAME:?source env/setup-build-env.sh}"
: "${CSE_TRIAL_RELEASE:?source env/setup-build-env.sh}"
: "${CSE_SPACK_SHARED_ROOT:?source env/setup-build-env.sh}"
: "${SPACK_ROOT:?select the recorded shared Spack root}"
: "${ENVIRONMENT:?select one workspace environment}"
: "${ENV_DIR:?derive it from WORKSPACE and ENVIRONMENT}"
: "${BUILD_JOBS:?use the recorded default or an approved override}"

test -f "$WORKSPACE/workspace-manifest.yaml"
test -f "$SPACK_ROOT/share/spack/setup-env.sh"
test -f "$ENV_DIR/spack.yaml"
test "$SPACK_ROOT" = "$CSE_SPACK_SHARED_ROOT"
test "$CSE_SPACK_VERSION" = "$(spack --version | awk '{print $1}')"
test "$(git -C "$SPACK_ROOT" rev-parse HEAD)" = "$CSE_SPACK_COMMIT"
```

The shared checkout is a tool installation, not the package install tree. Do
not modify it, pull a new revision into it, or place bootstrap/cache data under
it. `SPACK_ROOT` identifies the tool; `config:install_tree:root` in the merged
environment configuration identifies where built packages are installed.

To select a different populated environment in the same prepared shell:

```bash
export ENVIRONMENT="gcc/serial"
export ENV_DIR="$WORKSPACE/environments/$ENVIRONMENT"
ENV_KEY="${ENVIRONMENT//\//-}"
export ENV_KEY
export SPACK_USER_CACHE_PATH="$SPACK_USER_STATE_ROOT/cache/$CSE_NODE_CONTEXT/$ENV_KEY"

test -f "$ENV_DIR/spack.yaml"
install -d -m 0700 "$SPACK_USER_CACHE_PATH"
printf 'workspace:   %s\n' "$WORKSPACE"
printf 'environment: %s\n' "$ENVIRONMENT"
printf 'manifest:    %s\n' "$ENV_DIR/spack.yaml"
```

The stage selector writes and executes a small probe in each candidate before
choosing it. That matters because a path can be writable but mounted `noexec`.
If no candidate passes, the site owner must supply another approved absolute
stage path; do not silently use an unreviewed filesystem.

`SPACK_DISABLE_LOCAL_CONFIG` disables Spack's user and system configuration.
`SPACK_USER_CACHE_PATH` moves per-process cache data. The generated
`config:misc_cache` references `SPACK_MISC_CACHE_PATH`, which selects one
builder-named partition below the shared restricted cache root. The generated
permission helper recursively makes existing and newly written entries
CSE-group-accessible; different builders retain separate mutable index
partitions. These are standard Spack path and config variables documented under
[local configuration overrides](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst#L669-L705).

`SPACK_BOOTSTRAP_ROOT` and `CSE_BUILD_STAGE` matter because this workspace's
`bootstrap.yaml` and `config.yaml` reference them. Spack expands ordinary
environment variables written as `$NAME` or `${NAME}` in configuration paths;
see [Spack config-file variables](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst#L503-L555).

Before proceeding, find every unresolved shell placeholder used by the selected
environment and its common configuration:

```bash
grep -R '\${[A-Za-z_][A-Za-z0-9_]*}' \
  "$ENV_DIR/spack.yaml" "$WORKSPACE/configs" || true
```

Every variable reported there must either be set in the shell or be one of
Spack's own variables such as `$spack`, `$user`, or `$tempdir`.

Do not manually preload the selected compiler or MPI provider before invoking
Spack. Their external records carry the module chains Spack should load when a
build needs them. The recorded `prepare-module-state.sh` helper in the startup
sequence unloads only an exact selected compiler/MPI module that is already
active; unrelated site modules remain in place.

## 5. Confirm the selected environment

These commands do not concretize or build anything:

```bash
spack -e "$ENV_DIR" env status
spack -e "$ENV_DIR" location -e
sed -n '1,260p' "$ENV_DIR/spack.yaml"
```

The first two commands confirm that Spack resolved the same environment path
you intended. Continue to use `spack -e "$ENV_DIR"` even if you also choose to
activate the environment interactively.

If you prefer activation for an interactive shell, activate without loading a
view that may not exist yet:

```bash
spack env activate --without-view -p "$ENV_DIR"
spack env status

# When finished:
spack env deactivate
```

Activation changes the current shell. `spack -e` does not. Spack describes the
difference and view behavior in
[Activating an Environment](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L138-L184).

## 6. Inspect configuration scopes before concretizing

First look at Spack without an environment, then with the selected environment:

```bash
spack config scopes -vp
spack -e "$ENV_DIR" config scopes -vp
```

The environment view should show:

- an active command-line scope;
- the active `env:<path>` scope for `spack.yaml`;
- the workspace scopes from its `include::` list;
- Spack's defaults and `_builtin`; and
- the structural `spack` scope may remain active, while `site` is overridden
  and `system`/`user` are absent or overridden rather than active sources of
  policy.

Stop if an unexpected active scope can affect the solve. `spack config scopes`
lists scopes from highest to lowest precedence; Spack documents the command and
the precedence order in its
[configuration guide](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst#L59-L107).

Now inspect the fully merged configuration Spack will use:

```bash
spack -e "$ENV_DIR" config get config
spack -e "$ENV_DIR" config get bootstrap
spack -e "$ENV_DIR" config get concretizer
spack -e "$ENV_DIR" config get packages
spack -e "$ENV_DIR" config get repos
spack -e "$ENV_DIR" config get mirrors
spack -e "$ENV_DIR" config get modules
spack -e "$ENV_DIR" config get toolchains
```

At minimum, confirm:

- `config:install_tree:root` is the intended restricted package store;
- `config:build_stage` references `${CSE_BUILD_STAGE}`, and the shell variable
  itself names the intended executable stage (`config get` may display the
  placeholder literally because expansion occurs when Spack uses the path);
- `bootstrap:root` references `${SPACK_BOOTSTRAP_ROOT}`, and that shell variable
  points outside the shared Spack checkout;
- the source cache points to the intended shared restricted cache root;
- `config:misc_cache` references `${SPACK_MISC_CACHE_PATH}`, whose resolved
  directory is the current builder's CSE-group-accessible partition outside the
  generated workspace;
- `config:locks` is `true`;
- the portable target and package pins are present;
- the selected compiler and MPI requirements match this environment;
- expected system components are marked external; and
- the expected package repositories and recipe versions are present.

When a merged value is surprising, ask Spack which file supplied it:

```bash
spack -e "$ENV_DIR" config blame config
spack -e "$ENV_DIR" config blame packages
spack -e "$ENV_DIR" config blame toolchains
spack -e "$ENV_DIR" config blame modules
```

`config get` shows the merged result; `config blame` annotates it with its
source file. Both are documented in
[Seeing Spack's Configuration](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst#L586-L647).

## 7. Understand or create `spack.yaml` manually

The populated environments already contain complete manifests, so the normal
builder only reads them. If you need to make an independent environment by
hand, the minimum is ordinary native Spack YAML. Replace `<workspace-root>`
with the absolute root of the complete generated workspace:

```yaml
spack:
  include::
    - <workspace-root>/catalog/scopes/common
    - <workspace-root>/catalog/scopes/compilers/<compiler>/<version>
    - <workspace-root>/configs/common

  specs:
    - hdf5@<version>~mpi+fortran %<compiler>@<version>
```

For an MPI build, add the matching MPI catalog scope and use the toolchain or
compiler/MPI binding named by that scope:

```yaml
spack:
  include::
    - <workspace-root>/catalog/scopes/common
    - <workspace-root>/catalog/scopes/compilers/<compiler>/<version>
    - <workspace-root>/catalog/scopes/mpi/<provider>/<version>/<compiler-axis>
    - <workspace-root>/configs/common

  specs:
    - hdf5@<version>+mpi+fortran %<toolchain-name>
```

Use the catalog paths and values that actually exist; do not invent a compiler–
MPI pairing from module names. A Serial environment omits the MPI scope and
uses `~mpi`. A GPU environment adds the compatible GPU scope.

The usual sections are:

| Section | Required? | Meaning |
|---|---|---|
| `spack:` | yes | top-level Spack environment mapping |
| `include::` | required for this isolated workspace | catalog and configuration scopes |
| `specs` | yes | root package requests |
| `definitions` | optional | reusable lists referenced by `$name` |
| `group` and `needs` | optional | in-environment producer/consumer ordering |
| `concretizer` | optional inline | solve behavior when not supplied by an included scope |
| `view` | optional | filesystem view definitions |

An independent environment is simply a directory containing `spack.yaml`; use
its absolute directory with `spack -e`. Do not copy a populated workspace
manifest alone if it has relative includes - the referenced tree must remain
available.

## 8. Concretize

Check for an existing lock first:

```bash
if test -f "$ENV_DIR/spack.lock"; then
  printf 'existing lock: %s\n' "$ENV_DIR/spack.lock"
else
  printf 'no lock exists; this environment still needs concretization\n'
fi
```

For the first controlled solve:

```bash
spack -e "$ENV_DIR" concretize --fresh -j 1
```

This writes `$ENV_DIR/spack.lock`; it does not install packages. In Spack
1.2.2, `--fresh` disables dependency reuse for the solve, while `-j 1` limits
concretizer parallelism. `--fresh` is different from `--force`.

When a lock already exists:

- plain `spack concretize` adds only roots that are not yet concrete and leaves
  existing concrete specs unchanged;
- do not use `--force` merely to resume a build; and
- use `--force` only when you intentionally approve replacing existing lock
  entries after changing an owning input.

Spack documents preservation of already concrete specs and forced
reconcretization in
[Concretizing environments](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L301-L326).

Never edit `spack.lock` by hand. Correct `spack.yaml` or one of its included
configuration scopes, then reconcretize deliberately.

## 9. Inspect the concrete graph

Use `-c` before installation so `spack find` includes concrete specs that are
not installed yet:

```bash
# Concrete roots only.
spack -e "$ENV_DIR" find -c -r -l -v

# Complete concrete DAG, including dependencies.
spack -e "$ENV_DIR" find -c -d -l -v

# Only concrete externals in this environment.
spack -e "$ENV_DIR" find -c -d -e -l -v
```

Spack documents `find -c` specifically for viewing concrete, uninstalled
environment specs in its
[environment guide](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L323-L340).

Review the graph for:

- requested root versions and variants;
- the intended compiler surface;
- the intended MPI provider in an MPI environment;
- no MPI provider in a Serial environment;
- the intended portable CPU target on source-built packages;
- platform-owned packages appearing as externals rather than source builds;
- expected build tools and pinned dependency combinations; and
- matching hashes for producers that should be reused across environments.

To see one root's dependency graph in a more structural form:

```bash
spack -e "$ENV_DIR" graph -a <root-package>
```

With an active/selected environment, `spack graph` reads concrete specs from
the lockfile rather than performing another solve. This is stated in the
[Spack 1.2.2 graph command](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/graph.py#L17-L31).

## 10. Fetch sources

On a connected login or preparation node, fetch every locked root and its
dependencies:

```bash
spack -e "$ENV_DIR" fetch -D
```

`-D` includes dependencies. With `-e` and no spec argument, Spack obtains the
specs from the concrete environment. The exact behavior is described by the
[Spack 1.2.2 fetch command](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/fetch.py#L19-L80).

Fetching does not install packages. It populates the configured source cache
and stages so the same lock can later be installed from a compute node that
lacks outbound network access.

## 11. Install the locked environment

From the selected build node or allocation:

```bash
spack -e "$ENV_DIR" install \
  --only-concrete \
  -j "$BUILD_JOBS" \
  --fail-fast \
  --show-log-on-error
```

The important option is `--only-concrete`. Ordinary `spack install` is allowed
to concretize an environment that is not fully concrete. `--only-concrete`
disables that install-time solve and limits the command to specs already in
`spack.lock`. Spack's implementation describes the option as protection from
accidental concretization in
[the 1.2.2 install command](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/install.py#L343-L381).

`-j` controls build jobs supplied to package builds. It is not the number of
environments being built. Keep the first pass simple: one Spack process for one
environment. If multiple Spack processes share a node, their CPU and memory
budgets add together.

To build only one exact concrete root from the selected environment, identify
its hash with `find -c -r -l`, then run:

```bash
spack -e "$ENV_DIR" install \
  --only-concrete \
  -j "$BUILD_JOBS" \
  --fail-fast \
  /<root-hash>
```

The dependencies needed by that root are installed with it. Using a hash avoids
ambiguity when the environment contains more than one version or configuration
of the same package.

If installation stops, fix the operational cause and rerun the same locked
install. Spack skips exact hashes already present in the configured store.
Do not reconcretize simply because compilation or installation failed.

## 12. Look at build progress and logs

The primary live view is the terminal running `spack install`. Add `-v` when
you need more verbose Spack output:

```bash
spack -e "$ENV_DIR" install \
  --only-concrete \
  -j "$BUILD_JOBS" \
  --fail-fast \
  --show-log-on-error \
  -v
```

From another prepared shell using the same workspace and install tree, inspect
the environment's current state:

```bash
# Concrete graph with installed/build-cache status markers.
spack -e "$ENV_DIR" find -c -I -d -l -v

# Installed packages and their prefixes.
spack -e "$ENV_DIR" find -p
```

For one exact hash:

```bash
# Installed prefix, after installation succeeds.
spack -e "$ENV_DIR" location -i /<hash>

# Stage directory, while retained or after a failed build.
spack -e "$ENV_DIR" location -s /<hash>

# Combined Spack build log, after it is available.
spack -e "$ENV_DIR" logs /<hash>
```

Spack also creates environment-specific log links below:

```text
<environment>/.spack-env/logs/
```

List them with:

```bash
find "$ENV_DIR/.spack-env/logs" -maxdepth 1 -type l -print 2>/dev/null | sort
```

In Spack 1.2.2, `spack logs` cannot show the final combined log while that
package is actively building; it becomes available only after the combined log
has been written for a completed or failed build, or archived with an installed
prefix. The limitation is recorded directly in the
[1.2.2 logs command](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/logs.py#L31-L58).
For a live build, use the install terminal. After a failure, use the printed log
path, `--show-log-on-error`, `spack location -s`, and `spack logs` when
available.

These commands inspect the build and its filesystem state. They are not runtime
or acceptance tests.

## 13. Move from login to compute without reconcretizing

Use the same:

- workspace and `spack.lock`;
- pinned Spack 1.2.2 identity;
- restricted install tree;
- shared source cache and the same builder-partitioned, CSE-group-accessible
  misc/concretization cache; and
- bootstrap root.

Only the build context, stage, and per-process cache need to change. In an
already prepared shell, select the recorded compute context like this:

```bash
export CSE_NODE_CONTEXT="compute"
source "$WORKSPACE/env/select-build-context.sh"
cse_select_build_context "$CSE_NODE_CONTEXT"
source "$WORKSPACE/env/setup-build-env.sh"

ENV_KEY="${ENVIRONMENT//\//-}"
export ENV_KEY
export SPACK_USER_CACHE_PATH="$SPACK_USER_STATE_ROOT/cache/$CSE_NODE_CONTEXT/$ENV_KEY"

install -d -m 0700 "$CSE_BUILD_STAGE" "$SPACK_USER_CACHE_PATH"

source "$SPACK_ROOT/share/spack/setup-env.sh"
spack -e "$ENV_DIR" config get config
spack -e "$ENV_DIR" find -c -r -l -v
```

Confirm that the resolved install tree, caches, and lock are unchanged, then run
the locked install. Changing the temporary stage or node does not require a new
concretization.

## 14. Select another environment

To move from one environment to another, change only the selection and its
per-process cache path:

```bash
export ENVIRONMENT="gcc/mpi-openmpi"
export ENV_DIR="$WORKSPACE/environments/$ENVIRONMENT"
ENV_KEY="${ENVIRONMENT//\//-}"
export ENV_KEY
export SPACK_USER_CACHE_PATH="$SPACK_USER_STATE_ROOT/cache/$CSE_NODE_CONTEXT/$ENV_KEY"

test -f "$ENV_DIR/spack.yaml"
install -d -m 0700 "$SPACK_USER_CACHE_PATH"

spack -e "$ENV_DIR" env status
spack -e "$ENV_DIR" config scopes -vp
```

Run the same inspect → concretize if missing → inspect lock → fetch → install
sequence for that environment.

Different environments may be installed by different Spack processes into the
same shared store only when `config:locks` remains `true` and the shared
filesystem honors the required locks. Exact matching hashes are built once and
reused. Do not launch two processes for the same environment: they would also
compete to update that environment's view and module tree.

## 15. Refresh the populated view and module configuration

The workspace already contains each environment's view definition and
`modules.yaml`. After a successful install, refresh them with:

```bash
spack -e "$ENV_DIR" env view regenerate
spack -e "$ENV_DIR" module tcl refresh --delete-tree -y
```

The first command applies the `view:` block in `spack.yaml`. The second applies
the merged `modules` configuration. Inspect that configuration with:

```bash
spack -e "$ENV_DIR" config get modules
```

Detailed module publication and runtime validation are outside this guide.

## 16. Builder handoff record

Before another person resumes the same workspace, give them:

- the absolute `WORKSPACE` path;
- the selected `ENVIRONMENT` value;
- whether `spack.lock` exists;
- the last context used: login or compute;
- the last command attempted;
- the last package/hash reported;
- whether `fetch -D` completed;
- the relevant build log or stage path; and
- whether the environment install finished.

The receiving builder reconstructs the shell variables in Sections 4 and 5,
checks scopes and the existing lock, and reruns the same locked install. The
workspace, lockfile, store, and caches are the recovery point; a terminal
session is not.

## 17. Optional `cse-build` convenience command

The workspace may include `./cse-build`. It is optional; the bare commands in
this guide are sufficient. Its actions correspond approximately to:

| Convenience action | Bare-Spack work |
|---|---|
| `status` | select runtime/context, then run `spack -e ... find -lv` |
| `concretize` | create missing locks with `spack -e ... concretize --fresh -j 1` |
| `verify` | inspect scopes and run the workspace lock checker |
| `fetch` | run `spack -e ... fetch -D` |
| `install` | run locked installs, regenerate views, and refresh modules |

Use it only when you want its prepared-shell or loop behavior. It does not
replace the Spack concepts or commands described above.

## Official Spack 1.2.2 references

- [Environments: manifests, locks, activation, concretization, groups, views](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst)
- [Included configuration scopes and `include::`](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/include_yaml.rst)
- [Configuration scopes, precedence, variables, `config get`, and `config blame`](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst)
- [Concretizer configuration and reuse](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/build_settings.rst)
- [Package preferences, requirements, and externals](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packages_yaml.rst)
- [Install command implementation, including `--only-concrete`](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/install.py)
- [Fetch command implementation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/fetch.py)
- [Find command implementation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/find.py)
- [Logs command implementation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/logs.py)
