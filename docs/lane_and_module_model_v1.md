# Lane And Module Model v1

The lane, toolchain, exposure, and module model for the stack-generation system.
Recovered from the retired v6 design and reconciled to the current
provider/defaults vocabulary (no `contract`/`toolchain`-as-contract/`vendor_cray`).
Read `CONTEXT.md` first for the term definitions; this doc is the working model
those terms describe. Foundation/core *view* semantics live in
`foundation_core_view_semantics_note_v1.md`; the input/render method lives in
`stack_generation_structure_v1.md`.

## Provenance vocabulary

Every user-facing package has a provenance class, surfaced in its modulefile:

| Provenance | Meaning |
|---|---|
| `Stack-built` | Built by Spack as part of this managed stack (explicit stack policy/fork). |
| `Platform-backed` | Provided by the platform/vendor, exposed through the stack (e.g. Cray PE). |
| `Site-external` | Provided by the site, registered as a Spack external. |
| `Spack-built` | Built from an upstream recipe with no special stack ownership. |

## Lanes

A **lane** is one rendered build target: a single (compiler × optional MPI
provider × optional GPU arch) at a chosen CPU target. Each lane is a normal,
independently-concretized Spack environment with its **own `spack.yaml`,
lockfile, view, and module root** (e.g. `gcc/core`, `cce/mpi-craympich`,
`gcc/gpu-craympich-gfx942`). If the profile has multiple versions of one
compiler family, an exact compiler selection such as `aocc@4.2.0` gets a
versioned lane axis such as `aocc420` so environment paths and toolchain names
do not collide.

**Lanes are derived, not enumerated.** The renderer computes the lane set by
resolving `profile ∩ defaults ∩ per-build override` (compilers × MPI provider ×
GPU archs × runtime nodes). There is no stored lane list. `stack.yaml`
`per_system:` blocks only **prune** the derived set; they cannot add a lane the
derivation wouldn't produce. A missing lane means the gap is in `profile.yaml` or
`defaults.yaml`.

### Lane kinds (tiers)

| Kind | Purpose | Built/exposed |
|---|---|---|
| **foundation** | build tools + stable-ABI low-level libs (cmake, ninja, pkgconf, zlib, xz, zstd) | once per compiler; **view**-exposed (+compiler) |
| **core** | only-serial-by-nature packages (`gsl`; no MPI implementation exists) plus compiler-agnostic building blocks (`python`, `miniforge`, `cmake`) | compiler-init **view**; tools loadable |
| **serial** | MPI-*capable* package built without MPI by choice (`hdf5~mpi`) | module |
| **mpi** | built with MPI (osu, `hdf5+mpi`) | module |
| **gpu** | GPU backend (`+rocm`/`+cuda`), over GPU-aware MPI | module |

Placement rules (2026-07-08): serial means the package *could* build against
MPI and the stack deliberately offers the MPI-less build too; a package with no
MPI implementation at all is core, not serial. Edge cases are decided by the
second core criterion (compiler-agnostic): `openblas` has no MPI but is
compiler/performance-sensitive, so it stays payload-serial; `gnuplot` likewise
(decided 2026-07-13); it must be built with the surface's compiler for
library compatibility, so it is not compiler-agnostic and cannot be Core.
Open team question, recorded not decided: MPI built
for one rank can subsume a serial build, so the serial tier could in principle
collapse into MPI; CSE keeps the explicit serial tier for now.

Open team question (2026-07-14, Ravon): GPU-built, non-MPI packages. Today
the GPU lane is "the MPI roster plus the GPU payload", and its payload
(kokkos) is MPI-adjacent. Eventually a package will be GPU-accelerated but
have nothing to do with MPI. Where does it live (GPU lane only? a
GPU-analog of the serial/common split?), what does its kind derivation look
like, and does the common-compiler-dependent exposure rule need a GPU
counterpart? Needs semantics before the first such package lands.

