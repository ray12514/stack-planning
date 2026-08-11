# Working Draft: Spack Environment Build and Publication SOP

| Document control | |
|---|---|
| Draft | Working draft 1 |
| Date | 2026-08-11 |
| Status | Not approved - prepared for team and project-management review |
| Draft owner | CSE software stack team |
| Intended audience | Package managers and reviewers, including staff with limited Spack experience |
| Approval | Pending |
| Review cycle | Annual and after a major Spack, platform, or security-process change |

This working draft describes how a package manager uses a reviewed, per-system
Spack platform catalog to create, build, validate, and publish an environment.
It covers both the CSE environment and independently managed application
environments. It assumes that the reader may be new to Spack and explains the
main files and handoffs before giving the procedure.

The SOP begins after the system facts and static platform catalog are available.
It does not describe the internal software used to collect facts, generate the
catalog, or generate complete managed workspaces. Package managers work with
normal Spack YAML, lockfiles, build caches, views, and modules.

## 1. Purpose and operating principles

The purpose of this SOP is to make builds repeatable, compatible with the target
system, and safe to publish. Five principles govern the process:

1. **Use reviewed platform configuration.** Compiler, MPI, GPU, fabric, and
   system-external configuration comes from the versioned static catalog for the
   target system.
2. **Bind every environment to a coherent toolchain.** A Serial environment has
   an explicit compiler. An MPI environment has an explicit compiler and its
   matching MPI. A GPU environment has the matching compiler, MPI, and GPU
   toolkit/runtime set.
3. **Build and validate before publishing.** A package is not approved merely
   because it compiled. The environment must be exercised on the target system.
4. **Promote concrete artifacts, not a second solve.** The approved lockfile and
   hashes move from the restricted build to publication. The shared release is
   installed from the approved build cache only.
5. **Never edit an accepted release in place.** Changed inputs, concrete hashes,
   or published module/view content create a new release record.

## 2. Scope

This SOP applies to:

- the CSE software environment built and published by the CSE package manager;
- an application manager creating a system-compatible Spack environment from
  the static catalog;
- package updates, recipe changes, security fixes, and platform transitions;
- restricted builds, build-cache promotion, and shared publication.

This SOP does not prescribe:

- how the system fact sheet or static catalog is generated;
- an internal rendering or orchestration tool;
- one module naming convention for every independent application team;
- site account, scheduler, or filesystem administration outside the package
  manager's approved paths.

## 3. How the pieces fit together

A shared software release moves through a short chain:

```text
reviewed system facts
  -> static platform catalog
  -> package manager's spack.yaml
  -> exact spack.lock
  -> restricted build and tests
  -> signed build cache
  -> shared installation, views, and modules
```

Each item has one job. The system facts say what the machine provides. The
catalog turns those facts into Spack configuration that can be reused. The
package manager's environment says what software is wanted. The lockfile
records exactly what Spack selected. The restricted build proves that selection
on the target system. The build cache carries the approved binaries into the
shared installation without solving or compiling them again.

### 3.1 Terms in plain language

**System fact sheet**
: The reviewed record of what a system provides, including compiler and MPI
  pairings, GPU toolkits, fabric, filesystems, and node roles. It records facts,
  not what a package manager wants to install. For example, it may record that a
  particular Cray MPICH installation is paired with a particular compiler.

**Static platform catalog**
: A versioned tree of include-ready Spack configuration scopes derived from the
  reviewed system facts. It normally contains common policy plus compiler, MPI,
  GPU, target, and platform scopes. Its manifest identifies the release and the
  choices it carries. Think of the catalog as the site's approved starting
  configuration for Spack. It is not an installed software stack, and it does
  not choose an application team's packages.

**Scope**
: A directory containing valid Spack configuration YAML. A package manager
  includes selected scopes from an environment's `spack.yaml`. One scope might
  describe a compiler; another might describe the MPI that was built for that
  compiler. Including both tells Spack to use that exact pairing.

