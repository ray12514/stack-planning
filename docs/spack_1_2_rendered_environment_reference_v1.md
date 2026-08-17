# Spack 1.2 Rendered Environment Reference v1

## Status

Design reference for the full Stack Composer render. This document records the
target Spack 1.2 file seam and the intended Foundation, Core, Common, Serial,
MPI, and GPU behavior. It is the durable replacement for the temporary
rendered examples under `/tmp/cse-spack-render-examples`.

This is not the static-catalog manual-consumption path. The static catalog
publishes reusable configuration scopes. The full render additionally owns
environment manifests, views, module-generation policy, front-door modulefiles,
lane selectors, and the build workspace.

## Spack 1.2 ownership seam

Use Spack-native configuration files wherever Spack provides one.

| File | Owns |
|---|---|
| `spack.yaml` | environment-only data: `include::`, `definitions`, spec groups, `needs`, root specs, and named views |
| `packages.yaml` | externals, providers, buildability, requirements, and target policy |
| `toolchains.yaml` | reusable compiler/MPI bindings selected with `%toolchain` |
| `modules.yaml` | module generation, `use_view`, projections, exclusions, autoload/conflict policy, and module roots |
| `config.yaml` | install tree, permissions, build-stage, cache, and general Spack configuration |
| `concretizer.yaml` | reuse and concretizer policy |
| `repos.yaml` | package-repository generation pinning |
| `mirrors.yaml` | mirrors and build caches |

`view` is an environment-manifest field in Spack 1.2. It stays in
`spack.yaml`; there is no standalone native `view.yaml` configuration scope.

`modules.yaml` is a native configuration file. Full renders should stop
embedding the complete module policy in every `spack.yaml`. Each environment
includes its lane-local configuration directory, which contains the matching
`modules.yaml`.

## Package-class model

The names describe build and exposure behavior, not extra user-facing gates.

| Class | Build ownership | User exposure | Version policy |
|---|---|---|---|
| Foundation | part of the per-compiler Core environment | ambient compiler view; no package modules | one pinned version per release |
| Core | part of the per-compiler Core environment | package modules visible after `module load cse/<Compiler>` | roster policy; multiple public tool versions require explicit pins |
| Common | separate per-compiler environment, built once and reused by payload lanes | package modules visible after `module load cse/<Compiler>` | roster policy; currently newest two where multiple versions are useful |
| Serial | serial payload environment | modules visible after `module load Serial` | roster policy |
| MPI | MPI payload environment | modules visible after `module load MPI` | roster policy |
| GPU | GPU payload environment and MPI superset when the toolchain pairing is compatible | modules visible after `module load GPU` | roster policy |

Foundation and Core are represented as separate Spack 1.2 groups inside one
Core environment. There is no public Foundation lane. Common has the same
module-visible behavior as Core, but it remains a sibling per-compiler
environment because its payload libraries have a different rebuild and reuse
boundary. Common is not a public lane and is not part of Foundation's ambient
path surface.

The compiler front door performs three actions:

1. loads the selected compiler and any required provider modules;
2. prepends the Foundation view to the relevant path variables;
3. prepends both the Core and Common module roots to `MODULEPATH`.

Loading `Serial`, `MPI`, or `GPU` then prepends the selected payload module
root. A user does not load a second Common lane.

## Rendered tree

The same tree shape applies to Cray and generic Linux systems. Provider scopes
and producer groups differ; the renderer structure does not.

```text
<workspace>/
  configs/
    common/
      config.yaml
      concretizer.yaml
      packages.yaml
      repos.yaml
    compilers/<compiler>/<version>/
      packages.yaml
    mpi/<provider>/<version>/<compiler-version>/
      packages.yaml
      toolchains.yaml
    gpu/<provider>/<version>/
      packages.yaml
    environments/<compiler>/
      core/modules.yaml
      common/modules.yaml
      serial/modules.yaml
      mpi-<provider>/modules.yaml
      gpu-<provider>-<arch>/modules.yaml
  environments/<compiler>/
    core/spack.yaml
    common/spack.yaml
    serial/spack.yaml
    mpi-<provider>/spack.yaml
    gpu-<provider>-<arch>/spack.yaml
  modulefiles/
    cse/<Compiler>
    <compiler>/lanes/Serial
    <compiler>/lanes/MPI
    <compiler>/lanes/GPU
```

