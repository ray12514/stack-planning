# CSE Spack Learnings

**Systems:** Raider (Penguin Solutions AMD CPU) and Blueback (Cray EX)\
**Workstream:** CSE iteration work\
**Author:** Ravon\
**Updated:** 2026-07-14

This document collects what we learned while building Spack environments on Raider and Blueback. It records what worked, what failed, why the two systems needed different approaches, and what we would do when bringing the same process to another machine. The companion summary covers the main results without the build details.

## Contents

1. What We Built and Learned
2. Lane Coverage
3. What We Learned on Blueback (Cray EX)
4. What We Learned on Raider (Penguin Solutions)
5. Spack 1.x Lessons That Apply Across Systems
6. Checks and Known Limits
7. What We Still Need to Do
8. Appendix A: Per-Lane Environment Detail
9. How to Read This Document
10. References

## 1. What We Built and Learned
We built Spack software stacks on Raider and Blueback using the Spack 1.x compilers-as-dependencies model. That model first landed in Spack 1.0; this work used Spack 1.1 and newer. [1, 31] Raider is a Penguin Solutions AMD CPU system running RHEL 8 and Slurm. Blueback is a Cray EX system running SLES 15, Slurm, and Slingshot 11. The initial smoke tests use HDF5 with and without MPI, plus Kokkos with and without accelerator support.

We use the word **lane** for one complete build setup: the Spack environment, compiler, MPI implementation, accelerator support, and the system where it runs. Eleven lanes are deployed and verified.

External citations support package rules, upstream constraints, and system architecture. Results without citations, including lane outcomes, error signatures, and workarounds, come from our testing.

**Version basis.** The lane results are the tested record. The reference audit was updated on 2026-07-10 against Spack v1.2.0 and `spack-packages v2026.06.0`, the package release tested with Spack v1.2.0. [31, 32] Recipe-backed findings cite that package release unless a finding is tied to local testing or facility documentation.

### User-facing stack layout
[Verified, General]

This work also tested whether Spack can model the way the current CSE software environment is consumed by users. The question was not only whether HDF5 or Kokkos could compile. The question was whether normal Spack environment, module, view, and projection mechanisms can produce the user-facing layout we want. The lane model gives each compiler/MPI/accelerator combination a clear boundary. Spack still owns the concrete install tree and lockfile, but users should see curated module names and projected paths rather than raw hash-heavy install prefixes.

The practical layout goal is straightforward:

- expose only the packages that are meant to be public in the stack;
- keep internal build tools and low-level implementation dependencies out of the normal user module surface unless policy marks them public;
- use projections and module naming so users can distinguish variants such as serial and MPI builds;
- keep each lane's modules, view, and validation record tied to the compiler, MPI, and accelerator combination that produced it.

The HDF5 and Kokkos smoke set was useful for this because it exercised common user-facing patterns without requiring the broader CSE package subset. HDF5 tests the serial/MPI split, Kokkos tests CPU and accelerator variants, and the lane matrix tests whether the same presentation model still works across Linux-style and Cray-style systems. In that sense, the smoke set is also a stack-layout proof of concept, not only a build test.

**Finding status tags used in this document**

- **Verified:** Reproduced and traced to a confirmed cause in the current source.
- **Observed:** Reproduced, but the root cause is not yet confirmed.
- **Working assumption:** Supported by the current results, but not tested across enough lanes to treat as a general rule.
- **Time-bounded:** Valid for the current software release and expected to change at a known upstream release.

**Deployed lanes**

- **Raider:** Six lanes covering GCC and AOCC with site OpenMPI, Spack-built OpenMPI, and Spack-built MPICH, plus NVHPC with its bundled OpenMPI and CUDA. The `gcc-sitempi` lane also includes a validated GCC+CUDA Kokkos build.
- **Blueback:** Five Cray PrgEnv lanes using `cray-mpich`: CCE, GCC, AOCC, Intel, and AMDClang. The NVHPC Cray lane is deferred.

Section 2 shows the coverage tables. Appendix A lists the compiler, external packages, and Spack-built specs for each lane.

**Main findings**

- The same environment-generation process produced eleven working environments across six compiler families, three MPI families, CUDA, and ROCm.
- Raider supports two useful MPI models. GCC and AOCC work with the site OpenMPI module and with OpenMPI built by Spack.
- GCC+CUDA is validated on Raider, and GCC+ROCm is validated on Blueback. These host-compiler combinations cover more of the general package graph than the tested NVHPC and AMDClang lanes. The newer Blueback ROCm 7 stack has also produced GNU-hosted ROCm builds, but that does not yet complete the AMD/ROCm compiler lane. See §4.4 and §6.2.
- Intel oneAPI needs a registered GCC because `intel-oneapi-runtime` links against `gcc-runtime`. The ROCm compiler is selected with `%rocmcc`, not with the `llvm-amdgpu` package name. [19, 20] See §5.1 and §5.2.
- Each Cray lane must match one loaded, supported PrgEnv. On Blueback, that means one compiler family per lane, but not necessarily an exact compiler-version match to the version label embedded in the Cray MPICH path. HPE Cray MPI release notes list supported compiler minimums, such as GNU 11.2 or later for Cray MPI 9.0.1 and GNU 12.3 or later for Cray MPI 9.1.0. [33, 34] In practice, the path label is a compiler-family baseline for a vendor-supported flavor. Other Cray sites may provide vendor-supported hybrid PrgEnvs, but those should still be treated as their own lanes, not as ad hoc compiler mixes. [2, 12, 30] The recommended Fortran MPI modules are compiler-specific. The legacy `mpif.h` include file avoids the immediate module-file check, but it does not guarantee cross-compiler binary compatibility. [4, 28, 29] See §3.1 and §3.5.
- `cray-mpich` remains the default MPI on Slingshot 11. OpenMPI 5 has two documented ways to use CXI for inter-node traffic while keeping intra-node traffic in shared memory: OFI MTL with LINKx/LNX, or OB1 with the shared-memory and OFI BTLs. The BTL path does not need LNX, but published results show that it still needs performance testing. [5, 6, 7, 8] See §3.6.
- GPU-aware `cray-mpich` needs the matching GTL library. Facility documentation confirms that GTL must be linked for GPU-buffer communication. [9, 11, 12, 30] `LD_PRELOAD` works in the current lanes; linking GTL directly is the long-term fix. See §3.7.
- `spack verify libraries` checks recorded RPATHs and includes a built-in allowlist for expected unresolved libraries. [23, 24] Because healthy site libraries can still produce warnings, our deployment check uses `ldd` and executable startup tests. See §6.1.

## 2. Lane Coverage
**Lane result key**

- **Passed:** The lane built successfully and passed the initial HDF5 and Kokkos smoke tests.
- **Built:** The lane built successfully, but the smoke tests were not run or are not yet complete.
- **Deferred:** The lane was not built during this round.

### Raider (Penguin Solutions, RHEL 8, Slurm)
| Lane | Compiler | MPI | Accelerator | Lane result |
|---|---|---|---|---|
| `gcc-sitempi` | External GCC 8 | External OpenMPI (module) | NVIDIA CUDA (Kokkos) | Passed |
| `gcc-openmpi` | Spack-built GCC 15 | Spack-built OpenMPI 5 | n/a | Passed |
| `gcc-mpich` | External GCC 8 | Spack-built MPICH 4.2 | n/a | Passed |
| `aocc-sitempi` | External AOCC | External OpenMPI (module) | n/a | Passed |
| `aocc-openmpi` | External AOCC | Spack-built OpenMPI 5 | n/a | Passed |
| `nvhpc-nvompi` | NVHPC SDK 25.11 | SDK-bundled HPC-X OpenMPI | NVIDIA CUDA | Passed (B.9) |

