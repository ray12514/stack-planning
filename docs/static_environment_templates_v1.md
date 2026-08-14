# Static catalog environment templates (v1)

| Document control | |
|---|---|
| Date | 2026-07-25 |
| Status | Working templates for the pilot build, to be filled in per system |
| Scope | Hand-written Spack environments that consume a rendered static catalog. Not the full render. |
| Companion | `cray_mpich_gcc_compatibility_v1.md` for the compiler and MPI pairing rule |

Each template is a `spack.yaml` for one surface on one system. Two surfaces per
system:

- **The CSE GCC surface.** One GCC version, built by the stack, the same on
  every system. This is the consistency anchor: a user meets the same compiler
  everywhere. The MPI underneath stays each machine's own, so the surface is
  consistent in compiler and workflow, not in MPI implementation.
- **The platform baseline surface.** The compiler the machine blesses, CCE on
  the Crays and AOCC on the AMD systems, with the MPI that pairs with it.

Both surfaces build the same package roster, so a difference in results is a
difference in toolchain and nothing else.

What gets built therefore differs per system. On the Crays the CSE surface
builds only the compiler, because cray-mpich is consumed. On the generic Linux
systems it builds the compiler and the MPI.

## Reading the catalog first

Every `<placeholder>` below comes from the catalog rendered on that machine.
Run these before writing an environment:

```bash
# Every scope the catalog carries, with its exact relative path
grep -A2 'scopes:' <catalog>/manifest.yaml

# The physical MPI flavors, their compiler baselines, and compatible observed compilers
ls <catalog>/scopes/mpi/*/*/

# The compilers the machine reports
ls <catalog>/scopes/compilers/*/
```

On a Cray system, also confirm which GNU flavors the platform MPI actually
ships, since HPE does not publish that roster:

```bash
ls /opt/cray/pe/mpich/<version>/ofi/gnu
```

## Two rules that decide the shape of every file below

1. **`include::` with two colons.** It overrides every ambient configuration
   scope, so the environment resolves from the catalog plus Spack's own
   defaults and nothing else. A single colon lets a stray `~/.spack` join the
   concretization and the same inputs stop producing the same build.
2. **Including a compiler scope means taking the platform's compiler.** A
   compiler scope declares that compiler `buildable: false` with an external
   prefix. To build our own instead, leave that one scope out and name the
   compiler in the specs.

## Blueback, surface 1: stack-built GCC with cray-mpich

This is the consistency surface. The same GCC version is built on every system
in the pilot, so a user meets one compiler everywhere, while the MPI stays each
machine's own. On the Crays that means our GCC on top of the platform's
cray-mpich.

The compiler scope is left out, which is what makes GCC buildable. The MPI
scope is included, so cray-mpich is consumed as an external at the flavor
prefix.

```yaml
spack:
  include::
  - <catalog>/scopes/common
  - <catalog>/scopes/mpi/cray-mpich/<mpich-version>/gcc-<flavor-gcc-version>
  # compilers scope deliberately omitted: GCC is built here

  specs:
  - group: compiler
    specs:
    - gcc@<cse-gcc-version>

  - group: apps
    needs: [compiler]
    specs:
    - hdf5@<version> +mpi +fortran %gcc@<cse-gcc-version>
    - netcdf-c@<version> +mpi %gcc@<cse-gcc-version>
    - netcdf-fortran@<version> %gcc@<cse-gcc-version>
    - fftw@<version> +mpi %gcc@<cse-gcc-version>
    - openblas@<version> %gcc@<cse-gcc-version>
    - netlib-scalapack@<version> %gcc@<cse-gcc-version>
    - boost@<version> +mpi %gcc@<cse-gcc-version>

  concretizer:
    unify: false
    reuse: true
```

`<cse-gcc-version>` is the one CSE version, the same on every system.
`<flavor-gcc-version>` is the minimum compiler baseline encoded by that
machine's cray-mpich GNU flavor, and it selects which physical MPI scope to
include. It is not replaced by the newest installed GCC. The CSE version must
be at or above the flavor baseline, never below.

This combination is verified. A stack-built GCC 14.3.0 against a `gnu/13.3`
cray-mpich flavor concretizes with cray-mpich bound as an external at the
flavor prefix and its module, and the whole payload built against the stack
compiler.

If the machine's only GNU flavor turns out to be above the chosen CSE version,
this surface cannot be built as written. That is the pairing constraint showing
up for real, and the options are to raise the CSE version or to treat that
system's GCC surface as platform-provided instead.

### Variant: platform GCC instead

If the pilot decides a system should consume its own GCC rather than the CSE
one, include the compiler scope and drop the groups:

```yaml
spack:
  include::
  - <catalog>/scopes/common
  - <catalog>/scopes/compilers/gcc/<gcc-version>
  - <catalog>/scopes/mpi/cray-mpich/<mpich-version>/gcc-<flavor-gcc-version>

  specs:
  - hdf5@<version> +mpi +fortran
  # ... same roster, no %compiler needed
```

The selected platform GCC must be from the same family and at or above the MPI
flavor baseline. The compiler scope keeps the exact installed version; the MPI
scope keeps the physical flavor baseline.

## Blueback, surface 2: CCE with cray-mpich

Same roster, the machine's own compiler. This is the baseline surface.

```yaml
spack:
  include::
  - <catalog>/scopes/common
  - <catalog>/scopes/compilers/cce/<cce-version>
  - <catalog>/scopes/mpi/cray-mpich/<mpich-version>/cce-<flavor-cce-version>

  specs:
  - hdf5@<version> +mpi +fortran
  - netcdf-c@<version> +mpi
  - netcdf-fortran@<version>
  - fftw@<version> +mpi
  - openblas@<version>
  - netlib-scalapack@<version>
  - boost@<version> +mpi

  concretizer:
    unify: false
    reuse: true
```

`<flavor-cce-version>` is the CCE minimum baseline encoded by the Cray MPICH
product path. The selected `<cce-version>` must be from the same family and at
or above that baseline.

## Raider, surface 1: stack-built GCC with stack-built OpenMPI

Neither the compiler nor the MPI comes from the platform, so neither scope is
included. The concretization groups order the builds: compiler first, then MPI
against it, then the payload against both.

```yaml
spack:
  include::
  - <catalog>/scopes/common
  # compilers and mpi scopes deliberately omitted: both are built here

  packages:
    mpi:
      require: [openmpi]

  specs:
  - group: compiler
    specs:
    - gcc@<gcc-version>

  - group: mpi
    needs: [compiler]
    specs:
    - openmpi@<newest-supported> %gcc@<gcc-version>

  - group: apps
    needs: [mpi]
    specs:
    - hdf5@<version> +mpi +fortran %gcc@<gcc-version>
    - netcdf-c@<version> +mpi %gcc@<gcc-version>
    - netcdf-fortran@<version> %gcc@<gcc-version>
    - fftw@<version> +mpi %gcc@<gcc-version>
    - openblas@<version> %gcc@<gcc-version>
    - netlib-scalapack@<version> %gcc@<gcc-version>
    - boost@<version> +mpi %gcc@<gcc-version>

  concretizer:
    unify: false
    reuse: true
```

`group` and `needs` require Spack 1.2 or newer. On Spack 1.0 a stack-built
compiler had to be installed and registered as an external first; 1.2 removed
that requirement, which is one reason the pilot standardizes on it.

`packages: mpi: require: [openmpi]` pins the MPI virtual so nothing else can
satisfy it. The common scope stays included because OpenSSL, curl, and the
fabric userspace still come from the system.

## Raider, surface 2: AOCC with its matching OpenMPI

The baseline surface. AOCC is installed on the machine, so it is consumed
rather than built, and the OpenMPI that pairs with it comes from the catalog.

```yaml
spack:
  include::
  - <catalog>/scopes/common
  - <catalog>/scopes/compilers/aocc/<aocc-version>
  - <catalog>/scopes/mpi/openmpi/<openmpi-version>/aocc-<aocc-version>

  specs:
  - hdf5@<version> +mpi +fortran
  - netcdf-c@<version> +mpi
  - netcdf-fortran@<version>
  - fftw@<version> +mpi
  - openblas@<version>
  - netlib-scalapack@<version>
  - boost@<version> +mpi

  concretizer:
    unify: false
    reuse: true
```

If the catalog reports no OpenMPI built against the AOCC on the machine, that
scope path will not exist. In that case the surface either builds its own
OpenMPI against AOCC, following the pattern of Raider surface 1 with `aocc`
substituted for `gcc`, or the AOCC baseline waits. Which of those applies is a
fact from the machine, not a decision to make in advance.

## Pairing rule, restated

A compiler above the MPI's build baseline is safe; a compiler below it is not.
The MPI's runtime libraries come from the compiler it was built with, and those
libraries are forward compatible only, so an older compiler than the MPI
expects can be missing symbols the MPI references. On Cray systems the flavor
directory states the baseline. Do not go below it.

The Fortran module files are a separate question and, for GCC 8 through 14,
not a constraint: that range shares one module format. GCC 15 changes it. See
the compatibility note for the evidence.

## What to record per system

Capture these next to the build so a rebuild can be reproduced:

- the catalog release tag and the scopes actually included
- the compiler and MPI versions resolved, from `spack.lock`
- for a stack-built compiler, the exact version built
- `spack spec` output for one representative package per surface
