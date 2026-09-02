# CSE Spack Build and Publication SOP

| Document control | Value |
|---|---|
| Status | Working draft |
| Intended operator | CSE package manager or build owner familiar with Spack concepts |
| Procedure scope | Catalog release, workspace generation, restricted build, validation, promotion, publication, and retention |

## 1. Purpose

This SOP defines the CSE process for building, validating, promoting, and
publishing the managed CSE software environment. It uses the same control
points as the package-manager SOP, with CSE-specific storage, ownership,
toolchain, signing, module, and retention policy.

The required sequence is:

```text
select reviewed platform configuration
  -> generate and review the CSE workspace
  -> concretize and review every environment
  -> build and test in the restricted CSE area
  -> sign and push approved binaries to the private build cache
  -> publish the reviewed static catalog for external package managers
  -> create the stack release from the approved lockfiles and cache only
  -> validate views, modules, permissions, and runtime behavior
  -> freeze and approve the release
```

The Initial Conversion Trials exercise this process. This SOP records the
durable CSE release contract in Spack and release-artifact terms. The system
handoff supplies actual deployment paths, provider selections, node types, and
approving roles. Internal preparation utilities, trial-only adapters, operator
shortcuts, provisioning, exceptional recovery, and system-specific failure
analysis remain in the runbook.

### 1.1 Procedure use

Complete the sections in order. Do not continue past a failed control point.
The supported command interface in this SOP is the Spack command line. CSE may
prepare catalogs and workspaces manually or with approved internal automation,
but that automation, its private variables, and its recovery shortcuts are not
part of this procedure or the release contract. Operators receive and verify
the resulting Spack configuration and release artifacts.

After Sections 3 through 7 are complete, the normal restricted-build sequence
for each generated environment is:

```bash
export WORKDIR="<absolute-builder-work-root>"
export BUILD_WORKSPACE="<absolute-restricted-workspace>"
export ENVIRONMENT_ROOT="<absolute-generated-environment-path>"
: "${WORKDIR:?WORKDIR must be set}"
: "${BUILD_WORKSPACE:?BUILD_WORKSPACE must be set}"
: "${ENVIRONMENT_ROOT:?ENVIRONMENT_ROOT must be set}"

spack -e "$ENVIRONMENT_ROOT" config scopes -vp
spack -e "$ENVIRONMENT_ROOT" concretize --fresh -j 1
spack -e "$ENVIRONMENT_ROOT" find -c -d -l -v
spack -e "$ENVIRONMENT_ROOT" fetch -D
# Enter the approved compute allocation before installation when required.
spack -e "$ENVIRONMENT_ROOT" install --fail-fast
spack -e "$ENVIRONMENT_ROOT" env view regenerate
spack -e "$ENVIRONMENT_ROOT" module tcl refresh --delete-tree -y
spack -e "$ENVIRONMENT_ROOT" find -c -d -l -v
```

Run only the view and module commands enabled by that environment. Repeat the
sequence in the generated environment order. Run installation from an
allocation that satisfies the deployment record's compute-node requirements.
The system handoff supplies the scheduler command used to obtain that
allocation.

### 1.2 Evidence format

Retain command output as text together with the reviewed profile, deployment,
defaults, stack intent, package sets, manifests, environment sources,
lockfiles, concrete-hash inventories, checksums, test programs, SBOMs, and
approvals. Record the command, node, date, exit status, and output for each
required test. Screenshots are not required and must not be the only evidence
for a control point.

### 1.3 Static platform catalog orientation

The static platform catalog is CSE's versioned statement of the platform
configuration supported for Spack builds on one system. It tells a package
manager which compilers, compatible MPI and GPU providers, targets, externals,
and common Spack policies are approved, including which combinations may be
used together. It does not select CSE packages or deployment paths. CSE uses
the restricted release during managed workspace preparation; other package
managers receive the approved published release.

## 2. Responsibilities

| Role | Responsibility |
|---|---|
| CSE build owner | Select the approved inputs, create the workspace, concretize, build, test, and prepare the release record. |
| CSE technical reviewer | Review toolchains, lockfiles, concrete hashes, tests, modules, permissions, SBOM inventory, and change assessments. |
| CSE release authority | Approve the user-facing release. This is the CSE software lead or a documented delegate. |

The project manager receives schedule, risk, and release-status updates. The
build owner requires a second-person review before publication. One person may
serve as technical reviewer and release authority during the Initial
Conversion Trials.

## 3. Required inputs

Record these inputs before workspace preparation:

- target system and required login, build, and runtime node types;
- reviewed system platform record and corresponding restricted static platform
  catalog release;
- published catalog release when package managers outside CSE will consume it;
- installer-owned deployment record;
- reviewed CSE package roster, Spack environment definitions, and configuration
  scopes;
- compiler surfaces and matching MPI providers;
- approved portable CPU target;
- exact Spack version, tag, commit, and package-recipe source;
- restricted and published install trees;
- build-stage, source-cache, misc-cache, and build-cache locations;
- view, module, evidence, and release roots;
- `cse` group access policy; and
- CSE stack and release identifiers.

The controlled package roster is the source of truth for root versions and
variants. Email and this SOP may summarize the roster but do not override it.

### 3.1 CSE operating record

Complete one operating record for each system and release before preparing a
workspace. Use the reviewed platform record, deployment record, package roster,
Spack environment definitions, configuration scopes, and release manifest for
technical inputs. A controlled ticket or release database may carry approvals,
owners, and dates. Every retained input must provide actual selections rather
than instructions to discover them during a build.