On Raider, GCC and AOCC each work with the site OpenMPI module and with OpenMPI 5 built by Spack. These lanes show that we can keep MPI under site management or let Spack build the MPI stack. The `gcc-mpich` lane adds a third model: Spack builds MPICH while UCX, Slurm, and PMIx remain site externals.

### Blueback (Cray EX, SLES 15, Slurm, Slingshot 11 HSN)
| Lane | PrgEnv compiler | MPI | Accelerator | Lane result |
|---|---|---|---|---|
| `cce-craympich` | CCE (PrgEnv-cray) | `cray-mpich` | n/a | Passed |
| `gcc-craympich` | GCC (PrgEnv-gnu) | `cray-mpich` | MI300A ROCm | Passed |
| `aocc-craympich` | AOCC (PrgEnv-aocc) | `cray-mpich` | n/a | Passed |
| `intel-craympich` | oneAPI + site GCC | `cray-mpich` | n/a | Passed |
| `amdclang-craympich` | AMDClang (PrgEnv-amd, GPU-aware host compiler) | `cray-mpich` | MI300A | Passed |
| `nvhpc-craympich` | NVHPC (PrgEnv-nvhpc) | `cray-mpich` | n/a | Deferred |

Appendix A provides the external packages, Spack-built specs, and compiler and MPI versions for each lane.

## 3. What We Learned on Blueback (Cray EX)
Blueback's Cray Programming Environment adds constraints that do not exist on Raider. The most important rule is simple: each Spack lane must match one loaded, supported PrgEnv. On Blueback, the tested PrgEnvs map cleanly to one compiler family per lane. That rule is about the supported compiler family and wrapper-selected environment, not about forcing the active compiler version to equal the version label in the Cray MPICH directory. Sections 3.2 through 3.5 explain how the compiler, modules, external packages, and Fortran interface enforce that rule.

### 3.1 One PrgEnv per Spack environment
[Verified, Cray-specific]

A Cray EX lane must match one loaded, supported PrgEnv. On Blueback, each tested PrgEnv also maps to one compiler family. Three parts of the environment make that separation necessary:

- `cray-mpich` stores compiler-generated Fortran modules and its Fortran interfaces by compiler flavor (§3.5), so the external prefix selects a supported compiler-family flavor.
- The PrgEnv module sets compiler-specific variables such as `CRAY_LD_LIBRARY_PATH`, `PE_FORTRAN_PKGCONFIG_LIBS`, and `CRAY_PE_PKGCONFIG_PATH`.
- The `cray-mpich` external carries a `%<compiler>@<v>` stamp consistent with the active PrgEnv family (§3.4). A second compiler family has no matching provider in the same environment.

The practical rule on Blueback is one loaded PrgEnv and one compiler family per lane. If that compiler cannot build a spec, the spec belongs in another lane. The five current Cray lanes therefore come from five separate PrgEnv loads.

HPE's Spack guidance follows the same model. It documents separate `cray-mpich` prefixes for CCE, GCC, and ROCmCC and gives each external a compiler-family stamp. [2] The Fortran module bindings make the compiler relationship explicit, while the legacy include-file binding still depends on implementation-specific binary compatibility (§3.5).

The version label inside a Cray MPICH flavor path should not be read as an exact active-compiler requirement. HPE Cray MPI release notes describe compiler support as minimum supported compiler releases. For example, Cray MPI 9.0.1 lists GNU 11.2 or later, and Cray MPI 9.1.0 lists GNU 12.3 or later. [33, 34] That supports the interpretation that `ofi/gnu/11.2` or `ofi/gnu/12.3` is a vendor-supported GNU flavor baseline, not proof that only that exact GCC version may consume the interface. The practical requirement is still validation through the loaded PrgEnv, the Cray PE wrappers, and the direct-compiler Spack lane on the target system.

The rule still applies to a C/C++-only lane because the environment is generated with one PrgEnv loaded. The C ABI is not the problem: the `cray-mpich` C libraries can be linked across compiler families, and `mpi.h` is portable. The `amdclang-craympich` lane shows the distinction. It is intentionally limited to C/C++, but it still needs its own PrgEnv-specific lane (§6.2).

Other Cray systems can expose vendor-supported hybrid PrgEnvs. For example, ARCHER2 documents GPU development PrgEnvs where `ftn` uses GNU or Cray Fortran while `cc` and `CC` use AMD Clang. [12] Frontier also documents that PrgEnv-amd and ROCm module choices have to stay aligned for GPU development. [30] These are supported site environments, not arbitrary user mixes of compilers. In Spack, a hybrid PrgEnv should be represented as its own lane and validated against the MPI and library interfaces supplied with that environment.

### 3.2 Use the loaded PrgEnv compiler as a Spack external
[Verified, Cray-specific]

Each Blueback lane uses the compiler supplied by its loaded PrgEnv. Spack does not bootstrap another copy of that compiler. HPE's CPE documentation recommends this driver-less approach and provides examples for CCE, ROCmCC, and GCC. [2]

- HPE documents compiler-specific CPE paths and external package prefixes for the supported PrgEnv compilers. [2]
- The `cray-mpich` external's `%<compiler>@<v>` stamp must stay consistent with the active PrgEnv family. Exact version matching is not the right rule for Cray MPICH flavor paths; HPE release notes list supported compiler minimums, and the Cray PE wrappers define the supported pairing. [33, 34]

**How we configure it.** In `packages.yaml`, the PrgEnv compiler is a `buildable: false` external, and its `modules:` list includes the PrgEnv umbrella module. The same pattern applies to CCE, PrgEnv-gnu GCC, AOCC, and NVHPC.

The external points directly to the compiler executables: `craycc` / `crayCC` / `crayftn` for CCE, `amdclang` / `amdflang` for ROCmCC, and the native `gcc` / `g++` / `gfortran` binaries for GCC. It does not point to the unified `cc` / `CC` / `ftn` CPE drivers. HPE explains that direct compiler invocation leaves MPI and LibSci tooling out of the command and gives Spack control over the build. [2] The consequence is that anything normally supplied by the CPE drivers, including MPI flags, LibSci, and the GPU Transport Layer in §3.7, has to be added explicitly.

The same lesson applies on other HPC systems that provide a vendor-tuned GCC through a site module, including Cray PE, Bull SCS, and HPE-supplied GCC. Use the site compiler as the external instead of letting Spack bootstrap a parallel copy.

**Why use Cray externals instead of building the whole stack with Spack?** On Raider, Spack-built compilers and MPI providers are a reasonable baseline because the system behaves like a conventional Linux cluster. On Blueback, the vendor MPI is tied to the Cray Programming Environment, Slingshot 11, Libfabric/CXI, the scheduler launch path, compiler-specific Fortran interfaces, and GPU Transport Layer support. Rebuilding MPI inside Spack is possible, but it creates a new lane that must prove those same behaviors. For the production-facing Cray lanes, we therefore use the site-provided compiler and `cray-mpich` as externals, then use Spack to build the application stack above them.

### 3.3 Keep the full Cray PE module set until we know the minimum
[Verified, Cray-specific; minimum closure not bisected]

The reliable configuration on Blueback includes the full Cray PE module set in the `cray-mpich` external's `modules:` list: the `PrgEnv-<flavour>` umbrella, `cray-mpich`, `craype-network-ofi`, libfabric, xpmem, and `craype-hugepages2M`.

