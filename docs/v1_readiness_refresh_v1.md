# v1 Readiness Refresh

Recorded 2026-07-05, branch `codex/simplified-render-plan`. A synthesis of where
the four repos stand and what remains for a v1 release, after the Blueback smoke
passed and the render pipeline was firmed up. Detailed design lives in the
per-topic notes referenced inline; this is the map.

## Where we are

- **Real-system Cray smoke passed.** Blueback (HPE Cray EX, MI300A) rendered one
  coherent runtime set — PrgEnv-gnu, cray-mpich 9.1.0, ROCm 7.0.0, gfx942 — and
  reached the build path: `cluster-inspector -> profile.yaml -> validate/render
  -> spack-build`.
- **Render pipeline seam is complete.** All selection policy (MPI, GPU, common
  externals, compiler externals) is resolved once into the render context
  (`render/{network,gpu,common,compilers}.py`, plus `platform_plan`/
  `module_plan`); templates only print. The only template globals left are
  formatting helpers. See `simplified_render_plan_branch_v1.md`.
- **Inventory is cleaner.** cluster-inspector derives Cray facts from the PE
  product tree, dedups softlinked/same-version compilers, and derives the HIP
  prefix from the ROCm root. Dead code removed (vulture-clean).
- **Cray runtime packages are observed, not rendered.** GTL/PMI/PALS appear in
  `reports/render-plan.yaml` but are not written as externals without an
  explicit package-repo policy.

## Status by area

| Area | State | Reference |
|---|---|---|
| Plan-layer render seam | **Done** | `simplified_render_plan_branch_v1.md` |
| Cray real-system smoke | **Done** (Blueback) | runbook-notes |
| Generic Linux path | Built (fixtures green); **no real-system run yet** | — |
| Manual / Tier-0 consumption | Structural check only; no `spack concretize` on a box | `manual_config_catalog_note_v1.md` |
| Collapsed inventory schema (nested versions) | Designed, **not built** | `platform_runtime_set_design_v1.md` |
| CPE-locked GPU/MPI compat validation | Rules written, **not implemented** | `cpe_rocm_compatibility_note_v1.md` |
| GTL preload elimination (package repo) | Designed, **not built**; preload is the run-#1 workaround | `cray_runtime_package_repo_note_v1.md` |
| Manual config catalog command | **Not built** | `manual_config_catalog_note_v1.md` |
| Multi-CPE fan-out | **Not built**; deferred v1 goal | `platform_runtime_set_design_v1.md` |
| libsci / fabric rendered from selected set | **Not built** (observed only) | `cray_runtime_package_repo_note_v1.md` |

## Known open questions

1. **Compiler version pinning.** `mpi.version` exists in the stack schema; there
   is no `compiler.version` pin. Today compiler selection is family_min_version
   "newest satisfying the flavor baseline." Decide whether v1 needs an explicit
   compiler pin (guard: reject a pin below the flavor baseline). Likely yes for
   parity with `mpi.version`, but low priority if the default is right.
2. **GTL for v1.** Is the documented `LD_PRELOAD` workaround acceptable for a v1
   release, or must the package-repo path (no preload) land first? This gates
   whether GPU-aware MPI is "supported" or "workaround-documented" in v1.
3. **Collapsed inventory schema.** The nested-version inventory is a cleaner
   representation but a cross-repo schema change. Is it v1, or does the current
   flat-but-deduped inventory suffice for v1?
4. **Manual config catalog & multi-CPE.** Both are designed and both are real
   goals — but are they *v1* or *post-v1*? This is the biggest scope lever.

## Proposed v1 definition of done

Minimum for a defensible v1 (one managed stack, two system families):

1. Plan-layer render seam. **(done)**
2. Cray real-system smoke, oracle-checked. **(done — Blueback)**
3. **Generic Linux real-system smoke** — the current gap that most reduces risk.
4. **CPE-locked compatibility validation** — refuse cross-major GPU/MPI pairings
   at render, so a bad combination fails before a build, not at runtime.
5. GTL decision resolved (workaround-documented *or* package repo).
6. Explicit v1/post-v1 line drawn for: manual config catalog, multi-CPE,
   collapsed schema.

Everything past line 6 is post-v1 unless a decision pulls it in.

## Test sequence (agreed direction)

1. **Generic Linux cluster smoke first.** It exercises the same plan layer with
   no Cray-specific runtime, so it is the cleanest proof the seam is not
   Cray-coupled — and it is the untested path. Add a generic multi-provider
   render fixture before the run.
2. **Then re-run Cray (Blueback)** with the refreshed pipeline to confirm no
   regression from the firming-up.

## Decisions needed to lock v1 scope

- Which of {manual config catalog, multi-CPE fan-out, GTL package repo,
  collapsed inventory schema} are **v1** vs **post-v1**?
- GTL: preload-documented acceptable for v1, or eliminate first?
- Compiler version pin: needed for v1?

These four decisions size the remaining v1 work; everything else above is either
done or a small, well-scoped slice.
