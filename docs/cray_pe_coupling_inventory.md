> **Superseded (pre-provider-refactor).** This document predates the move to a
> single `defaults.yaml` (no contract/toolchain/build-class) and generic
> `compiler_providers`/`mpi_providers` (Cray PE is one `provider_family`). It is
> kept for design history. The current model lives in
> `stack_generation_structure_v1.md`, `stack_workspace_lifecycle_v1.md`, and the
> JSON Schemas under `../schemas/`. Names below (`vendor_cray`, `contract`,
> `toolchain`, `build_classes`, `compilers_external`) are historical.

# Cray PE coupling inventory

A list of every spot in the three component repos that bakes in
assumptions about the current Cray Programming Environment (CPE) — its
component naming, install paths, module conventions, and per-compiler
MPI flavor layout. When HPE ships a successor PE (unbundled,
container-friendlier, or otherwise different in shape), this is the
grep-once surface that has to change.

The point of this doc: when CPE2 lands, you do not want to discover
the coupling one file at a time. You want to open this doc, audit each
listed spot against the new reality, and ship.

This is a living doc. Each time someone touches one of the listed
spots, they should update the line numbers. The acceptance criterion
for a change that touches Cray-PE-shaped code is "I updated this
inventory."

---

## How to read this doc

Three columns matter:

- **Blast radius** — how many other files break if you change this spot
  without updating callers. Schema changes have the largest blast
  radius (every consumer must accommodate). A probe rewrite has the
  smallest (self-contained to inspector).
- **Coupling type** — how the Cray-PE assumption manifests:
  - *names* — string constants like `PrgEnv-cray`, `cray-mpich`
  - *paths* — filesystem layout assumptions like `/opt/cray/pe/`
  - *shape* — the structure of the data (e.g., `cray_mpich.flavors`
    being a map keyed by compiler name)
  - *flow* — control-flow special cases (e.g., `if provider ==
    "cray-mpich": ...`)
- **CPE2 likely change** — what would actually need to be different.

---

## Where the coupling lives

### Profile schema (highest blast radius — every consumer)

`stack-planning/schemas/profile-v1.json`

| Spot | Coupling | CPE2 likely change |
|---|---|---|
| `vendor_cray` top-level block (line 111-117) | shape | The block name itself encodes "Cray PE". If CPE2 unbundles, the components may not belong together. Options: keep `vendor_cray` for current CPE-shaped systems, add a sibling `vendor_blocks: [...]`; or schema v2 with a generic `vendor_externals` array. |
| `vendor_cray_block` definition (line 311+) — keys: `cce`, `gcc`, `aocc`, `intel`, `nvhpc`, `rocmcc`, `cray_mpich`, `libsci` (and friends) | names + shape | Per-component fields baked in. New components require a schema bump. |
| `cray_mpich_block.flavors` (line 356+) — map of `<compiler-name>` → `{prefix, modules}` | shape | Per-compiler-flavored MPI build prefixes are a CPE-specific packaging artifact. CPE2 unbundled MPI may not be compiler-flavored at all. |
| `compilers_external` description (line 120) — "Excludes Cray PE compilers (those live under vendor_cray)." | flow | Explicit carve-out. If `vendor_cray` goes away, this comment + the implicit routing logic in the inspector both have to move. |
| `mpi` description (line 127) — "Excludes cray-mpich (lives under vendor_cray)." | flow | Same carve-out for MPI. |

---

### cluster-inspector (Go) — probe code