| Item | Authoritative artifact or Spack term | Actual value required |
|---|---|---|
| System facts | Reviewed platform record | Reviewed system identifier, node types, compiler, MPI, GPU, target, external, and filesystem facts |
| Platform catalog | Restricted static catalog release | Versioned path, manifest, selected-scope inventory, source identity, and checksums |
| Deployment choices | Installer-owned deployment record | Install tree, build stage, caches, view and module roots, build-cache destinations, Spack root, and access policy |
| Site policy | Reviewed Spack configuration scopes | Compiler, MPI, GPU, target, external, module, Spack-floor, and release policy |
| Package intent | Controlled package roster and Spack environment definitions | CSE package specs, versions, variants, dependency constraints, lane intent, and release identifier |
| Package recipes | Pinned `spack-packages` and CSE package repositories | Approved repository locations and commits |
| Restricted workspace | Prepared Spack workspace | Absolute workspace assembled from the reviewed inputs |
| Published workspace | Publication deployment record | Absolute cache-only publication workspace path |
| Spack runtime identity | Approved Spack source, version, tag, and commit | One exact identity; selected shared or builder-local root may differ |
| Provider selections | Catalog manifest, release manifest, and prepared Spack scopes | Approved compiler, MPI, target, optional GPU tuple, and exact module or prefix evidence |
| Restricted and published releases | Deployment and publication records | Install, view, module, cache, evidence, and consumer roots |
| Collaboration group | Deployment record | Installer-confirmed Unix group |
| Signing identity | Publication record | Full approved public-key fingerprint |
| Reviewer and release authority | Release record | Named people or documented roles |
| Support and announcement channels | Release record | Approved queue and user-notification channel |

The handoff owner fills the record before transferring responsibility. The
receiving builder verifies the retained inputs and prepared Spack configuration
but does not select replacement paths or providers during the build. Session
shell variables may abbreviate paths, but they are not release artifacts and
do not replace the records above.

## 4. Storage, access, and Spack runtime

### 4.1 CSE shared layout

Use separate locations for restricted work and published content:

```text
<approved-cse-shared-root>/
  restricted/
    catalogs/<system>/static/<catalog-release>/
    workspaces/<system>/<stack>/<release>/
    cache/source/
    cache/misc/$USER/
    releases/<system>/<release>/
    buildcache/<system>/<release>/
    evidence/<system>/<release>/
  published/
    catalogs/<system>/static/<catalog-release>/
    catalogs/<system>/static/current
    workspaces/<system>/<stack>/<release>/
    releases/<system>/<release>/

<approved-per-user-stage-root>/$USER/<release>/
  build-stage/
  publish-stage/
```

The restricted catalog path is the retained CSE catalog of record. CSE
workspace preparation uses the platform configuration from that exact release.
The workspace may include the selected scopes directly or materialize
equivalent Spack configuration from the reviewed platform and policy records.
The release manifest must bind the workspace to the catalog release, source
identities, and selected-scope digests.

The published catalog path is an immutable, system-local configuration release
for package managers outside CSE. It is readable and traversable by all
authenticated system users and is not writable by consumers outside CSE. Every
CSE package manager retains management access through the owning group.
Immutability means the version is not edited or overwritten in place. The
optional `current` pointer is for discovery. External package-manager
environments pin the versioned public path, not `current`.

The public static catalog contains reviewed Spack configuration, its manifest,
profile snapshot, reports, and examples. Publishing it does not publish the
restricted CSE workspace, private build cache, restricted package prefixes, or
signing material.

The generated `build_stage::` list uses ordered fallbacks. Put a verified
temporary or node-local path first, verified scratch paths next, and an
absolute `${WORKDIR}/$USER/...` path last. Every entry must be set, absolute,
writable, and executable where the build requires it. Spack skips an unusable
candidate and tries the next valid entry.

Restricted roots use the installer-confirmed CSE Unix group, `cse`, for the
current shared-build environment. Multiple CSE builders require read, write,
and traverse access while a release is assembled. The group name is an explicit
deployment input, not a default inferred by the tooling. Use setgid directories
and the approved default ACL or `umask 0007` so new content remains group-owned
and group-writable.

The restricted-build storage contract is:

| State | Access and ownership |
|---|---|
| Workspace, generated YAML and lockfiles, shared source cache, views, modules, file-backed build cache, and evidence | Shared by the recorded CSE group. Directories are `2770`, ordinary files are `0660`, executable files are `0770`, and access for others is disabled while the release is assembled. |
| Spack package install tree, database, and prefix locks | Shared by the recorded CSE group through Spack `packages:all:permissions`; keep locking enabled and validate the real filesystem's cross-node lock and access behavior. |
| Misc/provider/concretization cache | Persistent builder-named partition at `cache/misc/$USER`. The partition is group-accessible for recovery and inspection, but another builder uses a different partition rather than concurrently replacing its mutable indexes. |
| Build stage, `SPACK_USER_CACHE_PATH`, bootstrap store, and GPG home | Private per-builder mutable state. These paths are recreated for the receiving builder and are not part of the handoff. |
| Shared Spack tool root | Read-only to builders. A builder-local identity-equivalent checkout is private to its owner and remains unchanged during the release. |

Setgid inheritance, a default ACL, and `umask 0007` establish defaults; they do
not override a program that explicitly creates a `0600` file or `0700`
directory. The CSE build entry point therefore normalizes entries owned by the
active builder across the handoff-critical shared surfaces before and after
work. `status`, `concretize`, and `verify` also perform a permission gate across
the common shared surfaces and the active builder's misc-cache partition after
parallel work has stopped. Each builder normalizes its own misc-cache partition
before handoff; one builder does not rewrite another builder's mutable
partition. Every system uses this common generated control; it is not a
Blueback-specific exception.

Publication uses package permissions equivalent to `read: world`,
`write: group`, and the recorded CSE collaboration group. CSE package managers
retain write access. Consumers outside that group receive read and execute
access only. Final publication modes are `2775` for directories, `0775` for
executable files, and `0664` for ordinary files; other write remains disabled.
The leading `2` is setgid, which makes new entries inherit the CSE group. It is
not the sticky bit; sticky is the leading `1` bit and is not used here.

Do not apply recursive ownership or mode changes to a shared tree until the
filesystem owner confirms that the target is dedicated to this release.

### 4.2 Pinned Spack runtime

CSE builders may use either an installer-provisioned shared checkout or a
builder-local checkout. Both must provide the exact approved Spack runtime
identity. The path may differ between builders; the version, tag, commit, and
clean source tree may not.

Select one root:

```bash
export SPACK_VERSION="1.2.2"
# Shared option:
export SPACK_ROOT="<shared-cse-tools-root>/spack/$SPACK_VERSION"
# Builder-local option instead:
# export SPACK_ROOT="$HOME/STACK_TESTING/spack/$SPACK_VERSION"
export SPACK_DISABLE_LOCAL_CONFIG=true
export SPACK_USER_CACHE_PATH="<approved-per-user-cache-root>/$USER/cse-spack/$SPACK_VERSION"
export SPACK_GNUPGHOME="<approved-private-keyring-root>/$USER/spack-gnupg"
export PYTHONDONTWRITEBYTECODE=1
source "$SPACK_ROOT/share/spack/setup-env.sh"
```

The Spack tool root is separate from the restricted and published package
install trees. It contains no workspaces, stages, caches, package prefixes,
views, modules, or signing keys.

The shared checkout is read-only to builders. A local checkout may be writable
by its owner, but it is treated as immutable after a release starts. Builders
do not:

- run `spack isolate` against it;
- modify `$SPACK_ROOT/etc/spack`;
- pull, switch branches, or edit files in place; or
- replace an existing version directory with a newer Spack version.

Provision a new Spack version in a new sibling directory. Switching between a
shared and local checkout with the same verified runtime identity is
operational. A Spack version or commit change is release- and DAG-significant.

### 4.3 Explicit deployment and security configuration

The CSE release retains a durable deployment record for paths and access
policy. It does not derive these choices from the platform record or an
operator's shell. The reviewed record must explicitly contain the selected
install tree, stage, caches, presentation roots, build-cache destination,
Spack root when centrally supplied, and collaboration policy. The record format
is site controlled; the following shows the required information:

```yaml
schema_version: 1
system: <system>

access:
  group: cse
  read: group
  write: group

install_tree:
  root: <absolute-restricted-install-tree>
  padded_length: 128

build_stage:
  default: <absolute-per-builder-stage>
  by_node_type:
    compute: <absolute-compute-stage>

caches:
  source: <absolute-restricted-source-cache>
  misc: <absolute-restricted-misc-cache-root>

roots:
  views: <absolute-restricted-view-root>
  modules: <absolute-restricted-module-root>

modules:
  publish_root: <absolute-site-module-publication-root>

buildcache:
  destinations:
    - name: restricted
      url: file://<absolute-private-build-cache-root>

spack:
  root: <absolute-approved-spack-root>
```

Before concretization, inspect the prepared Spack configuration for every
environment:

```bash
spack -e <environment-path> config get config
spack -e <environment-path> config get packages
spack -e <environment-path> config get mirrors
spack -e <environment-path> config get modules
spack -e <environment-path> config scopes -vp
```

The workspace `config.yaml` must show the selected install tree, ordered build
stages, source cache, builder-specific miscellaneous cache, and enabled locks.
The workspace `packages.yaml` must show the CSE group and restricted read/write
policy. Mirror configuration must distinguish the source cache from the signed
binary build cache. Module configuration must state whether generation is
enabled, the generated-module root, projections, dependency behavior, and
conflicts. The SOP does not prescribe a complete `modules.yaml`; retain and
review the generated file for the release.

Treat every recipe and patch in the selected concrete dependency closure as
executable build input. Pin the Spack runtime, the upstream `spack-packages`
repository, and every CSE package repository to reviewed commits. Review the
repository changes since the previous accepted release, with full manual
review for new or locally changed recipes, changed fetch logic, custom build
hooks, checksum exceptions, and security-critical packages.

The restricted workflow separates network access from user publication:

1. Concretize the reviewed specs and retain unedited lockfiles.
2. Fetch sources into the restricted source cache from a network-enabled node.
3. Verify recipe checksums or immutable version-control commits and retain the
   source inputs used by the lockfile.
4. Build and test in the restricted CSE area. Disable outbound build access
   when site policy requires it.
5. Retain concrete hashes, manifests, test evidence, SBOMs, and the separate
   inventory of system externals.
6. Sign only validated concrete packages and push them to the private build
   cache.
7. Populate the user-facing release from the approved lockfiles and signed
   build cache only. A cache miss stops publication and returns to the
   restricted workflow.

Source checksums authenticate fetched bytes against the pinned recipe. They do
not establish that a recipe or upstream source is free of malicious or
vulnerable behavior. Lockfiles preserve the selected graph but do not replace
recipe-repository review. SBOMs support inventory but do not perform CVE
matching. Use the organization-approved scanners and advisory sources for the
Spack-installed inventory and the separately recorded externals. The detailed
Spack signing, SBOM, integrity, recipe-trust, and package-manager comparison is
kept in the [Spack supply-chain security research](spack_supply_chain_security_primary_source_research_v1.md)
and the [Spack 1.2 signing and SBOM note](spack_1_2_signing_sbom_security_note_v1.md).

## 5. Preflight

Complete platform, deployment, package-roster, path, package-repository, and
Spack checks before workspace preparation. Complete the prepared-workspace checks
before concretization:

- all required repositories and content are on the approved branch and commit;
- the reviewed platform and deployment records name the same target system;
- the selected package roster, environment definitions, and Spack configuration
  scopes are the reviewed release inputs;
- the selected compiler and approved MPI pairings are present;
- the restricted and published roots have the intended group and permissions;
- the build owner and another member of the recorded CSE group can traverse,
  read, create, replace, and remove a controlled test artifact on each shared
  working root before responsibility is transferred;
- the selected Spack checkout matches the approved version, tag, commit, and
  clean state;
- per-user cache and keyring paths are absolute, private where required, and
  outside the selected Spack checkout;
- build-stage candidates are writable from the selected build node and have
  adequate space and inodes;
- shared install-tree locking is enabled and the filesystem supports the
  required lock semantics; and
- login and compute nodes resolve shared paths consistently.

Verify Spack before use:

```bash
SPACK_VERSION_OUTPUT="$(spack --version)"
test "${SPACK_VERSION_OUTPUT%% *}" = "$SPACK_VERSION"
test -z "$(git -C "$SPACK_ROOT" status --porcelain)"
git -C "$SPACK_ROOT" rev-parse HEAD
git -C "$SPACK_ROOT" rev-parse "${SPACK_TAG}^{commit}"
```

