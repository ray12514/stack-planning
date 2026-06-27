# Agent guidance for `stack-planning`

This repo is the **source of truth** for the Spack stack generation
system's architecture and data contracts. Implementation repos
(`stack-composer`, `cluster-inspector`) consume what's here.

If you change anything in `schemas/` or rename anything in `docs/`,
expect downstream tools to break — coordinate the change.

## Pre-v1 policy

No stack release has been deployed or tagged as v1 yet. **Nothing in this repo
is legacy or sacred** until a v1 release ships that real users depend on. If the
model changes, every example, walkthrough, schema, and fixture must be updated to
match it — proactively, in the same change, without waiting to be asked. A full
rewrite is acceptable when the design warrants it. Until v1, do not add
compatibility paths for previous contract shapes, schema fields, template
behavior, or generated layouts. Treat the model as still changeable when the
design calls for it:

- update the design and schema directly instead of preserving unused
  behavior;
- keep all examples, fixtures, and walkthroughs consistent with the current
  model; a stale example is a bug to fix now, not a legacy artifact to preserve;
- fail fast when required fields are missing;
- do not describe pre-v1 changes as migrations from deployed behavior;
- reserve compatibility/migration sections for behavior that existed
  in a tagged, deployed release.

## Layout

- `docs/stack_generation_structure_v1.md` — current method: where each file lives, defaults/profile/stack/template resolution, and `stack-composer show`.
- `docs/stack_workspace_lifecycle_v1.md` — per-stack workspaces, shared install tree, and kept/regenerable/durable lifetimes.
- `docs/end_to_end_map_v1.md` — complete input/output/tool/cadence map and worked example.
- `docs/deployment_inputs_and_ownership_v1.md` — installer-owned `deployment.yaml`; install tree and roots are never auto-derived.
- `docs/stack_build_handoff_note_v1.md` — render/build seam and the stack-content handoff.
- `docs/stack_generation_orchestration_note_v1.md` — external driver contract for multi-system render/build loops.
- `docs/cluster_inspector_stack_profile_design_v1.md` — Go inspector: product boundary, CLI, repo shape.
- `docs/cluster_inspector_profile_extraction_map_v1.md` — per-field probe map for `profile.yaml`.
- `docs/foundation_core_view_semantics_note_v1.md` — hardening note for foundation/Core visibility, build-only views, version-collision policy, and whether foundation packages are public modules.
- `docs/pre_v1_hosting_and_external_inventory_note_v1.md` — pre-v1 GitLab/import-path policy and the external-candidate boundary between observed profile facts and Stack Composer policy.
- `schemas/*-v1.json` — canonical JSON Schemas (Draft 2020-12, strict).
- `schemas/README.md` — schema conventions and doc-to-schema mapping.
- `schemas/.validation/` — round-trip validation harness + positive example YAMLs.
- `examples/reference/` — canonical example corpus (planned; populated as Phase 0b/0c land).

## Active hardening reminders

