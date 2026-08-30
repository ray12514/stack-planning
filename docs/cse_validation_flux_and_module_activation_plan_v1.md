# CSE Validation, Flux Execution, And Module Activation Plan v1

| Document control | |
|---|---|
| Date | 2026-08-28 |
| Status | Active implementation plan; Phase 0 is trial-only and blocks Initial Conversion Trial CCE publication |
| Scope | Current CPU-only CSE trials, published release regression, optional nested Flux execution, and the post-trial consumption environment |

## 1. Outcome and decisions

CSE should add one downstream validation path that proves a rendered and built
release is usable through the same module surface a user receives. ReFrame is
the recommended test harness. Flux is an optional execution adapter inside an
allocation; it is not a new renderer responsibility and it is not required for
release correctness.

The decisions are:

1. **Adopt ReFrame for release acceptance and recurring regression.** ReFrame
   compiles and runs focused probes, schedules native or Flux jobs, evaluates
   sanity/performance results, and produces durable reports.
2. **Do not use ReFrame's Spack build backend to build the CSE release.** The
   reviewed CSE lockfiles, complete-lock verification, shared store, and
   cache-only publication remain authoritative. A ReFrame test may compile a
   disposable consumer program against the installed release; it may not
   reconcretize the release.
3. **Use layered tests, not one mega-application.** Small capability probes
   locate failures. Cross-library probes prove composition. A few pinned
   application canaries prove realistic consumption. No one application can
   cover every language binding, version pair, lane, launcher, and runtime.
4. **Keep the native scheduler/launcher path canonical.** A Flux run proves the
   optional nested executor. It does not replace the direct Slurm, PBS, PALS,
   or site-MPI launch that proves platform integration.
5. **Use the production render as the behavioral reference, not the Phase 0
   implementation target.** The full Stack Composer renderer already defines
   the compiler-front-door then lane-selector hierarchy. The current
   `render-static`/`init-workspace` pilot should mimic that public contract with
   its authored Jinja modulefiles; Phase 0 does not redesign or modify the
   production renderer.
6. **Make the module activation work Phase 0.** The active pilot originally
   exposed two shared-GCC paths from its platform front door. The structural
   correction and template regressions have landed, but the executable Cray
   wrapper/launcher gate still must pass before presenting the CCE surface.
7. **Keep the tools in their existing roles.** Cluster Inspector observes
   facts. `render-static` creates the restricted review catalog, and
   `publish-static` promotes that reviewed catalog for external consumers.
   `init-workspace` materializes both CSE workspaces from the retained
   restricted catalog. The eventual full `render` remains the production path.
   A downstream validation/build driver runs ReFrame, Flux, Spack, and
   scheduler commands.
8. **Do not use the parked `baseline_module_sets` proposal in the trials.** The
   exact reviewed module arrays in the profile/static catalog remain the
   authority.

The operator reports that CCE is the remaining live trial surface. The tracked
Blueback run record is blank and the running findings still contain pending
target-system work, so this plan treats that statement as current operator
status rather than repository-proven completion evidence.

## 2. Existing architecture and the trial seam

The new behavior fits the existing boundaries:

```text
Cluster Inspector profile
          |
          v
Stack Composer render-static --> reviewed static catalog
                                      |
trial values + cse-pilot content -----+
                                      |
                                      v
                         Stack Composer init-workspace
                                      |
                         +------------+-------------+
                         |                          |
                         v                          v
             locked Spack build path    trial front doors/lane modules
                         |                          |
                         v                          v
              published trial release    ReFrame acceptance
                                                    |
                                      +-------------+-------------+
                                      v                           v
                            native scheduler/launcher    Flux in outer allocation

Production reference (not changed in Phase 0):
Stack Composer render --> cse/<Compiler> --> Serial|MPI|GPU --> package modules
```

This creates two related but distinct planes:

- **Build plane:** `cse-build` neutralizes ambient state, lets Spack activate
  exact external records, installs only reviewed locks, owns one environment's
  view/module refresh, and publishes only accepted hashes.
- **Consumption/validation plane:** the compiler/lane entrance composes the
  reviewed user runtime, exposes exact identity, and is exercised from a clean
  session by ReFrame.

The user front door must never be preloaded as a workaround for a broken Spack
build environment. The build and consumption planes consume the same resolved
provider facts but apply different ambient-state policies.

### 2.1 Ownership

| Module/repository | Owns | Does not own |
|---|---|---|
| Cluster Inspector | Observed compiler/MPI/module/scheduler/fabric/runtime facts and evidence | Stack selection, test policy, or job execution |
| Stack Planning | Activation and acceptance contracts, ownership rules, release gates | Site commands or implementation code |
| Stack Content | Trial blueprint and modulefile templates; curated package/test policy, ReFrame probes, site adapters, application pins, runbook deltas | Host probing or production lane resolution |
| Stack Composer | `render-static`, trial blueprint materialization through `init-workspace`, and the separate eventual full-render behavior used as the reference | Spack installation, ReFrame execution, Flux lifecycle, or live wrapper selection |
| Build driver | Locked environment execution, cache/view/module ownership, optional Flux build adapter | Render policy or test verdicts |
| Validation driver | ReFrame configuration/run selection, evidence capture, optional Flux test adapter | Re-solving the CSE release |