During early testing, removing entries caused unresolved `fi_*` and `PMI2_*` symbols and left required PE variables out of Fortran builds. Restoring the full set fixed those failures.

We have not yet determined the smallest module set that works. libfabric and xpmem are also declared as Spack externals with installation prefixes, so Spack may be able to find their libraries without loading their modules. Those modules may only be needed for PE-specific variables such as `CRAY_PE_PKGCONFIG_PATH`, `PE_FORTRAN_PKGCONFIG_LIBS`, and `CRAY_LD_LIBRARY_PATH`. For now, the full set is conservative and reliable. Reducing it is follow-up work.

This result applies to the Blueback Cray PE layout. It is not a general rule for other MPI implementations. Across the five current Cray lanes, only the `PrgEnv-<flavour>` entry changes.

### 3.4 Use prefer: not require: at the all-packages level
[Verified, General lesson, surfaced first on Cray]

An all-packages compiler requirement is too strict for an environment that also uses system libraries. Setting `all: require: "%<family>@<v>"` in `packages.yaml` rejects every untagged external, including glibc, OpenSSL, curl, ncurses, Perl, Python, libfabric, Slurm, PMIx, and PALS. These packages have no compiler stamp and no compiler-specific ABI requirement, so concretization fails before Spack can evaluate the useful part of the graph.

**What works.** Use `all: prefer: "%<family>@<v>"` and leave general system externals untagged. A preference changes Spack's ordering without excluding every other choice; a requirement limits the solutions Spack may accept. [3] Reserve a `%<family>@<v>` requirement for a package such as an MPI external that has a real compiler ABI dependency.

This issue appeared first on Cray because `cray-mpich` makes the compiler relationship visible, but the lesson applies to any site combining vendor compilers with compiler-neutral system libraries.

### 3.5 The Fortran MPI binding affects compiler compatibility
[Verified, Cray-specific; underlying rule is general]

Fortran applications can access MPI in three ways. The choice changes compile-time checking and determines whether the compiler reads a generated module file:

1. **`use mpi_f08`:** This is the MPI-4.1 recommended binding. It provides explicit interfaces, compile-time argument checking, and distinct derived types for MPI handles. With the required compiler support, it also provides the most complete protection for nonblocking operations and modern Fortran features. [28]
2. **`use mpi`:** This older module also provides compile-time argument checking, but it represents MPI handles as `INTEGER` and remains mainly for backward compatibility. [28]
3. **`include 'mpif.h'`:** This is a textual Fortran include file, not the C header `mpi.h`. It usually provides less compile-time argument checking. MPI-4.1 deprecates it and strongly encourages applications to use one of the modules instead. [28]

Both module forms consume compiler-generated `.mod` files. Those files are not portable across compiler families. Intel documents that there is no common `.mod` format across vendors. [4] For example, gfortran cannot read an AOCC module file, and oneAPI cannot read an AMDClang module file.

Cray-MPICH installs its Fortran interfaces in compiler-flavor directories. HPE's Spack documentation uses the same directory model when selecting an external prefix. [2] The paths below show the `mpi.mod` layout; the `mpi_f08` module has the same compiler-generated module constraint.

```text
/opt/cray/pe/mpich/8.1.32/ofi/cray/17.0/include/mpi.mod
/opt/cray/pe/mpich/8.1.32/ofi/gnu/12.3/include/mpi.mod
/opt/cray/pe/mpich/8.1.32/ofi/aocc/4.2/include/mpi.mod
/opt/cray/pe/mpich/8.1.32/ofi/intel/2024.0/include/mpi.mod
/opt/cray/pe/mpich/8.1.32/ofi/amd/6.0/include/mpi.mod
/opt/cray/pe/mpich/8.1.32/ofi/nvidia/25.1/include/mpi.mod
```
The `cray-mpich` external's `prefix:` should point to the directory selected by the supported PrgEnv and wrapper pairing. The directory version label may be older than the active compiler version. For example, a PrgEnv-gnu lane can expose a newer GCC while Cray MPICH points at a GNU flavor directory labeled with the minimum supported GNU level for that MPI release. [33, 34] Selecting the wrong compiler-family directory still causes the first module-based `+fortran +mpi` package to fail with `not a <X> Fortran module file`.

`mpif.h` is more permissive at compile time because the compiler reads text instead of a `.mod` file. A source file may therefore compile with a compiler that could not read the installed `mpi.mod`. That removes one immediate barrier, but it does not establish cross-compiler compatibility. The MPI standard notes that Fortran binding choices can use different binary interfaces and procedure names. Calling conventions and values such as Fortran `LOGICAL` representations can also depend on the compiler. Users are advised to follow the MPI implementation's documented compatibility rules. [29]

The practical lane rule therefore does not change for Blueback: a supported Cray lane that includes Fortran uses a supported compiler-family pairing for C, C++, and Fortran, and that family matches the selected `cray-mpich` flavor directory. The exact version label in the path is not enough to prove or disprove support. The authority is the Cray PE wrapper behavior plus validation. Confirm the pairing first with `cc`, `CC`, and `ftn`, then reproduce the same include, link, and runtime behavior in the direct-compiler Spack lane. The minimum validation set should include C, C++, `mpif.h`, `use mpi`, and `use mpi_f08` compile/link tests. If a Cray site provides a hybrid PrgEnv, treat that supported hybrid as its own lane and follow the MPI interface supplied for that environment. A legacy `mpif.h` application built with another compiler should be treated as a separate compatibility experiment and must pass link and runtime tests against the exact MPI installation. For new or actively maintained code, prefer `use mpi_f08`.

### 3.6 Why cray-mpich remains the default on Slingshot 11
[Working assumption, Cray-specific; upstream architecture documented, not tested on Blueback]

OpenMPI can run on Slingshot 11, so basic support is not the question. The open question is whether a particular OpenMPI configuration gives us the intra-node and inter-node performance, launch behavior, and site integration we need. Until that is tested on Blueback, `cray-mpich` remains the safer default.

OpenMPI 5 supports libfabric through both an OFI MTL and an OFI BTL, and its documentation lists HPE Slingshot 11 among the supported OFI networks. [5] The two paths handle intra-node traffic differently.

**OFI MTL path.** OpenMPI's `cm` PML selects one active MTL. If the OFI MTL selects CXI directly, both intra-node and inter-node messages use CXI. Published Slingshot 11 testing reports poor intra-node latency and bandwidth with CXI alone, especially as the number of processes on a node increases. [7]

Libfabric's LINKx provider, exposed as `lnx`, combines several providers behind one interface. On Slingshot, it can combine `shm` and `cxi`, using shared memory for intra-node peers and CXI for inter-node peers. [8] Published results show much better intra-node performance than CXI alone. [7] Current libfabric documentation also lists limits in hardware offload, memory registration, and supported operation types. That means the site still has to test LNX with its applications and installed libfabric release. [8]

**OFI BTL path.** OpenMPI's `ob1` PML can activate more than one BTL. Pairing the `sm` BTL with the OFI BTL lets OpenMPI shared memory, including XPMEM when available, handle intra-node peers while libfabric CXI handles inter-node peers. [5, 6] This avoids the intra-node CXI penalty without using LINKx.

The Slingshot 11 paper tested this design and confirmed that the required changes were present in the OpenMPI 5.0.x branch. The authors did not choose it as their preferred path because the OFI BTL needed substantial refactoring to approach the OFI MTL's inter-node performance. [7] The BTL path can reach both local and remote peers; the concern is performance and readiness, not basic connectivity.

