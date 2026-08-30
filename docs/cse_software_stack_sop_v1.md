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

The Initial Conversion Trials use this process. This SOP contains the normal
command sequence and release controls. The system handoff supplies actual
paths, provider selections, node types, and approving roles. The trial runbook
covers provisioning, exceptional recovery, and system-specific failure
analysis.

### 1.1 Procedure use

Complete the sections in order. Do not continue past a failed control point.
The preferred execution interface after workspace generation is the generated
`cse-build` command. Raw `spack -e` commands in this SOP are inspection and
publication commands or the documented bare-Spack equivalent.

After Sections 3 through 7 are complete, the normal restricted-build sequence
is:

```bash
export WORKDIR="<absolute-builder-work-root>"
export BUILD_WORKSPACE="<absolute-restricted-workspace>"
: "${WORKDIR:?WORKDIR must be set}"
: "${BUILD_WORKSPACE:?BUILD_WORKSPACE must be set}"
cd "$BUILD_WORKSPACE"
./cse-build login status --spack-mode shared
./cse-build login concretize --spack-mode shared
./cse-build login verify --spack-mode shared
./cse-build login fetch --spack-mode shared
./cse-build compute install --spack-mode shared
./cse-build login verify --spack-mode shared
```

Run the compute install from an allocation that satisfies the workspace's
recorded compute context. The system handoff supplies the scheduler command
used to obtain that allocation.

### 1.2 Evidence format

Retain command output as text together with manifests, values files,
environment sources, lockfiles, concrete-hash inventories, checksums, test
programs, SBOMs, and approvals. Record the command, node, date, exit status,
and output for each required test. Screenshots are not required and must not be
the only evidence for a control point.

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

Record these inputs before workspace generation:

- target system and required login, build, and runtime node types;
- reviewed static platform catalog release;
- CSE package roster and package-set release;
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

Complete one operating record for each system and release before generating a
workspace. The record may be a tracked values file, controlled ticket, or
release database entry. It must provide actual values rather than instructions
to discover them.

| Item | Shell or configuration name | Actual value required |
|---|---|---|
| System | `CSE_SYSTEM_NAME` | Reviewed system identifier |
| Catalog release | `CATALOG_RELEASE` | Immutable catalog release identifier |
| Restricted catalog release | `CATALOG` | Absolute reviewed catalog path used for workspace generation |
| Published catalog release | `PUBLISHED_CATALOG` | Absolute approved path readable by all system users |
| Static output parent | `STATIC_ROOT` | Absolute restricted catalog output parent |
| Published static output parent | `PUBLISHED_STATIC_ROOT` | Absolute public catalog output parent |
| Profile and templates | `SYSTEM_DIR`, `CONTENT`, `TEMPLATE_SET` | Approved input paths and template-set identifier |
| Render provenance | `RENDERED_AT`, `SOURCE_REPO`, `SOURCE_COMMIT` | Fixed UTC time and reviewed source identity |
| Publication record | `PUBLISHED_AT`, `CATALOG_REVIEWER`, `CATALOG_APPROVER` | Fixed UTC time and named people or roles |
| Stack Composer command | `CSE_PYTHON`, `STACK_COMPOSER` | Approved Python interpreter and executable path |
| Stack and package roster | CSE release inputs | Approved source revision and release identifier |
| Restricted build values | `BUILD_VALUES` | Absolute approved values-file path |
| Restricted workspace | `BUILD_WORKSPACE` | Absolute workspace path |
| Builder work root | `WORKDIR` | Absolute builder-writable path |
| Published workspace | `PUBLISH_WORKSPACE` | Absolute publication workspace path |
| Shared Spack checkout | `CSE_SPACK_SHARED_ROOT` | Absolute read-only path |
| Spack identity | `CSE_SPACK_VERSION`, `CSE_SPACK_TAG`, `CSE_SPACK_COMMIT` | Approved version, tag, and commit |
| Login and compute contexts | Generated workspace values | Exact node-type keys and stage candidates |
| Compiler and provider selections | CSE build values | Approved compiler, MPI, target, and optional GPU tuple |
| Restricted and published releases | Deployment values | Install, view, module, cache, and evidence roots |
| Collaboration group | `CSE_GROUP` | Installer-confirmed Unix group |
| Signing identity | Publication record | Full approved public-key fingerprint |
| Reviewer and release authority | Release record | Named people or documented roles |
| Support and announcement channels | Release record | Approved queue and user-notification channel |