For the first implementation, ReFrame tests and source fixtures can live under
Stack Content and a generated `cse-validate` entry point can travel in the
workspace. A separate validation repository is unnecessary until the interface
and cadence stabilize.

## 3. Current trial inventory and coverage boundary

The Initial Conversion Trials contain eight independent environments: Core,
Common, Serial, and MPI for the shared GCC surface, and the same four for the
selected platform compiler.

| Placement | Approved roots/capabilities |
|---|---|
| Foundation | zlib 1.3.1, xz 5.4.6, zstd 1.5.6 |
| Core/build tools | CMake 3.31.12 and 4.4.2, Ninja, pkgconf, Git, Python 3.8.20/3.10.20/3.12.13, GSL 2.6/2.8, SQLite 3.51.2/3.53.1, Miniforge 26.1.1-3 |
| Common | Netlib LAPACK 3.10.1/3.12.1, Gnuplot 5.4.10/6.0.0 |
| Serial | HDF5 1.10.6/2.1.0, paired NetCDF-C/Fortran/CXX4 chains, FFTW 3.3.10/3.3.11, Boost 1.81/1.90, all without MPI |
| MPI | The MPI-enabled HDF5/NetCDF/FFTW/Boost chains plus Dakota 6.23/6.24 |

Netlib LAPACK supplies the current BLAS/LAPACK capability. OpenBLAS, LAMMPS,
OpenFOAM, Kokkos, and RAJA are not approved trial roots. Application canaries
may build in a disposable validation stage against the release without becoming
published stack content.

The current lock verifier already proves structure: expected environment set,
compiler and MPI selection, target policy, Serial/MPI separation, shared
producer hash convergence, NetCDF/HDF5 pairings, and Dakota dependency
relationships. ReFrame should add the missing user-observable proof; it should
not duplicate the lock verifier in Python test classes.

## 4. Phase 0: finish the CSE module entrance contract

### 4.1 Immediate CCE publication blockers and completed parity work

The active pilot front-door partial originally selected
`values.shared.compiler.name` for both of these public paths:

- the Foundation view; and
- the Core module root.

The platform front door therefore exposed the shared GCC Foundation and Core
instead of the selected platform surface. The platform Core environment and
module root were rendered but effectively orphaned. The trial templates now
select both paths with `surface.compiler.name`, add the production-compatible
`STACK_RELEASE`, `STACK_COMPILER`, `STACK_INIT_MODULE`, `STACK_LANE`,
`STACK_LANE_ID`, and `STACK_VIEW` identities, and require each short lane
selector's matching compiler front door. Template regressions cover both
shared and platform surfaces.

Do not call the CCE user surface ready after only this path correction. The
remaining entrance gates below are equally release-blocking.

### 4.2 The production contract the trial mimics

The full renderer already has the useful reference contract:

```text
module load cse/<Compiler>
module load <Serial|MPI|GPU>
module load <package>/<version>
```

Its compiler front door selects the compiler surface, exposes that surface's
Foundation view and Core/Common package-module roots, and makes only its lane
selectors visible. A lane selector conflicts with sibling lanes and exposes
only its own package-module root. The renderer's internal `module_plan` feeds
both its report and its modulefile emitter.

The current trial should reproduce that behavior directly in the existing
pilot templates. It does not need a new activation-plan abstraction and does
not need the production emitter to render the trial. The mapping is:

| Production reference | Current trial |
|---|---|
| `cse/GCC`, `cse/CCE` | builder-selected `cse/init-GCC`, `cse/init-CCE` |
| surface-specific Foundation/Core/Common | same, from `surface.compiler.name` |
| short `Serial`/`MPI` selector | same |
| `STACK_*` release/compiler/lane/view identity | same names and meanings |
| `platform_module_policy: autoload` when selected | ordered module loads from reviewed trial values |

The `init-` prefix is only a collision-avoiding trial convention. It is not a
new production namespace.

### 4.3 Entrance-name ownership

The **compiler front-door module**, also called the **CSE init module**, is the
gate the user enters. In the trial, the release builder/operator chooses its
public suffix through the reviewed build-value inputs
`CSE_SHARED_COMPILER_PUBLIC_NAME` and
`CSE_PLATFORM_COMPILER_PUBLIC_NAME`. The generated names are stored in the
workspace and become immutable release presentation:

```text
cse/<shared-public-name>
cse/<platform-public-name>
```

Blueback and Fran currently select `cse/init-GCC` and `cse/init-CCE`. The name
is not discovered from the login shell, `PE_ENV`, the default `PrgEnv`, or the
compiler executable. For the eventual full renderer, the stack/module policy
chooses the `cse` root and the resolved compiler identity deterministically
produces the canonical `cse/GCC` or `cse/CCE` name.

### 4.4 Required front-door behavior

The compiler front door must:

1. reject another CSE release or compiler surface;
2. establish the exact selected compiler chain in reviewed order;
3. expose only that surface's Foundation view, Core modules, Common modules,
   and lane-selector root;
