# Bare Spack Guide for the CSE Build Workspace

| Document control | |
|---|---|
| Date | 2026-09-09 |
| Status | Teammate handoff and learning guide |
| Spack version | 1.2.2 |
| Starting point | An existing, prepared CSE build workspace |

## 1. What you are taking over

The goal is to build and inspect software from the prepared workspace. Its
manifests, configuration, package overlays, compiler/MPI selections, and output
paths already exist. When its lockfiles and source acquisition are complete,
continue from that checkpoint. There is no need to recreate the workspace or
repeat source acquisition merely because a different person is building.

For the current **Fran GCC handoff**, the assignment is the shared GCC surface.
The workspace has been concretized and its required source bundle transferred
into Fran's configured source cache. CCE work remains a separate assignment.
Verify the checkpoint under your account, then build the GCC environments.
Learning a new concretization is a separate exercise described in Section 9.

Enter through the workspace's `cse-build` program. Once inside its prepared
shell, choose either its convenience actions or ordinary Spack commands.
This guide explains both routes without requiring another CSE document.
References are to official Spack documentation and source only.

### Handoff information

The person handing over the build supplies the actual values below. The
workspace path must identify the complete existing workspace on the build
system, not a transfer archive or the temporary connected-system copy.

| Item | Value to record |
|---|---|
| Workspace | `<absolute-shared-workspace-path>` |
| System and release | `<system / release>` |
| Assigned work | `<surface or exact environment directories>`; current Fran assignment: GCC / `shared` |
| Lock checkpoint | `<verification result>`; current prepared handoff expects all eight locks |
| Source checkpoint | `<completed fetch result and any known missing inputs>` |
| Build location | `<permitted login node or compute allocation>` |
| Other active work | `<builder / environment ownership; whether parallel builds are cleared>` |
| Last result | `<last command, package/hash, and relevant log path>` |

Your account needs the recorded CSE group access to the workspace and package
store, and the site's absolute, writable `WORKDIR`. `WORKDIR` is already your
per-user directory; do not add a username to it or recreate runtime paths by
hand. The entry point prepares the recorded runtime and your mutable state.
The shared package source cache does not include another builder's private
Spack bootstrap or user cache. Resolve any runtime/access prerequisite reported
on your first entry before starting installation.

## 2. Enter the prepared shell

On the login node, run:

```bash
cd "<absolute-shared-workspace-path>"
./cse-build login shell
```

This opens a prepared Bash shell without tmux. It works when launched directly
from another login shell such as tcsh. Execute `cse-build`; do not source it.
You do not need to source an operator-session file, activate Spack beforehand,
or manually load the chosen compiler/MPI module chain.

The entry point selects and verifies the recorded Spack runtime, establishes
this workspace's configuration and node context, prepares builder state and
permissions, and places you in the workspace directory. It does **not** select
one of the eight Spack environments or start an installation.

### Shell and tmux choices

| Command from the workspace directory | Result |
|---|---|
| `./cse-build login shell` | Prepared login-context Bash shell, without tmux |
| `./cse-build login` | Prepared login-context shell in a new or reattached tmux session |
| `./cse-build compute shell` | Prepared compute-context Bash shell, without tmux |
| `./cse-build compute` | Prepared compute-context shell in a new or reattached tmux session |

If tmux is unavailable, the default action opens the prepared shell directly.
If already inside tmux, it opens the prepared shell within that session.
Outside a prepared shell, supply `login` or `compute`; bare `./cse-build` cannot
infer the node context. Inside the prepared shell, actions can inherit the
context, for example `./cse-build status --surface shared`.

Choose the context for the node you are actually using. `compute` does not
request an allocation, log into another node, or move a running process. Enter
your site-provided compute allocation first, return to the same workspace path,
and then run `./cse-build compute shell` or `./cse-build compute`.
Login shells are suitable for inspection and source preparation. Install on a
login node only when the site permits that workload and job budget; otherwise
use a compute allocation. Native Spack commands use the prepared shell's
context too.

