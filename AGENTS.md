# Agent guidance for `stack-planning`

This repo is the **source of truth** for the Spack stack generation
system's architecture and data contracts. Implementation repos
(`stack-composer`, `cluster-inspector`) consume what's here.

If you change anything in `schemas/` or rename anything in `docs/`,
expect downstream tools to break — coordinate the change.

## Pre-v1 policy

No stack release has been deployed or tagged as v1 yet. Until that
happens, do not add compatibility paths for previous contract shapes,
schema fields, template behavior, or generated layouts. Treat the
model as still changeable when the design calls for it:

- update the design and schema directly instead of preserving unused
  behavior;
- fail fast when required fields are missing;
- do not describe pre-v1 changes as migrations from deployed behavior;
- reserve compatibility/migration sections for behavior that existed
  in a tagged, deployed release.

## Layout

- `docs/spack_stack_generation_design_v6.md` — cross-component design (the master plan).
- `docs/stack_composer_design_v1.md` — Python orchestrator: product boundary, commands, packaging.
- `docs/cluster_inspector_stack_profile_design_v1.md` — Go inspector: product boundary, CLI, repo shape.
- `docs/cluster_inspector_profile_extraction_map_v1.md` — per-field probe map for `profile.yaml`.
- `docs/non_cray_mpi_provider_lanes_hardening_note_v1.md` — hardening note for Cray-hosted non-Cray MPI provider lanes, such as Intel compiler/runtime plus Intel MPI compatibility lanes.
- `docs/foundation_core_view_semantics_note_v1.md` — hardening note for foundation/Core visibility, build-only views, version-collision policy, and whether foundation packages are public modules.
- `schemas/*-v1.json` — six canonical JSON Schemas (Draft 2020-12, strict).
- `schemas/README.md` — schema conventions and doc-to-schema mapping.
- `schemas/.validation/` — round-trip validation harness + positive example YAMLs.
- `examples/reference/` — canonical example corpus (planned; populated as Phase 0b/0c land).

## Active hardening reminders

- **Do not let Cray MPICH become a hidden universal MPI assumption.** Cray MPICH remains the normal Cray-native provider, but the model must also support explicit non-Cray MPI provider lanes on Cray-hosted systems when policy requires them.
- Preserve full provider module chains. A compatibility lane such as Intel compiler/runtime plus Intel MPI may need modules like `PrgEnv-intel`, the Intel compiler module, and the Intel MPI module recorded together.
- MPI provider selection should be contract-driven. Do not choose MPI solely from `system.family == cray` or by assuming every Cray MPI lane means `cray-mpich`.
- Read `docs/non_cray_mpi_provider_lanes_hardening_note_v1.md` before changing MPI provider selection, toolchain rendering, module emission, or profile MPI schema behavior.
- **Do not expose foundation/Core packages as public modules by default.** Treat them as internal/build-only unless stack policy explicitly marks them public.
- Do not project every transitive dependency into one flat public view. Foundation/Core view semantics must handle version collisions and shared library name conflicts explicitly.
- Read `docs/foundation_core_view_semantics_note_v1.md` before changing foundation lanes, Core lanes, views, module visibility, lockfile composition, buildcache reuse, or foundation package pins.

## How to validate

Every change touching `schemas/` must leave the harness exit `0`:

```bash
# One-time setup
python3 -m venv .schema-venv
.schema-venv/bin/pip install jsonschema pyyaml

# Run the full harness (6 schemas + 8 positive examples + 45 negative mutations)
.schema-venv/bin/python schemas/.validation/validate.py
# Expected last line: ALL CHECKS PASSED
```

A pre-commit hook is provided that runs the harness automatically.
Enable it once per clone with:

```bash
./scripts/install-hooks.sh
```

The hook is permissive when the venv is absent (warns and skips) and
strict when the venv exists (blocks the commit on a non-zero exit).

## Conventions

### JSON Schemas
- **Draft 2020-12** (`$schema: "https://json-schema.org/draft/2020-12/schema"`).
- **Strict**: every object that lists explicit properties sets
  `additionalProperties: false`.
- `$id` placeholder URLs at `https://stack-composer.example/schemas/`.
- Enums for closed vocabularies (no `...` in v6); `string` for open vocabularies.
- `$defs` for repeated sub-objects inside one schema; no cross-document `$ref`.
- Required keys mirror `# R` annotations in the v6 reference YAML;
  optional keys are `# O`. Defaults from `# O - default <x>` become
  `default: <x>` and stay absent from `required`.
- Before a deployed v1 tag, schemas may be edited in place when the
  design changes. After a deployed v1 tag, incompatible schema changes
  live as new files (`profile-v2.json`) alongside the previous
  version.

### Design docs
- v6 is the cross-component master; per-tool docs defer to v6 on cross-cutting
  seams (render contract, profile schema, manifest lifecycle).
- A doc-fix that affects a schema requires updating both: doc first,
  schema next, in the same PR.

### Naming
- The Python tool is `stack-composer` (renamed from `spack-composer`).
- The Go tool is `cluster-inspector` (distinct from the older
  `clusterinspector` repo, which stays as reference material).
- The Spack-driving helper is `spack-build` (descriptive — it drives
  Spack). Do **not** rename it.

## Do not

- Add language-specific code or test scaffolding here. Implementation
  repos own that.
- Pip-install runtime deps "for convenience" — the `.schema-venv` is
  dev-only.
- Move design docs between repos casually. The architectural source of
  truth lives here; routing through another repo creates drift.
- After a deployed v1 tag, edit `schemas/*-v1.json` in place to break
  a downstream — bump to `-v2.json` instead. Before that tag, update
  v1 schemas directly when the design changes.
- Skip the validation harness because "the change is small." If it
  touches `schemas/`, run the harness.

## When you need to look something up

| Question | Read |
|---|---|
| What does the rendered workspace contain? | `docs/spack_stack_generation_design_v6.md` § Render Step — Specification |
| What's the contract for a render-time check? | Same section, § Failure modes the render step catches |
| What's a `lane_kind`? | v6 § Lane Model |
| What variables can a Jinja template reference? | v6 § Template Render Context |
| What does `spack-composer render` actually do? | `docs/stack_composer_design_v1.md` § `stack-composer render` |
| What's in a `profile.yaml`? | v6 § Durable Inputs / `profile.yaml`, then `schemas/profile-v1.json` |
| How does `cluster-inspector` discover modules? | `docs/cluster_inspector_stack_profile_design_v1.md` § Module Discovery And Hints |
| Where do specific probe rules for `profile.yaml` fields live? | `docs/cluster_inspector_profile_extraction_map_v1.md` |
| How should Cray-hosted non-Cray MPI lanes be represented? | `docs/non_cray_mpi_provider_lanes_hardening_note_v1.md` |
| How should foundation/Core views and module visibility work? | `docs/foundation_core_view_semantics_note_v1.md` |
| What schema conventions am I supposed to follow? | This file's "Conventions" section, plus `schemas/README.md` |

## When you are tempted to add a new top-level concept

Stop. Read v6's § Glossary and § Guiding Principles first. The model
is intentionally small; most "new" concepts turn out to be a profile
fact, a contract resolver name, a build class, or a scope path. If
after that read it's still a genuine new concept, write the change as a
v6 amendment first, then update the schemas, then update the
implementations — never the other way around.
