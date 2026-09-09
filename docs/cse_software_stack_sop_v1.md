# CSE Spack Build and Publication SOP

| Document control | Value |
|---|---|
| Status | Working draft |
| Review revision | 2026-09-09 |
| Audience | CSE builders, reviewers, release authority, and supporting system and security personnel |
| Scope | CSE operating policy, supported software surfaces, security responsibilities, and release acceptance |
| Shared procedure | [Spack build and publication procedure](software_stack_sop_v1.md) |

## 1. Purpose

This SOP defines how CSE manages its software stacks and applies the shared
Spack procedure. It records CSE's package and platform choices, team
responsibilities, access policy, review decisions, user interface, and release
conditions. The [shared procedure](software_stack_sop_v1.md) owns the common
steps and commands for preparing inputs, creating mirrors, transferring
artifacts, building, validating, signing, publishing, and maintaining a release.

Designated CSE package managers operate Spack in user space to prepare and
maintain the CSE-managed stack, using the approved nonprivileged identities.
Signing and publication use the separately authorized roles and contexts in
Section 10. Normal users consume accepted software through published modules;
they do not build, modify, or publish CSE-managed releases.

Use both documents for a CSE release. Complete the shared procedure with the
CSE selections and acceptance conditions in this SOP. Record the revision of
each document in the release record. A conflict with an assigned system or
security requirement is resolved with its responsible authority before the
affected step; an operator does not choose whichever document is less strict.

This SOP and the shared procedure define the complete operating requirements.
Record system-specific paths, provider selections, scheduler commands, network
controls, and responsible people in the operating record specified in Section
3. The same release gates apply regardless of the approved tools used to carry
out the procedure. A completed release record demonstrates which controls were
performed on each system.

### 1.1 Procedure map

