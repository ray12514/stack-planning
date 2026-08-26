# Post-Trial CSE Consumption Environment Plan v1

| Document control | |
|---|---|
| Date | 2026-08-25 |
| Status | Proposed post-trial direction; review and refine from Initial Conversion Trials evidence |
| Scope | The deployed environment used by people building software on top of CSE |
| Trial impact | None. Do not reorganize the active trial YAML or invalidate its lockfiles to implement this plan. |

## 1. Outcome

The production CSE release should present one controlled development surface to
a user who does not need to know that Spack was used to create it. After the
user enters a selected compiler/lane environment, the approved compiler, build
tools, headers, libraries, metadata, and platform integrations are available in
a deliberate order. The user can bring source code into that surface and build
on top of it without accidentally resolving unrelated software from a personal
prefix, `/usr/local`, a site default module, or another CSE release.

The useful analogy is a container, but the intended product is not a kernel or
filesystem container. It is a **managed consumption environment**: hermetic at
the command, header, library, package-metadata, and module-discovery layer while
still using approved host services and hardware runtimes.

```text
user source tree
      |
      v
CSE compiler/lane front door
  + compiler-neutral managed substrate
  + compiler-bound Foundation
  + selected Core tools
  + compiler-shared Common packages
  + Serial / MPI / GPU payload
      |
      v
declared system-integration externals
  kernel, loader/libc contract, scheduler, drivers, fabric/vendor runtimes,
  and explicitly approved security-owned system libraries
```

## 2. What the trials contribute

The Initial Conversion Trials are not the final tier implementation. They are
the evidence-producing phase. Their lockfiles, install prefixes, dependency
types, compiler providers, runtime links, build logs, and cross-system outcomes
should be used to decide where each future package belongs and how narrowly it
must be rebuilt.

Keep the trial's current per-compiler Foundation/Core arrangement until the
remaining platform-compiler builds are complete. Changing the model in the
middle would mix an architecture experiment with the trial's acceptance work
and make the results harder to compare.

The post-trial questions are:

1. Which commands and libraries must always be present for a useful isolated
   user build environment?
2. Which of those artifacts are compiler-neutral within a reviewed platform
   compatibility domain?
3. Which must remain bound to one compiler, MPI provider, GPU runtime, or lane?
4. Which host-owned packages are intentional integration points rather than
   accidental ambient dependencies?
5. Which concrete artifacts can be reused through a build cache without
   weakening those contracts?

## 3. Separate the decisions currently hidden inside a tier name

The current trial uses Foundation/Core/Common/Serial/MPI as both layout and
build guidance. The production model should keep those useful placement names,
but it must not infer every other property from them. Each curated root should
carry independently reviewable attributes.

| Attribute | Question it answers | Candidate values |
|---|---|---|
| Placement | Where does it sit in the CSE product? | Foundation, Core, Common, Serial, MPI, GPU, private transitive |
| Exposure | How does a user receive it? | ambient, loadable, package module, hidden |
| Interface | What can consumers use? | command, headers/library, pkg-config/CMake metadata, language environment, runtime provider |
| Compiler binding | Which compiler identity owns it? | neutral, compiler surface, provider/toolchain, lane |
| Dependency role | Why does a concrete consumer need it? | build, link, run, test; possibly more than one |
| Reuse scope | Where may one exact artifact be accepted? | release, system, compatibility domain, compiler surface, provider, lane |
| Source policy | Who supplies it? | CSE-built, approved binary distribution, system-integration external |

The dependency role comes from the concrete DAG and package recipe. The other
attributes are CSE product policy. A package being a Spack `build` dependency
does not by itself make that package hidden from CSE users. Autoconf can be a
build-only edge in a package DAG and also an intentionally exposed command in a
user development environment.

## 4. Refined placement model

### 4.1 Foundation: automatically available substrate

Foundation is what a user receives automatically after entering CSE. It can
contain more than one compiler-binding class.

**Compiler-neutral Foundation tools** are commands whose output is not owned by
the selected C/C++/Fortran ABI. M4, Autoconf, and Automake are initial
candidates. Bison, Flex, Make, Meson, and similar build utilities may be
evaluated the same way. A successful classification means one reviewed artifact
can be used by multiple compiler surfaces within its compatibility domain; it
does not mean one binary works on every operating system or architecture.

**Compiler-bound Foundation libraries** are ambient headers, libraries, and
metadata deliberately made available to user builds. The trial's zlib, xz, and
zstd roots remain in this class initially. They may later qualify for broader
reuse, but C language and a stable-looking ABI are not sufficient evidence on
their own.

Foundation should remain single-version within one release's unqualified
ambient namespace. A package that needs competing public versions belongs in a
namespaced or loadable surface instead.