### Check the prepared session

Run the following **after** entering the shell:

```bash
printf 'Workspace: %s\n' "$CSE_BUILD_WORKSPACE"
printf 'System/release: %s / %s\n' "$CSE_SYSTEM_NAME" "$CSE_TRIAL_RELEASE"
printf 'Spack: %s\n' "$SPACK_ROOT"
printf 'Node context: %s\n' "$CSE_NODE_CONTEXT"
printf 'Stage: %s\n' "$CSE_BUILD_STAGE"
printf 'Build jobs: %s\n' "$BUILD_JOBS"
spack --version
./cse-build status --surface shared
```

Then verify the prepared inputs and all eight locks:

```bash
./cse-build verify
```

Continue only after verification succeeds. The whole-workspace check includes
CCE locks even when your build assignment is GCC. A CCE compilation failure is
not itself a reason to replace its lock; changes to recipes, configuration, or
locks must be coordinated with everyone building from this workspace.

Run the examples one block at a time and inspect each result. Do not enable
`set -e` in your interactive shell: an ordinary command failure can exit that
shell. The multi-command install example below confines error-stop behavior to
a subshell so the terminal remains open for diagnosis.

## 3. Build GCC with the convenience actions

The four GCC environments are selected by **`--surface shared`**. This is
separate from `--spack-mode shared`, which selects the shared Spack checkout.
Without `--surface`, fetch and install default to both compiler surfaces.

In the prepared login shell, this optional pass lets you inspect source-fetch
behavior and confirm that your account can use the completed source cache:

```bash
./cse-build fetch --surface shared
```

After that succeeds, use the prepared shell on your assigned build node:

```bash
./cse-build install --surface shared
```

This installs GCC environments in order: `core`, `common`, `serial`, then
`mpi-<shared-MPI-provider>`. For each environment the action fetches sources,
installs only the existing concrete specs, regenerates views, and refreshes
package modules. Exact hashes already installed in the shared store are reused.
It does not reconcretize existing environments.

The prior overlay fixes are part of the prepared workspace. Its input verifier
checks the required overlay content. Existing fixes are useful preparation;
success on another system does not establish that every build will succeed on
this system. Retain the actual build results and failures.

Use this route when you want the entire assigned compiler surface processed in
order. To learn and run each native Spack operation yourself, use Sections 4–7
instead. Assign one owner to an environment at a time; do not run both routes
against the same environment concurrently.

## 4. Locate an environment and understand its inputs

The important parts of the workspace are:

```text
<workspace>/
  cse-build
  workspace-manifest.yaml
  environments/
    <shared-compiler>/{core,common,serial,mpi-<provider>}/
      spack.yaml
      spack.lock
    <platform-compiler>/{core,common,serial,mpi-<provider>}/
      spack.yaml
      spack.lock
  configs/                 common, surface, and per-environment configuration
  catalog/scopes/          reviewed platform/compiler/MPI external configuration
  package-repos/           workspace-owned package overlays
  env/                     prepared-shell and node-context support
  scripts/                 workspace verification support
```

The install store, source cache, stages, views, and generated package modules
have their own configured locations. They are not inferred from where you
happen to run `spack`.

| File or setting | What it means |
|---|---|
| `spack.yaml` | Requested roots, variants, groups, includes, and view definitions |
| `spack.lock` | The concrete dependency graph and package identities selected for the build |
| `include::` | The environment's explicit configuration scope list |
| `configs/common/repos.yaml` and `package-repos/` | Recipe repository identity/order and local overlays |
| `config:install_tree:root` | Shared package store and Spack database |
| `config:source_cache` | Shared source archives used by this build |
| `config:build_stage` | Temporary unpacking/compilation space selected for this node context |
| `config:misc_cache` | Builder-named partition under the shared misc-cache root |
| `view` and `modules` | Locations and rules for exposing installed software |