**Environment**
: A normal Spack environment containing root specs and explicit catalog
  includes. This is where a package manager lists packages such as HDF5 or
  Dakota, with their requested versions and options. It owns a lockfile after
  concretization.

**Lane**
: One independently concretized execution surface. The CSE reference layout has
  Core, Common, Serial, MPI, and GPU environments. Independent package managers
  may use fewer environments, but each environment must still select one
  coherent compiler or compiler-plus-MPI/GPU toolchain. Lanes keep incompatible
  builds apart. For example, Serial HDF5 and MPI HDF5 are two different builds,
  even though users see the same package name.

**Concretization**
: Spack's dependency-solving step. It turns requested specs into an exact graph
  of package versions, variants, compilers, providers, dependencies, and hashes.
  The result is written to `spack.lock`.

**Lockfile**
: The exact build plan produced by concretization. It is the record that lets
  the restricted and published installations use the same concrete packages.
  A lockfile is generated by Spack and is never edited by hand.

**Restricted build**
: The operator-controlled installation where packages are built from source and
  tested. It is not user-facing.

**Build cache**
: The controlled repository of approved Spack binaries. It is closer to a
  private package repository than to temporary compiler cache space. Access
  control comes from the filesystem or cache service, not from the Spack
  `--private` flag.

**View**
: A directory that presents selected installed packages through a simpler
  `bin`, `lib`, and `include` layout. A view does not replace the Spack install
  tree; it is a convenient way to expose part of it.

**Module**
: A user-facing environment file loaded with the site module command. It adds
  the selected software and required runtime paths to a user's shell without
  requiring the user to understand the underlying Spack installation.

**Software Bill of Materials (SBOM)**
: A machine-readable inventory describing installed software and its
  dependencies. Spack 1.2 writes an SPDX 2.3 SBOM inside each installed package
  prefix. The SBOM supports inventory and security review; it does not decide
  whether a package is affected by a vulnerability.

**Published release**
: The shared, read-only user installation created from approved binaries and
  the approved lockfile. It contains the user-facing views, modules, and
  validation record.

## 4. Responsibilities and approval

Three roles are enough for this process:

| Role | What the role does |
|---|---|
| Build owner | Selects packages and catalog scopes, chooses the approved paths, builds, tests, and assembles the release evidence. This is normally the package manager. |
| Technical reviewer | Checks the selected toolchain, lockfiles, hashes, tests, SBOM inventory, modules, permissions, and any security or platform-change assessment. This should be another qualified package manager or the CSE software lead. |
| Release authority | Authorizes the release to become user-facing after the technical review passes. For the CSE environment, this is the CSE software lead or a documented delegate. |

The project manager is kept informed of schedule, risk, and release status but
does not need to perform the technical approval. The release record names the
people who filled all three roles for that release. During the small initial
build team, one person may be both technical reviewer and release authority,
but the build owner should not be the only person who reviews a CSE release.

For an independently managed application, the application manager is the build
owner and follows the team's existing technical approval process. Publishing in
the CSE module namespace still requires CSE release authority.

## 5. Storage, access, and Spack location

For the controlled CSE build, keep personal tools and editable source under the
operator's home directory. Keep reviewed build and release products in the CSE
shared workspace.

```text
$HOME/STACK_TESTING/
  spack/<version>/                 optional operator-controlled Spack checkout
  source-and-editable-inputs/      mutable, not user-facing
  probe-and-review-work/           mutable evidence before approval

<approved-cse-shared-root>/
  restricted/
    catalogs/<system>/<catalog-release>/
    workspaces/<system>/<stack>/<release>/
    releases/<system>/<release>/
    buildcache/<system>/<release>/
    evidence/<system>/<release>/
  published/
    workspaces/<system>/<stack>/<release>/
    releases/<system>/<release>/

<node-local-or-site-scratch>/<user>/<release>/
  build-stage/
  publish-stage/
```

The Spack tool may be a pinned checkout in the operator's home directory or a
site-provided module. Its location is separate from the install tree where
Spack places packages. Record the exact Spack version and source in every
release. The initial CSE builds require Spack 1.2 or newer.

