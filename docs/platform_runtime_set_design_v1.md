# Platform Runtime Set: Design v1

Status: accepted target with partial implementation. Compiler/MPI flavor
selection is implemented; exact multi-CPE runtime-tuple binding remains open.
Written after a
day of Blueback render validation to stop independently selecting facts that
must be treated as one coherent platform set.
Builds on `cpe_rocm_compatibility_note_v1.md` (policy matrix,
family_min_version), `cray_runtime_package_repo_note_v1.md` (GTL/runtime
packaging), `lane_and_module_model_v1.md`, and `manual_config_catalog_note_v1.md`.

## Decisions from review (2026-07-04)

1. **family_min_version is correct** and is how the Cray PE actually works:
   loading a `PrgEnv-*` gives you a compiler; the flavor baseline is a *floor*,
   and any same-family compiler at or above it is interchangeable. The only
   guard needed is on an explicit user pin: **reject a pinned compiler below the
   flavor baseline** for that image. No `cpe_version` tag needed to make
   compiler selection correct.
2. **More inspector work is acceptable, and wanted**: specifically to
   *collapse* the inventory (see "Collapsed inventory model" below). The
   inventory today is too spread out.
3. **Generic Linux keeps the existing per-provider model** with the
   `mpi.version` ambiguity rule; the coherent-set logic here is Cray-specific.
4. **No libsci/GTL packaging for run #1.** GTL is part of Cray MPICH but must be
   opted into to link; that needs our own package repo or a spec-level opt-in
   (`cray_runtime_package_repo_note_v1.md`), which is later work. Run #1
   validates compiler + cray-mpich + ROCm selection only.

## The problem we keep hitting

cluster-inspector reports the raw inventory: on Blueback that is **six CPEs**
of `cray-mpich` (8.1.27 … 9.1.0), each with per-compiler-family flavors, plus
compilers reported multiple times (softlinked `gcc@14.3.0` at three prefixes).
stack-composer then renders the **full cartesian product** (every version ×
every flavor × every duplicate compiler) as one giant `packages.yaml`/
`toolchains.yaml` catalog.

Every error this week is a symptom of that one choice:

- `cray-mpich@8.1.27 %gcc@14.3.0 depends on gcc@14.3.0, multiple externals`:
  an old CPE we should not render, referencing a compiler that appears 3× from
  softlinks.
- "Why is it picking the oldest cray-mpich?": it is not picking; it is
  *validating all six* and erroring on one.
- Dangling `%aocc@4.1.0`, dropped gcc flavors, exploded toolchain names: all
  combinatorial artifacts of rendering inventory instead of a selection.

Patching each combination is a losing game. The fix is to **select one coherent
set and render only that.**

## Core concept: the Platform Runtime Set

On a Cray EX the supported unit is not an individual package version: it is the
**CPE release**, a set of versions built and validated together: a compiler set
(one version per family), a `cray-mpich` version with per-family flavors,
`cray-libsci`, the GPU runtime major (ROCm/CUDA) the GTL was built against, and
the fabric runtime (libfabric/GTL/PMI/PALS). HPE gives "a very narrow statement
of compatibility"; mixing members across CPEs is unsupported in both directions
(sources in `cpe_rocm_compatibility_note_v1.md`).

A **Platform Runtime Set** is our name for that coherent, versioned-together
unit. The managed render operates on exactly one of them.

## Selection: anchored on the MPI provider version

The selection key is the `cray-mpich` version: it is the MPI-lane anchor, and
its product-tree flavors already encode the compiler pairing
(`ofi/gnu/12.3` = "built against the gnu 12.3 baseline").

Selection order (composer, at plan time):

1. **Pick the cray-mpich version.** Default: the latest available. Override:
   `stack.yaml` `mpi.version` (field already exists). This is the
   `platform_release` policy from the compatibility note, made concrete.
2. **Derive usable compiler families + baselines** from that version's flavors.
3. **Select one compiler per family**: the deduplicated provider of that family
   with the newest version satisfying the flavor baseline (`family_min_version`
   for Cray MPICH, already implemented in `compiler_ref_satisfies_flavor`).
   On Blueback: gnu flavor baseline 12.3 → `gcc@14.3.0`.
