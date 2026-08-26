# CONTEXT — stack-generation domain glossary

Shared vocabulary for the four-repo stack-generation system (cluster-inspector,
stack-composer, stack-content, stack-planning). stack-planning is the definition
center, so the glossary lives here. Terms only — no implementation detail.

## Tiers

A package's **tier** says where it belongs in the CSE consumption model and its
default exposure shape. Tier does not by itself prove compiler binding or the
scope in which one artifact may be reused. There are two *base* tiers
(foundation, core) beneath three *payload* tiers (serial, mpi, gpu).

- **Foundation** — ambient base libraries and build substrate, off the MPI/GPU
  axis. The substrate every lane sits on. A Foundation member may be
  compiler-neutral or compiler-bound; the active Initial Conversion Trials
  conservatively build their Foundation library roots once per compiler
  surface. (e.g. zlib, xz, zstd; future build-substrate candidates include m4
  and autoconf.)
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

- **Managed consumption environment** — the deployed user-facing CSE
  development surface. A user enters a selected release/compiler/lane and
  receives approved commands, headers, libraries, metadata, and platform
  integrations without needing to know that Spack constructed them. It is
  managed discovery isolation, not a kernel or filesystem container.
- **Compiler binding** — the ownership scope imposed by an artifact's compiler
  or language interface, independent of its tier. A compiler-neutral artifact
  may be reused across compiler surfaces within an accepted compatibility
  domain; a compiler-bound artifact belongs to one compiler surface; a
  provider-bound artifact additionally belongs to an MPI/GPU/vendor toolchain.
- **Compatibility domain** — the reviewed set of operating-system ABI, CPU
  architecture/target, recipe, variant, external-runtime, and, where required,
  compiler/provider facts within which one exact built artifact may be reused.
- **System-integration external** — a declared host-owned package or runtime
  used because the host owns a meaningful security, scheduler, driver, fabric,
  hardware, or vendor compatibility contract. Ambient discovery alone never
  makes a package a system-integration external.

- **Lane** — one rendered build target: a single (compiler × optional MPI
  provider × optional GPU arch) combination at a chosen CPU target. The unit a
  Spack environment is rendered and built for.
- **Compiler surface** — one selected compiler and the environments exposed
  beneath its user-facing front door. The current CSE trial surface contains
  Core, Common, Serial, and MPI environments; a GPU environment is added only
  when GPU work is in scope. Each MPI or GPU environment still binds an
  explicit provider compatible with that compiler.
- **Toolchain** — a compiler-matched MPI binding: the pairing that pins which
  MPI build (flavor) a given compiler resolves to, so an abstract spec
  (`hdf5+mpi`) materializes as a concrete build bound to the right compiler +
  MPI. Originates from Spack spec mechanics. Canonical case: Cray `cray-mpich`'s
  per-compiler (per-PrgEnv) builds, where each compiler must land on its matching
  MPI prefix. In managed renders, Stack Composer realizes this as real Spack
  `toolchains.yaml` entries and decorates applicable root specs with
  `%<toolchain_name>`; the MPI provider scope still declares the matching
  externals in `packages.yaml`.
- **Provider family** — where a compiler or MPI comes from: `platform` (a vendor
  programming environment such as Cray PE), `site` (site-built), or `system` (OS
  package).
- **Platform family** — the specific platform a `platform` provider belongs to
  (e.g. `cray-pe`); detail beneath `provider_family: platform`.
- **Programming environment (CPE) version** — on Cray, the (compiler, MPI)
  toolchain is bound per CPE release: choosing a CPE version selects a coherent
  compiler + its matched `cray-mpich`. A profile may report several CPE versions;
  a build selects one (default: the latest).
- **Compiler baseline** — the minimum compiler family/version advertised by a
  platform MPI flavor. For Cray MPICH, an `ofi/gnu/12.3` flavor should be read
  as "GNU-family compiler baseline 12.3", not necessarily "the lane compiler
  must be exactly gcc 12.3".
- **Platform runtime set** — a coherent vendor runtime selection used by a lane:
  CPE release, compiler family, MPI provider/version/flavor, GPU toolkit, GTL,
  libfabric, LibSci, PMI/PALS, and related CrayPE components selected together.
- **Platform runtime transition** — the reviewed comparison between the runtime
  set recorded for an approved release and a candidate set after a system or
  vendor update. Its outcome is recorded per lane as revalidate, remain pinned
  to a supported older set, rebuild, or hold promotion. Coexisting modules and
  changed system defaults are evidence to investigate, not compatibility proof.
- **Manual config catalog** — a maintainer-generated set of complete Spack
  configuration YAML files for one system, derived from `profile.yaml` facts and
  site policy for manual/package-manager use. Users write their own `spack.yaml`
  and include catalog files; this is separate from the managed stack workspace
  render, where Stack Composer writes the full environment.
- **Spack runtime identity** — the exact Spack source, version/tag, and commit
  approved for a release. Two checkouts at different paths have the same
  runtime identity only when those values and their clean source trees match.
- **Spack tool root** — the shared or builder-local checkout that provides the
  approved Spack runtime identity. It is not a package store, workspace, build
  stage, cache, view, or module tree.
- **Spack package install tree** — the store where Spack installs concrete
  package prefixes and maintains the database and locks that coordinate those
  prefixes. It is separate from the Spack tool root.
