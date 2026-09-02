# Package Manager Spack Build and Publication SOP

| Document control | Value |
|---|---|
| Status | Working draft |
| Intended operator | Package manager familiar with Spack concepts but not site-specific commands |
| Procedure scope | Environment definition, build, validation, publication, and release retention |

## 1. Purpose

This SOP defines the standard process for a package manager to build and
publish software with Spack on a supported system. The package manager supplies
the package intent. The site-supplied static platform catalog supplies reviewed
compiler, MPI, target, and external-package configuration.

This document contains the normal operating procedure. A system-specific
handoff supplies actual paths, supported catalog releases, toolchain names,
Unix groups, scheduler details, and support contacts. A separate runbook may
cover site provisioning, exceptional recovery, and platform-specific failure
analysis. The operator should not need the runbook for a normal build and
publication cycle.

The required sequence is:

```text
select reviewed platform configuration
  -> define the Spack environment
  -> concretize and review the lockfile
  -> build and test on the target system
  -> publish the approved installation and modules
  -> retain the source, lockfile, and validation record
```

Every environment must use an explicit supported toolchain. A successful build
is not sufficient for publication. Runtime and module tests must also pass.

### 1.1 Procedure use

Complete the sections in order. Each section defines a control point. Do not
continue past a failed control point.

1. Complete the operating record in Section 3.
2. Start the approved Spack runtime and complete preflight.
3. Select one released catalog and its documented scopes.
4. Define and review the environment source.
5. Concretize and review `spack.lock`.
6. Build and run the required tests on the target node types.
7. Publish only the accepted concrete hashes.
8. Retain the environment source, lockfile, evidence, and approval record.

Command examples use angle-bracket placeholders for site-supplied values. The
operator must replace every placeholder before running a command. Shell
variables shown in the operating record may be used to avoid repeating paths.

### 1.2 Evidence format

Retain command output as text files together with the environment source,
lockfile, manifests, checksums, and test programs. Record the command, node,
date, exit status, and output for every required test. Screenshots are not
required and must not be the only evidence for a control point.

### 1.3 Static platform catalog orientation

The static platform catalog is the site's versioned statement of the platform
configuration supported for Spack builds on one system. It tells the package
manager which compilers, compatible MPI and GPU providers, targets, externals,
and common Spack policies are approved, including which combinations may be
used together. It does not select application packages or deployment paths.
The package manager reads its manifest, chooses a supported set of scopes, and
follows this SOP to include those scopes in an owned Spack environment.

## 2. Responsibilities

| Role | Responsibility |
|---|---|
| Package manager | Select packages and catalog scopes, define the environment, build, test, and prepare the release record. |
| Technical reviewer | Review the toolchain, lockfile, test results, module behavior, and change assessment. |
| Release authority | Approve publication under the application team's normal process. |

The same person may fill more than one role when local policy permits it. A
module published in a centrally managed namespace requires approval from the
owner of that namespace.

## 3. Required inputs

Record these inputs before concretization:

- target system and node types used for the build and runtime tests;
- approved public static platform catalog root, release, and approval record;
- selected compiler and, when applicable, matching MPI and GPU scopes;
- root package specs, versions, variants, and dependency constraints;
- exact Spack version and package-recipe source;
- install tree, build-stage, cache, view, and module locations;
- filesystem ownership and access policy; and
- application-team release identifier.

The static platform catalog contains configuration. It does not select the
application packages, install tree, views, module roots, or release lifecycle.
Those remain package-manager or site deployment decisions.

### 3.1 Operating record

Create a release worksheet and fill every actual-value field before preflight.
The worksheet may be a tracked text file, ticket, or release database record.

