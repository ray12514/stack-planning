# Documentation Index

This is the routing index for the four-repository stack-generation project.
The architecture and ownership contracts live in this repository. The JSON
Schemas in `../schemas/` are the machine-readable contracts. Exact command
syntax lives with the implementing tool and in the current operator runbook.

Use the following precedence when two documents appear to disagree:

1. `../CONTEXT.md`, the current-model documents below, and `../schemas/` define
   the architecture and data contracts.
2. `software_stack_sop_v1.md` owns the shared Spack operating procedures;
   `cse_software_stack_sop_v1.md` supplies CSE policy and acceptance choices.
   `runbook.md` supplies Initial Conversion Trials tooling, orchestration, and
   recovery details within those gates. The SOPs define enduring requirements
   independently of that internal implementation material and can be distributed
   together without the rest of this repository. These SOPs remain working drafts;
   assigned system/security requirements and recorded approvals still apply.
3. `../../stack-content/systems/<system>/runbook-notes.md` contains only the
   system-specific delta and recovery commands for that system.
4. The current tool `--help`, generated workspace `README.md`, and
   `BUILDER-HANDOFF.md` define the exact executable surface.
5. Research, readiness, branch-history, and presentation notes provide
   evidence and context; they do not override the current model or runbook.

The internal source directory remains `stack-content/pilots/cse-pilot/` for
the current trial blueprint. `init-workspace` is the supported blueprint
assembler. The activity described to operators and stakeholders is the
**Initial Conversion Trials**, not a separate production mode.

Production-path selection remains open. Static-catalog consumption, supported
blueprint assembly and standard full render are alternative preparation
paths; they share the downstream SOP lifecycle. The
[failure/recovery and test matrix](stack_failure_recovery_and_test_matrix_v1.md)
records their current coverage and missing lifecycle tests. The retained
assembler decision supersedes older descriptions of `init-workspace` as a
temporary command; the current CSE blueprint remains specific to the trials.

## Current model: start here

Editable review copies of the CSE SOP and shared procedure, together with the
Word edition of the response drafting guidance, are in
[Word documents](word-documents/README.md). Keep the two SOP Word files together
when sharing them so their companion-document links remain usable.

