# Initial Conversion Trials dependency risk audit

Date: 2026-08-19

This audit covers the CPU-only CSE Initial Conversion Trials roster against
Spack 1.2.2 and `spack-packages` tag `v2026.06.0`. It combines recipe review
with the concrete GCC lockfile produced by the local overnight test. It does
not claim that recipe-valid specs build with CCE, AOCC, or oneAPI; those
compiler paths still require real-system builds.

## Package-repository boundary

The trial package namespace is the pinned builtin repository plus the rendered
`cse_trials` overlay. The overlay intentionally adds CMake 3.31.12 and 4.4.2
and carries the reviewed CCE recipe. Therefore, those CMake versions are not a
tag mismatch. Python 3.8.20 is in the pinned builtin Python recipe but is
deprecated because it is end-of-life. Spack is configured to allow that one
intentional deprecated root.

Primary sources:

- [`spack-packages` v2026.06.0](https://github.com/spack/spack-packages/releases/tag/v2026.06.0)
- [Spack v1.2.2](https://github.com/spack/spack/releases/tag/v1.2.2)
- [Python recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/python/package.py)
- [CMake recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/cmake/package.py)

## Proven graph drift

### Ninja introduced a fourth Python

The pinned Ninja recipe has an unconditional build dependency on Python. The
GCC core lockfile resolved that edge to Python 3.14.5, in addition to the
approved public roots 3.8.20, 3.10.20, and 3.12.13. Ninja also selected its
default `+re2c` path. This is valid Spack behavior, but it is outside the trial
version policy.

The root should constrain Ninja's build interpreter to Python 3.12.13. The
lockfile verifier should reject every Python version outside the approved set
and require a single Python hash per compiler surface and version.

Source: [Ninja recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/ninja/package.py).

### Dakota can create parallel producer DAGs

Dakota defaults to `+python` and independently depends on the `blas`, `lapack`,
and `mpi` virtuals plus Boost. An unconstrained Dakota root can therefore add a
new Python, LAPACK, Boost, or MPI hash even when approved roots already exist.

For these trials Dakota should retain its Python interface but bind it to
Python 3.12.13, bind BLAS/LAPACK to netlib-lapack 3.12.1, bind Boost to the
approved Boost 1.90 MPI root, retain the selected lane MPI provider, and keep
the unused HDF5 and optional Python-interface variants disabled. Verification
must compare the dependency hashes, not only names and versions.

Source: [Dakota recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/dakota/package.py).

### Boost roots did not request the standard compiled libraries

In this recipe generation, most Boost component variants default to false.
`boost@...~mpi` or `boost@...+mpi` does not mean the usual set of compiled
Boost libraries. The package recipe supplies a standard component set for
consumers, but a direct public root must request those variants explicitly.

The common package policy should require the standard compiled set for both
public versions and their consumers. Serial and MPI roots continue to differ
only in `~mpi` versus `+mpi`. The MPI Dakota dependency must reuse the exact
Boost 1.90 MPI root hash.

Source: [Boost recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/boost/package.py).

## Expected graph growth that must be frozen

These are not automatically errors, but they must be explicit policy rather
than unnoticed recipe defaults.

- NetCDF-C defaults to Szip, Blosc, and Zstd compression plugins in this tag.
  Szip and C-Blosc add packages beyond the public roster; Zstd should reuse the
  Foundation producer. The current decision can remain, but the exact plugin
  vector must be recorded and checked. [NetCDF-C recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/netcdf_c/package.py)
- GNUplot defaults to GD, Cairo, libcerf, and readline and always depends on
  libXpm and an iconv provider. That is a substantial graphics closure. The
  current `iconv: glibc` rule prevents the observed GNU libiconv/glibc linker
  conflict, but the feature vector still needs an explicit accept-or-reduce
  decision. [GNUplot recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/gnuplot/package.py)
- Git defaults to Perl, NLS, manuals, and subtree support and depends on curl,
  OpenSSL, iconv, gettext, PCRE2, and other tools. It should be treated as a
  full Core closure, not a small executable. [Git recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/git/package.py)
- OpenMPI 4.1.8 with external UCX still normally builds or resolves hwloc,
  PMIx, and libevent. Those are expected runtime dependencies, not accidental
  provider leakage. The selected UCX, scheduler, Fortran, ROMIO, launcher,
  Lustre, and CUDA variants must match the rendered policy exactly.
  [OpenMPI recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/openmpi/package.py)

## Scientific-chain conclusions

- HDF5 is CMake-only in the pinned recipe. The existing CMake 3.31.12 edge is
  sufficient for both HDF5 1.10.6 and 2.1.0; there is no HDF5 build-system
  variant to add. [HDF5 recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/hdf5/package.py)
- The two explicit chains remain correct trial policy:
  NetCDF-C 4.9.2 with HDF5 1.10.6, and NetCDF-C 4.10.0 with HDF5 2.1.0.
- NetCDF-Fortran has no MPI variant of its own. When its NetCDF-C dependency is
  MPI-enabled, the recipe adds an MPI dependency. The lane-wide MPI
  requirement and hash verifier must force that edge to the same provider.
  [NetCDF-Fortran recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/netcdf_fortran/package.py)
- NetCDF-CXX4 has no MPI variant. The two builds of version 4.3.1 are
  distinguished by their explicitly constrained NetCDF-C/HDF5 chains. The
  existing module projection that includes dependency versions is required.
  [NetCDF-CXX4 recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/netcdf_cxx4/package.py)
- `~parallel-netcdf` is intentionally explicit in MPI NetCDF-C. It keeps
  PnetCDF out of this trial while retaining parallel HDF5 through `+mpi`.
- FFTW's `~mpi`/`+mpi` split is sufficient when the lane MPI provider is
  mandatory and lockfile-verified. [FFTW recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/fftw/package.py)

## Hash and provider rules

Hashes are expected to match only where the complete concrete spec is intended
to match.

- Repeated Foundation, CMake, approved Python, and selected LAPACK producers
  must have one hash within each compiler surface.
- GCC, CCE, AOCC, and oneAPI builds are different compiler surfaces and are
  expected to have different hashes.
- Serial and MPI variants are intentionally different hashes.
- Every MPI payload root must reach exactly one selected MPI provider hash.
- External Cray MPICH must remain a leaf external selected from the exact
  compiler-flavor scope. Its platform runtime is validated from the complete
  module/prefix evidence; it should not be remodeled as Spack-built libfabric
  or PMI dependencies.
- Built OpenMPI must use the rendered full provider constraint. UCX and a
  verified scheduler are explicit externals; PMIx, hwloc, and libevent are
  expected recipe dependencies unless policy deliberately changes them.
- Every external node must be on an allow-list with exact spec, prefix, and
  module evidence. Ambient discovery is not acceptance evidence.

## Required lockfile gates

The generated verifier should fail on:

1. an unexpected root, root version, or root variant;
2. any Python version outside 3.8.20, 3.10.20, and 3.12.13;
3. more than one hash for an intended repeated producer within one compiler
   surface;
4. a Dakota dependency that does not reuse the approved Python, LAPACK, Boost,
   CMake, and MPI producers;
5. a NetCDF/HDF5 chain outside the two approved pairs;
6. more than one MPI implementation or provider hash in an MPI root closure;
7. any MPI provider reachable from a Serial root;
8. a built node with the wrong CPU target, except reviewed binary-package
   exceptions such as Miniforge;
9. an unexpected external or an expected external with the wrong spec/prefix;
10. public module selection that exposes implicit dependencies or collapses
    two distinct roots to one module name.

## What recipe inspection cannot settle

Package recipes and generic Linux concretization can expose dependency and
provider mistakes before site builds. They cannot prove that CCE, AOCC 4.1, or
oneAPI 2024.2.1 accepts every package's flags and language probes. They also
cannot prove Cray wrapper/module ABI compatibility, scheduler launch behavior,
shared-filesystem locking, or runtime visibility.

The remaining real-system sequence is therefore:

1. fresh-concretize all eight environments and run the lockfile verifier;
2. build Foundation/Core/Common on each compiler surface;
3. build and exercise Serial C, C++, and Fortran roots;
4. build each MPI provider and compile C, C++, `mpif.h`, `use mpi`, and
   `use mpi_f08` probes;
5. build the MPI payload and run two-rank HDF5, NetCDF, FFTW, Boost, and Dakota
   probes through the selected launcher;
6. regenerate views/modules and verify package visibility after installation.

If a vendor compiler fails on an individual dependency, add one reviewed
package-level compiler exception. Do not preemptively mix GCC dependencies
into every CCE, AOCC, or oneAPI DAG.