| Item | Shell name used in this SOP | Actual value required |
|---|---|---|
| Target system | `STACK_SYSTEM` | System name |
| Application release | `STACK_RELEASE` | Immutable application release identifier |
| Catalog release root | `CATALOG_RELEASE_ROOT` | Absolute path to one approved catalog release |
| Environment directory | `ENVIRONMENT_ROOT` | Absolute path containing `spack.yaml` |
| Approved Spack checkout | `SPACK_ROOT` | Absolute path to the pinned checkout |
| Spack version | `SPACK_VERSION` | Approved version and commit |
| Package repository | Release record | Approved `spack-packages` or site-repository source and commit |
| Per-user Spack state | `SPACK_USER_CACHE_PATH` | Builder-private absolute path |
| Build stage | `SPACK_STAGE_ROOT` | Builder-writable absolute path |
| Install tree | Site configuration | Absolute package store selected by the application team |
| Source cache | Site configuration | Absolute shared cache populated during the controlled fetch step |
| Miscellaneous cache | Site configuration | Absolute shared root, partitioned by builder when required |
| Build cache | Release configuration | Approved private or published mirror URL and trust policy |
| View root | Environment configuration | Absolute view path, or `none` |
| Module root | Environment configuration | Absolute module path, or `none` |
| Build group | Deployment record | Approved Unix group |
| Build and runtime nodes | Deployment record | Login, build, and test node types |
| Reviewer and release authority | Release record | Named people or approving roles |

Start the approved Spack session after filling the record:

```bash
export STACK_SYSTEM="<system>"
export STACK_RELEASE="<application-release>"
export CATALOG_RELEASE_ROOT="<absolute-catalog-release-root>"
export ENVIRONMENT_ROOT="<absolute-environment-directory>"
export SPACK_ROOT="<absolute-approved-spack-root>"
export SPACK_VERSION="<approved-spack-version>"
export SPACK_STAGE_ROOT="<absolute-build-stage>"

export SPACK_DISABLE_LOCAL_CONFIG=true
export SPACK_USER_CACHE_PATH="<absolute-per-user-cache-root>/$USER/spack/$SPACK_VERSION"
export PYTHONDONTWRITEBYTECODE=1

test -f "$SPACK_ROOT/share/spack/setup-env.sh"
test -r "$CATALOG_RELEASE_ROOT/manifest.yaml"
source "$SPACK_ROOT/share/spack/setup-env.sh"
spack --version
```

Record the output of `spack --version` and the checkout commit. Stop if they do
not match the approved Spack identity.

## 4. Storage, access, and Spack runtime

Keep the following locations separate:

- the pinned Spack tool root;
- the Spack package install tree;
- the build workspace;
- shared source and package-manager metadata caches;
- per-builder build stages and mutable user state;
- build caches;
- views and module roots; and
- release records and test evidence.

Use a site-approved, pinned Spack installation. Record its exact version,
source, and commit when applicable. Do not treat the Spack checkout as the
package install tree or store mutable build artifacts inside it.

Use per-user mutable Spack state:

```bash
export SPACK_DISABLE_LOCAL_CONFIG=true
export SPACK_USER_CACHE_PATH="<approved-per-user-cache-root>/$USER/spack/<version>"
source "<approved-spack-root>/share/spack/setup-env.sh"
```

If signing is used, keep the keyring in a private per-user or site-approved
location outside the Spack tool root and package install tree.

The application team's shared workspace must be group-writable while a release
is assembled. Record the owning Unix group for that independently managed
software stack in its deployment inputs; different teams or stacks may use
different approved groups. Keep that group stable for the life of the release.
Use setgid directories and the site's default ACL or umask policy. Published
users outside the approved package-manager group receive read and execute
access, not write access.

Record which paths are shared and which are builder-private before work starts:

| State class | Normal policy |
|---|---|
| Shared build state | Workspace, generated environment files and lockfiles, source cache, package install tree/database/locks, views, modules, file-backed build cache, and release evidence. Restrict write access to the approved build group. |
| Builder-partitioned shared state | Mutable package-manager metadata may use a persistent `$USER` partition below a shared root when concurrent replacement is unsafe. The partition remains accessible to the build group for handoff and recovery. |
| Builder-private state | Build stage, `SPACK_USER_CACHE_PATH`, bootstrap state, signing keyring, and other temporary command state. A receiving builder creates its own paths rather than inheriting another user's. |
| Spack tool root | Shared and read-only, or an identity-equivalent builder-local checkout treated as immutable for the release. Never use it as a cache or package store. |