| File | Spot | Coupling | CPE2 likely change |
|---|---|---|---|
| `internal/probes/system.go:117-119` | `detectCrayEvidence()` — `/opt/cray/pe`, `CRAYPE_VERSION` env, `PE_ENV` env | paths + names | CPE2 may live elsewhere (`/opt/hpe/cpe2/`?) or expose different env vars. |
| `internal/probes/system.go:121-130` | `deriveSystemFamily` returns `cray-rhel` / `cray-sles` / `cray` based on the Cray flag | names | New family discriminator for CPE2 (e.g., `cpe2-rhel`). |
| `internal/probes/system.go:27` | `CrayEvidence bool` field on `SystemResult` | shape | Single-vendor bool. If CPE coexists with CPE2 during transition, becomes inadequate. |
| `internal/probes/cray.go` (entire file) | Cray PE component discovery — PrgEnv modules, /opt/cray/pe paths, cray-mpich flavor enumeration | names + paths + shape | Either rewrite in place for CPE2 conventions, or add a sibling `cray_pe2.go` probe and dispatch from system.go. |
| `internal/probes/modules.go` | knowledge that `PrgEnv-*` modules are how compilers get loaded on Cray | names | New PE may not use PrgEnv naming. Module inventory + classification might still work; just the matching patterns change. |
| `internal/probes/mpi.go` | excludes `cray-mpich` from generic MPI probing (per the schema's carve-out) | flow | If CPE2 unbundles MPI, the carve-out should move to a unified `mpi_externals` flow. |
| `internal/probes/compiler.go` | excludes `cce`, `gcc`, `aocc`, etc. when they came from Cray PE | flow | Same — carve-out tied to current schema split. |
| `internal/probes/module_verify.go` | clean-shell verification of PrgEnv-* + cray-mpich modules | names | New module conventions, same verification pattern. |
| `internal/commands/merge.go` | merge logic that knows about the `vendor_cray` block shape | shape | Schema v2 means new merge rules. |
| `internal/model/profile.go` + `internal/model/fragments.go` | Go structs mirroring the profile schema's `vendor_cray` block | shape | Regenerated from schema; mechanical. |

Inventory snapshot: **9 Go files have Cray-PE-shaped knowledge.** Most are
self-contained to the inspector; the schema dependency makes them all
move together.

---

### stack-composer (Python) — renderer code

| File:line | Spot | Coupling | CPE2 likely change |
|---|---|---|---|
| `src/stack_composer/render/plan.py:165-177` + `src/stack_composer/render/scopes.py:74-80` | `vendor_scope_for(profile, contract)` resolves required `contract.vendor_scope_selectors`, and each rendered lane carries the selected `vendor_scope` | flow + names | CPE2 or another vendor should add a profile discriminator, a `contract.vendor_scope_selectors` entry, and a template-set scope; no Python render edit should be needed unless the selector language itself is insufficient. |
| `src/stack_composer/render/platform_modules.py:43-59` | `_compiler_modules` checks `vendor_cray.<compiler>` first, then falls back to `compilers_external` | shape + flow | Tied to the schema's `vendor_cray` block layout. |
| `src/stack_composer/render/platform_modules.py:68-82` | `_mpi_modules` special-cases `provider == "cray-mpich"` to read `vendor_cray.cray_mpich.flavors` | names + flow | Hardcoded provider name and special-case data path. **Generalize to per-provider `modules:` field in `profile.mpi[]`-style block.** |
| `src/stack_composer/render/plan.py:141-149` | `compiler_candidates()` enumerates `vendor_cray` compiler names in a hardcoded tuple `("gcc", "cce", "aocc", "intel", "nvhpc", "rocmcc")` | names + shape | New compilers added to CPE2 require code change. Could be schema-driven (iterate the block's keys). |
| `src/stack_composer/render/plan.py:168-169` | `mpi_provider_for()` returns `"cray-mpich"` if `profile.vendor_cray.cray_mpich` is set | flow | Hardcoded provider name + special-case path. |
| `src/stack_composer/render/environments.py:54-65` | `toolchain_for_lane()` reads `vendor_cray.<compiler>` for compiler version and the `cray_mpich` block for MPI metadata | shape + flow | Same coupling as plan.py and platform_modules.py. |
| `src/stack_composer/commands/explain.py:87` | `summarize_profile_facts` walks `vendor_cray` keys | shape | Schema-shaped enumeration. |
| `src/stack_composer/scaffold/facts.py:7-19,49` | Scaffold fact summarizer walks `vendor_cray.<compiler>` and emits `vendor_cray: bool` | shape | Same. |
| `src/stack_composer/commands/scaffold_templates.py:66` | `review_text` prints `vendor_cray: <bool>` in the proposed-template review | names | Cosmetic but exposes the schema vocabulary to maintainers. |
| `src/stack_composer/manifest/provenance.py:66` | `provenance_bucket` classifies an external as `platform_backed` if its prefix starts with `/opt/cray`, `/opt/rocm`, or `/usr` | paths | Path-prefix heuristic. Already flagged in PHASE_STATUS Phase 3 follow-ups. |

Inventory snapshot: **10 Python spots across 9 files.** Of those, the
three under `render/` are the load-bearing ones — the rest follow if
those move.

---

### stack-composer (Python) — fixture template-set and starters

| Spot | Coupling | CPE2 likely change |
|---|---|---|
| `tests/fixtures/template-sets/v6/configs/vendor/cray/packages.yaml.j2` | Renders cce/gcc/aocc/intel/rocmcc/nvhpc externals from `profile.vendor_cray` | shape | Read from a new schema block. |
| `tests/fixtures/template-sets/v6/configs/mpi/cray-mpich/packages.yaml.j2` | Renders per-flavor cray-mpich externals | shape | Probably a different shape for CPE2 MPI. |
| `src/stack_composer/scaffold/starters/{library,application}/configs/vendor/cray/...` | Mirror of the fixture | shape | Same. |
| `src/stack_composer/scaffold/starters/{library,application}/configs/mpi/cray-mpich/...` | Mirror | shape | Same. |

Inventory snapshot: **4 template files.** These are arguably the
least painful spots to change — a new template-set for CPE2 can be
authored alongside the v6 one, and the renderer happily selects
between them based on the profile.

---

### Design doc

| File:line | Spot | Coupling | CPE2 likely change |
|---|---|---|---|
| `stack-planning/docs/spack_stack_generation_design_v6.md` (415 mentions of "cray" total) | Examples and canonical packages.yaml templates for CPE | names + shape | A successor doc (v7 / cpe2 supplement) describes the new conventions; v6 stays valid for current CPE-shaped deployments. |
| `stack-planning/docs/cluster_inspector_profile_extraction_map_v1.md` | Extraction rules for `vendor_cray` fields | shape | Either extend in place or supplement with a `cpe2_extraction_map.md`. |

---

## Recommended hardening work (do BEFORE CPE2 lands)

Three changes that significantly reduce the CPE2 sprint:

### 1. Lift vendor selection from Python into the contract

Today: `render/scopes.py::vendor_scope` is `if profile.vendor_cray:
return "vendor/cray" else "vendor/linux"`. To add a third vendor, you
edit Python.

Implemented direction: declare the rule in `contract.yaml`:

```yaml
vendor_scope_selectors:
  cray:
    profile_key: vendor_cray
    scope: vendor/cray
  cpe2:
    profile_key: vendor_cpe2
    scope: vendor/cpe2
  linux:
    default: true
    scope: vendor/linux
```

Renderer evaluates profile-key selectors first and then the default.
New PE → new profile discriminator + contract entry + template-set
scope, no Python render change.

**Cost:** ~50 lines Python, plus a contract schema field, plus test.

### 2. Generalize the MPI special case

Today: `platform_modules.py::_mpi_modules` has
`if provider == "cray-mpich": <special path through vendor_cray>`. The
fact that cray-mpich has compiler-flavored externals is encoded in
*renderer code*.

Better: make every MPI provider describe its own `modules:` and
optional `flavors:` block in `profile.mpi[]`. The renderer becomes
provider-agnostic; cray-mpich just has more fields filled in than
openmpi does.

**Cost:** schema field migration (profile-v1 → v2 for MPI block),
~60 lines renderer code, inspector probe writes the new shape.

### 3. Enumerate compiler names from schema, not hardcoded tuples

Today: `plan.py:141-149`, `scaffold/facts.py:9-10`,
`explain.py:87` all iterate a hardcoded
`("gcc", "cce", "aocc", "intel", "nvhpc", "rocmcc")` tuple.

Better: iterate the keys present in the relevant profile block (skip
non-compiler fields like `pe_version`, `cray_mpich`, `libsci`,
`cce_extras`). Define the non-compiler exclusions in one place
(`render/known_blocks.py` or similar).

**Cost:** ~30 lines + 3 callsite updates.

---

## When CPE2 actually lands

Workflow that this doc enables:

1. Open this inventory.
2. For each spot, read the "CPE2 likely change" column against the new
   reality and confirm/refute.
3. Open a `cpe2-migration` branch and an issue per group of related
   spots (schema, inspector probes, renderer, templates).
4. Pick the order:
   - **Templates first** if the new PE structurally resembles CPE v1 —
     just write a new template-set and skip the rest.
   - **Schema first** if the new PE shape doesn't fit the existing
     `vendor_cray` block — bump to profile-v2 and migrate everything.
5. The smoke pipeline runtime is the verification surface. Stage a
   CPE2-shaped profile.yaml in the runtime and run the pipeline before
   declaring the migration done.