Verify configuration scopes globally and for each environment:

```bash
spack config scopes -vp
spack -e <environment-path> config scopes -vp
```

Unexpected active user, system, or site policy is a failed preflight. The
prepared `include::` scopes are the CSE configuration boundary.

After Section 7.1 prepares the workspace, verify it from the login context:

```bash
: "${WORKDIR:?WORKDIR must be set}"
cd "$BUILD_WORKSPACE"
test -f release-manifest.yaml
test -d configs
test -d environments
find environments -name spack.yaml -print | sort

spack -e <environment-path> config scopes -vp
spack -e <environment-path> config get config
spack -e <environment-path> config get packages
spack -e <environment-path> config get mirrors
spack -e <environment-path> config get modules
```

Repeat the read-only Spack inspections from the receiving builder's approved
Spack runtime before transferring responsibility. Preflight passes only when
the approved Spack identity, canonical inputs, prepared workspace, stages,
shared paths, locking, scope boundary, and cross-user access checks pass.

## 6. Select platform configuration

### 6.1 Create and review the static catalog

Prepare the catalog in the restricted review root from the approved platform
record, Spack policy, and source revisions. It may be assembled manually or by
an approved CSE process. The preparation method is internal and does not change
the catalog contract.

The completed versioned tree must contain include-ready Spack configuration,
the catalog manifest, the reviewed platform snapshot, a static plan, and any
operator guidance or examples approved for release. Every scope file must be
complete valid Spack configuration. The manifest must identify the supported
compiler, MPI, GPU, target, external, and module selections; the source
revisions; the selected-scope inventory; the catalog release identifier; and a
fixed UTC creation time. Reviewed uncommitted input is permitted only when the
release record explicitly approves and identifies it. All preparation methods
pass the same inspection and approval gates.

Inspect the result before selecting scopes:

```bash
export SYSTEM_PROFILE="<absolute-reviewed-profile>"
export CATALOG="<absolute-versioned-restricted-catalog>"
test -r "$CATALOG/README.md"
test -r "$CATALOG/manifest.yaml"
test -r "$CATALOG/profile.yaml"
test -r "$CATALOG/reports/static-plan.yaml"
cmp "$SYSTEM_PROFILE" "$CATALOG/profile.yaml"
find "$CATALOG/scopes" -type f -print | sort
```

Review the manifest, static plan, every selected `packages.yaml`, and every
selected `toolchains.yaml`. Confirm the system, release, compiler, MPI, GPU,
target, module, prefix, external-package, and node-type facts. Stop if the
static plan records a missing provider dependency or if a selected pairing is
not supported by reviewed evidence.

### 6.2 Retain the restricted catalog

After review, keep the catalog at its versioned restricted path and freeze that
version through the release procedure. Do not edit it in place. The owning CSE
group retains management access for controlled replacement, retention, and
retirement actions. The restricted release is the source for the later public
static-catalog publication and the platform-configuration record for CSE
workspace preparation. The managed CSE workspace either consumes selected
restricted scope content or materializes the same selections from the reviewed
platform and policy records. It then adds the approved CSE package intent and
deployment choices. It does not use the public catalog to authorize a
restricted build.

The public static catalog is an independent configuration product for package
managers outside CSE. Publish it during the release procedure in Section 10.2.
Public promotion does not replace or remove the restricted review copy or the
managed workspace inputs.

### 6.3 Select scopes

For a package-manager-owned environment, use the scope paths recorded in the
static catalog manifest. Select:

1. common CSE policy;
2. one compiler scope;
3. the portable target and platform scopes;
4. the MPI provider scope paired with that compiler for MPI builds; and
5. a compatible GPU scope only when GPU work is approved.

Do not select MPI by system family alone. Cray systems normally use the
site-provided Cray MPICH selected for the compiler surface. Non-Cray systems use
the CSE-selected MPI provider. Other explicit providers remain possible when
the catalog and CSE policy approve the pairing.

A Cray MPI flavor's GNU version is a supported compiler baseline, not an exact
requirement that the CSE-built GCC version match the flavor name. The catalog
must express the supported pairing. The environment must not infer it from the
directory name.

System OpenSSL, curl, platform MPI, fabric, launcher, math, and runtime
components remain external when the selected catalog policy says so.

Catalog selection passes when each selected path is present in
`manifest.yaml`, the selected compiler and MPI tuple is supported, and the
environment scope listing contains no ambient policy outside the selected
configuration boundary. The managed CSE workspace uses the compiler, MPI,
target, GPU, and external configuration approved by the restricted catalog. It
adds the CSE package intent and deployment inputs and records the catalog
identity, selected scopes, and resulting configuration in the release manifest.

## 7. Define the environment

### 7.1 Prepare and inspect the restricted workspace

Prepare the restricted workspace from the reviewed platform configuration,
deployment choices, package roster, Spack environment definitions,
configuration scopes, and package-repository revisions. It may be assembled
manually or by an approved CSE process. The preparation method is internal and
does not change the workspace contract.

The complete workspace must contain the release manifest, one `spack.yaml` for
each required environment, all referenced configuration scopes, CSE package
repository overlays, module entrance candidates, and operator handoff
instructions. Every relative `include::` path must resolve inside the
transferred workspace. The workspace is accepted through the Spack inspection
commands below.

Do not replace a workspace that contains a lockfile, build output, or evidence.
Follow the runbook recovery procedure or create a new release.

Inspect the complete handoff:

```bash
: "${WORKDIR:?WORKDIR must be set}"
cd "$BUILD_WORKSPACE"
test -r README.md
test -r BUILDER-HANDOFF.md
test -r release-manifest.yaml
find environments -name spack.yaml -print | sort
find configs -type f \( -name config.yaml -o -name packages.yaml \
  -o -name mirrors.yaml -o -name modules.yaml \) -print | sort
find modulefiles -type f -print | sort

spack -e <environment-path> config scopes -vp
spack -e <environment-path> config get config
spack -e <environment-path> config get packages
spack -e <environment-path> config get mirrors
spack -e <environment-path> config get modules
```

