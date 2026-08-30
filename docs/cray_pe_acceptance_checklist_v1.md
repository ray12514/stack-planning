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

## Runtime transition evidence

- [ ] The approved and candidate fact sheets are attached, with a structured
      platform-runtime-set diff for every affected lane.
- [ ] The selected CPE release notes and HPE product dependency/support matrix
      have been reviewed for Cray MPICH, libfabric/CXI, PMI/PALS, GTL, LibSci,
      compiler, and GPU-runtime changes.
- [ ] Clean-shell module chains for both the approved and candidate runtime sets
      are captured; no result depends on the ambient system default.
- [ ] The selected Cray MPICH resolves the intended libfabric/CXI provider,
      launcher/PMI components, compiler flavor, and GTL integration.
- [ ] Runtime identity was verified with module inspection and executable or
      library evidence (`readelf`, `ldd`, wrapper output, and fabric-provider
      diagnostics), not inferred from version names alone.
- [ ] Each lane has a recorded decision: revalidate, remain pinned to a
      supported older runtime set, rebuild, or hold promotion.
- [ ] The previous release was tested on the candidate system before being
      declared compatible, and any user-visible module prerequisites or
      deprecation dates are documented.

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

For the CSE GCC plus external Cray MPICH trial, completed locked MPI payload
builds may satisfy the compile, link, and runtime-closure item when their logs
identify the selected CSE GCC and Cray MPICH prefix. The workspace candidate
module must still prove the exact wrapper paths and `MPICH_*` compiler bindings.
The selector remains unpublished until the scheduler-launched multi-node item
passes on the target site.

## Operational evidence sources

- HPE CPE release notes and product dependencies for the selected release:
  <https://cpe.ext.hpe.com/docs/latest/release_notes/sles_15_6_release_notes.html>
- HPE Cray MPI runtime and OFI guidance:
  <https://cpe.ext.hpe.com/docs/latest/mpt/mpich9/intro_mpi.html>
- HPE CPE Spack integration and compiler-specific external layouts:
  <https://cpe.ext.hpe.com/docs/latest/craype/spack.html>

Site release notes and support tickets supplement these sources when local
module packaging or supported coexistence differs from the vendor baseline.
