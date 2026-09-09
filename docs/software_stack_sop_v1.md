# Spack Build and Publication Procedural SOP

| Document control | Value |
|---|---|
| Status | Working draft |
| Review revision | 2026-09-09 |
| Intended operator | Package manager familiar with Spack concepts but not site-specific commands |
| Procedure scope | Standard procedures for runtime verification, environment definition, review, mirrors and transfer, build, validation, publication, and retention |
| Command baseline | Spack 1.2.2; revalidate commands before adopting another version |

## 1. Purpose

This SOP defines the standard process for a package manager to build and
publish software with Spack on a supported system. The package manager supplies
the package intent. The site-supplied static platform catalog supplies reviewed
compiler, MPI, target, and external-package configuration.

This document provides the complete common procedure for sustained operation.
The operating record in Section 3 supplies the actual system paths, approved
configuration, toolchain names, Unix groups, scheduler details, security
requirements, acceptance criteria, retention periods, and support contacts.
Team-specific policy may supplement those values and requirements. The
procedure uses native Spack configuration and commands and does not depend on
a particular workspace preparation or orchestration tool.

The required sequence is:

```text
select reviewed platform configuration
  -> define the Spack environment
  -> concretize and review the lockfile
  -> admit sources and prepare approved mirrors
  -> transfer and verify the bundle when the destination cannot obtain all required inputs directly
  -> build and test on the target system
  -> obtain independent review and publish the approved artifacts
  -> retain the source, lockfile, and validation record
```

Every environment must use an explicit supported toolchain. A successful build
is not sufficient for publication. Runtime and module tests must also pass.

### 1.1 Procedure use

Complete the applicable sections in order, following the producer/destination
branch order in Section 9.2.1 for transfers. Each section defines a control
point. Do not continue past a failed control point. A skipped branch must be
recorded as not applicable with a reason; it is not a passed test.

1. Complete the operating record in Section 3.
2. Start the approved Spack runtime and complete preflight.
3. Select one released catalog and its documented scopes.
4. Define and review the environment source.
5. Concretize and review `spack.lock`.
6. Create source mirrors; use the transfer branch when needed.
7. Build or install the candidate and test on the destination node types.
8. Obtain the second-person review and publish only accepted concrete hashes.
9. Retain the source, lockfile, evidence, and approval record.

Command examples use angle-bracket placeholders for site-supplied values. The
operator must replace every placeholder before running a command. Shell
variables shown in the operating record may be used to avoid repeating paths.
Retain the resolved values in the operating record; session variables alone
are not a durable deployment record. Publication and transfer examples assume a
supported Linux shell and the site's approved storage and transfer mechanism.

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
The catalog includes valid Spack configuration files and a readable inventory
of their paths, supported combinations, source identities, and approval. The
package manager selects a supported set of scopes from that inventory and
includes them in an owned Spack environment. Section 6.1 defines the required
catalog contents; no particular catalog-generation tool or metadata schema is
required.

## 2. Responsibilities

| Role | Responsibility |
|---|---|
| Package manager | Select packages and catalog scopes, define the environment, build, test, and prepare the release record. |
| Technical reviewer | Independently review the candidate inputs, change assessment, lockfile, test and scan results, module behavior, and publication evidence. |
| Release authority | Approve publication under the application team's normal process. |
| Platform or transfer owner | Provide destination compatibility evidence, enforced network restrictions, approved transfer handling, and system-owned externals. |
| Security reviewer or responsible security authority | Review escalated security questions and advise on changes outside the agreed operating bounds. Decisions on exceptions follow the authority assigned by the local process. |

Use two distinct people for each release: one builds and prepares the evidence;
the other reviews and records the disposition before publication. The reviewer
may also be the release authority when delegated by the team's policy. Roles
may alternate across releases, but a builder does not approve their own work.
If the reviewer is unavailable, hold publication and use a documented alternate
reviewer. This does not require two people to repeat every build command.

Routine releases within the recorded operating bounds use the team's review
and release process. Obtain security review or a decision through the local
process for the escalation triggers in Section 12. A module in a centrally managed
namespace also requires the namespace owner's approval.

## 3. Required inputs

Record these inputs before concretization:

- target system and node types used for the build and runtime tests;
- approved static platform catalog root, release, inventory, approval record,
  and authorized audience;
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
| Catalog inventory and usage record | `CATALOG_RECORD` | Absolute path to the record within that release defining its contents, supported selections, and approval; Section 6.1 |
| Environment directory | `ENVIRONMENT_ROOT` | Absolute path containing `spack.yaml` |
| Approved Spack checkout | `SPACK_ROOT` | Absolute path to the pinned checkout |
| Spack version | `SPACK_VERSION` | Approved version and commit |
| Package repository | Release record | Approved `spack-packages` or site-repository source and commit |
| Per-user Spack state | `SPACK_USER_CACHE_PATH` | Builder-private absolute path |
| Bootstrap configuration | `BOOTSTRAP_CONFIG_DIR` | Absolute approved scope outside the Spack checkout; Section 4.5 |
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
| Connectivity and transfer | Release record | Connected, restricted-internet, or disconnected destination; approved intake node and transfer method when applicable |
| Mirror and bundle identity | Release record | Source-mirror path, signed binary-cache URL if used, archive digest, and origin/destination acceptance evidence |
| Security operating bounds | Operating record | Review triggers, approved scanning method, network policy, exception authority, and transfer authorization reference |
| Acceptance and support | Operating record | Required checks and tolerances, support contacts, retention and notification periods |

Start the approved Spack session after filling the record:

```bash
export STACK_SYSTEM="<system>"
export STACK_RELEASE="<application-release>"
export CATALOG_RELEASE_ROOT="<absolute-catalog-release-root>"
export CATALOG_RECORD="<absolute-catalog-inventory-and-usage-record>"
export ENVIRONMENT_ROOT="<absolute-environment-directory>"
export SPACK_ROOT="<absolute-approved-spack-root>"
export SPACK_VERSION="1.2.2"
export SPACK_TAG="v1.2.2"
export SPACK_COMMIT="<approved-full-spack-commit>"
export SPACK_STAGE_ROOT="<absolute-build-stage>"
export BOOTSTRAP_CONFIG_DIR="<absolute-approved-bootstrap-config-directory>"

export SPACK_DISABLE_LOCAL_CONFIG=true
export SPACK_USER_CACHE_PATH="<absolute-per-user-cache-root>/$USER/spack/$SPACK_VERSION"
export PYTHONDONTWRITEBYTECODE=1

test -f "$SPACK_ROOT/share/spack/setup-env.sh"
test -r "$CATALOG_RECORD"
source "$SPACK_ROOT/share/spack/setup-env.sh"
spack --version
```