**Lane-agnostic payload exposure (decided 2026-07-13).** Where a package is
*built* and where it is *visible* are separate axes. Packages that are
non-core (not compiler-agnostic: compiler- or performance-sensitive) but
lane-agnostic (no MPI implementation exists for `openblas`, `netlib-lapack`,
`gnuplot`, so serial and MPI code link the same build) build
exactly once, in the compiler column's serial lane, and are module-exposed in
*every* payload lane of that column: Serial, MPI, and GPU. No rebuild, no new
loadable layer, and the lane conflicts stand unchanged; without this, an MPI
user had no loadable BLAS/LAPACK at all. Mechanics: the package set declares
`lane_agnostic:` names (schema-validated to be serial-only root specs); the
serial lane's environment emits their modulefiles into a per-compiler shared
module root (`…/<compiler>/shared`, a Spack second module set with an
include whitelist) and excludes them from its own lane root; every payload
lane selector module prepends the shared root below its own lane root. A
stack that skips the serial kind renders with a recorded warning (the
declaration is vacuous there); two serial lanes in one column declaring
lane-agnostic packages is a hard render error (one shared root, one owner).
`boost` is deliberately **not** on the list: it is MPI-capable, so it is a
dual-build package (`~mpi` in serial, `+mpi` in MPI, same clean name) like
HDF5 and FFTW (decided 2026-07-13). Validation enforces the boundary: a
lane_agnostic name with root specs in any non-serial kind is a render error.

**User-facing statement of the model (2026-07-13).** The Serial lane
contains two distinct classes of software: common compiler-dependent
packages, and non-MPI configurations of packages that also support MPI.

Common compiler-dependent packages (BLAS/LAPACK, gnuplot) are made
available in the Serial, MPI, and GPU lanes, because the lanes are mutually
exclusive and applications in each lane may require those packages. They
are built once, in the Serial lane, and every lane sees the same install.

Non-MPI configurations are not automatically propagated beyond the Serial
lane. When an MPI-enabled configuration of the same package is selected for
the MPI or GPU lane's roster, that configuration is what the lane's users
see, under the same clean module name, never a suffixed one. For example:
Serial users get `boost` built without MPI; MPI and GPU users get `boost`
built with MPI, because those rosters select the `+mpi` build. Serial FFTW
exists only in the Serial lane; the MPI and GPU lanes carry MPI-enabled
FFTW. Consequence for rosters: the gpu kind selects the MPI-enabled roster
alongside the GPU payload, keeping GPU a superset of the MPI lane's runtime
surface (identical specs reuse the same installs by hash; no rebuilds).

The rejected alternative, recorded for the record (2026-07-13): appending
the lane to the public module name (`fftw-serial`, `fftw-mpi`). Names carry
facts only when the user still has a choice to make; inside a loaded lane
the choice is already made, and suffixed names reintroduce the flat-surface
failure mode (users must know which variant to type, and nothing but
convention stops the wrong one).

A simple stack may use one payload lane and no separate Core. Variant-rich stacks
use front-door compiler-init and lane modules so a user enters one compiler
surface and then picks exactly one serial/MPI/GPU lane.

**Lane naming convention (2026-07-09, supersedes the 07-08 note):** two
naming layers, one rule.

- **Internal lane ids** (rendered environment directories, lockfiles,
  manifests) always carry the full facts:
  `{build-name}[-{mpi-provider}][-{gpu-arch}]`, e.g.
  `gpu-craympich-gfx942`. Machines and oracle diffs want everything spelled
  out; these never reach users.
- **Public module names** use a compiler front door plus compiler-specific lane
  names: `cse/<Compiler>` followed by `<Lane>` from the MODULEPATH exposed by
  that compiler: `cse/GCC` then `Serial`, `MPI`, or `GPU`. Lane names are
  **qualified only when the system is ambiguous**: two MPI implementations →
  `MPI-openmpi` / `MPI-mpich` (and a GPU lane per MPI, since GPU codes ride
  one); two GPU architectures → `GPU-gfx90a` / `GPU-gfx942` (Blueback's
  MI250X + MI300A case). One implementation → unqualified. The remaining
  facts (exact MPI version, fabric, GPU-awareness) live in `module whatis`
  / `module help` metadata, not in the name. This is the same
  qualify-only-when-ambiguous principle toolchain names already follow.
