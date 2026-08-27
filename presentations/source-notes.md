# Source Notes: Design-History Narrative for the CSE Spack Stack

Narrative goal: trace how the CSE software stack project (HPC Spack-based
stacks with compiler/MPI/GPU "lanes", clean module/view exposure) converged
on its design, drawing on Spack community talks and other HPC centers'
production stacks.

---

## Document 1: "Spack: Common Stacks Update" (Kitware / Spack project)

**Who/where:** Ryan Krattiger, Software Solutions Engineer at Kitware Inc.,
Spack TSC member (works on CI/Build Cache/Environments/Packaging).
**Spack User Group Meeting, 19 March 2026**, co-located with HPSF Conference
2026 (Chicago, IL). Spack-project-level talk about the mechanics/community
convergence around "common stacks" as a Spack feature, motivated by
Kitware's own build-farm pain (ParaView, PyTorch, LLVM, GPU-enabled libs
rebuilt repeatedly across many separate stacks).

**What it describes:** Evolution of Spack's own environment/build-cache
machinery to support shared, layered "stacks" as build-farm infrastructure
feeding CI/release caches - the underlying Spack capability other sites
(NASA, ALCF, etc.) build their production stacks on top of.

**Architecture / layers:**
- Four community efforts "thinking about software stacks": **HPSF
  Binaries WG** (bottom-up, application binaries), **E4S** (top-down,
  "distribution" target, "large environments are very difficult to
  manage"), **ECP/PESO** (highly coupled *mostly* unified envs, limited
  size for tractable dependency reasoning), **EESSI** (Host OS ->
  Filesystem (CernVM-FS) -> Compatibility Layer (cross-distro/arch
  portability) -> Software Layer).
- Krattiger's own "Incremental Concretization" hierarchy (closest analog to
  CSE lanes): **Foundation** (Base/GCC, Build Systems, Tutorial) -> column
  of **GPU, MPI, Python Base, Toolchains** -> **Software Integrations**
  (Vis/Compute/ML) -> **Distribution** (E4S, Radiuss). Each column
  concretizes incrementally on the one before - a base-then-fan-out design.
- Talk is Spack-internal build/cache graph focused; user-facing
  modules/views are out of scope here.

**Concrete details:**
- `unify: when_possible` used minimizing E4S for HDF5; "version pinning is
  not enough" - many packaging bugs surfaced anyway.
- Large-environment "dark art": version pinning, incremental
  concretization, **environment chaining** (Build Cache reuse, Include
  Concrete/Environment, `reuse: from: type: environment, path: EnvA`) mostly
  landed in Spack v1.0.
- A "stack" generates one child CI pipeline, is a list of specs, may only
  push to one cache ("buildcache-destination"); the cache holds only what
  its stack built.
- Dependency Holes: layered caches (ML/GPU/Build Systems/Foundation) need
  lower-layer packages resolvable without rebuild - solved via
  location-independent metadata, cache redirection (`deps.json` -> base
  cache URL), and new **Index Views** (multiple indices per cache, built
  from environment specs, appended to existing index).
- Scale: ~2000 specs across GPU-variant envs (`ml-linux-x86_64-cpu/cuda/
  rocm`) merged to ~800 in a combined group; top-10 build-time packages
  included llvm, root, py-torch, paraview, trilinos (up to ~200 hrs/week);
  `composable-kernel` was priciest per-build (~$6 vs <$1.50 others).
- Roadmap: v1.0 (2025) Include Concrete/Compiler Nodes/Content-Addressed
  tarballs; v1.1–v1.2 (2026) Hierarchy of Stacks, Push with Lease, Index
  Views, Spec Groups; future work targets win64/aarch64/darwin, "Expand
  dimensions of Base," "Create Distribution Views."

**Key quotes:**
1. "Reindex timing out… Stacks -> copy -> >32TB" (p. 8) - the original
   pain point driving the redesign.
2. "unify: when_possible / Version Pinning is not enough! / Many packaging
   bugs" (p. 19).
3. "Stack: Used to generate a single child pipeline… Stacks may only push
   to one cache ('Buildcache-destination') / Build Cache: Only contains
   what is built by the associated stack" (p. 27).