Record the output of `spack --version` and the checkout commit. Stop if they do
not match the approved Spack identity.
Prepare the prerequisite configuration in Section 4.5 before any solve or
operation that may bootstrap a tool. The command examples carry that scope
explicitly so its source/trust policy persists across the workflow.

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

Keep verification keyrings and any authorized signing keyring in private
per-user or site-approved locations outside the Spack tool root and package
install tree. Private release-signing keys do not travel in a workspace or
transfer bundle; their use follows Section 10.1.

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
directories. The operator or approved build process must normalize owner-created
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
scope named by the environment's `spack.include` list. Apply the reviewed
deployment access policy consistently to every environment that writes to the
same install tree, and retain the policy file with the release.

For the approved Spack runtime, verify the merged configuration before
installation:

```bash
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config get packages
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
| Observed compiler, MPI, GPU, operating-system, and external-package facts | Reviewed platform evidence retained with the static catalog | Selected `packages.yaml`, compiler, target, and provider scopes |
| Package names, versions, variants, dependency constraints, and compiler/provider selection | Package-manager-owned `spack.yaml` | `spack.specs` and explicit compiler or toolchain constraints |
| Install tree, build stage, source and miscellaneous caches, view and module roots, build-cache destinations, and access policy | Controlled deployment record with the actual values from Section 3 | `config.yaml`, `packages.yaml`, `modules.yaml`, mirror configuration, and view paths |
| Site-wide provider and selection defaults | Reviewed defaults and catalog policy | Included configuration scopes |

Do not use an operator-local shell-variable bundle as the release contract.
Shell variables may shorten commands during one session, but the retained
environment source, deployment record, lockfile, and release record must
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
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config get config
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config get packages
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config get mirrors
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config get modules
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config scopes -vp
```

### 4.3 Supply-chain security boundary

Treat the Spack runtime, package repositories, package recipes, patches,
fetched sources, external packages, and binary caches as separate inputs to
the release. A checksum proves that fetched bytes match the checksum approved
by the recipe. It does not prove that the recipe, upstream source, or dependency
is safe. A lockfile fixes the selected concrete graph; it does not replace
review of a changed recipe repository or vulnerability assessment.

Apply the following gates using the later procedures:

| Gate | Required result |
|---|---|
| Admit inputs, Section 8.1 | Pinned tool and repository identities, complete inventory, risk-based review and scan dispositions |
| Acquire and transfer, Sections 9.1–9.2 | Approved source and binary mirrors, complete bundle when required, verified origin and destination bytes |
| Build and validate, Section 9.3 | Nonprivileged controlled build, approved network restriction, target-system tests and retained evidence |
| Review and release, Sections 10.1–10.4 | Independent review, approved signing identity, exact accepted hashes, controlled publication and inventories |
| Maintain, Sections 12–14 | Advisory handling, recorded exceptions, retention, withdrawal and rollback |

Shared working state remains writable by the recorded build group while a
candidate is assembled. An admitted baseline or accepted release is version
frozen by the release process: retain its digest and approval evidence, limit
writes through the site's storage controls, and verify the digests before use
or handoff. Group ownership alone does not make content immutable. Changed
admitted bytes return to review and receive a new recorded identity.

The operating record identifies approved scanners, advisory sources, network
controls, hardening requirements, and exception authority. Retain the actual
result and applicable acceptance criteria; a planned control is not evidence
that it ran. An unresolved requirement follows the hold and escalation process
in Section 12.

### 4.4 Verify the pinned runtime and package repositories

Use either the approved shared checkout or an identity-equivalent builder-local
checkout. The path may differ, but its version, tag, commit, and clean state may
not. Run after the session setup in Section 3.1:

```bash
SPACK_VERSION_OUTPUT="$(spack -C "$BOOTSTRAP_CONFIG_DIR" --version)"
test "${SPACK_VERSION_OUTPUT%% *}" = "$SPACK_VERSION"
test "$(git -C "$SPACK_ROOT" rev-parse HEAD)" = "$SPACK_COMMIT"
test "$(git -C "$SPACK_ROOT" rev-parse "${SPACK_TAG}^{commit}")" = "$SPACK_COMMIT"
test -z "$(git -C "$SPACK_ROOT" status --porcelain)"
spack -C "$BOOTSTRAP_CONFIG_DIR" config scopes -vp
```

For an approved runtime supplied as an archive without Git metadata, verify its
digest against the retained release identity instead. Do not pull, switch
branches, edit checkout-local configuration, or replace the approved tool
directory during a release. Provision a new version in a sibling directory.

Admit repository provenance and assess new/changed executable recipe inputs
using Section 8.1 before the first solve imports those recipes. After the solve,
complete that assessment against the resolved dependency closure. Inspect every
effective package repository after the environment is prepared:

```bash
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config get repos
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" repo list
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config scopes -vp
```

Compare each repository's source, commit or approved archive digest, namespace,
and effective search order with the release record. Include overlays, helper
code and patches that recipes import. Verify the corresponding trees are clean
or match the approved archive digests; an unrecorded overlay is a failed gate.
`SPACK_DISABLE_LOCAL_CONFIG` disables user and system configuration in the
command baseline. Use explicit `include::` to select the environment's intended
configuration and inspect every effective scope, repository order and security
setting, including approved command-line overrides. Neither this variable nor
an include list alone proves the complete configuration is approved.

### 4.5 Prepare admitted bootstrap and runtime prerequisites

Before concretization, the intake or destination system needs the approved
Python, solver and other runtime tools. Use pre-provisioned admitted tools, or
complete a bootstrap-only acquisition and, where needed, the authorized
transfer steps in Section 9.2 before the first solve. This prerequisite bundle
does not require an application lockfile. A receiver installing an already
reviewed lockfile does not need to reconcretize it.

Keep the approved bootstrap configuration in `$BOOTSTRAP_CONFIG_DIR` outside
the pinned checkout, and keep the active builder's mutable bootstrap root
private. For pre-provisioned tools, its `bootstrap.yaml` is:

```yaml
bootstrap::
  enable: false
  root: <absolute-private-builder-bootstrap-root>
  sources: []
  trusted: {}
```

If an admitted local bootstrap mirror is needed, use this alternative after
its metadata and artifacts have passed the acquisition/transfer gate:

```yaml
bootstrap::
  enable: true
  root: <absolute-private-builder-bootstrap-root>
  sources:
    - name: local-binaries
      metadata: <absolute-admitted-bootstrap-root>/metadata/binaries
    - name: local-sources
      metadata: <absolute-admitted-bootstrap-root>/metadata/sources
  trusted:
    local-binaries: true
    local-sources: true
```

The `bootstrap::` override replaces the public default sources and trust list.
List only the admitted metadata actually supplied; omit the binary source if
its runtime/architecture compatibility has not been accepted. Resolve all
paths in the retained local configuration. Trusting bootstrap metadata is
separate from trusting a signed release package.

```bash
spack -C "$BOOTSTRAP_CONFIG_DIR" bootstrap list
spack -C "$BOOTSTRAP_CONFIG_DIR" bootstrap status
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config get bootstrap
```

Require successful prerequisite status before the first solve. Run the last
command after Section 7 has prepared the environment and before concretization.
Inspect effective bootstrap configuration with the environment active; retain
the same `-C` scope on later commands. Source acquisition, bootstrap and build
network restrictions are enforced outside Spack. See the official
[bootstrap configuration](https://github.com/spack/spack/blob/v1.2.2/etc/spack/defaults/bootstrap.yaml)
and [read-only command-line scope](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/main.py#L460-L468).

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
spack -C "$BOOTSTRAP_CONFIG_DIR" config scopes -vp
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config scopes -vp
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
test -d "$CATALOG_RELEASE_ROOT"
test -r "$CATALOG_RECORD"
find "$CATALOG_RELEASE_ROOT" -type f -print | sort
```

Compare the files and their digests with the approved catalog inventory. Read
its supported compiler, MPI, GPU, target, module, prefix, and external-package
selections and compare them with the operating record. Verify every selected
scope path exists. Stop if a required scope is absent or the catalog records an
unresolved provider dependency.

Preflight passes only when the recorded paths and node types are usable, the
approved Spack identity matches, the catalog is readable, and the global and
environment scope listings contain no unexpected configuration.

## 6. Select platform configuration

### 6.1 Prepare and review a catalog when acting as catalog owner

Catalog consumers proceed to Section 6.2. The designated catalog owner
assembles a versioned directory containing include-ready native Spack
configuration, its supporting platform evidence, and a readable catalog record.
Manual preparation and approved automation must meet the same requirements:

1. Retain observed platform facts and their provenance: system and node types;
   compiler versions and identities; available MPI, fabric/launcher and GPU
   providers; CPU targets; and system-owned external versions, prefixes and
   required modules. Record how and when the facts were verified.
2. Prepare valid Spack configuration files in configuration-scope directories.
   Each scope must be usable from a native Spack environment. Record exact
   relative paths, file inventories and digests; check any symbolic links and
   record their targets. File layout is a site choice, not a tool contract.
3. Include a readable catalog record that identifies the system, catalog
   release, exact Spack baseline, source identities, preparation date, scope
   paths and contents, and supported compiler/provider/target combinations.
   Include instructions for selecting scopes, their required order, any named
   toolchains and provider constraints, and the platform evidence supporting
   those choices. Record unsupported combinations and unresolved limitations.
   The record may be plain text, Markdown, or a documented structured format.
4. Set `CATALOG_RELEASE_ROOT` and `CATALOG_RECORD` in the operating record.
   Verify the record resides in that release. Inspect every selected scope
   through native Spack configuration commands in Sections 4.2 and 7.5, using
   a representative environment. Compare effective values with the platform
   evidence; successful parsing alone does not establish compatibility.
5. Record independent review, reviewer, disposition, date, and exact candidate
   identity. Every claimed compiler/provider pairing and node type must have
   supporting evidence; hold unsupported or unresolved selections.
6. Retain the versioned candidate and its evidence. Publish it through Section
   10.2 after applicable acceptance gates. Keep the complete reviewed copy when
   publication uses a separate directory.

The catalog record and its inventory are maintained independently of the
application package release. A catalog does not contain application package
selection or silently assign install trees, cache locations, views, module
roots, or access permissions; those are retained deployment choices.

### 6.2 Select released scopes

Read the catalog inventory and usage record and select the exact scope paths
it lists. A normal environment includes:

1. common site configuration;
2. one compiler scope;
3. one target or platform scope;
4. one matching MPI scope for MPI builds; and
5. one compatible GPU scope for GPU builds.

Use a version-frozen catalog release path in a reproducible environment. A site may
publish a `current` pointer for discovery, but the environment source and
release record must identify the resolved release directory. The published
catalog must be readable and traversable by its approved consumer audience.
Consumers outside the approved catalog-manager group must not have write
access. The approved group retains management access, but no operator edits a
released version in place. Correct the owning inputs, prepare and review a new
catalog release, publish a new version with fresh approval metadata
and checksums, and move the discovery pointer only after acceptance. Retain or
retire the superseded version through the recorded release policy.

Use `include::` to replace inherited include-list entries with the reviewed
list. This does not remove every other configuration scope; inspect effective
values and scope precedence as required in Section 4.4. Use absolute paths to
a version-frozen catalog release in a published environment. The directory
names below illustrate one valid layout; substitute the actual paths listed
in the selected catalog record:

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

Keep the catalog and environment tree together when a controlled workspace uses
relative includes. Do not copy a single `spack.yaml` without the configuration
directories it references.

Select only documented compiler and MPI pairings. Do not construct a pairing from
module names or installed directories without catalog support.

Record the exact selected scope paths in the release worksheet. Catalog
selection passes when every selected path is present in the approved catalog
inventory and the environment scope listing resolves those paths without an
unapproved policy override.

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
placeholder with values from the operating record and catalog inventory:

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
deployment record described in Section 4.2. A minimum native Spack environment
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

### 7.5 Inspect the complete prepared workspace

Verify the complete environment and configuration before concretization,
whether the package manager prepared the files directly or received them from
another authorized operator. A workspace contains one or more `spack.yaml`
files, any existing reviewed `spack.lock` files, all referenced configuration
files, and accessible pinned package repositories and overlays. Its retained
operating record identifies the system, release, approved catalog, package
intent, deployment choices, file paths and digests, repository identities, and
operator responsibilities. No special workspace directory layout or metadata
filename is required.

For each environment identified in that record:

```bash
test -r "$ENVIRONMENT_ROOT/spack.yaml"
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config scopes -vp
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config get config
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config get packages
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config get mirrors
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config get modules
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config get repos
```

Every relative `include::` path must resolve inside the retained workspace or
its associated catalog tree, and the complete referenced tree must accompany
a transfer. Record and verify external absolute paths on the intended system.
A lone copied `spack.yaml` is insufficient when it references other files.
Systems unable to reach required configuration or repositories need reviewed
local copies; resolve remote includes into reviewed local inputs before
transfer.

Compare merged deployment paths, access, compilers, targets, providers and
module policy with the operating record. Verify each file's recorded identity,
repeat inspections using the receiving builder's runtime, and confirm shared
access before transferring responsibility. Correct the owning input and
prepare a new candidate when configuration must change. Preserve existing
lockfiles, build output and evidence rather than overwriting their workspace.

## 8. Concretize and review

Concretize and retain the generated lockfile:

```bash
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" concretize --fresh
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" find -c -d -l -v
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" find -c -d -e -l -v
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
approved intent, all providers and externals come from approved scopes, and the
complete dependency closure is covered by the admission assessment below.
Save the two `find` listings with the release evidence. A recorded automated
assessment with risk-based human review can cover unchanged transitive inputs;
individual manual approval of each dependency is not required by this SOP.

<a id="procedure-review"></a>

### 8.1 Assess package changes and record the two-person review

1. **Establish the baseline.** Inventory the complete locked dependency
   closure, including repositories and imported recipe helpers, patches,
   source resources, bootstrap/build tools and system externals. On the first
   release, record repository provenance, pinned identities, available upstream
   assurance, scan coverage and risk criteria. There is no previous baseline
   to inherit, but this still does not require reading every package line by
   line.
2. **Assess later changes.** Compare the candidate against the last accepted
   lockfiles, recipe-repository commits and external inventory. Retain the
   added, removed and changed packages and inputs. Record the approved
   repository baseline supporting unchanged components. Include common helper
   changes that affect reachable recipes, not only changed package files.
3. **Focus manual review.** Inspect team-authored or locally modified recipes
   and patches, changed download locations or checksum/commit rules,
   custom hooks and undeclared build-time downloads, security-sensitive
   components, new providers, and material scanner findings. Select newly
   introduced third-party recipes for manual review by provenance and risk;
   do not turn repository updates into a blanket manual review of thousands of
   unchanged packages. Record why deeper review was or was not needed for the
   assessed change groups.
4. **Apply the configured checks.** Run the site's approved source, recipe,
   dependency and binary checks at their appropriate intake/build stages.
   Record tools, rule or advisory versions, time, scope, result, and any
   coverage gap. Spack checksums, `spack audit` and SBOM generation are not a
   substitute for vulnerability matching. Disposition findings or route them
   to Section 12 before proceeding past the affected gate.
5. **Have the other person review.** The builder supplies the assessment and
   locked candidate. The reviewer checks the selected baseline and deltas,
   manual-review triggers, graph/provider decisions and dispositions. After
   Section 9, the same review record covers build/test/scan evidence, expected
   release hashes and publication readiness. A review may be staged, but its
   final approval must bind the exact candidate and evidence digests.
6. **Record and enforce the decision.** Retain builder and reviewer names,
   dates, candidate/lockfile identities, scope checked, findings, disposition
   (`accepted`, `changes required`, or `held`) and release authority. Evidence
   changed after review returns to the reviewer. Signing and publication require
   the completed independent review.

This is one auditable release assessment covering the complete inventory, with
deeper manual inspection driven by change and risk. The team's approved policy
may require additional review for named components or system conditions.

## 9. Build and validate

<a id="procedure-source-mirrors"></a>

### 9.1 Create and verify source mirrors at controlled intake

Use an approved intake system with the necessary network access to acquire the
reviewed inputs. This serves systems that cannot directly retrieve every
required source archive or supporting input, whether external access is partly
restricted or absent. Prepare the destination's reviewed platform configuration
and lockfiles before acquisition; the intake host does not silently substitute its
own compiler, target or external package choices.

For login and compute nodes sharing the same source cache, fetch the complete
locked dependency closure:

```bash
test -f "$ENVIRONMENT_ROOT/spack.lock"
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" fetch -D
```

The later install may run on a different node when it uses the same workspace,
source cache, install tree, Spack version, and lockfile. A populated local
source cache alone is not the transfer artifact for another network.

Create a dedicated transportable source mirror for every locked environment
that the destination will use:

```bash
export SOURCE_MIRROR_ROOT="<absolute-release-source-mirror>"
test -f "$ENVIRONMENT_ROOT/spack.lock"
mkdir -p "$SOURCE_MIRROR_ROOT"
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" find -c -d -l -v
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" mirror create \
  --all --directory "$SOURCE_MIRROR_ROOT"
```

In Spack 1.2.2, `--all` with an active concrete environment selects that
environment's concrete roots and dependencies; it does not mirror every recipe
in the repository. Repeat for all release environments into the same reviewed
release mirror. Inspect the mirror command's missing/failed-fetch report and
record completeness against all retained lockfiles. Externals are not fetched.
([Spack mirror procedure](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/mirrors.rst#L142-L195))

Retain source archives, package resources and patches with their acquisition
locations, recipe identities and checksums. Use full immutable commits for VCS
inputs. For a VCS source converted to a mirror archive, independently record
how the archive was produced from the reviewed commit and retain its digest:
Spack 1.2.2 cannot apply an ordinary recipe archive checksum to that generated
tar file. Stop for unrecorded downloads or checksum failures; do not suppress
verification to complete the mirror.
([Spack VCS mirror verification](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/stage.py#L669-L685))

Run the approved intake checks and record their disposition before admitting
the mirror. Register an admitted source mirror in the owned environment:

```bash
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" mirror add \
  --scope "env:$ENVIRONMENT_ROOT" --type source \
  admitted-sources "$SOURCE_MIRROR_ROOT"
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" mirror list
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config get mirrors
```

This changes the environment's mirror configuration; retain and review that
configuration with the candidate before use. If the name is already configured,
verify its value and use the reviewed configuration update process instead of
adding a duplicate. A source mirror is not a binary build cache. Registration
also does not prevent fallback to original URLs: enforce the required network
restriction outside Spack and treat an attempted fallback as a failed gate.

<a id="procedure-disconnected-transfer"></a>

### 9.2 Transfer to a system with limited or no external network access

Use this sequence when the destination cannot directly obtain all required
source tarballs or other build inputs. It applies even when the system can
reach some Internet or internal-network resources, and also covers fully
air-gapped systems. Where a classified or other controlled boundary is involved,
the site's authorized transfer process supplies handling, scanning, release and
import permission. This SOP does not authorize a transfer or select removable
media or a cross-domain mechanism. Record the applicable authorization and
destination owner before assembling the bundle.

#### 9.2.1 Select the destination execution mode

| Mode | Required destination evidence | Next action |
|---|---|---|
| Build from admitted sources | Destination-specific catalog, locked graph, approved compilers/providers/externals and complete sources/tools | Build a restricted destination candidate from the local source mirror, then validate, review, sign and publish through the normal gates |
| Install approved signed binaries | Approved release hashes and keys, compatible target/OS/ABI/providers/externals, supported relocation paths and complete signed cache | Install cache-only into a controlled destination candidate store, run local acceptance, then approve destination publication |

For source delivery, complete source intake in Section 9.1, transfer and receive
under Sections 9.2.2–9.2.3, then finish destination validation in Section 9.3
and publication in Section 10. For binary delivery, the producer first completes
Section 9.3 build/validation, independent review and Section 10.1 signing. An
existing accepted cache may supply that producer record. Only then assemble and
receive the signed-cache bundle under Sections 9.2.2–9.2.3. The destination
verifies and retains the producer's signatures and signing record, completes
local acceptance, and follows the remaining applicable Section 10 publication
gates. Record separate producer and destination dispositions.

Sister systems are a useful starting point for comparison, not evidence of
binary compatibility. Compare CPU target/features, OS and libc/runtime ABI,
compiler runtime, MPI/fabric/launcher and GPU identities, external versions and
prefixes, and install-prefix relocation limits. Have the platform owner record
the result. A compatible name or identical Spack hash alone is insufficient.
An incompatible or uncertain binary goes to the source-build branch, with a
new destination candidate and any revised lockfile reviewed before transfer.
Neither a rebuild nor a transferred binary bypasses destination acceptance.

#### 9.2.2 Assemble and verify the complete bundle at origin

1. Populate a dedicated release bundle for the selected execution mode: the
   admitted source mirror for destination source builds, the approved signed
   build cache for binary-only installs, or both when the delivery deliberately
   supports both modes. Section 10.1 creates the signed cache. Preserve its
   entire mirror root, index/manifests, signatures and content blobs. Do not
   copy only package archives or only the index.
2. Include the complete destination workspace, catalog snapshot and relative
   configuration tree; all `spack.yaml` and unedited `spack.lock` files;
   pinned Spack runtime and package repositories/overlays; patches/resources;
   release records; and approval, scan, inventory and test evidence.
3. Include or separately pre-provision the exact admitted Python, bootstrap
   prerequisites, compilers, build tools and other runtime requirements.
   Package mirrors exclude system externals; retain their separate inventory
   and verify destination availability. A source mirror is not a complete
   Spack/bootstrap installation.
4. When bootstrap acquisition is needed, prepare a dedicated mirror on a
   compatible connected system:

```bash
export BOOTSTRAP_ROOT="<absolute-release-bootstrap-bundle>"
spack -C "$BOOTSTRAP_CONFIG_DIR" bootstrap mirror --binary-packages "$BOOTSTRAP_ROOT"
```

Retain the generated source/binary metadata, bootstrap cache and emitted setup
instructions. Review and admit their provenance/digests and destination
architecture/runtime compatibility separately from the ordinary signed package
cache. Bootstrap metadata trust is a separate decision; it does not inherit
approval from a normal build-cache signature. Destination bootstrap
configuration follows Section 4.5; do not modify the pinned Spack checkout or rely
on an ambient user configuration disabled by this SOP.
([Spack bootstrap mirrors](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/bootstrapping.rst#L148-L173))

5. Retain a bundle manifest listing origin/destination, release IDs, workspace
   and lockfile identities, repository/runtime identities, source and binary
   inventories, source-archive digests, expected signing fingerprints, bootstrap
   inputs, external requirements, execution mode and transfer authorization.
   Keep private keys, credentials and another builder's mutable state out.
6. Check that relative includes and mirror symlinks remain inside the bundle,
   no required link refers to an origin-only absolute path, and the archive will
   extract without replacing unrelated destination files. Preserve the complete
   directory structure and links. Freeze the assembled input before packaging.
7. Create and verify a digest for the transfer archive. For example, after the
   site-approved assembly has populated a dedicated bundle directory:

```bash
export TRANSFER_BUNDLE_ROOT="<absolute-complete-transfer-bundle>"
export TRANSFER_OUTPUT_ROOT="<absolute-transfer-output-parent>"
(
  set -euo pipefail
  cd "$TRANSFER_OUTPUT_ROOT" || exit 1
  test ! -e release-bundle.tar
  tar -C "$TRANSFER_BUNDLE_ROOT" -cpf release-bundle.tar .
  sha256sum release-bundle.tar > release-bundle.tar.sha256
  sha256sum --check release-bundle.tar.sha256
)
```

Use a fresh output directory outside the bundle tree for each transfer. Bind
that digest and manifest to the reviewed transfer record through the site's
authenticated record or signature mechanism. A checksum file accompanying
arbitrary bytes alone does
not establish origin approval. The reviewer checks completeness, findings and
the exact bundle digest before the authorized transfer process begins.

#### 9.2.3 Verify, configure and accept at destination

1. Receive into the approved intake area. Complete local import checks and
   compare the archive digest to the independently authenticated origin record
   before extracting. Retain both origin and destination results:

```bash
export RECEIVED_ARCHIVE_ROOT="<absolute-received-archive-parent>"
export RECEIVE_ROOT="<absolute-new-destination-bundle-directory>"
(
  set -euo pipefail
  cd "$RECEIVED_ARCHIVE_ROOT" || exit 1
  sha256sum --check release-bundle.tar.sha256
  test ! -e "$RECEIVE_ROOT"
  test ! -L "$RECEIVE_ROOT"
  mkdir -p "$RECEIVE_ROOT"
  tar -C "$RECEIVE_ROOT" -xpf "$RECEIVED_ARCHIVE_ROOT/release-bundle.tar"
)
```

2. Check the extracted bundle against its manifest and provision the approved
   destination-local bootstrap configuration from Section 4.5. Repeat runtime,
   repository, configuration, local external and scope checks from Sections
   4–7. Keep the complete workspace and relative `include::` paths intact.
   Configure approved local repository and deployment paths before use and
   retain the reviewed destination configuration delta. If the dependency or
   platform identity must change, stop and create a new candidate; do not
   silently reconcretize during import.
3. Configure only admitted destination-local mirrors in the effective
   environment. A reviewed inline replacement has this shape:

```yaml
spack:
  mirrors::
    admitted-sources:
      url: file://<absolute-destination-source-mirror>
      source: true
      binary: false
    approved-binaries:
      url: file://<absolute-destination-binary-mirror>
      source: false
      binary: true
      signed: true
```

Omit either mirror entry when that mirror is not part of the admitted delivery.
Retain the rest of the reviewed environment unchanged; this is a configuration
fragment, not a new
environment source. Inspect local repositories and bootstrap configuration,
and verify the effective settings:

```bash
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config get mirrors
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config scopes -vp
```

Import only a public release key whose full fingerprint matches the
independently approved record, using Section 10.1. A key found in the transfer
bundle or mirror does not establish trust by its presence.

4. Have the platform owner enforce and record denial of outbound access to
   nonapproved networks for fetch, bootstrap, build and installation. Verify
   that restriction with the site's approved test. Mirrors alone do not disable
   Spack's origin fallback or downloads initiated by package build scripts.
   Missing sources, tools, cache objects or keys stop the run and return to
   controlled intake for a reviewed supplemental bundle; do not temporarily
   restore Internet access or bypass integrity/signature checks.
5. For the source-build mode, fetch from the local mirror into the approved
   destination source cache and install the existing concrete graph in the
   restricted candidate area:

```bash
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" fetch -D
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" install \
  --only-concrete --use-buildcache=never --fail-fast
```

`--use-buildcache=never` disables binary-cache use; it can still reuse existing
or upstream installations and declared externals. Use a clean or dedicated
controlled store with no unapproved upstream store and separately admitted
externals. Record and accept any intentionally reused installations. Record
which packages were actually rebuilt; claim source reconstruction only for
those outputs.

For the binary mode, verify mirror consistency and install the approved hashes
cache-only into the controlled destination candidate environment/store:

```bash
spack -C "$BOOTSTRAP_CONFIG_DIR" buildcache check-index --verify all <local-approved-binary-mirror>
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" install \
  --only-concrete --use-buildcache=only --fail-fast
```

The binary mode uses the same clean/controlled store, signature and external
admission requirements as Section 10.3. A cache miss or relocation failure is a
held candidate, not permission to build from source in that store.

6. Run Section 9.3 on destination login and compute nodes, including scheduler,
   MPI/fabric, GPU and module tests when applicable. Retain local SBOM and
   external evidence and obtain independent review. A destination source build
   produces a new candidate artifact even when concrete hashes match the
   origin; sign its accepted outputs through the authorized destination release
   process. Complete Section 10 before user exposure.

The transfer gate passes only when authenticated origin identity, received
digests, intake disposition, complete local inputs, enforced connectivity
bounds and destination compatibility are recorded. The release gate additionally
requires destination acceptance and review.

<a id="procedure-build-validation"></a>

### 9.3 Build and validate the candidate on the target system

Run as a nonprivileged build identity in the restricted candidate area. Record
the approved network restriction and enter the required compute allocation.
Section 9.1 must have completed controlled source intake. When inputs arrive
by transfer, Section 9.2 must also have passed transfer and configuration checks.

When several environments install in parallel, verify the complete lock set
first, give every process a distinct mutable user cache, never run the same
environment twice, and assign view/module refresh to that environment's one
owning process. After parallel work stops, run the shared-output permission gate
before transferring responsibility to another builder.

Install the reviewed concrete graph, then refresh the environment-owned
presentation. If Section 9.2 already installed the candidate, continue with
presentation and validation without repeating the install:

```bash
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" install --only-concrete --fail-fast
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" env view regenerate
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" module tcl refresh --delete-tree -y
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

Select numerical-correctness and representative performance checks according
to package purpose, platform, candidate changes, and risk. Record the cases,
tolerances, comparison baseline, and acceptance results. Evidence for an
unchanged package may be reused when the inputs, platform, and test assumptions
remain applicable. Record that basis and the reason for any check marked not
applicable; a required missing result holds the candidate.

Also retain the configured security-check results, approved compiler-hardening
settings and any scoped exceptions. Verify installed-file integrity and linkage
where the platform supports those checks. These checks do not replace the
organization's vulnerability scanner. Complete the required functional,
numerical and performance acceptance before approving a hardening change that
can affect scientific results or runtime behavior.

When the environment defines additional named module sets, refresh each
configured set separately. Substitute a set name from the reviewed
`modules.yaml`; do not create an additional namespace merely to run this
example:

```bash
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" module tcl -n <configured-module-set> refresh --delete-tree -y
```

Record `module avail`, `module show`, load, conflict and runtime results from
clean login and batch sessions. Compare selected prefixes and concrete hashes.
When two module names expose the same package, they must resolve to the same
accepted prefix and conflict as the team's presentation policy requires.
Check required direct-dependency loads and version conflicts; do not expose
every private transitive dependency as a user module.

After parallel work stops, verify the recorded group and modes on shared
outputs. A second package manager must be able to traverse/read the required
inputs and create, replace and remove a controlled test artifact in each
shared working root. Do not use package prefixes or database files as the test
artifact. Preserve private keyrings, bootstrap state and per-builder temporary
state. Retain the results with the reviewer handoff.

Record the result as `built`, `runtime-passed`, or `held`. Publish only a
`runtime-passed` environment.

Validation passes only when the required compile, runtime, scheduler, MPI,
GPU, view, module, clean-session, and permission tests have recorded successful
exit status. Mark the release `held` when a required resource was unavailable
or a required result was not obtained.

## 10. Publish

Use the application team's approved publication method. Preserve the reviewed
lockfile and concrete hashes. Final independent review of the exact candidate
and evidence must pass before signing or publication. Record whether the
accepted installation is published directly or installed from an approved
signed cache. Both methods complete the same acceptance, authenticated release
record, and access gates; Section 10.1 applies whenever a binary cache is used.

<a id="procedure-signing"></a>

### 10.1 Sign and populate the approved binary cache

Use the release identity and authorized key custodian named in the operating
record. Keep the private key in the restricted signing process. Obtain the
approved public key and full fingerprint through an authenticated record;
compare the key fingerprint before deliberately trusting it. Verification uses
a dedicated keyring containing approved public keys only. Keep its directory
private to the operator:

```bash
export SPACK_GNUPGHOME="<absolute-verification-only-spack-keyring>"
spack -C "$BOOTSTRAP_CONFIG_DIR" gpg trust <verified-release-public-key-file>
```

Do not infer trust from a key arriving with a mirror. Avoid
`spack buildcache keys --install --trust` unless every key in that controlled
mirror is explicitly approved. Retain old approved public keys while retained
releases require them; follow Section 12 for rotation, revocation or exposure.

Use a URL/filesystem build-cache backend supporting native Spack package
signing. In Spack 1.2.2, an OCI cache does not meet this native-signature
procedure. Configure the binary mirror separately from source mirrors:

```bash
export BINARY_MIRROR_ROOT="<approved-build-cache-path-or-url>"
export SIGNING_KEY_FINGERPRINT="<full-approved-signing-fingerprint>"
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" mirror add \
  --scope "env:$ENVIRONMENT_ROOT" --type binary --signed \
  approved-binaries "$BINARY_MIRROR_ROOT"
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" config get mirrors
```

Configure and review that endpoint before the candidate is frozen; if it
already exists, inspect its exact value instead of adding it again. The signer
checks that every package selected for the push belongs to the accepted
release set. Push by full concrete hash, repeating for the complete approved
non-external closure:

```bash
export SPACK_GNUPGHOME="<absolute-restricted-signing-keyring>"
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" buildcache push \
  --signed --key "$SIGNING_KEY_FINGERPRINT" --update-index --fail-fast \
  "$BINARY_MIRROR_ROOT" /<approved-full-concrete-hash>
spack -C "$BOOTSTRAP_CONFIG_DIR" buildcache update-index --keys "$BINARY_MIRROR_ROOT"
spack -C "$BOOTSTRAP_CONFIG_DIR" buildcache check-index --verify all "$BINARY_MIRROR_ROOT"
```

Run that signing block only in the authorized signing context with the
provisioned private key. End that context before build or publication work;
the verification-only keyring is used again by destination and publication
installation. The private key is not copied into that keyring.

No unsigned push or signature-verification bypass belongs in the normal path.
Retain signing identity, approved hashes, push results and cache-index digest.
Finalize the index before checksumming a transfer bundle. Preserve the entire
mirror when moving it: package manifests/signatures and content blobs must
travel together. `check-index` checks consistency; installation performs
package signature verification. The Spack 1.2.2 index itself is not signed, so
the separately authenticated release record must bind the permitted hash set
and transferred mirror digest. Compare that permitted set before installation.
([Spack signing and cache layout](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst#L598-L704))

<a id="procedure-catalog-publication"></a>

### 10.2 Publish the reviewed static catalog

This branch is for the catalog owner. The operating record sets its place in
the release sequence and its authorized audience; the catalog remains a
separate configuration product from package binaries.

1. Confirm Section 6.1 review of the catalog record, supporting platform
   evidence, scope files and usage instructions. Verify paths and instructions
   from the intended final location; no consumer path may depend on inaccessible
   restricted storage.
2. Reserve a new versioned destination and a staging directory in the same
   dedicated publication parent. Serialize publication through the site's
   approved ownership/locking method. Never overwrite an existing version.
3. Copy the complete reviewed bytes without regenerating them. Retain a
   publication record identifying the catalog release, source identities,
   candidate digest, reviewer, approval, date, intended audience and final
   destination. Use an auditable text or structured record; its format and
   filename are site choices. Keep its content and the released file inventory
   bound to the authenticated approval record.
4. Create `SHA256SUMS` over every released regular file, including the
   publication record and excluding `SHA256SUMS` itself. Confirm any links are
   reviewed and resolve within the released tree; record their targets in the
   publication inventory. Apply the approved group and public modes in this
   dedicated tree: directories `2775`, executables `0775`, ordinary files `0664`.

The following example uses a `SHA256SUMS` inventory produced by the system's
SHA-256 utility. The publication record is included in the staged tree at the
path selected by the operator; it is not a Spack configuration file. Prepare
that record and the required modes before running:

```bash
export CATALOG_STAGE="<absolute-new-catalog-staging-directory>"
export PUBLISHED_CATALOG="<absolute-new-versioned-published-catalog>"
export BUILD_GROUP="<approved-catalog-manager-group>"
export CATALOG_PUBLICATION_RECORD="<absolute-publication-record-within-staged-tree>"
(
  set -euo pipefail
  test -r "$CATALOG_PUBLICATION_RECORD"
  cd "$CATALOG_STAGE" || exit 1
  find . -type f ! -name SHA256SUMS -print0 \
    | sort -z | xargs -0 sha256sum > SHA256SUMS
  sha256sum --check SHA256SUMS
)
```

5. Recheck the staging tree, including the inventory file's ownership/mode.
   Expose the directory as one same-filesystem rename only after approval:

```bash
(
  set -euo pipefail
  test ! -e "$PUBLISHED_CATALOG"
  test ! -L "$PUBLISHED_CATALOG"
  mv -T -n "$CATALOG_STAGE" "$PUBLISHED_CATALOG"
  test ! -e "$CATALOG_STAGE"
  cd "$PUBLISHED_CATALOG" || exit 1
  sha256sum --check SHA256SUMS
)
test -z "$(find "$PUBLISHED_CATALOG" -type d ! -perm 2775 -print -quit)"
test -z "$(find "$PUBLISHED_CATALOG" -type f -perm /111 ! -perm 0775 -print -quit)"
test -z "$(find "$PUBLISHED_CATALOG" -type f ! -perm /111 ! -perm 0664 -print -quit)"
test -z "$(find "$PUBLISHED_CATALOG" -perm -0002 -print -quit)"
test -z "$(find "$PUBLISHED_CATALOG" ! -group "$BUILD_GROUP" -print -quit)"
```

6. Verify read/traverse and denied write using a consumer account outside the
   management group, and controlled management access using another group
   member. Retain checksum, mode, ownership and access results. Move an optional
   `current` discovery pointer only after acceptance; consumers pin the exact
   versioned path. Corrections create a new reviewed catalog release.

<a id="procedure-cache-publication"></a>

### 10.3 Install and accept the release from the cache only

When a build cache is used:

1. push only validated concrete packages;
2. create a separate publication workspace;
3. copy the approved lockfile;
4. install the locked packages from the approved cache;
5. stop on a cache miss rather than building unreviewed source in the
   publication workspace; and
6. compare the published hashes with the validated build hashes.

Prepare a separate matching publication workspace from the same reviewed
package/platform inputs, repositories and release identity, applying the
approved publication deployment record and access audience. Keep referenced
scopes intact. Do not copy a mutable working tree wholesale. Before install,
verify effective configuration, approved source and signed binary mirrors,
bootstrap policy, expected release hashes, and the world-read/group-write
package policy from Section 4.1.

Use a clean or dedicated controlled publication store with no unapproved
upstream store. Cache-only options do not retroactively verify packages already
installed in a store, and externals are not supplied by the binary cache.
Separately accept those external identities and retain their inventory. Run
publication installation with a verification-only keyring in a context without
access to the signing private key. Confirm the public key's full fingerprint
against the authenticated approved record before the trust command. After the validated hashes are
available in the approved cache:

```bash
export PUBLICATION_ENVIRONMENT_ROOT="<absolute-publication-environment>"
export SPACK_GNUPGHOME="<absolute-verification-only-spack-keyring>"

spack -C "$BOOTSTRAP_CONFIG_DIR" gpg trust <verified-release-public-key-file>
test -f "$PUBLICATION_ENVIRONMENT_ROOT/spack.yaml"
cp "$ENVIRONMENT_ROOT/spack.lock" "$PUBLICATION_ENVIRONMENT_ROOT/spack.lock"
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$PUBLICATION_ENVIRONMENT_ROOT" find -c -d -l -v
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$PUBLICATION_ENVIRONMENT_ROOT" install \
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
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" find -c -d --format '{hash}' | sort -u \
  > "$EVIDENCE_ROOT/validated-hashes.txt"
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$PUBLICATION_ENVIRONMENT_ROOT" find -c -d --format '{hash}' | sort -u \
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

Compare the concrete listings above to the authenticated approved release
inventory, and retain separate installed-package listings showing that every
required non-external hash is installed. Matching copied lockfiles alone does
not prove an installation completed. Run all applicable destination validation
and cross-user access checks from Section 9.3 before exposing module defaults.

### 10.4 Retain SBOMs and the separate external inventory

Spack 1.2.2 writes a per-installation SPDX 2.3 SBOM for a non-external package:

```text
<package-prefix>/.spack/sbom/spdx-2.3.json
```

Locate an accepted package and retain its producer SBOM with a checksum:

```bash
spack -C "$BOOTSTRAP_CONFIG_DIR" -e "$ENVIRONMENT_ROOT" location -i /<approved-full-concrete-hash>
sha256sum <approved-package-prefix>/.spack/sbom/spdx-2.3.json
```

Record package name/version, full hash, prefix, SBOM location and digest. Retain
the producer SBOM and approved scan result as release evidence separately from
the published prefix. Binary installation runs hooks and may regenerate local
SBOM metadata, so producer and consumer SBOM files need not have equal bytes
for the same concrete hash. Record the consumer copy separately and compare
component identity and dependency relationships against the approved release;
investigate substantive discrepancies. Inventory and assess system externals
separately because Spack does not generate their SBOMs. SBOM presence is an
inventory check, not a vulnerability assessment.
([Spack SBOM generation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/hooks/sbom_generate.py),
[binary installation hooks](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/binary_distribution.py#L2163-L2174))

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

Routine releases inside the team's agreed source, build, signing and transfer
bounds stay with the builder, reviewer and release authority. Obtain security
review or a decision through the local process at these points:

| Trigger | Action and retained decision |
|---|---|
| First use on a new authorization/network boundary, or material change to intake, transfer, egress, signing/trust or publication access | Obtain the platform/security owners' assessment and applicable approval before enabling that changed path |
| Exception to required integrity/signature checks, isolation, hardening or scan coverage; unresolved finding beyond the team's risk authority | Hold the affected gate; record scope, justification, compensating controls, owner, expiry and approving authority |
| Suspected compromise, unapproved artifact change, or exposed/revoked signing key | Follow the site's incident process, hold affected releases and coordinate withdrawal, key handling and recovery |
| Unclear applicability or a proposed control change with useful security input | Request a focused interpretation/recommendation and retain the resulting operating-boundary update |

Security review is not a routine per-package approval gate. The local process
identifies the responsible reviewer and any required approval authority. A
discussion does not itself approve an exception. Record the decision or keep
the affected release held.

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

- system, resolved catalog release path, and catalog approval record;
- environment source, selected scope paths, and effective scope listing;
- exact Spack runtime and every package-repository source, commit, and search
  order;
- deployment record and the install, source-cache, miscellaneous-cache,
  build-cache, view, module, and build-stage locations;
- approved `spack.lock` and concrete hashes;
- source/mirror inventory, baseline and recipe-delta assessment, manual-review
  selection, build-cache signing identity, and actual scan results/dispositions;
- prerequisite/bootstrap identity, approved source/trust configuration, enforced
  network-control evidence and configuration digests;
- when transferred: authorized route/reference, complete bundle manifest,
  authenticated origin digest, received digest and import results, destination
  configuration delta, compatibility assessment and source-build/binary mode;
- build, runtime, view, module, and permission test results;
- package inventory, SBOM locations, and external inventory;
- change or security assessment when applicable;
- builder, independent reviewer, release authority, review scope, candidate and
  evidence identities, disposition and dates; and
- user instructions and support contact.

## Appendix A. Terms

**Static platform catalog**
: Versioned, include-ready native Spack configuration for one system, with a
  readable inventory, supported selections, platform evidence, and approval
  record as defined in Section 6.1.

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

**Source mirror**
: A retained collection of source archives, resources, and patches from which
  Spack can fetch reviewed build inputs. A source mirror is distinct from both
  a source cache used during a build and a binary build cache.

**Build cache**
: A repository of concrete Spack binaries and metadata.

**Bootstrap prerequisites**
: Tools needed to run Spack or solve/install an environment, such as the
  approved Python and solver. Their source and trust configuration is admitted
  separately under Section 4.5.

**External package**
: A component supplied outside the managed Spack installation, with its
  version, prefix or modules, provider identity, and compatibility separately
  recorded and accepted.

**Release record**
: The retained inputs, evidence, exact accepted candidate identities, and
  authenticated review and publication decisions required by Section 14. It
  may be a set of controlled files or an auditable record system; no particular
  metadata schema is required.

**View**
: A combined filesystem presentation of selected installed packages.

**Module**
: A user-facing environment file loaded through the site module command.

**Published release**
: An accepted installation, views, modules, and release record exposed to
  users.
