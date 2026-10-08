# CSE and Spack personal discussion notes

8 October 2026. Talking points for my internal discussion and the conversation with the ISSM.

## What I want to establish first

- **CSE is an existing service with a user purpose.** Researchers should arrive on a system, find the common software they need, compile against it, and get to useful work. Familiar modules and consistent package availability should make moving between machines easier. Optimized software is part of that service goal.
- **We started with a practical maintenance problem.** CSE software was built manually. With two people maintaining it, we wanted to see whether Spack could make that work more repeatable and manageable across systems.
- **The initial trial was discovery.** We selected sixteen commonly used packages across four varied systems to find out whether Spack could build them, whether the builds were usable, how the process differed between systems, and what problems we encountered.
- **Those builds used baseline optimization.** We were not deliberately tuning packages for each machine's architecture. Architecture-specific work, such as tuning FFTW, comes later as we develop the service and move toward user evaluation.
- **The initial trial had no user-facing release.** Its findings were meant to help us understand the work and develop the SOP. A successful exploratory build answers a feasibility question; broader validation and release decisions come as the work progresses.

**How I might explain it:**

> We started by asking whether Spack could help us maintain CSE. The initial trial was to build the first sixteen packages on different systems, see whether they could be used, and learn what the process involved. We used baseline optimization and recorded the issues we encountered. From that, we develop the SOP, run through it, and revise it as we learn. Architecture tuning and user rollout come later. We want security involved in that process so we can work out a practical, secure implementation together.

## The iteration I want us to preserve

**Build → document findings → update the SOP → run through the revised SOP → review and repeat.**

The SOP develops from actual experience and then becomes something we exercise. If a step fails, takes more effort than expected, or depends on a service we do not have, we capture that and resolve it. The same approach should apply to proposed security mechanisms: understand the intended protection, try the applicable procedure, and assess whether it works in our environment.

Security input is useful during discovery. The concern is committing to a detailed final implementation before the team has learned enough to make that commitment. We need clarity about the requirements governing the current work and room to resolve implementation details through the trials.

| Part of the work | What we are trying to learn or deliver |
|---|---|
| Initial discovery on the sixteen packages and four systems | Build feasibility, basic usability, system differences, failures, and practical lessons. Baseline optimization; no user-facing release. |
| Repeated builds and SOP development | Whether the documented steps are accurate, repeatable, and workable for the team; how applicable security requirements fit those steps. This overlaps discovery and continues afterward. |
| Further qualification and architecture tuning | Appropriate package and toolchain settings, correctness, representative performance, and the effects of proposed hardening. Tune packages such as FFTW for the relevant architecture as that work is undertaken. |
| Broader deployment of the subset and user evaluation | Repeat the relevant checks on additional systems, then assess whether users can adopt the software and run their workloads effectively. |
| Expansion toward the supported portfolio | Apply what we have learned to more packages and systems, at a pace the team can maintain. |

These are the purposes to keep distinct in discussion; the detailed sequencing can evolve with the results. The original broader plan extended over roughly a year. A server stand-up date, a package qualification milestone, and a user release each need a clear deliverable and realistic dependencies.

## Points to align internally

- Agree on the short account of the trial: what we attempted, what worked, what issues remain, and what we learned. Keep completed work distinguishable from later plans.
- Bring both draft SOPs into the discussion: the [CSE SOP](cse_software_stack_sop_v1.md) for responsibilities and the managed service, and the [shared SOP](software_stack_sop_v1.md) for the operating steps.
- Identify a few real build experiences that explain why the SOP needs iteration. Use the records we already have rather than creating a new reporting exercise.
- Agree on the immediate request to security: review the process with us, identify applicable requirements for this stage, and help resolve the details as we exercise it.
- Be clear about what two people can sustain. Additional infrastructure, reviews, and automation require owners and maintenance effort alongside package work.

## Points to bring to the ISSM

**Start by sharing the SOPs and explaining the stage of the work.** They have not yet reviewed our SOPs. Walk through an actual trial build, what it taught us, and how the procedure changed. Use that as the basis for discussing their concerns.

Questions to raise:

- Which requirements govern the discovery builds we are doing now, and which apply when we begin publishing software for users?
- Where does the existing SOP already address the concern? What specific risk or requirement remains uncovered?
- Which provisions are established requirements, and which are proposed ways of implementing them? For a local requirement, what policy or decision establishes it?
- Which implementation details can we exercise and refine together during the trials?
- What would we need to demonstrate before taking the next step, and who will review it?
- Where does the procedure depend on system administrators, security staff, infrastructure, or services beyond the CSE team?

