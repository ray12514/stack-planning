# Platform Runtime Set — Design v1

Status: proposed 2026-07-04. Written after a day of Blueback render thrash to
stop patching a catalog that should not exist. Builds on
`cpe_rocm_compatibility_note_v1.md` (policy matrix, family_min_version),
`cray_runtime_package_repo_note_v1.md` (GTL/runtime packaging),
`lane_and_module_model_v1.md`, and `manual_config_catalog_note_v1.md`.

## The problem we keep hitting

cluster-inspector reports the raw inventory: on Blueback that is **six CPEs**
of `cray-mpich` (8.1.27 … 9.1.0), each with per-compiler-family flavors, plus
compilers reported multiple times (softlinked `gcc@14.3.0` at three prefixes).
stack-composer then renders the **full cartesian product** — every version ×
every flavor × every duplicate compiler — as one giant `packages.yaml`/
`toolchains.yaml` catalog.

Every error this week is a symptom of that one choice:

- `cray-mpich@8.1.27 %gcc@14.3.0 depends on gcc@14.3.0, multiple externals` —
  an old CPE we should not render, referencing a compiler that appears 3× from
  softlinks.
- "Why is it picking the oldest cray-mpich?" — it is not picking; it is
  *validating all six* and erroring on one.
- Dangling `%aocc@4.1.0`, dropped gcc flavors, exploded toolchain names — all
  combinatorial artifacts of rendering inventory instead of a selection.

Patching each combination is a losing game. The fix is to **select one coherent
set and render only that.**

## Core concept: the Platform Runtime Set

On a Cray EX the supported unit is not an individual package version — it is the
**CPE release**, a set of versions built and validated together: a compiler set
(one version per family), a `cray-mpich` version with per-family flavors,
`cray-libsci`, the GPU runtime major (ROCm/CUDA) the GTL was built against, and
the fabric runtime (libfabric/GTL/PMI/PALS). HPE gives "a very narrow statement
of compatibility"; mixing members across CPEs is unsupported in both directions
(sources in `cpe_rocm_compatibility_note_v1.md`).

A **Platform Runtime Set** is our name for that coherent, versioned-together
unit. The managed render operates on exactly one of them.

## Selection: anchored on the MPI provider version

The selection key is the `cray-mpich` version — it is the MPI-lane anchor, and
its product-tree flavors already encode the compiler pairing
(`ofi/gnu/12.3` = "built against the gnu 12.3 baseline").

Selection order (composer, at plan time):

1. **Pick the cray-mpich version.** Default: the latest available. Override:
   `stack.yaml` `mpi.version` (field already exists). This is the
   `platform_release` policy from the compatibility note, made concrete.
2. **Derive usable compiler families + baselines** from that version's flavors.
3. **Select one compiler per family**: the deduplicated provider of that family
   with the newest version satisfying the flavor baseline (`family_min_version`
   for Cray MPICH — already implemented in `compiler_ref_satisfies_flavor`).
   On Blueback: gnu flavor baseline 12.3 → `gcc@14.3.0`.
4. **Match the GPU runtime** (ROCm/CUDA major) by the CPE↔GPU matrix; validate
   the toolkit major is in range (compatibility note's validation rules).
5. **Match `cray-libsci` / fabric** from the same release.

Everything the render emits comes from this one resolved set. Nothing else is
rendered.

### Why default-latest-with-opt-in, not inspector pre-filtering

You asked whether the inspector should just report the latest CPE. Recommend
**no** — the inspector reports the *full deduplicated* inventory (all CPEs,
tagged), and the composer selects. Reasons:

- Selection is policy; the inspector's job is facts. Keeping selection in the
  composer is what makes the **opt-in** you also want possible — a stack can pin
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

- `configs/vendor/cray/packages.yaml`: one external per compiler family — the
  selected version, deduplicated. Not three `gcc@14.3.0`.
- `configs/mpi/cray-mpich/packages.yaml`: **one** cray-mpich version; its
  flavors bound to the selected compilers (family_min_version). No other
  versions.
- `configs/mpi/cray-mpich/toolchains.yaml`: one toolchain per flavor of that one
  version. Clean names (no six-version explosion).
- `configs/gpu/amd-rocm` (or nvidia): the ROCm/CUDA matched to that cray-mpich.

This bounds the render. The combinatorial problems cannot occur because the
combinations are never emitted.

## Inventory-quality rules (inspector)

1. **Softlink/duplicate dedup.** Group compiler providers by `(name, version)`;
   resolve prefixes with symlink evaluation; if several remain, prefer the
   platform/CPE entry (`provider_family: platform`, `platform_family: cray-pe`)
   and keep one canonical prefix. Report once. (Directly fixes the current
   `multiple externals for gcc@14.3.0` error.)
2. **CPE tagging.** Where derivable from the module set / product tree, tag
   cray-mpich versions (and compilers, where unambiguous) with `cpe_version`.
   Advisory: selection still works version-anchored without it, but tags make
   the render plan legible and enable future multi-CPE fan-out.

## Scope boundary

This design is the **managed render** (Stack Composer owns package intent → one
coherent set). It is deliberately *not* the **manual config catalog**
(`manual_config_catalog_note_v1.md`), a separate future flow where a full
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
5. **Tests**: a fixture that mirrors Blueback — six cray-mpich versions,
   softlinked duplicate compiler, newer-than-baseline compilers — asserting the
   render emits exactly one version's set, one compiler per family, clean
   toolchains.

## Open questions for review

1. **Is "newest compiler satisfying the flavor baseline" always the CPE
   compiler?** On a clean CPE it should be, but a newer non-CPE gcc installed
   outside the PE could beat it. Acceptable as default + opt-in, or do we need
   the inspector's `cpe_version` tag to be authoritative for compiler selection?
2. **Selection key: cray-mpich version (proposed) vs. explicit CPE version.**
   Anchoring on cray-mpich needs no cpe-module probing and reuses existing
   fields. Explicit CPE version is conceptually cleaner but needs the inspector
   to resolve CPE→members. Proposed: cray-mpich anchor now, cpe tag as advisory.
3. **Non-Cray systems.** This is Cray-specific (CPE coherence). Generic Linux
   keeps the existing per-provider model with the `mpi.version` ambiguity rule.
   Confirm no regression to the generic path.
4. **libsci/fabric matching** depth for run #1 — is validating the cray-mpich
   version enough, or do we render libsci/GTL from the same set now?