The handoff owner fills the record before transferring responsibility. The
receiving builder verifies the values but does not select replacement paths or
providers during the build.

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

The restricted catalog path is the retained CSE catalog of record. Both CSE
workspaces are initialized from its exact versioned path. The published catalog
path is an immutable, system-local configuration release for package managers
outside CSE. It is readable and traversable by all authenticated system users
and is not writable by consumers outside CSE. Every CSE package manager retains
management access through the owning group. Immutability means the version is
not edited or overwritten in place. The optional `current` pointer is for
discovery. External package-manager environments pin the versioned public path,
not `current`.

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

## 5. Preflight

Complete path, catalog, and Spack checks before workspace generation. Complete
the generated-workspace checks before concretization:

- all required repositories and content are on the approved branch and commit;
- the catalog manifest and reports match the target system;
- the selected compiler and approved MPI pairings are present;
- the restricted and published roots have the intended group and permissions;
- `./cse-build login status` passes from the build owner and from another
  member of the recorded CSE group before responsibility is transferred;
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
generated `include::` scopes are the CSE configuration boundary.

After Section 7.1 generates the workspace, verify it from the login context:

```bash
: "${WORKDIR:?WORKDIR must be set}"
cd "$BUILD_WORKSPACE"
test -f workspace-manifest.yaml
test -x cse-build
test -d catalog/scopes
test -d environments
./cse-build login status --spack-mode shared
```

Run the same `status` command as a second member of the recorded CSE group
before transferring responsibility. Preflight passes only when the approved
Spack identity, catalog, generated workspace, stages, shared paths, locking,
scope boundary, and cross-user access checks pass.

## 6. Select platform configuration

### 6.1 Generate and review the static catalog

Generate the catalog in the restricted review root from the approved profile,
template set, and source revisions:

```bash
"$CSE_PYTHON" "$STACK_COMPOSER" render-static \
  --profile "$SYSTEM_DIR/profile.yaml" \
  --templates "$CONTENT/templates" \
  --template-set "$TEMPLATE_SET" \
  --output-root "$STATIC_ROOT" \
  --release "$CATALOG_RELEASE" \
  --rendered-at "$RENDERED_AT" \
  --source-repo "$SOURCE_REPO" \
  --source-commit "$SOURCE_COMMIT"
```

The operating record or system handoff supplies every variable in this
command. Use a fixed UTC value for `RENDERED_AT`. Add the renderer's dirty
source flag only when the release record explicitly permits reviewed,
uncommitted input.

Inspect the result before selecting scopes:

```bash
test -r "$CATALOG/README.md"
test -r "$CATALOG/manifest.yaml"
test -r "$CATALOG/profile.yaml"
test -r "$CATALOG/reports/static-plan.yaml"
cmp "$SYSTEM_DIR/profile.yaml" "$CATALOG/profile.yaml"
find "$CATALOG/scopes" -type f -print | sort
```

Review the manifest, static plan, every selected `packages.yaml`, and every
selected `toolchains.yaml`. Confirm the system, release, compiler, MPI, GPU,
target, module, prefix, external-package, and node-type facts. Stop if the
static plan records a missing provider dependency or if a selected pairing is
not supported by reviewed evidence.

### 6.2 Retain the restricted catalog

After review, keep `$CATALOG` at its versioned restricted path and make that
review copy read-only. Both the restricted build workspace and the later
cache-only publication workspace use this retained restricted catalog. The
workspace snapshot makes each workspace portable after initialization, but it
does not change the catalog of record.

Do not switch either CSE workspace to a public catalog path. The public static
catalog is an independent configuration product for package managers outside
CSE. Publish it during the release procedure in Section 10.2. Public promotion
does not replace or remove the restricted review copy.

### 6.3 Select scopes

Use the scope paths recorded in the static catalog manifest. Select:

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
workspace scope listing contains no ambient policy outside the generated CSE
configuration boundary.

## 7. Define the environment

### 7.1 Generate and inspect the restricted workspace

Generate the restricted workspace from the approved blueprint, reviewed
catalog, and completed build values:

```bash
"$CSE_PYTHON" "$STACK_COMPOSER" init-workspace \
  --blueprint "$CONTENT/pilots/cse-pilot" \
  --catalog "$CATALOG" \
  --values "$BUILD_VALUES" \
  --output "$BUILD_WORKSPACE"
```

