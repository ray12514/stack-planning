# CSE Spack security assurance case for DoD HPC v1

| Document control | Value |
|---|---|
| Date | 2026-09-03 |
| Alignment review | 2026-09-16; explicit Spack installation and bootstrap admission, repository snapshot waiting period, and optional review outside CSE, aligned with the SOP drafts |
| Status | Research-backed proposed policy basis; not an authorization decision or operator procedure |
| Audience | CSE package managers, security reviewers, assessors, system owners, and responsible authorizing roles |
| Primary scope | Spack 1.2.2 used to build and publish software for unclassified DoD HPC systems |
| Secondary scope | Transfer of approved artifacts to a classified enclave is identified only as a separate acceptance boundary |
| Method | Primary sources from NIST, DoD, OMB, Spack, RPM, DNF, Conda, GCC, GNU binutils, glibc, and HPE |

This document supplies supporting security rationale. The
[CSE SOP](cse_software_stack_sop_v1.md) records CSE policy and acceptance choices;
the [shared procedural SOP](software_stack_sop_v1.md) owns the common operating
steps. Additional control options in this analysis remain proposals until
adopted through the applicable local process. This alignment review does not
revalidate every external reference or establish local implementation.

## Executive assessment

CSE proposes to meet the stated software supply-chain, build-integrity,
configuration, hardening, and change-control outcomes through a managed
software-production process. The assessment concerns that defined process,
its operating bounds, and the evidence required for production use.

Designated CSE package managers use Spack in user space to prepare and maintain
the managed stack. Authorized release personnel install accepted signed cache
artifacts into the publication or destination store. Normal users access the
installed software through CSE modules; they do not build or publish the
CSE-managed stack. The managed installation and end-user paths have distinct
responsibilities and acceptance evidence.

Source production executes Python recipes and upstream build systems and uses
configuration, source, and bootstrap inputs. Those inputs and execution paths
require explicit control. Spack checksums, lockfiles, package hashes, tests,
signatures, and SBOMs contribute evidence; none independently establishes that
an input or output is benign.

The proposed CSE process can support a defensible DoD HPC software supply
chain. The acceptable operating model is:

> controlled intake, pinned and digest-bound input admission, concrete-graph review,
> egress-denied unprivileged build, security and functional validation,
> independent approval and signing, frozen versioned publication, managed
> cache-only installation, module-based user access, and continuous monitoring.

The proposed intake policy uses an aged, pinned package-repository snapshot
to delay routine adoption of recent recipe changes. A proposed 90-day minimum
implements the intended approximately three-month observation period.
Independent review may be assigned to a qualified person outside CSE when
additional expertise or organizational distance is needed. These are proposed
local controls, not Spack guarantees or evidence of implementation on a system.

This model aligns the security outcomes with controls and evidence at each
stage. Where package-manager comparisons help explain a control, compare
equivalent governed production or installation processes. A signed, controlled
CSE build cache supports managed installation while preserving the compiler,
provider, ABI, and microarchitecture selections required for HPC. The technical
comparison later in this document is supporting analysis.

### Proposed authorization position

| Operating mode | Proposed position | Reason |
|---|---|---|
| Ad hoc Spack source build with public fallback, ambient user configuration, or unsigned output | Do not approve for system-wide publication | The executable input set, network path, and promotion authority are not adequately bounded |
| Restricted CSE intake and build using the gates in this document | Candidate for conditional approval of the bounded operating model | Production use on each system requires demonstration and acceptance of the applicable intake, build, validation, review, signing, and publication controls |
| Managed installer using only the approved signed CSE build cache | Required CSE stack-publication installation path under the current SOP | Designated operators install accepted artifacts without source-build fallback. Their Spack core, repositories, hooks, configuration, and installation behavior remain within the trust boundary |
| Normal end user of the accepted CSE stack | Access through published environment modules | Users execute the accepted installed software without operating Spack or publishing CSE releases |
| Transfer from unclassified to classified | New acceptance decision | The destination enclave, transfer mechanism, target compatibility, keys, scanning, and AO conditions require separate approval |

Approval should identify the controlled CSE operating model, its scope, and
required evidence. It does not automatically accept another system, destination,
transfer route, or security boundary. Production starts only after the required
controls are demonstrated and accepted for the receiving system. A deviation
such as an unreviewed overlay, public fetch fallback, an uncontrolled
configuration scope, unsigned publication, or an
in-place release edit invalidates the assurance case for that candidate.

## Scope, assumptions, and limitations

This assessment assumes that CSE intends to:

* pin Spack core, `spack-packages`, overlays, sources, and concrete dependency
  selections;
* use an access-controlled management area for intake, resolution, build,
  testing, and review;
* fetch source content in a distinct, controlled-egress step;
* build as a nonprivileged identity with outbound network access denied;
* prevent ambient `~/.spack` and other unapproved configuration from affecting
  the build;
* scan, test, document, approve, and sign candidate artifacts before
  publication;
* publish frozen versioned releases with retained digests and controlled
  management actions, without repairing accepted bytes in place;
* require designated installers to use the approved signed build cache without
  source-build fallback; and
* provide normal users with accepted installed software through managed modules.

The organizational white paper was not available for review. This document
evaluates the described security outcomes and proposed operating model; it does
not quote the paper or attribute specific assertions to it. The system
categorization, NSS status, selected RMF baseline, overlays,
Control Correlation Identifiers, assignment values, contract requirements,
Component policy, and AO-specific conditions were also unavailable.

The NIST control references in this document are candidate traceability
mappings. They do not mean that a Spack command implements a control, that
every listed control is assigned to the system, or that the process is
compliant. The system owner, assessor, security reviewer, and responsible
authorizing role must confirm the actual requirements and the evidence accepted
for them.

Unclassified does not mean non-NSS. That designation must be confirmed. An
approved artifact on an unclassified system does not become approved for a
classified enclave merely because it was scanned and signed.

## Findings

### The security concern is valid

