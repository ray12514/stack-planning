# CONTEXT — stack-generation domain glossary

Shared vocabulary for the four-repo stack-generation system (cluster-inspector,
stack-composer, stack-content, stack-planning). stack-planning is the definition
center, so the glossary lives here. Terms only — no implementation detail.

## Tiers

A package's **tier** says both how it is built and how it is exposed. There are
two *base* tiers (foundation, core) beneath three *payload* tiers (serial, mpi,
gpu).

- **Foundation** — base libraries and build substrate, off the MPI/GPU axis,
  built once per compiler and shared across lanes. The substrate every lane sits
  on. (e.g. zlib, xz, zstd.)
- **Core** — lane-independent tools and packages safe to expose at the compiler
  layer. (e.g. cmake.)
- **Serial** — an MPI-*capable* package built **without** MPI by deliberate
  choice. The defining trait is the choice to omit MPI, not the absence of MPI
  support. (e.g. `hdf5~mpi`.)
- **MPI** — a package built **with** MPI. (e.g. osu, `hdf5+mpi`.)
- **GPU** — a package built with a GPU backend (ROCm/CUDA), typically over
  GPU-aware MPI. (e.g. `kokkos +rocm`.)

## Exposure

How a tier is made available to a user who enters a lane.

- **View** — a merged filesystem tree presented to a compiler environment or
  lane. How **foundation** packages, selected **core** tools, and the compiler
  are made available. No package modulefiles.
- **Module** — a generated modulefile the user loads. How lane choices and
  payload tiers are made available.

Exposure rule: **lane-independent foundation/core → compiler view (+ compiler);
lane-sensitive payload → lane modules.**

## Other terms

- **Lane** — one rendered build target: a single (compiler × optional MPI
  provider × optional GPU arch) combination at a chosen CPU target. The unit a
  Spack environment is rendered and built for.
- **Toolchain** — a compiler-matched MPI binding: the pairing that pins which
  MPI build (flavor) a given compiler resolves to, so an abstract spec
  (`hdf5+mpi`) materializes as a concrete build bound to the right compiler +
  MPI. Originates from Spack spec mechanics. Canonical case: Cray `cray-mpich`'s
  per-compiler (per-PrgEnv) builds, where each compiler must land on its matching
  MPI prefix. It is the per-lane (compiler, MPI) binding viewed from the spec
  side; how it is realized (per-compiler `%compiler` externals, or a named
  `toolchains.yaml` decoration) is an implementation choice, not the concept.
- **Provider family** — where a compiler or MPI comes from: `platform` (a vendor
  programming environment such as Cray PE), `site` (site-built), or `system` (OS
  package).
- **Platform family** — the specific platform a `platform` provider belongs to
  (e.g. `cray-pe`); detail beneath `provider_family: platform`.
- **Programming environment (CPE) version** — on Cray, the (compiler, MPI)
  toolchain is bound per CPE release: choosing a CPE version selects a coherent
  compiler + its matched `cray-mpich`. A profile may report several CPE versions;
  a build selects one (default: the latest).
- **Manual config catalog** — a maintainer-generated set of complete Spack
  configuration YAML files for one system, derived from `profile.yaml` facts and
  site policy for manual/package-manager use. Users write their own `spack.yaml`
  and include catalog files; this is separate from the managed stack workspace
  render, where Stack Composer writes the full environment.