Each `spack.yaml` includes the corresponding
`configs/environments/<compiler>/<environment>` directory so Spack reads that
environment's native `modules.yaml`.

## Native `modules.yaml`

Core uses a module-only view. Foundation is absent from the module include
list and is instead selected by the ambient Foundation view in `spack.yaml`.

```yaml
modules:
  prefix_inspections:
    bin: [PATH]
    lib: [LD_LIBRARY_PATH]
    lib64: [LD_LIBRARY_PATH]
    include: [CPATH]
    lib/pkgconfig: [PKG_CONFIG_PATH]
    lib64/pkgconfig: [PKG_CONFIG_PATH]
    share/pkgconfig: [PKG_CONFIG_PATH]
    share/man: [MANPATH]
    '.': [CMAKE_PREFIX_PATH]

  default:
    enable: [tcl]
    use_view: cse_modules
    arch_folder: false
    roots:
      tcl: /shared/cse/modules/<release>/<system>/<stack>/<compiler>/core
    tcl:
      hash_length: 0
      exclude_implicits: true
      include:
      - cmake@3.31.12
      - cmake@4.4.2
      - ninja
      - pkgconf
      - git
      - python@3.8.20
      - python@3.10.20
      - python@3.12.13
      - miniforge3@26.1.1-3
      - gsl@2.6
      - gsl@2.8
      - sqlite@3.51.2
      - sqlite@3.53.1
      projections:
        all: '{name}/{version}'
      all:
        autoload: none
```

Common, Serial, MPI, and GPU receive their own `modules.yaml` with the same
mechanism and their own root and package include list. Module paths are
calculated from the named `cse_modules` view because `use_view` points to that
view. This keeps public module paths on stable projections instead of Spack's
hashed install prefixes.

Every selected package must have a unique view projection. Multiple public
versions use `{name}/{version}` or a dependency-qualified projection such as
`{name}/{version}-python{^python.version}`. The hash projection is a fallback,
not the normal public name.

## Core environment: Foundation plus Core

The following is the common Spack 1.2 shape. Provider-specific include paths
are shown later.

```yaml
spack:
  include::
  - ../../../configs/common
  - ../../../configs/compilers/gcc/13.3.1
  - ../../../configs/environments/gcc/core

  definitions:
  - foundation:
    - zlib@1.3.1
    - xz@5.4.6
    - zstd@1.5.6
  - core:
    - cmake@3.31.12
    - cmake@4.4.2
    - ninja
    - pkgconf
    - git
    - python@3.8.20
    - python@3.10.20
    - python@3.12.13
    - miniforge3@26.1.1-3
    - gsl@2.6
    - gsl@2.8
    - sqlite@3.51.2
    - sqlite@3.53.1

  specs:
  - group: foundation
    specs:
    - $foundation
  - group: core
    needs: [foundation]
    specs:
    - $core

  view:
    foundation:
      root: /shared/cse/views/<release>/<system>/<stack>/gcc/foundation
      group: foundation
      link: roots
      link_type: symlink
    cse_modules:
      root: /shared/cse/views/<release>/<system>/<stack>/gcc/core-modules
      group: core
      link: roots
      link_type: symlink
      projections:
        all: '{name}/{version}'
```

The Core group `needs` Foundation so Spack 1.2 concretizes the lower group
first and can reuse it. Foundation's view is deliberately flat: loading the
compiler front door can prepend one `bin`, `lib`, `include`, and `share` tree.
Its one-version-per-release rule prevents ambiguity and collisions. Foundation
still has no generated package modules. The `cse_modules` view is deliberately
projected by package and version because generated Core modules need unique,
stable package roots.