A Spack package repository is executable supply-chain input. Spack imports
`package.py`, invokes package and builder methods, modifies the build
environment, applies patches and resources, and runs external build tools. The
recipe can therefore perform actions under the authority of the build identity
([Spack repository loader](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/repo.py#L128-L176),
[imperative install example](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L1297-L1308)).

That executable surface is larger than `package.py`. A recipe may invoke
upstream `configure`, CMake, Make, Python, shell, vendor installers, generated
code, patches, tests, and bootstrap tools. Compilers, Cray PE modules, MPI,
system libraries, and other externals also participate in the result. Reading
only a recipe does not fully vet the software.

Spack source and package hashes improve change detection and identity. They do
not approve intent. An archive checksum proves that downloaded bytes match an
admitted digest. A malicious change that replaces both a URL and its digest can
still pass the checksum. A build-cache signature proves that the trusted key
holder signed the described cache object. It does not prove that the source,
recipe, builder, or binary was safe.

### Assessing the defined operating mode

The primary-source analysis below concerns risk, provenance, controlled
processes, testing, integrity, authorization, and continuous monitoring. Use
those requirements to assess the specific operating mode and its evidence.

The DoD memorandum on software development and open source software requires
open source to receive equal consideration while meeting the same rigorous
supply-chain and cyber-testing expectations as other software
([DoD software development and open source software memorandum](https://dodcio.defense.gov/Portals/0/Documents/Library/SoftwareDev-OpenSource.pdf)).
The defensible comparison is therefore between configured operating modes, not
brand names.

### The proposed CSE architecture is directionally sound

The proposed restricted-intake, isolated-environment, lockfile, testing,
build-cache, SBOM, and frozen-publication design defines release boundaries.
For each boundary, retain:

1. a named owner;
2. an explicit pass or fail decision;
3. evidence bound to the exact release;
4. a defined failure response; and
5. a rule that changed input creates a new candidate release.

The remaining work is primarily control completion and evidence definition,
not a replacement of Spack.

## Trust-boundary model

| Input or authority | Security effect | Required control |
|---|---|---|
| Spack core and its runtime | Runs the concretizer, configuration system, fetch logic, build orchestration, hooks, signing, and installation; includes bundled Python libraries and the separately supplied starting interpreter | Bind the release tag to a full commit and retained content digest; inventory and assess bundled libraries, the actual Python interpreter, and system prerequisites; approve before operational use on builders, publishers, and managed installers |
| `spack-packages` and overlays | Supply executable recipes, patches, resources, variants, providers, conflicts, and hooks | Pin exact commits; record repository order; review the reachable baseline or approved delta |
| Source archives and VCS content | Supply the software and upstream build logic | Use approved origins, immutable identifiers, strong digests, controlled intake, scanning, and retained source objects |
| Bootstrap content | May introduce solvers, GPG support, or other tools outside the ordinary package source mirror. Spack's default bootstrap enables bundled public binary and source methods | Disable bootstrap and pre-provision approved prerequisites, or admit a separate local bootstrap mirror and its metadata and digests. Bootstrap's `--trust` setting is configuration trust, not a GPG signature assertion ([default bootstrap configuration](https://github.com/spack/spack/blob/v1.2.2/etc/spack/defaults/bootstrap.yaml), [bootstrap verification path](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/bootstrap/core.py#L154-L192)) |
| Configuration scopes and command line | Can replace compilers, externals, mirrors, repos, permissions, variants, targets, and build behavior | Use a controlled launcher, allowlist scopes, prohibit unapproved overrides, and retain effective configuration evidence |
| Compilers, Cray PE, MPI, OS, libraries, and other externals | Affect ABI, generated code, runtime behavior, and dependency trust but may not be fully represented in a lockfile | Inventory exact module/version/path/identity; validate target compatibility; include externals in vulnerability and release records |
| Build host or image | Supplies kernel, filesystem, process, network, tool, and credential boundaries | Harden and baseline it; use least privilege; deny egress; make approved inputs read-only; preserve logs |
| Builder | Can execute recipes and produce candidate artifacts | Prevent self-approval and access to release-signing credentials during build execution; grant only required write paths; monitor actions |
| Reviewer and approver | Determines whether input and evidence satisfy policy | Define review depth, two-person rules, exceptions, and go/no-go authority |
| Release signing key | Converts a candidate into an authenticated CSE artifact | Protect outside the builder; control use, fingerprint distribution, rotation, revocation, and recovery |
| Catalog, index, and release aliases | Determine which signed packages managed installers select and which accepted release users access | Bind the approved set in an authenticated CSE release record and update aliases atomically |
| Managed installer configuration | Can permit unapproved mirrors, keys, recipes, hooks, source fallback, upstream stores, existing local installs, or externals | Trust only approved fingerprints; verify membership in the authenticated approved release set; use a clean or dedicated store; prohibit unapproved upstreams; admit externals separately; require build-cache-only installation; block fallback |

## Defining recipe vetting

Define recipe admission by input identity, review scope, risk criteria,
frequency, evidence, and responsible role. The process covers the complete
selected inventory and directs manual attention to changes and risk.

### Initial baseline admission

For the first approved baseline, generate the complete concrete closure of the
selected root specifications. Identify the effective recipe selected for every
node after repository precedence and namespace resolution. Inventory and retain
the following input categories, apply the configured automated checks, and
document the selection and results of risk-based human review:

* the exact Spack core, `spack-packages`, and overlay commits;
* effective repository names, namespaces, order, and overrides;
* every reachable recipe, patch, resource, submodule, extra source, and custom
  build phase;
* lifecycle hooks and code that changes the build or dependent environment;
* URLs, VCS revisions, archive digests, upstream signatures when available,
  and license information;
* build-time network activity, generated downloads, vendored dependencies, and
  package-manager use inside upstream build systems;
* compilers, MPI, Cray PE modules, system libraries, and other externals;
* bootstrap sources and tools; and
* maintainer health, release history, known vulnerabilities, source-origin
  concerns, and criticality appropriate to the package.

Admit an exact package-repository revision and retain its identity and approved
context. This process does not require recreating upstream recipes or manually
reading every recipe and source file. Record automated coverage and gaps;
manually inspect CSE-authored or modified inputs and select other recipes by
provenance, changed execution or fetch logic, security sensitivity, and findings.
Repository pinning identifies the admitted baseline; it does not establish
that every package is safe. The review should identify the full executable
trust boundary,
apply automated checks across the candidate, and use deeper human review where
criticality, exposure, privilege, source novelty, custom logic, or change risk
justifies it. NIST SP 800-161 and SP 1326 support risk- and criticality-based
due diligence rather than a single undifferentiated review depth
([NIST SP 800-161 Rev. 1 Update 1](https://doi.org/10.6028/NIST.SP.800-161r1-upd1),
[NIST SP 1326](https://doi.org/10.6028/NIST.SP.1326)).

### Repository snapshot waiting period

Use the age of the admitted upstream package-repository snapshot as a routine
intake criterion. This gives upstream users and security monitoring time to
surface defects or compromise before CSE adopts recent changes. It is a delay
before adoption, not a claim that time makes code safe. Spack supports fixing
a Git-backed package repository to a tag or commit; retain the tag as a human
reference and bind admission to its resolved full commit and retained content
([Spack repository pinning](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/repositories.rst),
[snapshot research and limits](spack_repository_snapshot_admission_research_v1.md)).

The proposed default is **at least 90 elapsed days since the verified upstream
publication of the selected snapshot**, subject to local approval. Do not
assume a quarterly upstream cadence or derive age from the tag's name or Git
author date. Record the publication evidence, observation date, resolved
commit, assessment date, elapsed age, and adopted waiting rule. If publication
age cannot be established, the snapshot does not satisfy the normal rule
without a documented exception. A moved tag or altered content must return to
admission review; it cannot retain approval by keeping the same label.

| Selection case | Proposed disposition |
|---|---|
| Newest snapshot has been published for at least 90 days | Eligible for normal admission review, subject to supported tooling, current findings, and all other checks |
| Newest snapshot is younger than 90 days | Normally assess the preceding supported snapshot; verify its actual age and findings too |
| Preceding snapshot is also too young, unsupported, or unacceptable under current findings | Assess an earlier supported eligible snapshot, hold affected adoption, or request a scoped exception; being one release behind is not enough |
| Urgent security remediation needs a newer snapshot, source version, or local backport | Use expedited review and an authorized exception to the waiting period; do not postpone remediation merely to reach the age threshold |

Select the most recent supported snapshot that satisfies the adopted rule and
the security assessment. Here, supported means compatible with the approved
Spack core/package APIs and within the locally approved maintenance scope,
including a viable path to required fixes; a published tag alone does not
establish continuing upstream maintenance. At admission and again before promotion, check current
advisories and available compromise information against the selected recipes,
sources, dependencies, and externals; retain findings and their dispositions.
Continue monitoring accepted releases. An older snapshot may retain known
vulnerabilities, and a newer one may contain the needed fix. Passage of time
does not resolve an open finding or justify indefinite use of a stale baseline.

The snapshot age applies only to that exact upstream recipe content. A newly
added CSE overlay, backport, patch, source selection, bootstrap component, or
external does not inherit that age. Inventory and review those inputs
separately and record the basis for admitting them. Where a change bypasses the
waiting rule, record the exact delta, reason, evidence, approver, compensating
controls, expiration or follow-up date, and revalidation requirements. Retain
the unchanged baseline evidence without treating it as approval of the change.

This policy supplies the observation period for eligible upstream recipe
inputs; it does not add a second automatic 90-day hold after every build.
Candidate binaries still require the normal build, scan, test, independent
review, and publication gates. **Quarantine for suspected compromise, failed
integrity, or unresolved findings remains a separate containment decision** and
does not expire automatically when the waiting period ends. A separately
mandated artifact hold remains in force until the responsible authority changes
it. The 90-day proposal is a local risk-management choice, not an upstream or
NIST requirement, and does not change currently recorded trial pins by itself.

### Later release admission

A later release may use delta review when the prior approved baseline and its
evidence remain identifiable, retained, and protected from unrecorded changes.
The release process must compare:

* root specifications and the full concrete DAG;
* recipe, patch, resource, and overlay content;
* repository commits and order;
* source origins, versions, commits, and digests;
* variants, providers, targets, compilers, and externals;
* effective configuration and command-line inputs;
* builder baseline and build tools; and
* hardening, test, scan, signing, and publication policy.

Every changed reachable input enters the delta assessment. Select deeper human
review using the recorded risk criteria, including local changes, custom phases,
hooks, new trust sources, external changes, security-sensitive components,
privilege boundaries, and findings. Newly introduced third-party packages enter
that assessment without requiring a blanket manual review of every package.
An unchanged package can inherit its prior recipe-review decision only when the
input identity and effective context are demonstrably unchanged.

### Minimum review record

| Field | Required content |
|---|---|
| Candidate identity | Release ID, root specification, environment, lane, platform, and build ID |
| Effective recipe input | Repository, commit, namespace, package file digest, patches, resources, and override status |
| Snapshot admission | Upstream tag and resolved full commit, verified publication evidence and date, observation and assessment dates, elapsed age, waiting rule, current advisory review, and any exception |
| Change | New, changed, removed, or unchanged relative to the approved baseline |
| Executable behavior | Phases, hooks, commands, environment changes, downloads, write locations, tests, and install actions |
| Source provenance | Origin, immutable identifier, digest, upstream signature status, acquisition time, and mirror object |
| Dependency and external impact | Changed DAG nodes, providers, compiler, MPI, Cray PE, system libraries, and bootstrap inputs |
| Automated evidence | Spack audit results, malware result, vulnerability result, source analysis, secrets result where applicable |
| Human decision | Reviewer, organization, qualifications and independence from candidate preparation, review scope, evidence revision, date, disposition, rationale, required controls, and additional reviewer when required |
| Exceptions | Scope, unmitigated risk, compensating controls, approver, expiration, and retest triggers |

`spack audit` is useful structural lint. It is not a malicious-code review or a
vulnerability scanner
([Spack audit implementation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/audit.py#L180-L223)).

## Assurance gates

The release should move forward only when every applicable gate passes.
Spack runtime and bootstrap admission is a prerequisite to G1: approve staged
inputs before controlled provisioning, then approve the installed supporting
toolchain before its first production solve. Bootstrap preparation may require
its own restricted provisioning and resolution; it must not be deferred until
application-source intake at G2. The admission requirements below apply to
that preparation as well as later production use.

| Gate | Decision | Mandatory evidence | Failure response | Candidate NIST alignment |
|---|---|---|---|---|
| G0 Governance and baseline | Are policy, roles, package criticality, exact tool and repository revisions, and configuration authority approved? | C-SCRM plan; owners; independent-review assignments; snapshot publication/age evidence and waiting-rule decision; review and exception policy; exact commits; repository order; approved launcher and configuration baseline; Spack/Python/bootstrap admission record and installed-toolchain acceptance before G1 | Do not resolve production environments or begin production work | SR-1, SR-2, SR-3, RA-3, RA-9, CM-2, CM-5; SP 800-161; SP 1326 |
| G1 Resolve and review | Is the complete concrete closure and executable input delta understood and approved? | `spack.yaml`; `spack.lock`; evaluated roots, DAGs and hashes; recipe and patch snapshots; change report; review decisions | Reject, revise, or return to review | SR-5, SR-6, SR-10, SR-11, SA-11; SSDF PW.4. SA-9 applies only if CSE relies on an externally operated repository, mirror, scanner, signer, or build service |
| G2 Source intake | Did controlled intake acquire immutable, verified, scanned, and complete source and bootstrap content? | Origins; commits and digests; VCS-commit-to-mirror-archive bindings; separate bootstrap admission; mirror inventory; TLS/checksum results; scanner engine, policy, signature database date and result; acquisition log | Quarantine or reject | SI-3, SI-7, SC-7, AC-6; SSDF PO.5; SP 800-204D by analogy |
| G3 Controlled build | Did a nonprivileged builder use only approved, read-only inputs with no outbound network and no release-key access? | builder identity and baseline; effective scopes; config blame; security environment variables; compiler/module/external inventory; egress-denial evidence; full logs | Destroy candidate output and rebuild | AC-6, CM-2, CM-3, CM-4, CM-5, CM-6, CM-7, SA-10, SA-15; SSDF PO.3, PO.5, PW.6 |
| G4 Validate | Did the candidate pass the security, integrity, functional, ABI, linkage, runtime, numerical, MPI/GPU, and performance checks applicable to its risk tier? | test results; artifact inspection; `spack verify` results; malware and vulnerability results; SBOM; external inventory; documented exceptions | Reject or obtain authorized scoped exception | RA-5, SA-11, SI-2, SI-3, SI-7; SSDF PW.6, PW.7, PW.8; NIST IR 8397. CA-2 applies when the results support a formal assessment of assigned controls |
| G5 Approve and sign | Did a separate release authority approve the exact artifact set and bind it to the evidence? | go/no-go record; artifact digests; package signatures; key fingerprint; authenticated CSE release record; exception acceptance | Do not publish | AC-5, CM-3, CM-5, SI-7, SR-4, SR-9, SR-10, SR-11; SSDF PS.2, PS.3 |
| G6 Publish and provide user access | Is the accepted release frozen and write-controlled, installed through verified cache-only publication, and accessible to normal users through modules? | versioned namespace and retained digests; permission check; backend-appropriate consistency and signing evidence; authenticated approved release-set membership; controlled installation store; no unapproved upstreams; approved externals; cache-only acceptance and negative-fallback tests; module/user-access tests; atomic alias update | Block or withdraw release | CM-5, SI-7, SR-9, SR-11; SSDF PS.2 |
| G7 Monitor and withdraw | Are later CVEs, upstream compromise, scanner intelligence, key status, exceptions, and policy changes monitored and acted on? | periodic scan and review records; findings and dispositions; revocation or withdrawal record; replacement release linkage | Quarantine, revoke, rebuild, and re-release | CA-7, RA-5, SI-2, SI-4, SI-5, IR-4; SSDF RV.1 through RV.3 |

These mappings are a traceability aid. The actual RMF package, assessment
procedures, and AO determinations control.

## Configuration isolation requirements

`SPACK_DISABLE_LOCAL_CONFIG=true` is necessary for the proposed model, but it
does not prove that only CSE configuration is active. In Spack 1.2.2 it disables
the system and user scopes. Spack can still consider defaults, site, plugin,
Spack-instance, environment, custom `-C`, and command-line inputs. Configuration
lists can also merge across scopes
([configuration scope precedence](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst#L55-L134),
[local-configuration and isolation limits](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst#L667-L711)).

The controlled CSE launcher should therefore:

1. invoke a pinned Spack installation;
2. set `SPACK_DISABLE_LOCAL_CONFIG=true`;
3. set `SPACK_USER_CACHE_PATH` to a candidate-specific controlled location;
4. activate an explicit environment by controlled path;
5. control or remove Spack site and plugin configuration;
6. pin and allowlist package repositories and their order;
7. prohibit unapproved custom scopes, `-C` inputs, and security-relevant CLI
   overrides;
8. start from an allowlisted process environment and module state;
9. capture `spack config scopes -p`, `spack config blame`, repository status,
   mirrors, compilers, externals, and bootstrap configuration; and
10. fail if observed inputs differ from the approved baseline.

Spack 1.2.2 describes `spack isolate` as experimental and best effort. It may
assist with reproducibility, but it should not be the security boundary. Host,
container, scheduler, filesystem, identity, and network controls must enforce
the boundary outside Spack.

## Spack installation and bootstrap admission

Installing Spack and preparing its supporting tools are security-relevant
intake and execution steps. They precede application builds and require their
own admission record. This applies to builder, publisher, signing, and managed
installer runtimes, including tools used only to verify or install an accepted
binary cache. A signed application cache does not approve the Spack runtime
that operates on it. The [shared SOP sections 4.4 and 4.5](software_stack_sop_v1.md)
own the operating procedure; [CSE SOP section 4](cse_software_stack_sop_v1.md)
records CSE responsibilities. These requirements remain proposed controls
until adopted and demonstrated on the applicable system.

### Required assessment scope

Keep an inventory separate from the application environment's `spack.lock`
and per-package SPDX documents. Those application records do not establish
the identity or vulnerability status of the complete Spack runtime.

| Component set | Required identity and coverage |
|---|---|
| Pinned Spack installation | Origin, release tag, resolved full commit, retained archive or checkout digest, and any local delta; include bundled/vendored Python libraries and their component identities, not only the top-level Spack version |
| Starting Python and host prerequisites | Actual interpreter path, version, provider or site package identity, supporting libraries, and required system tools; link applicable OS/vendor inventory and advisory evidence, including backport information |
| Bootstrap inputs | Clingo solver, GnuPG, Linux patchelf, and other tools actually required for the role and platform, together with transitive dependencies, source/binary objects, bootstrap metadata, exact digests, origins, and transfer records |
| Provisioned toolchain | Installed supporting-tool inventory and prefixes, external tools actually selected, effective bootstrap/configuration scopes, provisioning logs, installed-file evidence, and the scan and acceptance record bound to that result |

Spack must already have an approved Python interpreter to start. Its bootstrap
configuration treats that running interpreter as an external; it does not
bootstrap a missing starting Python. Tool needs vary by operation and platform,
so the named helpers are assessment examples rather than a mandate to install
every helper everywhere
([Spack bootstrap Python handling](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/bootstrap/config.py#L30-L75),
[bootstrap functions and separate store](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/bootstrapping.rst)).

### Intake, provisioning, and release to use

1. Acquire the pinned Spack content and required supporting inputs through
   the approved intake route. Keep newly acquired content in staging or
   quarantine; verify origin and immutable identity, inventory components, and
   complete the required malware and vulnerability assessment before invoking
   the acquired Spack code or installing its tools. Intake utilities and any
   Spack instance used to prepare the bundle must themselves be approved.
2. Record both malware-scanner coverage and component/vulnerability analysis
   against current approved advisory data. A file scan is not a CVE assessment.
   A Python package-manager inventory alone is not evidence that bundled
   libraries or native bootstrap dependencies were covered. Record component
   matching uncertainty, unsupported formats, exclusions, scan errors, and
   available supplier/backport evidence. Unresolved required findings or
   coverage gaps hold admission unless the responsible authority accepts a
   documented, scoped exception with compensating controls and expiry.
3. Use approved preinstalled prerequisites with bootstrap disabled, or an
   independently admitted local bootstrap bundle. Replace the public default
   source/trust configuration, retain the effective configuration, and enforce
   outbound denial outside Spack during provisioning and operational use.
   Missing content must stop the operation rather than cause public fallback.
   Select already acquired and reviewed local recipe repositories before entering
   bootstrap context; a remote repository descriptor can initiate a fetch even
   when bootstrap metadata is local. Source provisioning also uses those recipes.
   Setting a private bootstrap root alone does not establish these controls.
4. Provision admitted inputs in the restricted, nonprivileged context. Capture
   what was actually installed or selected, including transitive and external
   dependencies, then assess the installed toolchain before the first
   production solve, build, signing, or managed installation that uses it.
   Retain provisioning and readiness evidence; readiness is not security
   acceptance. Required scan coverage, finding disposition, configuration, and
   installed inventory must pass independent review before release to use.
5. Bind acceptance to exact input and installed identities, target compatibility,
   effective configuration, scanner/intelligence versions and dates, reports,
   reviewer, and exceptions. Later builders may reference applicable evidence
   for unchanged admitted content while verifying their installed state.
   Changed Spack code, Python, helpers, dependencies, metadata, or configuration
   require reassessment. New intelligence requires review of retained inventory
   and rescanning or replacement as applicable; elapsed time does not renew
   approval automatically.

Spack's default bootstrap methods include public binary and source locations.
Prebuilt bootstrap packages use SHA-256 values in bootstrap metadata and are
treated as unsigned cache packages. Therefore the metadata must be admitted
alongside the artifacts; its checks are not the signed CSE release-cache trust
model. `spack bootstrap add --trust` grants configuration trust, not a GPG
signature verification result
([default bootstrap methods](https://github.com/spack/spack/blob/v1.2.2/etc/spack/defaults/bootstrap.yaml),
[bootstrap verification](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/bootstrap/core.py#L154-L192)).

Neither a pinned version nor the recipe snapshot's proposed 90-day waiting
period proves that this toolchain is safe. Spack core, Python, newly acquired
bootstrap content, and local changes do not inherit a package-repository
snapshot's age or approval. `spack bootstrap status`, `spack audit`, and
`spack verify` are not substitutes for vulnerability matching against this
inventory. The [Spack security capability note](spack_1_2_signing_sbom_security_note_v1.md)
distinguishes those commands from an external vulnerability scanner.

This draft does not select a scanner or assert that an automated gate exists.
Before adoption, the security owner must name the approved scanning methods,
component-discovery coverage, advisory sources and update cadence, evidence
retention, disposition authority, and reassessment rules. The stop conditions
above apply even when the process is performed manually.

## Source intake and scanning

The fetch phase should be the only phase with outbound access. It should create
a closed source set for the reviewed concrete graph, including archives, VCS
content, patches, resources, submodules, generated dependencies, and bootstrap
content. For URL sources, strong checksums are mandatory. For VCS sources, use
full immutable commits and retain the acquired archive or checkout digest
([Spack checksum rules](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L542-L564),
[Git provenance rules](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L618-L648)).

Spack mirrors support offline source preparation, including creation from a
concrete environment
([Spack mirror documentation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/mirrors.rst#L12-L77)).
A configured mirror does not prove that a build could not fall back to a public
origin or that an upstream build script did not make its own download. Outbound
network denial must be enforced and tested outside Spack. Missing approved
content must cause a build failure. Spack's ordinary fetcher path retains the
public origin after caches and mirrors
([Spack stage and fetcher behavior](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/stage.py#L555-L600)).

VCS-backed sources require an additional control. When the original source is
Git or another VCS but a mirror supplies an archive, Spack 1.2.2 cannot prove
that the archive is equivalent to the VCS checkout because the recipe does not
contain a tree-archive hash. Spack warns and skips the ordinary archive checksum
verification for that mirror object. CSE must retain evidence that binds the
approved full commit to the exact archived mirror object and its independently
calculated digest
([Spack VCS mirror verification limitation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/stage.py#L669-L685)).

Bootstrap remains a separate supply-chain path governed by
[Spack installation and bootstrap admission](#spack-installation-and-bootstrap-admission).
An application-source mirror or reviewed application lock does not replace
the earlier toolchain admission and installed-state assessment.

If Trellix or another organization-approved scanner is used, retain at least:

* the source object digest and origin;
* scanner product, engine version, policy, and command or job identity;
* signature or intelligence database version and timestamp;
* scan time, result, exclusions, errors, and reviewer disposition; and
* quarantine, exception, or acceptance decision.

Scan the staged source and the installed candidate. Reevaluate retained release
inventory when scanner intelligence or vulnerability data changes. One intake
scan is not a continuing assurance claim.

## Independent review, including reviewers outside CSE

The normal two-person process can use qualified CSE personnel. The CSE release
authority, system owner, or responsible security authority may designate or
request a qualified reviewer outside CSE when independent organizational
scrutiny, specialist knowledge, a significant finding, or a conflict of
interest warrants it. That reviewer may fill the independent technical-review
role or provide an additional assessment with a recorded scope. No blanket
requirement for an outside reviewer on every release is introduced.

Give the reviewer the exact candidate identity and the applicable input,
change, scan, test, and exception records, with a way to ask for evidence and
record findings and their disposition. Independence requires freedom from
preparing or modifying the candidate being approved; outside affiliation alone
does not establish it. Record the reviewer's organization, relevant
qualifications, scope, independence, findings, and decision. If a reviewer also
changes candidate inputs or outputs, obtain an independent review of the
revised candidate before release.

Use approved read-only evidence access or an authorized evidence transfer;
outside review does not require membership in the CSE build-write group or
access to release keys. Role assignment does not automatically grant build,
signing, publication, or risk-acceptance authority. Those authorities remain
explicitly assigned under the local process. An unresolved required review
holds affected publication until its findings receive an authorized disposition.

## Controlled build requirements

The designated build owner uses a nonprivileged identity. A second qualified
person, within or outside CSE as assigned above, independently reviews the exact
candidate and may also perform the
delegated release/signing role in a separate controlled context. This does not
require a third routine team member. Build execution has read-only access to
approved inputs,
write access only to candidate work and output locations, no routine ability to
alter the admitted mirror or baseline, no outbound network access, and no
access to the release private key.

The release record should identify the builder host or image, OS, architecture
and microarchitecture target, kernel-relevant constraints, Spack revision,
package-repository revisions, compiler and Cray PE state, MPI provider,
bootstrap tools, externals, environment variables, and complete build logs.
`spack.lock` is central evidence, but it is not a complete build attestation or
a guarantee of bit-for-bit reproducibility
([Spack manifest and lock](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L39-L47),
[lockfile recreation qualifications](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L84-L121)).

An approved source set should be built without `--dirty`, `--no-checksum`,
`--insecure`, unsigned ordinary-release-cache, signature-bypass, or unapproved
configuration options. The separately admitted bootstrap path described above
is not evidence that unsigned ordinary release packages are acceptable. Any
required exception must be visible in the candidate record and approved before
promotion.

## Validation requirements

Validation depth should follow package criticality, exposure, privilege,
language, compiler, and lane. The complete program may include:

* package and installation tests;
* command startup and representative functional tests;
* library, RPATH/RUNPATH, ABI, symbol, and unintended-system-dependency checks;
* serial, OpenMP, MPI, multi-node, GPU, and mixed-language tests where
  applicable;
* numerical correctness, reproducibility, and restart or checkpoint checks;
* input parser, archive, protocol, and file-format negative tests;
* malware scanning of installed output;
* software-composition and vulnerability analysis against the release SBOM
  and separate external inventory;
* static, dynamic, fuzz, sanitizer, and hardening checks selected by risk; and
* performance, memory, startup, launch-scale, and scaling comparisons for
  security controls that may affect HPC behavior.

Spack 1.2 writes a per-install SPDX 2.3 document. Its generator sets
`filesAnalyzed` to false and skips an external root. The result is useful
inventory, but it is not a release-wide SBOM, a malware result, a CVE result,
or build provenance
([Spack 1.2 release](https://github.com/spack/spack/releases/tag/v1.2.0),
[SBOM generator](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/hooks/sbom_generate.py#L53-L170)).

Preserve and hash the candidate-production SBOM before build-cache publication
and bind that exact copy in the authenticated CSE release record. A build-cache
installation runs post-install hooks that regenerate the SPDX file and the
install manifest using the managed installation's time and local recipe
metadata. That installation's `.spack/sbom/spdx-2.3.json` is useful local
inventory,
but it should not be treated as cryptographically identical to the retained
release copy
([binary install hooks](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/binary_distribution.py#L2163-L2174),
[hook ordering](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/hooks/__init__.py),
[SBOM hook](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/hooks/sbom_generate.py)).

`spack verify manifest` can detect changed installed files and `spack verify
libraries` can detect missing or unintended library dependencies. These are
integrity and linkage checks, not vulnerability scanners
([Spack verification documentation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/advanced_topics.rst#L53-L104)).

## Security evidence answers different questions

| Evidence or control | What it establishes | What it does not establish |
|---|---|---|
| TLS during acquisition | Confidentiality and server authentication according to the configured trust store | That the server content is benign or the selected origin is approved |
| Source checksum | The acquired bytes match the admitted digest | Publisher identity, intent, absence of vulnerabilities, or review approval |
| Upstream signature | A holder of the corresponding upstream key signed the content | That the signer or content is trustworthy for CSE without key and publisher due diligence |
| Recipe and patch review | Identified executable packaging behavior was reviewed at the stated depth | Complete safety of upstream source or generated build logic |
| Malware scan | Content did not trigger the selected engine, policy, and intelligence at that time | Absence of unknown, obfuscated, logic-level, or later-discovered threats |
| Vulnerability or SCA scan | Known component or vulnerability matches and dispositions at that time | Malware absence, exploitability certainty, or complete component discovery |
| Static and dynamic analysis | Selected defect classes in analyzed code or executions | Complete path coverage or absence of other defects |
| Functional and numerical tests | Observed behavior met defined cases and tolerances | Absence of malicious behavior or behavior outside test coverage |
| SBOM | Component and relationship inventory to the tool's available metadata | Safety, approval, vulnerability disposition, malware absence, or complete external inventory |
| Lockfile | A fully concrete Spack dependency graph | Signature, approval, host-tool identity, complete externals, or bit-for-bit reproducibility |
| Build attestation | Recorded builder, inputs, parameters, and output digests at the claimed assurance level | Safety of those inputs or builder unless their trust is separately established |
| Build-cache signature | CSE's trusted key signed the described package manifest and its referenced content digests | Safety before signing or authenticity of an unsigned release index |
| Install integrity manifest | Installed files still match the recorded post-build state | That the original recorded state was safe |

## Signing, controlled publication, and user access

Designated operators perform the cache-installation steps in this section;
normal users access the resulting accepted installation through modules.
A frozen release has a versioned identity, retained digests, controlled write
authority, and a rule against editing accepted bytes in place. The CSE SOP
retains group management access, so directory permissions alone do not prove
storage-enforced immutability. Any required read-only snapshot or WORM storage
is a separately selected and demonstrated control.

Spack build caches contain installed prefixes and metadata. Spack 1.2.2 can
sign binary package manifests, configure a mirror as signed, select a signing
key, and verify signatures during installation
([build-cache creation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst#L27-L38),
[signing controls](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst#L229-L309)).
`spack install --use-buildcache only` prevents fallback to a source build
([cache-only consumption](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst#L99-L137)).

That option governs packages Spack must install. It does not retroactively
verify signatures for a matching hash already present in the local store or an
upstream store, and declared externals do not come from the cache. The managed
installer must therefore use a clean or dedicated controlled store, prohibit
unapproved upstream stores, separately admit and inventory externals, and
verify that the requested concrete DAG hashes are members of the approved CSE
release record before installation
([existing-install decisions](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/new_installer.py#L1792-L1812),
[external and installed-spec handling](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/installer.py#L2271-L2278)).

CSE should:

* keep the private release key outside the builder and ordinary workspaces;
* authorize a separate release role to use it only after the validation gate;
* distribute the complete public-key fingerprint through a controlled channel;
* trust only designated CSE keys, not every key downloadable from a mirror;
* configure the authoritative mirror as signed;
* prohibit unsigned pushes and signature-verification bypasses;
* record the release key fingerprint and signature result;
* publish into a new versioned, write-controlled release namespace and retain its digests;
* update any human-friendly alias atomically after the release passes; and
* revoke or withdraw by state change and replacement release, not by modifying
  installed files in place.

Spack 1.2.2 explicitly states that build-cache index manifests are not yet
signed
([build-cache index caveat](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst#L676-L704)).
The existing CSE signing process is described in the
[signing and security note](spack_1_2_signing_sbom_security_note_v1.md#build-cache-signing-and-trust)
and the [shared signing procedure](software_stack_sop_v1.md#procedure-signing):
the release-signing identity signs the approved package artifacts. The existing
[release-manifest contract](../schemas/release-manifest-v1.json) records release
inputs, build evidence, and build-cache information. Its `buildcache.signed`
field describes package-cache signing; it is not a digital signature on the
manifest file.

The CSE release process must not say that the entire index is authenticated by
native Spack signing. The SOP also requires an authenticated record of the
approved release set, with its authentication method and evidence recorded in
the operating baseline. A separate digital signature on that release record is
one optional mechanism, subject to applicable requirements. It is an additional
protection, not an unresolved requirement of the documented package-signing
procedure or a replacement for the existing release-manifest contract. If
selected, the signed record binds:

* release ID and approval state;
* expected root specifications and complete DAG hashes;
* package-manifest and content-blob digests;
* catalog and build-cache index digests;
* platform, target, compiler, provider, and external identities;
* release evidence location and digest;
* signing identity and timestamp; and
* prior or replacement release relationships.

`spack buildcache check-index --verify all` remains useful as a mirror
consistency check. It does not replace package signature verification or
authentication of the approved release record. The verified record must constrain
the expected DAG hashes before installation. When the signed-manifest option
is selected, verify its signature and enforce its permitted hash set. Creating
that record alone does not prevent index-based omission, selection of a
different but validly signed artifact, or rollback if the managed installer
does not enforce the binding.

Native Spack signing is also backend-dependent in 1.2.2. When an `oci://`
build-cache push requests signing, Spack warns and forces the push to unsigned.
OCI caches also lack the index views used by `spack buildcache check-index`.
An OCI or GitLab container registry cannot satisfy this document's native
Spack-signature gate unless CSE implements a separate OCI signing mechanism and
mandatory verification that binds the same release evidence. The safer initial
authority is a supported filesystem, HTTPS, or object-store Spack cache with
native package signing
([Spack OCI signing behavior](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/buildcache.py#L516-L532),
[OCI index limitation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/buildcache.py#L1031-L1045)).

### Cryptographic compliance caution

FIPS 140-3 defines requirements for cryptographic modules, and the CMVP
validates modules. It does not validate package managers or supply chains. A
successful GPG signature does not, by itself, establish that signing or
verification used a CMVP-validated module in an approved mode. When
cryptography is required to protect sensitive information or by an assigned
control or local policy, CSE must identify the exact implementation, version,
module certificate, operating environment, approved mode, key generation and
storage path, and verification path. Do not label ordinary Spack GPG use as
FIPS compliant without that evidence
([FIPS 140-3](https://csrc.nist.gov/pubs/fips/140-3/final),
[NIST Cryptographic Module Validation Program](https://csrc.nist.gov/projects/cryptographic-module-validation-program)).

The CMVP transition schedule states that FIPS 140-2 modules on the Active list
may be used for new systems only through September 21, 2026. They then move to
the Historical list for existing-system use under the applicable policy. This
near-term date should be checked before selecting a signing or verification
module.

FIPS 199 and FIPS 200 address system categorization and minimum system-security
requirements. They do not certify Spack, a recipe repository, or a build cache
([FIPS 199](https://csrc.nist.gov/pubs/fips/199/final),
[FIPS 200](https://csrc.nist.gov/pubs/fips/200/final)). DoDI 8510.01 directs
DoD categorization and control selection through CNSSI 1253 and DoD-specific
assignments and overlays. Confirm that operative process rather than treating
FIPS 199 or FIPS 200 as a direct certification mechanism for this workflow.

## Package-manager comparison

This table compares package production and managed installation. In the CSE
column, the cache installer is a designated operator; normal users receive
module access to the resulting accepted software.

| Dimension | Ordinary Spack source build | Governed CSE Spack release | Curated RPM/DNF consumption | Governed Conda channel consumption |
|---|---|---|---|---|
| Installer receives | Source plus recipe-driven local build | Prebuilt CSE package from approved cache | Prebuilt RPM from configured repository | Prebuilt Conda package from selected channel |
| Package build phases and upstream build system execute on installing system | Normally yes | No for packages installed from the cache. The approved recipe module can still be imported and Spack post-install hooks run | No for a prebuilt RPM, although install or transaction scriptlets may execute | No build recipe for a prebuilt package, although link or activation scripts may execute |
| Main trust anchor | Public recipes, upstream sources, local configuration, local builder | CSE intake, builder, evidence, approval, key, and authenticated release record | Distribution or repository governance and trusted package or metadata keys | Channel governance and whatever signature or trust controls are configured |
| Dependency identity | Concrete DAG and package hashes | Approved lock, DAG, artifact manifest, and external inventory | Repository metadata and RPM dependencies | Channel metadata, package records, and environment solution |
| Integrity mechanism | Source checksums and local install metadata | Source digests, evidence, signed package manifests, and authenticated CSE release record | RPM signatures/digests and configured DNF package or repository checks | Package and metadata checks plus channel-specific signature controls when configured |
| Executable supply-chain surface | Spack Python, recipe, patches, resources, upstream build system, tools, and externals | Build phases are confined to CSE intake/build. Approved installer-side Spack core, repositories, hooks, and installation behavior remain in the managed installation boundary | Upstream distro build pipeline plus RPM transaction scriptlets on consumer | Upstream channel build pipeline plus link and activation scripts on consumer |
| Principal risk if poorly governed | Recipe/source compromise, public fallback, configuration injection, builder compromise | CSE pipeline, reviewer, signer, key, external dependency, or release-record compromise | Repository, build system, maintainer, key, metadata, or scriptlet compromise | Channel, build system, maintainer, metadata, link script, activation script, or trust-configuration compromise |

DNF exposes package signature and repository metadata checks as configuration
controls
([DNF configuration reference](https://dnf.readthedocs.io/en/latest/conf_ref.html#gpgcheck)).
RPM signatures and digests support integrity and signer verification, while RPM
packages may include executable scriptlets
([RPM signatures and digests](https://rpm.org/docs/4.20.x/manual/signatures_digests.html),
[RPM scriptlets](https://rpm.org/docs/latest/manual/triggers.html)).

Conda-build recipes execute shell or batch build scripts. Packages may contain
link scripts that run during installation or removal, and may install activation
scripts that are sourced or called when an environment activates
([Conda build scripts](https://docs.conda.io/projects/conda-build/en/stable/resources/build-scripts.html),
[Conda link scripts](https://docs.conda.io/projects/conda-build/en/stable/resources/link-scripts.html),
[Conda activation scripts](https://docs.conda.io/projects/conda-build/en/stable/resources/activate-scripts.html)).

The supported conclusion is not that all four modes have equal risk. Ordinary
Spack source building has a larger local build-plane trust surface than
consuming a curated binary. The supported conclusion is that repository
governance and the configured consumption path determine the comparison. A
controlled CSE binary-promotion process is the relevant analogue to a curated
RPM or Conda channel.

## Compiler hardening for HPC

### Policy principle

Compute-node isolation reduces some likelihood and blast radius. It does not
eliminate memory-corruption risk. During an allocation, a process may retain
whatever access the job identity and allocation grant, including access to
persistent storage, peer ranks, interconnects, devices, services, and output
data. A defect can corrupt results and checkpoints, destroy accessible data,
consume an allocation, affect distributed ranks, or participate in an exploit
chain. Post-job sanitization cannot undo an impact that occurred during the
job.

NIST SP 800-223 identifies specialized HPC software, compilers, libraries,
communications, shared access, compute, and data zones and recommends measuring
security controls against performance. NIST SP 800-234 provides an HPC overlay
intended to be practical and performance-conscious. It calls for zone-specific
tailoring and recognizes scanner and integrity-check scaling effects
([NIST SP 800-223](https://doi.org/10.6028/NIST.SP.800-223),
[NIST SP 800-234](https://doi.org/10.6028/NIST.SP.800-234)).

The following CSE policy is a local implementation proposal informed by the
NIST guidance. SP 800-223 and SP 800-234 do not prescribe these package tiers,
compiler profiles, benchmark methods, or waiver thresholds. The appropriate
policy is not to inject every available hardening flag into every package. It
is to maintain approved, compiler- and language-specific profiles, test their
operational effects, and document narrow exceptions.

### Risk tiers

| Tier | Typical software | Production disposition |
|---|---|---|
| A | Access-node, management, network-facing, parser, scheduler-adjacent, publication, or privileged tools | Apply an approved high-assurance production profile after correctness, ABI, platform, and performance qualification. Evaluate PIE, strong stack protection, fortification, RELRO/NOW, non-executable stack, stack-clash protection, and supported hardware control-flow protection as applicable |
| B | Site-wide shared libraries and applications, especially those processing user-controlled content | Retain low-cost baseline controls. Qualify stronger controls for ABI, plugin, MPI, GPU, startup, and performance effects. A shared library inherits the risk of its highest-risk consumer |
| C | Closed numerical kernels using trusted input under exclusive, nonprivileged compute allocation | Retain qualified low-cost controls. Permit an exception only for a demonstrated correctness, compatibility, or statistically supported performance problem with compensating controls |
| D | Restricted test and quarantine builds | Select applicable, supported sanitizers, fuzzing, bounds checks, race detection, and other diagnostics in separate validation builds. Do not publish sanitizer- or diagnostic-instrumented binaries as normal production or performance artifacts |

### Control disposition

| Control | Proposed disposition | Qualification concern |
|---|---|---|
| PIC for shared libraries | Require PIC for objects incorporated into ELF shared objects, including static archives consumed by shared objects, using the exact compiler's supported syntax. Verify absence of text relocations. PIC is a linkage enabler, not a standalone memory-safety control | Non-PIC assembly, TLS models, linker limitations, and compiler-specific syntax. Ordinary fully static executables do not require PIC; static PIE is a distinct case |
| PIE for executables | Strong candidate for tiers A and B; measure tier C hot executables | Fixed-address assumptions, mixed objects, old build systems, launcher and startup behavior; OS ASLR must be enabled for address randomization |
| Strong stack protector | Strong candidate for supported C/C++ tiers A and B; evaluate broader use | Language and compiler coverage, prologue/epilogue cost, Fortran behavior, and silently ignored options |
| `_FORTIFY_SOURCE` | Use an approved level only for translation units, optimization modes, and libc/compiler combinations that support it. It protects selected libc calls, not general C/C++ memory accesses or Fortran arrays | Object-size analysis and optimization, libc/compiler version, source/runtime compatibility, and level 3 dynamic-object-size cost |
| RELRO | Strong candidate for dynamic executables and shared objects. Validate emitted `PT_GNU_RELRO` and loader behavior | Linker and loader compatibility. RELRO alone is not full RELRO; immediate binding remains a separate control |
| Immediate binding or NOW | Strong candidate for tier A; benchmark launch and plugin-heavy paths elsewhere | Startup, `dlopen`, optional symbols, rank count, and plugin behavior |
| Non-executable stack | Strong candidate after correcting objects that request an executable stack | Nested-function trampolines, JIT behavior, hand assembly, and missing metadata |
| Stack-clash protection | Use where the exact compiler and target support it and tests pass | Target support, large or variable stack frames, and Fortran automatic arrays |
| CET, BTI, or PAC | Risk-based, platform-specific qualification | Matching compiler instrumentation and object metadata, CPU, kernel, loader, and compatible assembly and vendor objects |
| Compiler control-flow integrity | Risk-based qualification, with no universal cross-DSO assumption | LTO, visibility, whole-program requirements, plugin and MPI boundaries, mixed languages, vendor libraries, and experimental cross-DSO behavior |
| ASan, TSan, MSan, LSan, and broad UBSan | Restricted validation builds by default | Significant time or memory overhead, runtime dependencies, static-link limits, MPI-scale output, and production-support limitations |

Do not adopt GCC `-fhardened` as a universal Spack flag. GCC documents it as a
moving set whose exact contents can change by compiler release. It is not a
portable C, C++, Fortran, Clang, CCE, MPI, GPU, static, and shared-library
policy
([GCC instrumentation options](https://gcc.gnu.org/onlinedocs/gcc-15.2.0/gcc/Instrumentation-Options.html)).

### CCE qualification

Record the exact CPE and CCE version and whether the build used Cray PE wrappers
`cc`, `CC`, and `ftn` or direct drivers such as `craycc` and `crayCC`. The Cray
PE wrappers use the active PE/module environment and add the associated compile
and link options and libraries; direct drivers bypass that PE integration. CCE
C/C++ compiler lineage does not prove that a GCC flag works for Cray Fortran.
HPE's public `crayftn` manual documents PIC and experimental address and thread
sanitizer behavior, but does not establish a general GCC-equivalent Fortran
hardening set
([HPE CPE and CCE overview](https://cpe.ext.hpe.com/docs/latest/getting_started/CPE-CCE-Overview.html),
[HPE `crayftn` manual](https://cpe.ext.hpe.com/docs/latest/cce/man1/crayftn.1.html)).

These HPE pages were reviewed as CPE 26.03 and CCE 21.0.0 documentation; the
`crayftn` page is dated November 13, 2025. Because the `/latest/` URLs are
mutable, retain a snapshot and digest with the policy decision. Blueback's
actual CPE/CCE patch level and driver behavior remain authoritative.

For every required flag, probe each language and production driver actually
used by the package or profile. Fail if a required option is rejected or
silently ignored. The absence of a public `crayftn` stack-protector entry means
CSE must not assume that GCC's option works. Require an effective artifact or
runtime probe, not only a zero compiler exit status. Validate shared and static
linkage separately. Do not infer CCE coverage from a successful GCC build.

### Qualification and waiver evidence

For each selected hardening qualification case, record the `package@version`,
compiler and version, language, architecture, lane, and linkage model. Select
cases by the proposed control, affected package groups, and risk; retain the
basis for representative coverage or reuse of applicable baseline evidence.
For each selected case:

1. build the baseline and hardening candidate from identical approved source,
   lockfile, dependency graph, and configuration, changing only the hardening
   delta;
2. retain the exact compiler and linker invocations and option-support probes;
3. run functional, numerical, ABI, mixed-language, plugin, serial, OpenMP, MPI,
   multi-node, and GPU tests that apply;
4. inspect applicable ELF headers, dynamic tags, and program headers using
   expected results defined for the linker and linkage model. Examples include
   `PT_GNU_RELRO`, `BIND_NOW` or NOW dynamic flags, non-executable
   `PT_GNU_STACK`, absence of TEXTREL and unexpected read-write-execute
   segments, and CET or BTI GNU properties together with runtime capability.
   `ET_DYN` alone does not prove PIE because shared objects also use it, and
   ordinary static binaries have no lazy dynamic binding;
5. benchmark with the same allocations, input, affinity, clocks, rank layout,
   toolchain, and storage conditions, randomizing paired order and reporting
   variability rather than one run;
6. measure startup and `dlopen` separately from steady-state computation and
   scaling; and
7. archive raw results, tool versions, artifacts, reviewer decisions, and
   predeclared site or mission thresholds.

A waiver must name the exact control, package, version, compiler, language,
architecture, lane, failure or regression, unmitigated threat, compensating
controls, affected consumers, owner, approver, expiration, and retest triggers.
There should be no blanket CCE exemption and no blanket HPC-performance
exemption.

## NIST and DoD traceability

| Lifecycle objective | Candidate controls and guidance | CSE evidence |
|---|---|---|
| Governance and C-SCRM plan | SP 800-53 SR-1, SR-2, SR-3, RA-3, RA-9; SP 800-161; SP 1326; DoDI 8510.01 | roles, criticality tiers, risk and exception policy, AO-confirmed tailoring |
| Source, supplier, and recipe due diligence | CM-10, SR-5, SR-6, SR-10, SR-11, SA-11; SSDF PW.4; DoD OSS memorandum. SA-9 applies when an externally operated service is relied upon | source and repository admission, reachable-delta review, provenance, maintainer and dependency assessment |
| Controlled configuration and build | AC-6, CM-2, CM-3, CM-4, CM-5, CM-6, CM-7, SA-10, SA-15; SSDF PO.3, PO.5, PW.6 | launcher, scope evidence, exact pins, least-privilege builder, egress denial, build baseline and logs |
| Integrity and provenance | CM-3, CM-8, SA-10, SI-7, SI-12, SR-4, SR-9, SR-11; SSDF PS.2 and PS.3; SP 800-204D by analogy. AU-3, AU-9, and AU-11 apply when build and release actions and records are defined as auditable events in the system logging strategy | source and artifact digests, lockfile, SBOM, external inventory, build record, signed package manifests and an authenticated release record |
| Verification and hardening | RA-5, SA-11, SI-2, SI-3, SI-7; SSDF PW.6, PW.7, PW.8; NIST IR 8397. CA-2 applies when evidence supports formal assessment of assigned controls | functional, numerical, linkage, multi-node, security, scanner, vulnerability, hardening, and performance results |
| Promotion and separation of duties | AC-5, CM-3, CM-5, SR-9, SR-10, SI-7; SSDF PS.2 and PS.3 | independent go/no-go, protected signing key, versioned write-controlled namespace, retained digests, atomic alias, approvals and exceptions |
| Continuous monitoring and response | CA-7, RA-5, SI-2, SI-4, SI-5, IR-4; SP 800-161; SSDF RV.1 through RV.3 | periodic rescans, intelligence review, finding dispositions, revocation, withdrawal, replacement release |
| HPC performance-conscious tailoring | SP 800-223; SP 800-234 | zone and package risk tiers, controlled A/B builds, correctness and performance data, expiring exceptions |
| Classified transfer | DoDI 8540.01 plus destination AO, CDS, media, and enclave procedures | authorized transfer record, post-transfer hash/signature verification, destination scan and approval, enclave-controlled key if required |

NIST SP 800-234 is an optional HPC overlay built from the SP 800-53B moderate
baseline. It is not automatically the assigned DoD overlay. Reconcile any use
of it with CNSSI 1253, the DoD RMF Knowledge Service, the system's selected
controls, and AO-approved tailoring. Its zone-aware and performance-conscious
guidance supports the local CSE proposal, but it does not prescribe CSE's
package tiers, compiler profiles, A/B builds, or waiver thresholds.

NIST SP 800-53 is a flexible control catalog, and DoDI 8510.01 establishes the
DoD RMF and AO risk-decision structure. The control set actually assigned to
the system takes precedence over this candidate mapping
([NIST SP 800-53 Rev. 5, Release 5.2.0](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final),
[DoDI 8510.01](https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodi/851001p.pdf)).

NIST SP 800-204D focuses on cloud-native CI/CD. Its artifact, attestation,
isolation, repository, and promotion-gate concepts are used here by analogy,
not presented as HPC-specific requirements
([NIST SP 800-204D](https://doi.org/10.6028/NIST.SP.800-204D)).

## Current federal policy context

OMB M-26-05, issued January 23, 2026, rescinded M-22-18 and M-23-16. It requires
agencies to maintain complete software and hardware inventories and to develop
assurance processes matched to mission and risk. The government-wide secure
software attestation form developed under the now-rescinded M-22-18 regime
remains available as an optional tool. Contractual SBOM provisions are also
optional government-wide tools unless another authority, Component, AO,
acquisition, or contract requires them
([OMB M-26-05](https://www.whitehouse.gov/wp-content/uploads/2026/01/M-26-05-Adopting-a-Risk-based-Approach-to-Software-and-Hardware-Security.pdf)).

This change does not reduce the need for evidence. It means the CSE response
should be anchored in the system's current RMF package, C-SCRM plan, mission
risk, and AO decision rather than an outdated claim that one universal federal
attestation workflow is mandatory.

## Release evidence package

| Evidence group | Minimum contents |
|---|---|
| Release control | release ID, status, timestamps, owners, reviewers, approvers, versioned path, retained digests, write authority, predecessor, replacement, and withdrawal state |
| Tool and recipe provenance | Spack core and package-repository commits, origins, verification, snapshot publication and age evidence, waiting-rule decision and exceptions, overlay commits and diffs, repository namespaces and order, controlled launcher version |
| Spack runtime and bootstrap admission | Exact Spack content and bundled-library inventory; starting Python and host-prerequisite identities; bootstrap sources, binaries, metadata and transitive dependencies; staged and installed scan/SCA reports and coverage gaps; provisioned inventory and configuration; digest-bound independent acceptance; builder, publisher and installer applicability |
| Independent review | Reviewer identity and organization, qualifications, independence, assigned scope, exact evidence revision, findings and dispositions, approval or hold; outside-CSE participation when assigned |
| Environment identity | `spack.yaml`, `spack.lock`, evaluated root specs, full DAGs and hashes, variants, providers, architecture, lane, view and module configuration |
| Effective configuration | `spack config scopes -p`, config-blame evidence, approved scope digests, repositories, mirrors, bootstrap configuration, compilers, externals, and security-relevant environment variables |
| Source intake | source, patch, resource, submodule, VCS and bootstrap inventory; URL or origin; immutable identifier; digest; VCS-commit-to-mirror-archive binding; upstream signature status; acquisition log; mirror location; scan evidence |
| Builder provenance | builder identity and baseline, OS, host or image ID, CPE and module state, compiler and linker, target, build tools, network-policy evidence, start/end times, and full logs |
| Validation | package and functional tests, ABI and linkage, runtime, numerical, serial, OpenMP, MPI, multi-node, GPU, artifact inspection, scanner and vulnerability results, performance results and dispositions |
| Inventory | per-install Spack SPDX documents, release-level component inventory, separate system-external inventory, licenses, known vulnerabilities and dispositions |
| Publication | package-manifest and blob digests, signature verification, trusted key fingerprint, backend-appropriate consistency result, catalog and index digests, authenticated CSE release record, managed-installation and upstream-store policy, external admission, permission checks, module-user acceptance |
| Exceptions and monitoring | exception scope and residual risk, compensating controls, approval and expiry, retest triggers, rescan history, later findings, revocations, withdrawals, and replacement linkage |

The evidence package should be write-protected after approval. Corrections and
minor changes create a new candidate, new evidence, new checksums, new approval,
and new release. Restricted candidates should also be regenerated rather than
manually edited when their evidence is expected to support publication.

## Delivery and destination acceptance boundaries

Use the shared SOP's mirror and transfer procedure whenever a destination
cannot directly retrieve all required source archives or supporting inputs.
This includes partial external-access restrictions and fully air-gapped
systems. Deliver admitted sources for destination builds, compatible approved
signed cache artifacts for managed installation, or both for the recorded
execution modes. Retain destination configuration, compatibility, receipt,
validation, and approval evidence. A sister-system relationship alone does not
establish acceptance.

The classified workflow is not simply a file copy. The approved unclassified
build cache may be the source set for transfer, but the destination must apply
its authorized cross-domain or media procedure. At minimum, the destination
should verify digests and signatures after transfer, rescan under enclave
policy, confirm platform and external compatibility, review revocation status,
approve the artifact set, and re-sign under enclave-controlled keys if required.

DoDI 8540.01 governs cross-domain solutions in its scope. Offline media and
destination procedures may impose additional requirements that are not public
and are not defined here
([DoDI 8540.01](https://www.esd.whs.mil/portals/54/documents/dd/issuances/dodi/854001p.pdf)).

## Residual risk

The controlled process reduces risk but does not eliminate:

* deliberately malicious upstream source or build logic that survives review
  and scanning;
* scanner false negatives, incomplete vulnerability data, and unknown defects;
* compromised build hosts, credentials, dependencies, or trusted insiders;
* weak or vulnerable compilers, Cray PE components, MPI, system libraries, and
  other externals;
* signing-key compromise, incorrect trust bootstrap, or approval error;
* incomplete SBOM metadata and external inventory;
* mismatch between build and target systems;
* non-reproducible outputs even when the concrete Spack DAG is unchanged;
* unsigned Spack cache index semantics without an authenticated approved
  release record; and
* vulnerabilities discovered after publication.

Residual release risk is handled by the authority defined in the authorized
system's configuration- and change-management process. Significant changes or
risks outside existing authorization conditions are elevated to the AO as
required. CSE provides the evidence and enforces the release process; it does
not self-declare system compliance.

## Control clarifications

These topics explain the proposed controls. They are not statements attributed
to the unavailable organizational white paper. Use them in a response only
where the actual paper or the proposed operating model makes them relevant.

### Recipe admission and review depth

Recipes are executable inputs. CSE proposes admission of an exact repository
baseline, inventory of the complete selected closure, automated checks, and
targeted manual review of local, exceptional, changed, or higher-risk inputs.
Every reachable change enters the assessment; manual inspection is selected by
recorded criteria. Retained baseline evidence supports unchanged inputs when
its context remains applicable. Any stricter assigned review requirement
should identify the content, depth, reviewer qualification, and accepted
evidence.

### Comparison of governed installation processes

A consumer of a well-governed signed binary repository has a smaller local
build-plane trust surface than an ordinary Spack source builder. That is a
valid distinction. It does not prove that Yum/DNF, RPM, or Conda content is
inherently safer. Their recipes, upstream pipelines, transaction scripts, link
scripts, channels, maintainers, metadata, and keys remain supply-chain inputs.
The CSE managed installer uses the governed binary-repository model; ordinary
users access the accepted installation through modules.

### Contribution of checksums and SBOMs

Checksums establish content identity relative to an admitted
digest. SBOMs support inventory and analysis. Neither proves benign intent,
absence of vulnerabilities, correct build behavior, or approval.

### Compiler-hardening applicability

NIST guidance supports risk-informed controls, approved build configurations,
testing, and documented decisions. Assigned RMF controls or local policy may
make particular practices mandatory. NIST does not publish one universal GCC,
CCE, Fortran, MPI, and GPU flag set. CSE should implement a qualified baseline,
stronger profiles for higher-risk software, validation builds with diagnostic
controls, and narrowly scoped expiring exceptions supported by correctness and
performance evidence.

### Contribution of exclusive compute allocation

Exclusive allocation and post-job sanitization are valuable compensating
controls. They do not protect a user's persistent data, peer ranks, output,
credentials, interconnect, devices, or scientific results during the job.
They reduce selected threats; they do not eliminate the need for proportionate
hardening and testing.

### Continuing assurance after intake

Intake scanning addresses the scanner's knowledge at acquisition
time. Later CVEs, source compromise, scanner updates, key compromise, and new
threat intelligence require monitoring, rescanning, disposition, withdrawal,
and replacement procedures.

## Conditions to resolve for security review and production use

1. Confirm the system's categorization, NSS status, selected control baseline,
   overlays, CCIs, assignment values, and AO-specific conditions.
2. Confirm whether DoDI 5200.44 applies and identify designated critical
   components.
3. Approve package criticality tiers, recipe-review depth, the proposed 90-day
   snapshot waiting rule and urgent-update exceptions, reviewer qualifications,
   outside-CSE review assignment, and exception authority.
4. Name the approved source and binary scanners and vulnerability/SCA methods,
   including discovery and advisory coverage for Spack's bundled libraries,
   starting Python, bootstrap tools and transitive dependencies. Define update
   cadence, evidence fields, coverage-gap and false-positive disposition,
   quarantine rule, installed-toolchain acceptance, rescan cadence, and
   remediation timing for builders, publishers, and managed installers.
5. Select the authoritative build-cache backend and define signing-key custody,
   fingerprint distribution, use authorization, rotation, revocation, and
   recovery.
6. Define evidence retention and any immutable or WORM storage requirement.
7. Approve hardening profiles, correctness and performance thresholds, and
   waiver authority for every compiler, language, architecture, and lane.
8. Define the allowed source domains, intake egress path, technical egress
   denial for builds, and negative tests that prove fallback fails.
9. Define the applicable transfer and destination acceptance process for systems
   with limited or no external access, including additional classified-boundary
   requirements when applicable.
10. Decide whether bit-for-bit reproducibility is required for selected
    critical packages or whether repeatable inputs and functionally equivalent
    output are the accepted objective.

## Proposed authorization rationale

> CSE proposes to meet the stated security outcomes through a defined managed
> software-production process. Designated CSE personnel operate Spack in user
> space, with recipes, upstream build logic, sources, bootstrap tools,
> configuration, and externals treated as controlled supply-chain inputs.
> The proposed decision identifies the operating scope and evidence required
> before production use on each system.
>
> The model pins the tool, repository, source, configuration, compiler,
> provider, and dependency baseline; inventories the complete selected closure;
> and applies automated checks with risk-based manual review of local,
> exceptional, and changed inputs. It performs source acquisition and scanning
> in a distinct controlled-egress step; builds without outbound network access as a
> nonprivileged identity; retains the concrete graph and complete effective
> configuration; performs risk-based security, functional, numerical, ABI,
> linkage, multi-node, and performance validation; and separates builders from
> the approval and release-signing role.
>
> Routine intake uses a supported pinned repository snapshot with a proposed
> minimum publication age of 90 days, verified against current findings. This
> delays adoption of recent changes without treating age as proof of safety or
> delaying urgent remediation; scoped exceptions receive explicit review.
>
> A second qualified person reviews the exact candidate and evidence before
> signing and publication. A qualified reviewer outside CSE may be assigned
> where independent scrutiny or expertise is needed, with explicit scope and
> authority. Accepted artifacts enter a versioned, write-controlled
> CSE build cache using a backend that satisfies the selected signing policy.
> Designated installers verify the approved CSE key and release-set membership,
> use a clean or dedicated controlled store with separately admitted externals, and use
> cache-only installation with no transparent public-source fallback. Normal
> users consume the accepted software through modules. Each release retains
> source and artifact digests, recipe and configuration
> provenance, lockfiles, external inventory, build logs, test and scan results,
> the candidate-production SBOMs, approvals, exceptions, and an authenticated
> CSE release record that binds the approved release set. Changes
> create a new release. Published artifacts remain subject to vulnerability
> monitoring, revocation, withdrawal, and replacement.
>
> CSE requests evaluation of this process through the responsible local security
> and authorization process against the system's assigned requirements and
> mission risk. Production begins after the required controls are demonstrated
> and accepted on the receiving system. Acceptance on one system does not
> automatically accept another site, transfer route, or security boundary.
> Any additional recipe review, compiler-hardening, scanning, retention,
> cryptographic, or transfer
> requirement should be stated as a testable gate with scope, evidence, and an
> approval authority so that it can be implemented and assessed consistently.

## Claim-to-source ledger

| ID | Claim | Principal primary source | Confidence and qualification |
|---|---|---|---|
| C1 | Spack recipes are executable inputs | [Spack v1.2.2 repository loader](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/repo.py#L128-L176) and [packaging guide](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L1297-L1308) | High; upstream build logic remains a separate executable input |
| C2 | Checksums establish admitted-byte identity, not safety | [Spack v1.2.2 checksum rules](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L542-L564) | High |
| C3 | Full VCS commits are preferable to mutable branches and tags | [Spack v1.2.2 Git provenance rules](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L618-L648) | High; commit identity is not author approval |
| C4 | A lockfile fixes a concrete DAG but is not a complete attestation | [Spack v1.2.2 environment guide](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L84-L121) | High |
| C5 | `SPACK_DISABLE_LOCAL_CONFIG` does not eliminate every configuration scope | [Spack v1.2.2 configuration guide](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst#L55-L134) | High |
| C6 | `spack isolate` is experimental and best effort | [Spack v1.2.2 isolation documentation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst#L694-L711) | High; external host and network controls remain required |
| C7 | Source mirrors support offline preparation but do not prove egress denial | [Spack v1.2.2 mirror guide](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/mirrors.rst#L12-L77) | High for mirror behavior; enforced no-egress is a CSE control |
| C8 | Signed build-cache packages and cache-only installation are supported | [Spack v1.2.2 binary-cache guide](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst#L99-L137) | High |
| C9 | Spack 1.2.2 does not sign build-cache index manifests | [Spack v1.2.2 build-cache layout](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst#L676-L704) | High; the approved release set needs separate authentication. A signed release record is one optional mechanism, subject to applicable requirements |
| C10 | Spack SPDX output is useful but incomplete and is not a scan | [Spack v1.2.2 SBOM generator](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/hooks/sbom_generate.py#L53-L170) | High |
| C11 | RPM and Conda do not eliminate executable lifecycle code | [RPM scriptlets](https://rpm.org/docs/latest/manual/triggers.html), [Conda link scripts](https://docs.conda.io/projects/conda-build/en/stable/resources/link-scripts.html), and [Conda activation scripts](https://docs.conda.io/projects/conda-build/en/stable/resources/activate-scripts.html) | High; governance varies by repository and channel |
| C12 | NIST supports risk-based C-SCRM and due diligence | [SP 800-161 Rev. 1 Update 1](https://doi.org/10.6028/NIST.SP.800-161r1-upd1) and [SP 1326](https://doi.org/10.6028/NIST.SP.1326) | High; due diligence depth remains a local risk decision |
| C13 | NIST provides HPC-specific, performance-conscious system-control tailoring guidance | [SP 800-223](https://doi.org/10.6028/NIST.SP.800-223) and [SP 800-234](https://doi.org/10.6028/NIST.SP.800-234) | High; the CSE package tiers, compiler profiles, A/B method, and waiver thresholds are local proposals. SP 800-234 is optional and not automatically the assigned DoD overlay |
| C14 | Approved compiler and build configuration requires operational testing | [SP 800-218](https://doi.org/10.6028/NIST.SP.800-218) | High; NIST does not prescribe a universal flag set |
| C15 | DoD authorization remains an RMF and AO decision | [DoDI 8510.01](https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodi/851001p.pdf) | High |
| C16 | Open source is subject to the same rigorous SCRM and cyber-testing expectations | [DoD OSS memorandum](https://dodcio.defense.gov/Portals/0/Documents/Library/SoftwareDev-OpenSource.pdf) | High |
| C17 | Classified transfer is a separate authorization boundary | [DoDI 8540.01](https://www.esd.whs.mil/portals/54/documents/dd/issuances/dodi/854001p.pdf) | High for CDS scope; local media and enclave procedures may add requirements |
| C18 | Government-wide software assurance policy changed in 2026 | [OMB M-26-05](https://www.whitehouse.gov/wp-content/uploads/2026/01/M-26-05-Adopting-a-Risk-based-Approach-to-Software-and-Hardware-Security.pdf) | High; Component, contract, acquisition, and AO requirements may still mandate specific artifacts |
| C19 | Native Spack 1.2.2 signing is not available for OCI build-cache pushes | [Spack v1.2.2 OCI push logic](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/buildcache.py#L516-L532) | High; separate OCI signing and mandatory verification may supply another trust model but is not native Spack package signing |
| C20 | Default bootstrap is a separate public and unsigned-cache trust path | [Spack v1.2.2 default bootstrap configuration](https://github.com/spack/spack/blob/v1.2.2/etc/spack/defaults/bootstrap.yaml) and [bootstrap core](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/bootstrap/core.py#L154-L192) | High; SHA-256 metadata verification provides identity, not a native package signature |
| C21 | VCS mirror archives have a commit-to-archive verification gap | [Spack v1.2.2 stage implementation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/stage.py#L669-L685) | High; CSE must create and retain the missing binding evidence |
| C22 | Cache-only installation does not retroactively verify existing stores or supply externals | [Spack v1.2.2 install decisions](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/new_installer.py#L1792-L1812) | High; use a clean controlled store and separate external admission |
| C23 | Consumer-side binary installation regenerates the local SBOM through hooks | [Spack v1.2.2 binary installation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/binary_distribution.py#L2163-L2174) | High; retain and sign the candidate-production SBOM separately |

## Primary-source register

### NIST, OMB, and DoD

* [OMB M-26-05, Adopting a Risk-based Approach to Software and Hardware Security](https://www.whitehouse.gov/wp-content/uploads/2026/01/M-26-05-Adopting-a-Risk-based-Approach-to-Software-and-Hardware-Security.pdf), January 23, 2026.
* [DoDI 8510.01, Risk Management Framework for DoD Systems](https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodi/851001p.pdf), July 19, 2022.
* [NIST SP 800-53 Rev. 5, Release 5.2.0](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), August 27, 2025.
* [NIST SP 800-53B, Release 5.2.0](https://csrc.nist.gov/pubs/sp/800/53/b/upd1/final), August 27, 2025.
* [NIST SP 800-161 Rev. 1 Update 1](https://doi.org/10.6028/NIST.SP.800-161r1-upd1), November 1, 2024 update.
* [NIST SP 1326, C-SCRM Due Diligence Assessment Quick-Start Guide](https://doi.org/10.6028/NIST.SP.1326), July 8, 2026.
* [NIST SP 800-218, Secure Software Development Framework v1.1](https://doi.org/10.6028/NIST.SP.800-218), February 3, 2022.
* [NIST SP 800-204D, Strategies for the Integration of Software Supply Chain Security in DevSecOps CI/CD Pipelines](https://doi.org/10.6028/NIST.SP.800-204D), February 12, 2024.
* [NIST SP 800-223, High-Performance Computing Security](https://doi.org/10.6028/NIST.SP.800-223), February 2024.
* [NIST SP 800-234, High-Performance Computing Security Overlay](https://doi.org/10.6028/NIST.SP.800-234), May 4, 2026.
* [NIST IR 8397, Guidelines on Minimum Standards for Developer Verification of Software](https://doi.org/10.6028/NIST.IR.8397), October 2021.
* [FIPS 199, Standards for Security Categorization of Federal Information and Information Systems](https://csrc.nist.gov/pubs/fips/199/final), February 2004.
* [FIPS 200, Minimum Security Requirements for Federal Information and Information Systems](https://csrc.nist.gov/pubs/fips/200/final), March 2006.
* [FIPS 140-3, Security Requirements for Cryptographic Modules](https://csrc.nist.gov/pubs/fips/140-3/final), March 22, 2019.
* [DoD software development and open source software memorandum](https://dodcio.defense.gov/Portals/0/Documents/Library/SoftwareDev-OpenSource.pdf), January 24, 2022.
* [DoD Enterprise DevSecOps Fundamentals v2.5](https://dodcio.defense.gov/Portals/0/Documents/Library/DoD%20Enterprise%20DevSecOps%20Fundamentals%20v2.5.pdf), October 16, 2024. This is an educational compendium, not a control baseline.
* [DoDI 5200.44, Protection of Mission Critical Functions to Achieve Trusted Systems and Networks](https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodi/520044p.pdf), February 16, 2024. Applicability must be confirmed.
* [DoDI 8540.01, Cross Domain (CD) Policy](https://www.esd.whs.mil/portals/54/documents/dd/issuances/dodi/854001p.pdf), May 8, 2015, Change 1, August 28, 2017.

### Spack 1.2.2

* [Package repository loading](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/repo.py#L128-L176)
* [Package creation and source integrity](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst)
* [Repository pinning and precedence](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/repositories.rst)
* [Configuration scopes and isolation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst)
* [Environment manifests and lockfiles](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst)
* [Source mirrors](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/mirrors.rst)
* [Bootstrapping and air-gapped bootstrap mirrors](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/bootstrapping.rst)
* [Default bootstrap methods](https://github.com/spack/spack/blob/v1.2.2/etc/spack/defaults/bootstrap.yaml)
* [Bootstrap verification implementation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/bootstrap/core.py#L154-L192)
* [Source-stage fallback and VCS mirror verification](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/stage.py)
* [Binary caches and signing](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst)
* [OCI build-cache behavior](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/buildcache.py#L516-L532)
* [Binary installation hooks](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/binary_distribution.py#L2163-L2174)
* [SPDX generator](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/hooks/sbom_generate.py)
* [Audit implementation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/audit.py)

### Package comparison and compiler hardening

* [DNF configuration reference](https://dnf.readthedocs.io/en/latest/conf_ref.html)
* [RPM signatures and digests](https://rpm.org/docs/4.20.x/manual/signatures_digests.html)
* [RPM package scripts and triggers](https://rpm.org/docs/latest/manual/triggers.html)
* [Conda-build recipe and build process](https://docs.conda.io/projects/conda-build/en/stable/concepts/recipe.html)
* [Conda-build scripts](https://docs.conda.io/projects/conda-build/en/stable/resources/build-scripts.html)
* [Conda link scripts](https://docs.conda.io/projects/conda-build/en/stable/resources/link-scripts.html)
* [Conda activation scripts](https://docs.conda.io/projects/conda-build/en/stable/resources/activate-scripts.html)
* [GCC instrumentation options](https://gcc.gnu.org/onlinedocs/gcc-15.2.0/gcc/Instrumentation-Options.html)
* [GCC link options](https://gcc.gnu.org/onlinedocs/gcc-15.2.0/gcc/Link-Options.html)
* [GNU linker options](https://sourceware.org/binutils/docs/ld/Options.html)
* [glibc source fortification](https://sourceware.org/glibc/manual/latest/html_node/Source-Fortification.html)
* [HPE CPE and CCE overview](https://cpe.ext.hpe.com/docs/latest/getting_started/CPE-CCE-Overview.html)
* [HPE `crayftn` manual](https://cpe.ext.hpe.com/docs/latest/cce/man1/crayftn.1.html)
* [HPE Sanitizers4HPC guide](https://cpe.ext.hpe.com/docs/25.03/debugging-tools/sanitizers4hpc/guides/user_guide.html)

## Conclusion

The assurance basis for conditional approval is a bounded managed process with
evidence for each required control:

1. acknowledge that source recipes and upstream build systems are executable
   and must be governed;
2. define a complete, risk-based admission and review boundary;
3. enforce source intake and build isolation outside the package manager;
4. retain the exact configuration, dependency, external, build, test, scan,
   and approval evidence;
5. separate building from signing and publication;
6. publish frozen versioned signed artifacts through managed cache-only
   installation and give normal users access through accepted modules;
7. qualify compiler hardening against both security and HPC correctness and
   performance; and
8. monitor, revoke, and replace releases when risk changes.

This supports consideration of Spack as a mechanism within the defined CSE
software supply chain. Production use depends on demonstration and acceptance
of the required controls for the specific system. The decision belongs to the
responsible authorizing role under the applicable process, with the release
scope, evidence, and residual risk recorded.
