# Cray wrapper consumption: primary-source research note v1

| Document control | Value |
|---|---|
| Date | 2026-08-28 |
| Status | Research note and recommendation for the Initial Conversion Trials |
| Scope | HPE Cray EX/CPE, Cray MPICH 8.x and 9.x, and the current `cse-pilot` `init-workspace`/static trial handoff |
| Method | Primary sources only: HPE CPE documentation, HPE release notes, and official Spack documentation/source |

## Executive recommendation

There are two valid, but different, consumption models:

1. **Platform CCE + Cray MPICH:** retain the reviewed, module-driven CPE chain
   (`PrgEnv-cray`, CCE, `craype`, `cray-mpich`, and the site-required runtime
   modules) for the first trials. Build and link with `cc`, `CC`, and `ftn`.
   HPE explicitly defines those as the CPE compiler drivers and says that
   `PrgEnv` selects the programming environment.
2. **CSE-built GCC + Cray MPICH:** use HPE's documented driverless Spack model:
   register GCC by its exact compiler paths with `modules: []`, register the
   exact compiler-flavor Cray MPICH prefix as a non-buildable external, and
   retain `+wrappers`. Do not use an ambient `PrgEnv-*`, `PE_ENV`, or CrayPE
   `cc`/`CC`/`ftn` as the compiler selector for this lane.

The second model proves that Spack can consume an external Cray MPICH prefix
with a directly selected GCC. It does **not** prove that an arbitrary
Spack-built GCC can be silently substituted underneath the platform's CrayPE
drivers. HPE documents the drivers as selecting the currently loaded CPE
environment; it does not document a user-facing variable that points `cc` or
`ftn` at an arbitrary compiler executable. A site could provide and support a
custom compiler module/PrgEnv, but that is a new platform integration and must
be validated as such.

For both models, separate compile, link, and launch evidence. A successful
Spack concretization or a one-node link is not evidence that the selected
libfabric/CXI, PMI/PALS, GTL, runtime search path, and Slurm launch path form a
working CPE tuple.

### Trial boundary

This note is guidance for the current static-catalog trial workspace created by
`cse-pilot init-workspace`, its generated `cse-build` entry point, and the
static trial module entry. It does not propose changing the production
Stack Composer renderer or introducing a new renderer mode. The current handoff
already snapshots the reviewed static catalog and includes the full relative
configuration tree; the wrapper policy below applies to how that handoff is
initialized and consumed on Blueback and Fran.

The trial initializer's build entry point may unload an exact ambient external
compiler or MPI module before Spack activates the reviewed chain. This is
different from asking the renderer to discover or rewrite platform policy. A
chain such as `[PrgEnv-aocc, aocc/4.1.0]` remains ordered so that the CPE
programming environment is established before its compiler member is selected.
For the shared CSE GCC lane, the trial process must instead clear ambient
`PrgEnv-*`/`PE_ENV` state and select the managed GCC through its recorded Spack
compiler paths.

## Findings from primary sources

### 1. What `cc`, `CC`, and `ftn` mean