4. "Where can we optimize? What are people actually using? ... Increase
   release cadence means we have more release caches…and more copies"
   (p. 9).

---

## Document 2: "Mixing and Matching and Multiple Versions, Oh My!" (NASA JSC)

**Who/where:** Brad Richardson (presenter), Darby Vicker, and Shahzeb Siddiqui,
**Flight Sciences Laboratory, NASA Johnson Space Center**. HPSF
Conference / Spack Project Meeting, 19 March 2026. Siddiqui is credited as
a former primary maintainer of **E4S**, bringing that expertise into FSL's
design - an explicit E4S -> NASA lineage link.

**What it describes:** NASA JSC FSL's production Spack deployment
replacing "RPM installations + manual builds" (gcc 4.8, HDF5 1.10, custom
RPMs; "a major system upgrade meant rebuilding everything"). The most
directly analogous prior art: a real production, module-facing,
multi-compiler/multi-MPI HPC stack.

**Architecture / layers:**
- User exposure: **Lmod hierarchical modules**, `Core -> Compiler -> MPI`.
  `module load gcc/12.3.0` -> `module load openmpi/4.1.6` -> `module load
  hdf5/1.14.3`; loading a compiler updates available MPIs, loading an MPI
  updates available libs/apps. **Users never run a spack command**
  ("clean separation of concerns" - Spack + Lmod). Clearest "modules as
  user contract, Spack hidden" statement across all documents.
- Multi-Environment Strategy - six ordered environments, each reusing the
  prior: **(1) compilers** (gcc/oneAPI/NVHPC/LLVM, 9–12 versions each) ->
  **(2) base** (~60 single-build pkgs: cmake, git, pandoc) -> **(3) mpis**
  (OpenMPI/MPICH/MPT, built per compiler) -> **(4) hpc-libs** (HDF5,
  NetCDF, every compiler×MPI combo) -> **(5) hpc-apps** (FUN3D, Pegasus,
  OSU-MB, every compiler×MPI) -> **(6) 32bit** (32-bit Boost/HDF5, etc.).
  This ordered fan-out is functionally the same "lanes" idea as CSE, with
  an extra 32-bit compatibility lane.
- Scale: 4 compiler suites × 9–12 versions each, 3 MPIs, ~20 packages built
  for nearly every compiler×MPI combo. Over **270 root specs -> 1,000+**
  installed packages.

**Concrete details:**
- Concretizer settings: `reuse: true` (reuse from prior envs, no
  `upstreams:` needed), `compiler_mixing: false` (blocks building a
  dependency with a different compiler than its parent), `%%`
  (double-percent) toolchain propagation (whole dependency tree prefers
  same compiler toolchain) - the direct mechanism enforcing one
  lane/compiler+MPI with no cross-contamination.