**What Blueback still needs to test.** Both paths need an OFI stack that exposes the Slingshot 11 CXI provider. HPE documents CXI as the default Slingshot 11 provider for Cray MPI. [9] We have not tested the BTL path with the exact OpenMPI, HPE libfabric, and Slingshot Host Software versions installed on Blueback. The HPE-provided libfabric should be the first option. Building another libfabric may work, but it adds another component whose compatibility and performance have to be tested.

**Launcher integration.** The resource manager has to give the job access to its Slingshot VNI. The Slingshot 11 paper documents `srun` establishing that access on Slurm. On PBS-based HPE systems, OpenMPI needs PALS-aware PRRTE support. [7] Current OpenMPI documentation describes the PALS ESS/PLM components and automatic PALS use when `mpirun` starts inside a PBS allocation. [10]

**What we will do.** Keep `cray-mpich` as the default MPI on Slingshot 11 and offer OpenMPI when an application requires it. An OpenMPI lane should test either OFI MTL with LNX or OB1 with the `sm` and OFI BTLs. It should also test the scheduler-specific launch path that establishes the VNI. On PBS, check the PALS ESS/PLM components with `prte_info`; on Slurm, check the `srun`/PMIx path. Before treating the lane as performance-equivalent to the vendor MPI, benchmark workloads that include both intra-node and inter-node messages.

### 3.7 GTL must be attached for GPU-aware cray-mpich
[Verified, Cray-specific, GPU-aware cray-mpich lanes]

GPU-aware `cray-mpich` needs a GPU Transport Layer library: `libmpi_gtl_hsa` for AMD GPUs or `libmpi_gtl_cuda` for NVIDIA GPUs. HPE documents GPU-aware Cray MPI for both device families, and facility documentation identifies GTL as a required link-time dependency when MPI communicates directly with GPU buffers. [9, 11, 12, 30] The CPE compiler drivers normally add the matching library when an accelerator target is enabled. [11, 30]

Our lanes invoke the compilers directly instead of using the CPE drivers, so the `craype-accel-*` tooling does not add GTL. The Spack spec also has no GTL package or dependency. As a result, the package builds successfully, but an MPI test using GPU device pointers fails at runtime.

The MI300A packages built successfully, and the device-pointer MPI test passed as soon as GTL was attached. Two integration options are available:

- **Runtime preload:** Add the matching GTL library through `LD_PRELOAD`. The MI300A test passes with `libmpi_gtl_hsa` preloaded in this work.
- **Build-time integration:** Add the GTL external and its link flags to the lane so the executable records the dependency at build time.
GTL lives under `/opt/cray/pe`, so this also exposes a limit in `spack verify libraries` (§6.1). A missing GTL is the kind of dependency that the command may not flag. The check that catches it is a runtime smoke test that actually passes a GPU device pointer through MPI.

**What we will do.** Attach the matching GTL library to every `cray-mpich` lane that passes GPU device pointers. The current validation cases are `gcc-craympich` and `amdclang-craympich`, but they are not the only possible configurations. Future CCE or AOCC GPU lanes need the same treatment. NVHPC is not a GPU lane on Blueback, and Intel GPU support has not been validated. Existing binaries can continue using `LD_PRELOAD`; new builds should link GTL directly so they do not depend on a runtime preload.

### 3.8 Keep observed platform catalogs separate from lane selection
[Verified, General lesson, surfaced on Blueback]

Cluster discovery should retain every real compiler, MPI, GPU toolkit, and
platform-runtime generation it observes. A build lane should consume only one
coherent selection from that catalog. On Blueback, rendering every observed
Cray MPICH and Cray PE generation into one lane produced ambiguous externals and
made it possible to mix components from different CPE releases. The working
pipeline keeps the complete inventory in the fact sheet, then renders only the
lane-selected Cray MPICH generation and compiler flavor.

Compiler binding is expressed through Spack's native `toolchains.yaml`. The
Cray MPICH package external remains a plain provider spec such as
`cray-mpich@9.1.0`; the toolchain binds it to the selected compiler. This keeps
package discovery, platform selection, and compiler/MPI pairing as separate,
reviewable facts.

The same evidence rule applies to GPU toolkits. The Blueback HIP external must
use the ROCm toolkit root proven by the discovered `hipcc` binary. Constructing
an assumed `$ROCM_ROOT/hip` prefix produced a non-existent compiler path. A
generated fact sheet must report what the probe verified, not synthesize a
layout from a vendor convention.

Platform runtime packages remain conservative. Cray GTL, PMI, and PALS are
recorded as observed facts, but they are not rendered as Spack externals until a
package repository defines their Spack package semantics. LibSci and fabric
externals are rendered only when the selected policy says they are consumable.

Finally, rendered intent is not enough to prove lane isolation. The serial
lane is accepted only when its concrete lockfile contains no MPI
implementation, including through transitive dependencies. This check caught a
NetCDF chain whose root requested `~mpi` while a transitive HDF5 dependency was
still free to select its default `+mpi` variant. Pinning the complete dependency
chain and auditing the lockfile made the lane definition enforceable.

### 3.9 A PE update silently relinks existing binaries through sonames
[Observed on Blueback; the mechanism is general]

After the Blueback system update we rebuilt the smoke package set against the
newer programming environment, and everything built cleanly. The update also
delivered a newer libfabric, moving from the 1.2x release that shipped with
the older Cray PE to a 2.x release (it also delivered the ROCm 7 stack, whose
compatibility limits are covered in §6.2). The finding is about the packages
built **before** the update: they still ran, but inspection showed them
resolving the **new** libfabric at run time, not the one present when they
were built. The soname did not change across that version jump, the default PE
environment places the new library on the runtime search path, and the loader
resolves by soname.

Nothing broke, and libfabric's design is why. The project maintains ABI
compatibility deliberately: it exports only a handful of functions directly,
routes most calls through static inline functions and provider function
pointers, and extends structures by appending fields rather than changing
existing ones, so "compiled applications can continue to work as-is" across
releases. [35] The 2.0 release was published as a minor ABI revision intended
as a drop-in replacement for existing 1.x binaries. [36] So this was a
designed-for outcome rather than luck, and our inspection agreed with it.

Two cautions keep it from being a general reassurance. First, 2.0 is ABI
compatible but **not** API compatible: calls that worked against 1.x can fail
against 2.x, so the relief applies to already-built binaries, not to the next
rebuild or to source we compile later. [36] Second, upstream's ABI promise
covers upstream's library. The PE ships HPE's libfabric with the CXI provider,
and provider behavior and performance can move within an ABI-stable release,
which is a runtime question our acceptance tests answer, not one the soname
answers.

**Why Spack allowed it.** We build against `cray-mpich` as an external.
Registering an external records that package, not its dependency closure. The
PE's MPI carries its own runtime requirements, libfabric among them, and
because those were not themselves nodes in Spack's graph for our builds,
nothing was RPATH-pinned to a specific libfabric prefix. They remain
**unmanaged runtime dependencies**: the package needs them on the runtime
path to run at all, they are satisfied by whatever the loaded environment
provides today, and the system can change them underneath an installed stack
without touching a single Spack-owned file.

The general rule: when you register an external without registering the
externals it depends on, that dependency closure is resolved by the dynamic
loader at run time, not by Spack at build time. Build time captures whatever
was loaded then; run time uses whatever the environment provides now. The
drift is invisible to the lockfile and to `spack verify manifest`, because no
installed file changed. Only runtime inspection shows it: `ldd` against the
recorded runtime fingerprint, or provider diagnostics.