Setgid, default ACLs, and a group-friendly umask establish creation defaults,
but do not override software that explicitly requests `0600` files or `0700`
directories. The selected build adapter must therefore normalize owner-created
content on every shared non-package surface and verify access from another
group member before handoff. A typical restricted policy uses `2770` for
directories, `0660` for ordinary files, and `0770` for executables. Spack's
native package-permission configuration owns installed prefixes; do not use a
blind recursive chmod around the package database and prefix locks.

### 4.1 Installed-package permission policy

The package manager must supply the installed-prefix policy as deployment
configuration. It is not part of the static platform catalog. For a published
stack managed by a package-manager group, use:

```yaml
packages:
  all:
    permissions:
      group: <approved-package-manager-group>
      read: world
      write: group
```

This may be written directly below `spack.packages` in an environment's
`spack.yaml`, or placed in a separate `packages.yaml` inside a configuration
scope named by the environment's `spack.include` list. A managed workspace
generator should create the included file from the deployment access values so
every environment receives the same policy. A package manager assembling an
environment without that generator must create and include the policy file.

For the approved Spack runtime, verify the merged configuration before
installation:

```bash
spack -e "$ENVIRONMENT_ROOT" config get packages
```

The published filesystem contract is `2775` for directories, `0775` for
executable files, and `0664` for ordinary files. The owner and approved package
manager group can write. Users outside the group can traverse directories, run
executables, and read ordinary files, but cannot write. The leading `2` is the
setgid bit, which makes new entries inherit the directory's group; it is not
the sticky bit. Sticky is the leading `1` bit and is not used here.

For a restricted build tree, change only `read` from `world` to `group` and
retain `write: group`. Its normal modes are `2770`, `0770`, and `0660`. Keep the
private build cache in the restricted tree. General users consume the final
installed prefixes, views, and modules rather than the private cache.

### 4.2 Spack configuration ownership

Record portable package intent separately from system deployment choices. A
managed stack uses these durable inputs:

| Information | Authoritative input | Spack output or configuration |
|---|---|---|
| Observed compiler, MPI, GPU, operating-system, and external-package facts | `profile.yaml` or the released static catalog | Selected `packages.yaml`, compiler, target, and provider scopes |
| Package names, versions, variants, dependency constraints, and lane intent | `stack.yaml`, a package set, or a package-manager-owned `spack.yaml` | `spack.specs` and explicit compiler or toolchain constraints |
| Install tree, build stage, source and miscellaneous caches, view and module roots, build-cache destinations, and access policy | `deployment.yaml` or an equivalent controlled deployment record | `config.yaml`, `packages.yaml`, `modules.yaml`, mirror configuration, and view paths |
| Site-wide provider and selection defaults | Reviewed defaults and catalog policy | Included configuration scopes |

Do not use an operator-local shell-variable bundle as the release contract.
Shell variables may shorten commands during one session, but the retained
environment source, deployment record, lockfile, and release manifest must
contain the reviewed values.

At minimum, the effective Spack configuration must explicitly resolve these
settings before concretization:

```yaml
config:
  install_tree:
    root: <absolute-install-tree>
  build_stage:
    - <absolute-per-builder-stage>
  source_cache: <absolute-reviewed-source-cache>
  misc_cache: <absolute-builder-misc-cache>
  locks: true
```

Keep `SPACK_USER_CACHE_PATH`, bootstrap state, and the signing keyring outside
that shared configuration because they are private to the active builder.
Configure build-cache mirrors separately from the source cache. A source cache
contains fetched source inputs. A build cache contains installed concrete
packages and their metadata. They are different trust and promotion
boundaries.

Module configuration must state whether module generation is enabled, the
absolute generated-module root, the naming or projection policy, and required
dependency loads and conflicts. The SOP does not prescribe one complete
`modules.yaml`; the package manager selects those presentation details and
retains the generated file with the release.

Verify the merged values rather than assuming that the intended file won
scope precedence:

```bash
spack -e "$ENVIRONMENT_ROOT" config get config
spack -e "$ENVIRONMENT_ROOT" config get packages
spack -e "$ENVIRONMENT_ROOT" config get mirrors
spack -e "$ENVIRONMENT_ROOT" config get modules
spack -e "$ENVIRONMENT_ROOT" config scopes -vp
```

### 4.3 Supply-chain security boundary

Treat the Spack runtime, package repositories, package recipes, patches,
fetched sources, external packages, and binary caches as separate inputs to
the release. A checksum proves that fetched bytes match the checksum approved
by the recipe. It does not prove that the recipe, upstream source, or dependency
is safe. A lockfile fixes the selected concrete graph; it does not replace
review of a changed recipe repository or vulnerability assessment.

Use this control sequence for every release:

1. Pin the Spack runtime and every package repository to reviewed commits.
2. Record the package-repository diff since the last accepted release. Review
   changed recipes, patches, fetch locations, build systems, and custom hooks
   that enter the selected dependency closure.
3. Concretize once, review the complete graph and externals, and retain the
   resulting `spack.lock` without manual edits.
4. Fetch in the restricted, network-enabled stage. Require approved checksums
   or immutable version-control commits and retain the populated source cache.
5. Build the reviewed lockfile from that cache. Where policy requires network
   isolation, block outbound access during compilation and installation.
6. Run compile, runtime, linkage, integrity, module, and permission tests.
   Retain the generated SBOMs and maintain a separate inventory for externals.
7. Sign approved binary packages and promote only their exact concrete hashes
   to the controlled build cache.
8. Install the user-facing release from the approved lockfiles and signed build
   cache only. A cache miss returns to restricted build and review.

Reviewing every line of every recipe on every build is not a scalable control.
The scalable unit is the change to a pinned package-repository generation plus
the recipes and patches reachable from the selected lockfile. Perform deeper
manual review for new repositories, new or locally modified recipes, changed
fetch logic, packages that execute downloaded code during the build, security
critical components, and exceptions to checksums or isolation. Run the
approved source-code, secret, license, and vulnerability scanners in addition
to this review.

Spack's source-oriented model gives the operator detailed control over specs,
recipes, patches, source checksums, build provenance, and concrete hashes, but
it also places more recipe and build-process trust on the site than a signed
binary distribution normally does. The release process supplies the policy
boundary: pinned inputs, reviewed changes, controlled fetching, isolated
building, validation, signed binary promotion, SBOM retention, vulnerability
scanning, and immutable publication. See the
[Spack supply-chain security research](spack_supply_chain_security_primary_source_research_v1.md)
and the [Spack 1.2 signing and SBOM note](spack_1_2_signing_sbom_security_note_v1.md)
for the exact signing, SBOM, integrity, and CVE boundaries.

## 5. Preflight

Complete these checks from the node types that will perform the build and
runtime tests:

- the catalog release and selected scopes are readable;
- the selected compiler and, when applicable, its approved MPI pairing are
  present in the catalog;
- the install tree, caches, views, and module root are reachable;
- shared generated content is readable, writable, and traversable by another
  member of the approved build group;
- the selected build stage is writable and has adequate space and inodes;
- the Spack version matches the approved version;
- the package-recipe source is available;
- the expected scheduler, launcher, fabric, and GPU resources are available
  when required; and
- the active configuration scopes contain no unexpected user, system, or site
  policy.

Check the active scopes before using an environment:

```bash
spack config scopes -vp
spack -e "$ENVIRONMENT_ROOT" config scopes -vp
```

Run the global command during initial preflight. Run the environment command
after `spack.yaml` has been created in Section 7 and before concretization.

Stop if an unexpected scope can affect the solve. Correct the environment or
runtime setup before concretization.

Check a build-stage candidate from the intended build node:

