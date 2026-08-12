# CCE, AOCC, and GNU on AMD-based HPE Cray EX systems (v1)

| Document control | |
|---|---|
| Date | 2026-08-12 |
| Status | Research note for initial CSE conversion trials |
| Question | Does an AMD CPU imply AOCC, or should CCE/GNU remain normal Cray EX build surfaces? |
| Method | Primary sources only: HPE CPE documentation and official production-site documentation |

## Conclusion

An AMD CPU does **not** imply that AOCC should be the platform baseline.
Production HPE Cray EX sites treat the compiler as one part of a coherent
programming environment, selected for application suitability and site support,
while the CPU and GPU architecture are separate compilation targets.

CCE is not an Intel-only or generic fallback compiler. HPE states that CCE
targets x86-64 processors from both Intel and AMD, Arm processors, and AMD and
NVIDIA accelerators. HPE also integrates GNU and AMD compiler environments with
the same CPE libraries and tools. HPE Cray MPI is similarly tuned for Intel,
AMD, and Arm CPUs and for AMD and NVIDIA GPUs
([HPE CPE overview](https://cpe.ext.hpe.com/docs/latest/)).

The maintainable CSE model is therefore:

- select a compiler **surface** from observed, site-supported programming
  environments;
- select the CPU/GPU target independently (`craype-x86-*`,
  `craype-accel-*`, or the equivalent Spack target);
- pair every compiler surface with the Cray MPICH external built for that
  compiler family and version;
- do not infer `AOCC` merely from `vendor: AMD` in the processor inventory.

## What production sites actually do

| System | AMD hardware | Offered compiler environments | Site default or practice | Implication |
|---|---|---|---|---|
| Frontier (OLCF) | AMD EPYC CPU and AMD MI250X GPUs | CCE, AMD/ROCm, GNU | All three are supported; the guide recommends the common `cc`, `CC`, and `ftn` wrappers and describes `PrgEnv-amd` as the environment for AMD host compilers. Cray MPICH is the system MPI. | Even the flagship all-AMD Cray EX is multi-compiler. AMD hardware does not collapse policy to one AMD compiler. |
| LUMI | AMD Milan/Trento CPUs and AMD MI250X GPUs | CCE, GNU, AOCC, AMD/ROCm | `PrgEnv-cray` is loaded at login. LUMI distinguishes `PrgEnv-aocc` for CPU-only work from `PrgEnv-amd` for the ROCm compiler environment on the GPU partition. | AOCC and AMD/ROCm are distinct surfaces; neither replaces CCE because the processor vendor is AMD. |
| Setonix (Pawsey) | AMD Milan/Trento CPUs and AMD MI250X GPUs | CCE, GNU, AOCC | GNU is loaded by default. Pawsey's August 2025 update continued to recommend against AOCC because of ongoing issues and maintained GNU and CCE software stacks. | A production all-AMD Cray EX can deliberately prefer GNU and CCE over AOCC. Site validation outweighs CPU-brand affinity. |
| Perlmutter (NERSC) | AMD EPYC CPUs; NVIDIA A100 GPUs | CCE, GNU, AOCC, NVIDIA (plus Intel/LLVM availability) | GNU is the default. NERSC tells users to select the compiler best suited to the application and supplies each vendor compiler through a complete programming environment. | AMD host CPUs coexist with GNU/CCE/NVIDIA-oriented workflows; the accelerator and application model affect compiler choice. |

Sources:

- [Frontier compiler, programming-environment, and MPI guidance](https://docs.olcf.ornl.gov/systems/frontier_user_guide.html#compiling)
- [LUMI programming environments and architecture targets](https://docs.lumi-supercomputer.eu/development/compiling/prgenv/)
- [LUMI software-stack compiler distinctions](https://docs.lumi-supercomputer.eu/runjobs/lumi_env/softwarestacks/)
- [Setonix software environment](https://pawsey.atlassian.net/wiki/spaces/US/pages/51929054/Setonix%2BSoftware%2BEnvironment)
- [Pawsey August 2025 compiler recommendation](https://pawsey.atlassian.net/wiki/spaces/US/pages/878772225/August%2B2025%2BSoftware%2BUpdate%2B-%2BImportant%2BInformation)
- [NERSC base compilers](https://docs.nersc.gov/development/compilers/base/)

## CCE versus AOCC versus AMD/ROCm

These names should not be conflated:

- **CCE / `PrgEnv-cray`** is HPE's compiler suite. It supports AMD x86 CPUs
  and AMD GPU offload as well as other HPE-supported architectures. On LUMI it
  is the login default, and on Frontier it is a normal supported environment.
- **AOCC / `PrgEnv-aocc`** is AMD's CPU-oriented optimizing compiler suite.
  HPE enables integration but does not bundle AOCC itself; administrators must
  install it and the CPE support bundle
  ([HPE CPE user guide](https://cpe.ext.hpe.com/docs/24.11/getting_started/CPE-General-User-Guide-CSM.html#about-aocc)).
  LUMI explicitly describes its AOCC toolchain as being for CPU-only work.
- **AMD/ROCm / `PrgEnv-amd`** is the ROCm compiler environment used for AMD GPU
  systems. Frontier exposes `amdclang`, `amdclang++`, and `amdflang` through
  this environment; LUMI offers it on the GPU partition. It is not the same
  provider identity as AOCC.
- **GNU / `PrgEnv-gnu`** is a first-class CPE programming environment, not an
  unsupported generic escape hatch. Both Setonix and Perlmutter use it as the
  default despite their AMD host CPUs.

Consequently, a profile field such as `cpu.vendor: amd` may guide the target
(`zen3`, `x86_milan`, `x86_trento`, and so on), but it cannot decide whether
the compiler provider is `cce`, `aocc`, `rocmcc`/AMD, or `gcc`.

## How Cray MPICH pairs with these choices

Cray MPICH remains the platform MPI across compiler environments. The common
Cray wrappers select the active underlying compiler and add the matching MPI,
LibSci, and other CPE include/link options. Frontier documents that a
`PrgEnv-<compiler>` loads compatible toolchain components, including MPI, and
LUMI states that loading a programming environment loads `cray-mpich`; MPI
applications are compiled with the same `cc`, `CC`, and `ftn` wrappers
([Frontier](https://docs.olcf.ornl.gov/systems/frontier_user_guide.html#cray-programming-environment-and-compiler-wrappers),
[LUMI](https://docs.lumi-supercomputer.eu/development/compiling/prgenv/#compile-an-mpi-program)).

For driver-less Spack use, that wrapper behavior must become explicit catalog
data. HPE's Spack documentation shows separate Cray MPICH installations under
`ofi/amd`, `ofi/aocc`, `ofi/cray`, `ofi/gnu`, `ofi/intel`, and `ofi/nvidia`, and
instructs users to choose the prefix corresponding to the compiler. Its example
maps distinct `%cce`, `%gcc`, and `%rocmcc` external specs to distinct prefixes
([HPE CPE Spack user documentation](https://cpe.ext.hpe.com/docs/latest/craype/spack.html#cpe-software-configuration)).

Thus `cray-mpich@X` is not one compiler-neutral external in the CSE catalog.
It is a family of observed pairings such as:

```text
cce@A       + cray-mpich@X from ofi/cray/A
gcc@B       + cray-mpich@X from ofi/gnu/B
aocc@C      + cray-mpich@X from ofi/aocc/C
rocmcc@D    + cray-mpich@X from ofi/amd/D
```

GPU-aware MPI adds another compatibility axis: the Cray MPICH release must be
compatible with the selected ROCm release and GTL. OLCF advises loading a
coherent CPE release and publishes tested CCE/ROCm/Cray MPICH combinations;
this reinforces release-level tuple selection rather than CPU-vendor inference
([Frontier compatibility guidance](https://docs.olcf.ornl.gov/systems/frontier_user_guide.html#understanding-the-compatibility-of-compilers-rocm-and-cray-mpich)).

## Practical implications for the initial CSE conversion trials

1. **Keep the CSE GCC surface.** It is the cross-system consistency surface.
   On a Cray EX it should consume the observed `ofi/gnu/<flavor>` Cray MPICH
   external; the selected GCC must satisfy the already-recorded flavor
   compatibility rule.
2. **Keep CCE + Cray MPICH as the first Cray-native baseline.** This is well
   supported on AMD Cray EX systems and matches actual production practice.
   The fact that the node CPU is AMD is not evidence to replace it with AOCC.
3. **Treat AOCC as an optional, evidence-gated surface.** Generate it only when
   the target system reports a supported AOCC compiler and matching
   `ofi/aocc/<version>` Cray MPICH prefix, and the site has not discouraged the
   environment. Setonix is concrete evidence that installation alone does not
   make AOCC the blessed baseline.
4. **Model AMD/ROCm separately from AOCC.** For an AMD GPU programming surface,
   use the provider identity observed for `PrgEnv-amd`/ROCm and the `ofi/amd`
   MPI flavor. Do not render it as `aocc` merely because both come from AMD.
5. **Let site policy select the platform baseline.** Prefer, in order:
   an explicit profile/config choice; the site's documented or observed
   default `PrgEnv`; then a conservative CCE baseline on Cray EX. CPU vendor
   should select target tuning, not compiler family.
6. **Validate every surface independently.** At minimum compile and run C,
   C++, Fortran, MPI, and OpenMP smoke tests. For GPU surfaces add a
   GPU-aware-MPI test against the exact CPE/ROCm/Cray MPICH tuple.

For the current examples, the defensible minimum remains two Cray surfaces:
the common CSE GCC surface and the CCE platform surface. An AOCC or AMD/ROCm
surface is useful as a subsequent trial when target-system inventory and site
policy prove that exact compiler/MPI tuple is supported; it should not replace
CCE automatically.