Confirm that the release manifest identifies the approved platform catalog,
deployment record, package roster, environment definitions, configuration
scopes, package repositories, system, stack, release, and source revisions.
Confirm that every include path resolves inside the complete workspace handoff.
Serial environments contain no MPI scope. Each MPI environment uses the
provider paired with its compiler surface. Workspace paths and access policy
must match the deployment record.

Do not hand-edit released YAML, helper scripts, or module files. Correct the
owning platform record, deployment record, package roster, environment
definition, configuration scope, recipe repository, or other reviewed input
and prepare a replacement workspace.

### 7.2 CSE environment layout

The Initial Conversion Trials create four independently concretized
environments for each compiler surface:

| Environment | Content | Required binding |
|---|---|---|
| Core | Foundation packages, CSE-selected tools, Python, and other core roots | compiler |
| Common | Compiler-dependent packages shared by payload lanes | compiler |
| Serial | Non-MPI builds of the payload roster | compiler; MPI disabled |
| MPI | MPI-enabled builds of the payload roster | compiler and matching MPI |

GPU is not part of the current trial roster. When approved later, the GPU
environment is composed from the MPI package set plus GPU-specific packages and
uses a compatible compiler, MPI, and GPU runtime. Do not maintain a duplicated
MPI package list for GPU.

Each environment contains the producer groups it needs. The normal order is:

```text
compiler -> foundation -> build tools/core -> payload
```

Groups and `needs` order and expose those producers inside the same environment;
conditional toolchains select them for dependent roots. The same compiler,
Foundation, and build-tool specs may appear in several environments. Identical
concrete hashes reuse the shared restricted store; they are not separate
package builds.

### 7.3 CSE package and dependency policy

- Foundation packages use one pinned version per release.
- Public packages normally use the current approved CSE version and the newest
  active version in the pinned recipe set.
- If the current CSE version is absent from the recipe set, use the two newest
  approved recipe-backed versions.
- A controlled-roster exception may select one or more additional versions.
- Publish HDF5 and NetCDF combinations as tested dependency chains, not an
  untested cross-product.
- Pin the approved build-tool version where package recipes must use it. An
  additional public tool version does not replace that build dependency.
- Version-sensitive modules must load, require, or conflict with the dependency
  versions recorded in the lockfile.
- Serial specs explicitly disable MPI. MPI specs explicitly enable MPI and
  bind the selected provider.

The portable CPU target applies to every source-built root and dependency in
the trial workspace. Approved architecture-specific binary distributions may
use the generic target required by their recipe.

## 8. Concretize and review

Concretize and review each generated environment in the release's documented
order:

```bash
spack -e <environment-path> concretize --fresh -j 1
spack -e <environment-path> find -c -d -l -v
spack -e <environment-path> find -c -d -e -l -v
spack -e <environment-path> config scopes -vp
```

`-j 1` limits concretizer parallelism for clearer trial diagnostics. It does
not set compilation parallelism. The first `find` shows the complete concrete
DAG, including specs not yet installed. The second filters that DAG to
externals.

Review every environment for:

- all controlled-roster root versions;
- the selected compiler surface;
- the matching MPI provider and external prefix or module;
- the portable CPU target and approved exceptions;
- external OpenSSL, curl, fabric, launcher, math, and platform runtimes;
- required build-tool and HDF5/NetCDF dependency pairings;
- the absence of MPI from Serial;
- identical producer hashes where reuse is intended; and
- the absence of unexpected providers or configuration scopes.

After all environments concretize, compare their concrete hashes and provider
bindings with the release manifest and retain the listings as the
cross-environment lock review. Do not edit a lockfile or released YAML.
Correct the owning package roster, environment definition, platform record,
deployment record, configuration scope, or recipe repository and prepare a
replacement workspace.

Concretization passes only when every expected lockfile exists, every reviewed
item above is confirmed, intended producer reuse has identical hashes, and the
scope and concrete-graph evidence is retained. A failed or incomplete
environment holds the complete workspace at this control point.

## 9. Build and validate

Fetch on a login node when compute nodes lack network access:

```bash
spack -e <environment-path> fetch -D
```

Complete fetch for every locked environment and retain the source-cache
inventory before entering an egress-restricted build context. The install may
continue on a compute node using the same environment, source cache, shared
restricted install tree, Spack version, and lockfile. Changing the build-stage
path or node does not change the concrete DAG.

Install in the restricted area from an approved compute allocation:

```bash
spack -e <environment-path> install --fail-fast
spack -e <environment-path> env view regenerate
spack -e <environment-path> module tcl refresh --delete-tree -y
```

Two builders may install identical hashes into the shared restricted tree.
Keep Spack locking enabled. The shared filesystem must support the lock
semantics. Separate Spack processes also have separate build-job budgets; the
operators must coordinate total CPU and memory use.

Parallel installation begins only after all lockfiles pass review and the real
install tree passes the cross-node prefix-lock test. Use distinct generated
environments and a separate process for each one:

```bash
spack -e <first-environment-path> install --fail-fast
spack -e <second-environment-path> install --fail-fast
```

Do not run the same environment twice. Each process has a distinct private
`SPACK_USER_CACHE_PATH`; each builder has a distinct persistent misc-cache
partition. The owning process alone regenerates that environment's views and
modules. After parallel processes stop, each builder runs the approved
shared-output permission normalization for entries that builder owns. The
designated handoff owner then runs the read, write, traverse, group, and mode
checks across the shared workspace, source cache, that builder's misc-cache
partition, views, modules, and file-backed build cache before another builder
resumes. The system runbook owns the filesystem-specific commands.

Run the checks that apply:

- representative C, C++, and Fortran compile/link/run tests;
- package runtime tests;
- headers, libraries, RPATHs, and package metadata;
- Serial tests with no MPI loaded;
- scheduler-launched, multi-node MPI tests;
- launcher, PMI, fabric, and MPI-provider identity;
- view regeneration and module refresh;
- package-module visibility from a clean shell; and
- login-node and compute-node access using another `cse` group member.