| Activity | Follow the shared procedure | CSE decisions in this SOP |
|---|---|---|
| Assign roles and record the release | Sections 2 and 3 | Sections 2 and 3 |
| Prepare runtime, storage, and configuration | Sections 4 and 5 | Sections 4 and 5 |
| Select the catalog and prepare environments | Sections 6 and 7 | Sections 6 and 7 |
| Resolve and review the candidate | [Review procedure](software_stack_sop_v1.md#procedure-review) | Section 8 |
| Prepare sources and mirrors | [Source mirror procedure](software_stack_sop_v1.md#procedure-source-mirrors) | Section 9.1 |
| Deliver inputs to a system with limited or no external network access | [Transfer procedure](software_stack_sop_v1.md#procedure-disconnected-transfer) | Section 9.2 |
| Build and validate | [Build and validation procedure](software_stack_sop_v1.md#procedure-build-validation) | Section 9.3 |
| Sign, publish the catalog, and install the public stack | [Signing](software_stack_sop_v1.md#procedure-signing), [catalog publication](software_stack_sop_v1.md#procedure-catalog-publication), and [cache publication](software_stack_sop_v1.md#procedure-cache-publication) | Section 10 |
| Accept user access and maintain releases | Sections 11 through 14 | Sections 11 through 14 |

The normal CSE sequence is reviewed inputs and lockfiles, controlled source
intake, restricted build and validation, second-person review, approved signing,
catalog publication, cache-only stack installation, destination acceptance,
and user exposure. A failed gate holds the candidate at the affected step.

## 2. Responsibilities

Assign a build owner and a separate qualified technical reviewer for each
candidate release. The process can be performed by two CSE team members, who
may exchange roles between releases. Their recorded decisions must remain
attributable to separate people.

| Role | CSE responsibility |
|---|---|
| Build owner | Prepare the candidate, identify inputs and changes, perform intake/build/tests, record results and exceptions, and submit the exact candidate for review. |
| Technical reviewer | Independently examine the input/change record, targeted package reviews, test and scan evidence, publication plan, and destination acceptance. Record approval, required correction, or hold with a reason. |
| Release authority | Authorize signing and user exposure. This is the CSE software lead or a documented delegate. The technical reviewer may fill this role when delegated; a third routine CSE position is not required. |
| System or platform owner | Provide and confirm filesystem, account, network, scheduler, compiler, MPI, GPU, external-library, and destination controls that CSE relies on. |
| Security reviewer or responsible security authority | Advise on the operating security baseline and assess security exceptions, boundary changes, or incidents within the authority assigned by the local process. Route decisions requiring another authorizing role to that role. |

The project manager receives schedule, risk, and release-status updates. The
release record names the people filling the CSE roles and identifies the
system/security contacts; role names alone do not prove that review occurred.

### 2.1 Two-person review and audit trail

The builder submits the candidate identity, input and change inventory, review
scope and rationale, test and scan results, unresolved items, and proposed
disposition. The reviewer records their identity, date, reviewed evidence
revision or digest, decision, and any conditions. Record corrections and the
reviewer's recheck against the new candidate state. Approval of earlier bytes
does not approve later changes.

The two people need not repeat the full build independently or manually read
every package. The reviewer verifies that the defined procedure ran, evaluates
the risk-based review and its findings, and checks selected evidence directly.
One designated reviewer remains accountable for the complete candidate and
independent of its material preparation or input changes. The reviewer may
witness repeatable operations and run verification against unchanged approved
inputs; requested corrections go back to the builder. If both people author
material candidate changes, hold release or obtain a qualified independent
reviewer through the existing management process. Reciprocal review of separate
changes does not replace independent review of the complete release.

Use one controlled ticket, review record, or release database entry to connect
these decisions to the candidate. Preserve history and the reviewed snapshots;
do not replace a previous decision with an edited description of the outcome.

### 2.2 Security review and decisions

Routine releases within the agreed baseline stay with the CSE builder,
reviewer, and delegated release authority. Obtain security review or a decision
at the following points. The local process identifies the responsible reviewer
and any required approval authority:

| Trigger | Requested involvement | CSE action while unresolved |
|---|---|---|
| Initial operating baseline or a material change to source trust, build isolation, signing, review, or publication boundaries | Confirm the applicable security outcomes, acceptable evidence, and who may accept exceptions. | Prepare and test the candidate; hold affected production use pending the required decision. |
| An unresolved security finding or an exception to an agreed security requirement | Assess the exposure and proposed mitigation; obtain a scoped, time-bounded decision from the authorized role. | Hold affected promotion; document owner, scope, expiration, and retest conditions. |
| Suspected malicious content, key compromise, or a failed integrity check suggesting compromise | Engage the established incident-response/security process and obtain containment guidance. | Quarantine affected inputs or outputs and preserve evidence; do not promote them. |
| First use of a new transfer route or destination security boundary, or a change to an existing approved route | Confirm transfer handling, destination acceptance, and any required security approval with the transfer and system authorities. | Prepare the delivery inventory; do not use an unapproved route or assume source-system approval covers the destination. |

This SOP does not add separate security approval for each unchanged dependency
or routine source-mirror refresh within an already accepted scope. Ask for input
where it can resolve a security question. CSE technical sign-off does not grant
authority to waive a system security requirement.

## 3. Required inputs

Complete the common operating record in shared procedure Section 3 for each
system and release. CSE additionally binds the following selections:

| CSE record | Required selection |
|---|---|
| Release identity | System, stack, candidate/release identifier, predecessor, builder, reviewer, release authority, and the SOP/procedure revisions used. |
| Package intent | Controlled CSE roster and environment definitions, including root versions, variants, supported dependency combinations, and explicit exceptions. |
| Platform catalog | Exact restricted catalog release, source identities, selected-scope digests, and the reviewed platform/provider records. |
| Tool and recipe baseline | Exact approved Spack version/tag/commit, package-repository commits and order, and CSE overlays. Verify the selected version against the command baseline in the shared procedure before use. |
| Deployment | Installer-chosen restricted and published roots, stages, caches/mirrors, evidence location, gateway location, collaboration group, and access audiences. |
| Security baseline | Input origins, preparation/build network controls, approved scanners and test requirements, signing backend and full key fingerprint, review scope, and applicable exception decisions. |
| Transfer when used | Source and destination identifiers, transfer authorization/route, bundle identity and inventory, destination build or binary-install mode, compatibility evidence, and receipt/acceptance decisions. |
| Operations | Support queue, announcement channel, system/security contacts, retention choices, and any stricter site response targets. |

The roster controls root versions and variants. An email, mirror's contents,
or an available binary does not override that selection. The platform catalog
controls supported configuration, and the installer records deployment paths;
CSE does not infer those paths from system discovery.

## 4. Storage, access, and Spack runtime

Follow shared procedure Section 4 to configure and verify the selected paths,
runtime, permissions, and effective configuration. CSE uses separate restricted
working and published namespaces:

```text
<approved-cse-shared-root>/
  restricted/
    catalogs/<system>/static/<catalog-release>/
    workspaces/<system>/<stack>/<release>/
    cache/source/
    cache/misc/<builder>/
    releases/<system>/<release>/
    buildcache/<system>/<release>/
    evidence/<system>/<release>/
  published/
    catalogs/<system>/static/<catalog-release>/
    catalogs/<system>/static/current
    workspaces/<system>/<stack>/<release>/
    releases/<system>/<release>/

<approved-per-user-stage-root>/<builder>/<release>/
  build-stage/
  publish-stage/
```

This is a deployment pattern. Record actual roots rather than copying the
placeholders. Source-mirror snapshots, transfer staging, and accepted evidence
snapshots have separately recorded paths and write authorities.

| State | CSE access policy |
|---|---|
| Restricted working workspace, source cache, views, modules, file-backed candidate cache, and working evidence | Recorded CSE group; directories `2770`, ordinary files `0660`, executables `0770`, with no access for others while assembling the candidate. |
| Restricted install tree, database, and locks | Spack package permissions use the recorded group, group read/write, and enabled locking; shared-filesystem lock behavior must be verified. |
| Persistent miscellaneous cache | A builder-named partition, group-accessible for recovery; different builders use different mutable index partitions. |
| Build stage, per-process/user cache, and bootstrap work state | Private to the builder or process, recreated for a handoff, outside the Spack tool root. |
| Admitted inputs, reviewed snapshots, and accepted evidence | Retained as identifiable versions with controlled write authority; read-only to build execution where required by the baseline. Shared working-directory modes alone do not provide this protection. |
| Release private key | Controlled signing context outside build execution and transfer bundles. Builder work does not receive the release-signing credential. |
| Published content | Same recorded CSE management group; directories `2775`, executables `0775`, ordinary files `0664`, and no write for users outside CSE. |

Record and confirm the designated CSE Unix collaboration group on each system.
Setgid and the selected default ACL or
`umask 0007` provide working defaults; programs can create stricter modes, so
the common handoff permission checks still apply. Each builder normalizes
only their own working outputs after parallel work stops. Do not recursively
change a shared tree without its filesystem owner's confirmation of scope.

CSE retains group management access to published content for controlled
retirement and replacement. A frozen release is not edited in place. Protect
and retain the approved snapshot/digests and record management actions;
group-writable permissions are not a claim of storage-enforced immutability.

CSE accepts either a read-only shared Spack checkout or an identity-equivalent
builder-local checkout. Both must match the approved clean version/tag/commit
and remain unchanged during the release. The tool root contains no workspace,
package install tree, stage, cache, view, module tree, or signing key. Provision
a changed Spack version in a new sibling directory. Follow the shared runtime
and scope checks rather than changing checkout-local configuration in place.

## 5. Preflight

Follow shared procedure Section 5 with the CSE operating record. Before work
proceeds, the two team members confirm that the prepared system/catalog,
deployment, roster, runtime, repositories, and configuration identify the same
candidate; the required node types and providers are available; shared paths
and locking work; and both accounts have the intended working access.

Record the actual intake/build network enforcement, signing context, and
mirror paths. An intended control written in this SOP is not evidence of
enforcement. When inputs arrive by transfer, complete the receiving-system
preflight and approved transfer checks before executing transferred tools or
recipes. A failed prerequisite holds the affected step.

## 6. Select platform configuration

Use shared procedure Section 6 for catalog preparation, inspection, and scope
selection. CSE retains an exact restricted catalog as the configuration record
for both its build workspace and its later publication workspace. Record the
catalog identity, source revisions, scope selections, and resulting effective
configuration in the release evidence.

The public static catalog is a separate configuration product for package
managers outside CSE. It contains reviewed Spack configuration, a contents and
identity inventory, supported platform/provider combinations, usage
instructions, and its approval record. It does not expose restricted
workspaces, package prefixes, private caches, or signing material. Its
versioned public path is pinned by its consumers; `current` is for discovery.
Public catalog publication does not replace the restricted catalog of record.

CSE selects compiler/MPI/GPU combinations from reviewed provider evidence.
Cray MPICH is the normal Cray-native provider, with explicit alternative MPI
providers allowed when CSE policy and the catalog support them. Do not infer
MPI solely from system family. A GNU version in a Cray MPI flavor name is a
supported compiler baseline, not by itself an exact CSE GCC version pin.

System OpenSSL, curl, MPI, fabric, launcher, math, and runtime components remain
external when selected catalog policy assigns them to the platform. Inventory
their exact identities and test their integration. The acquisition host's
platform facts do not replace those of the destination system.

## 7. Define the environment

Use shared procedure Section 7 to prepare and inspect the complete Spack
environment and its approved inputs. Retain the release record, environment
sources and lockfiles, configuration scopes, overlays, module definitions, and
instructions needed by another authorized operator. Preserve relative includes
as a complete tree during delivery. Accept the resulting configuration through
the same Spack checks whether it was assembled manually or with approved
automation.

### 7.1 CSE environment layout

CSE separates the following independently concretized environments for each
supported compiler surface:

| Environment | CSE content and binding |
|---|---|
| Core | Foundation libraries and CSE-selected tools/Python; bound to the compiler surface. |
| Common | Compiler-dependent packages shared by payload lanes; bound to the compiler. |
| Serial | Non-MPI payloads; bound to the compiler with MPI disabled. |
| MPI | MPI-enabled payloads; bound to the compiler and its selected MPI provider. |

When the approved package selection includes GPU software, compose a GPU
environment from the applicable MPI set plus GPU-specific packages and
compatible compiler/MPI/GPU selections. Record the supported combinations and
required GPU acceptance checks for the destination.

Producer order is compiler, Foundation, build tools/Core, then payload.
Use the shared procedure's Spack-native grouping and toolchain constraints to
express producer order and selection.
Repeated compiler, Foundation, and build-tool specs reuse installed packages
only when their complete concrete hashes match. Foundation is owned per
compiler surface; a public view alone does not establish cross-surface
compatibility.

### 7.2 CSE package and dependency policy

- Foundation libraries use one pinned version per release and remain ambient
  through the selected view, without per-package modules.
- Public packages normally include the current approved CSE version and the
  newest active version in the pinned recipe set. If the current CSE version
  is absent, use the two newest approved recipe-backed versions.
- Record additional versions as controlled-roster exceptions.
- Publish HDF5 and NetCDF as tested dependency combinations. Pin build-tool
  dependencies independently from any additional public tool version.
- Version-sensitive modules express the tested dependency loads and conflicts.
- Serial specs disable MPI; MPI specs enable it and bind the selected provider.
- Apply the approved portable CPU target to source-built roots and dependencies.
  Approved architecture-specific binary distributions may use their recipe's
  required generic target.

## 8. Concretize and review

Follow the shared [review procedure](software_stack_sop_v1.md#procedure-review)
for resolution, inventory, changes, and review evidence. CSE checks the complete
set of environments for controlled-roster versions, compiler/MPI binding,
portable targets, externals, HDF5/NetCDF combinations, build-tool pins, absence
of MPI from Serial, and matching producer hashes where reuse is intended.
All required lockfiles and cross-environment checks must pass before production
builds start.

### 8.1 Scalable package review

CSE inventories the full concrete dependency closure and applies the required
automated checks across the available source/artifact inventory. It does not
require manual inspection of every package recipe or every line of every
dependency for each buildout. Recipe and source code remain executable inputs
even when no individual manual review is selected.

For an initial baseline, the builder records the pinned repositories and source
origins, selected dependency inventory, automated findings, and a risk-based
human review plan. The reviewer assesses that plan and its results. Human
attention focuses on CSE-authored or modified recipes/patches, new trust
sources, changed fetch or execution logic, unusual hooks or embedded downloads,
security-sensitive components, and material findings. A package's presence in
an upstream repository alone is not a local review decision.

For later candidates, compare the complete input inventory with the retained
baseline. Use the resulting delta and findings to select further review; do
not require a person to inspect every upstream repository change unrelated to
the selected release. Reuse an earlier review only when its input identity,
context, and risk assumptions remain applicable. Record the selection criteria,
what was examined, tools/results, decisions, and what was covered by baseline
inheritance. Increase review when a finding or changed trust boundary warrants
it. An unresolved material finding follows Section 2.2.

The independent reviewer signs off on the candidate's review record and
required corrections. Any required stricter organizational review is recorded
in the operating baseline and followed within its actual scope.

## 9. Build and validate

### 9.1 CSE source and mirror preparation

Follow the shared [source mirror procedure](software_stack_sop_v1.md#procedure-source-mirrors).
CSE prepares an identifiable source-mirror snapshot for the approved concrete
environments on a system with the required approved network access. Include
dependency sources, patches/resources, VCS-derived source archives and their
identity bindings, and separately admitted bootstrap/tool prerequisites.
Retain origin, digest, scan, completeness, and review evidence with the
snapshot. An ordinary fetch cache alone is not the documented transfer bundle.

When a system cannot directly retrieve all required source tarballs or other
build inputs, use an approved acquisition system with the necessary access to
prepare the content, then use Section 9.2 for delivery. This applies to partial
external-access restrictions as well as fully air-gapped systems. The receiving
build uses destination-approved configuration and local mirrors. Missing
content returns to controlled acquisition as a recorded supplemental delivery.

### 9.2 Systems with limited or no external network access

Apply the shared [transfer procedure](software_stack_sop_v1.md#procedure-disconnected-transfer)
when a destination cannot directly obtain all required inputs, even if it can
reach some Internet or internal-network resources. Air-gapped systems follow
the same preparation and verification sequence. Transfer only through the
authorized route for the source/destination pair. This procedure also supplies
the technical preparation pattern for future classified destinations; their
transfer and destination-security rules remain additional acceptance conditions.

The CSE builder prepares the delivery inventory and the second person reviews
it before submission to the authorized transfer process. On receipt, retain
the destination verification and acceptance record. The bundle contains the
approved source mirrors and/or signed build-cache objects, required pinned
tools and recipe repositories, complete configuration inputs, lockfiles,
inventories, and transferable evidence. It contains no release private keys
or acquisition credentials. The receiving system separately establishes trust
in the approved public keys.

Record one of these modes for each destination environment:

| Mode | CSE use and acceptance |
|---|---|
| Build from transferred sources | Prepare or verify a destination-specific concrete graph and ensure its complete source/tool inputs are available locally. Build in the destination's restricted area, test there, and submit the new candidate to the two-person review and signing/publication process. |
| Install compatible approved binaries | Verify the approved release and package signatures, exact selected hashes, and destination compatibility. Install from the transferred local build cache without a source-build fallback, then complete destination runtime/module/permission acceptance before user exposure. |

Sister systems are good candidates for reuse, but their relationship is not a
compatibility test. Compare OS/ABI, architecture and CPU target, compiler and
runtime, MPI/fabric/launcher, GPU stack when applicable, external identities,
and required paths/relocation. Record supporting evidence from the destination.
If binary reuse cannot be accepted, choose a source-build candidate explicitly
and apply its gates; do not silently rebuild during publication.

Use the same approved lockfile on the acquisition host only to collect the
destination's inputs, without substituting acquisition-host compiler or external
choices. If destination resolution changes the graph, review the new candidate
and prepare any missing sources before building. Do not assume a source tar
set from a sister system is complete for a different graph.

The destination owns its acceptance decision and release evidence. Source-site
review can be referenced for unchanged inputs; destination configuration,
platform integration, transfer integrity, and execution results still require
local evidence. A destination rebuild produces new artifacts with their own
build, test, review, and signing records.

### 9.3 Restricted build and acceptance

Use the shared [build and validation procedure](software_stack_sop_v1.md#procedure-build-validation).
Separate approved acquisition from build execution. CSE's intended production
baseline uses a nonprivileged restricted build, approved local inputs, enforced
outbound-network denial, and no access to release-signing credentials.
Record platform enforcement and its verification. Any proposed deviation is
handled through Section 2.2 before affected production promotion.

Parallel CSE builds use distinct environments, enabled and verified shared
locks, separate private process state, builder-specific miscellaneous caches,
and one owner for each environment's views/modules. Coordinate total CPU and
memory budgets. The two-person review remains required after parallel work;
concurrency does not supply independent approval.

CSE acceptance covers applicable C/C++/Fortran compile/link/run checks, package
runtime behavior, headers/libraries/linkage, numerical correctness and
representative performance, clean Serial execution, native multi-node MPI and
fabric/launcher behavior, and GPU tests when approved. Select checks and any
reused baseline evidence under shared procedure Section 9.3.
Apply the recorded security scans and qualified compiler-hardening settings;
record failures and exceptions together with functional and performance evidence
where relevant. Scans, SBOMs, and successful tests answer different questions.

Stage the compiler front doors and lane selectors in the restricted module
root and review the presentation as a team. This does not expose the stack to
non-CSE users. Record each required environment as `built`, `runtime-passed`,
or `held`, and retain the applicable security disposition. Signing requires
all release-required environments to pass and all required findings to have
an accepted disposition; `runtime-passed` alone is not security approval.

A presentation-only correction can repeat module/view validation without a
new solve or package build if the graph is unchanged. A compiler, provider,
external, dependency, recipe, or hash change returns to candidate review.
Using an alternate compiler for a dependency requires an explicit
mixed-toolchain decision with ABI/linkage tests and retained compatibility
evidence.

## 10. Publish

### 10.1 CSE signing and release decision

Follow the shared [signing procedure](software_stack_sop_v1.md#procedure-signing).
Use the dedicated approved CSE signing identity and distribute its complete
public-key fingerprint through a controlled channel. The reviewer/release
authority may perform the signing action using separate controlled credentials;
this separation does not require a third team member. A build job receives no
private key.

Sign only the exact reviewed artifact set and bind the evidence and decision to
it in the release record. Record the selected cache backend and its verified
signing behavior; do not assume an OCI registry meets Spack 1.2.2 native signing
requirements. Native package signatures do not authenticate the complete cache
index or establish membership in an approved CSE release. Under shared procedure
Section 10.1, bind the permitted concrete-hash set to the authenticated release
record and require the installer to compare the selected hashes with that set
before installation.

Review the release key at least annually. Retain old public keys while retained
releases need verification. Rotation, expiration, revocation, or suspected
exposure receives a recorded security/release disposition under Section 12.

### 10.2 CSE static catalog publication

Follow the shared [catalog publication procedure](software_stack_sop_v1.md#procedure-catalog-publication).
Publish the accepted restricted catalog after restricted validation and the
build-cache gate. The catalog remains an independent configuration product;
this sequence defines CSE's release order.

Require the versioned public tree, publication approval record, checksum
inventory, original catalog identity, and approved consumer-facing paths,
using the records defined in the shared procedure. Use CSE's published
permissions from Section 4 and test access from outside the CSE group. Retain
the restricted original. CSE's own workspaces continue to use the restricted
catalog identity; external package managers pin the public versioned catalog.

### 10.3 CSE stack publication

Follow the shared [cache publication procedure](software_stack_sop_v1.md#procedure-cache-publication).
CSE prepares a separate publication workspace from the same approved package
and platform inputs, applies its publication deployment record, and carries
over the approved lockfiles. Do not copy the mutable restricted workspace,
reconcretize, or substitute the public catalog as a new configuration authority.

The publication deployment and effective Spack package permissions retain the
recorded CSE group with `read: world` and `write: group`. This access policy is
a deployment choice, not a platform-catalog fact. A missing or unverified cache
object stops publication and returns to restricted preparation; a changed input
or required hash creates a new candidate.

After cache installation, verify package signatures and each hash's membership
in the permitted set bound to the authenticated release record. Accept the
destination's runtime behavior, module/view presentation, and permissions. Verify
management access with the second CSE account and read/execute plus denied
write with a non-CSE account on the relevant node types. Perform write probes
in designated test locations without changing approved artifact bytes.

The reviewer records the result and the delegated release authority approves
user exposure. Publish a new version and update the discovery/default pointer
only after acceptance; do not repair an accepted release in place.

### 10.4 CSE inventory

Use shared procedure Section 10.4 for SBOM and external-inventory handling.
Bind the retained producer SBOMs and their digests to the accepted release.
Record any destination-generated SBOM separately; installation hooks can
regenerate metadata, so equal Spack hashes do not require equal SBOM bytes.
Compare expected package/component identities and retain the platform-owned
external inventory. Use the approved vulnerability analysis process rather
than interpreting an SBOM as a scan result.

## 11. User access

Use shared procedure Section 11 for clean-session module, runtime, and access
checks. CSE's public entrance is:

```bash
module load cse/<compiler-surface>
module load <Serial|MPI>
module load <package>/<version>
```

The CSE gateway lives in the site's established module namespace, directly or
through an approved symlink. It selects the accepted compiler surface and adds
the release-owned lane-module root; the lane selects the corresponding Spack
package-module root. Generated package modules and views remain under the
published release. Normal users do not need `module use`, Spack hashes, package
prefixes, or a local Spack installation to use the accepted software.

The compiler front door activates its exact chain and records `CSE_CC`,
`CSE_CXX`, and `CSE_FC`. The MPI lane records `CSE_MPI_PROVIDER`,
`CSE_MPI_VERSION`, `CSE_MPICC`, `CSE_MPICXX`, and `CSE_MPIFC`. A CSE-built MPI
lane loads its exact provider module. A platform Cray MPI lane uses the reviewed
module supplied by its selected PrgEnv/CPE chain and does not silently replace
that chain.

For CSE-built compilers with external Cray MPICH, accept the ordinary-user
wrapper interface separately from the completed Spack builds. It exposes the
exact-prefix `mpicc`, `mpicxx`, `mpifort`, `mpif90`, and `mpif77`, binds the
`MPICH_*` compiler overrides to the CSE front door, and avoids loading a
compiler-selecting `PrgEnv-*`. Require a native multi-node launch through the
site-approved scheduler/launcher before exposing this selector.

Foundation libraries remain ambient without package modules. Core tools and
payloads use the approved projections. Serial and MPI selections conflict;
versioned modules express tested dependency loads/conflicts. Test a
version-sensitive combination such as NetCDF-C and its exact public HDF5
dependency, including rejection of an incompatible simultaneous HDF5 load.

Candidate module paths are allowed during validation. In accepted clean login
and compute shells, generated package roots must be absent before the gateway
is loaded, and only the selected accepted roots may appear afterward.

### 11.1 Fully qualified module aliases

The compiler-surface/lane sequence is CSE's primary presentation. If additional
fully qualified module names are published, define them in a separate named
Spack module set and module root. They refer to the same accepted specs and
prefixes, with no separate build, environment, view, or install tree.

Qualified Serial names include package and compiler versions; MPI names also
include the provider and version. Use the common module refresh/inspection
procedure for each enabled set. Alias modulefiles must resolve to the same
prefix/hash and conflict with each other. Record clean login and batch results
and the approved public presentation. If both are public, keep the lane
presentation as the documented entrance.

## 12. Changes, security events, and platform updates

Follow shared procedure Section 12 for change handling, advisory assessment,
platform revalidation, withdrawal, and replacement. A build-defining root,
version, variant, recipe, patch, repository revision/order, compiler, MPI/GPU
provider, catalog scope, Spack runtime, external identity, environment, or
lockfile change creates a new CSE candidate/release. Reuse unchanged packages
only with matching full hashes and applicable retained provenance/approval.

CSE uses the approved support queue as its system of record. Assign advisory
ownership to one team member; the other reviews the affected-release assessment
and remediation evidence. Include transferred destination releases and their
local contacts. Refresh vulnerability/scan intelligence on systems with limited
or no external access through the approved update route and record its currency.
A missed update or newly discovered finding requires a recorded disposition.

Use these CSE response targets unless an applicable stricter policy is recorded:

| Priority | Initial assessment | Target action |
|---|---|---|
| Emergency: known exploitation, active compromise, or security-designated critical exposure | Same business day | Remove exposure or apply an approved mitigation within 72 hours; publish a replacement when validation passes. |
| High: serious remotely reachable or broadly used component | Within 3 business days | Remediate within 30 calendar days. |
| Routine: other confirmed advisories | Within 10 business days | Address in the next planned release, no later than 90 calendar days. |

Escalate the cases in Section 2.2 through the existing security process.
Immediate containment follows incident authority; planned release approval
must not delay required containment. Notices identify affected releases,
temporary actions, replacement, retirement date, and support reference.

For OS, CPE, compiler, MPI, fabric, launcher, GPU, or platform-library changes,
obtain the updated reviewed platform/catalog evidence and use the common
compatibility and runtime checks to decide revalidation, continued pinning,
rebuild, or hold. A changed default module alone proves neither compatibility
nor incompatibility.

## 13. Retention, recovery, and rollback

Apply shared procedure Section 13 with these CSE retention requirements, unless
a documented applicable site/security decision supersedes them:

- Keep the current release and at least one accepted previous release.
- Keep the previous release available for at least 90 days after replacement.
- Give at least 30 days' notice before normal module-tree removal.
- Retain a build-cache hash while a retained lockfile refers to it; wait at
  least 30 further days after the last referring release is removed before
  cache pruning.
- Retain manifests, lockfiles, SBOMs, reviews/approvals, security decisions,
  test evidence, and transfer/destination acceptance records for at least three
  years, subject to the destination's handling rules.

Retain or reference the admitted sources, recipes, and tool prerequisites
needed to rebuild supported releases, including disconnected destinations,
and record the selected retention period in the operating record. Preserve
failed-workspace evidence and the last accepted checkpoint until the
replacement is accepted. Reuse a candidate only for an operational retry with
unchanged defining inputs; otherwise create a new candidate.

Rollback selects a retained release that remains acceptable under current
security findings. It changes the supported pointer or module default without
editing either release. Do not restore an exposed release merely because it
was previously approved.

## 14. Required release record

Use the common release record in shared procedure Section 14. CSE adds the
controlled roster and cross-environment checks, restricted/public catalog
relationship, CSE permissions, compiler/lane/module acceptance, and the
transfer records when applicable. The record links the builder's
execution evidence, independent review, release authority's decision, and the
exact approved candidate/artifact identities.

Complete the system roots, contacts, approved security baseline, scanner/update
process, signing authority/backend, transfer route when used, support channel,
and named CSE assignments before the corresponding operation. Track remaining
values explicitly as open prerequisites; this draft does not assign unknown
people or certify unavailable controls.

## Appendix A. Terms

Common terms, including source mirror, build cache, lockfile, environment,
scope, and transfer, are defined in the shared procedure.

**CSE restricted catalog** is the retained configuration release used to
prepare both CSE workspaces. **CSE public catalog** is its separately accepted
configuration publication for external package managers.

**CSE package roster** is the approved list of package roots, versions,
variants, and supported combinations recorded for the release; Section 7.2
defines its selection policy.

**Foundation** means the pinned support libraries made available through the
selected view without individual package modules. **Core** contains those
libraries and user-loadable tools. **Common** contains compiler-dependent
packages shared by the Serial and MPI environments.

**CSE compiler surface** is one selected compiler and its associated Core,
Common, Serial, MPI, and any approved GPU environments. A **lane** is a selected
Serial, MPI, or GPU software environment. The **CSE gateway** is the module
entry point that selects the compiler surface and makes its lane selectors
available, as defined in Section 11.

**CSE published release** is the accepted
cache-installed software, views, modules, and release evidence exposed to the
approved users.
