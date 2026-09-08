# Guidance for drafting the Spack security white paper response

September 8 2026

## Purpose and use

Our response should explain how Spack's existing capabilities, combined with a defined CSE operating process, can meet the security outcomes raised in the organizational white paper. Lead with the capabilities and controls that address each concern. Explain the operating conditions, supporting evidence, and any remaining work needed to make that answer defensible.

Treat complete coverage as a conclusion to establish through the evidence. Where a concern is only partly addressed, identify the specific gap and a practical way to close it. A constructive response can correct a technical premise or narrow an overbroad conclusion without questioning the author's motives or dismissing the underlying security objective.

Use this guide with the approved organizational chatbot. Supply the four source inputs below, then paste the companion prompt in `cse_spack_white_paper_response_prompt_v1.md`. The prompt also appears at the end of the Word edition of this guide. Use **Spack**, the software's standard spelling, in the paper.

| Input | Role in the drafting task |
|---|---|
| Organizational white paper | Defines the actual questions, assertions, proposed requirements, and requested decisions to answer. |
| Applicable SOP | Describes the procedure and its stated status. For CSE stack production, start with `cse_software_stack_sop_v1.md`; include `software_stack_sop_v1.md` as well if the response covers other application package managers. |
| Existing security write-up | Use `cse_spack_security_assurance_case_v1.md` as a technical argument and reference bank. Its status is proposed policy basis. Its hypothetical assertions are not evidence of what the organizational paper says. |
| Starter response | Supplies reusable wording, organization, and author voice. Keep, revise, move, or remove material according to accuracy and usefulness. No preservation quota applies. |

Confirm that the chatbot can read all supplied material, including tables and citations. If an attachment exceeds its limits, provide labeled sections and require an ingestion inventory before drafting. Identify the SOP version intended for review; a newer date alone does not establish approval. If the starter is supplied later, the first draft can proceed with its absence recorded in the drafting notes.

## Position and tone

The central argument is that the relevant subject of assessment is the managed Spack workflow on the supported systems. Explain which parts Spack supplies, which settings CSE selects, which controls the hosting systems enforce, and which decisions belong to organizational security authorities.

For each concern, use this sequence in connected prose:

1. Identify the security outcome sought by the white paper and cite its exact location.
2. State the relevant Spack capability and the supported CSE procedure.
3. Explain the configuration and operating boundary that make the capability useful for that outcome.
4. Cite the technical source and the local procedure or implementation evidence.
5. State the degree of coverage, remaining limitation, and any concrete action or decision.

Useful phrasing includes: “The concern in Section [x] is addressed by [capability] when [conditions] are enforced”; “This distinction changes the assessment for the managed publication workflow”; and “The remaining requirement is [specific control], with [evidence] needed to demonstrate it.” Replace every placeholder with supported content.

Avoid opening with a blanket concession, declaring the paper wrong, or asserting that all concerns are resolved before completing the mapping. Agreement with a risk does not require agreement with every remedy proposed for it. If the white paper specifies a mandatory mechanism, identify its authority and determine whether an equivalent mechanism may be accepted; do not silently substitute an outcome-based alternative.

Revise the existing assurance paper's opening and its “Responses to likely assertions” material around the actual organizational paper. Retain technically sound evidence and useful controls. Do not inherit its hypothetical claims, prohibitions, or requested approval position automatically.

## Evidence and claim discipline

Record capability, procedure, and deployment status separately. A draft SOP can prescribe a control without demonstrating that it is enforced on a system. A feature documented upstream can exist without being enabled locally.

Use two independent fields in the working crosswalk:

- **Implementation status:** demonstrated on the named system and release; documented procedure with execution unverified; proposed addition; or unknown. Mark approval status separately when relevant.
- **Coverage:** addressed by the demonstrated controls; conditionally addressed; partially addressed; unresolved; or not applicable with a supported rationale. Preserve a valid concern even if one supporting premise needs correction.

Each white paper item should have a stable ID such as WP-01. Split compound assertions when they need different answers. Record its section and page or paragraph, a faithful short paraphrase, whether it is a question, technical assertion, recommendation, or binding requirement, and any cited authority. Preserve the paper's wording strength: “may,” “should,” and “must” are different claims.

For every ID, record the relevant capability, CSE or platform control, implementation status, applicability by system, evidence locator, coverage determination, residual risk, owner or proposed owner, next action, and draft section. Use a concise table in the paper and detailed records in an appendix when the full crosswalk becomes too wide.

### Technical distinctions to preserve

These are reference-backed starting points for the pinned Spack 1.2.2 context of the existing write-up. Confirm the version used by the final response and cite the corresponding source. Public references establish software behavior; they do not establish local deployment status.