After every required environment has installed, regenerate its enabled view
and Spack package modules and create the restricted presentation checkpoint:

```bash
spack -e <environment-path> find -c -d -l -v
spack -e <environment-path> env view regenerate
spack -e <environment-path> module tcl refresh --delete-tree -y
spack -e <environment-path> config get modules
```

Run the view command only for environments that define a view. Stage the
generated CSE compiler front doors and ready lane selectors under the restricted
module root recorded by the deployment record. This checkpoint does not expose the
stack to non-CSE users, publish the static catalog, create the cache-only
publication workspace, alter lockfiles, or rebuild packages. Review the
restricted module presentation as a team before any build-cache or public
promotion.

Presentation-only corrections repeat the control refresh and module review
without rebuilding or reconcretizing. A module projection correction may
regenerate the affected Spack module tree when the concrete DAG is unchanged.
Any package, dependency, compiler, MPI provider, external, or hash change
returns to the applicable restricted build and validation gate.

Record each environment as `built`, `runtime-passed`, or `held`. Promote only
`runtime-passed` concrete specs.

After installation and tests, repeat the retained Spack inspections for every
environment:

```bash
spack -e <environment-path> find -c -d -l -v
spack -e <environment-path> config scopes -vp
spack -e <environment-path> config get packages
spack -e <environment-path> config get mirrors
spack -e <environment-path> config get modules
```

Restricted validation passes only when every required environment is
`runtime-passed`, concrete hashes are recorded, the prepared configuration
still matches the retained inputs, and the compile, runtime, scheduler, MPI,
view, module, clean-session, permission, and handoff checks have successful
evidence. GPU checks are required only for an approved GPU environment.

If a dependency fails with a platform compiler, record the failure first. A
GCC-built replacement is an explicit mixed-toolchain exception. Review its ABI
and runtime linkage, constrain the exact dependency, reconcretize affected
environments, and repeat the tests. Do not add an unconstrained fallback.

## 10. Publish

### 10.1 Signed private build cache

Use one dedicated CSE release-signing identity. Keep the private key in the
restricted release process. Publish and verify the full public-key fingerprint
through a controlled CSE channel.

Trust a reviewed public-key file deliberately:

```bash
spack gpg trust <verified-cse-public-key-file>
spack mirror add --signed cse-private-cache <private-build-cache-url>
```

`spack buildcache keys --install --trust` trusts every key served by the
configured mirror. Use it only when the controlled mirror contains no
unapproved keys. Review the release key at least annually. Retain old public
keys while a retained release may require verification. Treat key rotation,
expiration, revocation, or possible private-key exposure as a release event.

Push approved concrete packages with signing enabled:

```bash
spack buildcache push --signed --key <full-key-fingerprint> \
  <private-build-cache-url> <approved-specs>
```

Do not use unsigned pushes or signature-bypass options in the normal path.
Record the signing-key fingerprint and cache index state with the release.

Spack signs each package spec manifest and authenticates the referenced package
content. Spack 1.2 does not sign the build-cache index manifest. Check index
consistency separately:

```bash
spack buildcache check-index --verify all <private-build-cache-url>
```

### 10.2 Publish the static catalog for external consumers

Publish the retained restricted catalog after the restricted validation and
build-cache gate. This placement aligns the Initial Conversion Trials approval
sequence; static-catalog content remains independent of package binaries.

The designated CSE catalog publication procedure performs these operations:

1. Validate the manifest, profile snapshot, static plan, scopes, and examples.
2. Confirm that all paths and instructions resolve from the final published
   location. A catalog that embeds a restricted absolute path as a consumer
   path is not publishable.
3. Create a checksum inventory for every released file.
4. Record the source revisions, reviewer, approval, date, and catalog release
   identifier.
5. Stage the complete tree under the approved published catalog parent.
6. Publish the versioned directory as one operation.
7. Apply `2775` to directories, `0775` to executable files, and `0664` to
   ordinary files. Retain CSE group management access and remove write access
   for users outside CSE.

The publication record is `publication.yaml`; the file checksum inventory is
`SHA256SUMS`. Copy the reviewed bytes without regenerating them, create those
two records, apply CSE-group-manageable and consumer-readable modes, and expose
the versioned directory as one operation. The named CSE group owns the new
namespace and complete release tree. Updating the optional `current` pointer is
a separate acceptance action. An existing versioned publication is never
overwritten. Whether CSE performs these operations manually or with approved
internal automation, the resulting tree must pass the same checksum, ownership,
mode, and immutability checks.

Set and verify the resolved public path:

```bash
export PUBLISHED_CATALOG="<absolute-versioned-published-catalog>"
export CSE_GROUP="<approved-CSE-group>"
test -r "$PUBLISHED_CATALOG/manifest.yaml"
test -r "$PUBLISHED_CATALOG/publication.yaml"
test -r "$PUBLISHED_CATALOG/SHA256SUMS"
(cd "$PUBLISHED_CATALOG" && sha256sum -c SHA256SUMS)
test -z "$(find "$PUBLISHED_CATALOG" -type d ! -perm 2775 -print -quit)"
test -z "$(find "$PUBLISHED_CATALOG" -type f -perm /111 ! -perm 0775 -print -quit)"
test -z "$(find "$PUBLISHED_CATALOG" -type f ! -perm /111 ! -perm 0664 -print -quit)"
test -z "$(find "$PUBLISHED_CATALOG" -perm -0002 -print -quit)"
test -z "$(find "$PUBLISHED_CATALOG" ! -group "$CSE_GROUP" -print -quit)"
```

Package managers outside CSE pin `$PUBLISHED_CATALOG`. The optional `current`
pointer is for discovery only. Do not use `$PUBLISHED_CATALOG` to initialize
either CSE workspace. Do not edit a published catalog release; correct the
owning input, prepare a complete new restricted catalog release, review it, and
publish a complete new public catalog release with a fresh approval record and
checksum inventory. Move `current` only after acceptance. Record the
supersession and retain or retire the old release according to policy.
Directories grant `rwx` to the CSE group and `r-x` to other users; ordinary
files grant `rw-` to CSE and `r--` to other users. No released path grants
write access to users outside CSE.