The standard Unix group for shared CSE paths is `cse`. During the controlled
build, the operator owns writes and the `cse` group has read/execute access.
Use setgid directories or the site's approved default ACL so group ownership is
inherited. Do not recursively change ownership or permissions on an existing
shared tree without the filesystem owner's approval.

Fill in the path register before this draft is approved. The values are kept in
one place because the rest of the SOP refers to them by purpose rather than by
hard-coded path.

| System | Approved CSE shared root | Unix group |
|---|---|---|
| Blueback | `[enter path]` | `cse` |
| Raider | `[enter path]` | `cse` |
| Wheat | `[enter path]` | `cse` |
| Fran | `[enter path]` | `cse` |

## 6. Prerequisite checks

Do not author or concretize an environment until all of the following are true:

- the package manager has access to the target login and required compute node
  types;
- the selected static catalog release is reviewed and readable;
- the intended compiler/MPI/GPU tuple exists in the catalog;
- the install tree, source cache, misc cache, build cache, views, and module
  roots are approved and visible from the nodes that require them;
- the build stage is writable, has sufficient capacity and inodes, and permits
  build-time execution where required;
- the selected Spack version is active and meets the environment's version
  floor;
- the package/version/variant list and package-recipe source are recorded.

### 6.1 Build-stage writability check

Run the check from the node type that will perform the build, not only from the
login node:

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

Also confirm the path's retention policy, quota, cleanup schedule, and mount
options with the site. A writable login-node path is not sufficient evidence
that the same path is usable from a scheduled build node. Record the chosen
stage and the check result with the release evidence.

## 7. Select the catalog scopes

Read the catalog `README.md`, `manifest.yaml`, and static-plan report before
writing an environment. Select only scopes that form a supported tuple.

The catalog is a directory tree, not a command. A compiler scope contains the
Spack configuration for one approved compiler. An MPI scope contains the
configuration for one MPI build and identifies the compiler with which that MPI
must be used. A GPU scope identifies one approved toolkit/runtime. The manifest
lists the exact scope paths so the package manager does not have to recreate
those details.

For example, this pair of paths means "use this GCC and the OpenMPI built for
this GCC":

```text
scopes/compilers/gcc/<gcc-version>/
scopes/mpi/openmpi/<mpi-version>/gcc-<gcc-version>/
```

Typical selections are:

| Environment type | Required selections |
|---|---|
| Core or Serial | common + target/platform + one compiler |
| MPI | Core/Serial selections + one MPI built for that compiler |
| GPU | MPI selections + one compatible GPU toolkit/runtime scope |

Use the exact scope paths published by the catalog. Never construct a path from
memory or combine a compiler and MPI merely because both are installed on the
system. A missing pairing is a stop condition that must be resolved in the
system facts or catalog.

Use `include::` with two colons so ambient user/site configuration does not
silently join the solve:

```yaml
spack:
  include::
    - /shared/catalog/<system>/<release>/scopes/common
    - /shared/catalog/<system>/<release>/scopes/compilers/gcc/<version>
    - /shared/catalog/<system>/<release>/scopes/mpi/openmpi/<version>/gcc-<version>
  specs:
    - hdf5@<version>+mpi+fortran
    - netcdf-c@<version>+mpi
```

Including a compiler scope means using that cataloged compiler as configured.
If policy calls for building a compiler inside the environment, omit the
external compiler scope and model the compiler as a producer group. Apply the
same rule to a stack-built MPI. Never include an external scope and also expect
Spack to build a replacement for the same provider.

## 8. Author the environment

The package manager owns the root specs, versions, variants, views, and module
policy. Keep the environment self-contained and reviewable:

- pin public root package versions;
- state MPI and GPU variants explicitly;
- select the compiler or toolchain explicitly for every root that requires it;
- declare the MPI provider explicitly rather than accepting the first provider
  the solver can use;