| File | Purpose |
|---|---|
| `../CONTEXT.md` | **Glossary**: the ubiquitous language, tiers (foundation/core/serial/mpi/gpu), view/module exposure, lane, toolchain, CPE version, provider. Read first. |
| `stack_generation_structure_v1.md` | **The method.** What each file holds (profile, deployment, `defaults.yaml`, stack, templates), the selection/resolution rules, and `stack-composer show`. |
| `lane_and_module_model_v1.md` | **Lane + module model.** Lanes, per-compiler Core, the three GPU lane kinds, toolchain binding, externalization, exposure, front-door module anatomy, provenance, build order. |
| `stack_workspace_lifecycle_v1.md` | Per-stack workspaces, the one shared hash-deduplicated install tree, and the three lifetimes (kept / regenerable / durable). |
| `end_to_end_map_v1.md` | Point-A-to-point-B map: inputs, producers, outputs, consumers, tools, cadence, worked example. |
| `runbook.md` | Canonical Initial Conversion Trials procedure: probe → static catalog → restricted build/validation → private build cache → cache-only shared publication. |
| `initial_conversion_trials_build_execution_model_v1.md` | Why the trial uses eight independent environments, how exact hashes enable reuse during parallel installation, what the generated lock verifier and shared-builder permission contract prove, and which execution invariants should move into the full renderer. |
| `post_trial_cse_consumption_environment_plan_v1.md` | Post-trial plan for the container-like managed consumption environment, orthogonal package classification, compiler-neutral versus compiler-bound reuse, declared system integration, and evidence to extract from the trials. |
| `portable_tools_and_gitlab_transition_plan_v1.md` | Plan for self-contained Cluster Inspector and Stack Composer commands, a smaller renderer interface, GitLab authority, optional one-way private GitHub mirroring, and removal of GitHub as a build/runtime dependency. |
| `cse_builder_handoff_v1.md` | Resume guide for a second CSE builder: shared/private state, permission gate, parallel-builder boundary, generated workspace entry point, tmux reattachment, and checkpoint recovery. |
| `cse_spack_catalog_to_build_handoff_v1.md` | Self-contained bare-Spack guide with a per-system path/variable handoff sheet, shared-Spack startup, environment selection, scope inspection, concretization, fetching, installation, and build-state inspection. |
| `initial_conversion_trials_build_findings_v1.md` | Running technical record of trial build failures, causes, recoveries, permanent mitigations, and validation gates. |
| `cse_spack_customization_and_upstream_inventory_v1.md` | Consolidated inventory of CSE Spack policy, integration controls, provider adapters, active package overlays, and the upstream retirement queue. |
| `package_overlay_operating_model_v1.md` | Correction-layer decisions, canonical/deployed overlay paths, complete operator loop, SOP ownership, and build-lifecycle implementation/acceptance gaps. |
| `stack_failure_recovery_and_test_matrix_v1.md` | Three alternative preparation paths, exact trial pre-check behavior, SOP re-entry by failure type, partial-build preservation, and verified versus proposed recovery tests. |
| `recovery_hardening_implementation_v1.md` | Implemented source boundaries for scoped control recovery, generic overlay admission, module-only maintenance and disposable local lifecycle tests. |
| `recovery_operator_acceptance_2026_09_22.md` | Same-workspace correction/resume and module-preview regressions, real Spack tiny-fixture evidence, and remaining CCE acceptance. |
| `recovery_hardening_acceptance_2026_09_19.md` | Source branches, actual validation results, real-Spack evidence and outstanding target-system acceptance. |
| `recovery_upgrade_acceptance_2026_09_19.md` | Older workspace rehearsals, module-policy and inventory adoption, consumer/cache failure coverage, fresh-run and delivery evidence. |
| `software_stack_sop_v1.md` | Shared procedural SOP for CSE and application package managers: runtime/configuration setup, risk-based review, source mirrors, delivery to systems with limited or no external network access, build/validation, signing, catalog and cache publication, and maintenance. |
| `cse_software_stack_sop_v1.md` | CSE operating policy and acceptance choices, referencing the shared procedure: two-person builder/reviewer audit, security review points, CSE package/provider/module and access policy, delivery to systems with limited or no external network access, and release responsibilities. |
| `stack_build_handoff_note_v1.md` | Where render stops; build is a co-equal choice (spacktools / spack-build / Ansible / bare Spack); stack-content + config delivery modes. |
| `stack_generation_orchestration_note_v1.md` | Render across systems: the intersection model, input cadence, re-render/rebuild triggers, tool-agnostic driver contract. |
| `deployment_inputs_and_ownership_v1.md` | Auto-vs-explicit ownership and the `deployment.yaml` overlay; the install tree is never auto-derived. |
| `spack_1_2_rendered_environment_reference_v1.md` | Spack 1.2 full-render reference: native config-file seam, groups/`needs`, toolchains, Foundation/Core/Common views, modules, and Cray/Linux examples. |
| `pre_v1_hosting_and_external_inventory_note_v1.md` | Four-repo GitLab layout, the stack-content repo, and the (realized) provider-family generalization. |
| `cluster_inspector_stack_profile_design_v1.md` | `cluster-inspector` boundary, CLI, packaging. |
| `cluster_inspector_profile_extraction_map_v1.md` | Field-by-field extraction map for `profile.yaml` (provider inventories). |
| `../schemas/README.md` | The schemas (`profile`, `defaults`, `stack`, `package-set`, `release-manifest`). |

## Active supporting design and decision notes

These documents refine the current model. They are normative within their
stated scope and must remain aligned with the current-model documents above.

| File | Purpose |
|---|---|
| `compiler_mpi_provider_package_mapping_v1.md` | Mapping from compiler/MPI provider facts to Spack packages, externals, and toolchains. |
| `cluster_inspector_reliability_and_hierarchy_v1.md` | Shared artifact acceptance, hierarchy discovery, execution controls, and the unchanged-workspace compatibility boundary. |
| `compiler_provisioning_note_v1.md` | Rules for external and stack-built compiler producers. |
| `default_selection_policy_v1.md` | Explicit default-selection policy; profiles report candidates and never choose the deployment default. |
| `environment_granularity_note_v1.md` | Decision to keep one independent Spack environment per lane/surface. |
| `foundation_core_view_semantics_note_v1.md` | Foundation/Core build, reuse, view, and public-module semantics. |
| `cse_validation_flux_and_module_activation_plan_v1.md` | Integrated plan for the current module/Cray entrance gate, ReFrame package and application regression, native scheduler acceptance, and optional Flux execution inside an allocation. |
| `hpc_validation_reframe_implementation_spec_v1.md` | Separate downstream validation-suite boundary, runnable starter, full trial/package and platform/MPI/GPU coverage, evidence/reporting model and implementation milestones. |
| `full_render_open_decisions_v1.md` | Accepted full-render direction and remaining implementation work. |
| `platform_runtime_set_design_v1.md` | Coherent platform runtime-set selection across compiler, MPI, fabric, and CPE facts. |
| `cray_runtime_package_repo_note_v1.md` | Cray runtime package-repository direction for GTL, PMI/PALS, libfabric/CXI, and runtime closure. |
| `cpe_rocm_compatibility_note_v1.md` | Compatibility evidence and validation rules for CPE, ROCm, and Cray MPICH. |
| `static_platform_catalog_overview_v1.md` | Internal CSE team guide to catalog contents, restricted and published use, production options, and the consumer boundary. |
| `manual_config_catalog_note_v1.md` | Detailed static platform catalog and `render-static` product contract for reusable, include-ready configuration scopes. |