### 4.2 Core: selected user development tools

Core is the compiler/lane-independent user tool layer, normally selected or
loaded explicitly when multiple versions or distinct experiences are offered.
Core membership also does not imply compiler binding.

- Miniforge is already a compiler-neutral Core example in the trial.
- CMake, Ninja, pkgconf, and Git are candidates for compiler-neutral Core or
  ambient build substrate, depending on the final exposure decision.
- Python needs explicit treatment because it is both a command/runtime and an
  extension-development interface.
- SQLite, GSL, and other libraries should begin as compiler-bound unless the
  acceptance matrix demonstrates a broader safe scope.

Whether a tool is Foundation or Core is therefore an exposure/product choice:
always present versus intentionally selected. It is not the answer to whether
the tool can be built once.

### 4.3 Common: compiler-bound reuse across payload lanes

Common remains useful for packages that belong to one compiler surface but are
shared by its Serial, MPI, and future GPU environments. Netlib LAPACK is the
clear current example. Common is neither ambient by definition nor a dumping
ground for every repeated transitive dependency.

### 4.4 Payload and private transitive dependencies

Serial, MPI, and GPU remain behavior-bearing payload placements. Provider- or
performance-sensitive packages stay with the appropriate lane even when many
lanes use them. A transitive dependency that users do not directly consume can
remain hidden and RPATH-isolated rather than being promoted merely because it
appears often.

## 5. Initial classification hypotheses

These are audit starting points, not final roster changes.

| Package family | Likely placement/exposure | Initial binding | Evidence still required |
|---|---|---|---|
| M4, Autoconf, Automake | Foundation; ambient commands | compiler-neutral candidate | runtime closure, generated-output comparison, OS/glibc floor |
| Make, Bison, Flex, Meson | Foundation or Core; decision by user workflow | compiler-neutral candidate | runtime closure and target-host execution |
| CMake, Ninja, pkgconf, Git | Core or selected ambient substrate | compiler-neutral candidate | embedded libraries, plugins, runtime paths, compatibility-domain tests |
| zlib, xz, zstd | Foundation; ambient headers/libraries/metadata | compiler-bound initially | cross-compiler compile/link/run and symbol/runtime audit |
| Miniforge | Core; loadable language environment | compiler-neutral within vendor binary domain | upstream platform support and extension-build behavior |
| Python | Core; loadable command and development interface | compiler-bound initially | extension ABI, libpython, sysconfig and toolchain behavior |
| SQLite, GSL | Core/Common according to exposure | compiler-bound initially | exported ABI and clean consumer tests |
| Netlib LAPACK | Common | compiler-bound | compiler/runtime and Fortran ABI verification |
| HDF5, NetCDF, FFTW, Boost | Serial/MPI payload | compiler and lane | existing chain and module acceptance tests |
| MPI, fabric, GPU/vendor runtimes | provider/lane or system integration | provider/toolchain | platform compatibility and runtime-set validation |

## 6. System-integration external policy

Isolation does not mean rebuilding every package. A system package should be
used only when the system owns a meaningful part of its compatibility or
operational contract.

Good reasons include:

- privileged or kernel-adjacent integration;
- scheduler and launcher integration;
- hardware driver, fabric, or vendor programming-environment coupling;
- vendor performance libraries whose value is tied to the platform; or
- a security-updated system component that CSE deliberately chooses to follow.

Likely candidates include the kernel/dynamic-loader/libc base, Slurm or
PALS/PMI integration, selected MPI providers, libfabric, UCX where the platform
owns it, Cray runtime/performance libraries, and GPU drivers/toolkits. OpenSSL
and curl may remain system externals when following the operating system's
security lifecycle is the chosen policy.

Every system-integration external must be declared. The profile records the
observed version, prefix, modules, provider family, and evidence; CSE policy
decides whether it may be used; the release records the exact selection.
"Present in `/usr`" or "found by configure" is never approval.

System updates are therefore handled as changes to an explicit external
contract. They trigger revalidation or rebuild according to the affected
release graph rather than silently changing an existing CSE environment.

## 7. Consumption-environment interface

The desired public interface is one front door for the selected release,
compiler, and lane. Exact naming remains a module-policy decision, but the
activation behavior should be deep: users make one selection and the
implementation composes the required layers.

Activation should:

- establish a clean, deterministic module order;
- put CSE commands ahead of unapproved personal and site software;
- expose only the selected Foundation headers/libraries and package metadata;
- expose Core and payload modules according to policy;
- load only the reviewed compiler, scheduler, fabric, MPI, GPU, and vendor
  prerequisites;
- prevent another CSE release or compiler surface from leaking into discovery;
- prefer build-time RPATH and exact metadata over a broad global
  `LD_LIBRARY_PATH`; and
