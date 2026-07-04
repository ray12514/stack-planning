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

## Policy matrix shape

The managed renderer should not select Cray MPICH, ROCm/CUDA, GTL, LibSci, and
libfabric as independent externals. For Cray systems, it should first select a
**platform runtime set**, then render lanes from that coherent set.

Minimum policy fields:

| Policy axis | Meaning | Blueback example / current interpretation |
|---|---|---|
| `platform_family` | Vendor runtime family | `cray-pe` |
| `platform_release` | Site-selected CPE/runtime release | latest active CPE unless user pins one |
| `mpi.provider` | Platform MPI provider | `cray-mpich` |
| `mpi.version` | Selected MPI release | `9.1.0` for ROCm 7-era Blueback testing |
| `mpi.flavor.family` | Compiler family for MPI flavor | `gcc`, `cce`, `rocmcc`, etc. |
| `mpi.flavor.compiler_baseline` | Minimum compiler baseline read from the MPICH product path | `ofi/gnu/12.3` -> `gcc` baseline `12.3` |
| `compiler.selected` | Lane compiler selected by policy/user | e.g. `gcc@14.3.0` under `PrgEnv-gnu` |
| `compiler.compatibility` | How selected compiler relates to MPI flavor baseline | for Cray MPICH: same family and selected version >= baseline |
| `gpu.provider/version` | GPU runtime selected for GPU lanes | ROCm 7 with `cray-mpich@9.1.0`; ROCm 6.x with older CPE-era MPICH |
| `gtl.source` | How GTL is tied to MPI | GTL path must come from the selected `cray-mpich` prefix |
| `libfabric.source` | Preferred fabric runtime source | prefer Cray platform libfabric over site/admin `/p/app/unsupported` copies unless policy explicitly opts in |
| `libsci.source` | Math runtime source | select LibSci from the same platform runtime set/CPE policy |
| `pmi_pals.source` | Launcher/runtime integration source | select PMI/PALS from platform runtime set or explicit package repo policy |

The MPI flavor path is a **compiler baseline**, not an exact lane compiler pin.
For example, Blueback may expose `cray-mpich@9.1.0` with an `ofi/gnu/12.3`
flavor while the loaded `PrgEnv-gnu` compiler is `gcc@14.3.0`. That should be
treated as valid if policy says Cray MPICH uses `family_min_version` semantics:

```text
same compiler family and selected compiler version >= flavor baseline
```

Generic OpenMPI/MPICH providers should default to stricter semantics:

```text
same compiler family and exact compiler version, unless site policy overrides
```

## Compatibility evidence sources

Public sources rarely expose a complete machine-readable matrix. The policy
should combine:

1. public release/user-guide facts;
2. module/product-tree facts from cluster-inspector;
3. site policy for which discovered combinations are supported.

Current public evidence:

- OLCF Frontier states that `cpe/<YY.MM>` modules load "the set of compiler
  versions associated with that particular release of CrayPE" and warns that
  each `cray-mpich` release is compiled using a specific ROCm version, with
  cross-version compatibility not guaranteed.
- OLCF Frontier publishes a CrayPE/cce/cray-mpich/ROCm table that validates the
  matrix model: the supported unit is a CPE/runtime set, not independent
  package versions.
- HPE release notes identify the ROCm 7 transition in the CPE 26.03/Cray MPICH
  9.1.0 era; this should be treated as a major runtime boundary.
- LLNL El Capitan's known-good triples validate the ROCm 6-era pattern for
  MI300A systems: CPE/compiler/MPICH/ROCm combinations are published and tested
  together.

Blueback-specific facts that cluster-inspector should capture or the runbook
should confirm:

- selected/default CPE module set;
- selected `PrgEnv-*` compiler module and actual compiler version;
- selected `cray-mpich` module and product-tree flavor baselines;
- `PE_MPICH_GTL_DIR_*` / `PE_MPICH_GTL_LIBS_*` values from the selected MPI
  module;
- Cray platform libfabric loaded or implied by the selected CPE/module set;
- Cray LibSci version(s) selected by the active module set;
- ROCm/CUDA module version and GPU architecture.

## Validation rules to add

Stack Composer should validate the selected platform runtime set before writing
Spack configs:

| Rule | Severity |
|---|---|
| Cray MPICH GPU lane uses ROCm/CUDA major outside the selected MPICH/CPE policy range | error |
| Selected compiler family does not have an MPI flavor for that family | error |
| Selected compiler version is older than the MPI flavor compiler baseline under `family_min_version` policy | error |
| GTL path does not come from the selected `cray-mpich` prefix | error for GPU MPI lanes |
| Cray platform libfabric exists but a site/admin libfabric is selected without explicit policy | error or warning depending on lane policy |
| LibSci/PMI/PALS selected from a different platform runtime set than MPI | error |
| Public policy lacks an entry for a discovered CPE/MPICH/GPU major combination | warning for show; error for managed production render |

## Test sweep needed

The first Blueback smoke should be followed by a render-only sweep before any
large build:

| Scenario | Expected result |
|---|---|
| `cray-mpich@9.1.0 + gcc@14.3.0 + rocm@7.0 + gfx942` | pass if `gnu/12.3` baseline is selected |
| `cray-mpich@9.1.0 + gcc@10.x + rocm@7.0` | fail: compiler below baseline |
| `cray-mpich@9.1.0 + rocm@6.x` | fail: GPU runtime major mismatch |
| `cray-mpich@8.1.x + rocm@7.x` | fail unless explicit site policy allows it |
| selected GTL path under a different MPICH prefix | fail for GPU MPI lanes |
| site/admin libfabric selected while Cray platform libfabric is available | fail or warn per policy |
| LibSci version outside selected platform runtime set | fail |

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
- **GTL packaging direction**: for the first smoke run, an explicit GTL
  `LD_PRELOAD` workaround is acceptable if required. Pre-v1, move toward a
  package-repo-backed Cray runtime model instead of embedding GTL/PALS/PMI
  special cases in Stack Composer. See
  `cray_runtime_package_repo_note_v1.md`.