Do not use `--overwrite` on a workspace that contains a lockfile, build output,
or evidence. Follow the runbook recovery procedure or create a new release.

Inspect the complete handoff:

```bash
: "${WORKDIR:?WORKDIR must be set}"
cd "$BUILD_WORKSPACE"
test -r README.md
test -r BUILDER-HANDOFF.md
test -r workspace-manifest.yaml
test -x cse-build
find environments -name spack.yaml -print | sort
find configs/environments -name modules.yaml -print | sort
find modulefiles -type f -print | sort
./cse-build login status --spack-mode shared
```

Confirm that the workspace manifest identifies the approved catalog, values,
system, stack, release, and source revisions. Confirm that every include path
resolves inside the complete workspace handoff. Serial environments contain no
MPI scope. Each MPI environment uses the provider paired with its compiler
surface. Deployment paths must match the operating record.

Do not hand-edit generated YAML, helper scripts, or module files. Correct the
catalog, CSE values, blueprint, package roster, template, recipe overlay, or
reviewed system input and generate a replacement workspace.

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

Concretize and verify the complete restricted workspace:

```bash
cd "$BUILD_WORKSPACE"
./cse-build login concretize --spack-mode shared
./cse-build login verify --spack-mode shared
```

The generated command creates only the required lockfiles and applies the
workspace-wide lock verifier. Use the following bare-Spack commands to inspect
one environment or to follow an approved manual handoff:

```bash
spack -e <environment-path> concretize --fresh -j 1
spack -e <environment-path> find -c -d -l -v
spack -e <environment-path> find -c -d -e -l -v
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

Run the workspace lock verifier after all environments concretize. Do not edit
a lockfile or generated YAML. Correct the owning roster, values, catalog,
template, recipe overlay, or reviewed system data and regenerate.

Concretization passes only when every expected lockfile exists, the workspace
verifier passes, every reviewed item above is confirmed, and the scope and
concrete-graph evidence is retained. A failed or incomplete environment holds
the complete workspace at this control point.

## 9. Build and validate

Fetch on a login node when compute nodes lack network access:

```bash
cd "$BUILD_WORKSPACE"
./cse-build login fetch --spack-mode shared
```

The install may continue on a compute node using the same workspace, source
cache, shared restricted install tree, Spack version, and lockfile. Changing the
build-stage path or node does not change the concrete DAG.

Install in the restricted area from an approved compute allocation:

```bash
cd "$BUILD_WORKSPACE"
./cse-build compute install --spack-mode shared
```

For an approved bare-Spack handoff, the equivalent per-environment commands
are:

```bash
spack -e <environment-path> install --fail-fast
spack -e <environment-path> env view regenerate
spack -e <environment-path> module tcl refresh --delete-tree -y
```

Two builders may install identical hashes into the shared restricted tree.
Keep Spack locking enabled. The shared filesystem must support the lock
semantics. Separate Spack processes also have separate build-job budgets; the
operators must coordinate total CPU and memory use.

Parallel installation begins only after all lockfiles pass the workspace
verifier and the real install tree passes the cross-node prefix-lock test. Use
distinct environments or the two disjoint surface commands:

```bash
./cse-build compute install --surface shared
./cse-build compute install --surface platform
```

Do not run the same environment twice. Each process has a distinct private
`SPACK_USER_CACHE_PATH`; each builder has a distinct persistent misc-cache
partition. The owning process alone regenerates that environment's views and
modules. After parallel processes stop, each builder exits its prepared shell
so its own misc-cache partition is normalized. The designated handoff owner
then runs `./cse-build login status` to perform the shared-output permission
gate before another builder resumes.

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

After every required environment has installed and regenerated its view and
Spack package modules, refresh the existing workspace's generated controls from
the reviewed Stack Content revision. Then create the restricted presentation
checkpoint:

```bash
cd "$BUILD_WORKSPACE"
./cse-build login verify --spack-mode shared
./cse-build login publish-modules
```

The action copies CSE compiler front doors and ready lane selectors into the
module root recorded by the restricted build values. It does not publish the
stack to non-CSE users, publish the static catalog, create the cache-only
publication workspace, alter lockfiles, or rebuild packages. Review this
restricted module presentation as a team before any build-cache or public
promotion.

Presentation-only corrections repeat the control refresh and module review
without rebuilding or reconcretizing. A module projection correction may
regenerate the affected Spack module tree when the concrete DAG is unchanged.
Any package, dependency, compiler, MPI provider, external, or hash change
returns to the applicable restricted build and validation gate.

Record each environment as `built`, `runtime-passed`, or `held`. Promote only
`runtime-passed` concrete specs.

After installation and tests, run:

```bash
cd "$BUILD_WORKSPACE"
./cse-build login verify --spack-mode shared
```

Restricted validation passes only when every required environment is
`runtime-passed`, the final verifier passes, concrete hashes are recorded, and
the compile, runtime, scheduler, MPI, view, module, clean-session, permission,
and handoff checks have successful evidence. GPU checks are required only for
an approved GPU environment.

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
spack mirror add --signed cse-buildcache <cse-buildcache-url>
```