```bash
export SPACK_STAGE_ROOT="<approved-build-stage>"
mkdir -p "$SPACK_STAGE_ROOT"
test -d "$SPACK_STAGE_ROOT"
test -w "$SPACK_STAGE_ROOT"
touch "$SPACK_STAGE_ROOT/.spack-write-test"
rm "$SPACK_STAGE_ROOT/.spack-write-test"
df -Pk "$SPACK_STAGE_ROOT"
df -Pi "$SPACK_STAGE_ROOT"
```

Also confirm the quota, cleanup schedule, retention period, and mount options.

Confirm the released catalog is readable and complete:

```bash
test -r "$CATALOG_RELEASE_ROOT/README.md"
test -r "$CATALOG_RELEASE_ROOT/manifest.yaml"
test -r "$CATALOG_RELEASE_ROOT/reports/static-plan.yaml"
test -d "$CATALOG_RELEASE_ROOT/scopes"
find "$CATALOG_RELEASE_ROOT/scopes" -type f -print | sort
```

Inspect the release manifest and static plan. Confirm that their system,
release, compiler, MPI, GPU, target, module, prefix, and external-package facts
match the operating record. Stop if a required scope is absent or if the
catalog records an unresolved provider dependency.

Preflight passes only when the recorded paths and node types are usable, the
approved Spack identity matches, the catalog is readable, and the global and
environment scope listings contain no unexpected configuration.

## 6. Select platform configuration

Read `manifest.yaml` and select the exact scope paths it publishes. A
normal environment includes:

1. common site configuration;
2. one compiler scope;
3. one target or platform scope;
4. one matching MPI scope for MPI builds; and
5. one compatible GPU scope for GPU builds.

Use an immutable catalog release path in a reproducible environment. A site may
publish a `current` pointer for discovery, but the environment source and
release record must identify the resolved release directory. The released
catalog must be readable and traversable by all authenticated system users.
Consumers outside the approved catalog-manager group must not have write
access. The approved group retains management access, but no operator edits a
released version in place. Correct the owning inputs, generate and review a new
restricted catalog release, publish a new version with fresh approval metadata
and checksums, and move the discovery pointer only after acceptance. Retain or
retire the superseded version through the recorded release policy.

Use `include::` so the environment's explicit configuration replaces ambient
configuration. Use absolute paths to an immutable catalog release in a
published environment:

```yaml
spack:
  include::
    - <absolute-catalog-release-root>/scopes/common
    - <absolute-catalog-release-root>/scopes/compilers/<compiler>/<version>
    - <absolute-catalog-release-root>/scopes/mpi/<provider>/<version>/<compiler-flavor>
    - <absolute-catalog-release-root>/scopes/platform/<platform>
```

Use the toolchain name recorded in the selected MPI scope's
`toolchains.yaml`. A Serial environment omits the MPI scope and constrains each
root with the selected compiler. Do not retype catalog-owned compiler, MPI,
external prefix, or module policy in the environment.

Keep the catalog and environment tree together when a private test uses
relative includes. Do not copy a single `spack.yaml` without the configuration
directories it references.

Select only documented compiler and MPI pairings. Do not construct a pairing from
module names or installed directories without catalog support.

Record the exact selected scope paths in the release worksheet. Catalog
selection passes when every selected path is present in `manifest.yaml` and
the environment scope listing resolves those paths without an ambient policy
override.

## 7. Define the environment

Define root packages in `spack.yaml`. Pin public versions and important
variants. Use normal Spack spec syntax.

Minimum requirements:

- every source-built root has an explicit compiler;
- Serial roots explicitly disable MPI;
- MPI roots explicitly enable MPI and bind the selected provider;
- GPU roots bind the selected compiler, MPI provider, and GPU runtime;
- system-provided components remain external when site policy requires them;
- dependency versions that affect compatibility are constrained; and
- views and module projections avoid ambiguous multi-version names.

A package manager may use one environment or several independently
concretized environments. Use separate environments when compiler, MPI, GPU,
or module-conflict boundaries require them.

### 7.1 Minimum Serial environment

The following source is the minimum normal Serial pattern. Replace every
placeholder with values from the operating record and catalog manifest:

```yaml
spack:
  include::
    - <absolute-catalog-release-root>/scopes/common
    - <absolute-catalog-release-root>/scopes/compilers/<compiler>/<version>
    - <absolute-catalog-release-root>/scopes/platform/<platform>

  specs:
    - <package>@<version>~mpi %<compiler>@<compiler-version>

  concretizer:
    unify: false
    reuse: false

  view: false
```

If the package has no MPI variant, omit `~mpi`. The root must still select the
approved compiler. Add the application-owned install, view, and module policy
before concretization.

### 7.2 Minimum MPI environment

The following source is the minimum normal MPI pattern:

```yaml
spack:
  include::
    - <absolute-catalog-release-root>/scopes/common
    - <absolute-catalog-release-root>/scopes/compilers/<compiler>/<version>
    - <absolute-catalog-release-root>/scopes/mpi/<provider>/<version>/<compiler-flavor>
    - <absolute-catalog-release-root>/scopes/platform/<platform>

  specs:
    - <package>@<version>+mpi %<catalog-toolchain-name>

  concretizer:
    unify: false
    reuse: false

  view: false
```

Read `<catalog-toolchain-name>` from the selected MPI scope's
`toolchains.yaml`. Do not construct the name from the provider or module name.
Add a GPU scope and the approved GPU variants only for a GPU build.

### 7.3 Deployment configuration

The package manager or site supplies deployment paths through the reviewed
deployment record described in Section 4.2. A minimum rendered environment
configuration has this form:

```yaml
spack:
  config:
    install_tree:
      root: <absolute-install-tree>
    build_stage:
      - <absolute-per-builder-stage>
    source_cache: <absolute-source-cache>
    misc_cache: <absolute-builder-misc-cache>
    locks: true
```

Add view and module configuration only when the release publishes them. The
view path and module root must be absolute, owned by the application team, and
recorded before concretization. Configure the build-cache destination and
signature policy independently from the source and miscellaneous caches. Do
not take deployment paths from the static catalog. The catalog provides
platform configuration only.

### 7.4 Ordered producer example

Spack 1.2 groups and `needs` may be used to order producers and consumers in
one environment:

```yaml
spack:
  packages:
    c:
      prefer: [gcc@<version>]
    cxx:
      prefer: [gcc@<version>]
    fortran:
      prefer: [gcc@<version>]
    mpi:
      require: [openmpi]

  specs:
    - group: compiler
      specs:
        - gcc@<version>

    - group: mpi
      needs: [compiler]
      specs:
        - openmpi@<version> %<catalog-toolchain-name>

    - group: applications
      needs: [compiler, mpi]
      specs:
        - hdf5@<version>+mpi+fortran %<catalog-toolchain-name>

  concretizer:
    unify: false
    reuse: false
```

The toolchain selects the compiler and MPI providers conditionally for the
languages and virtuals each root actually uses. `needs` orders the groups and
makes their producer hashes available; it is not a selector. The soft
preferences remain useful defaults but are not sufficient enforcement. Resolve
new lockfiles for this stack-built-compiler surface without concrete-spec reuse,
then reuse identical hashes between environments through the shared install
tree, build cache, and normal Spack locking. An external compiler surface may
retain its established reuse policy because it has no managed producer to
protect from an installed seed-compiler DAG.

## 8. Concretize and review

Concretize and retain the generated lockfile:

```bash
spack -e "$ENVIRONMENT_ROOT" concretize --fresh
spack -e "$ENVIRONMENT_ROOT" find -c -d -l -v
spack -e "$ENVIRONMENT_ROOT" find -c -d -e -l -v
```

The first `find` shows the complete concrete DAG, including specs not yet
installed. The second filters that DAG to externals.

Review at least:

- root versions and variants;
- compiler selection;
- MPI and GPU providers;
- external package modules and prefixes;
- CPU target;
- dependency versions and hashes;
- the absence of MPI from Serial builds; and
- the absence of unapproved providers or configuration.

Do not edit `spack.lock`. Correct the environment or selected catalog scopes
and concretize again.