### 10.3 Cache-only stack publication

Prepare a separate publication workspace from the same reviewed platform
catalog, package roster, environment definitions, configuration scopes,
recipe-repository revisions, and release identity used for the restricted
workspace. Apply the reviewed publication deployment record, then copy the
approved restricted lockfiles into their corresponding environments. Verify
that the publication release manifest identifies the same package and platform
inputs.
Do not copy the mutable restricted workspace, do not reconcretize, and do not
switch to the public static-catalog path. Use the same restricted catalog
release or equivalent reviewed platform-plan identity recorded for the
restricted workspace.

The publication deployment must change the access audience while retaining the
same CSE management group:

```yaml
access:
  group: cse
  read: world
  write: group
```

Record that deployment policy in the workspace's
`configs/common/packages.yaml`:

```yaml
packages:
  all:
    permissions:
      group: cse
      read: world
      write: group
```

Each prepared environment includes `configs/common` through its
`spack.include` list, so the permission policy does not need to appear inline
in every `spack.yaml`. The static platform catalog does not supply this policy.
It is CSE deployment configuration taken from the reviewed publication
deployment record.

Before installation, inspect the generated file and verify the merged setting:

```bash
test -r <publication-workspace>/configs/common/packages.yaml
spack -e <published-environment> config get packages
```

Stop if the merged `packages:all:permissions` setting does not show the CSE
group with world read and group write.

Install source-free from the signed build cache:

```bash
spack -e <published-environment> install \
  --only-concrete --use-buildcache=only --fail-fast
```

A cache miss stops publication. Build and validate the missing locked hash in
the restricted area, push it, and retry. If the required fix changes a hash,
create a new release.

After every cache-only install:

1. compare published and restricted hashes;
2. regenerate views and modules;
3. verify package-module visibility;
4. run clean-session runtime tests;
5. verify every path retains the recorded CSE group;
6. verify a second CSE package-manager account can create, replace, and remove
   a controlled test artifact in the publication tree;
7. verify directory traverse, file read, executable run, and denied write from
   a non-CSE account on login and compute nodes;
8. verify directories are `2775`, executable files are `0775`, ordinary files
   are `0664`, and no path grants other write; and
9. version-freeze the accepted release through the release record.

### 10.4 SBOM and external inventory

Spack 1.2 writes an SPDX 2.3 SBOM for each non-external installation at:

```text
<package-prefix>/.spack/sbom/spdx-2.3.json
```

Record package name, version, full Spack hash, prefix, SBOM path, and SBOM
checksum. Compare restricted and published SBOM checksums for identical hashes.
Inventory system externals separately because Spack does not create their
SBOMs.

SBOMs support inventory and security review. They do not perform CVE matching.

## 11. User access

The site module path exposes the CSE gateway module in the site's established
module namespace. The gateway is a site integration artifact. It may be placed
in that namespace directly or supplied through an approved symlink from the
CSE release tree.

The gateway module selects one accepted CSE compiler surface and adds the
release-owned lane module location to `MODULEPATH`. The selected lane module
then adds the corresponding generated Spack package-module root. Generated
Spack package modules, views, and lane-specific module roots remain under the
published CSE release tree. They are not copied into the site's general module
tree.

Normal users do not run `module use` for the accepted CSE environment.

The user sequence is:

```bash
module load cse/<compiler-surface>
module load <Serial|MPI>
module load <package>/<version>
```

Use the public names recorded in the release manifest and module configuration.
Do not expose Spack hashes or package-prefix paths as the user interface.

The compiler surface and lane have separate activation responsibilities. The
compiler front door activates its exact compiler chain and records the selected
commands in `CSE_CC`, `CSE_CXX`, and `CSE_FC`. A CSE-built MPI lane loads its
exact generated MPI provider module. A platform Cray MPI lane requires the
reviewed Cray MPI module already supplied by the selected PrgEnv/CPE chain; it
does not silently change that chain. After `module load MPI`, the resolved
interface is recorded in `CSE_MPI_PROVIDER`, `CSE_MPI_VERSION`, `CSE_MPICC`,
`CSE_MPICXX`, and `CSE_MPIFC`.

Verify the selected commands from a clean login:

```bash
module load cse/<compiler-surface>
command -v "$CSE_CC" "$CSE_CXX" "$CSE_FC"
module load MPI
module list
command -v "$CSE_MPICC" "$CSE_MPICXX" "$CSE_MPIFC"
```

For a CSE-built compiler paired with external Cray MPICH, completed locked MPI
package builds establish the selected headers, link inputs, and runtime closure
for the Spack build plane. Validate the ordinary-user interface from the
workspace candidate module. It must expose the exact-prefix `mpicc`, `mpicxx`,
`mpifort`, `mpif90`, and `mpif77` wrappers, bind their `MPICH_*` compiler
overrides to the compiler activated by the CSE front door, and avoid loading a
compiler-selecting `PrgEnv-*`. Do not publish the selector into the release
module root until it completes a native multi-node launch through the site's
approved Slurm or Cray launch path.

Foundation libraries are ambient through the selected compiler/lane view and
do not receive package modules. Core tools and payload packages use the
approved module projections. Serial and MPI surfaces conflict. Versioned
package modules express required dependency loads and conflicts.

Load at least one version-sensitive package during acceptance. For example,
loading NetCDF-C must activate the exact public HDF5 module it was built and
tested with. Loading an alternate HDF5 version alongside it must fail with a
clear conflict diagnostic.

Use `module use <candidate-module-root>` only during validation and rollout.

Validate the gateway from a clean login shell and a clean compute shell. Before
loading the gateway, the generated package-module roots must not be present in
`MODULEPATH`. After loading the compiler surface and one lane, only the
corresponding accepted roots may be present. A Serial and MPI lane conflict
must prevent both from being active at the same time.

### 11.1 Qualified module comparison