4. **Match the GPU runtime** (ROCm/CUDA major) by the CPE↔GPU matrix; validate
   the toolkit major is in range (compatibility note's validation rules).
5. **Match `cray-libsci` / fabric** from the same release.

Everything the render emits comes from this one resolved set. Nothing else is
rendered.

### GPU runtime ↔ MPI mapping (policy on evidence)

Which ROCm/CUDA pairs with which cray-mpich is **policy**, not pure inventory,
but it sits on discoverable evidence. Keep the two separate:

- **Evidence (inspector, facts):** per cray-mpich version, the GPU runtime its
  GTL was built against: the amd flavor baseline (`ofi/amd/7.0`) and the
  `PE_MPICH_GTL_DIR/LIBS_amd_*` module vars. Report this alongside the collapsed
  ROCm inventory.
- **Authority (curated matrix, policy):** what is *supported*, e.g.
  `cray-mpich 9.1.0 → ROCm ">=7.0"`, `8.1.29 → ROCm 6`, and the "ROCm 6 no
  longer supported on 26.03" cutoffs. Not on the filesystem; distilled from
  `cpe_rocm_compatibility_note_v1.md`. Lives as a machine-readable
  compatibility-matrix data file owned by content/template policy,
  site-extensible.

Composer, during coherent-set selection:

1. Pick cray-mpich version (latest / `mpi.version`).
2. Resolve its supported GPU-runtime major from the matrix (authority), using
   the product-tree GTL evidence as cross-check / fallback when the matrix lacks
   an entry (warn, don't silently guess, for managed production).
3. Select the matching ROCm/CUDA from the collapsed inventory.
4. **Hard-error** if no matching runtime is installed, or if a requested runtime
   is outside the supported range (the compatibility note's validation rules).

Anchoring is MPI → GPU-runtime (the cray-mpich version is the CPE anchor). The
inventory shows all ROCm versions collapsed; policy maps the pairing; the
composer selects one. Run #1 needs a trivial matrix (`9.1.0 → ROCm 7`); it grows
per CPE.

### Why default-latest-with-opt-in, not inspector pre-filtering

You asked whether the inspector should just report the latest CPE. Recommend
**no**: the inspector reports the *full deduplicated* inventory (all CPEs,
tagged), and the composer selects. Reasons:

- Selection is policy; the inspector's job is facts. Keeping selection in the
  composer is what makes the **opt-in** you also want possible: a stack can pin
  an older CPE without re-running discovery differently.
- The inspector still helps by **grouping/tagging** CPE membership so the
  composer's selection is trivial and legible (see below).

## Ownership boundaries

| Repo | Owns | Concretely |
|---|---|---|
| cluster-inspector | Deduplicated inventory + CPE-membership facts | Resolve softlinks so each `(name, version)` compiler is reported once with a canonical prefix; tag providers with `cpe_version` where derivable; keep reporting cray-mpich flavor→baseline maps. |
| stack-composer | Select one runtime set, render only that | Pick cray-mpich version (latest/opt-in); resolve members; render one cray-mpich version's externals + toolchains, one compiler per family, matched ROCm/libsci. No catalog. |
| stack-content | Pin policy | Default = latest; `mpi.version` (and future compiler pins) to opt into a specific CPE. |

## Rendered output contract (the change)

For a managed Cray render, the workspace contains **exactly one runtime set**:

- `configs/vendor/cray/packages.yaml`: one external per compiler family, the
  selected version, deduplicated. Not three `gcc@14.3.0`.
- `configs/mpi/cray-mpich/packages.yaml`: **one** cray-mpich version; its
  flavors bound to the selected compilers (family_min_version). No other
  versions.
- `configs/mpi/cray-mpich/toolchains.yaml`: one toolchain per flavor of that one
  version. Clean names (no six-version explosion).
- `configs/gpu/amd-rocm` (or nvidia): the ROCm/CUDA matched to that cray-mpich.

This bounds the render. The combinatorial problems cannot occur because the
combinations are never emitted.

## Collapsed inventory model (inspector)

The inventory is sloppy today because it is *spread out*: `cray-mpich` is six
flat entries, `gcc@14.3.0` is listed three times (softlinks), ROCm 6 and 7 are
separate packages. The model should be **one logical entry per package, with its
versions and locations nested underneath**: "this package exists, supports
these versions, at these prefixes, for these compilers." One entry, collapsed,
still showing the full support surface.

Today (flat, one entry per version × prefix):

```yaml
mpi_providers:
- {name: cray-mpich, version: 8.1.27, flavors: {...}}
- {name: cray-mpich, version: 8.1.29, flavors: {...}}
- ... (six entries)
compiler_providers:
- {name: gcc, version: 14.3.0, prefix: /opt/cray/pe/gcc-native/14}
- {name: gcc, version: 14.3.0, prefix: /opt/cray/pe/gcc/14.3.0}   # softlink dup
```

Collapsed (one entry per package, versions nested):

```yaml
mpi_providers:
- name: cray-mpich
  provider_family: platform
  platform_family: cray-pe
  versions:
    - version: 9.1.0
      cpe_version: "26.03"          # advisory tag
      flavors:                      # keyed by compiler FAMILY, baseline a field
        gcc:    {baseline: "12.3", prefix: .../ofi/gnu/12.3, modules: [...]}
        rocmcc: {baseline: "7.0",  prefix: .../ofi/amd/7.0,  modules: [...]}
    - version: 8.1.29
      cpe_version: "24.07"
      flavors: {...}

compiler_providers:
- name: gcc
  provider_family: platform
  platform_family: cray-pe
  versions:
    - version: 14.3.0
      canonical_prefix: /opt/cray/pe/gcc-native/14
      aliases: [/opt/cray/pe/gcc/14.3.0]     # collapsed softlinks
      modules: [PrgEnv-gnu, gcc-native/14]

gpu_toolkits:
- name: rocm
  versions:
    - {version: "7.0.0", prefix: <site-rocm-root>/rocm-7.0.0, modules: [rocm/7.0.0]}
    - {version: "6.0.0", prefix: <site-rocm-root>/rocm-6.0.0, modules: [rocm/6.0.0]}
```

`<site-rocm-root>` is an explanatory placeholder. Rendered profile YAML must
contain the absolute prefix observed on the target system.

Rules this encodes:

1. **Collapse by logical package.** One `cray-mpich`, one `gcc`, one `rocm`:
   versions nested. The human view (and `stack-composer show`) reads this
   directly; no more scrolling a spread-out list.
2. **Softlink/duplicate dedup.** Each `(name, version)` appears once, with a
   `canonical_prefix` (symlink-resolved) and its `aliases`. Fixes the current
   `multiple externals for gcc@14.3.0` error at the source.
3. **Flavor key is the compiler family, baseline is a field.** `gcc` with
   `baseline: "12.3"`, not the composite `gcc@12.3` key that caused the
   baseline-vs-exact confusion.
4. **Multi-version is kept, not discarded.** ROCm 6 and 7 both listed (one
   `rocm` entry), because when multiple cray-mpich versions exist, their
   compatible ROCm majors differ, and the render's coherent-set selection needs
   both present to match one to the chosen MPI. The inventory shows everything,
   collapsed; the composer selects one.
5. **CPE tagging** (`cpe_version`) advisory: selection works version-anchored
   without it, but it makes the render plan legible and enables multi-CPE
   fan-out later.

This normalization is the "redesign": it changes the profile schema (canonical
in `stack-planning/schemas`, mirrored in the inspector), the inspector's output,
the composer's consumption, and the fixtures. It can land as one coordinated
change or staged (compilers first, then mpi/gpu).

## Scope boundary

This design is the **managed render** (Stack Composer owns package intent → one
coherent set). It is deliberately *not* the **static platform catalog**
(`manual_config_catalog_note_v1.md`), a separate product where a full
multi-flavor catalog is a feature, not a bug. Do not let the catalog use case
pull the managed render back toward rendering everything.

## Concrete changes (once this design is accepted)

1. **stack-composer / plan**: cray-mpich version selection already picks latest
   for platform providers (`select_platform_mpi`); confirm every lane carries
   the one resolved `mpi_version`.
2. **stack-composer / scopes**: thread `rendered_lanes` into
   `mpi_external_packages` and filter externals/toolchains to the lane-selected
   version(s) only. This is the single change that collapses the catalog.
3. **stack-composer / scopes**: dedup compiler externals by `(name, version)` at
   render as a belt-and-suspenders guard even after inspector dedup.
4. **cluster-inspector**: softlink/duplicate compiler dedup; optional
   `cpe_version` tagging.
5. **Tests**: a fixture that mirrors Blueback (six cray-mpich versions,
   softlinked duplicate compiler, newer-than-baseline compilers), asserting the
   render emits exactly one version's set, one compiler per family, clean
   toolchains.

## Implementation sequencing (once accepted)

Because the collapse is a schema change, stage it to avoid a big-bang:

1. **Inspector: collapse + dedup compilers first** (smallest, highest-value,
   fixes the `multiple gcc@14.3.0` error). One `gcc` entry, versions nested,
   softlinks collapsed to `canonical_prefix` + `aliases`.
2. **Schema: collapsed `mpi_providers` + `gpu_toolkits`** (nested versions;
   family-keyed flavors with `baseline`). Canonical in `stack-planning/schemas`,
   mirror to inspector.
3. **Composer: consume collapsed inventory + select one runtime set.** Pick
   cray-mpich version (latest / `mpi.version`); resolve compilers via
   family_min_version; match ROCm major; render only that set: one version's
   externals + toolchains, one compiler per family. Reject a pinned compiler
   below the flavor baseline.
4. **Blueback-shaped fixture + tests**: six versions, softlinked compiler,
   newer-than-baseline compilers → assert exactly one coherent set renders.

Run #1 stops at step 3's ROCm match: no libsci/GTL packaging.

## Confirmed decisions

All four review questions are resolved in "Decisions from review" above:
family_min_version is correct (guard: reject pins below baseline); more inspector
work (collapse) is wanted; generic Linux path unchanged; no libsci/GTL for
run #1. Selection stays cray-mpich-version-anchored with `cpe_version` as an
advisory tag.