- **Do not let Cray MPICH become a hidden universal MPI assumption.** Cray MPICH remains the normal Cray-native provider, but the model must also support explicit non-Cray MPI provider lanes on Cray-hosted systems when policy requires them.
- **Keep Stack Composer declarative-first.** Python should validate, merge, generically resolve, and render; package/provider/module/GPU/MPI/external policy should live in profile facts, stack policy, defaults, and templates wherever possible. Read `docs/stack_generation_structure_v1.md` before changing `stack-composer` lane planning, scope selection, spec expansion, provider resolution, or template inputs.
- **Treat Cray PE as provider-family metadata, not the universal model.** Cray-specific probes are allowed, but new render policy should prefer generic compiler/MPI/GPU/fabric/system-external provider facts and compatibility relationships.
- **Do not add project-owned personal-GitHub import paths.** Before a v1 tag, move Go module/import paths and project-owned docs references to the final GitLab namespace or a neutral vanity path. Read `docs/pre_v1_hosting_and_external_inventory_note_v1.md` before changing repository hosting assumptions or external inventory schema.
- **Stack Composer renders; it does not build.** It produces the rendered workspace tree (the handoff). Build/concretize is a co-equal downstream choice — `stack tools`, `spack-build`, Ansible, or bare Spack; never the renderer. The whole tree must travel intact (relative `include::`) or use GitLab-direct remote includes. The `stack-content` repo is the hosted source dir synced to the shared filesystem. Read `docs/stack_build_handoff_note_v1.md` before changing the build seam, the workspace handoff, the stack-content layout, or `config.yaml`/install-tree rendering. Do not rename `spack-build`. Render is a pure per-system seam; the multi-system loop and re-render cadence live in an external driver, not in `stack-composer` — see `docs/stack_generation_orchestration_note_v1.md`.
- **Keep `stack.yaml` spec-native and minimal.** A build is `name` + Spack `specs` (or a `package_set`). `kind` (cpu/mpi/gpu), `compilers`, and other narrowing fields are optional and inferred from the spec + profile/defaults — never make them required, and do not invent user-facing policy names like `science-mpi-default`. The user surface stays Spack-native. Catch wrong-environment specs with a fact-based preflight, never by running Spack inside `stack-composer`.
- **Install tree, caches, view/module roots, and module exposure are installer-chosen, never auto-derived.** The profile offers candidates only; the installer records the choice in `systems/<system>/deployment.yaml` (or build-time flags). Read `docs/deployment_inputs_and_ownership_v1.md` before changing install-tree, `config.yaml`, module-exposure, or deployment-path handling.
- Preserve full provider module chains. A compatibility lane such as Intel compiler/runtime plus Intel MPI may need modules like `PrgEnv-intel`, the Intel compiler module, and the Intel MPI module recorded together.
- MPI provider selection should be provider/defaults-driven. Do not choose MPI solely from `system.family == cray` or by assuming every Cray-hosted MPI lane means `cray-mpich`.
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
| What does the rendered workspace contain? | `docs/stack_build_handoff_note_v1.md` and `docs/stack_workspace_lifecycle_v1.md` |
| What's the render-time model? | `docs/stack_generation_structure_v1.md` |
| What's a lane? | `docs/stack_generation_structure_v1.md` § Resolution |
| What variables can templates reference? | `docs/stack_generation_structure_v1.md`, plus implementation docs in `stack-composer` |
| What does `stack-composer render` do? | `docs/end_to_end_map_v1.md` Stage 5 + `docs/stack_build_handoff_note_v1.md` |
| How should Stack Composer avoid hardcoded site/vendor policy? | `docs/stack_generation_structure_v1.md` |
| What's in a `profile.yaml`? | v6 § Durable Inputs / `profile.yaml`, then `schemas/profile-v1.json` |
| How does `cluster-inspector` discover modules? | `docs/cluster_inspector_stack_profile_design_v1.md` § Module Discovery And Hints |
| Where do specific probe rules for `profile.yaml` fields live? | `docs/cluster_inspector_profile_extraction_map_v1.md` |
| How should MPI provider policy work? | `docs/stack_generation_structure_v1.md` § Resolution |
| How should foundation/Core views and module visibility work? | `docs/foundation_core_view_semantics_note_v1.md` |
| How should pre-v1 GitLab hosting and external candidates be handled? | `docs/pre_v1_hosting_and_external_inventory_note_v1.md` |
| How is the rendered workspace handed off to a build tool? | `docs/stack_build_handoff_note_v1.md` |
| Where does the `stack-content` source directory live and how is it hosted? | `docs/stack_build_handoff_note_v1.md` + `docs/pre_v1_hosting_and_external_inventory_note_v1.md` |
| How is render orchestrated across systems, and what re-renders when an input changes? | `docs/stack_generation_orchestration_note_v1.md` |
| What is the complete flow from `profile.yaml` to a built `spack.yaml`? | `docs/end_to_end_map_v1.md` |
| Who chooses the install tree / module exposure / site paths, and where? | `docs/deployment_inputs_and_ownership_v1.md` |
| What schema conventions am I supposed to follow? | This file's "Conventions" section, plus `schemas/README.md` |

## When you are tempted to add a new top-level concept

Stop. Read v6's § Glossary and § Guiding Principles first. The model
is intentionally small; most "new" concepts turn out to be a profile
fact, a contract resolver name, a build class, or a scope path. If
after that read it's still a genuine new concept, write the change as a
v6 amendment first, then update the schemas, then update the
implementations — never the other way around.
