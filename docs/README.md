# Documentation Index

This directory contains the human-readable contracts for the stack planning
system. The JSON Schemas in `../schemas/` are the machine-readable form of these
contracts.

## Start Here

| Reader | Start with | Then read |
|---|---|---|
| Architecture reviewer | `spack_stack_generation_design_v6.md` | `stack_composer_design_v1.md` |
| Tool implementer | `stack_composer_design_v1.md` | `spack_stack_generation_design_v6.md`, `../schemas/README.md` |
| System probe implementer | `cluster_inspector_stack_profile_design_v1.md` | `cluster_inspector_profile_extraction_map_v1.md` |
| Schema consumer | `../schemas/README.md` | The specific schema file and matching design section |
| Fixture author | `../examples/reference/README.md` | `spack_stack_generation_design_v6.md` |

## Files

| File | Purpose |
|---|---|
| `spack_stack_generation_design_v6.md` | Cross-component architecture and operating model. |
| `stack_composer_design_v1.md` | `stack-composer` product boundary, commands, packaging, and phases. |
| `cluster_inspector_stack_profile_design_v1.md` | `cluster-inspector` product boundary, CLI, packaging, and build plan. |
| `cluster_inspector_profile_extraction_map_v1.md` | Field-by-field extraction map for `profile.yaml`. |