`spack buildcache keys --install --trust` trusts every key served by the
configured mirror. Use it only when the controlled mirror contains no
unapproved keys. Review the release key at least annually. Retain old public
keys while a retained release may require verification. Treat key rotation,
expiration, revocation, or possible private-key exposure as a release event.

Push approved concrete packages with signing enabled:

```bash
spack buildcache push --signed --key <full-key-fingerprint> \
  <cse-buildcache-url> <approved-specs>
```

Do not use unsigned pushes or signature-bypass options in the normal path.
Record the signing-key fingerprint and cache index state with the release.

Spack signs each package spec manifest and authenticates the referenced package
content. Spack 1.2 does not sign the build-cache index manifest. Check index
consistency separately:

```bash
spack buildcache check-index --verify all <cse-buildcache-url>
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

Run the Stack Composer publication command:

```bash
"$CSE_PYTHON" "$STACK_COMPOSER" publish-static \
  --catalog "$CATALOG" \
  --output-root "$PUBLISHED_STATIC_ROOT" \
  --published-at "$PUBLISHED_AT" \
  --reviewed-by "$CATALOG_REVIEWER" \
  --approved-by "$CATALOG_APPROVER" \
  --group "$CSE_GROUP" \
  --set-current
```

The command copies the reviewed bytes without rerendering, creates
`publication.yaml` and `SHA256SUMS`, applies CSE-group-manageable and
consumer-readable modes, and publishes the versioned directory as one
operation. The named CSE group owns the new namespace and complete release
tree. `--set-current` is optional. An existing versioned publication is never
overwritten.

Set and verify the resolved public path:

```bash
export PUBLISHED_CATALOG="${PUBLISHED_STATIC_ROOT}/${CSE_SYSTEM_NAME}/static/${CATALOG_RELEASE}"
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
owning input, render a complete new restricted catalog release, review it, and
publish a complete new public catalog release with a fresh approval record and
checksum inventory. Move `current` only after acceptance. Record the
supersession and retain or retire the old release according to policy.
Directories grant `rwx` to the CSE group and `r-x` to other users; ordinary
files grant `rw-` to CSE and `r--` to other users. No released path grants
write access to users outside CSE.

### 10.3 Cache-only stack publication

Create a separate publication workspace from the same restricted `$CATALOG`
used for the build workspace. Copy the approved restricted lockfiles. Do not
copy the mutable restricted workspace, do not reconcretize, and do not use the
public static-catalog path.

The publication values supplied to Stack Composer must contain:

```yaml
permissions:
  group: cse
  read: world
  write: group
```

Stack Composer renders those values into the workspace's
`configs/common/packages.yaml`:

```yaml
packages:
  all:
    permissions:
      group: cse
      read: world
      write: group
```

Each generated environment includes `configs/common` through its
`spack.include` list, so the permission policy does not need to appear inline
in every `spack.yaml`. The static platform catalog does not supply this policy.
It is CSE deployment configuration generated from the publication values.
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

Use the public names recorded in the release values. Do not expose Spack hashes
or package-prefix paths as the user interface.

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

A root spec, version, variant, recipe, patch, compiler, MPI, GPU provider,
catalog scope, Spack version, package-recipe source, workspace input, or
lockfile change creates a new CSE release. Reuse unchanged concrete packages
only when their full hashes remain unchanged.

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
- exact Spack version, tag, commit, and package-recipe source;
- selected Spack root, runtime-mode, identity verification, and
  configuration-scope evidence;
- restricted and published deployment roots and access policy;
- environment sources, selected scopes, and approved lockfiles;
- restricted and published concrete hashes;
- private build-cache identity, index result, and signing-key fingerprint;
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