Concretization passes only when `spack.lock` exists, every root matches the
approved intent, all providers and externals come from approved scopes, and no
unreviewed compiler, target, or dependency appears in the graph. Save the two
`find` listings with the release evidence.

## 9. Build and validate

Fetch on a network-capable node when compute nodes cannot reach package
sources:

```bash
spack -e "$ENVIRONMENT_ROOT" fetch -D
```

The later install may run on a different node when it uses the same workspace,
source cache, install tree, Spack version, and lockfile.

When several environments install in parallel, verify the complete lock set
first, give every process a distinct mutable user cache, never run the same
environment twice, and assign view/module refresh to that environment's one
owning process. After parallel work stops, run the shared-output permission gate
before transferring responsibility to another builder.

Install and refresh the environment-owned presentation:

```bash
spack -e "$ENVIRONMENT_ROOT" install --fail-fast
spack -e "$ENVIRONMENT_ROOT" env view regenerate
spack -e "$ENVIRONMENT_ROOT" module tcl refresh --delete-tree -y
```

Run view regeneration only when the environment defines a view. Run module
refresh only when the environment defines module generation. A build that does
not publish a view or modules records those checks as not applicable.

Run the checks that apply:

- compile and run representative C, C++, and Fortran programs;
- confirm headers, libraries, RPATHs, and package metadata;
- test Serial packages without MPI loaded;
- run scheduler-launched, multi-node MPI tests;
- confirm the intended launcher, fabric, and MPI provider;
- run GPU and GPU-aware MPI tests when applicable;
- verify views and package modules after regeneration; and
- test from clean login-node and compute-node sessions.

Record the result as `built`, `runtime-passed`, or `held`. Publish only a
`runtime-passed` environment.

Validation passes only when the required compile, runtime, scheduler, MPI,
GPU, view, module, clean-session, and permission tests have recorded successful
exit status. Mark the release `held` when a required resource was unavailable
or a required result was not obtained.

## 10. Publish

Use the application team's approved publication method. Preserve the reviewed
lockfile and concrete hashes.

When a build cache is used:

1. push only validated concrete packages;
2. create a separate publication workspace;
3. copy the approved lockfile;
4. install the locked packages from the approved cache;
5. stop on a cache miss rather than building unreviewed source in the
   publication workspace; and
6. compare the published hashes with the validated build hashes.

The site supplies the approved cache push and signing command. After the
validated hashes are available in that cache, perform the cache-only install
with a matching publication environment:

```bash
export PUBLICATION_ENVIRONMENT_ROOT="<absolute-publication-environment>"

test -f "$PUBLICATION_ENVIRONMENT_ROOT/spack.yaml"
cp "$ENVIRONMENT_ROOT/spack.lock" "$PUBLICATION_ENVIRONMENT_ROOT/spack.lock"
spack -e "$PUBLICATION_ENVIRONMENT_ROOT" find -c -d -l -v
spack -e "$PUBLICATION_ENVIRONMENT_ROOT" install \
  --only-concrete --use-buildcache=only --fail-fast
```

Do not concretize the publication environment. A cache miss is a failed
publication control point. Return to the validated build, supply the missing
approved hash, and repeat the cache-only install. If the correction changes a
hash, create a new release record.

Record and compare hashes before approval:

```bash
export EVIDENCE_ROOT="<absolute-evidence-path>"
mkdir -p "$EVIDENCE_ROOT"
spack -e "$ENVIRONMENT_ROOT" find --format '{hash}' | sort \
  > "$EVIDENCE_ROOT/validated-hashes.txt"
spack -e "$PUBLICATION_ENVIRONMENT_ROOT" find --format '{hash}' | sort \
  > "$EVIDENCE_ROOT/published-hashes.txt"
diff -u \
  "$EVIDENCE_ROOT/validated-hashes.txt" \
  "$EVIDENCE_ROOT/published-hashes.txt"
```

When the validated install tree is published directly, freeze the accepted
release after view, module, permission, and clean-session tests pass. Do not
change an accepted release in place.

Generate or refresh views and modules only after installation. Use
version-sensitive module names, dependencies, and conflicts when more than one
public package version is available.

