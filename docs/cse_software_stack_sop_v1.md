# CSE Spack Build and Publication SOP — Working Draft

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
  -> publish from the approved lockfiles and cache only
  -> validate views, modules, permissions, and runtime behavior
  -> freeze and approve the release
```

The Initial Conversion Trials use this process. The trial runbook supplies the
current commands and site values. This SOP supplies the release policy.

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

## 4. Storage, access, and Spack runtime

### 4.1 CSE shared layout

Use separate locations for restricted work and published content:

```text
<approved-cse-shared-root>/
  restricted/
    catalogs/<system>/<catalog-release>/
    workspaces/<system>/<stack>/<release>/
    cache/source/
    cache/misc/$USER/
    releases/<system>/<release>/
    buildcache/<system>/<release>/
    evidence/<system>/<release>/
  published/
    workspaces/<system>/<stack>/<release>/
    releases/<system>/<release>/

<approved-per-user-stage-root>/$USER/<release>/
  build-stage/
  publish-stage/
```

The generated `build_stage::` list uses ordered fallbacks. Put a verified
temporary or node-local path first, verified scratch paths next, and an
absolute `${WORKDIR}/$USER/...` path last. Every entry must be set, absolute,
writable, and executable where the build requires it. Spack skips an unusable
candidate and tries the next valid entry.

Restricted roots use the lowercase Unix group `cse`. Both assigned CSE
builders require read, write, and traverse access while a release is assembled.
Use setgid directories and the approved default ACL or `umask 0007` so new
content remains group-owned and group-writable.

The restricted-build storage contract is:

| State | Access and ownership |
|---|---|
| Workspace, generated YAML and lockfiles, shared source cache, views, modules, file-backed build cache, and evidence | Shared by the CSE group. Directories are `2770`, ordinary files are `0660`, executable files are `0770`, and access for others is disabled while the release is assembled. |
| Spack package install tree, database, and prefix locks | Shared by the CSE group through Spack `packages:all:permissions`; keep locking enabled and validate the real filesystem's cross-node lock and access behavior. |
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
`write: user`, and group `cse` while the release is assembled. Consumers receive
read and execute access only. After acceptance, remove group and other write
access from the release, views, modules, and release pointer.

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
- the selected compiler and compiler–MPI pairings are present;
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

## 6. Select platform configuration

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

## 7. Define the environment

### 7.1 CSE environment layout

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

### 7.2 CSE package and dependency policy

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

Concretize each restricted environment and retain its lockfile:

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

## 9. Build and validate

Fetch on a login node when compute nodes lack network access:

```bash
spack -e <environment-path> fetch -D
```

The install may continue on a compute node using the same workspace, source
cache, shared restricted install tree, Spack version, and lockfile. Changing the
build-stage path or node does not change the concrete DAG.

Install in the restricted area:

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

Record each environment as `built`, `runtime-passed`, or `held`. Promote only
`runtime-passed` concrete specs.

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

### 10.2 Cache-only publication

Create a separate publication workspace. Copy the approved restricted
lockfiles. Do not reconcretize. Install source-free from the signed build cache:

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
5. verify consumer permissions from login and compute nodes; and
6. freeze the accepted release.

### 10.3 SBOM and external inventory

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

The accepted CSE module root is added to the site's standard `MODULEPATH`.
Normal users do not run `module use` for the published CSE environment.

The user sequence is:

```bash
module load cse/<compiler-surface>
module load <Serial|MPI>
module load <package>/<version>
```

Use the public names recorded in the release values. Do not expose Spack hashes
or package-prefix paths as the user interface.

Foundation libraries are ambient through the selected compiler/lane view and
do not receive package modules. Core tools and payload packages use the
approved module projections. Serial and MPI surfaces conflict. Versioned
package modules express required dependency loads and conflicts.

Use `module use <candidate-module-root>` only during validation and rollout.

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
3. review the supported compiler–MPI pairing;
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
- exact Spack version, tag, commit, and package-recipe source;
- selected Spack root, runtime-mode, identity verification, and
  configuration-scope evidence;
- restricted and published deployment roots and access policy;
- environment sources, selected scopes, and approved lockfiles;
- restricted and published concrete hashes;
- private build-cache identity, index result, and signing-key fingerprint;
- package inventory, SPDX 2.3 SBOMs, checksums, and external inventory;
- compiler, MPI, target, module-chain, and platform-runtime identities;
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
: An explicit compiler or a supported compiler–MPI pairing, with a compatible
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