**The agreement I want:** a shared understanding of the current stage, applicable requirements, and next iteration. As we gain evidence, we can settle the deployment details and the conditions for a user release.

Useful wording:

> We have a process under development and working drafts of the SOPs. Let's review those against your concerns, identify what applies to the work underway, and exercise the remaining details together. That gives us a basis for implementation decisions and a procedure we know the team can follow.

## Why the effect on the CSE service matters

We want users to choose CSE because it saves them work and gives them software that performs well. That also gives shared review, testing, coordinated maintenance, and release records a practical route to the software researchers actually use.

If requirements make CSE slow to update, incomplete, difficult to maintain, or unsuitable for workloads, users may build more software independently. Research demand continues. More acquisition, configuration, patching, and support work may then sit with individual users and research teams. The assessment should include that possibility alongside the protection a proposed requirement adds.

**My question for the discussion:** What happens to the program's actual software use and risk if the managed service becomes less useful or less available?

The comparison should include what two people can sustain through manual delivery, how much coverage and update responsiveness we could retain, and what users would do when their needs are unmet. A return to manual work has real staffing consequences. Reduced CSE coverage is a possible consequence to assess, rather than something to present as a threat or an inevitable outcome.

We do not have metrics proving the net security effect. A shared CSE release also needs protection because a compromised component can reach many users. My point is to examine the whole operating outcome, including adoption and mission benefit.

Things we can observe as the work advances:

- Setup and porting effort, and how soon users reach a correct representative run.
- Why users need independent builds or choose an alternative to CSE.
- Package availability, update turnaround, review delays, and staff effort.
- Correctness and representative performance, including the effects of architecture tuning and hardening.

Better allocation use and less end-of-allocation pressure are plausible benefits to discuss. We should describe them as expected effects until we have measurements, and separate software setup delays from queue waits and other causes.

NIST's HPC guidance supports considering usability, performance, and adoption together. [SP 800-223, §§3.1 and 4.5](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-223.pdf).

## SOP references to have handy

These are provisions in the drafts to discuss and exercise. Their inclusion does not imply that the initial discovery trial completed the full release procedure.

