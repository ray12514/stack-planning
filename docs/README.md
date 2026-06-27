# Documentation Index

Human-readable contracts for the stack-planning system. The JSON Schemas in
`../schemas/` are the machine-readable form and the source of truth.

## Current model — start here

| File | Purpose |
|---|---|
| `stack_generation_structure_v1.md` | **The method.** What each file holds (profile, deployment, `defaults.yaml`, stack, templates), the selection/resolution rules, and `stack-composer show`. Read this first. |
| `stack_workspace_lifecycle_v1.md` | Per-stack workspaces, the one shared hash-deduplicated install tree, and the three lifetimes (kept / regenerable / durable). |
| `end_to_end_map_v1.md` | Point-A-to-point-B map: inputs, producers, outputs, consumers, tools, cadence, worked example. |
| `runbook.md` | First-iteration operator runbook: probe → compose → build → expose → validate. |
| `stack_build_handoff_note_v1.md` | Where render stops; build is a co-equal choice (stack tools / spack-build / Ansible / manual); stack-content + config delivery modes. |
| `stack_generation_orchestration_note_v1.md` | Render across systems: the intersection model, input cadence, re-render/rebuild triggers, tool-agnostic driver contract. |
| `deployment_inputs_and_ownership_v1.md` | Auto-vs-explicit ownership and the `deployment.yaml` overlay; the install tree is never auto-derived. |
| `pre_v1_hosting_and_external_inventory_note_v1.md` | Four-repo GitLab layout, the stack-content repo, and the (realized) provider-family generalization. |
| `cluster_inspector_stack_profile_design_v1.md` | `cluster-inspector` boundary, CLI, packaging. |
| `cluster_inspector_profile_extraction_map_v1.md` | Field-by-field extraction map for `profile.yaml` (provider inventories). |
| `../schemas/README.md` | The schemas (`profile`, `defaults`, `stack`, `package-set`, `release-manifest`). |

The model in one line: one site `defaults.yaml` (no contract/toolchain/class);
generic `compiler_providers` + `mpi_providers` tagged by `provider_family`;
lanes = selected compilers × MPI provider × GPU archs, resolved from
`defaults ∩ profile ∩ per-build override`.

## Historical — superseded (pre-provider-refactor)

Kept for design rationale; each carries a banner pointing here. The model they
describe (`contract` / `toolchain` / `vendor_cray`) is **not** current.

| File | Was |
|---|---|
| `spack_stack_generation_design_v6.md` | The big cross-component design; superseded by the v1 notes above. |
| `stack_composer_design_v1.md` | Composer boundary under the contract model. |
| `stack_composer_declarative_render_alignment_v1.md` | Declarative-render correction; realized in the structure note. |
| `cray_pe_coupling_inventory.md` | Cray PE coupling; Cray is now one `provider_family`. |
| `non_cray_mpi_provider_lanes_hardening_note_v1.md` | Non-Cray MPI lanes; folded into the provider model. |
| `design_implementation_coverage.md` | Pre-refactor implementation tracker. |