Spack defines the manifest and lock separately in its
[environment documentation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst).
The shared misc-cache partition remains CSE-group-accessible. Bootstrap state,
command/user caches, and the GPG home are private per builder; entry through
`cse-build` establishes them without copying another person's runtime state.

List the manifests in the existing workspace:

```bash
find "$CSE_BUILD_WORKSPACE/environments" -type f -name spack.yaml -print | sort
```

For the first GCC environment, select the recorded compiler name:

```bash
export ENVIRONMENT="$SHARED_COMPILER_NAME/core"
export ENV_DIR="$CSE_BUILD_WORKSPACE/environments/$ENVIRONMENT"
export ENV_KEY="${ENVIRONMENT//\//-}"
export SPACK_USER_CACHE_PATH="$SPACK_USER_STATE_ROOT/cache/$CSE_NODE_CONTEXT/$ENV_KEY"
install -d -m 0700 "$SPACK_USER_CACHE_PATH"
```

The environment-specific user cache separates this native command session's
mutable indexes from other environment sessions. Its parent root is already
provided by `cse-build`; do not reconstruct it from `WORKDIR` or `$USER`.

Confirm the selection before fetching or installing:

```bash
spack -e "$ENV_DIR" env status
spack -e "$ENV_DIR" location -e
sed -n '1,260p' "$ENV_DIR/spack.yaml"
test -f "$ENV_DIR/spack.lock"
```

A missing lock at this prepared checkpoint is a handoff issue: stop and have
the owner resolve it. Do not remove or regenerate the accepted locks to make
an install proceed.

Use `spack -e "$ENV_DIR" ...` for native commands. The environment is selected
for that command without being activated in the shell. This also lets you
switch between native Spack and `cse-build` actions. If you choose to run
`spack env activate` independently, run `spack env deactivate` before invoking
`cse-build` again; its entry check rejects an already-active Spack environment.
See [Spack environment selection](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst).

### Read the configuration that Spack will use

```bash
spack -e "$ENV_DIR" config scopes -vp
spack -e "$ENV_DIR" config get config
spack -e "$ENV_DIR" config get packages
spack -e "$ENV_DIR" config get repos
spack -e "$ENV_DIR" config get mirrors
spack -e "$ENV_DIR" config get modules
```

Check that the selected configuration points to this build's store/cache,
compiler surface, external MPI where applicable, and recipe repositories.
`config get` can show shell-variable placeholders that Spack expands when it
uses a path; compare those with the variables printed by the prepared shell.
To identify where a value came from:

```bash
spack -e "$ENV_DIR" config blame config
spack -e "$ENV_DIR" config blame packages
```

Relative includes are resolved against the file containing them. The whole
workspace tree therefore matters; a copied `spack.yaml` may depend on files
several directories above it. `include::` overrides the normal built-in scope
list. Within an include list, earlier entries take precedence; inline values
in the manifest take precedence over included values. See Spack's
[included configuration guide](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/include_yaml.rst)
and [configuration guide](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst).

`group` and `needs` express ordering within an environment's solve. For example,
a compiler group can be concretized first and reused by downstream roots.
They do not launch another environment or schedule a build node. The current
surface's `core` and `common` environments provide tools/libraries that later
payload environments may reuse by exact hash. Serial deliberately excludes
MPI; the MPI environment uses its recorded provider. Preserve those selections
for this build.

## 5. Inspect the concrete graph and fetch its sources

With a completed lock, view roots and dependencies without solving again:

```bash
# Concrete roots, including those not installed yet.
spack -e "$ENV_DIR" find -c -r -l -v

# Concrete roots and dependencies.
spack -e "$ENV_DIR" find -c -d -l -v

# Concrete graph with installation-status markers.
spack -e "$ENV_DIR" find -c -I -d -l -v
```

Review versions, variants, compiler/provider identities, and hashes. `-c`
includes the environment's concrete but uninstalled specs; ordinary installed
package listings alone do not show everything you still need to build. See the
[Spack find command](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/find.py).