**Mitigation.** This is the concrete case behind the platform runtime
fingerprint and the transition gate (SOP §7 and
`platform_runtime_set_design_v1.md`). Record the exact libfabric, CXI, and
PE component versions a lane was built and validated against. On a system
update, diff the fingerprint, then decide per lane: revalidate against the
new runtime with the acceptance tests, pin the old runtime set explicitly
where the site still supports it, or rebuild. "Same soname and it still
starts" is not compatibility evidence. This also sharpens the §6.1 practice:
`spack verify libraries` will not flag the swap, because the library resolves
either way. The check that catches it is comparing resolved paths against
the recorded fingerprint, not checking that resolution succeeds.

## 4. What We Learned on Raider (Penguin Solutions)

### 4.1 PMIx: externalize as a hint, not as a hard pin
[Verified, General]

Raider provides PMIx 2.2.5 under `/usr`. That version can remain available to compatible packages, but it is too old for the tested MPICH 4.2 configuration.

When `packages.yaml` marked the site PMIx as `buildable: false`, MPICH failed during compilation because PMIx 4.x symbols were missing: `PMIX_FABRIC_COORDINATES`, `PMIX_COORD`, and `PMIX_ARGV_SPLIT`. The Spack MPICH recipe adds a PMIx dependency when `pmi=pmix`, but it does not set a minimum version. [13] The solver was therefore allowed to choose the older site external.

**What works.** Two settings are needed together:

- Keep the detected PMIx external in `packages.yaml`, but set `buildable: true`. Compatible packages may still use it, while Spack may build a newer version for packages that need one.
- Add `^pmix@4` to the `gcc-mpich` MPICH spec so this consumer cannot select the older external.

The broader lesson is to distinguish system packages that must stay under operating system management from packages that are only useful as hints. OpenSSL and curl remain `buildable: false` because DNF patches them under `/usr`. Other detected libraries can remain `buildable: true` so the solver has another option when a consumer needs a newer version.

### 4.2 cmake ./bootstrap intermittently fails on system curl
[Observed, root cause not pinned]

The CMake build sometimes fails to find the system curl even though the same build succeeds on retry. The Spack CMake recipe uses system curl for both `+ownlibs` and `~ownlibs`. [16] In this case, `./bootstrap --system-curl` uses the `buildable: false` curl external under `/usr` and intermittently reports:

```text
Could NOT find CURL (missing: CURL_LIBRARY CURL_INCLUDE_DIR)
```

We replayed the captured Spack environment by hand with the same flags, `spack-build-env.txt`, and CMake source. Six isolation attempts succeeded. Re-running `spack install cmake` for the same spec hash also succeeds on the next attempt. The problem appears only through the Spack install driver, but it is not repeatable enough to isolate further.

**Current workaround.** Retry the build. We did not switch CMake to bundled curl. If we can produce a reliable reproducer, this may be worth filing as a Spack bug.

### 4.3 Reusing CMake across lanes requires three matching conditions
[Verified, General]

A CMake build may already exist in the shared buildcache, but that does not guarantee that a new lane will reuse it. Spack can still choose a new hash and rebuild CMake, or concretization can fail if the lane's compiler cannot build CMake.

Spack buildcaches distribute installed specs and their dependencies, and the concretizer can reuse specs from local stores and registered buildcaches. [14, 15] The `nvhpc-nvompi` lane used this path to reuse CMake built with GCC.

Reuse worked only when all three conditions matched:

1. The reuse pool contained CMake and its full dependency set: CMake, gmake, pkgconf, ncurses, and zlib-ng, all built with the same compiler. A rule for CMake alone does not match when one dependency differs.
2. `--buildcache-uri` was passed to every Spack command that was allowed to reuse the build. Because each lane has its own `install_tree`, cross-lane reuse flows through the shared mirror.
3. The lane's local `install_tree` did not contain conflicting builds of those dependencies. With `reuse: roots: true`, Spack prefers a local installation over a buildcache fetch. A dependency such as ncurses left behind by an earlier attempt can therefore keep producing a different CMake hash.

When reuse does not happen as expected, clear the lane's local store before reconcretizing. Reusing CMake saves build time and avoids repeating the intermittent build path described in §4.2.

### 4.4 Vendor GPU compilers cover a narrower general package graph
[Working assumption, based on two vendor-host-compiler lanes]

The tested NVHPC and AMDClang lanes encountered more restrictions in the general package graph than the GCC-hosted GPU builds. This conclusion is based on two vendor-host-compiler lanes, compared with the separate GCC+CUDA and GCC+ROCm results.

The `nvhpc-nvompi` lane showed three restrictions:

- The Spack CMake recipe rejects `+ownlibs %nvhpc` because CMake's vendored dependencies do not build with NVHPC. [16] The `~ownlibs` path was not viable under this lane's dependency constraints, so the lane reused a GCC-built CMake.
- A C/C++ difference involving `_Float16` required HDF5 to use `~cxx`.
- Kokkos `+cuda` required `+wrapper`. Without it, compilation failed. Kokkos documents `nvcc_wrapper` as the tool that separates host and device flags and routes CUDA C++ compile and link commands. The Spack recipe requires `+wrapper` for CUDA unless another supported launch method is used. [17, 18]

The `amdclang-craympich` lane has a different limit: ROCm 6.x cannot register as a Spack Fortran provider (§6.2), so the lane supports C/C++ only.

HIP is the AMD GPU programming interface inside ROCm, not a separate replacement for ROCm. It matters when a package builds AMD GPU kernels directly or enables a ROCm backend that uses HIP underneath. In this report, Kokkos `+rocm` is the practical example: user code may be written to the Kokkos abstraction, but the ROCm/HIP compiler and runtime path still handles the AMD GPU backend.

The general-purpose compilers, GCC, CCE, AOCC, and Intel, completed the smoke set without a recipe-level rejection. Intel still needs a registered GCC for its runtime (§5.1).

**Recommendation.** Start with GCC+CUDA for broad CUDA package coverage and use NVHPC when an application needs CUDA Fortran, `attributes(device)`, or OpenACC. On AMD systems, start with GCC+ROCm and use AMDClang when a test needs HIP single-source compilation or OpenMP target offload. This remains a working assumption until we test more GPU packages and compiler combinations.

### 4.5 The tested NVHPC lane needs a GCC path for CMake
[Verified, NVHPC-specific operational requirement]

The tested NVHPC lane needs CMake built with GCC. The Spack CMake recipe rejects `+ownlibs %nvhpc`, and the `~ownlibs` dependency graph was not viable under this lane's constraints. [16]

This does not force a particular lane order. Spack supports package-specific compiler requirements, so CMake can use GCC while the root packages use NVHPC. [3] In these specs, CMake is a build dependency and is not linked into the installed application.

Two implementations are valid:

- Register GCC in the same environment and require CMake to build with GCC while the root packages use NVHPC.
- Reuse a compatible GCC-built CMake and its dependencies from the shared buildcache.

The Raider `nvhpc-nvompi` lane reused CMake from the buildcache. A prior GCC lane is needed only for that implementation. Registering both compilers in the same environment removes the ordering dependency.

## 5. Spack 1.x Lessons That Apply Across Systems
These findings surfaced during the Raider and Blueback work, but they are not specific to either system.

### 5.1 A %oneapi environment needs a registered GCC
[Verified, General]

In the tested Spack 1.x configuration, even a small spec such as `zlib %oneapi@2023.2.0` fails to concretize when no GCC is registered. The errors do not mention GCC or the runtime dependency:

```text
internal_error("If a root can provide a virtual, it must be the provider")
internal_error("something depends_on a non-node")
```

`spack compiler list` still shows the Intel compiler correctly, which makes the missing dependency easy to overlook.