HPE describes `ftn`, `cc`, and `CC` as compiler drivers that forward to the
compiler required by the selected programming environment. Its CCE release
overview says to use those three commands to compile and link, and that the
`craype` module forwards them to the compiler required by the specific
environment ([HPE CCE release overview](https://cpe.ext.hpe.com/docs/24.07/guides/CCE/HPE_Cray_Compiling_Environment_Release_Overview_18.0.0_S-5212.html)).

The `cc` manual says the C compiler is part of several compiler suites and that
the desired `PrgEnv-*` module must be loaded before compiling. It also records
that `cc -c` compiles objects and `cc` performs the final link, so the driver is
relevant at both compile and link time ([HPE `cc` manual](https://cpe.ext.hpe.com/docs/latest/craype/cc.html)).

`PrgEnv` modules are meta-modules, not mere path conveniences. HPE says that
they automatically load the modules essential to the named environment. Its
example shows swapping `PrgEnv-cray` for `PrgEnv-gnu` replacing CCE with
`gcc-native` and reloading dependent CPE packages ([HPE Programming Environment Modules](https://cpe.ext.hpe.com/docs/latest/craype/swap_prg_env.html)).

HPE's module inspection example shows `PrgEnv-cray` setting `PE_ENV=CRAY` and
loading `craype`, `cray-mpich`, and LibSci ([HPE CPE General User Guide, module inspection](https://cpe.ext.hpe.com/docs/latest/getting_started/CPE-General-User-Guide-CSM.html)).
The CPE driver then uses `PE_ENV` and target-module state to resolve the
programming environment and target-specific paths ([HPE environment-module internals](https://cpe.ext.hpe.com/docs/24.07/craype/env_modules_intro.html)).

**Implication:** `cc`, `CC`, and `ftn` are appropriate selectors for a
platform-managed CPE lane. They are not a neutral alias for whichever GCC is
first on `PATH`. Putting a CSE GCC directory on `PATH` while leaving a
`PrgEnv-cray`/`PE_ENV=CRAY` state active is not a supported way to select that
GCC; it can make the driver and the compiler/runtime modules disagree.

### 2. What Cray MPI wrappers do

HPE Cray MPICH 9 documents these wrappers:

| Language | Wrapper names | Documented action |
|---|---|---|
| C | `mpicc` | Invokes the C compiler and links the main MPI library |
| C++ | `mpicxx`, `mpic++` | Invokes the C++ compiler and links the main MPI library |
| Fortran | `mpifort`, `mpif77`, `mpif90` | Invokes the Fortran compiler and links the main and Fortran MPI libraries |

The same HPE page says that these are simple MPI wrappers, that additional
libraries remain the user's responsibility, and that they are **not intended
to replace the link behavior provided by the CrayPE compiler wrappers** ([HPE Cray MPICH 9 `intro_mpi`](https://cpe.ext.hpe.com/docs/latest/mpt/mpich9/intro_mpi.html)).
The MPICH 8 documentation states the same wrapper contract ([HPE Cray MPICH 8 `intro_mpi`](https://cpe.ext.hpe.com/docs/latest/mpt/mpich/intro_mpi.html)).

The wrappers add optional huge-page and XPMEM link inputs when available. HPE
documents `-no-auto-hugetlbfs`, `-no-auto-xpmem`, and `-no-auto-cray-opts` for
turning those additions off. For GPU-aware programs, the wrappers do not
discover GTL libraries automatically; HPE instructs users to link the
appropriate `-lmpi_gtl_cuda` or `-lmpi_gtl_hsa` library ([HPE Cray MPICH 9 wrapper section](https://cpe.ext.hpe.com/docs/latest/mpt/mpich9/intro_mpi.html)).

This gives the practical distinction:

* `cc`/`CC`/`ftn` select a CPE compiler and carry CPE target/library policy;
* `mpicc`/`mpicxx`/`mpifort` select an MPI compile/link interface, but do not
  replace all CPE compiler-driver behavior; and
* a raw compiler path carries neither MPI nor CPE library policy unless those
  inputs are supplied explicitly by the build system or by another wrapper.

The CPE 24.11 release notes record a Cray MPICH 8.1.31 change adding a
`craype` check to the MPI wrappers. The Cray MPICH 9.1.0 notes record fixes for
`mpifort` and `mpicc` ([CPE 24.11 release notes, MPICH 8.1.31](https://cpe.ext.hpe.com/docs/24.11/release_notes/index.html), [CPE 26.03 release notes, MPICH 9.1.0](https://cpe.ext.hpe.com/docs/latest/release_notes/sles_15_6_release_notes.html)).
This is another reason to record the exact MPICH release and wrapper behavior,
not only the package name.

### 3. Can a user GCC be put beneath a Cray wrapper?

HPE documents two supported mechanisms, but they should not be conflated.

**Module-driven CPE.** `PrgEnv-gnu` selects the GNU environment supplied and
integrated by the site/CPE. HPE's examples show the swap replacing CCE with
`gcc-native`. CPE Lmod can also load a user-generated compiler module, but HPE
explicitly limits support to compiler modules released by CPE and says it
cannot guarantee compatibility for user-generated mixes ([HPE CPE General User Guide, mixed compiler support](https://cpe.ext.hpe.com/docs/latest/getting_started/CPE-General-User-Guide-CSM.html)).
Thus, a CSE-built GCC may be put under `cc`/`CC`/`ftn` only if the site has
made it a real, supported CPE compiler/module integration and has validated the
whole resulting chain. There is no documented general-purpose `CC=/path/to/gcc`
override for the CrayPE drivers.

**Driverless Spack.** HPE's Spack integration page explicitly configures CCE,
ROCm, and GCC with full executable paths and `modules: []`. It then configures
Cray MPICH as `buildable: false`, selects a compiler-specific external prefix,
and sets `variants: +wrappers` ([HPE Spack User Documentation](https://cpe.ext.hpe.com/docs/latest/craype/spack.html)).
The page's GCC example uses `/opt/cray/pe/gcc-native/13/bin/gcc`, but the
mechanism is path-based and is the relevant precedent for a CSE-built GCC
prefix. The page does not say to load `PrgEnv-gnu` around that compiler.

HPE's compiler-interoperability guidance makes the boundary explicit: direct
compiler invocation bypasses the CrayPE module/driver selection, and the user
must provide target flags, include paths, linker flags, and MPI flags; Cray MPI
wrappers are an alternative for adding MPI flags ([HPE compiler interoperability](https://cpe.ext.hpe.com/docs/24.07/cce/man7/compiler_interop.7.html)).
HPE's `ftn` manual consequently warns that directly calling GCC/AMD/Intel/NVIDIA
Fortran compilers for compute, login, or service-node code makes the user
responsible for constructing the link options ([HPE `ftn` manual](https://cpe.ext.hpe.com/docs/24.07/craype/ftn.html)).

**Recommendation:** do not invent a third model in which a raw CSE GCC is
placed underneath an ambient `cc`/`CC`/`ftn`. Use direct compiler paths in the
Spack lane, and let the selected Spack/MPI wrapper contract or explicit link
flags provide the MPI closure. If an application build outside Spack needs
MPI wrappers, test the selected `mpicc`/`mpicxx`/`mpifort` with the exact GCC
and runtime environment and record the wrapper's expanded command.

### 4. Runtime variables are part of the contract

HPE defines `CRAYPE_LINK_TYPE` as the default link mode (`dynamic`, `shared`,
or `static`); it takes priority over command-line options ([HPE `cc` environment variables](https://cpe.ext.hpe.com/docs/latest/craype/cc.html)).
The Initial Conversion Trial policy should therefore set or clear it
deliberately rather than inheriting it from a login shell.

HPE defines `CRAY_LD_LIBRARY_PATH` as paths combined with `LD_LIBRARY_PATH`,
for overriding `ld.so.cache` or adding runtime search paths. HPE also warns
that swapping a dynamically linked MPI module does not necessarily change the
runtime selection because of the linker cache; it instructs users to prepend
the selected `CRAY_LD_LIBRARY_PATH`. `PE_LD_LIBRARY_PATH=system` changes the
behavior so CPE modules directly interact with `LD_LIBRARY_PATH` ([HPE CPE General User Guide, runtime library paths](https://cpe.ext.hpe.com/docs/latest/getting_started/CPE-General-User-Guide-CSM.html)).

Therefore, an exact CPE tuple must include, as applicable:

* the compiler executable and compiler runtime (`libgcc`, `libstdc++`, and
  Fortran runtime for GCC);
* the exact Cray MPICH flavor prefix and wrappers;
* Cray PMI/PALS and the scheduler integration;
* libfabric and the required Slingshot provider (normally `cxi` on current
  HPE Cray EX MPICH 9);
* GPU GTL, ROCm/CUDA, XPMEM, and huge-page components when the lane needs them;
* `CRAY_LD_LIBRARY_PATH`, `PE_LD_LIBRARY_PATH`, RPATH/RUNPATH, and any explicit
  `LD_LIBRARY_PATH`; and
* the CPE release and OS against which the tuple was validated.

HPE's CPE 24.11 release notes list Cray MPICH 8.1.31 dependencies of
`craype`, `cray-pals`, `cray-pmi`, and libfabric, and a GNU 11.2-or-later
support floor. HPE's CPE 26.03 notes list MPICH 9.1.0 as requiring the same
families of components, GNU 12.3-or-later, and libfabric ABI 1.6/API 1.14 or
later. MPICH 9 is MPI 4.1; MPICH 8 is MPI 3.1 ([MPICH 8.1.31 release notes](https://cpe.ext.hpe.com/docs/24.11/release_notes/index.html), [MPICH 9.1.0 release notes](https://cpe.ext.hpe.com/docs/latest/release_notes/sles_15_6_release_notes.html)).
These are HPE support floors, not proof that every arbitrary newer/older GCC
and every site-packaged runtime combination is compatible.

### 5. Compile, link, and launch are separate proof points

**Compile:** prove that C, C++, `mpif.h`, `use mpi`, and `use mpi_f08` select
the intended headers/modules and compiler. For the CSE GCC lane, inspect the
compiler command and the Fortran module files; do not infer success from a
version string in a module path.

**Link:** prove that the final link uses the intended MPI libraries and CPE
runtime. Capture the expanded wrapper command, `readelf --dynamic` `NEEDED` and
RPATH/RUNPATH entries, and `ldd` output. Check that no system linker-cache
entry silently supplies a different MPICH, libfabric, PMI, or compiler runtime.
For GPU lanes, explicitly verify the GTL library.

**Launch:** HPE's Cray EX user guide demonstrates Slurm batch and interactive
execution with `srun`, including multi-node examples. It also recommends `ldd`
inside the job for troubleshooting ([HPE Cray EX getting-started guide](https://cpe.ext.hpe.com/docs/26.03/getting_started/CPE_Getting_Started_User_Guide_for_HPE_Cray_Supercomputing_EX_Systems_S-9934.html)).
Cray MPICH documents that PMI controls interaction with Slurm and that
`PMI_SPAWN_SRUN_ARGS` defaults to `--mpi=cray_shasta --exclusive` for relevant
dynamic-process cases ([HPE Cray MPICH 9 `intro_mpi`](https://cpe.ext.hpe.com/docs/latest/mpt/mpich9/intro_mpi.html)).
The CSE acceptance test must run inside actual scheduler allocations, not only
as a login-node singleton. A one-rank singleton is useful as a smoke test, but
it cannot prove Slingshot fabric, PMI, multi-node placement, or provider setup.

### 6. Spack's build interface is not automatically the user interface

The pinned `cray-mpich` package uses `+wrappers` for current Cray MPICH and
inherits Spack's MPICH environment adapter. While building a dependent package,
that adapter sets `MPICH_CC`, `MPICH_CXX`, `MPICH_FC`, `MPICH_F90`, and
`MPICH_F77` to Spack's selected compiler wrappers. The MPI package exposes
`<prefix>/bin/mpicc`, `mpicxx`, `mpif90`, and `mpif77` to the dependent recipe.
Consequently the vendor MPI wrapper can invoke the CSE-selected GCC through
Spack's wrapper layer and retain Spack's dependency/RPATH policy.

Spack also supports a direct-library build: raw compiler invocation plus MPI
headers, libraries, definitions, and runtime paths supplied by the package or
build system. Its packaging guide explicitly distinguishes builds that treat
MPI as an external library from builds that require MPI compiler wrappers
([official Spack MPI packaging guidance](https://spack.readthedocs.io/en/latest/packaging_guide_build.html)).
This validates the operator's observation that Cray MPI can be consumed without
CrayPE or MPI wrapper commands when the full link interface is supplied.

Neither mechanism automatically survives publication as an interactive user
contract. Spack's `MPICH_*` values and compiler wrappers belong to an isolated
dependent-build process. The CSE GCC MPI lane must therefore recreate the
selected interface explicitly:

1. a governed Spack consumer workspace/command that recreates the exact
   dependent-build environment; and
2. an exact-prefix lane for ordinary builds, backed by the vendor MPI wrappers
   with exact `MPICH_*` compiler overrides. A generated direct compiler/link
   interface remains a fallback if a selected provider lacks those wrappers.

The lane must identify its backend and preserve the same compiler, MPI prefix,
and runtime evidence. Successful locked HDF5, FFTW, and related MPI builds
establish the build-plane compile/link/runtime closure. The remaining release
evidence is that the emitted wrapper lane selects the same compiler and that it
runs across multiple nodes through the approved site launcher.

## Recommendation matrix

| Decision point | Platform CCE + Cray MPICH | CSE-built GCC + Cray MPICH |
|---|---|---|
| Compiler selection | Reviewed `PrgEnv-cray`/CCE chain; `cc`, `CC`, `ftn` | Exact GCC/G++/GFortran paths in Spack compiler config; `modules: []` |
| MPI selection | Matching platform `cray-mpich` module/flavor | Exact `cray-mpich` external prefix for the GNU flavor, `buildable: false`, `+wrappers` |
| `PrgEnv-*` / `PE_ENV` | Retain the exact reviewed chain for the initial trial; record `PE_ENV` | Do not inherit ambient `PrgEnv-*` or `PE_ENV`; do not use them as GCC selectors |
| `cc`/`CC`/`ftn` | Primary compile and final-link interface | Not the default interface; only allowed after a separately supported site compiler-module integration |
| `mpicc`/`mpicxx`/`mpifort` | Optional and version-specific; do not assume they replace CrayPE link behavior | Use only through the validated Spack/MPI wrapper path or an explicitly tested direct build; capture underlying compiler and expanded flags |
| CPE libraries | CrayPE supplies target/LibSci/MPI link policy through the driver and modules | Raw GCC does not; supply dependency/MPI flags and runtime paths through Spack/wrappers and verify them |
| Runtime search | Preserve reviewed module paths; check `CRAY_LD_LIBRARY_PATH` and `PE_LD_LIBRARY_PATH` | Explicitly carry exact MPICH/libfabric/PMI/compiler runtime paths; no newest-independent component selection |
| GPU lanes | Use the HPE-documented CPE link path and explicit GTL checks | Use direct GCC/Spack path plus exact GPU-aware MPICH external; explicitly link/verify GTL and toolkit closure |
| Initial status | **Approved for trial only with captured module chain and CPE tuple** | **Candidate/approved for Spack trial; not approved as a generic user `cc` substitution** |
| Promotion gate | C/C++/Fortran compile/link, `ldd`/`readelf`, fabric diagnostics, scheduler multi-node run | Completed locked package-build evidence for compile/link/runtime closure, exact wrapper and CSE GCC binding from the candidate lane, then scheduler multi-node run |

## Blueback and Fran: evidence that must be collected

Run the same evidence script in a clean login shell and inside a compute-node
allocation on **both Blueback and Fran**, separately for each compiler/MPI/GPU
lane. Preserve raw output with the selected CPE release and host identity.

### Platform facts and selection

* `module list`, `module show PrgEnv-*`, `module show cray-mpich`,
  `module show craype-network-*`, `module show cray-pmi`, `module show
  cray-pals`, and `module show` for XPMEM/GTL/toolkit components.
* `echo "$PE_ENV" "$CRAYPE_LINK_TYPE" "$PE_LD_LIBRARY_PATH"` and the full
  `CRAY_LD_LIBRARY_PATH`/`LD_LIBRARY_PATH` values.
* Exact CCE, GCC, Cray MPICH, craype, PMI/PALS, libfabric, provider, OS, CPU,
  GPU, and Slingshot versions; the selected MPICH `ofi/<family>/<version>`
  prefix and its `include`, `lib`, and `bin` contents.

### Compiler and wrapper identity

* For CCE: `type -a cc CC ftn craycc crayCC crayftn`; capture `cc --version`,
  `cc -craype-verbose` on a harmless link, and the CCE paths.
* For CSE GCC: `type -a gcc g++ gfortran`; resolve each path and capture its
  version. Confirm Spack's generated compiler configuration has those exact
  paths and no `modules:` dependency.
* For Cray MPICH: resolve `mpicc`, `mpicxx`/`mpic++`, `mpifort`, `mpif90`, and
  `mpif77` from the selected prefix; capture each wrapper's `--version`,
  `-show`/equivalent expanded command where supported, and the underlying
  compiler. On MPICH 9, also prove that no unwanted CrayPE wrapper state causes
  a wrapper conflict.

### Compile/link checks

* C and C++ MPI hello-world programs.
* Fortran programs using `include 'mpif.h'`, `use mpi`, and `use mpi_f08`.
* `readelf --dynamic` and `ldd` for every resulting executable, checking
  `libmpi`, `libmpich`, libfabric, PMI, compiler runtime, GTL, RPATH/RUNPATH,
  and accidental system-cache resolution.
* `fi_info -p cxi` (or the site-equivalent provider diagnostic) where CXI is
  required, both outside and inside the allocation as appropriate.

### Scheduler and runtime checks

* One-rank singleton smoke test, one-node multi-rank `srun`, and multi-node
  `srun` using the site's required task and CPU-binding options.
* MPI collectives and a representative threaded test; GPU-aware MPI with the
  appropriate `MPICH_GPU_SUPPORT_ENABLED` and explicit GPU mapping where the
  lane claims GPU support.
* Run `ldd` from inside the allocation and record `SLURM_*`, PMI, fabric, and
  GPU-provider diagnostics.
* Repeat after a clean shell/module reset to prove that success does not depend
  on a login-node default or stale linker path.

## Consequences for the local stack-planning model

This recommendation is consistent with the existing local notes:

* [Spack 1.2 Concretizer Cache and Cray PE Runtime Note](spack_1_2_concretizer_cache_and_cray_pe_runtime_note_v1.md)
  already distinguishes module-driven CCE from the driverless external-MPICH
  model and requires a complete runtime tuple before removing the module chain.
* [Cray MPICH GNU compatibility note](cray_mpich_gcc_compatibility_v1.md)
  records the compiler-flavor prefix and Fortran-module checks needed when a
  CSE GCC differs from the GCC used to build a platform MPICH flavor.
* [Cray PE Acceptance Checklist](cray_pe_acceptance_checklist_v1.md) supplies
  the compile/link/runtime and provider evidence gates.
* [Lane and Module Model](lane_and_module_model_v1.md) should continue to bind
  compiler and genuinely compiler-specific Cray MPICH flavors in one lane,
  while keeping provider choice fact/defaults-driven rather than assuming that
  every Cray-hosted lane is module-driven.

For this phase, those are consumption and acceptance constraints on the static
trial handoff. They are not a request to alter the production renderer's
provider-resolution implementation.

## Primary sources

* [HPE Cray Programming Environment 26.03 documentation](https://cpe.ext.hpe.com/docs/latest/)
* [HPE Programming Environment Modules](https://cpe.ext.hpe.com/docs/latest/craype/swap_prg_env.html)
* [HPE Environment Modules internals and `PE_ENV`](https://cpe.ext.hpe.com/docs/24.07/craype/env_modules_intro.html)
* [HPE CCE release overview: compiler drivers](https://cpe.ext.hpe.com/docs/24.07/guides/CCE/HPE_Cray_Compiling_Environment_Release_Overview_18.0.0_S-5212.html)
* [HPE `cc` manual: link mode and runtime paths](https://cpe.ext.hpe.com/docs/latest/craype/cc.html)
* [HPE `ftn` manual](https://cpe.ext.hpe.com/docs/24.07/craype/ftn.html)
* [HPE compiler interoperability guidance](https://cpe.ext.hpe.com/docs/24.07/cce/man7/compiler_interop.7.html)
* [HPE Cray MPICH 8 `intro_mpi`](https://cpe.ext.hpe.com/docs/latest/mpt/mpich/intro_mpi.html)
* [HPE Cray MPICH 9 `intro_mpi`](https://cpe.ext.hpe.com/docs/latest/mpt/mpich9/intro_mpi.html)
* [HPE CPE Spack User Documentation](https://cpe.ext.hpe.com/docs/latest/craype/spack.html)
* [HPE CPE 24.11 release notes: Cray MPICH 8.1.31](https://cpe.ext.hpe.com/docs/24.11/release_notes/index.html)
* [HPE CPE 26.03 SLES release notes: Cray MPICH 9.1.0](https://cpe.ext.hpe.com/docs/latest/release_notes/sles_15_6_release_notes.html)
* [HPE Cray EX getting-started guide: Slurm and `srun`](https://cpe.ext.hpe.com/docs/26.03/getting_started/CPE_Getting_Started_User_Guide_for_HPE_Cray_Supercomputing_EX_Systems_S-9934.html)
* [Official Spack packaging guide: MPI wrappers and Cray behavior](https://spack.readthedocs.io/en/latest/packaging_guide_build.html)
