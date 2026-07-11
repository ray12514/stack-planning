# CSE Spack Learnings: Summary

**Systems:** Raider (Penguin Solutions AMD CPU) and Blueback (Cray EX)\
**Workstream:** CSE iteration work\
**Author:** Ravon\
**Updated:** 2026-07-10

This summary captures the main results from our Spack work on Raider and Blueback. It focuses on what worked, what we learned, and what still needs attention. The full document explains the build details, supporting evidence, and per-environment configuration. The lane results come from Spack 1.1 and newer, and the current reference pass is aligned with Spack 1.2.0 and `spack-packages v2026.06.0`.

## What we built

We built and verified eleven Spack environments across the two systems. In these documents, we call each complete build setup a **lane**. A lane includes the Spack environment, compiler, MPI implementation, accelerator support, and the system where it runs.

Raider has six lanes covering GCC, AOCC, NVHPC, OpenMPI, MPICH, and CUDA. CUDA-enabled Kokkos was validated with both GCC and NVHPC. Blueback has five lanes, one for each Cray Programming Environment tested so far. Two Blueback lanes include ROCm, and their GPU-aware MPI tests pass when the matching GTL library is attached. The Blueback NVHPC lane is the only lane still deferred.

Each of the eleven working lanes passed the initial HDF5 and Kokkos smoke tests, including basic module/view presentation.

## Main takeaways

1. **Spack 1.x compilers-as-dependencies worked with every compiler family we tested.** We used the same environment-generation process across six compiler families, three MPI families, CUDA, and ROCm. The process transferred well, but each vendor compiler still needed some specific configuration. Spack 1.0 matters as the starting point for this model, not as a test limitation in this work.

2. **Raider supports both site-managed and Spack-built MPI.** GCC and AOCC work with the site OpenMPI module and with OpenMPI 5 built by Spack. This gives us a practical choice: use the site MPI when local integration matters most, or build MPI with Spack when we want more control over the complete dependency stack.

3. **A general-purpose host compiler is the best starting point for most GPU builds.** GCC+CUDA is validated on Raider, and GCC+ROCm is validated on Blueback. These combinations build more of the general package graph than NVHPC or AMDClang as the host compiler. The newer Blueback ROCm 7 stack also works with a GNU-hosted ROCm build, although the AMD/ROCm compiler lane still needs its own validation. NVHPC and AMDClang still have important roles when an application needs CUDA Fortran, OpenACC, HIP single-source compilation, or OpenMP target offload. We will revisit this recommendation as the GPU test matrix grows.

4. **Each Cray lane needs one supported PrgEnv.** On Blueback, that means one compiler family per lane because the Fortran MPI modules and `cray-mpich` interfaces are compiler-specific. The version label in a Cray MPICH flavor path is best read as a supported compiler-family baseline, not an exact active-compiler requirement. HPE Cray MPI release notes list compiler minimums, such as GNU 11.2 or later for 9.0.1 and GNU 12.3 or later for 9.1.0. The supported pairing should be confirmed through the Cray PE wrappers and then reproduced in the direct-compiler Spack lane. Other Cray sites may provide vendor-supported hybrid PrgEnvs; those should be represented as their own lanes rather than arbitrary compiler mixes. Five of the six PrgEnv flavors available at the site are working. The NVHPC Cray lane remains deferred.

5. **`cray-mpich` remains the default MPI on Slingshot 11.** OpenMPI 5 can use CXI for inter-node messages while keeping intra-node messages in shared memory. There are two documented paths: OFI MTL with LINKx/LNX, or the OB1 PML with the shared-memory and OFI BTLs. The BTL path does not require LNX, but published testing found that its inter-node performance still needed work. The exact OpenMPI and HPE libfabric combination also needs to be tested on the target system. On PBS systems, OpenMPI needs PALS-aware PRRTE launch support for the Slingshot VNI. Slurm handles that connection through `srun`. `cray-mpich` already covers these requirements on the Cray system.

6. **GPU-aware `cray-mpich` needs the matching GTL library.** A driver-less Spack build on CPE does not add that library automatically. The GPU device-pointer MPI test passes when `libmpi_gtl_hsa` is supplied through `LD_PRELOAD`. The next step is to link GTL directly so the lane does not depend on a runtime preload.

## Two details that are easy to miss

- **Intel oneAPI needs a registered GCC in the environment.** The oneAPI runtime depends on GCC's C++ runtime. Without a registered GCC, concretization fails with internal errors that do not explain what is missing.
- **Spack selects the ROCm compiler with `%rocmcc`, not `%llvm-amdgpu`.** `llvm-amdgpu` is the package name used when the compiler is registered. `rocmcc` is the compiler name used on specs and compiler preferences. Using the package name in a compiler preference does not select the intended compiler. For ROCm 6.x, the recipe does not satisfy Spack's Fortran compiler virtual. ROCm 7 advertises that provider, and the newer Blueback stack has produced GNU+ROCm builds, but the AMD/ROCm compiler and Fortran lane still need direct validation.

The full document also covers the PMIx version requirement, CMake reuse, external package variants, and the difference between compiler preferences and hard compiler requirements.

## How we check a lane

`spack verify libraries` still reports warnings on healthy installs because Spack does not add `/usr` to RPATH and several trusted Cray PE libraries live under `/opt/cray/pe`. For deployment checks, we therefore use `ldd` to confirm that every dependency resolves and run `<tool> --version` to confirm that the executable starts successfully.

The longer-term improvement is a site-configurable allowlist, or an equivalent verifier input, for intentional Cray PE and system externals.

## Current status

Eleven lanes are verified across Raider and Blueback. The remaining Cray lane, `nvhpc-craympich`, will complete the six-PrgEnv matrix. Other follow-up work includes narrowing the required Cray PE module set, proposing the verifier improvement, linking GTL directly into GPU-aware lanes, validating the ROCm 7 AMD compiler path, and recording package capabilities for each lane as the broader CSE package subset grows.

The full document collects this work in Section 7 and provides the lane details in Appendix A.

## What comes next

The next round will apply the same process on systems with different operating systems, schedulers, network fabrics, and vendor compilers. That work will show which parts of the current lane design transfer unchanged and which parts need site-specific handling. The target systems are still being selected.