4. avoid exposing package roots for unselected Serial/MPI/GPU lanes;
5. set the same stable `STACK_*` release, compiler, and entry identity used by
   the production reference; and
6. fail clearly through the module engine or provider module when required
   state cannot be established.

The lane module must:

1. require the exact matching compiler front-door identity;
2. conflict with every sibling lane and incompatible CSE identity;
3. activate or require the exact reviewed MPI/runtime chain when applicable;
4. expose only its package module root;
5. set stable lane and view identity; and
6. make a direct load through a manually added lane `MODULEPATH` fail with a
   clear prerequisite diagnostic.

The trial now sets the production-compatible identity variables:

```text
STACK_RELEASE
STACK_COMPILER
STACK_INIT_MODULE
STACK_LANE
STACK_LANE_ID
STACK_VIEW
```

Do not add or override `CC`, `CXX`, `FC`, `MPICC`, `MPIFC`, or `MPIEXEC` in the
hand-authored trial front-door/lane partials until the live wrapper/launcher
contract is approved. The Spack-generated GCC producer module already sets
`CC`, `CXX`, `FC`, and `F77` to exact CSE GCC view paths; preserve and test
that behavior. ReFrame can receive explicit compiler and launcher commands
from its site configuration without adding unrelated guesses to the lane.

### 4.5 Module dependency behavior in the trial

The front door loads the exact compiler modules recorded in values. MPI lane
activation is source-sensitive. When MPI is built by CSE, the selector adds the
provider-module root and loads the exact generated MPI provider module. When
MPI is supplied by the platform, the selector uses an exact `prereq` check and
does not replace the site programming environment. On Cray, the reviewed
compiler front door establishes the selected PrgEnv/CPE chain; the MPI selector
fails clearly if its exact Cray MPICH module is not active.

Use portable Tcl `conflict` for sibling surfaces/lanes and `prereq` to require
the matching front door before a lane loads. Test load, unload, and swap on the
actual Environment Modules/Lmod versions on Blueback and Fran. Do not add
sticky behavior, purge an entire login environment, or infer module names.
The arrays selected from the reviewed static catalog remain authoritative.

### 4.6 Cray compiler and MPI cases

Treat these as distinct activation shapes:

| Shape | Public compile/link interface | MPI/runtime selection | Required proof |
|---|---|---|---|
| CCE + Cray MPICH | Exact reviewed PrgEnv/CCE chain, then `cc`, `CC`, and `ftn` | Matching Cray MPICH flavor and coherent CPE runtime tuple | Driver identity, all Fortran MPI interfaces, library/runtime closure, native multi-node launch |
| CSE GCC Serial | Exact CSE `gcc`, `g++`, and `gfortran`; no ambient PrgEnv compiler selection | No CSE MPI payload is activated | Exact executable paths and compiler-runtime closure |
| CSE GCC + Cray MPICH | Exact CSE GCC commands plus only a validated GNU-flavor MPI wrapper or explicit MPI link interface | Exact compatible Cray MPICH prefix and proven runtime tuple | No `gcc-native` substitution, wrapper expansion selects CSE GCC, libfabric/CXI/PMI closure, native multi-node launch |
| Compiler + CSE-built Open MPI | Exact surface compiler; provider-generated MPI wrappers | Generated Open MPI provider module | Wrapper identity, retained `mpirun`, direct site launcher where configured |
| Prefix-only external MPI | Exact surface compiler; validated prefix interface | Exact prefix/runtime metadata; no invented module requirement | Same compile/link/library/launch evidence as module-backed MPI |

HPE defines `cc`, `CC`, and `ftn` as CrayPE compiler drivers controlled by the
selected programming environment. Use them as the primary public CCE compile
and final-link interface. The raw `craycc`, `crayCC`, and `crayftn` drivers are
appropriate direct compiler paths for controlled build configuration; they are
not the default CPE consumption interface. Cray MPICH also supplies the simple
MPI wrappers `mpicc`, `mpicxx`, and `mpifort`, but HPE explicitly says they do
not replace all CrayPE link behavior. They may be published as secondary CCE
interfaces only after version-specific tests.

The CSE GCC + Cray MPICH case is the sharp edge. HPE documents a driverless
Spack model: exact compiler executable paths with no compiler modules, plus an
exact compiler-flavor Cray MPICH external marked non-buildable and retaining
wrappers. It does not document a general way to retarget `cc`, `CC`, or `ftn`
to an arbitrary CSE-built GCC. Do not load `PrgEnv-gnu` if it selects the site's
`gcc-native`, and do not assume the `cray-mpich` module alone establishes the
right flavor/runtime tuple.

Direct compilation is valid: raw CSE GCC can consume Cray MPICH as an external
library when the build receives the exact headers, libraries, link order,
RPATH/runtime closure, and Fortran modules. Spack also supports builds that use
MPI wrappers. For the latter, the pinned `cray-mpich+wrappers` recipe sets
`MPICH_CC`, `MPICH_CXX`, `MPICH_FC`, `MPICH_F90`, and `MPICH_F77` to Spack's
selected compiler wrappers while building a dependent package. Those Spack
wrappers resolve to the selected CSE GCC and carry dependency search/RPATH
policy. This is how a Spack package can use external Cray MPICH without making
CrayPE `cc`, `CC`, or `ftn` the selected compiler.