- Never name a lane by its contents (`GPU`, not `GPU-kokkos`); name a build
  after its kind unless a stack fans out several builds of one kind.
- `Core` loads with the compiler surface; it is not a chooseable lane.

### Per-compiler Core (committed)

Every compiler owns its own Core environment/view/module root (`gcc/core`,
`cce/core`, …). A shared cross-compiler Core does not work under per-lane builds:
two compilers' `cmake/3.30.5` are disjoint binaries but a single shared view has
one path for that name+version. Per-compiler view roots remove the collision
honestly. Cost: build tools + stable-ABI libs are duplicated per compiler,
acceptable on these systems; a shared-Core extraction is an evidence-gated future
optimization, not a dependency. (This is "Option B / squeezed Core" in
`foundation_core_view_semantics_note_v1.md`.)

### Layer composition

| Layer | Conflicts with siblings? | Composes with |
|---|---|---|
| compiler (precondition) | selected first via the front-door | its own column |
| `<compiler>/core` | no | every lane in the same compiler column |
| serial | yes, with mpi/gpu in the column | the compiler's Core |
| mpi | yes, with serial/gpu in the column | the compiler's Core |
| gpu | yes, with serial/(non-gpu)mpi + incompatible gpu | the compiler's Core |

A **dual-build package** (HDF5, NetCDF-C, PnetCDF) lives in *both* serial and MPI
lane views under the same clean name (`hdf5`), never `hdf5-mpi`. The loaded lane
decides which build is visible; the lane is the prefix, expressed as MODULEPATH
position. The serial/mpi conflict blocks only mistakes (header/pkg-config bleed,
linking serial into MPI), never a real workflow.

## Targets (per tier)

- **foundation/core**: a fixed conservative baseline (e.g. `x86_64_v2`),
  unoptimized, built once, shared.
- **CPU payload (serial/mpi)**: ONE build at the **lowest-common-denominator**
  uarch across the CPU runtime nodes (the highest target that runs on all of
  them). Not per-uarch fan-out.
- **GPU payload**: fan out per GPU node type, each **optimized to that node's
  exact arch** (e.g. `gfx942`); the GPU node's CPU target is that node's uarch.
