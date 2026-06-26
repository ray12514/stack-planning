# Documentation Index

This directory contains the human-readable contracts for the stack planning
system. The JSON Schemas in `../schemas/` are the machine-readable form of these
contracts.

## Start Here

| Reader | Start with | Then read |
|---|---|---|
| End-to-end overview (any reader) | `end_to_end_map_v1.md` | `runbook.md`, `stack_generation_orchestration_note_v1.md` |
| Architecture reviewer | `spack_stack_generation_design_v6.md` | `stack_composer_design_v1.md` |
| Tool implementer | `stack_composer_design_v1.md` | `spack_stack_generation_design_v6.md`, `../schemas/README.md` |
| Stack Composer refactor implementer | `stack_composer_declarative_render_alignment_v1.md` | `design_implementation_coverage.md` |
| Build/handoff integrator | `stack_build_handoff_note_v1.md` | `runbook.md`, `pre_v1_hosting_and_external_inventory_note_v1.md` |
| Orchestration / driver author | `stack_generation_orchestration_note_v1.md` | `stack_build_handoff_note_v1.md`, `runbook.md` |
| Installer / deployment author | `deployment_inputs_and_ownership_v1.md` | `runbook.md`, `stack_build_handoff_note_v1.md` |
| System probe implementer | `cluster_inspector_stack_profile_design_v1.md` | `cluster_inspector_profile_extraction_map_v1.md` |
| Schema consumer | `../schemas/README.md` | The specific schema file and matching design section |
| Fixture author | `../examples/reference/README.md` | `spack_stack_generation_design_v6.md` |
| Pre-v1 repository/setup reviewer | `pre_v1_hosting_and_external_inventory_note_v1.md` | `AGENTS.md` |

## Files

| File | Purpose |
|---|---|
| `spack_stack_generation_design_v6.md` | Cross-component architecture and operating model. |
| `stack_composer_design_v1.md` | `stack-composer` product boundary, commands, packaging, and phases. |
| `stack_composer_declarative_render_alignment_v1.md` | Pre-v1 correction note: keep Stack Composer declarative-first and move site/vendor policy out of Python branches. |
| `cluster_inspector_stack_profile_design_v1.md` | `cluster-inspector` product boundary, CLI, packaging, and build plan. |
| `cluster_inspector_profile_extraction_map_v1.md` | Field-by-field extraction map for `profile.yaml`. |
| `pre_v1_hosting_and_external_inventory_note_v1.md` | Pre-v1 GitLab/import-path policy and external-candidate inventory boundary. |
| `stack_build_handoff_note_v1.md` | Pre-v1 build-handoff: Stack Composer renders a workspace tree; build is a co-equal choice (stack tools / spack-build / Ansible / manual); stack-content source dir + config delivery modes. |
| `stack_generation_orchestration_note_v1.md` | How render is orchestrated across systems: per-system seam, intersection model, input lifecycle/cadence, re-render/rebuild triggers, tool-agnostic driver contract. |
| `end_to_end_map_v1.md` | The consolidated point-A-to-point-B map: inputs, producers, outputs, consumers, tools, sync, and first-time-vs-continuous cadence, with a worked example. |
| `deployment_inputs_and_ownership_v1.md` | Input ownership (auto vs explicit) and the `deployment.yaml` overlay for installer-chosen site paths; the install tree is never auto-derived. |
| `runbook.md` | First full-iteration operator runbook: probe → compose → build → expose → validate, with bring-back notes. |