That build-time behavior is not automatically a user interface. It exists in
the isolated `spack install` subprocess and is absent after a user merely loads
the current trial's front door and `MPI` selector. Phase 0 must explicitly
publish the consumer interface described next.

The trial's `Serial` selector describes the CSE package DAG and namespace: it
adds no CSE MPI provider or MPI-built package payload. On a CCE surface, the
reviewed platform PrgEnv may already make CPE/MPI commands visible. Record that
platform behavior; do not misclassify it as leakage from the CSE MPI lane and
do not claim that `Serial` removes platform commands.

Launcher identity remains separate from compiler/MPI wrapper identity. The
trial already observed CMake selecting an unrelated ambient MVAPICH2
`mpiexec` while the intended Cray MPICH compiler and libraries were selected.
The trial acceptance record and ReFrame configuration must therefore carry the
approved launch command and arguments explicitly.

### 4.7 CSE GCC MPI consumer interface

Support two consumption contexts for the CSE GCC + Cray MPICH lane:

1. **Spack-managed consumer build.** A generated `cse-spack` consumer command
   or workspace includes the release's exact compiler/MPI toolchain and
   external scopes. A package that depends on MPI is concretized with the CSE
   GCC language providers and the compatible `cray-mpich+wrappers` external.
   Spack owns its temporary compiler-wrapper environment. This is the
   authoritative path for applications that have or receive a Spack package.
2. **Ordinary build through the lane selector.** The workspace candidate module
   exposes the selected Cray MPICH simple wrappers by exact prefix. It publishes
   `mpicc`, `mpicxx`, `mpifort`, `mpif90`, and `mpif77` through `PATH`, records
   their absolute paths in `MPICC`, `MPICXX`, `MPIFC`, `MPIF90`, and `MPIF77`,
   and binds `MPICH_CC`, `MPICH_CXX`, `MPICH_FC`, `MPICH_F90`, and `MPICH_F77`
   to the compiler commands already activated by the CSE GCC front door. It
   never loads compiler-selecting CrayPE `cc`, `CC`, or `ftn` drivers.

The trial values helper now records the selected MPI scope path/module list and,
for external Cray MPICH, separately copies the selected external's exact prefix
and an allow-listed `extra_attributes.environment` record from that scope's
`packages.yaml`. It writes those candidate facts to the initialized workspace's
`presentation/mpi-consumer-candidates.yaml`. The
consumer interface must use the same facts that Spack uses; it must not
rediscover a prefix from ambient modules. The CCE lane may keep its reviewed
module-driven CPE chain, while the CSE GCC lane uses the exact-prefix facts and
must not load a compiler-selecting `PrgEnv-*`.

The implementation now carries those exact-prefix facts into the workspace
candidate selector. The rendered Spack environment input remains byte-for-byte
unchanged when the consumer record is added. The completed locked MPI package
builds establish the build-plane header, link, and runtime closure. The
candidate status is `multi-node-validation-required`, and the presentation
publisher withholds it only from the release module root.

The lane must not replace the exact `CC`, `CXX`, `FC`, and `F77` already
supplied by the GCC producer module. Launcher identity also remains separate
from the compiler-wrapper prefix. Record the approved `srun --mpi=<plugin>` or
Cray native launch command only after live inspection and execution on the
target site.

The stable interface can use either of two implementations:

- `vendor-wrapper`: set exact `MPICH_*` compiler overrides and execute the
  simple wrapper from the selected Cray MPICH flavor prefix. This matches
  Spack's current dependent-build mechanism and is the first Phase 0 candidate.
- `direct`: a fallback that executes raw CSE GCC with MPI headers, libraries,
  link order, RPATH, and runtime inputs generated from the accepted spec. Use
  it only if the selected Cray MPICH flavor does not supply the documented
  simple wrappers.

Record the implementation in `STACK_MPI_INTERFACE`. Do not claim `direct`
when a vendor wrapper is still underneath it. If neither implementation passes
the native multi-node gate, do not copy the CSE GCC MPI selector into the
release module root. Continue using the workspace candidate for validation.

### 4.8 Phase 0 tests

Add both render-time tests and live acceptance:

| Test | Expected result |
|---|---|
| Render shared and platform front doors | Every view/module path uses the selected surface unless a reviewed policy explicitly says otherwise |
| Load from a pristine module session | Exact front door and lane activate; identities and paths match the reviewed trial values |
| Load platform front door | Platform Foundation/Core/Common exposed; shared GCC Core absent |
| Direct lane load | Fails with a clear matching-front-door prerequisite diagnostic |
| Load a second lane/surface/release | Fails with a clear module conflict diagnostic |
| Wrong ambient PrgEnv | Approved swap or exact failure; never a silent mixed compiler |
| Unload/swap | Dependency state and CSE paths restore correctly |
| Serial activation | No CSE MPI provider, MPI-built package namespace, or MPI lane activation is added; any commands inherited from the platform compiler gate are recorded separately |
| Built Open MPI activation | Generated provider and approved launcher resolve |
| External Cray MPICH activation | Exact flavor and runtime tuple resolve; no unrelated launcher |
| Spack-managed CSE GCC MPI consumer | Build log proves Spack's compiler wrappers resolve to the exact CSE GCC and the selected Cray MPICH external |
| CSE GCC MPI candidate identity | `mpicc`, `mpicxx`, `mpifort`, `mpif90`, `mpif77`, and their `MPI*` variables resolve under the recorded prefix; `MPICH_*` selects CSE GCC and no CrayPE compiler driver or `gcc-native` appears |
| CSE GCC MPI native launch | The candidate runs across multiple nodes through the site's approved Slurm MPI plugin or Cray native launcher |
| Compatible package module chain | Loads and runs |
| Incompatible HDF5/NetCDF chain | Prevented or fails clearly |

The live CCE gate additionally compiles and runs C, C++, and Fortran; compiles
`mpif.h`, `use mpi`, and `use mpi_f08`; records wrapper show output; inspects
`readelf`/`ldd`; verifies fabric provider identity; and runs same-node and
multi-node jobs through the native site launcher.

The pilot's safe controls refresh now owns only the workspace `modulefiles/`
and `presentation/` trees in addition to its existing generated controls.
Those paths are separate from the release module root where Spack generates
package modules. The explicit `cse-build publish-modules` action verifies the
existing locks and required views/package-module roots, then atomically copies
only the two CSE front doors and ready lane selectors. It never invokes Spack's
module refresh and cannot bypass the withheld CSE GCC MPI native multi-node
gate. Never edit an accepted release in place.

## 5. ReFrame validation architecture

### 5.1 Configuration model

Generate ReFrame configuration from the release's acceptance manifest rather
than hand-copying compiler/MPI facts into tests.

Use named partitions for execution contexts:

| Partition | Scheduler | Launcher | Purpose |
|---|---|---|---|
| `login-local` | local | local | Module discovery, command/version, compile-only probes allowed by site policy |
| `compute-native` | Slurm/PBS/PBSPro/site backend | exact reviewed launcher | Canonical one-node and multi-node acceptance |
| `compute-flux` | Flux | Flux/reviewed MPI launcher | Optional nested-executor acceptance inside an active Flux instance |

Create one ReFrame programming environment per accepted compiler/lane entry.
Its modules contain only the CSE entrance module (or exact front-door + lane
pair during the transition). Its compiler commands, features, and extras come
from the reviewed trial acceptance record and, later, the full-render release
manifest. Always use an explicit clean-environment policy and explicit stage,
output, report, and performance-log roots.

Useful environment features/extras include:

```text
features: serial | mpi | cray-pe | flux-capable
extras: compiler provider/version, MPI provider/version, release, activation id,
        launcher id, fabric id, CPU target, node role
```

Use fixtures to compile one probe once per programming environment and reuse it
for several runtime shapes. Parameterize only supported release combinations;
list the selected cases before executing to prevent an accidental Cartesian
explosion.

### 5.2 Test layers

| Gate | Layer | What it proves | Release role |
|---|---|---|---|
| G0 | Manifest and module structure | Inputs, expected cases, module files, conflicts, and identities are complete | Required before jobs |
| G1 | Entrance/compiler | Clean activation and C/C++/Fortran consumer builds use the selected surface | Required |
| G2 | Focused package probes | Each public capability and version chain functions | Required for roots in scope |
| G3 | Same-node MPI | MPI language bindings, collectives, and parallel-library behavior work | Required for MPI lane |
| G4 | Native multi-node | Scheduler, launcher, PMI, fabric, and runtime tuple work on target nodes | Required for MPI release |
| G5 | Flux execution | Nested executor schedules equivalent probes correctly | Optional capability; never substitutes for G4 |
| G6 | Application/performance canaries | Real consumers integrate and trend within reviewed tolerances | Initially advisory; promote deliberately |

Every test must emit a sanity verdict. Performance observations remain advisory
until a system/partition reference and tolerance are reviewed. Retries are
allowed only for named operational classes; first-failure evidence is retained.

### 5.3 Package capability matrix

