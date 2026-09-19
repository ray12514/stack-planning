# HPC research software intake, telemetry, and recovery discussion

**Date:** 2026-09-17  
**Status:** Sourced discussion note; not approved policy, a site incident finding, or authorization to change access or recovery requirements.

## Assessment

Support controlled third-party intake with a prompt path for research changes,
enforced containment, and tested monitoring. Challenge the assumption that a
fixed catalog or internal location makes software safe. Equally, do not treat
execution telemetry alone as proof that an incident was confined to particular
nodes. This note concerns public technical options for unclassified research
systems; it does not establish a particular HPCMP requirement or deployed control.

## Repository policy: what is defensible and what is incomplete

The security objective is reasonable: control third-party software intake,
reduce exposure to malicious releases, retain artifact identity, and withdraw
affected content quickly. An internal repository can provide these controls.
The December 2023 NSA/CISA/ODNI guidance also recognizes the impact of intake
processes on developer agility and supports different repository policies for
development and production (Section 3, printed pages 7–9). This is guidance,
not proof of an HPCMP mandate or an authorization for a particular site.
[Official guidance](https://media.defense.gov/2023/Dec/11/2003355557/-1/-1/0/ESF_SECURING_THE_SOFTWARE_SUPPLY_CHAIN%20RECOMMENDED%20PRACTICES%20FOR%20MANAGING%20OPEN%20SOURCE%20SOFTWARE%20AND%20SOFTWARE%20BILL%20OF%20MATERIALS.PDF).

Distinguish three implementations when discussing a “walled garden”:

| Implementation | Assessment for this discussion |
|---|---|
| Proxy that automatically caches arbitrary upstream packages | Improves availability and may supply logs; without an admission gate it can redistribute malicious releases. |
| Governed intake with exact artifacts, retained evidence, enforced source selection, and prompt research access | Recommended direction; combine prevention, containment, detection, and recovery. |
| Fixed catalog with a slow manual exception process for every research change | May reduce new intake, but creates a mission bottleneck. Measure delay, staffing and user workarounds rather than assuming it is sustainable. |

These are analytical distinctions and proposed design judgments. Internal
location alone is not evidence of safety; NIST's zero-trust model explicitly
rejects automatic trust based solely on network location or asset ownership.
[NIST SP 800-207](https://csrc.nist.gov/pubs/sp/800/207/final).

“Vetted” should name the exact artifact and dependency set, origin, digest,
checks and their coverage, decision date, allowed context, and reassessment
owner. It should not mean a package name was approved once. Hashes and signatures
bind identity; they do not establish harmless behavior. A repository cannot
remove unknown vulnerabilities in admitted software. A malicious release may
also execute ordinary permitted code without exploiting a software defect.
These distinctions already appear in the
[security draft's evidence table](cse_spack_security_assurance_case_v1.md#security-evidence-answers-different-questions).

## Public incidents relevant to the discussion

The closest literal match to “PyPI and Lightning” is the April 30, 2026
PyTorch Lightning distribution compromise. The maintainer advisory identifies
`pytorch-lightning` 2.6.2 and 2.6.3, describes behavior consistent with credential
harvesting, and recommends rotating exposed credentials and rebuilding affected
systems from a known-clean state. Its May 12 update still describes an ongoing
investigation. This is a historical incident description, not a recommendation
for a current production version.
[Maintainer advisory](https://github.com/Lightning-AI/pytorch-lightning/security/advisories/GHSA-w37p-236h-pfx3).

Lightning's incident post says its PyPI publishing credentials were abused,
while its GitHub source repository remained intact. The malicious builds were
available for 42 minutes and activated on import. The post uses both
`pytorch-lightning` and `lightning` naming; match actual local distribution
metadata and artifact hashes when investigating. Inference: a mirror that
immediately synchronized these legitimate-channel releases could distribute
the attack too; an effective admission delay and subsequent threat-intelligence
check could have prevented that intake.
[Lightning incident account](https://lightning.ai/blog/pytorch-lightning-supply-chain-attack).

A separate December 2022 incident involved Linux PyTorch nightly installs and
a malicious public-PyPI `torchtriton` dependency; its payload executed when
`triton` was imported. This was dependency confusion, and the official notice
states that stable PyTorch was unaffected. Inference: an enforced source-bound
repository with no public fallback would address that substitution path.
[PyTorch incident notice](https://pytorch.org/blog/compromised-nightly-dependency/).

Neither source establishes which incident affected a particular HPC system,
the local extent of compromise, or the necessity or duration of a local outage.
Do not infer those facts from a remembered package name.

## Proposed research access model

The following is a discussion proposal, not a change to the SOP or approved
network access:

| Use | Proposed access and controls |
|---|---|
| Supported shared stack | Existing CSE admission, isolated build, independent review, signing, controlled publication, and advisory response. |
| Project research environment | Self-service request for an exact environment through governed intake; reuse accepted artifacts automatically; assess new dependencies by risk; install into project scope without shared publication rights. |
| Experimental or exceptional software | Dedicated execution environment with enforced limits on credentials, writable storage, network and resources; record owner and expiry, then promote useful environments through stronger review. |

The critical operational requirements are:

1. **Serve research promptly.** Set and measure a request-turnaround target,
   staffing, escalation path, and emergency route. Already accepted artifacts
   should be immediately reusable where their acceptance scope still applies.
   A missed deadline triggers escalation, not silent approval.
2. **Control exact inputs across ecosystems.** Include Miniforge installers,
   Conda channels, Python/pip packages, Spack/bootstrap content, Git revisions,
   containers, and dependencies. Record origins and digests; do not let a
   reviewed top-level tool imply approval of everything it later downloads.
3. **Make intake separate from execution.** Resolve/build candidate packages in
   a restricted context with no production credentials or broad writable home
   and project mounts. Package installation and metadata/build operations can
   run upstream code. pip documents hash-checked installation and binary-only
   inputs as safeguards; neither proves the selected package is benign.
   [pip secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/).
4. **Enforce source and network policy outside user configuration.** pip searches
   indexes without a trusted-first priority; its documentation warns that
   `--extra-index-url` can enable dependency confusion. An environment variable
   naming an internal index is not an enforcement boundary. Define approved
   network routes for intake and separately for research data/API access.
   [pip package selection](https://pip.pypa.io/en/stable/cli/pip_install/#finding-packages).
5. **Test containment.** Python virtual environments and module selections
   organize dependencies; they are not hostile-code isolation. Apptainer
   integrates with the host and does not isolate network and process namespaces
   by default. Select and test filesystem, identity and network controls for the
   actual threat, with stronger separation for higher-risk experiments.
   [Apptainer security model](https://apptainer.org/docs/user/latest/security.html).
6. **Keep observing and responding.** Reassess admitted content when intelligence
   changes; deny withdrawn artifacts, notify affected projects, and supply
   replacements. Join software identity, scheduler accounting and host/network
   evidence so incidents can be contained on defensible evidence.

Measure median and tail request delay, urgent-update delay, researcher days
blocked, coverage of install/import/run telemetry, time to identify affected
accounts and jobs, and time to restore trusted service. These are proposed
mission/security measures, not claims about present site performance.

## XALT contribution and limits

XALT can materially improve the scoping of an HPC software supply-chain incident. A retained run record can connect an executable hash and path to a user, job, time interval, cluster, scheduler context, selected environment variables, loaded shared libraries, and workload size. Link records can add build provenance for artifacts linked through XALT. These are useful positive observations for finding affected jobs and prioritizing systems, users, credentials, shared storage, and artifacts for investigation.

XALT records are not proof that everything absent from the database did not execute. Coverage is site-configured and commonly sampled; dynamically linked execution depends on `LD_PRELOAD`; static binaries built outside XALT are not tracked; MPI normally records task 0 rather than every rank; and interpreter package tracking requires optional hooks. XALT is therefore one incident evidence source, not full endpoint detection and response (EDR), a tamper-resistant audit trail, or a forensically complete execution history.

## What XALT observes

XALT has three record families: `link`, `run`, and `pkg`. Exact fields and coverage depend on the deployed version, build options, site filters, transmission/ingestion configuration, and retention.

At build time, XALT linker wrappers add a watermark and emit link JSON. Documented fields include the link line; linked object/library paths (with a hash or `0` when hashing is skipped); build time, user, configured system name, working directory, and output path; linker identity; UUID; and executable hash. This observes the linker phase when the XALT wrapper is actually selected. It does not by itself observe compiles, copies, downloads, extraction, package-manager scriptlets, or installs, and an unwrapped link produces no XALT link record or watermark. [XALT JSON records](https://xalt.readthedocs.io/en/latest/120_xalt_json.html) [XALT database design](https://xalt.readthedocs.io/en/latest/110_db.html) [XALT internal design](https://xalt.readthedocs.io/en/latest/115_xalt_internal_design.html)

At run time, documented JSON includes an executable SHA-1, path and modification time, working directory, command line when enabled, a filtered environment, parent process tree, user, account, job ID, queue, scheduler, submit host, configured `syshost`, start/end/runtime, and counts for tasks, nodes, cores, threads, and GPUs. It records shared objects observed for the process; current documentation says the record generator interrogates the environment and `/proc`, and the upstream changelog says modern XALT reads `/proc/$PID/maps`. A watermark block adds build metadata when the executable was linked under XALT. Environment collection is deliberately limited, and sites may disable command-line collection, so missing values do not show that they were absent at execution. [XALT JSON records](https://xalt.readthedocs.io/en/latest/120_xalt_json.html) [XALT site filtering](https://xalt.readthedocs.io/en/latest/030_site_filtering.html) [XALT upstream](https://github.com/xalt/xalt)

`syshost` is a site-configured system/cluster identifier. XALT can derive it from a hostname component, file, mapping, stripped hostname, environment variable, or hard-coded value. It is not necessarily the literal execution hostname. The documented run schema has `job_id`, `submit_host`, `syshost`, and `num_nodes`, but no allocation node-list field; `Build_host` separately identifies the build host for a watermarked artifact. For MPI, XALT says only task 0 is tracked. Thus a run record does not prove per-rank or per-node observation. Recover the allocation node list by joining job ID and time to authoritative scheduler/accounting data, recognizing that allocation still does not prove execution on every node. [XALT system-name configuration](https://xalt.readthedocs.io/en/latest/020_site_configuration.html) [XALT JSON records](https://xalt.readthedocs.io/en/latest/120_xalt_json.html) [XALT internal design](https://xalt.readthedocs.io/en/latest/115_xalt_internal_design.html)

XALT can optionally hook package/import mechanisms for Python, R, and MATLAB when the executable is classified `PKGS` and the language integration is installed. Package records contain name, path, version, program, and XALT run UUID. For Python, the installation example adds XALT's `site_packages` to `PYTHONPATH`. Package programs remain subject to scalar sampling, and package data is associated with the end record. This is package-import telemetry, not a record of arbitrary script contents, `eval`/`exec`, sourced shell code, notebooks, generated code, or every import mechanism. [XALT site filtering](https://xalt.readthedocs.io/en/latest/030_site_filtering.html) [XALT installation](https://xalt.readthedocs.io/en/latest/050_install_and_test.html) [XALT JSON records](https://xalt.readthedocs.io/en/latest/120_xalt_json.html)

## Coverage gaps that affect incident conclusions

- **Filters and sampling:** Sites may exclude nodes, paths, system tools, compilers, MPI helpers, or build probes. Scalar/package and smaller MPI runs may be sampled by runtime. The documented TACC example records only 1 in 10,000 scalar runs under 30 minutes; that is an example, not a universal default. Sampled executions that terminate abnormally may leave no record because no start record was produced.
- **Execution mechanism:** `LD_PRELOAD` instruments dynamically linked ELF programs. XALT says static executables are tracked only when linked through its wrapper. Scripts expose the interpreter, and optional hooks cover only supported/configured mechanisms. Container coverage requires explicit propagation and testing.
- **MPI and nodes:** Task 0 plus aggregate counts is not a node list or independent observation from every allocated host.
- **Lifecycle:** Abnormal termination, optional signal handling, failed transport, pre-ingestion filters, ingestion lag/failure, retention, and clock or scheduler-ID ambiguity can remove or weaken evidence.
- **Bypass and tampering:** `XALT_EXECUTABLE_TRACKING=yes` and `LD_PRELOAD` are required, while scalar/MPI tracking can be overridden. A process that sanitizes its environment, invokes an unwrapped linker, or runs a static binary can evade normal collection. A privileged adversary may also alter the collector, configuration, queued records, transport, database, or related credentials. [XALT environment variables](https://xalt.readthedocs.io/en/latest/095_xalt_env_vars.html) [XALT filtering and sampling](https://xalt.readthedocs.io/en/latest/030_site_filtering.html) [XALT internal design](https://xalt.readthedocs.io/en/latest/115_xalt_internal_design.html)

## Incident-scoping and recovery limit

XALT's strongest use is positive correlation: query a suspect executable/library hash or path; find observed users, jobs, times, libraries, and build provenance; join jobs to scheduler allocations; and prioritize containment and examination. A matching, integrity-validated record is actionable exposure evidence.

A negative query is weaker. “No XALT hit” supports retention of a node only if responders can show that XALT was enabled there at the relevant time; the execution/link/container/interpreter was coverable; filters and sampling could not omit it; record generation, transport, ingestion, and retention were healthy; alternate paths/hashes and replaced files were queried; scheduler joins were complete; and the adversary could not tamper with telemetry. Credential theft and modification through shared filesystems or shared images can also extend impact beyond nodes where the suspect binary was observed.

XALT may reduce an initially cluster-wide unknown set and help support targeted recovery instead of an automatic full-cluster rebuild, but it cannot make that decision alone. Corroborate it with scheduler/accounting, identity/authentication and credential evidence, shared-filesystem/image history, software inventories and artifact attestations, audit/network telemetry, and incident-specific host examination. NIST frames incident response as risk management across detection, response, and recovery, and its forensic guidance calls for acquiring evidence from multiple sources while preserving integrity. [NIST SP 800-61 Rev. 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final) [NIST SP 800-86](https://csrc.nist.gov/pubs/sp/800/86/final)

## Site facts to establish before reliance

Document the deployed XALT version/options and coverage dates; compiled hostname/path/argument/environment/pre-ingestion rules; actual scalar/MPI/package sampling tables; literal-host and scheduler node-list sources; Python/package-hook coverage; static/container/build/login/service-node coverage; record-health monitoring and retention; and controls protecting XALT configuration and data from the relevant adversary privilege level.

## Relation to the existing CSE documents

| Existing material | What it already contributes | Additional question for a site-wide policy |
|---|---|---|
| [CSE SOP §4.1](cse_software_stack_sop_v1.md#41-admit-spack-and-its-supporting-tools-before-production-use) and shared SOP §§4.4–4.5 | Explicit admission of Spack, starting Python, prerequisites and bootstrap tools | How are researcher-owned Conda/pip environments admitted and inventoried? |
| CSE SOP §§8.1 and 9 | Input review, snapshot waiting rule, mirror preparation, restricted builds and acceptance | Which research changes qualify for a faster, scoped route? |
| CSE SOP §10 | Reviewed shared publication and signed cache consumption | What separates project experimentation from shared publication? |
| [Shared SOP §12](software_stack_sop_v1.md#12-changes-security-events-and-platform-updates) and CSE SOP §12 | Advisory ownership, impact assessment, withdrawal/replacement and incident escalation | Which runtime evidence, retention periods and recovery criteria establish incident scope? |
| [Post-trial consumption plan](post_trial_cse_consumption_environment_plan_v1.md) | Explicitly supports users bringing source and building on the CSE environment | How will intake and execution controls support that workflow? The plan expressly distinguishes managed discovery from kernel isolation. |

The CSE SOP governs production of the managed stack; its module-based consumer
path should not be silently extended into a prohibition on all researcher-built
software. A separate site research-access policy can define that boundary.
The proposed 90-day rule concerns an identified recipe snapshot and includes
urgent remediation exceptions. It does not establish the age or safety of
separate package archives, Python wheels, bootstrap tools, or local changes.

Suggested position for discussion:

> Support controlled software intake and enforceable containment, with a prompt,
> risk-based path for research software. Use tested telemetry and recovery
> criteria to limit incident impact. Approval of a shared production stack and
> permission to experiment within a bounded project environment are separate
> decisions.
