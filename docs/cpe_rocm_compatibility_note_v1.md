# CPE / ROCm / cray-mpich Compatibility Note v1

Researched 2026-07-01 (sources linked inline). Records the compatibility rules
that drive the deferred CPE-locked render validation and the multi-CPE v1
design. Recorded here so the research does not have to be repeated.

## The rule

ROCm, cray-mpich, and CCE are versioned **together per CPE release**, and HPE
gives only "a very narrow statement of compatibility" (LLNL). The GPU-aware
layer (GTL) in each cray-mpich release is compiled against a specific GPU
runtime; cross-version compatibility is not guaranteed:

> "Releases of cray-mpich are each compiled using a specific version of ROCm,
> and compatibility across multiple versions is not guaranteed."
> — [OLCF Frontier guide](https://docs.olcf.ornl.gov/systems/frontier_user_guide.html)

## Matrix highlights (see Frontier guide for the full table)

| CPE | cray-mpich | ROCm support |
|---|---|---|
| 24.03 | 8.1.29 | 6.0-era; HPE: "not backwards compatible with previous versions of ROCm" ([announcement](https://cpe.ext.hpe.com/docs/24.03/release_announcements/CPE-24.03-CSM-Release-Announcement.html)) |
| 24.07–25.09 | 8.1.30–9.0.1 | ROCm 6.x era |
| 26.03 | 9.1.0 | ROCm 7 ("Enable ROCM 7 support", GTL changelog CPE-13399); CCE 21: ROCm 6.x "no longer supported" ([release notes](https://cpe.ext.hpe.com/docs/latest/release_notes/sles_15_6_release_notes.html)) |

Cross-major pairings are unsupported in **both** directions (ROCm 7 over a
ROCm-6-era cray-mpich, and ROCm 6 over cray-mpich 9.1.0). Treat the two CPE
stacks as disjoint lanes; never mix components across CPE releases.

Known-good MI300A triples published by
[LLNL El Capitan](https://hpc.llnl.gov/documentation/user-guides/using-el-capitan-systems/known-issues):
`cce/17.0.1 + cray-mpich/8.1.29 + rocm/6.0.3 or 6.1.2`, and
`cce/18.0.0 + cray-mpich/8.1.30 + rocm/6.1.2 or 6.2.0`. The most commonly
cited breakage mode for mismatches is CCE Fortran module-file incompatibility.

## NVIDIA analog

Same major-version coupling: cray-mpich 9.1.0's GTL moved to CUDA 13 in the
same release (CPE-13351). CUDA's driver-level minor-version/forward
compatibility is **not** confirmed to extend to the GTL — apply the same
CPE-locked pairing logic on NVIDIA systems.

## Implications for the tools

- **Profile facts** (cluster-inspector / profile schema): per-provider
  `cpe_version` (the authoritative key — already sketched as deferred in
  `lane_and_module_model_v1.md`), plus per-MPI GPU-runtime linkage
  (e.g. cray-mpich 8.1.29 -> `rocm@6.0:`, 9.1.0 -> `rocm@7.0:`).
- **Render validation** (stack-composer preflight): hard-error a GPU lane that
  pairs a toolkit major outside its MPI's declared range, or mixes
  `cpe_version` tags across compiler/MPI/toolkit; warn (not fail) on minor
  versions above the officially supported one. Providers without these facts
  validate as today.
- **Blueback run #1**: the profile captured the system default = the new
  ROCm 7-era CPE. The known-good Kokkos baseline was the prior CPE, so the
  oracle diff is structural (flavor paths, toolchain binding), not
  version-exact.