| Package/capability | Focused probe | Context |
|---|---|---|
| Compiler/front door | Clean load, module/command/version identity, exact producer-module `CC`/`CXX`/`FC`, mixed C/C++/Fortran build/run, conflict tests | Login and compute, every surface |
| MPI provider/consumer lane | Spack-managed package evidence plus the exact-prefix wrapper lane; C, C++, `mpif.h`, `use mpi`, and `use mpi_f08`; collectives; backend/compiler/library identity | Two ranks same node and at least two nodes |
| Cray runtime/fabric | Native scheduler launch, launcher/PMI identity, `ldd`/`readelf`, CXI/provider diagnostic | Multi-node Cray |
| zlib/xz/zstd | API or CLI compress/decompress round trip and checksum | One node |
| CMake/Ninja/pkgconf | Configure/build a mixed-language consumer and discover a CSE library through metadata | One node, both CMake versions |
| Git | Local init/commit/checkout/archive; no network | One node |
| Python | Exact interpreter/version, standard library, venv, small compiled extension | One node, all three versions |
| Miniforge | Command/base identity and offline metadata/environment smoke | One node |
| GSL | Numerical integration or root solve with tolerance | One node, both versions |
| SQLite | C API create/insert/query/close plus CLI readback | One node, both versions |
| Netlib BLAS/LAPACK | CBLAS DGEMM plus C/Fortran LAPACK solve and residual | One node, both versions |
| Gnuplot | Headless SVG/PNG generation and nonempty artifact check | One node, both versions |
| HDF5 Serial | C/C++/Fortran and HL create/write/read/verify | One node, both chains |
| HDF5 MPI | `H5Pset_fapl_mpio`, distributed hyperslabs, collective write/read/verify | Same node and multi-node |
| NetCDF-C Serial | Dimensions, variables, attributes, write/read/data verification | One node, both chains |
| NetCDF-C MPI | Parallel NetCDF-4/MPI-IO create, collective access, verify | Same node and multi-node |
| NetCDF-Fortran | Serial and MPI `nf90_*` create/write/read | One node and multi-node |
| NetCDF-CXX4 | C++ create/write/read and exact NetCDF/HDF5-chain identity | One node, both projected chains |
| FFTW Serial | Forward/inverse transform and reconstruction error | One node, both versions |
| FFTW MPI | Distributed transform plus global error reduction | Same node and multi-node |
| Boost Serial | Program Options, Regex, Serialization, header-only System | One node, both versions |
| Boost MPI | Broadcast/reduce and serialized object exchange | Same node and multi-node |
| Dakota | Deterministic optimization, expected objective, Python import, MPI run | One node and multi-node, both versions |
| Module namespace | Expected roots present, private dependencies absent, compatible chains load, incompatible mixes fail | Clean login and compute |

The probes must verify behavior and provenance. Successful output is
insufficient if compilation or runtime resolved an unapproved `/usr/local`,
personal prefix, other CSE release, unrelated MPI launcher, or wrong HDF5 chain.
Capture CMake/pkg-config discovery logs and binary dependency paths.

### 5.4 Cross-library and application canaries

Add a small number of integration tests after the focused probes pass:

1. **CSE I/O mini-application:** MPI domain decomposition, FFTW transform,
   BLAS/LAPACK solve, parallel HDF5/NetCDF output, and readback. This is a
   CSE-owned diagnostic program, not the sole acceptance test.
2. **Quantum ESPRESSO canary:** strong match for Fortran + MPI + FFTW +
   BLAS/LAPACK and scientific/materials workloads.
3. **LAMMPS canary:** strong match for C++ + CMake + MPI and optional FFTW/HDF5
   integration for chemistry/materials workloads.
4. **OpenFOAM canary:** valuable C++/MPI/CFD coverage, but later and lower
   cadence because its build system and ThirdParty bundle can bypass the CSE
   dependencies being tested.

Build canaries from pinned, checksum-verified, pre-fetched source in disposable
validation stages. Force CSE dependencies, fail when a bundled fallback is
used, archive configure/build logs, and audit linked paths. Do not install the
canary into the CSE release or let its dependency manager mutate the release.

Start with the CSE I/O mini-application and one of Quantum ESPRESSO or LAMMPS.
OpenFOAM should not block the first ReFrame adoption.

## 6. Flux execution plan

### 6.1 Role

Flux is a user-owned step scheduler inside resources granted by the site
scheduler:

```text
outer Slurm/PBS/Cray allocation
  -> site launcher starts one Flux broker per selected node
    -> Flux schedules independent locked environment workers and ReFrame jobs
```

The outer scheduler owns queueing, accounting, walltime, and allocation
lifetime. Flux owns only the resources its brokers discover. It must remain an
optional build/validation-driver adapter.

### 6.2 Qualification gates

Before running a CSE build under Flux, prove on each system:

1. Flux is available at the same reviewed path/module on every allocated node.
2. The site permits a single-user nested instance.
3. The approved launcher starts exactly one connected broker per node; no
   singleton fallback occurs.
4. `flux resource info/list` matches the outer allocation's nodes, cores, and
   GPUs after broker reservation.
5. Parent binding does not hide cores/GPUs from HWLOC.
6. Broker overlay networking reaches quorum on the approved interface.
7. Flux state/runtime directories are on suitable storage and do not exhaust a
   small RAM-backed `/tmp`.
8. Outer walltime expiry, cancellation, node loss, and broker failure produce
   understood, recoverable evidence.
9. A multi-node MPI probe uses the selected CSE MPI/runtime and fabric.

Official Flux material gives a concrete Slurm path. PBS and Cray/PALS remain
site-qualified adapters, not assumed support.

### 6.3 Build scheduling

Preserve the existing CSE gates before Flux starts useful work:

1. verify rendered inputs and all eight locks;
2. prove shared prefix/database locking on the real filesystem;
3. fetch sources on the connected context;
4. start and qualify the Flux instance;
5. submit one job per distinct locked environment, never the same environment
   twice;
6. give every job a unique mutable user-cache/stage path and one owner for its
   view/module refresh;