- use groups and `needs` when a compiler or MPI is built as a producer;
- set `concretizer.unify: false` when the environment intentionally carries
  multiple versions of the same package;
- keep install, stage, cache, view, and module paths outside portable package
  intent and record them as deployment choices.

Example with stack-built compiler and MPI producers:

```yaml
spack:
  include::
    - /shared/catalog/<system>/<release>/scopes/common

  packages:
    mpi:
      require: [openmpi]

  specs:
    - group: compiler
      specs:
        - gcc@<gcc-version>

    - group: mpi
      needs: [compiler]
      specs:
        - openmpi@<mpi-version> %gcc@<gcc-version>

    - group: applications
      needs: [mpi]
      specs:
        - hdf5@<version>+mpi+fortran %gcc@<gcc-version>
        - netcdf-c@<version>+mpi %gcc@<gcc-version>

  concretizer:
    unify: false
    reuse: true
```

## 9. CSE reference environment layout

The CSE environment uses five independently concretized environments per
compiler surface:

| Environment | Purpose | Toolchain requirement |
|---|---|---|
| Core | Foundation libraries and loadable tools | explicit compiler |
| Common | compiler-dependent, lane-independent packages | explicit compiler |
| Serial | non-MPI builds of MPI-capable payload packages | explicit compiler; lockfile contains no MPI |
| MPI | MPI-enabled payload packages | explicit matching compiler + MPI |
| GPU | MPI roster plus GPU payload | explicit matching compiler + MPI + GPU runtime |

Foundation libraries are single-version and ambient in the compiler view. Core
tools and Common packages are loadable. Serial, MPI, and GPU are mutually
exclusive user surfaces. GPU is the matching MPI surface plus GPU-specific
payload; it is not a duplicated, independently selected package list.

This layout is the CSE example, not a requirement that every application team
publish five environments. A package manager building one application may use
one environment, provided the environment still has one explicit, supported
toolchain and a complete release record.

## 10. Version and dependency policy

For the CSE environment:

- Foundation libraries have one pinned version per release so the ambient link
  surface is unambiguous.
- Public packages normally carry the newest supported version and its immediate
  predecessor.
- A package may carry one version when multiple versions provide no useful user
  choice, when only one recipe is available, or when the team records a specific
  exception.
- Related packages are published as tested chains, not a cross-product. For
  example, each NetCDF version is paired with the HDF5 version against which it
  was concretized and tested.
- Version-sensitive package modules must require, load, or conflict with the
  dependency versions recorded in the lockfile.

The controlled package roster is the source of truth for CSE versions. Email,
slides, and this SOP may summarize that roster, but they do not override it.
Independent package managers own their version policy and must document it in
their environment source and release record.

## 11. Concretize and review

Concretize in the restricted workspace:

```bash
spack -e <environment-path> concretize --force -j 1
spack -e <environment-path> find -lv
```

Review the resulting `spack.lock` before installation. At minimum, confirm:

- every root resolved at the requested version and variants;
- the compiler is the selected compiler;
- MPI and GPU packages use the selected matching providers;
- platform-owned components remain external at the expected module or prefix;
- Serial contains no MPI node;
- multi-version dependency chains preserve their intended pairings;
- no unapproved provider, target, or external entered through ambient config.

Never hand-edit a lockfile. Correct the environment, catalog selection, package
recipe, or system fact and concretize a new release.

## 12. Build and target-system validation

Install in the restricted workspace:

```bash
spack -e <environment-path> fetch -D
spack -e <environment-path> install --fail-fast
spack -e <environment-path> env view regenerate
spack -e <environment-path> module tcl refresh --delete-tree -y
```

Run tests appropriate to the environment:

- compile and run representative C, C++, and Fortran programs;
- verify headers, libraries, RPATHs, and package metadata resolve to the
  selected release;
- run Serial tests without loading MPI;
- run scheduler-launched, multi-node MPI tests for MPI environments;
- verify the intended fabric, launcher, PMI, and MPI provider at runtime;
- run GPU and GPU-aware MPI tests on the target GPU node type when applicable;
- verify package modules after installation, view regeneration, and module
  refresh;