For a stack-built compiler, repeat one exact compiler producer group in every
environment on that compiler surface. The producer is built with an explicit
verified seed compiler from the platform catalog; it is not discovered from
ambient state:

```yaml
spack:
  include::
  - /catalog/scopes/compilers/gcc/11.5.0
  specs:
  - group: compiler
    specs:
    - gcc@13.3.1 languages='c,c++,fortran' %gcc@11.5.0
  - group: foundation
    needs: [compiler]
    specs:
    - matrix:
      - [$foundation]
      - ['%gcc@13.3.1']
  - group: core
    needs: [compiler, foundation]
    specs:
    - matrix:
      - [$core]
      - ['%gcc@13.3.1']
  view:
    compiler:
      root: /shared/cse/views/gcc/compiler
      link: roots
      group: compiler
```

The groups are environment-local. Separate Core, Common, Serial, MPI, and GPU
environments repeat the compiler, Foundation, build-tool, and MPI producer
groups they need. Exact producer specs generate exact hashes across independent
locks; the shared store and build cache reuse those concrete prefixes. Install
Core first on the initial pass, but all environments may be concretized before
the compiler is installed.

## Compiler selection without a toolchain

A toolchain represents a compiler/MPI pairing. A compiler by itself remains a
normal compiler constraint and does not get a `toolchains.yaml` alias.
Definitions plus a matrix apply the compiler constraint once to a whole
package list; package managers do not repeat it in every root spec.

```yaml
spack:
  definitions:
  - common:
    - openblas@0.3.33
    - openblas@0.3.32
    - gnuplot@6.0.0
    - gnuplot@5.4.10

  specs:
  - matrix:
    - [$common]
    - ['%gcc@13.3.1']
```

This is an `N x 1` expansion: every package in `common` receives the same
toolchain. Use a matrix only for a homogeneous package list that receives one
or more common compiler/MPI/GPU dimensions. Do not wrap a single producer spec
or a package with unique constraints in a ceremonial one-item matrix; write
that spec directly. Packages with explicit HDF5/NetCDF compatibility pairings
may stay explicit inside the definition while the matrix applies only the
shared toolchain selector.

## Cray MPI/GPU environment

Cray consumes the selected compiler, Cray MPICH flavor, and GPU runtime as
externals from profile-derived configuration scopes. It does not create
compiler or MPI producer groups.

The common profile-derived scope inventories the selected platform `libfabric`
external. Each Cray MPICH scope inventories the inspected, non-buildable
`cray-pmi` external beside the compiler-specific Cray MPICH external. These
records validate the active CPE runtime, but the selected Cray MPICH external
is represented to Spack as a platform leaf. Its external spec does not embed
compiler, CPU-target, `libfabric`, or `cray-pmi` dependency constraints; the
prefix and recorded module chain provide the platform runtime closure. A Cray
MPI environment is incomplete if either runtime record is absent, and it must
not let Spack replace the active CPE runtime with a source-built package.

Portable CPU-target policy applies to source-built roots. An `mpi:require`
entry for external Cray MPICH selects only its provider and version. It must
not require that the platform external claim the source-build target. A
build-sourced MPI provider such as OpenMPI does carry that target.

```yaml
# configs/mpi/cray-mpich/8.1.29/gcc-13.3.0/toolchains.yaml
toolchains:
  gcc1330_craympich8129:
  - spec: '%c=gcc@13.3.0'
    when: '%c'
  - spec: '%cxx=gcc@13.3.0'
    when: '%cxx'
  - spec: '%fortran=gcc@13.3.0'
    when: '%fortran'
  - spec: '%mpi=cray-mpich@8.1.29+wrappers'
    when: '%mpi'
```