| Capability or control | Defensible contribution | Boundary to state |
|---|---|---|
| Source checksums | Detect a mismatch with the expected source digest. [R1] | The digest and source selection need admission controls. A match does not establish benign content. VCS-to-mirror archive identity needs separate evidence. |
| Environments and lockfiles | Record a concrete dependency solution. [R2] | Record repository revisions, effective configuration, tools, and externals as well. A lockfile alone is not a complete build attestation or proof of identical binary output. |
| Signed build caches and cache-only installation | Support authenticated binary delivery and prevent source-build fallback for packages that must be installed. [R3] | Trust approved keys, bind approved release membership, govern existing and upstream stores, and admit externals. Cache installation still has trusted Spack code and hooks. |
| Package inventory and SBOMs | Support component identification and later analysis. [R4] | Inventory is not a malware or vulnerability result. Preserve release evidence and account for external and otherwise unrepresented components. |
| Mirrors and configuration controls | Support controlled input selection and preparation for disconnected builds. [R5] | A mirror or a Spack environment does not enforce network denial or a security sandbox. The platform must enforce and test those boundaries. |
| Review, scanning, approval, monitoring | Supply process controls around software production and use. [R6] | Name the responsible service or role and retain execution evidence. Do not attribute these organizational functions to Spack itself. |

For Spack 1.2.2, verify the selected cache backend: native signing does not cover the build-cache index, and OCI pushes do not support that native signing path. [R3] Do not describe every cache or registry as providing the same signing behavior. Also avoid calling Spack's structural audit a vulnerability scanner or treating signature success as proof of organizational cryptographic compliance.

Include Spack's opt-in Linux build sandbox where relevant as an existing supplementary capability. Its kernel requirements and build-phase scope matter: recipes can execute before the sandbox applies, so it does not establish isolation for the complete preparation and build workflow. [R7]

If package-manager comparisons are relevant to an actual white paper claim, compare equivalent operating modes: source production, repository governance, binary delivery, installation behavior, and ongoing maintenance. Do not claim that Spack, RPM/DNF, or Conda have equal risk merely because each has an executable supply-chain surface.

## Recommended response structure

Use a concise main paper, approximately six to ten pages unless the source requires more, with supporting detail in appendices. The complete question mapping takes priority over a page target.

| Section | What it should accomplish |
|---|---|
| Executive response | State the managed-use position, the strongest supported coverage findings, and the decisions still needed. Write this after completing the crosswalk. |
| Scope and operating model | Identify systems, actors, tool versions, production and consumption modes, and the boundaries of the assessment. |
| Existing Spack capabilities and CSE controls | Explain the controls already available and distinguish their documented and demonstrated status. Use a compact responsibility table. |
| Response to the white paper | Answer each item in the paper's order or in clearly mapped themes. Keep WP IDs visible so a reviewer can find every answer. |
| Controlled release workflow | Show intake, build, validation, approval, publication, consumption, and maintenance, with gates and evidence. |
| System application and remaining improvements | Separate common controls from local implementations. Identify only the additions required by actual gaps or justified operational improvements. |
| Recommended decisions | State the precise operating scope, controls, evidence, and unresolved decisions proposed for agreement. Avoid claiming an authorization already exists. |
| Appendices | Include the full question crosswalk, claim-to-source register, and detailed evidence or system records. Summarize and reference proposed SOP changes in a separate companion document. |

Preserve enough prose to explain why the controls answer the concern. A large matrix alone will not communicate the argument. Group repetitive issues only when every original item remains traceable.

### Applying the model across supported systems

Use one common control model with a per-system implementation and acceptance record. Populate system names and values only from supplied material. For each system, record the scope, build identity, enforcement of network and filesystem boundaries, approved catalog and configuration, compiler/MPI/GPU and external identities, cache backend and trust configuration, publication paths and permissions, runtime acceptance evidence, and responsible roles.

Do not use success on one machine as evidence that another system passed. Reuse evidence only where the shared control and unchanged scope justify inheritance, and state the justification. Keep vendor-specific implementation details in the system record. A classified or separately governed destination requires its own transfer and acceptance boundary if it is in scope.

## Figures that explain the workflow

Prefer two schematics with editable shapes, SVG, or Mermaid source. Use readable labels, explicit arrow meanings, captions, and text equivalents. Decorative imagery does not help this argument. Every figure must agree with the surrounding text and use source-backed labels for implemented controls.

**Figure 1 should show the controlled release lifecycle.** Use the sequence below as a proposed figure pattern, then reconcile it with the supplied SOP and the actual white paper. Do not present the pattern as proof of deployment.

An editable example is available in [the proposed lifecycle schematic](diagrams/cse_spack_response_lifecycle_v1.svg). Its steps describe a candidate model to reconcile with the source documents.

Reviewed tool and recipe baseline → bounded resolution and graph review → controlled source and bootstrap intake → restricted build → security and functional validation → release approval and signing → immutable publication and cache-only installation → user execution and monitoring.