The cause is in the `intel-oneapi-runtime` recipe. It declares a link dependency on `gcc-runtime`. [19] Without a registered GCC, the `gcc-runtime` virtual has no provider, and the solver reaches the `depends_on a non-node` error.

**What works.** Register GCC as a Spack compiler before concretizing the environment. A GCC external in `packages.yaml` is the preferred method, although any valid GCC registration satisfies the runtime dependency.

The other vendor-compiler lanes did not show the same missing runtime-provider problem. When `depends_on a non-node` appears in a `%oneapi` environment and `spack compiler list` contains no GCC, the first check should be whether a GCC provider is registered.

### 5.2 The package name and compiler name can differ
[Verified, General]

Spack uses one name to register a compiler package and may use another name to select that compiler on a spec. In `packages.yaml`, the external block uses the package name. Compiler stamps and `require:` or `prefer:` rules use the compiler name.

The ROCm documentation shows this directly: the external package is `llvm-amdgpu`, while compiler selection uses `%rocmcc`. [20] The oneAPI documentation makes the same distinction between the `intel-oneapi-compilers` package and the `%oneapi` or `%intel` compiler names. [27]

| External package | Compiler virtual (`%` stamp) |
|---|---|
| `llvm-amdgpu` | `rocmcc` |
| `intel-oneapi-compilers` | `oneapi` (or `intel`) |
| `aocc` | `aocc` |
| `nvhpc` | `nvhpc` |
| `gcc` | `gcc` |
| `cce` | `cce` |

If a rule uses `%llvm-amdgpu@6.3.0` where Spack expects `%rocmcc@6.3.0`, Spack does not report a parse error or warning. The compiler preference simply does not take effect, and the spec may concretize with another compiler. We saw this pattern during both the AMDClang and Intel lane work.

**How to check it.** Run `spack -e <env> spec -I <spec>` and inspect the compiler stamps on the root and key dependencies. If a `prefer:` or `require:` rule uses `%llvm-amdgpu` and Spack chooses another compiler, change the rule to `%rocmcc`.

This is easy to miss because `extra_attributes.compilers` in the external package block contains the C, C++, and Fortran executable paths. That makes the package name look like the compiler's selectable name. In Spack, registration uses the package name and spec selection uses the compiler name.

### 5.3 External specs must describe the installed variant set
[Verified, General]

When a package is `buildable: false`, Spack can use only the declared external. The external's `spec:` line must therefore describe the installed version and relevant features accurately. Spack recommends defining external specs clearly because it may guess omitted details incorrectly. [3]

The useful error phrase is `no externals satisfy`:

```text
Cannot build curl, since it is configured 'buildable:false' and no externals satisfy the request
```

This does not mean the external is missing. It means the declared external does not satisfy the requested constraints.

On Blueback, a bare `curl@8.14.1` external did not describe the features in the installed curl. The system binary reported nghttp2, libidn2, and OpenSSL support. Once the external spec recorded those features, the constraint matched. In the tested Spack recipe, the defaults are `+nghttp2`, `~libidn2`, and `tls=openssl`. The `+libidn2` setting describes the operating system's curl build; it is not a Spack default. [21]

**What works.** Read the recipe with `spack info <pkg>` or inspect `package.py`. Then check the installed binary with `<binary> --version` and the operating system package manager. Declare the features that are actually installed. Do not add a variant only to satisfy the solver, because an inaccurate declaration can move the failure from concretization to link time or runtime.

This lesson applies to any external package. As the broader CSE package graph grows, externals such as Perl, Python, libxml2, and SQLite need the same review.

## 6. Checks and Known Limits

### 6.1 spack verify libraries is useful, but not a deployment gate
[Verified, General, sharper on Cray]

`spack verify libraries` checks whether shared-library dependencies can be found through recorded RPATHs. Spack documents it as a way to find accidental system dependencies. [23] The command is useful, but its warnings do not map directly to a failed deployment on these systems.

Spack intentionally avoids adding `/usr/lib` to RPATHs for externals installed under `/usr`. [22] A binary can therefore produce a warning even when the system dynamic loader finds the library through its normal search path. On Cray, trusted CPE libraries under `/opt/cray/pe` create the same situation.

The verifier includes a built-in `ALLOW_UNRESOLVED` list for libraries expected in default loader paths. [24] It covers groups such as:

- glibc and the loader: `ld-linux*`, `libc`, `libm`, `libpthread`, `libdl`, `libnsl`, `libresolv`, `librt`, `libutil`, `libthread_db`, and `libnss_*`;
- the GCC runtime: `libgcc_s`, `libstdc++`, `libgomp`, `libgfortran`, `libquadmath`, and the sanitizers;
- the NVIDIA driver stub, `libcuda.so.*`;
- the `intel-oneapi-runtime` loader.

That built-in list is why glibc does not appear in the warnings. The remaining noise comes from Cray PE libraries such as libpmi, libfabric, libxpmem, libpals, `libsci_*`, and `libmpi_*`, along with trusted `/usr` externals such as libcurl, libssl, libcrypto, and libncurses.

The allowlist is implemented in Spack source. Package recipes can declare `unresolved_libraries`, but the documented verifier interface does not provide a site-level list. [23, 24]

**How we check deployments.** We use three complementary checks:

- `ldd <binary>` must resolve every required library.
- `<tool> --version` must confirm that the executable loads and starts.
- `spack verify manifest --all` must confirm file integrity against Spack's installation manifest. This check stays clean across all lanes. [23]

We retain `spack verify libraries` as a drift check. A new warning on a previously stable spec is still useful even when the known baseline contains warnings.

The longer-term proposal should be a site-configurable allowlist or equivalent verifier input, not a global expansion of `ALLOW_UNRESOLVED`. That would let a Cray site acknowledge intentional externals without weakening checks elsewhere.

### 6.2 ROCm 6.x lacks the Spack Fortran provider; ROCm 7 is the next validation target
[Verified for ROCm 6.x; Observed for GNU+ROCm on the newer ROCm 7 stack]

ROCm 6.x cannot register as a Spack Fortran provider even though `/opt/rocm-6.3.0/bin/amdflang` exists and runs. The `llvm-amdgpu` recipe declares C and C++ compiler support for all listed releases, but it declares Fortran support only for `@7.0:`. [25] Below that version, changing the external spec cannot make the package satisfy Spack's Fortran compiler virtual because the provider relationship comes from the recipe.

A `+fortran` spec under a `rocmcc` environment preference eventually reports `requires 'fortran' compiler, but no package found that provides it`. Several secondary errors appear first while the concretizer tries other compilers, so the relevant message can be buried.

**How the lane handles it.** `amdclang-craympich` contains C/C++ HDF5 specs with `~fortran` and Kokkos `+rocm +serial +apu`, which has no Fortran component. HDF5 specs that need Fortran remain in the `gcc-craympich` and `cce-craympich` lanes. We do not route Fortran to GCC inside a `rocmcc` lane because that would no longer show what the named lane actually proved (§3.1).

This finding remains true for the ROCm 6.x lanes that were part of the original matrix. It does not describe the newer Blueback stack. Blueback now has a ROCm 7 CPE stack available, and GNU-hosted ROCm builds have succeeded there. That is a useful update, but it does not by itself complete the AMD/ROCm compiler lane. The next check is `%rocmcc@7` with C, C++, Fortran, `cray-mpich`, HDF5 `+fortran`, Kokkos `+rocm`, GTL linkage, and GPU-aware MPI runtime tests.

Frontier's current notes show why the release-specific check matters: ROCm support is tied to specific CPE and Cray MPICH behavior, and GPU-aware MPI compatibility can change by release. [30] For example, the documented ROCm 6.x path is tied to Cray MPICH 9.0.1, while the newer ROCm 7.x path is tied to Cray MPICH 9.1.0.

