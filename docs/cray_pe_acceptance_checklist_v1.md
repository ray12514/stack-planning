# Cray PE Acceptance Checklist

Apply this checklist after the common procedure in `runbook.md`. It records
Cray PE-specific proof points; it does not replace the common runbook.

## Profile facts

- [ ] The selected CPE generation is explicit and its compiler, Cray MPICH,
      GPU toolkit, and platform-runtime facts come from the same generation.
- [ ] Every compiler surface carries the correct `PrgEnv-*` and compiler module
      chain.
- [ ] Cray MPICH flavors point at the compiler-family prefix reported by the
      platform, including the correct Fortran module interface.
- [ ] Slingshot/libfabric/CXI facts and scheduler-launch prerequisites are
      recorded.
- [ ] ROCm or CUDA toolkit roots and accelerator architectures match the target
      node type.

## Render and lockfiles

- [ ] Only the selected platform generation is rendered into a lane; other
      observed generations remain catalog facts.
- [ ] `cray-mpich` externals use plain provider specs; compiler binding is in
      the native Spack toolchain scope.
- [ ] Cray GTL, PMI, and PALS are not emitted as Spack externals without an
      explicit package-repository policy.
- [ ] Serial lockfiles contain no MPI implementation.
- [ ] MPI and GPU lockfiles use the selected Cray MPICH and toolkit externals
      rather than fetching replacements.

## Runtime

- [ ] C, C++, `mpif.h`, `use mpi`, and `use mpi_f08` compile/link checks pass
      for every supported compiler family.
- [ ] Scheduler-launched multi-node MPI passes over the site fabric.
- [ ] A GPU-aware MPI test passes with the matching GTL integration.
- [ ] `ldd` resolves trusted Cray PE libraries; verifier warnings for intentional
      externals are recorded rather than silently ignored.
- [ ] Version-sensitive package module chains are tested: compatible chains
      load cleanly, and incompatible dependency mixes fail or are prevented.
