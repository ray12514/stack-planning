# Curated-only user software: service requirements and research impact

**Date:** 2026-09-17  
**Status:** Discussion-only research note; not approved HPCMP policy, a security authorization, or evidence of any site's nonpublic controls.

## Corrected question and existing baseline

The user clarified that compute-node Internet restrictions and acquisition/build
activity primarily on login nodes already describe the site's normal operation.
Those controls are the baseline, not the proposed solution. The ISSM proposal
under discussion would remove researchers' current ability to acquire external
packages and repository content through those existing routes and limit them
to a centrally curated set. The question is what operating service, staffing,
turnaround and research restrictions that additional requirement creates.

The analysis below assumes a strict catalog of approved third-party inputs.
It does not assume a settled rule for researchers' own code or local changes;
that boundary materially changes feasibility. Public peer documentation is
supporting comparison only. Examples of ordinary user installs and proxies do
not demonstrate successful operation, cost or staffing of the proposed
curated-only model.

## What a strict catalog requires

A mirror stores available content. A curated catalog additionally decides which
exact content researchers are permitted to obtain and use. Mirroring an entire
ecosystem does not perform that decision. A new upstream release, Git revision,
dependency or artifact does not inherit approval merely because its project
name already appears in the catalog.

| Service obligation | What the center would need to operate | Consequence for researchers |
|---|---|---|
| Initial catalog | Establish the needed versions, platforms and complete dependency sets; assess them under a defined review depth. | Existing projects can lose required inputs if the initial catalog is selected without their environments. |
| New-software admission | Accept requests with repository/version/environment information, fetch complete inputs, assess findings and publish exact accepted artifacts. | A missing input becomes a service dependency before work can proceed. |
| Changes and maintenance | Assess new artifacts and changed dependencies, retain accepted prior versions, reassess advisories and distribute replacements. | Routine upgrades, collaborator changes and reproducing older results can enter a queue. |
| Build compatibility | Decide whether the catalog supplies approved sources for user builds, centrally built binaries, or both. | Binary-only curation restricts available compiler/MPI/GPU/variant combinations unless the service builds them. Source admission preserves more local build flexibility but still needs execution controls. |
| Exceptions and support | Provide scientific-software expertise, security decisions, an escalation route and accountable turnaround. | No usable exception route means some research is prohibited, rather than merely delayed. |
| Availability and evidence | Operate storage, metadata, backups, delivery, assessment records and withdrawal notices. | The catalog becomes a critical service for new environments and dependency changes. |

The center need not repeat unchanged reviews for every user, and admission can
be automated where the approved policy permits. Nonetheless, human findings,
dependency problems and exceptions require funded capacity. The arrival rate is
the number of new unique artifacts and exceptional requests, not just the number
of package names or researchers. Queue delay and researcher time lost belong in
the cost model alongside infrastructure and staff.

The policy must settle these boundaries before a credible implementation estimate:

- Whether local research code, collaborator branches, local patches and vendored
  dependencies are allowed to change without central approval; relabeling
  third-party code as local cannot by itself establish trust.
- Whether approval means provenance plus automated assessment, deeper human
  review, a waiting period, or a centrally built/tested artifact. These choices
  have different assurance, cost and turnaround.
- Whether approved source can be compiled into a user environment, or only
  centrally published binaries may run.
- Whether Git reads, Git pushes, external APIs and data transfers receive distinct
  permissions, rather than becoming collateral casualties of package restrictions.
- Which research needs can receive an exception, who decides, and the maximum
  response time the service is staffed to meet.

If every code revision requires independent approval before execution, the
edit/build/run cycle itself enters the approval queue. If changing research code
is permitted within defined limits, the policy is an approved third-party-input
boundary rather than a guarantee that all executed code has been vetted. Neither
interpretation should be hidden behind the phrase “curated repository.”

The bounded-research workflow later in this note is an alternative to the strict
model where indicated, not a claim that existing network controls already answer
the ISSM proposal. Storage facts and peer examples remain useful evidence, but
neither supplies the missing service-capacity or research-impact assessment.

## Question and limits

This note checks public, first-party documentation from NERSC, the Oak Ridge
Leadership Computing Facility (OLCF), and the Argonne Leadership Computing
Facility (ALCF). It asks what those centers explicitly permit or instruct users
to do with Python packages, source repositories, builds, network access, and
containers. It does not infer that an undocumented control is absent. In
particular, public instructions to download software do not prove unrestricted
egress, lack of scanning, or lack of monitoring. The review was bounded and is
not an audit of each center's complete policy set.