To observe or recheck source acquisition for the selected environment, run:

```bash
spack -e "$ENV_DIR" fetch -D
```

`-D` includes dependencies. With the selected locked environment and no extra
spec arguments, this fetch uses the existing concrete specs. It does not
install packages. See the
[Spack fetch command](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/fetch.py).

### Fran and other systems with restricted source access

For this handoff, source acquisition and transfer have already populated the
configured source cache. Use that cache through the existing environment
configuration. Repeating `fetch -D` is useful for learning and account checks;
it normally finds the required archives there and prepares any needed local
stages. Changing login/compute context can create a new stage without changing
the source archive or lock.

Do not point `spack mirror add` at the transferred `.tar` container. The bundle
has already been extracted and its source-mirror contents merged into the
configured source cache. A source mirror/cache holds inputs for builds; a
binary build cache holds built packages. They are different artifacts.

If an expected source is missing, record the exact package/version/hash and
error, check that the intended cache is selected and accessible, and have the
owner arrange the missing acquisition. Preserve the current locks. This is a
source-availability problem, not a reason to ask the solver for another graph.
A configured mirror or source cache does not enforce offline operation: Spack
may try an upstream URL when an artifact is absent. See the
[Spack mirror guide](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/mirrors.rst).

## 6. Install one locked environment with native Spack

Use the prepared shell on the actual node assigned for the build. If moving
from login to compute, first enter a compute allocation and run
`./cse-build compute shell` from the same workspace. Repeat Section 4's
`ENVIRONMENT`/`ENV_DIR` selection in the new shell. Keep the same lockfiles and
configured package store.

Run `./cse-build verify` before taking ownership of the native build. Coordinate
with the owner so accepted input files remain stable while you build. When
using native commands, you are responsible for the environment choice, command
ordering, and checking failures that the wrapper would otherwise handle.

The following block installs and refreshes the selected environment. Section 5
provides the optional separate fetch demonstration; it is not necessary to
repeat that command here when the source checkpoint is complete. Installation
still needs the sources and uses the configured cache.

The block explicitly disables interactive `errexit`/`pipefail`, then enables
error-stop behavior inside a subshell. It stops at the first failure and
reports the status without closing the interactive shell:

```bash
set +e
set +o pipefail
(
  set -e
  set -o pipefail
  test -f "$ENV_DIR/spack.lock"
  spack -e "$ENV_DIR" install --only-concrete -j "$BUILD_JOBS" --fail-fast --show-log-on-error
  spack -e "$ENV_DIR" env view regenerate
  spack -e "$ENV_DIR" module tcl refresh --delete-tree -y
)
native_build_status=$?
printf 'Native build status: %s (complete only if 0)\n' "$native_build_status"
```

For a hands-on walkthrough, run each `spack` command separately instead, inspect
its output, and continue only after it succeeds. Do not run the grouped block
at the same time as the individual commands.

`--only-concrete` prevents installation from triggering an implicit solve.
`--fail-fast` stops on an installation failure; `--show-log-on-error` prints the
available build log. These options do not turn a failed package into a passed
build. See the
[Spack install command](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/install.py).

`BUILD_JOBS` is the prepared per-process build budget. Multiple build processes
on a node add their CPU and memory demand; use the allocated budget rather
than increasing parallelism by trial and error. The wrapper restores its
recorded job default each invocation. A native `-j` adjustment applies to that
native command; it does not change the wrapper's recorded default.

The view and module commands update the configured outputs for this environment.
Only the environment's assigned builder should refresh them. Inspect the
`modules` configuration before using `--delete-tree`; it removes/regenerates
that configured module tree. These package-module operations do not approve or
publish a complete user-facing release. See Spack's
[environment views](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst)
and [module support](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/module_file_support.rst).

To continue GCC manually, repeat the environment selection and build steps in
this order, using the names already in the workspace:

1. `$SHARED_COMPILER_NAME/core`
2. `$SHARED_COMPILER_NAME/common`
3. `$SHARED_COMPILER_NAME/serial`
4. `$SHARED_COMPILER_NAME/mpi-$SHARED_MPI_NAME`

The platform/CCE environments remain outside the current GCC assignment.
If multiple builders work concurrently, they must own distinct environments,
use separate prepared sessions, and have confirmed that Spack's shared store
and database locks work across the actual build nodes. Do not edit shared
recipes, manifests, or locks underneath an active build.

## 7. Inspect results and recover from a failure

The running install terminal is the first source of progress and errors.
From another prepared shell with the same environment selected:

```bash
spack -e "$ENV_DIR" find -c -I -d -l -v
spack -e "$ENV_DIR" find -p
```

For a specific package, copy an actual concrete hash from the output above:

```bash
export PACKAGE_HASH="<concrete-hash-from-this-environment>"
spack -e "$ENV_DIR" location -i "/$PACKAGE_HASH"
spack -e "$ENV_DIR" location -s "/$PACKAGE_HASH"
spack -e "$ENV_DIR" logs "/$PACKAGE_HASH"
```

Use those commands individually as appropriate: an installed prefix exists
after installation succeeds; a stage is available only while retained; a
combined build log is available after it has been written or archived.
`spack logs` is not a live streaming build viewer. Use the active terminal and
the printed stage/log paths during a build. See the
[Spack logs command](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/logs.py).

Record the environment, command, concrete package hash, node/context, result,
and relevant log path. Fix an operational problem and retry the same locked
install. If a recipe or build-input change is required, coordinate that change
with the owner before proceeding; do not force a new solve just to clear an
error. Compilation success still needs the agreed functional/runtime validation.

## 8. Reconnect and resume

For a surviving tmux session, return to the same host and workspace and run
`./cse-build login` or `./cse-build compute` for its actual context. The `shell`
action has no tmux session to reattach. A terminated host or expired allocation
can also end a tmux session; neither mechanism replaces persistent build state.

For a new shell, repeat Section 2's entry command and Section 4's environment
selection. That restores your runtime/context variables and native command
selection. Check whether a prior process is still running before launching
another build against the same environment. Do not start a second copy merely
because your client disconnected.

Keep the same workspace, lockfiles, configured source cache, and installed
store. Completed package hashes can be reused. If installation completed but
view/module refresh did not, rerun the appropriate refresh after confirming
that environment is no longer being built. Source-fetch recovery does not
require repeating the whole connected-system transfer when the existing cache
already contains the required inputs.

Exit the prepared shell normally when finished so its permission-normalization
hook runs. Before handing responsibility back, run `./cse-build login status`
from a clean login context after coordinated writes have stopped, and provide
the checkpoint/log information from Section 1. Do not copy another builder's
private cache, bootstrap store, or keyring.

## 9. Learn concretization without replacing the current build

Concretization is worth learning. The practical distinction is whether you are
**consuming the accepted graph** or **creating a new one**.

| Exercise | What it teaches | Effect on current Fran work |
|---|---|---|
| Inspect the existing manifest, configuration, and concrete graph | How constraints and platform choices became an exact build graph | Read-only inspection |
| Repeat fetch and perform the assigned locked install | Source-cache use, compilation, dependency reuse, logs, and exposure | Advances the assigned build using the accepted locks |
| Create a separate practice environment and solve it | Manifest authoring, concretizer choices, and changed hashes | Separate output paths and source requirements; does not replace accepted locks |

### What happens if you concretize again?

`./cse-build concretize` keeps every existing lockfile and solves only missing
ones. With all eight locks present, it reports that it is keeping them and
verifies the set. It will not demonstrate a new solve.

