# CSE Spack Customization and Upstream Inventory v1

**Status:** Current implementation inventory

**Date:** 2026-08-24

**Applies to:** Initial Conversion Trials on Spack 1.2.2 with the `spack-packages` `v2026.06.0` repository pin

## 1. Purpose

This document is the authoritative inventory of the Spack-related behavior that CSE has changed, constrained, adapted, or patched across Cluster Inspector, Stack Composer, Stack Content, and Stack Planning.

The inventory separates four different kinds of work:

1. **CSE policy and configuration**: intentional choices made for the CSE stack. These are not defects in Spack.
2. **Spack integration behavior and workarounds**: controls required to make a reproducible multi-environment build work with Spack as it currently behaves.
3. **Site, provider, and compiler adapters**: handling for Cray PE, AOCC, Intel, schedulers, external MPI, and other platform facts.
4. **Package recipe overlays and patches**: local changes to `package.py` files or package sources, including their upstream disposition.

The current implementation is the source of truth. Working notes are cited only when they explain why an implemented control exists. Items that were tested but are not active are identified as historical or proposed.

## 2. Repository responsibilities

| Repository | Responsibility | Spack-related boundary |
| --- | --- | --- |
| Cluster Inspector | Collect and normalize system facts | It reports compilers, MPI providers, modules, filesystems, schedulers, and candidate build locations. It does not select deployment policy or call Spack. |
| Stack Composer | Validate inputs and render deterministic artifacts | It converts a profile plus authored policy into Spack scopes, environments, views, modules, and trial workspaces. It does not probe the host or build packages. |
| Stack Content | Store CSE policy, templates, package overlays, and provider adapters | This is where CSE's active package matrix and local Spack repository are authored. |
| Stack Planning | Record decisions, evidence, runbooks, and acceptance gates | This repository explains why the implemented controls exist and tracks what should be retired or proposed upstream. |

Primary repository rules are in [Cluster Inspector AGENTS.md](../../cluster-inspector/AGENTS.md), [Stack Composer AGENTS.md](../../stack-composer/AGENTS.md), [Stack Content AGENTS.md](../../stack-content/AGENTS.md), and [Stack Planning AGENTS.md](../AGENTS.md).

## 3. Executive summary

The current CSE implementation does not modify Spack core. It uses Spack-native configuration, an isolated package repository, rendered environments, and operational validation around Spack.

There are three active package overlays:

- `cmake`: adds the two trial versions missing from the pinned package repository.
- `cce`: records the CCE versions available on the trial systems while retaining an external-only compiler package.
- `dakota`: applies a narrow source patch that removes Dakota's obsolete compiled Boost.System linkage.

Only the Dakota change is presently a strong upstream defect candidate. The CMake versions are already present on the current `spack-packages` development branch, so that overlay is a pin-compatibility bridge. The CCE overlay is partly upstreamable version metadata and partly local platform policy. No Cray MPICH, libfabric, Open MPI, HDF5, NetCDF, Boost, Python, or Miniforge `package.py` is overlaid in the active trial repository.

The largest body of CSE-specific work is configuration and provider adaptation, not package patching. It includes exact external boundaries, compiler/MPI pairing, conservative CPU targets, grouped concretization, module projections, isolated Spack state, build-stage selection, and lockfile verification.

## 4. Active CSE policy and configuration

These settings intentionally differ from an unconstrained Spack installation. They express the CSE release model and should not be proposed upstream as global defaults.

### 4.1 Reproducibility and state isolation