Place resolution and intake within controlled preparation: loading recipes or concretizing can execute code before compilation begins. Show build-network denial and key separation as platform and identity controls. The normal user path should show access through approved modules and installed software; only designated publishers or installers need the cache installation step.

Label each boundary with the artifact crossing it and the receiving role. Use a return path for rejection or quarantine and another for advisory-driven review, withdrawal, and a new candidate. Bind the release record to the exact approved artifacts. Preserve prior releases according to the applicable policy rather than modifying an approved release in place.

**Figure 2 should show responsibility and trust boundaries.** Separate source preparation, candidate production, approval/signing, published software, and end-user execution. Mark who can write each area, where keys are held, where network access is permitted, and where verification happens. Use roles until names are confirmed. Show external compilers, MPI, GPU runtimes, and system libraries as explicit dependencies crossing the platform boundary.

Use solid lines for demonstrated behavior and dashed lines for proposed additions only when source evidence supports that distinction; label status in words as well. Otherwise title the entire figure as the proposed operating model. A lock icon, restricted directory name, or “approved” box is not evidence that a control is enforced. Supply a caption that states the scope and the evidence needed to validate the diagram.

## What belongs in the SOP

Keep the response paper focused on rationale, evidence, and the relationship to the white paper. Put repeatable operational requirements in the SOP: trigger, responsible role, action, pass/fail criterion, evidence, failure handling, and exception authority. Put system paths and provider selections in the controlled system operating record. Keep long comparisons and research discussions in the supporting paper.

Use this routing map to propose targeted changes to the CSE SOP. These are review targets, not findings that every listed item is missing.

| CSE SOP location | Assess or add only where needed |
|---|---|
| Sections 2 through 5 | Roles, implementation authority, pinned inputs, configuration boundaries, prerequisite and access checks. |
| Sections 6 through 9 | Catalog and graph review, recipe baseline/delta admission, controlled acquisition, build isolation, scan and test acceptance evidence. |
| Section 10 | Key custody, approval order, backend-specific signing, release membership, cache-only enforcement, external inventory, publication checks. |
| Sections 11 through 13 | User exposure, advisory handling, withdrawal, replacement, rollback, retention, and expiring exceptions. |
| Section 14 | A complete evidence record tied to the exact candidate and approved release. |

For every proposed change, identify the triggering WP item, current SOP section, exact insert or replacement text, rationale, owner, and acceptance evidence. Label new requirements as proposed. Do not silently change the SOP's response deadlines, retention periods, approval roles, or architecture because a research note suggests a different value. Record disagreements for a decision and make dependent text consistent once that decision is made.

Keep a short starter-document disposition log by section: retained, revised, moved, or removed, with a reason. This allows substantial reuse where the starter is useful and a clean rewrite where it is not.

## References and final review

For internal documents, cite the supplied filename, version/date, section, and page or paragraph. For external technical facts, prefer release-pinned official documentation or source code. Record title, publisher, version, exact URL, locator, the claim supported, and verification status. Follow inherited citations to their actual sources when access is available. Never invent a quotation, page, source, or successful verification.

Use public browsing only for generic public facts and approved public references. Keep organizational source text and system details within the approved environment. If browsing is unavailable, use supplied excerpts and mark inherited links as requiring verification. Missing evidence should narrow the claim and enter an open-items register; it should not prevent the chatbot from drafting the supported sections.

The following starting references support the technical distinctions above. They are not a compliance determination or a complete bibliography for the response.

- **R1 — Spack 1.2.2 packaging guide**, source version checksums and Git sources: https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L542-L648 ; VCS mirror check behavior: https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/stage.py#L669-L685
- **R2 — Spack 1.2.2 environments**, manifest, lockfile, and recreation qualifications: https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L39-L121
- **R3 — Spack 1.2.2 binary caches**, signing and cache-only installation: https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst#L99-L309 ; unsigned index: https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst#L676-L704 ; OCI signing behavior: https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/buildcache.py#L516-L532
- **R4 — Spack 1.2.2 SBOM generation**, SPDX content and external-root handling: https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/hooks/sbom_generate.py#L53-L170
- **R5 — Spack 1.2.2 configuration**, scope precedence: https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/configuration.rst#L55-L134 ; mirrors: https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/mirrors.rst#L12-L77
- **R6 — NIST SP 800-218**, Secure Software Development Framework version 1.1, especially PO.5, PS.2, PS.3, PW.6, and RV.1 through RV.3: https://doi.org/10.6028/NIST.SP.800-218 . Use as an outcome framework; confirm the organization's applicable requirements and any later version adopted by policy.
- **R7 — Spack 1.2.2 installation guide**, build isolation and sandboxing on Linux: https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/installing.rst#L156-L183

Before circulation, confirm that every WP item has an answer or an explicit open disposition; every material technical claim has a supporting source; every “we already do” claim has local evidence; diagrams and SOP proposals agree; unresolved risks remain visible; and the recommended decision is no broader than the demonstrated or explicitly conditional coverage.