```yaml
# environments/gcc/gpu-craympich-gfx942/spack.yaml
spack:
  include::
  - ../../../configs/common
  - ../../../configs/compilers/gcc/13.3.0
  - ../../../configs/mpi/cray-mpich/8.1.29/gcc-13.3.0
  - ../../../configs/gpu/rocm/6.0.0
  - ../../../configs/environments/gcc/gpu-craympich-gfx942

  definitions:
  - mpi_payload:
    - hdf5@2.1.0 +mpi +fortran +cxx +hl
    - hdf5@1.14.6 +mpi +fortran +cxx +hl
    - netcdf-c@4.10.0 +mpi +parallel-netcdf ^hdf5@2.1.0+mpi
    - netcdf-c@4.9.3 +mpi +parallel-netcdf ^hdf5@1.14.6+mpi
    - netcdf-fortran@4.6.2 ^netcdf-c@4.10.0+mpi ^hdf5@2.1.0+mpi
    - netcdf-fortran@4.6.1 ^netcdf-c@4.9.3+mpi ^hdf5@1.14.6+mpi
    - netcdf-cxx4@4.3.1 ^netcdf-c@4.10.0+mpi ^hdf5@2.1.0+mpi
    - fftw@3.3.11 +mpi
    - fftw@3.3.10 +mpi
    - boost@1.90.0 +mpi
    - boost@1.89.0 +mpi
    - netlib-scalapack@2.2.3
    - netlib-scalapack@2.2.2
    - dakota@6.24.0 +mpi
    - dakota@6.23.0 +mpi
  - gpu_payload:
    - tau@2.35.1 +mpi +rocm
    - kokkos@5.1.1 +rocm amdgpu_target=gfx942
    - kokkos@5.1.0 +rocm amdgpu_target=gfx942

  specs:
  - matrix:
    - [$mpi_payload]
    - ['%gcc1330_craympich8129']
  - matrix:
    - [$gpu_payload]
    - ['%gcc1330_craympich8129']

  view:
    cse_modules:
      root: /shared/cse/views/<release>/<system>/<stack>/gcc/gpu-craympich-gfx942-modules
      link: roots
      link_type: symlink
      projections:
        all: '{name}/{version}'
```

The GPU environment intentionally includes the compatible MPI payload. It is
an MPI superset when compiler, MPI, fabric, and GPU-runtime policy select one
compatible toolchain. If those facts differ, Stack Composer renders distinct
GPU and MPI surfaces instead of combining them.

## Generic Linux stack-built GCC/OpenMPI environments

On a generic Linux system where both GCC and OpenMPI are stack-built, every GCC
environment repeats the exact GCC producer group and binds downstream roots to
it. MPI environments also contain an OpenMPI producer group. Spack 1.2 groups
express that ordering inside each independent environment.

```yaml
# configs/mpi/openmpi/5.0.8/gcc-13.3.1/toolchains.yaml
toolchains:
  gcc1331_openmpi508:
  - spec: '%c=gcc@13.3.1'
    when: '%c'
  - spec: '%cxx=gcc@13.3.1'
    when: '%cxx'
  - spec: '%fortran=gcc@13.3.1'
    when: '%fortran'
  - spec: '%mpi=openmpi@5.0.8'
    when: '%mpi'
```

```yaml
# configs/mpi/openmpi/5.0.8/gcc-13.3.1/packages.yaml
packages:
  mpi:
    require:
    - openmpi@5.0.8
```

