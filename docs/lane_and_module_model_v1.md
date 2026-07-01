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
lockfile, view, and module root** — e.g. `gcc/core`, `cce/mpi-craympich`,
`gcc/gpu-craympich-gfx942`.

**Lanes are derived, not enumerated.** The renderer computes the lane set by
resolving `profile ∩ defaults ∩ per-build override` (compilers × MPI provider ×
GPU archs × runtime nodes). There is no stored lane list. `stack.yaml`
`per_system:` blocks only **prune** the derived set — they cannot add a lane the
derivation wouldn't produce. A missing lane means the gap is in `profile.yaml` or
`defaults.yaml`.

### Lane kinds (tiers)

| Kind | Purpose | Built/exposed |
|---|---|---|
| **foundation** | build tools + stable-ABI low-level libs (cmake, ninja, pkgconf, zlib, xz, zstd) | once per compiler; **view**-exposed (+compiler) |
| **core** | compiler-adjacent infrastructure exposed for use | compiler-init **view** |
| **serial** | MPI-*capable* package built without MPI by choice (`hdf5~mpi`) | module |
| **mpi** | built with MPI (osu, `hdf5+mpi`) | module |
| **gpu** | GPU backend (`+rocm`/`+cuda`), over GPU-aware MPI | module |

A simple stack may use one payload lane and no separate Core. Variant-rich stacks
use front-door compiler-init and lane modules so a user enters one compiler
surface and then picks exactly one serial/MPI/GPU lane.

### Per-compiler Core (committed)

Every compiler owns its own Core environment/view/module root (`gcc/core`,
`cce/core`, …). A shared cross-compiler Core does not work under per-lane builds:
two compilers' `cmake/3.30.5` are disjoint binaries but a single shared view has
one path for that name+version. Per-compiler view roots remove the collision
honestly. Cost: build tools + stable-ABI libs are duplicated per compiler —
acceptable on these systems; a shared-Core extraction is an evidence-gated future
optimization, not a dependency. (This is "Option B / squeezed Core" in
`foundation_core_view_semantics_note_v1.md`.)

### Layer composition

| Layer | Conflicts with siblings? | Composes with |
|---|---|---|
| compiler (precondition) | selected first via the front-door | its own column |
| `<compiler>/core` | no | every lane in the same compiler column |
| serial | yes — with mpi/gpu in the column | the compiler's Core |
| mpi | yes — with serial/gpu in the column | the compiler's Core |
| gpu | yes — with serial/(non-gpu)mpi + incompatible gpu | the compiler's Core |

A **dual-build package** (HDF5, NetCDF-C, PnetCDF) lives in *both* serial and MPI
lane views under the same clean name (`hdf5`) — never `hdf5-mpi`. The loaded lane
decides which build is visible; the lane is the prefix, expressed as MODULEPATH
position. The serial/mpi conflict blocks only mistakes (header/pkg-config bleed,
linking serial into MPI), never a real workflow.

## Targets (per tier)

- **foundation/core** — a fixed conservative baseline (e.g. `x86_64_v2`),
  unoptimized, built once, shared.
- **CPU payload (serial/mpi)** — ONE build at the **lowest-common-denominator**
  uarch across the CPU runtime nodes (the highest target that runs on all of
  them). Not per-uarch fan-out.
- **GPU payload** — fan out per GPU node type, each **optimized to that node's
  exact arch** (e.g. `gfx942`); the GPU node's CPU target is that node's uarch.