## 7. What We Still Need to Do
The current lanes are usable and verified. The remaining items either complete the system matrix or make the process easier to maintain and repeat:

- Determine the minimum `cray-mpich` external module set on Blueback (§3.3). Separate modules required for the build from modules included only as a precaution.
- Propose a site-configurable `spack verify libraries` allowlist or equivalent input for intentional Cray PE and `/usr` externals (§6.1).
- Build `nvhpc-craympich` on Blueback to complete the six-PrgEnv matrix. This lane must separate the NVHPC SDK's bundled HPC-X OpenMPI from the selected `cray-mpich` provider.
- Attach GTL to the GPU-aware Cray lanes. Continue using `LD_PRELOAD` for existing binaries and add GTL to future builds (§3.7).
- Validate the newer ROCm 7 path on Blueback. The GNU-hosted ROCm build has succeeded, but the AMD/ROCm compiler lane still needs `%rocmcc@7`, Fortran, HDF5 `+fortran`, Kokkos `+rocm`, GTL, and GPU-aware MPI runtime coverage (§6.2).
- Build a per-lane capability matrix as the broader CSE package subset expands. Record supported languages, compiler releases, MPI providers, and accelerator backends before installation.

## 8. Appendix A: Per-Lane Environment Detail
This appendix records the compiler, MPI source, external package classes, and Spack-built specs for each lane marked **Passed**. The external lists are grouped by class instead of repeating every transitive system library.

The following external classes are used below:

- **Patched system libraries (`buildable: false`):** OpenSSL and curl remain under operating system package management at `/usr` and receive security updates through DNF.
- **System hint externals (`buildable: true`):** glibc, Perl, Python, and ncurses. Spack may build another version when a consumer requires it.
- **Site MPI and network:** The system MPI stack and its required runtime modules, including the Cray PE module set described in §3.3.
- **Site compiler externals:** PrgEnv compilers on Cray, AOCC and NVHPC vendor modules, and the site GCC needed by the Intel runtime.

### A.1 Raider

#### gcc-sitempi
**Compiler:** external GCC 8 (`/usr`)
**MPI:** external OpenMPI (site module)
**Accelerator:** NVIDIA CUDA
**External classes:** patched system libraries; system hints; site OpenMPI

**Spack-built specs**

```text
hdf5@1.14.4-3 +mpi +fortran +cxx +hl ^openmpi
hdf5@1.14.4-3 ~mpi +fortran +cxx +hl
kokkos@4.7.01 +openmp +serial +cuda cuda_arch=80 +wrapper
```

#### gcc-openmpi
**Compiler:** Spack-built GCC 15.2
**MPI:** Spack-built OpenMPI 5.0.8 (`fabrics=ucx,ofi`)
**External classes:** patched system libraries; system hints

**Spack-built specs**

```text
openmpi@5.0.8 fabrics=ucx,ofi ~lustre ~rsh
hdf5@1.14.4-3 +mpi +fortran +cxx +hl ^openmpi
hdf5@1.14.4-3 ~mpi +fortran +cxx +hl
```

#### gcc-mpich
**Compiler:** external GCC 8
**MPI:** Spack-built MPICH 4.2.2 (`device=ch4 netmod=ucx pmi=pmix ~hydra +slurm ^pmix@4`)
**External classes:** patched system libraries; system hints; UCX, Slurm, and PMIx

See §4.1 for the PMIx version requirement.

**Spack-built specs**

```text
mpich@4.2.2 device=ch4 netmod=ucx pmi=pmix ~hydra +slurm ^pmix@4
hdf5@1.14.4-3 +mpi +fortran +cxx +hl ^mpich@4.2.2
hdf5@1.14.4-3 ~mpi +fortran +cxx +hl
```

#### aocc-sitempi
**Compiler:** external AOCC
**MPI:** external OpenMPI (site module)
**External classes:** patched system libraries; system hints; site OpenMPI; AOCC

**Spack-built specs**

```text
hdf5@1.14.4-3 +mpi +fortran +cxx +hl ^openmpi
hdf5@1.14.4-3 ~mpi +fortran +cxx +hl
```

#### aocc-openmpi
**Compiler:** external AOCC
**MPI:** Spack-built OpenMPI 5.0.8
**External classes:** patched system libraries; system hints; AOCC

**Spack-built specs**

```text
openmpi@5.0.8 fabrics=ucx,ofi ~lustre ~rsh
hdf5@1.14.4-3 +mpi +fortran +cxx +hl ^openmpi
hdf5@1.14.4-3 ~mpi +fortran +cxx +hl
```

#### nvhpc-nvompi (Wave B.9, first GPU lane)
**Compiler:** NVHPC SDK 25.11
**MPI:** HPC-X OpenMPI bundled in the SDK
**Accelerator:** NVIDIA CUDA 12.9 bundled in the SDK
**External classes:** patched system libraries; system hints; bundled OpenMPI, NVHPC, and CUDA
**CMake implementation used in this run:** reused from the `gcc-openmpi` buildcache; alternatively, CMake can be assigned to GCC within the same environment (§4.5)

**Spack-built specs**

```text
hdf5@1.14.4-3 +mpi +fortran ~cxx +hl ^openmpi
hdf5@1.14.4-3 ~mpi +fortran ~cxx +hl
kokkos@4.7.01 +openmp +serial +cuda cuda_arch=80 +wrapper
```

The HDF5 builds use `~cxx` because of the NVHPC `_Float16` issue described in §4.4.

### A.2 Blueback
All five Blueback lanes follow the same basic pattern. One PrgEnv is loaded, its compiler is declared as a `buildable: false` external, and `cray-mpich` carries the full Cray PE module set with a supported compiler-family stamp. Cray PE and `/usr` libraries are declared as external hints. Unless noted otherwise, each lane includes MPI and serial HDF5 builds plus `kokkos@4.7.01 +openmp +serial`.

#### cce-craympich
**Compiler:** CCE via PrgEnv-cray, declared as a `buildable: false` external
**MPI:** external `cray-mpich` at `ofi/cray/<v>/`
**Validation:** standard smoke set

The compiler external includes the PrgEnv-cray umbrella module. The MPI external includes the full Cray PE module set.

#### gcc-craympich
**Compiler:** GCC via PrgEnv-gnu, declared as a `buildable: false` external
**MPI:** external `cray-mpich` at `ofi/gnu/<v>/`
**Accelerator:** AMD MI300A via the ROCm module

This lane provided the first validation of PrgEnv-gnu GCC as a Spack external (§3.2).

Spack-built specs include the standard smoke set plus `kokkos@4.7.01 +rocm +serial +apu amdgpu_target=gfx942`. Kokkos documents Serial as a CPU execution space, HIP as the AMD GPU backend, and GFX942 APU as the MI300A target; the Spack recipe exposes the corresponding `apu` option. [18, 26] The lane currently contains both CPU and GPU Kokkos module files; that naming collision will be removed when the GPU build moves to a dedicated lane.

#### aocc-craympich
**Compiler:** AOCC via PrgEnv-aocc, declared as an external
**MPI:** external `cray-mpich` at `ofi/aocc/<v>/`
**Validation:** standard smoke set

#### intel-craympich
**Compiler:** oneAPI via PrgEnv-intel, plus a system GCC external for `gcc-runtime`
**MPI:** external `cray-mpich` at `ofi/intel/<v>/`
**Validation:** standard smoke set

See §5.1 for the GCC runtime requirement.