## Source map

| Center | Official pages used | What they establish |
|---|---|---|
| NERSC | [Python environments](https://docs.nersc.gov/development/languages/python/nersc-python/); [installing and sharing software](https://docs.nersc.gov/development/installing-sharing-software/); [job best practices](https://docs.nersc.gov/jobs/best-practices/); [containers](https://docs.nersc.gov/development/containers/); [software support policy](https://docs.nersc.gov/policies/software-policy/) | User Conda/pip and self-installed Python, source builds, project software locations, login-node builds, containers, and named prohibited software. |
| OLCF | [Python on OLCF systems](https://docs.olcf.ornl.gov/software/python/index.html); [Conda basics](https://docs.olcf.ornl.gov/software/python/conda_basics.html); [PyTorch on Frontier](https://docs.olcf.ornl.gov/software/analytics/pytorch_frontier.html); [containers on Frontier](https://docs.olcf.ornl.gov/software/containers_on_frontier.html); [user-managed software](https://docs.olcf.ornl.gov/software/UMS/index.html) | Personal Conda environments and pip builds, compute-node proxy, Git-based examples, user-built containers, scanning limits on center images, and responsibility for shared user-managed packages. |
| ALCF | [Polaris Python](https://docs.alcf.anl.gov/polaris/data-science/python/); [Polaris getting started](https://docs.alcf.anl.gov/polaris/getting-started/); [compiling and linking](https://docs.alcf.anl.gov/polaris/compiling-and-linking/); [Polaris containers](https://docs.alcf.anl.gov/polaris/containers/containers/); [Spack PE](https://docs.alcf.anl.gov/aurora/applications-and-libraries/libraries/spack-pe/) | Cloned/user Python environments, proxy configuration, compute-node builds, Apptainer, and site configuration for user Spack installs. |

All pages were accessed 2026-09-17. Page crawl freshness is not a policy
effective date unless the page itself supplies one.

## Explicitly documented practices

**NERSC.** NERSC describes four Python choices: its module, a custom Conda
environment, Shifter, or a user-installed Python. It says users are “free to
install your own Python” and documents `wget` of Miniconda, `conda install`, and
`pip install` inside a user environment. It recommends
`/global/common/software/<project>` for shared or scaled installations. Its
software-installation guide recommends source control “such as git” and normal
prefix-based user builds. Its job guide directs users to perform compilations
and environment setup on login nodes. NERSC encourages user-created containers;
Shifter can pull public or private images, and `podman-hpc` can build on
Perlmutter. These are explicit user-managed paths alongside site modules.

NERSC also publishes limits. Its software support policy prohibits named tools
and categories; the public table says it “may change at any time without
notice.” Magic Wormhole has been prohibited since 2024-03-27 and Warp Terminal
since 2024-06-01 for stated security/AUP reasons. The Python guidance warns that
channel choice changes dependencies and recommends pip inside an isolated Conda
environment. These are targeted controls and cautions, not evidence for or
against other nonpublic intake controls.

**OLCF.** OLCF documents personal Conda environments on Frontier and Andes,
including project-home environments for collaboration, and its Conda guide says
pip can build packages from source. Official examples clone GitHub repositories
and install Git revisions. Frontier compute nodes are closed to the Internet by
default, but the PyTorch guide supplies HTTP, HTTPS, FTP, and SOCKS proxy
variables for use cases such as downloading models. Thus “closed by default”
coexists with controlled outbound access through a documented proxy; it is not
the same as no external API access.

Frontier supports building and running Apptainer containers and building Podman
images after account setup. Users may pull registry images or build their own.
OLCF says some center-provided base images are temporarily unavailable when
upstream vulnerabilities prevent them from passing required security scans.
That statement establishes scanning for those provided images only; it does not
state the scan coverage or admission rule for every user package or image.

OLCF's User-Managed Software program is especially relevant to responsibility:
approved users receive both the ability and responsibility to “install,
maintain, document, and support” packages for general users. The program is not
available on every system and is distinct from a person's own environment.

**ALCF.** Polaris documentation provides base Conda environments and permits a
user to clone one to a writable path, then use `conda install` or `pip install`.
It also documents `pip install --user`, while marking that approach typically
not recommended. Application guides contain direct GitHub clones and Git-based
pip installs. For compilation, ALCF directs substantial builds to scheduled
compute nodes rather than login nodes. Polaris getting-started instructions say
that when a node lacks outbound connectivity, users can set the center's HTTP,
HTTPS, and FTP proxy variables. This wording deliberately does not promise that
every node has identical direct egress.

On Polaris, Apptainer build and execution are supported on compute nodes, with
the proxy configured for Internet access. Aurora documentation likewise allows
images built locally and published to Docker Hub or built directly on a compute
node. ALCF's Spack PE page supplies site configuration to users who want to
install their own software with Spack. These examples show supported external
source and user-build workflows, subject to system-specific execution and
network rules.

## Implications for the HPCMP repository discussion

The evidence supports curated center stacks **plus** bounded user-managed
software paths. It does not support describing peer DOE centers as universally
requiring all Python, Git, source, or container inputs to pass through one fixed
internal catalog. Conversely, it would be equally unsupported to call these
centers unrestricted: compute-node egress can be closed by default, proxies are
prescribed, container implementations constrain privilege, prohibited-software
lists exist, and at least some provided images undergo required scans.

A proposed HPCMP walled repository should therefore be presented as a local
policy choice with measured research-access consequences, not as an obvious
copy of a uniform DOE-center norm. A defensible comparison must specify the
boundary separately for supported shared software, personal/project
environments, Git source, build-time dependencies, containers, and runtime API
or model/data access. It should also say who maintains user software and how
urgent research exceptions work.

## Current supply-chain caveat

The separate repository research note records the April 2026 PyTorch Lightning
package compromise. In this bounded center-doc review, no official NERSC, OLCF,
or ALCF page was found announcing a Lightning-specific package-intake policy
change. That is silence, not evidence that no local response occurred. The only
current explicit supply-chain-related center statement found here is OLCF's
temporary withdrawal of provided container images that fail required security
scans, plus NERSC's maintained prohibited-software list. Any claim about a
center's Lightning response needs a center-issued source or direct confirmation.

## Mirror capacity: measured facts and unknowns

| Scope | Evidence as of 2026-09-17 | Meaning for a deployment |
|---|---|---|
| All PyPI release files | Official statistics display **46.4 TB**, cached for 24 hours. | Uploaded distribution files across versions/platforms, not expanded installs, scan workspaces, databases, replicas, or network traffic. The displayed total is rounded. |
| Miniforge installer | Release 26.7.2-0, published 2026-09-08: Linux x86_64 installer is **124,514,161 bytes**, about 124.5 decimal MB or 118.75 MiB. | An installer/base environment, not a copy of conda-forge. Retain selected releases and supported architectures, then size subsequently fetched packages separately. |
| Entire conda-forge | No current authoritative full-channel byte total was established in this review. | Package-name or download counts are not a capacity estimate. Scope platform subdirectories, `noarch`, versions, build variants, labels, and retention before quoting storage. |
| Spack source mirror | No current authoritative total for every upstream source/version was established. Spack documents mirrors of selected packages or concrete environments. | Size the union of needed archives, resources and source revisions. Recipe-repository size and binary build-cache size are different quantities. |

Sources: [PyPI statistics](https://pypi.org/stats/),
[Miniforge release](https://github.com/conda-forge/miniforge/releases/tag/26.7.2-0),
[Miniforge release metadata](https://api.github.com/repos/conda-forge/miniforge/releases/tags/26.7.2-0),
[Conda channel organization](https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/channels.html),
[Spack mirror documentation](https://spack.readthedocs.io/en/latest/mirrors.html).
The Spack web reference currently describes development documentation; operational
commands must match the site's pinned release. The existing shared SOP separately
records its Spack 1.2.2 mirror procedure.

Illustrative PyPI arithmetic, assuming the displayed 46.4 TB means decimal
terabytes: two complete logical copies and 30% growth allowance require
`46.4 × 2 × 1.30 = 120.64 TB`. This is **not** a storage purchase specification:
add temporary scan space, metadata, and any storage-level redundancy overhead
not already included. Two copies are not automatically independent backups.
At uninterrupted ideal line rate, an initial 46.4 TB transfer takes 4.30 days
at 1 Gbit/s or 10.31 hours at 10 Gbit/s. Real synchronization takes longer.

A full archive is an upper-scope option, not the recommended starting point.
PyPA's Bandersnatch supports filtered mirrors and regular incremental updates;
its maintainers explicitly suggest using demand information to select packages.
Filtering is not dependency resolution: a list of top-level project names alone
does not ensure compatible versions, build dependencies or platform files exist.
Conda supports redirecting community channels to a mirror. These mechanisms
provide distribution and selection, not a complete security approval service.
[Bandersnatch](https://github.com/pypa/bandersnatch),
[Conda mirroring](https://docs.conda.io/projects/conda/en/latest/user-guide/configuration/mirroring.html).

For a defensible selected-mirror estimate:

1. Inventory representative user environments and recorded dependency closures,
   including Python versions, GPU stacks, CPU architectures, older reproducibility
   requirements, and source builds. Do not infer demand from package popularity.
2. For Conda, count the actual files selected from relevant platform subdirectories
   plus `noarch`; include the metadata needed for correct solving. For PyPI, count
   required source archives and compatible wheels, including build dependencies.
   For Spack, use the union of concrete environments' source inputs. Deduplicate
   identical retained objects when the backend actually supports that layout.
3. Measure file bytes, object count, daily new bytes, metadata size and retained
   versions. A source archive may be reused by several compiler builds; compiled
   artifacts often cannot. Keep source storage and build-cache estimates separate.
4. Add replicas/backups, retention, growth, quarantine, extraction and scan/build
   workspaces. Include Git history, submodules, LFS, containers and model/data
   artifacts explicitly if those are in scope; they are not included in PyPI.

No remote HPC filesystem or local source mirror was measured in this research.
The unknown Conda/Spack totals should remain unknown until a scoped inventory is
produced; substituting an old conference statistic would misstate current capacity.

## A concrete user workflow to pilot

The goal is to preserve a researcher's edit/build/run cycle. The center must
first decide whether it accepts governed execution of changing research code,
or instead requires independent human approval of every code change. Those
choices have fundamentally different turnaround and staffing implications;
a repository proxy cannot make them equivalent.

The following workflow is proposed for a site accepting bounded research
execution. It does not claim that each experimental revision is fully vetted.

1. **Enter a development/build context.** A researcher uses an authorized project
   area and an appropriate login, development, or scheduled build node. Placement
   follows local resource rules; peer centers differ. Ordinary development retains
   editors, Git, compilers, Conda, pip, and interactive debugging.
2. **Acquire dependencies through a supported route.** Standard package-client
   configuration points to an internal service. Existing accepted artifacts are
   immediately reusable within their allowed scope. A new environment request
   provides a manifest/lockfile or lets an isolated resolver produce one. The
   resolver and any source build hooks are treated as execution of untrusted input.
   Checks, the request status, and missing dependencies are visible to the user.
3. **Preserve Git workflows.** Permit authorized repositories through a controlled
   egress route or an internal pull mirror. A researcher can pull a new commit,
   edit a branch, use editable installs, compile, and repeat in project scope.
   Record the fetched commit and dependency changes. In this proposed development
   mode, dependency admission and execution limits are the normal gates;
   general source scans are advisory rather than a new per-commit approval queue.
   Specific detected threats can still trigger a hold. Staff handle new trust
   sources, findings, and exceptional privileges instead of approving every local edit. External pushes
   require a separately specified outbound-data permission; read permission alone
   must not be interpreted as publication permission.
4. **Capture secondary downloads.** Git submodules are independent repositories;
   LFS objects and repository release assets are separate content; private
   submodules/LFS may need different credentials. Build scripts may download archives from
   CMake, Cargo, npm, or arbitrary URLs. The acquisition/build service must handle
   those paths or give a clear, prompt exception route. Merely allowing `github.com`
   neither mirrors all these dependencies nor establishes their trust.
   [Git submodules](https://git-scm.com/docs/gitsubmodules),
   [GitHub backup guidance including LFS](https://docs.github.com/en/repositories/archiving-a-github-repository/backing-up-a-repository).
5. **Separate mutable development from recorded runs.** Keep an editable project
   workspace for iteration. For a submitted/reproducible run, explicitly capture
   package artifacts/hashes, compiler/runtime identities, source commit and a
   reviewed patch or content manifest, and associate that snapshot with the job.
   Exclude secrets and unrelated/untracked data rather than blindly archiving a
   home directory or dirty tree. Protect the recorded run's environment from
   accidental edits. Later work remains editable and produces a new snapshot
   when needed; it need not become a centrally supported release. Promotion into
   the supported shared stack uses the stronger existing CSE process.
6. **Respond to findings without stranding the project.** Tell the researcher
   which artifact is held, the evidence and owner, available replacements,
   and expected decision time. A time-bounded isolated exception may be an
   available policy choice, with explicit mounts, credential access, network,
   compute scope, expiry and audit owner. Normal home mounts and broad API tokens
   must not be assumed safe merely because a job is called isolated.
   Exceeded service targets trigger escalation, not
   automatic approval or an unexplained indefinite block.

Changing one dependency should normally assess newly introduced artifacts and
the resulting environment, rather than re-reviewing every unchanged byte. A
changed advisory, scanner, policy or scope can nevertheless invalidate an earlier
decision. The CSE recipe-snapshot waiting rule must not silently become a
90-day waiting period on every user commit or package update.

## Hosting, update, and scanning operations

A candidate service uses existing center infrastructure where suitable:

| Component | Responsibility |
|---|---|
| Redundant internal HTTPS/index services | Serve accepted PyPI/Conda/Spack artifacts and metadata to standard clients; isolate publication authority from researcher writes. |
| Artifact and evidence storage | Retain exact bytes, origin, hashes, scope and decision records; back up accepted metadata and irreplaceable inputs; support withdrawal. |
| Acquisition and analysis workers | Fetch through controlled egress, inspect/extract in isolation, resolve dependencies, perform selected scans/builds, and report failures. |
| Git access or pull-mirror service | Support authorized repositories, private access, submodules/LFS and recorded revisions; separately retain required release assets/build downloads with their origins and hashes. |
| Egress proxy/API service | Support authorized live external communications independently of static artifact approval. |
| Operations and support | Monitor freshness, queues, certificates, storage, feeds, backups, availability, exceptions, and researcher problems. |

This is an architectural proposal, not a product selection or hardware sizing.
A pilot may start with a recoverable single instance; redundancy and disaster
recovery capacity must match the agreed production availability requirement.
Spack mirrors can be served from filesystem or web storage; Bandersnatch produces
a static mirror for a web server. A procurement evaluation must verify all required
ecosystems, authentication, policy hooks, source builds and failure behavior.
Buying a repository manager does not establish that the integration or staffing
already exists.

An update cycle can separate retrieval from availability:

`discover/request → fetch into quarantine → inventory/check → policy decision → publish exact artifacts → monitor/reassess/withdraw`

Run synchronization incrementally at a defined cadence, with request-triggered
fetches where supported. Retain older artifacts needed by recorded environments;
do not silently upgrade users when a mirror refreshes. Keep indexes consistent
with what can actually be served. Treat upstream removals and newly malicious
artifacts as recorded security events, with controlled evidence retention rather
than an unattended deletion or continuing general availability.
Evidence copies of malicious artifacts belong in restricted, non-indexed,
non-servable quarantine with a defined retention/deletion policy.

Known-vulnerability matching is only one check. `pip-audit` explicitly says it
does not detect malicious packages and that native-library coverage is limited.
Thus a clean CVE report would not establish protection from a Lightning-style
credential stealer. Use appropriate malware/behavior checks and isolation,
acknowledge their coverage gaps, and keep secret access small.
[pip-audit security model](https://github.com/pypa/pip-audit#security-model).

Scanning throughput must be benchmarked on actual archives. As a deliberately
simplified lower-bound illustration, reading 46.4 decimal TB once at 100 MB/s
takes 5.37 days before decompression or analysis. This is not a scanner benchmark.
Incremental object checks, parallel workers and advisory reassessment against
retained inventories can avoid repeatedly analyzing the entire corpus; full
rescans or deeper analysis remain necessary when the detection method changes.

## APIs and external data are a separate service

An API call is live communication, often authenticated and bidirectional. It is
not a package to mirror. A documented proxy route at a peer center demonstrates
a network mechanism, not that every endpoint or every data transfer is approved.

Proposed requirements are project-scoped destinations and purposes, appropriate
data-transfer permission, short-lived or narrowly scoped credentials where the
remote service supports them, reasonable quotas, and logs that support incident
correlation without recording secrets. Permit ordinary calls within that
authorization without a ticket for each request. Provide a timely route for a
new endpoint and record its owner, purpose, expiry and conditions.
Job correlation needs an actual authenticated user/project identity or a
short-lived scheduler-associated identity; a shared proxy address cannot supply
that association by itself. Keep credentials out of proxy URLs and ordinary
logs, and account for exposure through process environments. Test streaming,
WebSockets, long-lived calls, and any inbound callback requirements separately.

A conventional HTTPS CONNECT proxy can enforce the destination and observe
connection metadata; it cannot inspect encrypted API paths or payloads without
additional TLS termination/interception. If content-level restrictions are
required, that needs a separately designed broker/control. Avoid promising that
a domain allowlist prevents exfiltration: common hosting services can contain
attacker-controlled destinations. Software/code returned by an API still requires
the relevant execution policy.
[HTTP CONNECT semantics](https://datatracker.ietf.org/doc/html/rfc9110#section-9.3.6),
[OWASP guidance on excluding secrets from logs](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html).

## Personnel and cost: what can and cannot be estimated

No current primary publication was found that isolates the staffing cost of
this exact mirror, admission, API and user-support function at the researched
centers. A whole-center staff count is not a useful substitute. There must be
assigned service ownership and backup coverage, package/build support, security
triage and incident response, and network/storage operations. Whether these
require new hires depends on existing available capacity; assuming they are
free additional duties is not a credible plan.

Use measured workload rather than an unsupported FTE promise:

`weekly effort = fixed operations + artifact exceptions × handling time + access exceptions × handling time + findings × triage time + incidents + user support`

Also measure arrival peaks, p95 handling time, backlog age and required coverage
hours. Average labor alone does not establish the staffing needed to meet a
turnaround target during bursts, leave or incidents.

Count new **unique artifacts**, not just user requests: one environment can add
many dependencies, while many users may reuse the same checked artifact. For
illustration only, 500 new artifacts/day, 5% needing 30 minutes of manual work,
means 12.5 analyst hours/day, or 1.56 nominal eight-hour FTEs before operations,
leave/backup coverage, incidents or support. These input values are invented
workload assumptions to show the calculation, not a forecast or industry norm.

Budget separately for usable storage and redundancy, servers/VMs, scanner and
repository licenses if selected, backup/DR, network and transfer costs, staff
time, and researcher time lost to delays. Internal service rates and the selected
deployment are needed for a defensible dollar figure.

## Evidence required before a restrictive rollout

Run an initially observational, representative pilot and agree its duration and
success targets with researchers and security. Do not assume today's use pattern
from one package or one project. Include GPU/ML, MPI/source builds, private Git,
legacy reproducibility, and API-driven work.

| Acceptance scenario | What must work and what to measure |
|---|---|
| Create and frequently update a Conda/pip environment | Correct solving, new dependency handling, source-build dependencies, p50/p95 access delay, false-positive and exception rates. |
| Pull Git, switch/rebase branches, edit, run an editable install and compile | Repeated changes without a staff ticket for each edit; new or force-updated refs, private submodules/LFS and secondary downloads; project-scoped permissions. |
| Re-run an older published experiment | Retained exact inputs/environment and current security disposition; withdrawal/replacement behavior is explicit. |
| Use a container and large model/data files | Image access, artifact identity, separate storage budgeting and required filesystem/GPU/MPI integration. |
| Call an authenticated external API or push approved code | Correct egress path, allowed data flow, credential protection, service compatibility and reliable job correlation. |
| A newly admitted package is later declared malicious | Identify affected environments/accounts/jobs, withdraw access, notify users, rotate exposed credentials, and test recovery. |
| Intake service or upstream is unavailable | Cached accepted work continues where safe; new intake failure is clear; recovery/DR and support escalation meet agreed targets. |

Use pilot evidence to decide how much to cache, where full mirroring is justified,
which traffic needs a proxy or broker, and how many staffed hours the service
actually consumes. Public documents establish peer mechanisms; direct center
confirmation would still be needed for their nonpublic security enforcement,
actual false-positive rates, staffing, and response to the Lightning incident.

Related local analysis: [software intake and telemetry discussion](hpc_software_intake_and_telemetry_research_v1.md).