The compiler-surface and lane sequence is the primary CSE presentation. A
release candidate may also expose a qualified comparison namespace so reviewers
can compare it with the primary presentation before acceptance.

Generate the comparison namespace from the same concrete specs and installed
prefixes. Use a second named Spack module set with a separate module root. Do
not create another environment, view, install tree, or build. A qualified
Serial package name records the package version, compiler name, and compiler
version. A qualified MPI package name also records the MPI provider name and
version.

For each environment, refresh the primary and comparison sets separately:

```bash
spack -e <environment-path> module tcl refresh --delete-tree -y
spack -e <environment-path> module tcl -n qualified refresh --delete-tree -y
```

During comparison, the compiler front door and lane selector may add both
module roots to `MODULEPATH`. The two modulefiles for one concrete package must
resolve to the same installed prefix and concrete hash, and they must conflict
with each other so one process cannot load both names. Record `module avail`,
`module show`, load, conflict, and runtime results for both names from clean
login and batch shells.

The qualified namespace is presentation policy. It does not change the
lockfile, build cache, package prefix, view, or release identity. Select the
accepted public presentation in the release record. If both remain public,
keep the lane presentation as the documented CSE entrance.

## 12. Changes, security events, and platform updates

A root spec, version, variant, recipe, patch, package-repository revision or
order, compiler, MPI, GPU provider, catalog scope, Spack version,
external-package identity, workspace input, or lockfile change creates a new
CSE release. Reuse unchanged concrete packages only when their full hashes
remain unchanged.

For a security advisory:

1. record the advisory, affected range, severity, source, owner, and due date;
2. search release manifests, lockfiles, SBOM inventory, and external inventory;
3. coordinate system-external fixes with the platform owner;
4. rebuild affected Spack packages and their required dependency closure;
5. repeat restricted validation and cache-only publication; and
6. withdraw or replace exposed modules according to the approved response.

Use the organization-approved advisory source or scanner for CVE matching.

Until a stricter CSE or site policy replaces these targets, use:

| Priority | Initial assessment | Target action |
|---|---|---|
| Emergency: known exploitation, active compromise, or security-designated critical exposure | Same business day | Remove exposure or apply an approved mitigation within 72 hours; publish a replacement as soon as validation passes. |
| High: serious remotely reachable or broadly used component | Within 3 business days | Remediate within 30 calendar days. |
| Routine: other confirmed advisories | Within 10 business days | Address in the next planned release, no later than 90 calendar days. |

Use the approved support or service-desk queue as the system of record. User
notices state the affected releases, temporary action, replacement, retirement
date, and support reference.

For an OS, CPE, compiler, MPI, fabric, launcher, GPU, or platform-library
change:

1. obtain a new reviewed platform record and catalog release;
2. compare the previous and candidate runtime sets;
3. review the supported compiler and MPI pairing;
4. re-concretize against the candidate catalog;
5. run clean compile, runtime, scheduler, fabric, MPI, and module tests; and
6. classify the result as revalidate, remain pinned, rebuild, or hold.

A changed default module is evidence to review. It is not proof that the
existing release is compatible or incompatible.

## 13. Retention, recovery, and rollback

Unless a documented site or security exception applies:

- keep the current release and at least one accepted previous release;
- keep the previous release available for at least 90 days after replacement;
- give at least 30 days' notice before normal removal from the module tree;
- retain a build-cache hash while any retained lockfile refers to it;
- wait at least 30 additional days after the last referring release is removed
  before cache pruning; and
- retain manifests, lockfiles, SBOMs, approvals, security decisions, and test
  evidence for at least three years.

Resume the same release only when all build-defining inputs and hashes are
unchanged and the failure was operational. Create a new release when an input
or hash changes. Preserve failed-workspace logs and the last successful
checkpoint until the replacement is accepted.

Rollback moves the supported module default or release pointer to the last
accepted release. It does not modify either release.

## 14. Required release record

Retain:

- system, catalog, package roster, stack, and release identifiers;
- restricted and published catalog paths, catalog checksum inventory, catalog
  approval, and non-CSE access test;
- exact Spack version, tag, and commit plus every package-repository source,
  commit, and effective search order;
- selected Spack root, runtime-mode, identity verification, and
  configuration-scope evidence;
- restricted and published deployment roots and access policy;
- environment sources, selected scopes, and approved lockfiles;
- restricted and published concrete hashes;
- source-cache inventory, recipe-delta review, approved scan results, private
  build-cache identity, index result, and signing-key fingerprint;
- package inventory, SPDX 2.3 SBOMs, checksums, and external inventory;
- compiler, MPI, target, module-chain, and platform-runtime identities;
- gateway module location, release-owned lane and package-module roots, and
  clean-session `MODULEPATH` evidence;
- build, runtime, view, module, and permission test results;
- change or security assessment when applicable;
- build owner, technical reviewer, release authority, and dates; and
- user announcement, replacement, retirement date, and support record when
  applicable.

Before this draft is approved, fill in:

1. the approved CSE shared root for each system;
2. the approved shared CSE Spack tool root, when one is provided;
3. the support or service-desk queue;
4. the system announcement or mailing list; and
5. the named release authority or approving role.

## Appendix A. Terms

**Static platform catalog**
: Versioned, include-ready Spack configuration for one system.

**Scope**
: A directory containing valid Spack configuration YAML selected through an
  environment's `include::` list.

**Environment**
: A `spack.yaml`, its selected configuration, and the concrete package graph
  recorded in `spack.lock`.

**Compiler surface**
: One CSE compiler and the Core, Common, Serial, and MPI environments built for
  it.

**Toolchain**
: An explicit compiler or a supported compiler and MPI pairing, with a compatible
  GPU runtime when required.

**Restricted build**
: The group-writable CSE source-build and validation area.

**Build cache**
: The controlled repository of approved, signed concrete Spack binaries.

**Published release**
: The cache-only installation, views, modules, and release record approved for
  user access.

**Lockfile**
: The exact package graph generated by Spack in `spack.lock`.

**View**
: A combined filesystem presentation of selected installed packages.

**Module**
: A user-facing environment file loaded through the site module command.