- test from a clean shell and from both login and compute nodes where users
  require access.

Record each environment as `built`, `runtime-passed`, or `held`. Only
`runtime-passed` concrete specs may be promoted.

## 13. Signed build-cache promotion and shared publication

The build cache is the boundary between software that was merely built and
software that is approved for shared use. The CSE cache uses both access control
and cryptographic package signing. These controls solve different problems:
filesystem or service permissions limit who can reach or change the cache;
package signatures let Spack verify who signed a package manifest and whether
the referenced package content matches it.

### 13.1 CSE signing and trust policy

Use one dedicated CSE release-signing identity. Do not use an individual's
everyday key as the long-term release identity.

- Keep the private key only in the restricted release process and make it
  readable only by authorized release operators. Never copy it into a published
  workspace or shared consumer directory.
- Publish the public key and its full fingerprint through a controlled CSE
  channel. A publication workspace trusts the key only after its fingerprint is
  compared with the release record.
- Mark the CSE mirror as signed and push with
  `--signed --key <full-key-fingerprint>`. Do not use unsigned pushes or
  `--no-check-signature` in the normal release path.
- Record the signing-key fingerprint with every release. Review the key at
  least annually. Rotation, expiration, or revocation is a release-management
  event and requires a documented replacement key.
- Keep old public keys while a retained release may need verification. Remove
  or revoke a key immediately if its private half may have been exposed.

Spack uses its own keyring. Trust a verified public-key file deliberately:

```bash
spack gpg trust <verified-cse-public-key-file>
spack mirror add --signed cse-buildcache <buildcache-url>
```

`spack buildcache keys --install --trust` trusts every key served by the
configured mirror. Use it only when the controlled mirror contains no key that
the CSE release process does not intend to trust.

Spack signs each package's spec manifest. The manifest authenticates the
checksums of the package archive and spec metadata it references. Spack 1.2
does not sign the build-cache index manifest, so the release record must not
describe the entire index as signed. Run the index consistency check in
addition to, not instead of, package-signature verification:

```bash
spack buildcache check-index --verify all <buildcache-url>
```

### 13.2 Promote and publish

Push only approved concrete specs and dependencies to the controlled build
cache. Update and check the cache index, then record the approved hashes and
signing-key fingerprint.

Create the publication environment with the same package/provider intent and
copy the approved `spack.lock`. Do not reconcretize. Install with source
fallback disabled:

```bash
spack -e <published-environment> install \
  --only-concrete --use-buildcache=only --fail-fast
```

A cache miss stops publication. Return to the restricted workspace, build and
validate the exact locked hash, push it, and retry. If producing the package
requires a changed hash, create a new release.

After all cache-only installs succeed, regenerate published views and modules.
Compare the published hashes with the restricted-build hashes. Publish only
after clean-session module tests, runtime tests, permission checks, and release
approval pass.

Installation from the signed mirror performs package-signature verification.
Do not add an option that bypasses it. The cache-only install, signature check,
and hash comparison together prove that publication used the approved concrete
packages.

### 13.3 SBOM and installation evidence

Spack 1.2 automatically writes an SPDX 2.3 SBOM for each non-external package
installation at:

```text
<installation-prefix>/.spack/sbom/spdx-2.3.json
```

After the restricted build and again after cache-only publication:

1. verify that every non-external concrete package has this SBOM;
2. create a release inventory that maps the package name, version, full Spack
   hash, installation prefix, and SBOM path;
3. copy the SBOM files into the release evidence directory without changing
   their contents, and record their checksums;
4. compare the restricted and published SBOM checksums for the same concrete
   hashes; and
5. record platform and site externals separately because Spack does not create
   an SBOM for an external root package.

The per-package SBOMs and external inventory are inputs to the organization's
approved vulnerability source or scanning process. Spack 1.2 does not perform
CVE matching. Its `audit` and `verify` commands check other concerns, such as
recipes, installed-file integrity, and library linkage.

