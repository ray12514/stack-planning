# HPC Site Software Stack Survey (v1)

| Document control | |
|---|---|
| Date | 2026-07-13 |
| Status | Research note: reference material, not policy |
| Method | Official site documentation only, fetched 2026-07-13; source URLs inline. Fields a site does not publish are marked as such. |

A survey of how eleven major HPC centers build and expose user-facing scientific software stacks, structured around hierarchical module systems, meta-module gates, container activation models, and CVMFS-distributed stacks. Companion to the three references already cited in the lanes-model deck (NASA JSC Flight Sciences Lab, ALCF Polaris, Spack/E4S); the goal here is range, including models that disagree with ours.

---

## 1. NERSC (Perlmutter)

- **Site / system**: NERSC Perlmutter (NVIDIA GPU, HPE compute)
- **Build tooling**: Spack (E4S project, also discussed but detailed E4S docs at 404); no pinning approach documented at available pages
- **Module system**: Lmod (Lua-based, hierarchical)
- **Exposure model**:
  - Hierarchical dependency-based gating: `module avail` shows only modules accessible without unmet dependencies
  - Mutually exclusive compiler family (gcc, cce, aocc, nvidia), loading one compiler swaps it for another
  - `module spider` reveals full hierarchy across all dependencies
  - Default module loads baseline software on login
  - User commands: `module load`, `module unload`, `module list`, `ml` shorthand (e.g., `ml gcc` loads, `ml -gcc` unloads)
  - `contrib` module extends MODULEPATH with user-contributed software
- **Environments for users?**: Yes; Default and contrib modules gate access to community software.
- **Divergence / notable**: Compiler family exclusivity enforced by Lmod; hidden modules (prefix ".") require `--show_hidden` to view. Hierarchical discovery balances accessibility with compatibility.
- **Sources**:
  - https://docs.nersc.gov/environment/lmod/
  - https://docs.nersc.gov/applications/

---

## 2. OLCF (Frontier)

- **Site / system**: OLCF Frontier (AMD EPYC + MI250X GPU, HPE Cray PE)
- **Build tooling**: Hybrid: Cray Programming Environment (vendor-supplied, includes MPICH, Libsci, FFTW) + User-Managed Software (UMS; Spack-based, user-installed)
- **Module system**: Lmod (hierarchical)
- **Exposure model**:
  - Two-tier hierarchy:
    1. **Cray PE layer**: Load `PrgEnv-<compiler>` (cray, amd, gnu) to activate compatible compiler, MPI, scientific libraries, with automatic wrappers (cc, CC, ftn) for compilation
    2. **UMS layer** (opt-in gating): `module load ums` enables UMS, then `module load ums-<PROJECT>` accesses project-specific packages
  - ROCm GPU toolchain accessed via `rocm` modules alongside PrgEnv
  - User commands: `module avail`, `module spider`, `module load`
  - Core/25.03 versioned module layer (e.g., Core/24.07 default, Core/25.03 available March 2025)
- **Environments for users?**: Yes; PrgEnv combinations and UMS projects (currently E4S, AMD AFAR LLVM, UPC++, others). Core versioning provides coherent environment sets.
- **Divergence / notable**: Clear separation of vendor-managed (Cray PE) and user-managed (UMS) stacks. UMS projects must self-support their users; OLCF does not provide support.
- **Sources**:
  - https://docs.olcf.ornl.gov/software/index.html
  - https://docs.olcf.ornl.gov/systems/frontier_user_guide.html
  - https://docs.olcf.ornl.gov/software/UMS/index.html

---

## 3. LLNL Livermore Computing

- **Site / system**: LC clusters (TOSS-based systems)
- **Build tooling**: TOSS (Tri-Lab OS Stack; RedHat-based commodity OS) + TCE (Tri-Laboratory Computer Environment; development layer atop TOSS)
- **Module system**: Lmod (modules for compilers, debuggers, MPI, libraries)
- **Exposure model**:
  - Layered architecture: TOSS (stable OS/ABI base) and TCE (dynamic development tools, faster release cycle)
  - Users load TCE modules for compilers, debuggers, MPI, and other development tools
  - Spack user-driven builds supported for custom environments
  - Module-based discovery and loading (not hierarchical details documented)
- **Environments for users?**: No public hierarchical exposure model documented; users work within TCE-provided development environment.
- **Divergence / notable**: Deliberate separation of stable infrastructure (TOSS) from fast-moving tools (TCE). Less documented than other sites; module hierarchy not publicly specified.
- **Sources**:
  - https://hpc.llnl.gov/software/toss-tri-lab-operating-system-stack

