# stack-planning

Architectural design and canonical contract artifacts for the Spack stack
generation system: cross-component design notes, per-tool design docs,
JSON Schemas, and a round-trip validation harness for the schemas.

This repo is the **source of truth** for the contracts the implementations
must obey. The implementations themselves live in sibling repos
(`stack-composer`, `cluster-inspector`). The canonical example corpus lives in
this repo under `examples/reference/`. If a doc here disagrees with an
implementation, the doc is authoritative — change the implementation, or open a
doc fix first.

## Layout

```
stack-planning/
  docs/
    spack_stack_generation_design_v6.md         # cross-component design (the master plan)
    stack_composer_design_v1.md                  # the Python tool: product boundary, commands, packaging
    cluster_inspector_stack_profile_design_v1.md # the Go tool: product boundary, CLI, repo shape
    cluster_inspector_profile_extraction_map_v1.md # per-field probe map for profile.yaml
  schemas/
    profile-v1.json                              # canonical JSON Schema (Draft 2020-12, strict)
    stack-v1.json
    stack-defaults-v1.json
    template-contract-v1.json
    package-set-v1.json
    release-manifest-v1.json
    README.md                                    # schema conventions and doc-mapping
    .validation/
      example-*.yaml                             # positive examples for every schema
      validate.py                                # round-trip harness
  examples/
    reference/
      science-stack/                             # canonical self-contained reference stack fixture
    scripts/
      spack-build                                # reference local single-machine build script
```

## Where this fits

| Repo | Role | Relationship to this repo |
|---|---|---|
| `stack-planning` (this repo) | Architecture, design, canonical schemas, and canonical reference fixtures | Source of truth |
| `stack-composer` (sibling, future) | Python implementation of the render / validate / explain / publish-manifest tools | Consumes the schemas; implements the contracts in `docs/stack_composer_design_v1.md` and the render seam in v6 |
| `cluster-inspector` (sibling, future) | Go implementation of the system-facts probe | Implements the contracts in `docs/cluster_inspector_*_v1.md`; emits `profile.yaml` matching `schemas/profile-v1.json` |
| `examples/reference/science-stack` | Self-contained example stack corpus and end-to-end fixture | Exercises the schemas and tool contracts without relying on a downstream deployment repo. |

The implementations are expected to copy or import the canonical schemas
into their own source trees at build time (e.g., `stack-composer` ships
copies of `schemas/*-v1.json` inside its `.pyz` and loads them via
`importlib.resources`). The schemas in this repo remain the *master*.

## Validation harness

A small Python harness checks every schema for self-validity, validates
positive YAML examples, and runs deliberately broken mutations that must
each fail with a clear, locatable error.

```bash
# One-time setup (recreates the local dev venv; gitignored)
python3 -m venv .schema-venv
.schema-venv/bin/pip install jsonschema pyyaml

# Run the full harness (6 schemas + 8 positive examples + 45 negative mutations)
.schema-venv/bin/python schemas/.validation/validate.py
```

The harness must exit `0` with `ALL CHECKS PASSED` before any change to
`schemas/` is committed.

## Status

Phase 0a is complete: all six canonical JSON Schemas (`profile`, `stack`,
`stack-defaults`, `template-contract`, `package-set`, `release-manifest`)
are landed and validated end-to-end.

Phase 0b (starter template set content) and Phase 0c (end-to-end test fixture:
profile + stack + expected rendered workspace) land under
`examples/reference/science-stack/` and remain canonical in this repo.
