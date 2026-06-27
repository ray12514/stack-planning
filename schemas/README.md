# Canonical schemas

This directory holds the canonical JSON Schemas for the current pre-v1 model.
The matching prose lives in `../docs/stack_generation_structure_v1.md`,
`../docs/deployment_inputs_and_ownership_v1.md`, and
`../docs/end_to_end_map_v1.md`.

No v1 release has shipped. Until then, update these v1 schemas directly when the
model changes; do not add compatibility paths for unused alpha shapes.

## Files

| Schema | Purpose |
|---|---|
| `profile-v1.json` | Observed system facts: system/OS/fabric/modules, generic `compiler_providers`, `mpi_providers`, GPU toolkit facts, filesystem candidates, node types. |
| `defaults-v1.json` | Site/template-set policy: compiler/MPI/GPU/target defaults plus modules, externals, foundation pins, buildcache, release conventions. |
| `deployment-v1.json` | Installer-owned per-system choices: install tree, build stage, caches, view/module roots, module publish root, buildcache destinations, optional Spack root. |
| `stack-v1.json` | Stack/package intent: spec-native builds, optional per-build narrowing, package repos, and overrides. |
| `package-set-v1.json` | Curated Spack root-spec groups usable from stack builds. |
| `release-manifest-v1.json` | Draft/final manifest for the rendered workspace and downstream build evidence. |

## Conventions

| Aspect | Decision |
|---|---|
| JSON Schema draft | Draft 2020-12. |
| Strictness | Objects with declared properties use `additionalProperties: false`. Unknown keys are bugs. |
| `$id` | Placeholder `https://stack-composer.example/schemas/<name>.json` until a final namespace exists. |
| Cross-schema `$ref` | Not used in v1; each schema is standalone. |
| Versioning | Before deployed v1, edit in place. After deployed v1, incompatible changes become `*-v2.json`. |

## Validation harness

Developer-only validation lives in `.validation/`:

- `example-cray.yaml`
- `example-linux.yaml`
- `example-defaults.yaml`
- `example-deployment.yaml`
- `example-stack-science.yaml`
- `example-package-set.yaml`
- `example-release-manifest-draft.yaml`
- `example-release-manifest-final.yaml`
- `validate.py`

Run from the repo root:

```bash
.schema-venv/bin/python schemas/.validation/validate.py
```

Expected final line:

```text
ALL CHECKS PASSED
```