7. set the Spack `-j`/`BUILD_JOBS` budget from the cores assigned to that Flux
   job, retaining memory/linker headroom;
8. wait for all jobs, rerun lock/hash verification, and admit only successful
   lanes to later validation/cache promotion.

The first supported DAG should remain coarse:

```text
verify all locks + filesystem lock gate
    |
    +--> shared Core --------> shared Common / Serial / MPI
    |
    +--> platform Core ------> platform Common / Serial / MPI
    |
    `--> complete-lock/hash verify --> ReFrame acceptance
```

Core-first scheduling reduces cold-cache duplicate work. Spack's shared
prefix/database locks still arbitrate identical hashes. Do not create one Flux
job per Spack DAG node in the first implementation; that would split package
ownership and failure recovery below the existing tested environment seam.

Add a generated, exact worker interface such as:

```text
cse-build compute install --environment <surface/environment-id>
```

It should accept only an environment from the verified workspace manifest and
should perform install, view regeneration, module refresh, permissions, and
evidence capture for that one owner. Flux consumes this interface; it does not
reimplement Spack commands.

### 6.4 ReFrame on Flux

ReFrame has a native `flux` scheduler backend. Run it inside the active Flux
instance with explicit partition configuration, report roots, and resource
requests. Begin with one test and `max_jobs=1`, then raise concurrency only
after resource and filesystem behavior are measured.

Run equivalent high-value MPI tests twice:

- through the native site scheduler/launcher to prove site integration; and
- through Flux to prove the nested path.

Archive the parent allocation ID, Flux URI/instance depth, broker/resource
inventory, Flux job IDs, generated ReFrame scripts, and reports. A passing Flux
run cannot waive a failed native launch.

## 7. Cadence, triggers, and evidence

### 7.1 Cadence

| Cadence | Scope |
|---|---|
| Every render/change request | Schema/render fixtures, front-door/lane golden tests, ReFrame discovery/listing, no real allocation |
| Every restricted/published release | G0-G4 for every supported surface/lane and every public root/version chain |
| Nightly or site-selected frequent run | G1, high-value G2 probes, same-node MPI, one native multi-node smoke per current release |
| Weekly | Full G2-G4 matrix, CSE I/O mini-app, numerical/performance observations |
| Monthly/quarterly | Pinned application canaries, scale/performance trends, cache-only reconstruction/rollback exercise |
| On platform drift | Selective impact run followed by full affected-lane acceptance before reapproval |

### 7.2 Drift triggers

Cluster Inspector/profile and release-manifest diffs should trigger validation
when any of these change:

- CPE/programming environment, compiler, MPI, wrapper, prefix, or module chain;
- libfabric/CXI/UCX/PMI/PMIx/PALS/GTL or scheduler/launcher facts;
- OS, glibc, kernel/driver, CPU target, GPU toolkit/driver/architecture;
- module engine or site default module behavior;
- filesystem mount/locking/execution behavior;
- CSE package recipe, variant, lock hash, build cache, or module entrance contract; or
- ReFrame/Flux version or site integration wrapper.

A compiler/MPI/fabric/CPE change holds affected MPI/GPU lanes until full native
multi-node acceptance passes. A package-only hash change reruns that package's
focused probe, its public dependent chains, and applicable canaries. A module-
presentation-only change reruns the complete clean-session module gate even
when locks are unchanged.

### 7.3 Evidence record

Use deployment-owned evidence roots rather than ReFrame's home-directory
defaults:

```text
evidence/validation/<system>/<release>/<run-id>/
  acceptance-manifest.yaml
  activation/
  reframe/
    run-report.json
    generated-jobs/
    stdout-stderr/
    performance/
  native-scheduler/
  flux/
    instance.txt
    resources.json
    jobs.json
  binaries/
    dependency-audits/
  summary.yaml