---

## 4. CSCS (Alps/Daint)

- **Site / system**: CSCS Alps (one infrastructure, multiple vClusters)
- **Build tooling**: Stackinator (CSCS-developed tool for uenv configuration) + Spack (software compilation). Stackinator "currently maintained for internal use" with limited support.
- **Module system**: None (software embedded in uenv container images)
- **Exposure model**:
  - **Most divergent model**: Software delivered as self-contained squashfs images (uenv) rather than a global module tree
  - User workflow: `uenv image find` (search) → `uenv image pull` (download) → `uenv start <name>` or `uenv run` (activate for interactive or command execution)
  - Example: `uenv start namd/3.0:v1` activates a NAMD environment
  - No MODULEPATH or module hierarchy; entire environment is containerized
- **Environments for users?**: Yes, but as discrete domain-specific container images (NAMD, etc.), not as module selections within a hierarchy
- **Divergence / notable**: Containerized environments replace hierarchical module selection. No global software tree; each uenv is self-contained and versioned. Fundamental departure from module-based stacks.
- **Sources**:
  - https://docs.cscs.ch/software/uenv/
  - https://docs.cscs.ch/software/uenv/build/

---

## 5. LUMI (CSC/EuroHPC)

- **Site / system**: LUMI (AMD EPYC + MI250X GPU, HPE Cray PE)
- **Build tooling**: EasyBuild (primary central stack) with Cray-specific toolchains (cpeGNU, cpeCray, cpeAOCC, cpeAMD); users can also build custom software via EasyBuild in home/project directories
- **Module system**: Lmod (hierarchical, using HPE Cray's Lmod implementation; `module spider` output noted as incomplete due to non-standard Cray integration)
- **Exposure model**:
  - Load LUMI stack version: `module load LUMI/24.03` (version formats: year.month)
  - System auto-detects node type; users can override manually
  - Within a LUMI version, modules named by toolchain:
    - `*cpeGNU-yy.mm*`: GNU environment
    - `*cpeCray-yy.mm*`: Cray compilers
    - `*cpeAOCC-yy.mm*`: AMD CPU-only
    - `*cpeAMD-yy.mm*`: AMD ROCm (GPU)
  - Sticky modules protect stack activation (prevent accidental deactivation)
  - Four stacks available: CrayEnv (Cray PE + tools), LUMI (extensible via EasyBuild), spack (for experienced users), Local-* (partner-provided)
- **Environments for users?**: Yes, LUMI version selection provides environment families; CrayEnv and spack stacks are alternatives
- **Divergence / notable**: Compact central stack by design; users extend via EasyBuild in personal directories. Distributed model avoids bottlenecks during system maintenance. Cray PE integration requires custom Lmod configuration.
- **Sources**:
  - https://docs.lumi-supercomputer.eu/runjobs/lumi_env/softwarestacks/
  - https://docs.lumi-supercomputer.eu/software/installing/easybuild/
  - https://docs.lumi-supercomputer.eu/runjobs/lumi_env/Lmod_modules/

---

## 6. TACC (Frontera / Stampede3)

- **Site / system**: TACC Frontera (Intel Xeon), Stampede3 (Intel CPUs and GPUs)
- **Build tooling**: Local tooling (TACC maintains and develops Lmod module system itself)
- **Module system**: Lmod (hierarchical, with automatic dependency resolution and swapping)
- **Exposure model**:
  - Hierarchical with automatic compatibility management: loading a compiler can auto-replace incompatible dependent libraries
  - Standard TACC naming convention: module defines `TACC_<PKG>_BIN`, `TACC_<PKG>_LIB`, `TACC_<PKG>_INC`, `TACC_<PKG>_DIR` environment variables
  - User commands: `module load`, `module avail` (compatible), `module spider` (full hierarchy), `module save/restore` (named collections)
  - Note: "it's safe to execute module commands in job scripts" for reproducible workflows
- **Environments for users?**: Yes; compiler selection and the resulting auto-compatible library stack form implicit environments.
- **Divergence / notable**: TACC is the home site and primary maintainer of Lmod; their own systems demonstrate Lmod design philosophy. Automatic swapping and family enforcement central to user experience.
- **Sources**:
  - https://docs.tacc.utexas.edu/hpc/frontera/

---

## 7. NOAA/JCSDA spack-stack

- **Site / system**: Multi-platform (HPC centers, cloud, personal computers); supports NOAA UFS, JEDI, MPAS, NEPTUNE, UM, GEOS
- **Build tooling**: Spack (with spack-stack configuration layer; "mainly a collection of Spack configuration files")
- **Module system**: Lmod/lua and TCL modules (auto-generated by `spack stack setup-meta-modules`)
- **Exposure model**:
  - Meta-module gating: `spack stack setup-meta-modules` creates compiler, MPI, and Python meta-modules
  - Single-command activation: users "activate all necessary libraries for running a UFS application with just one command" (specific command not detailed)
  - Multi-compiler support (Intel and GNU MPI) on most Tier-1 machines
  - Pre-configured installations available on all UFS Tier-1 platforms and NOAA Cloud
  - Incremental expansion: users can install packages for one application, later add packages for another without full stack rebuild
- **Environments for users?**: Yes; compiler/MPI/Python meta-module combinations provide environment families
- **Divergence / notable**: Designed as multi-agency operational stack for weather/earth prediction. Emphasis on reproducibility across platforms (HPC, cloud, laptop). Meta-modules as primary access gate (not hierarchical).
- **Sources**:
  - https://epic.noaa.gov/spack-stack/
  - https://spack-stack.readthedocs.io/en/1.8.0/Overview.html

---

## 8. Pawsey (Setonix)

- **Site / system**: Pawsey Supercomputing Research Centre, Setonix (AMD EPYC + MI250X GPU)
- **Build tooling**: Spack (upgraded from 0.21.0 to 0.23.0; 7400+ software recipes)
- **Module system**: Lmod (hierarchical)
- **Exposure model**:
  - Hierarchical module organization by compiler and version
  - Pre-upgrade modules accessed by adding the reviewed Setonix module root and
    its `zen3/gcc/11.2.0` subtree to `MODULEPATH`
  - Version pinning via subdirectory structure (zen3/gcc/11.2.0, etc.)
  - Migrating from in-house Maali package manager to Spack for "more efficient scientific software management"
- **Environments for users?**: Not explicitly documented; compiler/version-specific paths serve as implicit environments.
- **Divergence / notable**: Hierarchical module exposure by hardware and compiler. Transitioning from home-grown to community tooling (Spack). Module path structure encodes compiler and version hierarchies.
- **Sources**:
  - https://pawsey.org.au/more-efficient-scientific-software-management-for-setonix/
  - https://support.pawsey.org.au/documentation/display/US/Spack (redirects; not fetched)

---

## 9. Jülich JSC (JUWELS)

- **Site / system**: Jülich Supercomputing Centre (Forschungszentrum Jülich), JUWELS (Intel Xeon + NVIDIA GPU)
- **Build tooling**: EasyBuild
- **Module system**: Lmod (hierarchical, explicit "stages")
- **Exposure model**:
  - Three-tier hierarchy with strict loading order enforced by dependency visibility:
    1. **Compiler stage**: Load desired compiler (GCC, Intel, NVHPC, AOCC, Clang)
    2. **MPI stage**: After compiler loads, compatible MPI options appear (ParaStationMPI, OpenMPI, IntelMPI)
    3. **Application stage**: Once MPI loads, applications built with that compiler-MPI combination become accessible
  - `module avail` shows only currently compatible modules
  - `module spider <name>` reveals full hierarchy and displays required load sequences
  - Command workflow: `module load <compiler>` → `module load <mpi>` → `module load <app>`
  - System automatically loads hidden dependencies
- **Environments for users?**: Yes; compiler+MPI combinations represent user environments
- **Divergence / notable**: Most explicit three-tier hierarchy documented. Module spider output shows exact load sequence needed. Prevents incompatible combinations by visibility control.
- **Sources**:
  - https://apps.fz-juelich.de/jsc/hps/juwels/software-modules.html

---

## 10. EESSI (European Environment for Scientific Software Installations)

- **Site / system**: Distributed European stack (available on HPC systems across Europe); architecture-agnostic
- **Build tooling**: EasyBuild
- **Module system**: Lmod (via CVMFS)
- **Exposure model**:
  - Initialization via source script: `source /cvmfs/software.eessi.io/versions/2023.06/init/lmod/bash` configures Lmod and loads EESSI module
  - Alternative direct bash sourcing: `source /cvmfs/software.eessi.io/versions/2023.06/init/bash`
  - Architecture detection: `eessi_archdetect.sh` automatically identifies system CPU/GPU; users can override via `EESSI_SOFTWARE_SUBDIR_OVERRIDE`, `EESSI_ACCELERATOR_TARGET_OVERRIDE`
  - CVMFS (CernVM-FS) distributes stack; data downloaded on-demand from Stratum 1 servers on first access
  - Version selection configurable via environment variables (default 2023.06, but others available)
- **Environments for users?**: Implicit via architecture detection; no explicit per-domain environments, but customizable via env vars
- **Divergence / notable**: CVMFS streaming replaces local installation. Automatic architecture detection. Distributed across many sites without central deployment. Single initialization activates all EESSI software.
- **Sources**:
  - https://www.eessi.io/docs/using_eessi/setting_up_environment/

---

## 11. Digital Research Alliance of Canada (formerly Compute Canada)

- **Site / system**: Distributed across Canadian supercomputing centers
- **Build tooling**: Three-layer stack:
  1. **Gentoo Prefix** (base compatibility layer): GNU C library, package management, dependency resolution via Gentoo "ebuilds"
  2. **EasyBuild** (applications layer): Compilers (Intel, NVHPC), MPI (OpenMPI), CUDA, MKL, scientific applications
  3. **CVMFS** (distribution layer): Deployed via caching proxies to all clusters, VMs, laptops
- **Module system**: Lmod
- **Exposure model**:
  - CVMFS mounts a consistent software stack globally (`/cvmfs/` mount point)
  - EasyBuild modules integrate with Lmod for selection
  - Users access stack in "a matter of a few minutes" after cluster access, independent of cluster-specific configuration
  - Installation workflow (internal): staff install software via EasyBuild, deploy to CVMFS, then available cluster-wide
- **Environments for users?**: Not explicitly documented; EasyBuild-managed environments implicit
- **Divergence / notable**: Gentoo Prefix enables distribution of base libraries without requiring privileged installation on each cluster. CVMFS ensures consistent stack across autonomous compute centers. Scaling innovation: single deployment reaches dozens of sites.
- **Sources**:
  - https://users.ugent.be/~kehoste/eum25/004_eum25_site_talk_Alliance.pdf
  - https://easybuild.io/eum23/eum23_008_Digital-Research-Alliance-Canada.pdf
  - https://pretalx.com/packagingcon-2021/talk/YWRVCT/

---

## Summary

The field clusters around three primary exposure models:

1. **Hierarchical Lmod (Core → Compiler → MPI)** (NERSC, OLCF Frontier, LUMI, TACC, Pawsey, Jülich JSC): Mutually exclusive compiler families, dependency-gated module visibility, and `module spider` discovery are standard. Compiler-MPI-Application tiers formalize incompatibility constraints. This is the field norm; on Cray systems it composes with the vendor PrgEnv layer.

2. **Meta-module gates and layered environments** (OLCF UMS program, NOAA spack-stack): Compiler/MPI/Python meta-modules provide environment coherence without full hierarchical visibility gating. Users opt-in to curated language/domain environments. Less common than hierarchy but gaining adoption for multi-project stacks.

3. **CVMFS distribution and architecture-automatic stacks** (EESSI, Digital Research Alliance): Software distributed via CernVM-FS and activated via initialization scripts rather than per-cluster installation. Architecture detection automates tuning. Rare but elegant for multi-site deployments.

4. **Containerized environments** (CSCS uenv): Software delivered as squashfs images activated by name rather than selection within a module tree. The most divergent documented approach in this survey.

Sites that keep their approach private or minimally documented: **LLNL (TCE)** publishes layered architecture but not the module hierarchy details. **CSCS Stackinator** is "maintained for internal use." Most other sites publish full documentation via official wikis and user guides.

---

## What this means for the lanes model

Hierarchical module exposure with compiler-family exclusivity and dependency-gated visibility is the documented field standard on major systems (NERSC, OLCF Frontier, LUMI, TACC, Pawsey, Jülich JSC). The lanes model (a compiler surface gating into mutually exclusive Serial/MPI/GPU lanes with clean package names below) sits inside that norm; the lane tier is our refinement of the standard Compiler→MPI level. The instructive divergences: OLCF's explicit opt-in gate for user-managed software (a clean pattern for multi-project stacks), CSCS's uenv container model (versioned and reproducible, at the cost of module discovery), LUMI's compact-central-stack-plus-user-EasyBuild split (pushes long-tail maintenance to users), and the CVMFS distribution models (EESSI, Digital Research Alliance) that solve a multi-site problem we do not have yet. None of these contradicts the lanes story; they mark the axes along which it could evolve.