- **Global override** — "build everything at one baseline" for testing/portability
  (used by Blueback run #1).

## Why GPU is its own kind (not an MPI sub-type)

A GPU lane *is* an MPI lane plus GPU-arch-pinned packages — a **superset** scoped
to one GPU class. It stays a distinct kind because: runtime targeting differs (GPU
partition + a runtime `rocm/cuda` prereq); GPU arch is a **build-time pin**
(`kokkos+rocm amdgpu_target=gfx942` ≠ `…gfx90a`, different hashes → two lanes);
one front-door per partition target is the clean user story; and "pick exactly one
lane" stays the whole mental model. A GPU-only code with no MPI still loads the GPU
lane (unused MPI symlinks are cheap) rather than doubling the matrix with a
GPU-no-MPI kind.

## Host-compiler policy for GPU lanes — the three lane kinds

Device performance is controlled by the GPU toolchain (hipcc/nvcc), not the host
compiler, so the default GPU lane uses a general-purpose host:

| Kind | Shape | Coverage |
|---|---|---|
| **Kind-1 — pure CPU** | (compiler, mpi) | wide |
| **Kind-2 — GPU + general host** (committed default) | (host_compiler, mpi, gpu_toolkit) | wide + GPU-toolkit-pinned subset |
| **Kind-3 — GPU-aware compiler** (opt-in specialist) | (nvhpc/rocmcc, mpi) | restricted to specs that need the vendor compiler |

On Cray this maps to **Option B** (general-purpose `PrgEnv` + standalone GPU
toolkit module, e.g. `PrgEnv-gnu` + `rocm/6.x`) as the committed default; **Option
A** (`PrgEnv-amd`/`PrgEnv-nvidia` all-in-one) is the narrow Kind-3 exception lane.
Slugs: Kind-1 `<compiler>-<mpi>`; Kind-2 `<host>-<mpi>-<toolkit>`; Kind-3
`<gpu_compiler>-<mpi>`. Compiler-family purity: if a lane's compiler can't build a
spec, drop it from the lane and document why — never silently reroute to another
compiler.

## Toolchain — compiler-matched MPI binding

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
- `toolchains.yaml` declares named toolchains such as `gcc_craympich`; applicable
  root specs are decorated with `%gcc_craympich` so Spack applies the compiler
  and MPI binding atomically.

On a single CPE this pins the current compiler/MPI pair. Across CPE versions,
tag providers with `cpe_version` and bind on matching version (deferred; run #1
= latest CPE only).

**Toolchain naming and same-name multi-version MPI (generic Linux).** Toolchain
names stay unversioned (`gcc_craympich`, `gcc_openmpi`) while a provider name
maps to exactly one version on the system — the versions are pinned inside the
toolchain entries, and Spack's own examples use unversioned names. When a
profile reports the *same provider name at more than one version* (two openmpi
installs on a generic Linux box — a real case Cray never hits, since one CPE
carries one pairing), the name alone would collide as a YAML key and one
version would silently vanish. So: (1) each version's toolchain key carries its
version (`aocc_openmpi_4.1.6`, `aocc_openmpi_5.0.3`) so both pairings render;
(2) a build that resolves to an ambiguous provider name must set `mpi.version`
in `stack.yaml` — unpinned ambiguity is a hard render error, never a silent
first-match pick or a silent skip; (3) build-sourced (Spack-built) MPI lanes
get a toolchain too, pinning the provider but not the version
(`%mpi=openmpi`) — the scope's `packages.yaml` `mpi:` requirement keeps the
lane's provider singular while Spack resolves the version.

**Externals carry no `%compiler`** — an external is a pre-existing binary the stack
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
- **`modules:` vs `prefix:`** — prefer `prefix:` (deterministic, no live-module
  coupling). Use `modules:` only for the sanctioned vendor case (Cray PE compilers
  + cray-mpich) where the modulefile establishes env a bare prefix can't.

## Exposure and module generation

Exposure rule (from `CONTEXT.md`): **lane-independent foundation/core → compiler
view (+ compiler); lane-sensitive payload → lane modules.** Two exposure modes:

- **`front_door`** (variant-rich): user loads one compiler init module
  (`science_init_gcc`), then one lane module (`science/mpi`), then package
  modules from that lane's root.
- **`direct`** (small app stacks): public package modules published directly under
  `modules.publish_root`; the direct module carries the conflict/runtime-prereq
  policy a front-door would.

In `front_door` mode, the site/init/bootstrap module is a compiler environment
gate. For example, `science_init_gcc` establishes the GCC compiler layer, exposes
the compiler-specific foundation/core view, and prepends the module root where
the available lane modules for that compiler live. It must not prepend package
module roots for every MPI/GPU/serial lane. A lane module is the isolation seam:
after the user loads one lane module, only that lane's package-module root is
visible.

The user-facing hierarchy is intentionally short:

```text
science_init_gcc
  ├─ exposes the GCC foundation/core view
  └─ exposes lane modules
       ├─ science/serial
       ├─ science/mpi
       └─ science/gpu
            └─ exposes package modules for that lane
```

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
visibility — foundation/core selected for the compiler view, payload=public —
and `deployment.module_root`) plus the front-door/direct module templates; the
build path runs `spack -e <env> module tcl refresh` to emit the package
modulefiles. Spack makes package modules; render makes compiler init and lane
modules. Tcl is the portable baseline (readable by both Environment Modules and
Lmod); Lmod specifics can layer on later.

### Compiler init module anatomy

```tcl
#%Module1.0
module-whatis "Science stack GCC compiler environment"

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
conflict science/serial
conflict science/mpi
conflict science/gpu

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

### Provenance in modulefiles

Every package module emits its class so `module avail`/`help` show it:

```tcl
setenv STACK_PACKAGE_PROVENANCE Platform-backed
module-whatis "netcdf-c 4.9.2 (Platform-backed via Cray PE)"
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
  per-prefix lock never engages — different prefixes). Build + cache the foundation
  Core first as an explicit checkpoint, *then* fan out so each lane pulls CMake
  from the cache.
- **Push to cache after every successful step** (first run included) — the cache is
  the cross-run progress checkpoint; a small DAG change then rebuilds only the
  changed spec.
- **build_stage** on a fast local exec path (reject `noexec`); `install_tree` +
  `source_cache` on shared storage; honor Spack `config:install_tree:padded_length`
  so cached binaries relocate.
- First run is for **correctness** (serial-ish, one lane proven end-to-end); the
  multi-node fan-out is the steady-state speed optimization.