When a package exposes a direct dependency as part of its public build or
runtime interface, configure its module to load the exact compatible dependency
module. Do not automatically load private transitive dependencies. Apply a
package-family conflict so a user cannot replace that dependency with another
published version in the same session. NetCDF-C and HDF5 are the minimum
acceptance case when both are in the release.

Publication passes only when the validated and published hashes match, the
required clean-session runtime and module checks pass, users have read and
execute access, consumers outside the approved package-manager group have no
write access, a second package manager in the group can perform a controlled
write test, and the release authority has recorded approval.

## 11. User access

Publish package modules under the application's established module root. The
normal module root should already be on users' `MODULEPATH`. A user normally
loads the package directly:

```bash
module load <package>/<version>
```

Use `module use` only for a private, test, or newly introduced module root.
Document that path with the release.

Verify that users can traverse the module tree, views, external runtime paths,
and package prefixes from login and compute nodes. Users outside the approved
package-manager group must not have write access to an accepted release.
Authorized package-manager writes remain subject to the release procedure; use
a new release for unrecorded package or configuration changes.

## 12. Changes, security events, and platform updates

A change to a root spec, version, variant, recipe, patch, package-repository
revision or order, compiler, MPI, GPU provider, catalog scope, Spack version,
external-package identity, or lockfile requires a new release record. Rebuild
and retest the affected dependency closure. Reuse unchanged concrete packages
only when their hashes are unchanged.

For a security advisory:

1. record the advisory and affected versions;
2. inspect lockfiles, package inventories, SBOMs, and the separate external
   inventory;
3. select an approved fix or mitigation;
4. rebuild and retest affected packages; and
5. withdraw or replace exposed modules according to local policy.

Spack SBOMs provide package and dependency inventory. They do not perform CVE
matching. Use the organization's approved vulnerability source or scanner.

For an operating-system or platform-runtime change, compare the previous and
current compiler, MPI, fabric, launcher, GPU, and external-package identities.
Revalidate when identities and ABIs remain unchanged. Rebuild when a required
provider, prefix, ABI, or supported pairing changes. Hold publication when the
compatibility result is unknown.

## 13. Retention, recovery, and rollback

Set and record the application's retention and user-notification periods.
Keep at least the current accepted release and one working previous release
when storage permits it. Do not remove a cache object while a retained lockfile
refers to its hash.

Resume an interrupted release only when its inputs and hashes are unchanged and
the failure was operational. Create a new release when a build-defining input
or hash changes.

Rollback changes the supported module default or release pointer to a previous
accepted release. It does not modify either release.

## 14. Required release record

Retain:

- system, resolved public catalog release path, and catalog approval record;
- environment source, selected scope paths, and effective scope listing;
- exact Spack runtime and every package-repository source, commit, and search
  order;
- deployment record and the install, source-cache, miscellaneous-cache,
  build-cache, view, module, and build-stage locations;
- approved `spack.lock` and concrete hashes;
- source-cache inventory, recipe-delta review, build-cache signing identity,
  and approved scan results;
- build, runtime, view, module, and permission test results;
- package inventory, SBOM locations, and external inventory;
- change or security assessment when applicable;
- release owner, reviewer, approval, and date; and
- user instructions and support contact.

## Appendix A. Terms

**Static platform catalog**
: Versioned, include-ready Spack configuration for one system.

**Scope**
: A directory containing valid Spack configuration YAML selected through an
  environment's `include::` list.

**Environment**
: A `spack.yaml`, its selected configuration, and the concrete package graph
  recorded in `spack.lock`.

**Toolchain**
: An explicit compiler or a supported compiler and MPI pairing, with a compatible
  GPU runtime when required.

**Lockfile**
: The exact package graph generated by Spack in `spack.lock`.

**Build cache**
: A repository of concrete Spack binaries and metadata.

**View**
: A combined filesystem presentation of selected installed packages.

**Module**
: A user-facing environment file loaded through the site module command.

**Published release**
: An accepted installation, views, modules, and release record exposed to
  users.