- record enough identity for a user or support engineer to report exactly which
  release/compiler/lane is active.

The operating system shell and essential base commands remain available.
Absolute paths and hostile build scripts cannot be made fully hermetic without
a real container or sandbox, so acceptance must describe this honestly as
managed discovery isolation, not kernel isolation.

## 8. Compatibility domains and build-cache reuse

"Build once" always means once within a named compatibility domain. A domain
should include at least:

- operating-system family and ABI/glibc floor;
- CPU architecture and portable target;
- package recipe generation and variants;
- external runtime contracts; and
- compiler/provider identity whenever the artifact is not compiler-neutral.

The build cache may contain artifacts for many domains. Reuse occurs only when
the concrete hash and the CSE compatibility policy both accept the artifact.
The release manifest should state whether a root was reused at the
compiler-neutral, compiler-surface, provider, or lane scope.

## 9. Evidence to collect from the remaining trials

Do not delay the remaining platform builds to implement a new tier system.
Add the following outputs to the post-trial analysis instead:

1. **Concrete dependency-role inventory.** For every root and transitive node,
   record build/link/run/test edges from each lockfile.
2. **Exported-interface inventory.** Record commands, headers, libraries,
   pkg-config/CMake metadata, Python extension surfaces, and public modules.
3. **Binary/runtime audit.** Record interpreter, dynamic dependencies, RPATH,
   compiler runtime, symbol-version floor, CPU target, and platform externals.
4. **Cross-surface comparison.** Identify packages repeated under GCC and the
   platform compiler and determine whether the artifacts or behavior truly
   differ.
5. **Clean consumer tests.** From a fresh user shell, build and run representative
   Autotools, CMake, C, C++, Fortran, MPI, and later GPU examples without Spack
   knowledge or an unapproved personal prefix.
6. **System-update exposure report.** List every selected system external and
   which release checks must rerun if it changes.

The generated lock verifier is the natural future seam for graph identity and
reuse evidence, but product classification should be supplied by reviewed
content rather than inferred solely from a lockfile.

## 10. Phased recommendation

### Phase 0 — Finish and preserve trial evidence

Complete the remaining platform-compiler builds with the current model. Save
locks, manifests, build logs, dependency reports, module/view output, and
system-specific findings.

### Phase 1 — Produce the package classification report

Generate one package matrix from all trial locks and installed artifacts. Give
each package a proposed placement, exposure, interface, binding, reuse scope,
source policy, and confidence level. Mark uncertain packages for testing rather
than forcing a classification.

### Phase 2 — Adopt the orthogonal content model

Represent the reviewed properties in Stack Content and the release manifest.
Replace special buckets such as `core_independent` with an explicit
compiler-binding attribute. Update Stack Planning contracts before changing
Stack Composer or templates.

### Phase 3 — Prototype one complete consumption environment

Use one system with both shared GCC and a platform compiler—Wheat is a useful
candidate—to prove:

- one compiler-neutral tool substrate is safely reused;
- compiler-bound Foundation stays separated;
- front-door activation produces the intended clean discovery order; and
- user builds succeed without Spack or a source checkout.

### Phase 4 — Expand compatibility domains and caches

Only after the two-compiler prototype passes should selected artifacts be
promoted to cross-system compatibility domains and shared build-cache lanes.
Start with command-only build tools before ambient libraries.

### Phase 5 — Release and system-update acceptance

Test immutable release activation, rollback, external-runtime change detection,
cache-only reconstruction, and clean consumer builds before treating the model
as the production CSE environment.

## 11. Acceptance gates

The post-trial model is ready for implementation when:

- every curated root has an explicit placement, exposure, compiler binding,
  reuse scope, and source policy;
- a user can enter the environment and build representative software without
  invoking or configuring Spack;
- discovery logs contain no unapproved personal, `/usr/local`, site-module, or
  other-release prefix;
- every system dependency is an explicit, versioned integration external;
- compiler-neutral reuse is demonstrated across at least two compiler
  surfaces;
- compiler-bound libraries remain separated unless stronger evidence approves
  broader reuse;
- release identity and rollback survive a system-default change; and
- the build cache can reconstruct the approved environment without changing
  its concrete graph.

## 12. Related documents

- [Foundation and Core view semantics](foundation_core_view_semantics_note_v1.md)
- [Initial Conversion Trials build execution model](initial_conversion_trials_build_execution_model_v1.md)
- [CSE customization and upstream inventory](cse_spack_customization_and_upstream_inventory_v1.md)
- [Platform runtime-set design](platform_runtime_set_design_v1.md)
- [Platform compatibility fingerprinting concept](cse_platform_compatibility_fingerprinting_concept_v1.md)