```

Every case records system, release, concrete hash/chain, entrance ID,
compiler/MPI/SDK-interface/launcher/fabric identity, node context, scheduler
and job ID, source/test revision, attempt count, status, and artifact paths. Use explicit
statuses: `pass`, `fail`, `blocked`, `not-applicable`. Never turn a missing
allocation or unsupported Flux bootstrap into `pass` or silently skip it.

## 8. Implementation sequence

### Phase 0 - CCE/module entrance gate now

1. Update this design and the trial work log with the entrance assessment.
2. Fix the selected-surface Foundation/Core path defects. **Complete in the
   trial templates.**
3. Add production-compatible CSE identity, exact parent requirements, sibling
   conflicts, and clear module-engine diagnostics to the trial modulefiles.
   **Structural template work complete.**
4. Resolve and validate complete Cray compiler/MPI activation from reviewed
   facts: module-driven CPE for CCE, driverless exact-prefix activation for CSE
   GCC, and a publication hold for any unresolved runtime tuple. **Exact
   external candidate facts and the publication hold are implemented; live
   runtime acceptance remains.**
5. Add the Spack-managed consumer workspace/command and the per-lane CSE MPI
   SDK contract; generate its direct compiler/link interface from the accepted
   concrete spec rather than copying paths into a module template.
6. Decide SDK implementation, wrapper, and launcher commands from live CCE/GCC
   evidence.
7. Add pilot render regressions, then run live load/unload/conflict acceptance
   on both module engines/sites. **Render regressions complete; live acceptance
   remains. The local Lmod HPC lab now covers clean-login compiler activation,
   CSE-built Open MPI activation, exact Cray MPICH prerequisite failure and
   success, direct package dependency loading, and incompatible-version
   conflicts.**
8. Run the real CCE and CSE-GCC clean-shell, consumer-build, and native
   multi-node gates.
9. Add a narrow safe module-presentation refresh or rerender the unaccepted
   publication workspace; do not alter locks or accepted releases. **Narrow
   workspace control-tree refresh and presentation-only publish action are
   implemented.**
10. Record the live system run state instead of leaving the run record blank.

Exit: both compiler surfaces enter the correct per-surface view/module tree;
Serial adds no CSE MPI payload; MPI exposes the exact provider/runtime;
conflicts and unload work; the CSE GCC lane supports both a Spack-managed
consumer and an accepted ordinary-build MPI SDK; CCE language and native
multi-node tests pass; and evidence identifies the compiler, wrapper/link
interface, launcher, and fabric.

### Phase 1 - Minimal ReFrame release gate

1. Define the acceptance manifest from reviewed trial values, catalog facts,
   module-entrance evidence, and release facts; later consume the full-render
   release manifest.
2. Add generated native ReFrame partitions/environments.
3. Port compiler, module, MPI language, native launch, HDF5, NetCDF, FFTW, and
   Dakota smoke probes first.
4. Integrate report/evidence paths with the workspace.
5. Run on one generic Linux system and one Cray system.

Exit: ReFrame exercises the exact published entrance users load and produces a
durable G0-G4 verdict without mutating a release Spack environment.

### Phase 2 - Complete trial package coverage

Implement the package matrix, both approved version chains, dependency-
compatibility module tests, clean consumer discovery audits, and the CSE I/O
mini-application.

Exit: every public root has at least one functional probe; every lane-sensitive
root is tested in its lane; every public version chain has a positive and, where
needed, incompatible-composition test.

### Phase 3 - Flux pilot

1. Add environment-specific `cse-build` worker execution.
2. Qualify a two-node Slurm Flux instance.
3. Schedule distinct locked environments with Core-first dependencies.
4. Run a small ReFrame subset through `scheduler: flux`.
5. Test cancellation, expiry, resume, state paths, and evidence capture.
6. Repeat on PBS/Cray only with site-qualified launch adapters.

Exit: Flux is marked supported only per system where its qualification passes.
Native build/test remains available and authoritative everywhere.

### Phase 4 - Long-lived regression service

Add scheduled cadence, drift-to-impact selection, performance baselines,
Quantum ESPRESSO/LAMMPS canaries, later OpenFOAM, dashboard/report retention,
deprecation policy, and release rollback/reconstruction rehearsals.

## 9. Acceptance criteria for the combined design

The design is implemented when:

- every published compiler/lane has one resolved, evidenced entrance record;
- the pilot templates mimic the documented full-render entrance contract while
  the production renderer remains unchanged by Phase 0;
- a clean user session receives the correct surface-specific Foundation/Core,
  exact compiler/MPI/runtime chain, package namespace, and stable identity;
- another surface/release/lane cannot leak into discovery;
- CSE GCC + Cray MPICH and CCE + Cray MPICH each have explicit, tested runtime
  activation and native launcher identity;
- CSE GCC users can build MPI applications through both the governed Spack
  consumer path and the exact-prefix MPI lane without selecting a site
  compiler;
- every current public root/version chain has a focused functional probe;
- one-node and multi-node MPI test all required C/Fortran interfaces and
  intended fabric/runtime paths;
- ReFrame reports are durable release evidence and never reconcretize the CSE
  release;
- Flux is optional, driver-owned, resource-bounded, and capability-gated per
  system;
- native scheduler acceptance remains required even where Flux passes; and
- drift in an explicit system external or module entrance contract holds affected lanes
  until the required regression scope passes.

## 10. Related documents

- [ReFrame and Flux primary-source research](reframe_flux_primary_source_research_v1.md)
- [Cray wrapper consumption primary-source research](cray_wrapper_consumption_primary_source_research_v1.md)
- [Initial Conversion Trials build execution model](initial_conversion_trials_build_execution_model_v1.md)
- [Initial Conversion Trials build findings](initial_conversion_trials_build_findings_v1.md)
- [Lane and module model](lane_and_module_model_v1.md)
- [Foundation/Core view semantics](foundation_core_view_semantics_note_v1.md)
- [Post-trial CSE consumption environment](post_trial_cse_consumption_environment_plan_v1.md)
- [Spack 1.2 concretizer cache and Cray PE runtime](spack_1_2_concretizer_cache_and_cray_pe_runtime_note_v1.md)
- [Cray PE acceptance checklist](cray_pe_acceptance_checklist_v1.md)
- [Generic Linux acceptance checklist](generic_linux_acceptance_checklist_v1.md)
- [Stack build handoff](stack_build_handoff_note_v1.md)
- [Stack generation orchestration](stack_generation_orchestration_note_v1.md)
