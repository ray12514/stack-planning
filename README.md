# stack-planning

Architecture, schemas, and operating notes for the pre-v1 Spack stack
generation project.

This repo is the design/schema source of truth for the tool repos
(`cluster-inspector`, `stack-composer`) and the data repo (`stack-content`).
No v1 deployment exists yet; if the model changes, update the current docs and
schemas directly rather than preserving old shapes.

## Current model

Start with:

- `docs/stack_generation_structure_v1.md` — the current method.
- `docs/end_to_end_map_v1.md` — point-A-to-point-B flow.
- `docs/deployment_inputs_and_ownership_v1.md` — installer-chosen paths.
- `docs/stack_build_handoff_note_v1.md` — where render stops and build begins.
- `docs/stack_workspace_lifecycle_v1.md` — rendered workspaces and shared
  install tree.
- `docs/runbook.md` — first full-iteration operator runbook.

The model in one line:

```text
profile.yaml facts + deployment.yaml paths + defaults.yaml policy
+ stack.yaml intent + templates render mechanics
-> rendered Spack workspace tree
```

There is no active `contract.yaml` / `stack-defaults.yaml` split. The active
template-set policy file is `defaults.yaml`.

## Repo layout

```text
docs/                      # current design notes and runbook
schemas/                   # canonical JSON Schemas
schemas/.validation/       # developer validation harness and positive examples
examples/reference/        # reference material, when populated
```

## Related repos

| Repo | Role |
|---|---|
| `cluster-inspector` | Optional Go helper that probes systems and emits `profile.yaml`. |
| `stack-composer` | Python renderer/validator. Consumes stack-content and writes rendered workspaces. |
| `stack-content` | Authored data repo: templates, package sets, package repos, stacks, profiles, deployments. |

## Schema validation

When schemas or validation examples change:

```bash
.schema-venv/bin/python schemas/.validation/validate.py
```

Expected final line:

```text
ALL CHECKS PASSED
```