## Initial Conversion Trials operations and acceptance

These documents apply to the active four-system trial. General commands belong
in `runbook.md`; system-specific commands belong in Stack Content system notes.

| File | Purpose |
|---|---|
| `cray_pe_acceptance_checklist_v1.md` | Cray PE validation gates applied after the common runbook. |
| `generic_linux_acceptance_checklist_v1.md` | Generic Linux validation gates applied after the common runbook. |
| `initial_conversion_trials_dependency_risk_audit_v1.md` | Dependency/reuse risks and the checks that guard the current package graph. |
| `initial_conversion_trials_package_version_check_v1.md` | Approved root versions and their availability in the pinned package repository. |
| `spack_1_2_2_build_orchestration_semantics_research_v1.md` | Verified Spack 1.2.2 build-stage, jobserver, locking, and multi-process behavior used by the trial launcher. |
| `spack_1_2_concretizer_cache_and_cray_pe_runtime_note_v1.md` | Concretization-cache behavior and the current clean-shell Cray PE runtime boundary. |
| `spack_1_2_signing_sbom_security_note_v1.md` | Spack signing, SBOM, trust, and security behavior used by the CSE SOP. |

## Research and evidence

These notes record evidence or earlier decision preparation. They are not
operator procedures and do not override the current model.

| File | Purpose |
|---|---|
| `package_overlay_spack_semantics_research_v1.md` | Primary-source Spack 1.2.2 evidence for repository precedence, inheritance, recipe identity, reconcretization, tests, and overlay retirement. |
| `cce_aocc_cpu_baseline_research_v1.md` | CPU-baseline research for CCE, AOCC, and GNU on AMD-based Cray EX systems. |
| `cse_spack_security_assurance_case_v1.md` | Supporting assurance rationale for conditional, system-specific acceptance of managed CSE Spack use: designated operators and module users, risk-based input review, controlled builds, signing and publication, evidence, hardening, and candidate NIST/DoD traceability. |
| `cse_spack_white_paper_response_guidance_v1.md` | Guidance for drafting a constructive, evidence-backed response to the organizational Spack security white paper, with a Word edition, lifecycle schematic, and standalone chatbot prompt in `cse_spack_white_paper_response_prompt_v1.md`. |
| `hpc_compiler_hardening_security_performance_research_v1.md` | Primary-source assessment of memory-corruption risk on isolated compute nodes, compiler-hardening controls, performance qualification, CCE considerations, and a proposed risk-tiered policy for ISSO review. |
| `cray_mpich_gcc_compatibility_v1.md` | Evidence for treating Cray MPICH GNU path versions as compiler-family baselines rather than exact lane pins. |
| `cray_wrapper_consumption_primary_source_research_v1.md` | Primary-source HPE guidance and the trial recommendation for CCE drivers, direct CSE GCC, Cray MPICH wrappers, runtime closure, and launch evidence. |
| `related_tools_assessment_v1.md` | Comparison with Stackinator and spack-stack. |
| `reframe_flux_primary_source_research_v1.md` | Primary-source ReFrame and Flux capability, integration, lifecycle, and risk research supporting the CSE validation plan. |
| `reframe_site_practices_and_reporting_research_v1.md` | Primary-source site adoption, reusable suites, current reporting capabilities, dashboard options and recommended reporting stages. |
| `site_stack_survey_v1.md` | External HPC-site survey used as background evidence. |
| `spack_supply_chain_security_primary_source_research_v1.md` | Primary-source security assessment of recipes, repository pins, source intake, signed cache-only promotion, SBOM limits, and the bounded RPM/DNF comparison used by both SOPs. |
| `spack-learnings/CSE-Spack-Learnings.md` | Full technical findings from system validation. |
| `spack-learnings/CSE-Spack-Learnings-Summary.md` | Short summary of those findings. |
| `robust_testing_roadmap_v1.md` | Testing roadmap and remaining acceptance coverage. |

## Parked follow-on architecture

| File | Purpose |
|---|---|
| `baseline_module_sets_v1.md` | Parked profile extension for named baseline module sets; not implemented or used by the Initial Conversion Trials. |
| `cse_platform_compatibility_fingerprinting_concept_v1.md` | Parked design for compute-authoritative compatibility classes and per-lane Platform Compatibility IDs used to prepare promotion candidates for restricted sister systems. Implementation waits for completion and adoption of the Initial Conversion Trials confidence and acceptance gates. |

The model in one line: one site `defaults.yaml` (no contract/toolchain/class);
generic `compiler_providers` + `mpi_providers` tagged by `provider_family`;
lanes = selected compilers × MPI provider × GPU archs, resolved from
`defaults ∩ profile ∩ per-build override`.

## Removed pre-v1 notes

The old contract/toolchain/vendor-Cray notes were removed during the provider
and spec-native cleanup. Do not route new work through the removed model; update
the current v1 notes above instead.