```yaml
# environments/gcc/gpu-openmpi-sm_80/spack.yaml
spack:
  include::
  - ../../../configs/common
  - ../../../configs/compilers/gcc/13.3.1
  - ../../../configs/mpi/openmpi/5.0.8/gcc-13.3.1
  - ../../../configs/gpu/cuda/12.4.1
  - ../../../configs/environments/gcc/gpu-openmpi-sm_80

  definitions:
  - mpi_payload:
    - hdf5@2.1.0 +mpi +fortran +cxx +hl
    - hdf5@1.14.6 +mpi +fortran +cxx +hl
    - netcdf-c@4.10.0 +mpi +parallel-netcdf ^hdf5@2.1.0+mpi
    - netcdf-c@4.9.3 +mpi +parallel-netcdf ^hdf5@1.14.6+mpi
    - netcdf-fortran@4.6.2 ^netcdf-c@4.10.0+mpi ^hdf5@2.1.0+mpi
    - netcdf-fortran@4.6.1 ^netcdf-c@4.9.3+mpi ^hdf5@1.14.6+mpi
    - fftw@3.3.11 +mpi
    - fftw@3.3.10 +mpi
    - boost@1.90.0 +mpi
    - boost@1.89.0 +mpi
    - netlib-scalapack@2.2.3
    - netlib-scalapack@2.2.2
  - gpu_payload:
    - tau@2.35.1 +mpi +cuda
    - kokkos@5.1.1 +cuda cuda_arch=80
    - kokkos@5.1.0 +cuda cuda_arch=80

  specs:
  - group: mpi
    specs:
    - openmpi@5.0.8 %gcc1331
  - group: payload
    needs: [mpi]
    specs:
    - matrix:
      - [$mpi_payload]
      - ['%gcc1331_openmpi508']
    - matrix:
      - [$gpu_payload]
      - ['%gcc1331_openmpi508']

  view:
    cse_modules:
      root: /shared/cse/views/<release>/<system>/<stack>/gcc/gpu-openmpi-sm_80-modules
      group: payload
      link: roots
      link_type: symlink
      projections:
        all: '{name}/{version}'
```

If GCC and OpenMPI are trusted site externals, include their catalog scopes and
drop the compiler and `mpi` producer groups. The payload matrix
and native toolchain remain the same.

## What changes from the current renderer

| Current shape | Spack 1.2 target |
|---|---|
| module-generation policy embedded in `spack.yaml` | native environment-local `modules.yaml` |
| repeated compiler/MPI selectors on roots | definitions plus matrices selecting `%toolchain` once |
| producer ordering inferred outside the manifest | repeated compiler/MPI producer groups plus native spec groups with `needs` for Foundation, Core/build tools, MPI, and payloads |
| provider requirements mixed into environment data | native `packages.yaml` scope |
| one view serving ambient paths and generated modules | flat Foundation view plus projected module-only views |

Views remain in `spack.yaml` because they are environment-owned in Spack 1.2.
Definitions, groups, `needs`, and root specs also remain there. Moving those
fields into invented project YAML files would make the design less native, not
more native.

## Serial and MPI manifests

Serial is the same pattern with a direct compiler constraint and no MPI scope.
MPI is the GPU pattern without the GPU scope or GPU roots and uses the selected
compiler/MPI toolchain. The package definitions are shared policy data rendered
into each independent environment; the manifests remain separate so failures,
rebuilds, views, and module trees stay isolated by lane.

Keep the rendered environments separate:

1. `core/spack.yaml` owns the repeated compiler producer, Foundation, and Core groups;
2. `common/spack.yaml` owns repeated producers plus compiler-common libraries;
3. `serial/spack.yaml` owns repeated producers plus serial payloads;
4. `mpi-<provider>/spack.yaml` owns repeated producers plus MPI payloads;
5. `gpu-<provider>-<arch>/spack.yaml` owns repeated producers plus the compatible MPI-plus-GPU
   payload.

The normal first-pass install order is Core, Common, Serial, MPI, then GPU.
Concretize and verify every lock first. Enable concurrent environment installs
only after verifying that the actual shared store honors Spack's file locks.
Independent manifests preserve failure, rebuild, lockfile, view, and module
publication boundaries. Exact specs, shared configuration policy, one Spack
install store, and build-cache reuse prevent identical dependencies from being
rebuilt. A package that depends on Foundation or Common software still records
that relationship in its concrete DAG; module visibility is not a substitute
for a build dependency.

Spec-group `needs` applies inside one environment. It does not create an edge
between separate `spack.yaml` files, and it is not transitive between groups.
A group that uses a stack-built MPI provider lists that producer group
directly, even when another needed group already depends on it. A stack-built
compiler is a repeated producer group in every environment on that surface.
Stack Composer's handoff or the external
build driver owns the environment build order. Spack 1.2's jobserver supplies
package-level concurrency within an install invocation; scheduler-level work
across multiple nodes remains an external orchestration concern.