| Topic | Where the drafts address it | Point to raise |
|---|---|---|
| Spack and supporting tools | CSE §4.1; shared §§4.4–4.5 | The proposed assessment includes Spack, bundled libraries, prerequisites, and bootstrap tools. |
| Recipes and dependencies | [CSE §8.1](cse_software_stack_sop_v1.md#81-review-package-changes); shared §§4.4.3 and 8.1 | Input identities, repository ordering, assessment before recipe execution, dependency inventory, and review of changes and risk are already part of the process. |
| Private repositories and local corrections | [Shared §7.6](software_stack_sop_v1.md#76-maintain-local-package-corrections); §§4.3–4.4 | Clarify whether the request means an access-controlled mirror, our local corrections, or individual approval of every recipe. Each has different maintenance implications. |
| Checksums and clean build environment | Shared §§4.2–4.4 and 9.1 | We can show the effective configuration and source identity. Spack documents native checksum and clean-environment settings; the SOP does not explicitly name `dirty: false`. [Spack settings](https://spack.readthedocs.io/en/v1.2.0/config_yaml.html). |
| Controlled builds and validation | [CSE §9.3](cse_software_stack_sop_v1.md#93-restricted-build-and-acceptance); shared §9.3 | The draft covers non-root builds, approved local inputs, outbound blocking, separation from signing credentials, and applicable correctness and performance checks. Discuss which provisions apply at each stage and how they are supplied. |
| Review and updates | [CSE §2.2](cse_software_stack_sop_v1.md#22-security-review-and-decisions); both §12s | The proposed workflow has review and distinguishes routine changes from exceptions, incidents, and boundary changes. Agree how that connects to local change approval. |
| Publication and module use | CSE §§10–11; shared §§10.1–10.3 | The intended user service consumes accepted software through modules. These are later publication steps to work toward. |
| Restricted destinations | [CSE §9.2](cse_software_stack_sop_v1.md#92-systems-with-limited-or-no-external-network-access); shared §9.2 | There is already a route for compatible binary delivery, authorized transfer, integrity checks, and destination acceptance. |
| Records and recovery | Both §§12–14; CSE §2.1 | The drafts provide for independent review, retained build and release records, maintenance, and rollback. Exercise the steps and see whether the records answer the actual review questions. |

The [assurance case](cse_spack_security_assurance_case_v1.md) provides supporting rationale and candidate mappings if needed. The SOPs are the practical process to discuss.

## Prompts if individual proposals come up

**Server, GitLab, and Ansible**

- What function does “Spack server” mean here: repository, source mirror, binary cache, build host, CI runner, signing service, or controller?
- Which function is needed for the current stage? Which is part of the eventual service?
- Who provides and maintains it, and what benefit or requirement does it satisfy?
- GitLab is already in our [transition plan](portable_tools_and_gitlab_transition_plan_v1.md). The [build handoff](stack_build_handoff_note_v1.md) supports different approved execution tools. We need to work through the proposed automation in that context.

Spack supports local operation and filesystem caches. A dedicated service is a deployment choice whose purpose needs definition. [Spack getting started](https://spack.readthedocs.io/en/v1.2.0/getting_started.html); [binary caches](https://spack.readthedocs.io/en/v1.2.0/binary_caches.html).

**An RFC for each update**

- What counts as an update: an exploratory recipe correction, a repeated build, a published release, a default-module change, an urgent fix, or a boundary change?
- Can routine work within an agreed scope use a defined review path, with escalation for material changes?
- How will review turnaround affect iteration and security fixes?

CM-3 calls for defined controlled change types and approval; CM-4 calls for prior impact analysis. The local implementation determines how those connect to an RFC. [NIST SP 800-53, CM-3 and CM-4](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final).

**Compiler flags and optimization**

- We are willing to evaluate the requested protections. Establish what protection is intended and how it applies across the actual compilers, languages, packages, and build systems.
- Keep the initial baseline builds and later architecture tuning clear in the discussion. The discovery builds do not tell us how a tuned FFTW build will perform or what a particular hardening profile will cost.
- Test the applicable settings, resulting binaries, correctness, and representative performance as we qualify those builds. Bring measured incompatibilities or costs back for a decision.
- For FFTW, HDF5, and similar packages, consider their actual use and exposure, along with whether the resulting software serves researchers' workloads.

Our [compiler performance research](standalone_compiler_hardening_performance_evidence_v1.md) can inform that work. The important issue is understanding and qualifying the requirement across our environment.

**Restricted systems and package boundaries**

- Separate connected build workflows from disconnected consumption. Compatible twin systems may let us reuse binaries and build evidence, with the required transfer and destination checks.
- Clarify whether an approved-package restriction concerns CSE's managed releases or changes what ordinary researchers can install and run.
- Describe the actual non-root accounts, locations, and access involved. The eventual shared publication audience also matters to the assessment.

**Recipe maturity**

- Our intent is a mature package-repository release line, normally one broad release behind, with roughly ninety days of community exposure guiding a broad refresh.
- Allow reviewed maintenance and security fixes sooner, recording exact revisions and testing the affected work.
- The current CSE §8.1 says **at least ninety elapsed days**. Bring up that wording difference so the SOP can express the intended policy.
- Spack core and the recipe repository have separate releases. Recipe maintenance can occur through selected release-branch commits; a regular numbered patch-release stream is not established by the records reviewed. Details are in the [release research](cse_spack_issm_public_source_research_v1.md#package-repository-release-and-maintenance-check).
- Keep this maturation guideline separate from the white paper's reported thirty/ninety-day implementation schedule.

## Public references for the discussion

- **[NIST SP 800-223](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-223.pdf):** HPC architecture, site-provided software, usability and adoption, and performance effects. Useful for keeping the mission and actual workflow in the assessment.
- **[NIST SP 800-234, §3.8](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-234.pdf):** The HPC overlay recognizes difficulties with per-program allowlisting where researchers compile code and distinguishes limited-group user software from system-wide publication. Use it to discuss how CSE is classified under the site's requirements. Its moderate baseline and local applicability need confirmation.
- **[HPCMP MHPCC guide, §§3.3.1–3.3.2](https://www.centers.hpc.mil/users/docs/mhpcc/introGuide.html):** Public context for modules, user-installed software, and user responsibilities. The relevant system's rules govern the actual work.
- **[Supporting research](cse_spack_issm_public_source_research_v1.md):** Detailed NIST, DoD, Spack, and release references. Confirm the assigned system requirements with security; CUI alone does not establish that SP 800-171 is the governing baseline for a DoD-operated system.

## What I want to come away with

- A common understanding of CSE's purpose and the discovery work already underway.
- Joint review of both SOPs, including the concerns they already address.
- Clear requirements and workable next steps for the current stage.
- Room to iterate on the procedure and implementation using actual findings.
- Agreed owners for work beyond the CSE team and realistic expectations for the next stage.

**The point to return to:** We are developing a process through experience. Let's use that process to arrive at a secure, useful CSE service that the team can sustain.
