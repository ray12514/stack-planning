# CSE Builder Handoff

## Purpose

The initialized CSE workspace is the build handoff. It contains the static
catalog snapshot, generated configuration scopes, eight Spack environments,
deployment paths, module policy, exact Spack identity, and any lockfiles or
installed hashes completed so far.

The receiving builder does not need Cluster Inspector, Stack Composer,
Stack Content, Stack Planning, or the original render inputs.

## Start or resume

Go to the handed-off workspace and run:

```bash
cd <complete-workspace-path>
./cse-build login
```

No system, release, compiler, MPI, catalog, install-tree, cache, view, module,
or environment values are entered by the builder. `cse-build` uses the values
already rendered into the workspace.

With no action, the command:

1. verifies CSE group access and the workspace;
2. selects or provisions the exact recorded Spack runtime;
3. creates private Spack cache and keyring state for the current builder;
4. activates Spack and the generated workspace configuration;
5. reports the current lockfile checkpoint; and
6. creates or reattaches a login-context tmux session named for the system and
   release.

Run `./cse-build login` again after a connection loss to reattach to the same tmux
session on that host. A tmux session does not survive loss of the host or an
expired compute allocation; the workspace, lockfiles, and installed packages
remain the recovery point.

To use a prepared shell without tmux:

```bash
./cse-build login shell
```

If tmux is unavailable, the default command reports that condition and opens
the prepared shell directly.

## Runtime prerequisites

The builder must have:

- membership in the recorded CSE Unix group;
- read and write access to the restricted workspace and package store;
- an absolute, writable site `WORKDIR` value;
- Git when the recorded Spack checkout still needs to be provisioned; and
- network access on the node used for first-time Spack provisioning or source
  fetches.

The workspace records the approved Spack source, version, tag, commit, shared
root, and local fallback root. Automatic mode uses an accessible matching
checkout and otherwise follows the recorded shared/local preference. The
builder may choose a mode explicitly:

```bash
./cse-build login --spack-mode shared
./cse-build compute --spack-mode local
```

The local path is `$HOME/STACK_TESTING/spack/<recorded-version>`. Both modes
verify the same source, version, tag, commit, and clean-checkout requirements.
Changing only the checkout path does not change the concrete DAG and does not
require reconcretization. Actions run from the prepared session retain that
session's selected mode automatically.

Do not run `spack isolate`, edit the selected Spack checkout, pull or switch
branches in place, or replace one pinned version with another in the same
directory.

## Checkpoint actions

The same entry point works before concretization, after lockfile creation, and
partway through installation. Use the login context for connected preparation
and the compute context for package installation:

```bash
./cse-build login status
./cse-build login concretize
./cse-build login verify
./cse-build login fetch
./cse-build compute install
```

`status` reports which environments have lockfiles and which concrete specs
are already installed.

`concretize` creates only missing lockfiles. Existing lockfiles are preserved.
After all eight exist, the command verifies configuration scopes, required
roots, toolchain bindings, and shared producer hashes.

`verify` checks the current configuration boundary and all lockfiles without
installing packages.

`fetch` downloads sources for every locked environment. Use it on a login node
when compute nodes do not have outbound network access.

`install` requires verified lockfiles, installs the environments in the
recorded order, regenerates views, and refreshes modules. Concrete hashes
already present in the restricted shared Spack store are reused.

The entry point is generated plain Bash. Its actions map directly to these
Spack commands for each applicable environment:

```bash
spack -e <environment> find -lv
spack -e <environment> concretize --fresh -j 1
spack config scopes -vp
spack -e <environment> config scopes -vp
spack python scripts/verify-lockfiles.py
spack -e <environment> fetch -D
spack -e <environment> install --only-concrete -j "$BUILD_JOBS" --fail-fast
spack -e <environment> env view regenerate
spack -e <environment> module tcl refresh --delete-tree -y
```

The wrapper determines ordering, skips environments that already have locks
when concretizing, and stops on the first failed command. Package managers may
inspect `./cse-build` or run the same commands manually.

The initialized workspace records both reviewed node contexts. Each invocation
selects an executable stage by creating and running a small probe; a writable
but `noexec` path is skipped. The login and compute contexts have separate tmux
sessions, stages, and mutable command caches, but share the per-builder Spack
bootstrap store, workspace, source cache, locks, install tree, views, modules,
and pinned Spack identity. Concretize on the login node first so Clingo is
available when installation moves to a network-restricted compute node.
Fetching may occur on a login node and installation later on a compute node
without reconcretization.

## Handoff record

Before transferring responsibility, record:

- system and release;
- current checkpoint: zero, some, or all lockfiles;
- last environment and action attempted;
- result and relevant log or evidence path; and
- whether source fetching is complete.

Do not run the same release on the same system from both builder accounts at
the same time. Spack locking remains enabled, but the initial conversion trials
use an explicit single-operator handoff on each system.

Signing authority is not transferred through this workspace. Publishing a
signed build cache remains a separate authorized release operation.
