# stack-planning

Architectural design and canonical contract artifacts for the Spack stack
generation system: cross-component design notes, per-tool design docs,
JSON Schemas, and a round-trip validation harness for the schemas.

This repo is the **source of truth** for the contracts the implementations
must obey. The implementations themselves live in sibling repos
(`spack-composer`, `cluster-inspector`); the content corpus that exercises
them lives in `cse-stack`. If a doc here disagrees with an implementation,
the doc is authoritative — change the implementation, or open a doc fix
first.

## Layout

```
stack-planning/
  docs/
    spack_stack_generation_design_v6.md         # cross-component design (the master plan)
    spack_composer_design_v1.md                  # the Python tool: product boundary, commands, packaging
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
```

## Where this fits

| Repo | Role | Relationship to this repo |
|---|---|---|
| `stack-planning` (this repo) | Architecture, design, canonical schemas | Source of truth |
| `spack-composer` (sibling, future) | Python implementation of the render / validate / publish-manifest / spack-build tools | Consumes the schemas; implements the contracts in `docs/spack_composer_design_v1.md` and the render seam in v6 |
| `cluster-inspector` (sibling, future) | Go implementation of the system-facts probe | Implements the contracts in `docs/cluster_inspector_*_v1.md`; emits `profile.yaml` matching `schemas/profile-v1.json` |
| `cse-stack` (sibling) | Content corpus and test fixture: real `stacks/<name>/stack.yaml` files, real `systems/<system>/profile.yaml` files, the v6 starter template set | Consumes the schemas to validate its content. Eventually becomes the canonical Phase 0c test fixture for the tools. |

The implementations are expected to copy or import the canonical schemas
into their own source trees at build time (e.g., `spack-composer` ships
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

## Provenance

The initial contents of this repo were extracted from `cse-stack`
through a sequence of design passes captured in that repo's commit log.
The pinned source commit is recorded in the initial-import commit
message of this repo. For pre-import design history, read
`cse-stack`'s `git log -- docs/spack_stack_generation_design_v6.md` (and
the corresponding paths for the other artifacts).

## Status

Phase 0a is complete: all six canonical JSON Schemas (`profile`, `stack`,
`stack-defaults`, `template-contract`, `package-set`, `release-manifest`)
are landed and validated end-to-end.

Phase 0b (starter template set content under `templates/v6/`) and Phase 0c
(end-to-end test fixture: profile + stack + expected rendered workspace)
are the next architectural deliverables. Both will land here, then the
content moves into `cse-stack` as the operational corpus.
