# Initial Conversion Trials Package Version Check

Status: working input for the Initial Conversion Trials email, 2026-08-11.

## Source basis

The active stack-content defaults and trial values both pin the package recipe
source to `spack/spack-packages` release `v2026.06.0`. This check therefore
uses that tag, not the moving `develop` branch or the newest upstream release
of each project. The pins are recorded in Stack Content's
`templates/v6/defaults.yaml` and
`pilots/cse-pilot/site-values.example.yaml`.

The newest official Spack application release is
[`v1.2.2`](https://github.com/spack/spack/releases/tag/v1.2.2), published
2026-07-20. The newest official `spack-packages` release remains
[`v2026.06.0`](https://github.com/spack/spack-packages/releases/tag/v2026.06.0).
They are separate pins and both should be recorded in the trial release.

## Versions declared by the pinned recipes

Except where stated otherwise, the pair shown is the two newest numbered
versions declared by the `v2026.06.0` recipe. Every version in this table is
active: none is marked deprecated by that recipe.

| Package | Newest active recipe version(s) | Trial interpretation | Official recipe |
|---|---|---|---|
| HDF5 | `2.1.0`, `1.14.6` | The trials use the current CSE version `1.10.6` and the newest recipe version `2.1.0`. | [hdf5](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/hdf5/package.py#L42-L55) |
| NetCDF-C | `4.10.0`, `4.9.3` | The trials use the current CSE version `4.9.2` and the newest recipe version `4.10.0`. | [netcdf-c](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/netcdf_c/package.py#L30-L61) |
| NetCDF-CXX4 | `4.3.1` only | One package version, built against both approved NetCDF-C/HDF5 chains. | [netcdf-cxx4](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/netcdf_cxx4/package.py#L20-L34) |
| NetCDF-Fortran | `4.6.2`, `4.6.1` | The trials use the current CSE version `4.6.0` and the newest recipe version `4.6.2`. | [netcdf-fortran](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/netcdf_fortran/package.py#L27-L37) |
| OpenMPI | `5.0.10`; `4.1.8` is the newest recipe-labeled still-supported 4.x release | One version for non-Cray systems. The meeting recommendation is `4.1.8`, not the recipe maximum. Both are active. | [openmpi](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/openmpi/package.py#L76-L160) |
| Miniforge3 | `26.1.1-3`, then `25.3.0-3`; latest 24.x is `24.3.0-0` | One version. `26.1.1-3` is available and avoids the reported 25.x concern; validate it on each target. The recipe marks only major versions below 20 deprecated. | [miniforge3](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/miniforge3/package.py#L12-L58) |
| Python | `3.14.5`, `3.13.13`; newest 3.12 is `3.12.13`; newest 3.10 is `3.10.20` | The Initial Conversion Trials use `3.12.13` and `3.10.20`, following the PET recommendation instead of the general newest-two rule. | [python](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/python/package.py#L57-L63) |
| CMake | `3.31.12`, `4.4.2` | The trials install both versions and use `3.31.12` for package builds. These entries are newer than `v2026.06.0` and come from the official current Spack recipe through the rendered trial-local recipe extension. | [current cmake recipe](https://github.com/spack/spack-packages/blob/develop/repos/spack_repo/builtin/packages/cmake/package.py) |
| Netlib LAPACK | `3.12.1`, `3.12.0`; current CSE version is `3.10.1` | The Initial Conversion Trials build `3.10.1` and `3.12.1`. | [netlib-lapack](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/netlib_lapack/package.py#L23-L39) |
| GSL | `2.8`, `2.7.1` | The trials use the current CSE version `2.6` and the newest recipe version `2.8`. | [gsl](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/gsl/package.py#L28-L40) |
| SQLite | `3.53.1`, `3.51.2` | Two versions. | [sqlite](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/sqlite/package.py#L26-L31) |
| FFTW | `3.3.11`, `3.3.10` | Two versions, with separate Serial and MPI builds. | [fftw](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/fftw/package.py#L237-L251) |
| Boost | `1.90.0`, `1.89.0` | The trials use `1.81.0` and `1.90.0`, with separate Serial and MPI builds. | [boost](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/boost/package.py#L31-L36) |
| Gnuplot | `6.0.0`, `5.4.10` | Two versions. | [gnuplot](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/gnuplot/package.py#L32-L38) |
| Dakota | `6.24.0`, `6.23.0` | Two versions. | [dakota](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/dakota/package.py#L46-L93) |

## LAPACK choice

The package list sent to PET names LAPACK, so the Initial Conversion Trials
will build Netlib LAPACK directly. The selected versions are the current CSE
version, `3.10.1`, and the newest active version in the pinned recipe,
`3.12.1`. The email does not substitute another BLAS/LAPACK provider for this
official package selection.

## Meeting-snapshot compatibility

The snapshot's installed CSE versions do not all exist in the selected
package-recipe generation. This matters if the intended rule is literally
"current CSE version plus newest Spack recipe version."

| Snapshot version | Present in `v2026.06.0`? | Recipe status |
|---|---:|---|
| HDF5 `1.10.6` | Yes | Active |
| NetCDF-C `4.9.2` | Yes | Active |
| NetCDF-CXX4 `4.3.1` | Yes | Active; the recipe's only version |
| NetCDF-Fortran `4.6.0` | Yes | Active |
| CMake `3.25.2` | No | The pinned recipe has `3.25.3`, not `3.25.2` |
| GSL `2.6` | Yes | Active |
| SQLite `3.41.2` | No | No exact recipe entry |
| FFTW `3.3.10` | Yes | Active |
| Boost `1.81.0` | Yes | Active |
| Gnuplot `5.4.6` | No | No exact recipe entry |
| Dakota `6.17.0` | No | No exact recipe entry |

The Initial Conversion Trials will not add recipe entries solely to recreate
these four older releases. CMake uses `3.31.12` as the build version and
`4.4.2` as the additional public version. SQLite uses `3.51.2` and `3.53.1`,
Gnuplot uses `5.4.10` and `6.0.0`, and Dakota uses `6.23.0` and `6.24.0`.

Users who still require the exact older versions can continue using the prior
CSE release during the normal transition window. The working SOP keeps the
previous accepted release available for at least 90 days after its replacement
becomes current and gives at least 30 days' notice before normal removal.

## Possible additions, not approved trial content

Kokkos and RAJA are outside the approved package list. If the team later adds
them, the pinned recipes currently offer active Kokkos `5.1.1` and `5.1.0`, and
active RAJA `2025.12.2` and `2025.12.1`. See the official
[Kokkos recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/kokkos/package.py#L29-L35)
and [RAJA recipe](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/raja/package.py#L39-L54).

The current CSE trial roster excludes both packages. Adding either one requires
a separate reviewed scope decision.