Native `spack -e "$ENV_DIR" concretize` normally preserves already-concretized
roots and concretizes new/unconcretized roots. `--force` allows replacing
existing concrete specs. `--fresh` controls dependency reuse for the solve;
it is not the same as `--force`. Keep both experimentation and forced solves
out of the accepted shared workspace. See
[Spack environment concretization](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst)
and [concretizer arguments](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/common/arguments.py).

A new solve is not guaranteed to produce the same hashes, even when the root
package requests look the same. Runtime/repository identity, configuration,
compiler/external facts, target, and reuse candidates can affect the result.
Reusing a compatible lock preserves the selected concrete identities. Keeping
a lock in a practice copy therefore teaches reproduction; deliberately solving
without that lock teaches selection. A copied lock is not permission to write
to the original store or exposure paths.

Different hashes do not always require different source tarballs: compiler or
variant changes can reuse the same source version. Conversely, a new solve can
require versions, resources, or patches not present in the prepared cache.
Pointing the practice environment at the existing source mirror does not make
those missing artifacts appear or give Fran additional network access.

### Set up a separate practice exercise deliberately

A personal directory alone does not isolate an environment. Before running an
experimental solve or install:

- Keep the accepted shared workspace intact. Copy the needed configuration
  tree, not just a manifest whose relative includes will break; alternatively
  write a small, self-contained native Spack manifest.
- Select a private install tree (including its database), stage, misc cache,
  view, and module roots. Disable views/modules for an initial exercise if they are unnecessary.
  Check the effective paths with `config get` and `config blame` before writing.
- Preserve the intended compiler/external and recipe definitions when comparing
  against the CSE graph. Inspect included files and absolute paths: copying a
  directory or changing its name does not rewrite them.
- Reuse the shared sources only through an agreed read-only source-mirror
  location with a private writable source cache. Do not turn the team's shared
  source cache into the practice workspace's write destination.
- Decide explicitly whether to retain the copied lock for reproduction or omit
  it **only in the practice copy** for a new solve. Compare the resulting graph
  with the accepted lock; do not copy experimental locks back to the build.

For an exercise that intentionally needs new sources, a system with sufficient
network access is usually simpler. On Fran, agree on the exercise's source set
first; the main GCC assignment should not depend on another mirror-transfer
cycle solely to demonstrate compilation. A practice copy is not ready until
its effective configuration and output locations have been checked. The
`cse-build` program in the accepted workspace is not a personal-workspace
creation tool.

## 10. Wrapper actions and their native Spack equivalents

All actions start with the prepared runtime/context and workspace input checks.
The table describes the work after that setup.

| `cse-build` action | Work performed |
|---|---|
| `status --surface shared` | Reports the workspace checkpoint and runs `spack -e ... find -lv` for GCC environments |
| `verify` | Checks all eight locks with the workspace verifier; this CSE check is not Spack's installed-file `spack verify` command |
| `concretize` | Keeps existing locks; runs `spack -e ... concretize --fresh -j 1` only where a lock is missing, then verifies the full set |
| `fetch --surface shared` | Verifies all locks, then runs `spack -e ... fetch -D` for GCC environments |
| `install --surface shared` | Verifies all locks, then runs fetch, `install --only-concrete`, view regeneration, and package-module refresh for each GCC environment |

`--surface` applies to status, fetch, and install. It does not narrow the
whole-workspace verification or concretization actions. Native `spack -e`
commands target the one environment you name; they do not run CSE's whole-set
checks or all of the wrapper's follow-up commands automatically. Returning to
`cse-build` actions after native inspection is normal; keep the same workspace
and prepared session.

## Official Spack 1.2.2 references

- [Environments, manifests, locks, groups, and views](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst)
- [Included configuration scopes](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/include_yaml.rst)
- [Configuration, path variables, and inspection](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst)
- [Package preferences, requirements, and externals](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packages_yaml.rst)
- [Source mirrors](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/mirrors.rst)
- [Install command](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/install.py)
- [Fetch command](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/fetch.py)
- [Find command](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/find.py)
- [Build logs](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/logs.py)
- [Module support](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/module_file_support.rst)