#### amdclang-craympich
**Compiler:** AMDClang via PrgEnv-amd, declared as an `llvm-amdgpu` external
**MPI:** external `cray-mpich` at `ofi/amd/<v>/`
**Accelerator:** AMD MI300A

The compiler virtual is `rocmcc` (§5.2). This lane is limited to C/C++ because ROCm 6.x does not provide the Spack Fortran compiler virtual (§6.2).

**Spack-built specs**

```text
hdf5 +mpi ~fortran +cxx +hl ^cray-mpich
hdf5 ~mpi ~fortran +cxx +hl
kokkos@4.7.01 +rocm +serial +apu amdgpu_target=gfx942
```

#### nvhpc-craympich (deferred)
This lane is not yet built. It must separate the NVHPC SDK's bundled HPC-X OpenMPI from the selected `cray-mpich` provider. Completing it will close the six-PrgEnv Cray matrix.

## 9. How to Read This Document
Each finding begins with a status tag: Verified, Observed, Working assumption, or Time-bounded. Scope tags show whether a finding is General, Cray-specific, or ROCm-specific.

Labels such as **What works**, **How we configure it**, and **What we will do** separate the observed behavior from the practical response.

External citations support upstream behavior, package constraints, and system architecture. Uncited build results and error signatures come from this work. Commands and one-time implementation steps remain in the operational tooling rather than this document.

## 10. References

1. Spack Project. [Spack v1.0.0 release notes: compiler dependencies](https://github.com/spack/spack/releases/tag/v1.0.0).
2. HPE Cray Programming Environment. [Spack User documentation](https://cpe.ext.hpe.com/docs/latest/craype/spack.html).
3. Spack Project. [Package Settings (`packages.yaml`), Spack v1.2.0 docs](https://spack.readthedocs.io/en/v1.2.0/packages_yaml.html).
4. Intel. [Intel Fortran Compiler `.mod` Files Version Compatibility](https://community.intel.com/t5/Blogs/Tech-Innovation/Tools/Intel-Fortran-Compiler-Module-mod-Files-Version-Compatibility/post/1600674).
5. Open MPI Project. [OpenFabrics Interfaces / Libfabric support, Open MPI 5.0.x](https://docs.open-mpi.org/en/v5.0.x/tuning-apps/networking/ofi.html).
6. Open MPI Project. [Shared Memory, Open MPI 5.0.x](https://docs.open-mpi.org/en/v5.0.x/tuning-apps/networking/shared-memory.html).
7. Shehata, A., Naughton, T., Bernholdt, D. E., and Pritchard, H. [Bringing HPE Slingshot 11 Support to Open MPI](https://www.osti.gov/servlets/purl/2438730).
8. OpenFabrics Interfaces Working Group. [Libfabric LNX provider documentation](https://ofiwg.github.io/libfabric/v2.3.1/man/fi_lnx.7.html).
9. HPE Cray Programming Environment. [Cray MPICH `intro_mpi`: Slingshot 11 and GPU support](https://cpe.ext.hpe.com/docs/latest/mpt/mpich/intro_mpi.html).
10. Open MPI Project. [Launching with HPE PALS](https://docs.open-mpi.org/en/main/launching-apps/pals.html).
11. NERSC. [Cray MPICH: CUDA-aware MPI and GTL linkage](https://docs.nersc.gov/development/programming-models/mpi/cray-mpich/).
12. ARCHER2. [GPU development platform: loading `libmpi_gtl_hsa`](https://docs.archer2.ac.uk/user-guide/gpu/).
13. Spack Project. [MPICH package recipe, Spack packages v2026.06.0](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/mpich/package.py).
14. Spack Project. [Build Caches, Spack v1.2.0 docs](https://spack.readthedocs.io/en/v1.2.0/binary_caches.html).
15. Spack Project. [Concretizer reuse settings, Spack v1.2.0 docs](https://spack.readthedocs.io/en/v1.2.0/build_settings.html#reuse-already-installed-packages).
16. Spack Project. [CMake package recipe, Spack packages v2026.06.0](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/cmake/package.py).
17. Kokkos Project. [Advanced Configuration and Build: `nvcc_wrapper`](https://kokkos.org/kokkos-core-wiki/get-started/advanced-configuration-and-build.html).
18. Spack Project. [Kokkos package recipe, Spack packages v2026.06.0](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/kokkos/package.py).
19. Spack Project. [Intel oneAPI runtime package recipe, Spack packages v2026.06.0](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/intel_oneapi_runtime/package.py).
20. Spack Project. [Using External GPU Support: `rocmcc` and `llvm-amdgpu`, Spack v1.2.0 docs](https://spack.readthedocs.io/en/v1.2.0/gpu_configuration.html).
21. Spack Project. [curl package recipe, Spack packages v2026.06.0](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/curl/package.py).
22. Spack Project. [Getting Started: system externals and `/usr/lib` RPATH handling, Spack v1.2.0 docs](https://spack.readthedocs.io/en/v1.2.0/getting_started.html).
23. Spack Project. [Auditing Packages and Configuration: `spack verify`, Spack v1.2.0 docs](https://spack.readthedocs.io/en/v1.2.0/advanced_topics.html#auditing-packages-and-configuration).
24. Spack Project. [`spack.verify_libraries` source and `ALLOW_UNRESOLVED`, Spack v1.2.0 docs](https://spack.readthedocs.io/en/v1.2.0/_modules/spack/verify_libraries.html).
25. Spack Project. [`llvm-amdgpu` package recipe and Fortran provider gate, Spack packages v2026.06.0](https://github.com/spack/spack-packages/blob/v2026.06.0/repos/spack_repo/builtin/packages/llvm_amdgpu/package.py).
26. Kokkos Project. [Configuration Guide: Serial, HIP, and MI300A GFX942 APU](https://kokkos.org/kokkos-core-wiki/get-started/configuration-guide.html).
27. Spack Project. [Intel oneAPI package documentation, Spack v1.2.0 docs](https://spack.readthedocs.io/en/v1.2.0/build_systems/inteloneapipackage.html).
28. MPI Forum. [MPI 4.1 Fortran support methods](https://www.mpi-forum.org/docs/mpi-4.1/mpi41-report/node465.htm).
29. MPI Forum. [MPI 4.1 Fortran interface specifications and binary compatibility](https://www.mpi-forum.org/docs/mpi-4.1/mpi41-report/node469.htm).
30. OLCF. [Frontier User Guide: GPU-aware MPI, ROCm, and PrgEnv-amd notes](https://docs.olcf.ornl.gov/systems/frontier_user_guide.html).
31. Spack Project. [Spack packages v2026.06.0 release notes](https://github.com/spack/spack-packages/releases/tag/v2026.06.0).
32. Spack Project. [Spack v1.2.0 release notes](https://github.com/spack/spack/releases/tag/v1.2.0).
33. HPE Cray MPI 9.0.1. Local release notes excerpt showing supported compiler minimums, including GNU 11.2 or later.
34. HPE Cray MPI 9.1.0. Local release notes excerpt showing supported compiler minimums, including GNU 12.3 or later.
35. OFI Working Group. [fabric(7): ABI changes and compatibility](https://manpages.debian.org/testing/libfabric-dev/fabric.7.en.html). Documents the versioned-ABI approach: few directly exported symbols, provider function pointers behind static inline calls, and structure extension by appended fields.
36. OFI Working Group. [libfabric 2.0 release discussion](https://github.com/ofiwg/libfabric/discussions/8049). States 2.0 as a minor ABI revision intended as a drop-in replacement for existing 1.x binaries, with breaking API changes.