The Initial Conversion Trials confirm the reuse invariant that the full
renderer must preserve. Every independent environment repeats the complete,
exact producer and Foundation/build-tool root specs it consumes. With the same
Spack version, package repository, included policy, target, variants, and
provider constraints, those roots concretize to the same hashes. All locks are
created and checked before installation. The environments then use one shared
install tree and database with `config:locks:true`: the first process reaching
an absent concrete prefix builds it, while another process requesting that
same hash waits on the prefix lock and reuses the completed installation.
Cross-environment ordering is never inferred from `needs`; sequential order or
multi-process scheduling remains the build driver's responsibility, and
concurrent installs are enabled only after the shared filesystem passes the
prefix-lock test.

The full renderer should therefore produce:

```text
Core:      compiler producer when needed -> Foundation -> Core
Common:    compiler producer when needed -> Foundation/build tools -> Common payload
Serial:    compiler producer when needed -> Foundation/build tools -> Serial payload
MPI:       compiler producer when needed -> Foundation/build tools -> MPI producer when needed -> MPI payload
GPU:       compiler producer when needed -> Foundation/build tools -> MPI producer when needed -> MPI + GPU payload
```

## Toolchain boundary

Spack 1.2 toolchains apply to the root where `%toolchain` appears and constrain
direct language/MPI dependencies. They do not recursively impose arbitrary
constraints on every transitive dependency. The renderer therefore uses all
three controls together:

1. a toolchain matrix to avoid repeating `%compiler`/`%mpi` on every root;
2. `packages.yaml` provider requirements so the MPI virtual cannot drift;
3. explicit dependency pairings in roots whose version compatibility matters,
   such as the two HDF5/NetCDF families.

This is compiler/MPI binding, not a new CSE spec language.

## Required Stack Composer changes

The current rendered examples predate this Spack 1.2 target and embed module
configuration in `spack.yaml`. The implementation should be changed as one
coherent render update:

1. emit one native `modules.yaml` per rendered environment;
2. add that environment's configuration directory to `include::`;
3. keep named views in `spack.yaml` and point `modules.yaml:use_view` at the
   module-only view;
4. render Foundation and Core as Spack 1.2 groups in one Core environment;
5. repeat an exact compiler producer group when the compiler is stack-built,
   and an MPI producer group with `needs` when MPI is stack-built;
6. apply compiler-only or compiler-plus-MPI toolchains to package lists through
   definitions and matrices;
7. expose Foundation through the compiler-init view, Core and Common through
   the compiler-init `MODULEPATH`, and payload packages through lane modules;
8. keep GPU as an MPI superset only when the selected compatibility tuple is
   valid.

No compatibility path is needed for the older pre-v1 inline-module manifest.
The renderer, fixtures, golden outputs, runbooks, and Docker module smoke test
should move to this shape together.

## Acceptance checks

For both Cray and generic Linux fixtures:

- every YAML file parses;
- `spack.yaml` contains no inline `modules:` block;
- every environment includes exactly one environment-local `modules.yaml`;
- `use_view` names a view defined in that environment's `spack.yaml`;
- Foundation packages appear in the Foundation view and never in module
  include lists;
- Core and Common modules become visible after the compiler front door;
- Serial, MPI, and GPU payload modules remain hidden until the matching lane is
  loaded;
- GPU exposes the compatible MPI payload when policy combines them;
- repeated stack-built compiler roots resolve to one concrete hash across Core,
  Common, Serial, and MPI fixtures under Spack 1.2;
- a Cray fixture consumes external compiler, MPI, and GPU scopes without a
  compiler or MPI producer group;
- public module paths resolve through projected views, not hashed Spack install
  prefixes.

## Primary references

- Spack 1.2 environment definitions, matrices, groups, `needs`, includes, and
  views: <https://spack.readthedocs.io/en/latest/environments.html>
- Spack module configuration and `use_view`:
  <https://spack.readthedocs.io/en/latest/module_file_support.html>
- Spack native toolchains: <https://spack.readthedocs.io/en/latest/toolchains_yaml.html>