- **Global override**: "build everything at one baseline" for testing/portability
  (used by Blueback run #1).

## Why GPU is its own kind (not an MPI sub-type)

A GPU lane *is* an MPI lane plus GPU-arch-pinned packages, a **superset** scoped
to one GPU class. It stays a distinct kind because: runtime targeting differs (GPU
partition + a runtime `rocm/cuda` prereq); GPU arch is a **build-time pin**
(`kokkos+rocm amdgpu_target=gfx942` ≠ `…gfx90a`, different hashes → two lanes);
one front-door per partition target is the clean user story; and "pick exactly one
lane" stays the whole mental model. A GPU-only code with no MPI still loads the GPU
lane (unused MPI symlinks are cheap) rather than doubling the matrix with a
GPU-no-MPI kind.

## Host-compiler policy for GPU lanes: three compiler shapes

Device performance is controlled by the GPU toolchain (hipcc/nvcc), not the host
compiler, so the default GPU lane uses a general-purpose host:

| Compiler shape | Tuple | Coverage |
|---|---|---|
| **CPU host** | (compiler, mpi) | wide |
| **GPU + general host** (committed default) | (host_compiler, mpi, gpu_toolkit) | wide + GPU-toolkit-pinned subset |
| **GPU-aware compiler** (opt-in specialist) | (nvhpc/rocmcc, mpi) | restricted to specs that need the vendor compiler |

On Cray this maps to **Option B** (general-purpose `PrgEnv` + standalone GPU
toolkit module, e.g. `PrgEnv-gnu` + `rocm/6.x`) as the committed default; **Option
A** (`PrgEnv-amd`/`PrgEnv-nvidia` all-in-one) is the narrow specialist lane.
Slugs: CPU host `<compiler>-<mpi>`; general GPU host
`<host>-<mpi>-<toolkit>`; GPU-aware compiler
`<gpu_compiler>-<mpi>`. Compiler-family purity: if a lane's compiler can't build a
spec, drop it from the lane and document why; never silently reroute to another
compiler.

## Toolchain: compiler-matched MPI binding

A **toolchain** binds a compiler to its matching MPI build so a concrete spec
materializes correctly. The canonical case: Cray `cray-mpich` ships per-compiler
(per-PrgEnv) builds at distinct prefixes:

```
cray-mpich@8.1.29 %cce    -> /opt/cray/pe/mpich/8.1.29/ofi/cray/17.0
cray-mpich@8.1.29 %gcc    -> /opt/cray/pe/mpich/8.1.29/ofi/gnu/13.3
cray-mpich@8.1.29 %rocmcc -> /opt/cray/pe/mpich/8.1.29/ofi/amd/6.0
```

**Realization in the current model:** each lane is a per-compiler environment.
The MPI provider scope emits two related Spack config files:

- `packages.yaml` declares the concrete MPI externals, including per-compiler
  flavor specs such as `cray-mpich@v %gcc` when the underlying binary really is
  compiler-specific.
- `toolchains.yaml` declares named toolchains such as
  `gcc1330_craympich8129`; applicable root specs are decorated with
  `%gcc1330_craympich8129` so Spack applies the compiler and MPI binding
  atomically.

On a single CPE this pins the current compiler/MPI pair. Across CPE versions,
tag providers with `cpe_version` and bind on matching version (deferred; run #1
= latest CPE only).

**Toolchain naming and same-name multi-version MPI (generic Linux).** Toolchain
names are Spack-spec-token-safe slugs: package names and versions are folded to
letters/numbers only because the name is referenced as `%<toolchain_name>` in
root specs. When versions are known, the key includes both compiler and MPI
versions, e.g. `aocc420_openmpi503` or `gcc1330_craympich8129`. This avoids two
classes of collision: multiple compiler versions for one family, and multiple
MPI versions for one provider. A build that resolves to an ambiguous provider
name must set `mpi.version` in `stack.yaml`; unpinned ambiguity is a hard render
error, never a silent first-match pick or a silent skip. Build-sourced
(Spack-built) MPI lanes get a toolchain too, pinning the provider but not the
MPI version (`%mpi=openmpi`); the scope's `packages.yaml` `mpi:` requirement
keeps the lane's provider singular while Spack resolves the version.

**Externals carry no `%compiler`**: an external is a pre-existing binary the stack
didn't build. The **only** exception is Cray PE per-flavor `cray-mpich`, where
`%compiler` names which real binary the spec refers to (the per-flavor `prefix:`
makes it observable). A site MPI built once and reused has no `%compiler`; only
genuinely per-compiler site builds at separate prefixes get the annotation.

Do not replace toolchain binding with `packages.all.require: ["%gcc"]`. That
over-constrains non-compiler system externals. Compiler/MPI lane binding belongs
in `toolchains.yaml` plus the root spec's `%<toolchain_name>` decoration.

## Externalization

| Posture | Use |
|---|---|
| `buildable: false` | force external (vendor MPI, compilers, system-coupled) |
| `buildable: true` + `require`/`prefer` | steer toward the external, build if needed |

- **Strict tier (`buildable: false`):** by default only **openssl + curl** among
  general Linux libs (site patches them; don't duplicate the CVE treadmill).
  Vendor compilers/MPI, glibc, the Spack-running Python may also be force-external
  as platform contracts.
- **Hint tier (`buildable: true`):** other detected libs (PMIx, libfabric, UCX,
  hwloc, …) are hints the solver may reuse or rebuild. Carry version floors in the
  consumer root spec (`mpich ^pmix@4`), not in the external.
- **`modules:` vs `prefix:`**: prefer `prefix:` (deterministic, no live-module
  coupling). Use `modules:` only for the sanctioned vendor case (Cray PE compilers
  + cray-mpich) where the modulefile establishes env a bare prefix can't.

## Exposure and module generation

Exposure rule (from `CONTEXT.md`): **lane-independent foundation/core → compiler
view (+ compiler); lane-sensitive payload → lane modules.** Two exposure modes:

- **`front_door`** (variant-rich): user loads one compiler surface module
  (`cse/GCC`), then one lane module (`MPI`), then package
  modules from that lane's root.
- **`direct`** (small app stacks): public package modules published directly under
  `modules.publish_root`; the direct module carries the conflict/runtime-prereq
  policy a front-door would.

In `front_door` mode, the front-door module is a compiler environment gate. For
example, `cse/GCC` establishes the GCC compiler layer, exposes
the compiler-specific foundation/core view, and prepends the module root where
the available lane modules for that compiler live. It must not prepend package
module roots for every MPI/GPU/serial lane. A lane module is the isolation seam:
after the user loads one lane module, only that lane's package-module root is
visible.

The user-facing hierarchy is intentionally short:

```text
cse/GCC
  ├─ exposes the GCC foundation/core view
  └─ exposes lane modules
       ├─ Serial
       ├─ MPI
       └─ GPU
            └─ exposes package modules for that lane
```

Do not nest lane selector files under the compiler-init module name in the lane
MODULEPATH. With Lmod, loading `cse/GCC` and then adding a tree containing
`cse/GCC/Serial` changes `cse/GCC` from a leaf into a parent while it is being
loaded, which can trigger repeated module reloads. The compiler-specific
MODULEPATH already supplies the namespace boundary, so short selector names are
both unambiguous and safe.

Foundation/core view contents are conservative: build tools and base libraries
that are safe for every lane under that compiler, such as `cmake`, `zlib`, `xz`,
and `zstd`. Do not put MPI-dependent, GPU-dependent, or otherwise lane-sensitive
packages in this view.

If multiple versions of a foundation/core package are present in the stack,
choose one visible version for the compiler init view. Prefer the version chosen
by the foundation/core concretization for that compiler, normally the newest
compatible version selected by the solver. Additional versions may exist as
build dependencies or lane internals, but they should not all be exposed from the
init module. Version fan-out belongs behind lane modules or package-specific
module names, not in the compiler init view.

**Generation (Q4):** render emits a `modules.yaml` scope (driven by tier
visibility: foundation/core selected for the compiler view, payload=public,
and `deployment.module_root`) plus the front-door/direct module templates; the
build path runs `spack -e <env> module tcl refresh` to emit the package
modulefiles. Spack makes package modules; render makes compiler init and lane
modules. Tcl is the portable baseline (readable by both Environment Modules and
Lmod); Lmod specifics can layer on later.

### Compiler surface module anatomy

```tcl
#%Module1.0
module-whatis "cse compiler surface: GCC"

# Compiler/platform prereqs for this compiler layer
prereq gcc-native/13

# Foundation/core view: compiler + selected lane-independent tools/libs
prepend-path PATH             ".../views/gcc/foundation/bin"
prepend-path CPATH            ".../views/gcc/foundation/include"
prepend-path LIBRARY_PATH     ".../views/gcc/foundation/lib"
prepend-path LD_LIBRARY_PATH  ".../views/gcc/foundation/lib"

# Make lane modules visible, but not lane package modules
prepend-path MODULEPATH ".../modules/gcc/lanes"
```

### Lane module anatomy

```tcl
#%Module1.0
module-whatis "Science stack lane: GCC + cray-mpich 8.1.29"

# Conflicts — generated from the resolved lane plan; one per sibling lane
conflict Serial
conflict MPI
conflict GPU

# Platform-module prerequisites for this lane
prereq cray-mpich/8.1.29

# Stack identity
setenv STACK_RELEASE   "2026.06"
setenv STACK_COMPILER  "GCC"
setenv STACK_MODE      "mpi"
setenv STACK_VIEW      ".../views/gcc/mpi-craympich"

# Expose package modules for this lane only
prepend-path MODULEPATH ".../modules/gcc/mpi-craympich/packages"
```

`module swap` between lanes works; `module load` of a second lane fails loudly via
the conflict block (no Lmod `family` dependency). The conflict list is rendered,
never hand-maintained.

### Lane runtime module requirements

Follows from how the lane's externals were provided:
- **module-provided external lane** (Cray PE compiler + cray-mpich) → the lane module
  requires those platform modules (`prereq`/check by default; `autoload` only if
  the site opts in). RPATH covers the stack's own binaries, not a user's fresh
  compile or the launcher's search.
- **prefix-only site external** → no automatic module load (exposed via the view);
  require an MPI module only if the external declares one in `modules:`.
- **fully Spack-built lane** → self-contained; no platform prereqs.

Verify per lane with `ldd` whether PE/site runtime libs resolve via RPATH (light
lane module) or need the external's `LD_LIBRARY_PATH` (lane module must require
the modules). Record the answer on a new lane's first build.

### Package module dependency compatibility

Clean package module names are the user-facing goal, but clean names must not
allow users to compose incompatible dependency versions. A stack can expose
multiple versions of related packages in the same lane, especially with
independently concretized package groups. The module layer must therefore carry
the resolved dependency relationship for version-sensitive public dependencies.

Rule: a package module that exposes a version-sensitive public dependency must
either load, prereq, or conflict against the exact dependency module family it
was built and tested with. Do this only where the dependency relationship is
part of the public runtime or build interface; do not over-constrain packages
whose dependencies are private, ABI-stable for the supported range, or already
isolated by RPATH.

Examples:

- `netcdf-c` built against `hdf5 +mpi` must not be loadable beside an
  incompatible `hdf5` module from the same lane.
- `netcdf-fortran` must preserve the compatible `netcdf-c` relationship.
- Parallel HDF5, PnetCDF, MPI-dependent I/O stacks, and GPU-enabled libraries
  should be treated as version-sensitive until proven otherwise.

The preferred user experience is still:

```text
module load cse/GCC
module load MPI
module load netcdf-c/4.9.3
```

The user should not have to know which HDF5 version is compatible. The
`netcdf-c/4.9.3` module carries that relationship internally through modulefile
metadata and checks.

Implementation source of truth: dependency constraints come from the per-lane
lockfile/install metadata plus stack policy identifying which package
relationships are public and version-sensitive. They are not hand-authored in
package modules.

Definition of done for module publication:

- package module generation has access to the resolved dependency chain for the
  lane being published;
- version-sensitive package modules encode compatible dependency requirements;
- incompatible manual load combinations fail clearly or are prevented by module
  prerequisites;
- compatible load chains are covered by module smoke tests.

### Provenance in modulefiles

Every package module emits its class so `module avail`/`help` show it:

```tcl
setenv STACK_PACKAGE_PROVENANCE Platform-backed
module-whatis "netcdf-c 4.9.3 (Platform-backed via Cray PE)"
```

Render derives the class from `packages.yaml`: `buildable: false` + Cray PE prefix
→ Platform-backed; `buildable: false` + non-PE prefix → Site-external; otherwise
Stack-built (explicit policy/fork) or Spack-built (unmodified upstream).

## Build order

The foundation neck is **sequential on purpose**: bottom compiler → stack-built
compiler (cached) → that compiler's Core (cached) → fan out its payload lanes.
Different compiler chains run in parallel once their bottom compiler exists.

- **Cold-cache race trap:** launching every lane in parallel on a cold cache makes
  each lane concretize+build CMake under its own compiler simultaneously (the
  per-prefix lock never engages; different prefixes). Build + cache the foundation
  Core first as an explicit checkpoint, *then* fan out so each lane pulls CMake
  from the cache.
- **Push to cache after every successful step** (first run included): the cache is
  the cross-run progress checkpoint; a small DAG change then rebuilds only the
  changed spec.
- **build_stage** on a fast local exec path (reject `noexec`); `install_tree` +
  `source_cache` on shared storage; honor Spack `config:install_tree:padded_length`
  so cached binaries relocate.
- First run is for **correctness** (serial-ish, one lane proven end-to-end); the
  multi-node fan-out is the steady-state speed optimization.
