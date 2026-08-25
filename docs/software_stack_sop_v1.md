# Package Manager Spack Build and Publication SOP — Working Draft

## 1. Purpose

This SOP defines the standard process for a package manager to build and
publish software with Spack on a supported system. The package manager supplies
the package intent. The site-supplied static platform catalog supplies reviewed
compiler, MPI, target, and external-package configuration.

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
- static platform catalog release;
- selected compiler and, when applicable, matching MPI and GPU scopes;
- root package specs, versions, variants, and dependency constraints;
- exact Spack version and package-recipe source;
- install tree, build-stage, cache, view, and module locations;
- filesystem ownership and access policy; and
- application-team release identifier.

The static platform catalog contains configuration. It does not select the
application packages, install tree, views, module roots, or release lifecycle.
Those remain package-manager or site deployment decisions.

## 4. Storage, access, and Spack runtime

Keep the following locations separate:

- the pinned Spack tool root;
- the Spack package install tree;
- the build workspace;
- build stages and source caches;
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
is assembled. Use the site's approved group, setgid directories, and default
ACL or umask policy. Published users receive read and execute access, not write
access.

## 5. Preflight

Complete these checks from the node types that will perform the build and
runtime tests:

- the catalog release and selected scopes are readable;
- the selected compiler and compiler–MPI pairing are present in the catalog;
- the install tree, caches, views, and module root are reachable;
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
spack -e <environment-path> config scopes -vp
```

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

## 6. Select platform configuration

Read the catalog manifest and select the exact scope paths it publishes. A
normal environment includes:

1. common site configuration;
2. one compiler scope;
3. one target or platform scope;
4. one matching MPI scope for MPI builds; and
5. one compatible GPU scope for GPU builds.

Use `include::` so the environment's explicit configuration replaces ambient
configuration:

```yaml
spack:
  toolchains:
    cse_shared:
      - {spec: '%c=gcc@<version>', when: '%c'}
      - {spec: '%cxx=gcc@<version>', when: '%cxx'}
      - {spec: '%fortran=gcc@<version>', when: '%fortran'}
      - {spec: '%mpi=openmpi@<version>', when: '%mpi'}

  include::
    - ../../../catalog/scopes/common
    - ../../../catalog/scopes/compilers/<compiler>/<version>
    - ../../../catalog/scopes/mpi/<provider>/<version>/<compiler-flavor>
    - ../../../catalog/scopes/platform/<platform>
```

Keep the catalog and environment tree together when includes are relative. Do
not copy a single `spack.yaml` without the configuration directories it
references.

Select only documented compiler–MPI pairings. Do not construct a pairing from
module names or installed directories without catalog support.

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
        - openmpi@<version> %cse_shared

    - group: applications
      needs: [compiler, mpi]
      specs:
        - hdf5@<version>+mpi+fortran %cse_shared

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
spack -e <environment-path> concretize --fresh
spack -e <environment-path> find -c -d -l -v
spack -e <environment-path> find -c -d -e -l -v
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

## 9. Build and validate

Fetch on a network-capable node when compute nodes cannot reach package
sources:

```bash
spack -e <environment-path> fetch -D
```

The later install may run on a different node when it uses the same workspace,
source cache, install tree, Spack version, and lockfile.

Install and refresh the environment-owned presentation:

```bash
spack -e <environment-path> install --fail-fast
spack -e <environment-path> env view regenerate
spack -e <environment-path> module tcl refresh --delete-tree -y
```

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

When the validated install tree is published directly, freeze the accepted
release after view, module, permission, and clean-session tests pass. Do not
change an accepted release in place.

Generate or refresh views and modules only after installation. Use
version-sensitive module names, dependencies, and conflicts when more than one
public package version is available.

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
and package prefixes from login and compute nodes. Users must not have write
access to an accepted release.

## 12. Changes, security events, and platform updates

A change to a root spec, version, variant, recipe, patch, compiler, MPI, GPU
provider, catalog scope, Spack version, or lockfile requires a new release
record. Rebuild and retest the affected dependency closure. Reuse unchanged
concrete packages only when their hashes are unchanged.

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

- system and catalog release;
- environment source and selected scope paths;
- exact Spack and package-recipe versions;
- install, cache, view, module, and build-stage locations;
- approved `spack.lock` and concrete hashes;
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
: An explicit compiler or a supported compiler–MPI pairing, with a compatible
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