## 14. User consumption

### 14.1 CSE environment

The CSE module root should be added to the site's default `MODULEPATH` before a
release is announced. In the normal user session, the sequence is:

```bash
module load cse/<compiler-surface>
module load <Serial|MPI|GPU>
module load <package>/<version>
```

The release validation procedure may use
`module use <published-cse-module-root>` before the site adds that root to the default path.
That is a validation and rollout step, not the normal user experience.

Users select one compiler surface and one lane. Loading a conflicting lane must
fail clearly. Foundation libraries are already present through the surface;
users do not load separate Foundation modules.

### 14.2 Independently managed environment

An independent package manager normally publishes package modules into the
established application module root that is already on users' `MODULEPATH`.
Users then load the package directly and do not need a separate `module use`
command. If a team must use a new or private module root, the package manager
documents the required `module use` command with the package.

The application team owns its module names and support lifecycle. It must not
place files in the CSE release tree or imply CSE support without approval.

The static catalog makes the build platform-compatible; it does not make an
independent environment part of the CSE release.

## 15. Changes, security events, and platform updates

Every change starts with an impact assessment. Identify the affected catalog
release, environment source, lockfile hashes, installed prefixes, cache
entries, modules, and downstream packages before deciding whether to
revalidate, rebuild, pin, or hold.

### 15.1 Package, recipe, or policy change

Create a new release when a root spec, version, variant, recipe, patch,
compiler, MPI, GPU provider, catalog scope, Spack version, or lockfile changes.
Rebuild and retest every affected environment. Unaffected packages may be
reused from an approved build cache when their concrete hashes are unchanged.

### 15.2 CVE or security advisory

Spack lockfiles and SBOMs provide package identity and dependency provenance;
they are not vulnerability scanners. Use the organization-approved advisory
source or scanner, and include the separate inventory of system externals. When
a CVE or upstream security advisory is reported:

1. Record the advisory identifier, affected version range, severity, source,
   and response deadline.
2. Search the release manifests, lockfiles, SBOM inventory, and external
   inventory for affected roots and dependencies. Include build-time and
   runtime dependencies.
3. Classify the component and apply the response below.

| Component | Required response |
|---|---|
| System external | Coordinate with the system owner. Record the patched package/runtime identity, refresh the platform record if facts changed, and revalidate every affected environment. |
| Spack-built package | Select a fixed upstream version, approved patch, or corrected recipe. Create a new release, rebuild the affected dependency closure, and repeat the promotion gate. |
| Compiler, MPI, GPU, fabric, or launcher runtime | Treat the event as a platform runtime transition and follow section 15.3. |

4. Hold new publication while compatibility or remediation status is unknown.
5. After replacement, verify that no vulnerable hash remains exposed by the active
   module tree or current release pointer. Retain the old release only under the
   approved incident-retention and access policy.
6. Record the decision, evidence, rebuilt hashes, validation results, and user
   notification.

Emergency timing may shorten review windows, but it does not permit a new,
unreviewed concretization in the published tree.

### 15.3 Operating system or platform runtime change

When the OS, programming environment, compiler, MPI, fabric, launcher/PMI, GPU
toolkit, or platform-coupled library changes:

1. obtain a new reviewed system fact sheet and static catalog release;
2. compare the old and candidate compiler/MPI/GPU/runtime fingerprints;
3. review vendor and site support evidence for the complete pairing;
4. concretize against the candidate catalog and classify each affected
   environment;
5. run clean-shell compile, link, scheduler, fabric, MPI, GPU, package, and
   module tests as applicable;
6. publish the decision and any required user action.

| Evidence | Required action |
|---|---|
| Runtime identity and linked providers are unchanged; tests pass | Revalidate. |
| Old runtime remains explicitly selectable and supported; recorded module chain and tests reproduce it | Keep the release pinned to the old runtime. |
| Required runtime, prefix, ABI, provider, or supported pairing changed | Rebuild affected environments and repeat the release gate. |
| Compatibility or support is unknown, or tests fail | Hold publication until evidence or a rebuilt release resolves it. |