| CSE control | Active implementation | Reason and default relationship |
| --- | --- | --- |
| Spack version is pinned to 1.2.2 | [trial workspace blueprint](../../stack-content/pilots/cse-pilot/blueprint.yaml), [site-values example](../../stack-content/pilots/cse-pilot/site-values.example.yaml) | Release input, not a Spack default change. The official release is [Spack v1.2.2](https://github.com/spack/spack/releases/tag/v1.2.2). |
| Package repository is pinned to `spack-packages` `v2026.06.0` | [repository template](../../stack-content/pilots/cse-pilot/templates/configs/common/repos.yaml.j2), [package repository manifest](../../stack-content/pilots/cse-pilot/templates/package-repos/spack_repo/cse_trials/repo.yaml) | Prevents package recipe drift during the trial. The official pin is [spack-packages v2026.06.0](https://github.com/spack/spack-packages/releases/tag/v2026.06.0). |
| Local CSE trial repository precedes the builtin repository | [repository template](../../stack-content/pilots/cse-pilot/templates/configs/common/repos.yaml.j2) | Makes the three reviewed overlays deterministic and visible. |
| User, site, and system Spack configuration is disabled | [workspace launcher template](../../stack-content/pilots/cse-pilot/templates/cse-build.j2), [workspace setup template](../../stack-content/pilots/cse-pilot/templates/env/setup-build-env.sh.j2) | Prevents ambient Spack configuration from silently changing a reviewed lockfile. The launcher also verifies active scopes. |
| Install tree, source cache, miscellaneous cache, and bootstrap root are release-owned paths | [config template](../../stack-content/pilots/cse-pilot/templates/configs/common/config.yaml.j2), [bootstrap template](../../stack-content/pilots/cse-pilot/templates/configs/common/bootstrap.yaml.j2), [site-values example](../../stack-content/pilots/cse-pilot/site-values.example.yaml) | Separates the trial from personal Spack state and supports handoff between CSE builders. |
| `locks: true` | [config template](../../stack-content/pilots/cse-pilot/templates/configs/common/config.yaml.j2) | Explicit concurrency safety for the shared install tree. |
| Group ownership and write permissions use the lowercase `cse` group | [package configuration template](../../stack-content/pilots/cse-pilot/templates/configs/common/packages.yaml.j2), [workspace initializer](../../stack-composer/src/stack_composer/workspace/initializer.py) | Allows the two trial operators to share lockfiles, source caches, build cache, and installs. Publication is a separate read-only consumer boundary. |
| `deprecated: true` | [config template](../../stack-content/pilots/cse-pilot/templates/configs/common/config.yaml.j2) | Narrow exception required to retain Python 3.8.20 in the approved initial matrix. It is not a general recommendation to prefer deprecated versions. |

### 4.2 Concretizer and environment model

| CSE control | Active implementation | Purpose |
| --- | --- | --- |
| `concretizer:unify: false` | [concretizer template](../../stack-content/pilots/cse-pilot/templates/configs/common/concretizer.yaml.j2) | Allows the approved public multi-version roots to coexist. |
| `concretizer:reuse: true` by default; `false` inline on the managed-GCC surface | [common concretizer template](../../stack-content/pilots/cse-pilot/templates/configs/common/concretizer.yaml.j2), [shared environment templates](../../stack-content/pilots/cse-pilot/templates/environments), [payload template](../../stack-content/pilots/cse-pilot/templates/_partials/payload-spack.yaml.j2) | Keeps existing platform-surface reuse behavior while resolving each new managed-GCC lock from current inputs instead of allowing an installed seed-compiler DAG to outrank that surface. Identical resulting hashes are still reused by the installer, shared store, and build cache. |
| Eight independent environments | [trial workspace blueprint](../../stack-content/pilots/cse-pilot/blueprint.yaml), [environment templates](../../stack-content/pilots/cse-pilot/templates/environments) | Creates Core, Common, Serial, and MPI environments for the shared GCC compiler and for the platform compiler. Independent environments do not create cross-environment `needs` relationships. |
| Groups and `needs` order producers inside each environment | [payload environment partial](../../stack-content/pilots/cse-pilot/templates/_partials/payload-spack.yaml.j2), [rendered environment reference](spack_1_2_rendered_environment_reference_v1.md) | Expresses compiler, Foundation, build-tool, MPI, and payload order using Spack 1.2 environment semantics. |
| Each compiler surface builds its own Foundation and Core roots | [trial workspace blueprint](../../stack-content/pilots/cse-pilot/blueprint.yaml), [dependency risk audit](initial_conversion_trials_dependency_risk_audit_v1.md) | Avoids an implicit cross-compiler ABI assumption. Within one compiler surface, repeated full specs are expected to produce the same hashes and be reused. |
| Shared compiler is GCC 12.5.0 built from an exact external seed compiler | [site-values example](../../stack-content/pilots/cse-pilot/site-values.example.yaml), [shared compiler template](../../stack-content/pilots/cse-pilot/templates/configs/surfaces/shared/compiler.yaml.j2) | Establishes a common compiler surface while preserving the system compiler as the bootstrap compiler. The built compiler includes C, C++, Fortran, and binutils. |
| Platform compiler is an external selected from the system profile | [build-values generator](../../stack-content/pilots/cse-pilot/scripts/create-build-values.py), [platform compiler template](../../stack-content/pilots/cse-pilot/templates/configs/surfaces/platform/compiler.yaml.j2) | Preserves the reviewed CCE, AOCC, or classic Intel compiler instead of substituting a generic compiler. |
| Every Serial and MPI lane receives an explicit toolchain | [serial lane partial](../../stack-content/pilots/cse-pilot/templates/_partials/serial-lane.j2), [MPI lane partial](../../stack-content/pilots/cse-pilot/templates/_partials/mpi-lane.j2) | Prevents the concretizer from selecting an unintended compiler or MPI provider. |
| Package-repository changes require forced replacement of the affected roots with `concretize -f --reuse-deps` | [trial runbook](runbook.md) | The normal launcher concretizes missing lockfiles with `--fresh`. After an overlay or producer-spec change, `--fresh` alone does not guarantee replacement of existing roots and hashes; use the runbook recovery procedure for the affected environments. |

Spack's documented environment and concretizer behavior remains upstream behavior; CSE's contribution is the rendered grouping and verification around it. The concurrency and environment limits are summarized in [Spack 1.2.2 build orchestration semantics research](spack_1_2_2_build_orchestration_semantics_research_v1.md).

### 4.3 Package and version policy

The complete active root roster is in [roster.yaml](../../stack-content/pilots/cse-pilot/roster.yaml). Important constraints include:

- Foundation roots are `zlib@1.3.1`, `xz@5.4.6`, and `zstd@1.5.6`.
- Build tools are CMake 3.31.12 and 4.4.2. Dependency constraints prefer CMake 3.31.12 for the initial build path.
- Core Python roots are 3.8.20, 3.10.20, and 3.12.13.
- Miniforge3 26.1.1-3 is a binary-distributed, compiler-independent root.
- BLAS and LAPACK resolve to the reviewed Netlib LAPACK roots rather than an arbitrary virtual provider.
- HDF5, NetCDF-C, NetCDF-Fortran, and NetCDF-CXX4 use explicit serial and MPI chains. Each newer NetCDF root is paired with the newer HDF5 root and each older root with the older HDF5 root.
- Dakota explicitly reuses CMake 3.31.12, Python 3.12.13, Netlib LAPACK 3.12.1, the selected MPI, and the reviewed Boost root.
- Boost roots explicitly request the compiled components required by the current dependency graph. MPI-enabled Boost is bound to Python 3.12.13.
- `xcb-proto` is also bound to Python 3.12.13 to avoid unplanned Python roots.
- `iconv` is required from glibc rather than built as a duplicate GNU libiconv root.

The corresponding package-level requirements are rendered by [packages.yaml.j2](../../stack-content/pilots/cse-pilot/templates/configs/common/packages.yaml.j2). The rationale and repository availability check are in [initial conversion trials package version check](initial_conversion_trials_package_version_check_v1.md).

### 4.4 CPU target policy

Source-built packages use the highest reviewed portable x86-64 baseline supported across the target system, capped at `x86_64_v3`. The binary Miniforge distribution is the reviewed `x86_64` exception because its available artifact is not rebuilt by CSE.

Implementation and enforcement are in [build-values generation](../../stack-content/pilots/cse-pilot/scripts/create-build-values.py), [package configuration](../../stack-content/pilots/cse-pilot/templates/configs/common/packages.yaml.j2), and [lockfile verification](../../stack-content/pilots/cse-pilot/templates/scripts/verify-lockfiles.py.j2).

This is CSE release policy. It should not be proposed as a Spack-wide target default.

### 4.5 Views and modules

The trial uses Spack-native views and a native `modules.yaml` for each environment. Active choices include:

- Foundation packages are linked into an ambient flat view and do not receive public modules.
- The Core environment for each compiler surface has its own Foundation build/view, but the current public compiler front-door modules intentionally prepend the shared GCC Foundation view. This is an exposure choice, not cross-compiler build reuse.
- Compiler, Core, Common, Serial, and MPI payloads receive named views or projected modules.
- Implicit dependencies are excluded from the public module surface.
- Public module names omit Spack hashes and use explicit projections.
- NetCDF-CXX4 projections include the selected NetCDF-C and HDF5 versions so parallel public versions do not collide.
- Front-door compiler modules and lane modules carry conflicts that keep incompatible compiler/lane surfaces from being active together.
- The front-door compiler and lane modules encode the reviewed compiler/MPI toolchain.

The implementation is in [module configuration partial](../../stack-content/pilots/cse-pilot/templates/_partials/modules.yaml.j2), [front-door module partial](../../stack-content/pilots/cse-pilot/templates/_partials/compiler-front-door.j2), and the [rendered environment reference](spack_1_2_rendered_environment_reference_v1.md). Version-sensitive conflicts and dependency handling between two public versions of the same package remain full-render work; they are not implemented by the current trial `modules.yaml` partial. These are CSE naming and consumption policy, not proposed Spack defaults.

## 5. Generic Spack integration behavior and workarounds

These controls are not site policy by themselves. They make the workflow reliable around observable Spack behavior.

### 5.1 Build-stage selection

Cluster Inspector reports candidate paths and node-specific writability facts. The generated `cse-build login ...` and `cse-build compute ...` commands then create and execute a probe in the selected candidate before exporting one exact `CSE_BUILD_STAGE` value.

Relevant implementation:

- [filesystem probe](../../cluster-inspector/internal/probes/filesystem.go)
- [profile merger](../../cluster-inspector/internal/commands/merge.go)
- [workspace launcher](../../stack-content/pilots/cse-pilot/templates/cse-build.j2)
- [Spack config template](../../stack-content/pilots/cse-pilot/templates/configs/common/config.yaml.j2)

The stage path is namespaced by system, release, node class, and uppercase `$USER`. Spack receives one verified path rather than a list of hoped-for fallbacks. This avoids permission failures that otherwise appear during concretization when Spack bootstraps solver components.

### 5.2 Login, compute, fetch, and install separation

The launcher supports the same workspace from login and compute nodes:

- Login mode is used for network-dependent bootstrap, concretization, and source fetch.
- Compute mode selects a compute-writable stage for builds.
- Fetched sources are retained in the shared source cache, so compute nodes do not need outbound internet access.
- Builders may run fetch and install explicitly rather than using one monolithic action.

This is orchestration around Spack, not a patch to Spack.

### 5.3 Parallelism and locking

In Spack 1.2.2's new installer, `build_jobs` is the global GNU make jobserver cap shared across concurrent package builds. The number of packages Spack may build concurrently is a separate installer setting, `concurrent_packages`, or the `spack install -p N/--concurrent-packages N` option. Independent environment processes can also run concurrently against the shared store because Spack locking and prefix locks are enabled. This two-level model is documented in Spack's official [Installing Packages: Parallelism](https://spack.readthedocs.io/en/latest/installing.html#parallelism) documentation as functionality added in Spack 1.2.

The current trial renders `build_jobs` but does not override `concurrent_packages`; the pinned Spack installer's package-concurrency behavior therefore applies. If CSE needs a per-process package limit for memory or scheduler accounting, it should add an explicit reviewed `concurrent_packages` value or pass `-p N` rather than reducing `build_jobs` and assuming only one package will run.

CSE therefore treats these separately:

- global build-token budget within one installer: rendered `build_jobs` and `-j` values;
- concurrent packages within one installer: `concurrent_packages` or the `-p N` limit;
- environment-level concurrency: operator or scheduler launches independent environment builds;
- shared producer safety: identical hashes and Spack locks prevent two successful installations into the same prefix.

See [Spack 1.2.2 build orchestration semantics research](spack_1_2_2_build_orchestration_semantics_research_v1.md).

### 5.4 Bootstrap and cache isolation

Concretization can install bootstrap dependencies such as Clingo even though it does not build the requested stack roots. The launcher assigns release-controlled bootstrap and user-cache paths, and it performs bootstrap on a network-capable node before compute builds.

This behavior is recorded in [initial conversion trials build findings](initial_conversion_trials_build_findings_v1.md) and implemented by [bootstrap.yaml.j2](../../stack-content/pilots/cse-pilot/templates/configs/common/bootstrap.yaml.j2) and [cse-build.j2](../../stack-content/pilots/cse-pilot/templates/cse-build.j2).

### 5.5 Source-cache recovery

The Raider trial exposed an unavailable Readline patch URL: the primary source returned 404 and an external mirror returned 502. The runbook recovery places the checksum-verified patch in Spack's configured shared source cache before retrying fetch.

This is an operational source-cache recovery, not an active package recipe overlay. It should become an upstream package issue only if the official recipe still points to a persistently unavailable artifact and the failure is reproducible without site network interference. See [Raider runbook notes](../../stack-content/systems/raider/runbook-notes.md).

### 5.6 Lockfile verification beyond successful concretization

A successful solver run is necessary but not sufficient for the CSE trial. The generated verifier checks:

- all eight expected environments;
- shared producer hashes within a compiler surface;
- exact compiler and MPI provider boundaries;
- target policy and the Miniforge exception;
- CMake dependency selection;
- the three Python roots;
- NetCDF/HDF5 version chains;
- Dakota dependency reuse;
- the local repository and required package overlays.

See [verify-lockfiles.py.j2](../../stack-content/pilots/cse-pilot/templates/scripts/verify-lockfiles.py.j2). This guard should remain part of CSE even when individual upstream defects are fixed.

## 6. Site, provider, and compiler adapters

### 6.1 Cray MPICH flavor semantics

A compiler version embedded in a Cray MPICH product path is treated as the minimum compatible compiler family baseline, not as proof that the active compiler must have the same exact version. For example, a `gcc/12.3` product path can be a valid external MPI flavor for GCC 12.5 when the site module test verifies that pairing.

Cluster Inspector therefore:

- retains every discovered Cray MPICH product version and compiler flavor;
- records verified compiler/MPI pairings separately from path-derived baselines;
- keeps unpaired candidates as evidence instead of silently dropping them;
- excludes ABI/helper activation modules from provider selection;
- normalizes activation module chains;
- switches exact PrgEnv/compiler modules while testing non-default pairings;
- canonicalizes compiler driver prefixes to the real compiler installation root.

Implementation is concentrated in [Cray provider adapter](../../cluster-inspector/internal/probes/cray.go), [module discovery](../../cluster-inspector/internal/probes/modules.go), [compiler probe](../../cluster-inspector/internal/probes/compiler.go), and [MPI probe](../../cluster-inspector/internal/probes/mpi.go). The behavior is covered by repository tests and the history around commits `8bf3dee`, `4e64df8`, `0ba1bad`, `062e116`, `306b4e2`, and `4e9135c`.

Stack Composer and Stack Content then select a reviewed flavor. Discovery remains separate from policy.

### 6.2 Cray MPICH as an external leaf

The selected Cray MPICH package is rendered as an external, non-buildable leaf. It must not inherit blanket compiler, target, libfabric, or PMI dependency constraints from the payload root. Its flavor-specific scope supplies the compiler and MPI wrapper evidence.

The implementation is in [static catalog rendering](../../stack-composer/src/stack_composer/render/static_catalog.py), [MPI scope rendering](../../stack-composer/src/stack_composer/render/scopes.py), and the [MPI lane template](../../stack-content/pilots/cse-pilot/templates/_partials/mpi-lane.j2).

### 6.3 Cray libfabric and PMI runtime metadata

Cray MPICH can depend at runtime on site-provided libfabric and PMI components even when those components are not separately built by CSE. The profile and generated scopes retain them as externals. The selected libfabric's `lib64` directory is added to the external MPI runtime metadata for clean build environments.

This is a provider adapter, not an instruction to build libfabric or PMI. It addresses the target-system finding that a clean environment could load the MPI wrapper but fail to resolve its runtime libfabric. See [provider package policy](../../stack-composer/src/stack_composer/render/provider_packages.py), [MPI scope rendering](../../stack-composer/src/stack_composer/render/scopes.py), and finding ICT-009 in [build findings](initial_conversion_trials_build_findings_v1.md).

### 6.4 Cray Programming Environment state hygiene

Ambient `PrgEnv-*`, provider modules, and `PE_ENV` can leak compiler flags or launcher selection into a build intended for another compiler. The generated launcher performs module operations in a child process, unloads reviewed ambient modules, unsets `PE_ENV`, and then loads only the explicit toolchain modules for the selected environment.

This is implemented in [module-state preparation](../../stack-content/pilots/cse-pilot/templates/env/prepare-module-state.sh.j2) and [cse-build.j2](../../stack-content/pilots/cse-pilot/templates/cse-build.j2), and documented by finding ICT-006 in [build findings](initial_conversion_trials_build_findings_v1.md). It is a Cray site adapter and process-hygiene control, not a Spack core patch.

### 6.5 Open MPI build policy

Non-Cray systems build Open MPI 4.1.8. The active policy uses discovered facts rather than unconstrained autodetection:

- UCX is selected when its external boundary is verified.
- Scheduler integration is selected from verified Slurm or PBS facts.
- `mpirun` is required.
- Direct Slurm launch is enabled only when the inspected launcher capabilities verify the required PMI interface.
- CUDA is disabled for the CPU trial.
- Fortran and ROMIO are enabled.
- Lustre is disabled unless an explicit verified policy enables it.

See [Open MPI policy](../../stack-content/pilots/cse-pilot/openmpi-policy.yaml), [build-values generator](../../stack-content/pilots/cse-pilot/scripts/create-build-values.py), and [MPI probe](../../cluster-inspector/internal/probes/mpi.go). The precise launcher choice is a CSE/provider policy. General launcher capability discovery may be useful to other sites, but no Spack change is required for the active design.

### 6.6 Compiler identity mapping

Human and module names do not always equal Spack package names. The renderer uses explicit identities, including:

- `intel` compiler family to `intel-oneapi-compilers-classic` package identity;
- `oneapi` to `intel-oneapi-compilers`;
- Intel MPI to `intel-oneapi-mpi`.

See [provider package identities](../../stack-composer/src/stack_composer/render/provider_packages.py) and [static catalog rendering](../../stack-composer/src/stack_composer/render/static_catalog.py). This mapping is generic renderer behavior driven by authored policy, not an upstream Spack patch.

### 6.7 AOCC and classic Intel

AOCC and classic Intel are platform compiler surfaces discovered from system modules and rendered as explicit external compilers. Open MPI is built against those compilers on the applicable non-Cray systems. GCC runtime providers required by Intel compiler packages remain explicit external dependencies rather than being inferred from a package name.

The relevant discovery and model paths are [compiler probe](../../cluster-inspector/internal/probes/compiler.go), [provider package identities](../../stack-composer/src/stack_composer/render/provider_packages.py), and [MPI/toolchain model](../../stack-composer/src/stack_composer/render/mpi.py).

## 7. Active package overlays

The active repository contains exactly three package overlays. The overlay set is verified by [test_package_repo_overlays.py](../../stack-content/pilots/cse-pilot/tests/test_package_repo_overlays.py) and by each generated workspace before build actions.

### 7.1 CMake

**Local implementation:** [CMake overlay](../../stack-content/pilots/cse-pilot/templates/package-repos/spack_repo/cse_trials/packages/cmake/package.py)

The overlay extends the builtin CMake package and adds:

- CMake 3.31.12 as preferred;
- CMake 4.4.2 as the second public root.

**Why it exists:** The pinned `spack-packages` `v2026.06.0` repository does not contain these exact versions, but the approved trial matrix requires them.

**Upstream disposition:** No new upstream change is required. Both versions are present in the current [CMake package on `develop`](https://github.com/spack/spack-packages/blob/develop/repos/spack_repo/builtin/packages/cmake/package.py). As of this inventory, `v2026.06.0` remains the latest immutable entry in the official [`spack-packages` releases](https://github.com/spack/spack-packages/releases), so there is no later released repository pin that contains both versions.

Do not switch the builtin package repository to the moving `develop` branch merely to remove this overlay. Changing the entire builtin repository to `develop`, or to an exact post-release commit, changes package recipes and therefore can change CMake hashes, dependency hashes, and complete DAGs across all eight environments. Such a pin change requires an all-environment impact review, fresh root reconcretization, lockfile comparison, and target-system validation. The narrow CMake overlay is the lower-risk control while the immutable repository pin remains `v2026.06.0`.

Remove the overlay only after CSE deliberately advances to an immutable repository release or reviewed exact commit containing both versions and the rendered trial passes that full impact review.

### 7.2 CCE

**Local implementation:** [CCE overlay](../../stack-content/pilots/cse-pilot/templates/package-repos/spack_repo/cse_trials/packages/cce/package.py)

The package remains external-only and adds the trial-system CCE versions:

- 19.0.0
- 20.0.0
- 21.0.0

It also records the CCE compiler drivers, wrapper link paths, and implicit runtime libraries needed to register an external compiler accurately.

**Why it exists:** The pinned repository's CCE recipe does not enumerate the compiler versions deployed on the systems. The current [upstream CCE package on `develop`](https://github.com/spack/spack-packages/blob/develop/repos/spack_repo/builtin/packages/cce/package.py) still enumerates only CCE 16.0.0.

**Upstream disposition:** Prepare a `spack-packages` pull request adding supported external CCE version metadata. Before submission:

1. compare the CSE overlay with current `develop` rather than copying the pinned recipe;
2. retain current upstream language-standard metadata, including any C++20 flag support missing from the local overlay;
3. include evidence from CCE 19, 20, and 21 registration or compiler tests;
4. keep site module names and CSE selection policy out of the upstream recipe.

The version declarations and generally applicable compiler metadata are upstream candidates. The selection of the latest three CSE-visible releases is CSE policy and should remain local.

### 7.3 Dakota and Boost.System

**Local implementation:**

- [Dakota overlay](../../stack-content/pilots/cse-pilot/templates/package-repos/spack_repo/cse_trials/packages/dakota/package.py)
- [Boost.System patch](../../stack-content/pilots/cse-pilot/templates/package-repos/spack_repo/cse_trials/packages/dakota/boost-system-header-only.patch)
- [overlay tests](../../stack-content/pilots/cse-pilot/tests/test_package_repo_overlays.py)

The overlay extends the builtin Dakota package and applies the patch to Dakota 6.23.0 through 6.24.0. The patch removes the obsolete compiled `system` component and `Boost::system` link targets while retaining the Boost components Dakota still uses.

**Evidence:** Boost.System has been header-only since Boost 1.69, and Boost 1.89 removed the compiled compatibility stub. The official [Boost 1.89 release notes](https://www.boost.org/releases/1.89.0/) direct consumers to stop requiring the `system` binary component. Current Dakota `devel` still names `Boost::system` in [DakotaFindSystemTPLs.cmake](https://github.com/snl-dakota/dakota/blob/devel/cmake/DakotaFindSystemTPLs.cmake), [plugin CMakeLists.txt](https://github.com/snl-dakota/dakota/blob/devel/src/plugins/CMakeLists.txt), and [surrogate unit-test CMakeLists.txt](https://github.com/snl-dakota/dakota/blob/devel/src/surrogates/unit/CMakeLists.txt). The current [Spack Dakota recipe](https://github.com/spack/spack-packages/blob/develop/repos/spack_repo/builtin/packages/dakota/package.py) also requests Boost `+system`.

**Upstream disposition:** This is the highest-priority upstream queue item.

1. Submit or coordinate a Dakota upstream change that removes `system` from the requested Boost components and all remaining `Boost::system` targets.
2. Submit a `spack-packages` change for affected Dakota releases. Depending on upstream release timing, this may carry the source patch for 6.23/6.24 and remove the obsolete `+system` dependency for fixed releases.
3. Attach the CSE patch-application test and target-system build evidence.
4. Retire the local overlay only after the pinned repository contains the fix and both Serial and MPI Dakota roots pass the CSE lock and install validation.

## 8. Package constraints that are not overlays

Several issues were resolved through Spack-native constraints rather than editing recipes.

| Package or graph | CSE handling | Classification |
| --- | --- | --- |
| Miniforge3 | Target is `x86_64`, not the source-build `x86_64_v3` baseline. | Reviewed binary-target exception. Consider an upstream issue only with a minimal reproducer showing current package metadata incorrectly accepts or rejects a published binary target. |
| GCC | Shared compiler root explicitly includes `+binutils` and the C, C++, and Fortran languages. | CSE compiler policy based on a failed target-system build; no recipe patch. |
| OpenSSL and curl | Registered as exact externals with the variants and prefix reported by inspection. No global compiler requirement is imposed on them. | External-boundary policy. |
| Netlib LAPACK | Both `blas` and `lapack` virtuals are constrained to the reviewed Netlib LAPACK roots. | Provider policy. |
| Dakota LAPACK | Dakota is explicitly constrained to the already-approved Netlib LAPACK 3.12.1 root. | DAG-reuse policy; avoids a third LAPACK build when the full spec matches. |
| HDF5/NetCDF | Explicit dependency chains pair each NetCDF generation with its intended HDF5 generation and MPI or Serial boundary. | Release compatibility matrix. |
| Python consumers | Ninja, Boost MPI, XCB Proto, and Dakota receive explicit Python 3.12.13 constraints where needed. | DAG cardinality control. |
| External UCX, scheduler, Cray MPICH, libfabric, and PMI | Root constraints stop at the reviewed external boundary instead of propagating compiler and target requirements into platform externals. | Provider-boundary integration. |

The exact constraints are in [roster.yaml](../../stack-content/pilots/cse-pilot/roster.yaml), [packages.yaml.j2](../../stack-content/pilots/cse-pilot/templates/configs/common/packages.yaml.j2), [environment templates](../../stack-content/pilots/cse-pilot/templates/environments), and [build-values generation](../../stack-content/pilots/cse-pilot/scripts/create-build-values.py).

## 9. Historical findings and proposed work not in the active overlay

These items must not be mistaken for current package patches.

### 9.1 Cray GTL, PMI, and PALS packaging

[Cray runtime package repository note](cray_runtime_package_repo_note_v1.md) describes a possible future repository for `cray-gtl`, `cray-pmi`, and `cray-pals`. The active CPU trial does not ship these package overlays. Current handling is external discovery and runtime metadata. Any future package should be justified by a concrete need that cannot be represented as an external boundary.

### 9.2 NVHPC and ROCm experiments

Earlier exploration found that NVHPC might need GCC-built tools and that the tested ROCm compiler surface lacked a working Fortran provider. Those findings remain in [CSE Spack learnings](spack-learnings/CSE-Spack-Learnings.md), but neither compiler is part of the current CPU conversion-trial matrix. They should not add compatibility paths to the current initializer.

### 9.3 Global compiler requirements

Early experiments showed that a global `%compiler` requirement can incorrectly constrain externals and compiler-independent packages. The active implementation uses package-level `prefer`, explicit producer groups, and toolchain constraints at the source-built roots. This is a CSE modeling correction, not a Spack patch.

### 9.4 `spack verify libraries` allowlist

The learnings propose an allowlist mechanism for known platform libraries when auditing installed binaries. No Spack core change is implemented. This remains a potential upstream feature proposal only after CSE has a concrete report format, false-positive examples, and a target-system validation workflow.

### 9.5 CMake `FindMPI` launcher leakage

An ambient scheduler launcher can influence CMake's `FindMPI` independently of the MPI library selected by Spack. The active mitigation is clean module state plus explicit provider and launcher policy. A generic upstream report may be appropriate if a minimal package reproducer demonstrates that Spack cannot convey the intended launcher to a consumer package; no package overlay exists today.

### 9.6 Stack Composer Python packaging

Stack Composer's build process pins a usable Python and modern packaging tools because target systems contain inconsistent Python and setuptools versions. This is tooling required to build Stack Composer, not a Spack package customization. The relevant files are [pyproject.toml](../../stack-composer/pyproject.toml), [build-pyz.sh](../../stack-composer/scripts/build-pyz.sh), and Part 3 of [the system runbook](runbook.md).

## 10. Actionable upstream queue

| Priority | Item | Destination | Required evidence | Local retirement gate |
| --- | --- | --- | --- | --- |
| P0 | Remove Dakota's compiled Boost.System requirement and links | Dakota upstream, followed by `spack-packages` | Patch applies to supported Dakota releases; configure/build and Serial/MPI install results with Boost 1.89 or later | Pinned repository carries the fix and both Dakota lanes pass CSE validation without the overlay |
| P1 | Add current external CCE versions and preserve current compiler-standard metadata | `spack-packages` CCE recipe | CCE 19/20/21 compiler registration and compile probes; comparison against current `develop` | A pinned package repository release contains the versions and the CSE systems render/concretize without the overlay |
| P2 | Determine whether Miniforge target modeling needs a recipe correction | `spack-packages`, only if reproducible | Minimal current-`develop` reproducer using the published binary and target metadata | No local target exception is required, or upstream confirms the exception is correct policy |
| P2 | Report persistent Readline patch source failure if it reproduces outside the site | `spack-packages` package/source metadata | Primary and mirror failures from a clean current repository, checksum and replacement source | Pinned repository has a reliable verified source; runbook cache injection removed |
| P3 | Propose library-verification allowlists if CSE operational evidence supports them | Spack core | Real audit output, known platform library cases, proposed schema and security behavior | CSE can use the upstream verifier without a local post-processing rule |
| P3 | Report MPI launcher metadata gap if a minimal consumer reproducer remains | Spack core or affected package | Clean environment, exact MPI external, scheduler launcher, CMake trace | Explicit site workaround becomes unnecessary |

No upstream work is required for the CMake overlay: current `spack-packages` development already contains both versions. Advancing the package repository pin is the retirement path.

## 11. Retention and review rules

1. Keep the local repository small. A package enters it only with a failing target-system reproducer and an explicit removal condition.
2. Do not copy an entire upstream recipe when a narrow subclass, version addition, or source patch is sufficient.
3. Compare every overlay against current `spack-packages` `develop` before proposing upstream or advancing the repository pin.
4. Keep site module names, filesystem paths, and CSE release choices out of upstream package changes.
5. After any package overlay change, regenerate the workspace, reconcretize affected roots with forced root replacement and dependency reuse, and run the generated lockfile verifier.
6. Validate both the shared GCC and platform-compiler surfaces. A fix proven under GCC is not automatically proven under CCE, AOCC, or Intel.
7. Record the exact system, compiler, environment, Spack commit, package-repository commit, lockfile hash, and build log with an upstream report.
8. Remove overlays directly when their retirement gate is met. The project is pre-v1 and does not retain legacy overlay paths.

## 12. Implementation and evidence index

### Active implementation

- [Cluster Inspector Cray adapter](../../cluster-inspector/internal/probes/cray.go)
- [Cluster Inspector compiler probe](../../cluster-inspector/internal/probes/compiler.go)
- [Cluster Inspector MPI probe](../../cluster-inspector/internal/probes/mpi.go)
- [Cluster Inspector filesystem probe](../../cluster-inspector/internal/probes/filesystem.go)
- [Stack Composer workspace initializer](../../stack-composer/src/stack_composer/workspace/initializer.py)
- [Stack Composer static renderer](../../stack-composer/src/stack_composer/render/static_catalog.py)
- [Stack Composer module renderer](../../stack-composer/src/stack_composer/render/modulefiles.py)
- [Stack Composer toolchain model](../../stack-composer/src/stack_composer/render/mpi.py)
- [Stack Content Initial Conversion Trials workspace](../../stack-content/pilots/cse-pilot)
- [Stack Content Open MPI policy](../../stack-content/pilots/cse-pilot/openmpi-policy.yaml)
- [Stack Content overlay tests](../../stack-content/pilots/cse-pilot/tests/test_package_repo_overlays.py)

### Decision and validation evidence

- [Initial conversion trials build findings](initial_conversion_trials_build_findings_v1.md)
- [Initial conversion trials dependency risk audit](initial_conversion_trials_dependency_risk_audit_v1.md)
- [Initial conversion trials package version check](initial_conversion_trials_package_version_check_v1.md)
- [Initial conversion trials system runbook](runbook.md)
- [Spack 1.2 rendered environment reference](spack_1_2_rendered_environment_reference_v1.md)
- [Spack 1.2.2 build orchestration semantics research](spack_1_2_2_build_orchestration_semantics_research_v1.md)
- [CSE Spack learnings](spack-learnings/CSE-Spack-Learnings.md)
- [Cray runtime package repository note](cray_runtime_package_repo_note_v1.md)

This inventory is validated against the current files and tests in all four
repositories. Commit messages and point-in-time status notes are supporting
history only; they do not override the current implementation.
