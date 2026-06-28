# CONTEXT — stack-generation domain glossary

Shared vocabulary for the four-repo stack-generation system (cluster-inspector,
stack-composer, stack-content, stack-planning). stack-planning is the definition
center, so the glossary lives here. Terms only — no implementation detail.

## Tiers

A package's **tier** says both how it is built and how it is exposed. There are
two *base* tiers (foundation, core) beneath three *payload* tiers (serial, mpi,
gpu).

- **Foundation** — base libraries and build substrate, off the MPI/GPU axis,
  built once and shared across stacks. The substrate every lane sits on. (e.g.
  zlib, xz, zstd.)
- **Core** — base packages and tooling exposed for direct use. (e.g. cmake.)
- **Serial** — an MPI-*capable* package built **without** MPI by deliberate
  choice. The defining trait is the choice to omit MPI, not the absence of MPI
  support. (e.g. `hdf5~mpi`.)
- **MPI** — a package built **with** MPI. (e.g. osu, `hdf5+mpi`.)
- **GPU** — a package built with a GPU backend (ROCm/CUDA), typically over
  GPU-aware MPI. (e.g. `kokkos +rocm`.)

## Exposure

How a tier is made available to a user who enters a lane.

- **View** — a merged filesystem tree presented to the lane. How **foundation**
  packages, together with the compiler, are made available. No modulefiles.
- **Module** — a generated modulefile the user loads. How **core** packages are
  made available (and the payload tiers likewise).

Exposure rule: **foundation → view (+ compiler); core → modules.**

## Other terms

- **Lane** — one rendered build target: a single (compiler × optional MPI
  provider × optional GPU arch) combination at a chosen CPU target. The unit a
  Spack environment is rendered and built for.
- **Provider family** — where a compiler or MPI comes from: `platform` (a vendor
  programming environment such as Cray PE), `site` (site-built), or `system` (OS
  package).
- **Platform family** — the specific platform a `platform` provider belongs to
  (e.g. `cray-pe`); detail beneath `provider_family: platform`.