The system's default module changing is not, by itself, proof that a rebuild is
required or that the old release remains compatible.

### 15.4 Security intake and user notification

Use the site's normal support ticket or service desk as the system of record for
a security advisory, package problem, or removal request. Email, chat, and phone
calls may alert the team, but the ticket holds the affected systems and
releases, owner, priority, decisions, evidence, due dates, and closure.

Until a stricter site security policy is supplied, use these response targets:

| Priority | Initial assessment | Target action |
|---|---|---|
| Emergency: known exploitation, active compromise, or an exposure the security team marks critical | Same business day | Remove exposure or apply an approved mitigation within 72 hours; publish the rebuilt release as soon as validation passes. |
| High: serious remotely reachable or broadly used component | Within 3 business days | Remediate within 30 calendar days. |
| Routine: other confirmed advisories | Within 10 business days | Address in the next planned release, no later than 90 calendar days. |

Notify affected users through the normal system announcement or application
mailing list. State what is affected, the temporary action if any, the
replacement release, the retirement date, and the support ticket reference.
For a forced security withdrawal, notify users as soon as the unsafe module is
removed from the default module tree.

## 16. Release retention, deprecation, and removal

Use the following default policy unless storage constraints or site policy
require a documented exception:

- Keep the current release and at least one previously accepted release that is
  known to work. The previous release remains available for at least 90 days
  after its replacement becomes current.
- Announce normal deprecation at least 30 days before removing a release from
  the default module tree. Name the replacement and the support contact.
- Remove a release only after the package manager confirms that no supported
  application or retained lockfile still depends on it.
- Do not prune a build-cache entry while any retained release lockfile refers
  to its concrete hash. Wait at least 30 additional days after the last
  referring release is removed.
- Retain release manifests, lockfiles, SBOMs, approvals, security decisions,
  and validation evidence for at least three years, even after binaries and
  modules are removed.
- A vulnerable or compromised release may be removed from the default module
  tree immediately. Preserve its records for the security review, restrict
  access to unsafe binaries, and document why the normal notice period was not
  used.

Deprecation means that a release remains available for a stated transition
period but is no longer recommended. Removal means that it is no longer exposed
through the supported module tree. Deleting build-cache objects is a later
storage operation governed by the lockfile rule above.

## 17. Recovery and rollback

Resume the same release only when all build-defining inputs and concrete hashes are
unchanged and the failure was operational, such as a scheduler timeout, node
loss, network interruption, quota exhaustion, or interrupted cache transfer.

Create a new release when a build-defining input or hash changes. Preserve the failed
workspace, logs, and last successful checkpoint until the replacement is
accepted. Fix the owning source, never generated YAML or a lockfile.

Rollback is a release operation: move the approved user-facing pointer or
module default back to the last accepted release. Do not copy files from an old
release into a new one or alter an accepted release in place.

## 18. Required release record

Every published environment must retain:

- system name and catalog release;
- environment source and selected scope paths;
- exact Spack version and package-recipe source;
- deployment roots and access policy;
- approved `spack.lock`;
- restricted and published concrete hashes;
- build-cache identity and signing/trust evidence;
- the per-package SPDX 2.3 SBOMs and a release inventory that maps each concrete
  hash to its SBOM;
- build, runtime, module, and permission test results;
- platform runtime fingerprint and required module chains;
- change/security assessment where applicable;
- release approval, date, owner, and user announcement.

## 19. Values to complete before approval

The process decisions are stated in this draft. Before approval, fill in the
site-specific values that cannot be made generic:

1. enter the approved shared root for Blueback, Raider, Wheat, and Fran in
   section 5;
2. enter the support ticket or service-desk queue used as the record for build
   and security issues: `[enter channel]`;
3. enter the system announcement or mailing list used for affected-user
   notices: `[enter channel]`.