- Failure modes: concretizer refused `openmpi` due to a stale
  `legacylaunchers` variant no longer valid for OpenMPI 5+ (one-line fix);
  Boost wouldn't compile with Intel/oneAPI, patched and **upstreamed into
  the Spack packages repo**; 270+ root specs in one environment was
  "impractical," concretizer hung (GH issue #51180) - fixed by splitting
  into the six environments above.
- Build economics: full from-scratch build 12+ hours; failure at hour 11
  meant "try again tomorrow" pre-buildcache; buildcache cut rebuilds to
  2–3 hours.
- Compiler bootstrapping is a hard constraint: compilers install first as
  a fully separate step/environment, historically via `spack compiler
  find` registration before later environments can use them.
- CI validates three modes: Incremental Build, Full Rebuild, Production
  Install.
- Config layout: `setup-env.sh`, `build.sh`, `spack-configs/fsl-25.08/`
  with per-layer `*.tmpl.yaml` (32bit/base/compilers/hpc-apps/hpc-libs/
  mpis/shared/source) plus concretizer.yaml, definitions.yaml,
  externals/system.yaml, repos.yaml, toolchains.yaml - sed-templated for
  `$SYSTEM`, `$DEPLOY_DATE`, etc. Close kin to CSE's per-lane YAML files.

**Key quotes:**
1. "Users see modules, not spack. ... Users never run a spack command /
   Spack + lmod = clean separation of concerns" (p. 9).
2. "Package Reuse `reuse: true` ... No Compiler Mixing
   `compiler_mixing: false` ... Toolchain Propagation `%%` ... ensures a
   package's entire dependency tree prefers the same compiler toolchain"
   (p. 17).
3. "Putting all 270+ root specs into one environment: impractical /
   Concretizer slows to a crawl… or hangs entirely / Solution: break into
   multiple focused environments" (p. 14).
4. "1,000+ packages · 4 compiler suites · 3 MPI implementations / All
   accessible. All compatible. No spack knowledge required." (p. 20).

---

## Document 3: "CSE Spack Editable Build Flows" (project's own diagram deck)

**Who/where:** Two-slide diagram deck; `docProps` metadata lists creator
"OpenAI," created 2026-05-30 - this is the CSE project's own working
diagram (AI-assisted), not third-party prior art. Included as the "target
shape" the convergence narrative explains, quotable in the CSE project's
own vocabulary.

**What it describes:** Two parallel build-flow diagrams - **Slide 1:
"Linux System Example"** (external AOCC + common GCC + shared Core +
fan-out compiler/MPI lanes) and **Slide 2: "Cray System Example"** (Cray PE
compilers + shared Core + fan-out Cray MPICH lanes, optional Open MPI).
Same seven-stage flow both slides.

**Architecture / lanes:**
Seven stages: **(1) System inspection/inputs** (OS, CPU target, MPI/fabric
detection, scheduler) -> **(2) Register compilers** (external: AOCC+GCC on
Linux; CCE+GNU/GCC on Cray) -> **(3) Compiler foundation** -> **(4) Build
Core once** (Spack Core env, built with GCC, baseline `x86_64_v3`; CMake,
Ninja, pkgconf, Git, Miniforge, Python tools; "Shared across all compiler
and MPI lanes") -> **(5) Fan-out lanes** (parallel per-compiler/MPI envs,
each with own yaml/lock/view/mods) -> **(6) Build and validate**
(Concretize, Fetch, Install, Test/verify, Microbenchmarks, Smoke tests;
"Lanes build independently; can run in parallel") -> **(7) Publish to
users** (Regenerate views, Refresh modules, Push build caches, Promote
release).

**Lanes, concretely:**
- Linux: GCC/serial, GCC/mpi-openmpi, AOCC/serial, AOCC/mpi-openmpi, plus
  optional site MPI (external). "Linux / InfiniBand: Open MPI typically
  built with UCX."
- Cray: CCE/serial, CCE/mpi-craympich, GCC/serial, GCC/mpi-craympich, plus
  "Optional Open MPI" (secondary, libfabric/CXI, "Validate before
  production"). "Cray MPICH is the primary production MPI on Cray
  systems."
- Each lane builds HDF5/NetCDF (serial or +MPI); MPI lanes add
  PnetCDF/TAU.
- User modules named explicitly - Linux: `CSE/Core`, `CSE/GCC/serial`,
  `CSE/GCC/mpi-openmpi`, `CSE/AOCC/serial`, `CSE/AOCC/mpi-openmpi`; Cray:
  `CSE/Core`, `CSE/CCE/serial`, `CSE/CCE/mpi-craympich`, `CSE/GCC/serial`,
  `CSE/GCC/mpi-craympich`, `CSE/optional/OpenMPI`.
- Legend distinguishes "build flow" vs "reuse" edges; Core is a reuse
  target for every lane. Cray callout: "Validate PALS / mpirun on PBS and
  srun on Slurm."

**Key quotes (slide):**
1. "Shared across all compiler and MPI lanes" (Slide 1 & 2, stage 4).
2. "Core is built once, then reused / Compiler + MPI combinations stay
   isolated" (Slide 1 & 2, closing annotations).
3. "Lanes build independently; can run in parallel" (Slide 1 & 2, stage 6).
4. "Cray MPICH is the primary production MPI on Cray systems" (Slide 2) /
   "Linux / InfiniBand: Open MPI typically built with UCX" (Slide 1).

---

## Pilot test systems (HPC Centers hardware inventory)

**Source:** [HPC Centers hardware inventory](https://centers.hpc.mil/systems/hardware.html),
accessed 14 July 2026. The four systems are the first production-test matrix
for the pilot stack. They were selected to exercise materially different
platform shapes rather than four copies of the same deployment.

- **Blueback (NAVY DSRC):** HPE Cray EX4000; SLES; AMD EPYC 9654 Genoa
  standard nodes; AMD MI300A AI/ML nodes and NVIDIA L40 visualization nodes.
  Proves Cray PE discovery/rendering and a mixed AMD/NVIDIA accelerator site.
- **Fran (ARL DSRC):** HPE Cray EX4000; 173,184 AMD EPYC Genoa compute cores;
  12 NVIDIA L40S GPUs; Cray Slingshot-11. Proves a second Cray site and the
  NVIDIA path without treating Blueback-specific facts as general Cray policy.
- **Raider (AFRL DSRC):** Penguin Computing TrueHPC; RHEL; AMD EPYC 7713
  Milan standard nodes; NVIDIA A40 and A100 nodes. Proves the generic-Linux
  path against a broad site module/compiler/MPI catalog.
- **Wheat (ERDC DSRC):** Liqid composable system; RHEL 8; Intel 9242 Cascade
  Lake nodes; NVIDIA A100 GPU nodes. Proves Intel CPU and composable-node
  behavior on generic Linux.

Together the matrix covers Cray and generic Linux, AMD and Intel CPUs, and AMD
and NVIDIA accelerators. System-specific facts remain Cluster Inspector output;
the shared policy and renderer must not hard-code any of these machine names.

---

## Convergence threads

- **Base/Core built once with a portable baseline, then reused
  everywhere.** Kitware's Foundation column, NASA's `base` environment
  (`reuse: true`, no `upstreams:` needed), and CSE's "Build Core once…
  Shared across all compiler and MPI lanes" (pinned to `x86_64_v3`) are the
  same idea three ways: build cheap, compiler-agnostic tooling once, fan
  out from there.
- **One lane per compiler(+MPI) combination, deliberately isolated.**
  Kitware's per-column fan-out (compiler -> GPU/MPI/Python/Toolchains ->
  integrations), NASA's `compiler_mixing: false` + `%%` toolchain
  propagation, and CSE's "Compiler + MPI combinations stay isolated" all
  enforce the same rule: no silent cross-toolchain linking.
- **Large flat environments don't scale - break into a hierarchy.** NASA
  hit concretizer hangs at 270+ root specs in one environment (GH #51180)
  and split into six ordered environments; Kitware arrived independently at
  `unify: when_possible` + incremental concretization + environment
  chaining for the same reason; CSE's multi-stage fan-out applies this
  lesson from the start rather than discovering it under duress.
- **Users see modules/views, not the package manager.** NASA's
  Lmod-hierarchical `Core -> Compiler -> MPI` with "users never run a
  spack command" is the most explicit version; Kitware's "Distribution
  Views" future-work item and CSE's stage 7 ("Regenerate views / Refresh
  modules… Publish to users") treat the same module/view boundary as the
  deliverable, not the Spack internals. Kitware and CSE both push
  environment metadata (yaml/lock/view/mods) as per-lane artifacts,
  mirroring NASA's per-layer `*.tmpl.yaml` files.
- **Build caches make iteration survivable.** All three treat the build
  cache as load-bearing, not optional: NASA's 12-hour-vs-2–3-hour rebuild
  story, Kitware's whole talk arc (reindex timing out at >32TB, dependency
  holes, index views, cache redirection), and CSE's stage 6/7 split
  (build+validate, then "Push build caches" as its own publish step).
- **A GPU/toolchain "hole" problem recurs whenever layers are cached
  separately.** Kitware names this directly (Dependency Holes across
  ML/GPU/Build Systems/Foundation); this maps onto the tracked CSE gap list
  (compiler multi-version first-match, CPE-ROCm validation, GTL preload
  elimination) as the same class of cross-layer resolution problem.
- **Community lineage is explicit, not incidental.** NASA's deck credits
  Shahzeb Siddiqui (former E4S maintainer) for bringing E4S ideas into
  FSL's design; Kitware's talk positions E4S/EESSI/PESO/HPSF Binaries WG as
  the recognized precedent set any new "common stack" effort - including
  CSE - is implicitly answering to.
