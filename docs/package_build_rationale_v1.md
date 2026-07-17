# Package Build Rationale

Status: 2026-07-10. Why the curated stack builds what it builds, the way it
builds it. Companion to the package sets in the catalog repo; when a decision
here changes, change the package set and this note together.

## Roots, not matrices

The package sets list explicit root specs, and the concretizer builds exactly
those roots. Nothing is cross-multiplied unless we write it out.

The python/numpy pairing is the worked example. Two supported python lines and
one numpy recipe version produce four explicit roots:

- python 3.14.5 and 3.13.13 (the two newest supported minor lines)
- numpy 2.4.6 against each python (the newest non-deprecated recipe supports
  both)

Reasoning: numpy versions exist to serve python versions, not the other way
around. Each interpreter wants the newest non-deprecated numpy that supports
it, which is one numpy today. Module and view naming consequence (2026-07-14):
two py-numpy roots share one name and version, so their modules carry the
python line (py-numpy/2.4.6-python3.14.5); this is the same
qualify-only-when-ambiguous rule lane and toolchain names follow, and the
renderer fails loudly on same-name/version root collisions that no python
line distinguishes. A user with genuinely unusual pairing needs uses
miniforge (in Core for exactly this) and manages their own environment. If the
team ever wants a broader matrix, it is an explicit package-set change, not a
renderer redesign.

The same principle pins the netcdf chains: each netcdf-c version is built
against one named hdf5 version (4.10.0 on 2.1.0 and 4.9.3 on 1.14.6), giving
two coherent stacks instead of an untested cross-product.

## Version policy

For packages carried at multiple versions, build exactly the newest supported
version and its immediate predecessor. Carry one where only one makes sense:

- miniforge3: single version. It is an installer for user-managed
  environments; multiple versions of the installer serve nobody.
- netcdf-cxx4: single version because the upstream package has exactly one
  release the recipes know.
- dakota follows the two-version rule. It is by far the heaviest build in the
  roster (a large Boost-anchored dependency tree), so do not expand it beyond
  the supported pair without a specific team request.
- hdf5 includes 2.1.0, the new major series. The netcdf recipes accept it;
  if it misbehaves on a real system, the 1.14.x chains stand alone and
  2.1.0 drops without touching anything else.

## Never built: what the system already provides

Compilers (GCC, CCE, AOCC), MPI implementations (Cray MPICH, Open MPI), and
OpenSSL are consumed as system externals, pinned in the rendered
configuration with buildable false. Reasons: the system's MPI is fabric- and
scheduler-integrated in ways a self-built one is not; the compilers are the
site's supported surfaces by definition; OpenSSL tracks the OS security
process, not ours. The build must use these: a build that starts compiling
its own MPI or OpenSSL means the inputs were wrong, and that is treated as a
stop-and-fix, not a fallback.

## One version rule per layer

- Foundation libraries (zlib, xz, zstd): exactly one pinned version,
  ambient in the user-facing view. A user's fresh compile links these
  without choosing them, so two versions on the link path would be
  indistinguishable; the pin is what keeps user links unambiguous.
- Core tools (cmake, python, miniforge, gsl, sqlite): multiple versions may
  be installed, but they are loadable choices, never ambient conflicts.
- Payload science libraries: multiple versions by design, disambiguated by
  the one-at-a-time module choice inside a lane.

## Placement decisions

- gsl and sqlite sit in Core: no MPI implementation exists for them and
  they behave as building blocks.
- openblas is compiler-common despite having no MPI: it is
  compiler- and performance-sensitive, which fails the compiler-agnostic
  test for Core. It sits in the compiler-common group (2026-07-13, group
  formalised 2026-07-14): one build per compiler, loadable from the surface
  before any lane, because MPI and GPU codes link BLAS/LAPACK constantly and
  lanes are exclusive; without it an MPI user had no loadable BLAS at all.
- netlib-lapack was dropped (decided 2026-07-14, resolving the team review
  it carried). It was added because the usage list names lapack explicitly,
  but that requirement is already met: the openblas recipe declares
  `provides("blas", "lapack")`, and for the versions we carry,
  `provides("lapack@3.9.1:")`. Shipping both put LAPACK in the view twice,
  once inside `libopenblas.so` and once as `liblapack.so`, so a user linking
  `-llapack` would silently get the unoptimized reference build. That is the
  same ambiguity the foundation single-version pin exists to prevent, one
  layer up. openblas is the single BLAS and LAPACK implementation. Reference
  LAPACK returns only if someone names a consumer that needs it for numerical
  validation.
- netlib-scalapack sits in the MPI lane (added 2026-07-14). ScaLAPACK is
  distributed dense linear algebra built on BLACS over MPI, so it has no
  serial form; a single-rank ScaLAPACK would just be LAPACK. It depends on
  the lane's blas and lapack, which openblas provides. The GPU lane carries
  it because that lane repeats the MPI roster.
- gnuplot placement is decided (2026-07-13, was flagged core-vs-serial):
  it is compiler-common because it is **not compiler-agnostic**:
  it must be built with the surface's compiler to stay compatible with the
  lane libraries it links, so it fails the Core test the same way openblas
  does. The compiler-common group keeps it visible to every lane's users.
- boost is a dual-build package (decided 2026-07-13): it **can be built
  with an MPI backend**, so the stack builds it both ways: ~mpi in the
  serial lane and +mpi in the MPI lane, same clean module name, the loaded
  lane picks the build, exactly like HDF5 and FFTW. It was briefly
  considered lane-agnostic; being MPI-capable disqualifies it.
- kokkos is the GPU lane pilot content: unlike a profiler, it compiles
  device code, which is what actually proves the GPU toolchain works. It is
  new to the roster; the flat stack that came before did not carry it.
- kokkos stays GPU-lane-only for this pass (decided 2026-07-14), and the
  reasoning is worth recording because the package invites the opposite
  conclusion. Kokkos does not link MPI: the recipe has no `mpi` variant and
  no `depends_on("mpi")`, so it is never an MPI-lane package the way HDF5 is.
  What it does have is a host backend and an optional device backend, and the
  recipe requires a host backend in every case
  (`requires("+serial", when="~hpx ~openmp ~threads")`), so the GPU build
  already runs on the CPU, single-threaded, today. A CPU build could therefore
  sit in the serial and MPI lanes under the same clean name, extending the
  dual-build rule from the MPI boundary to the GPU boundary exactly as boost
  does. We are not doing that yet: kokkos is here to prove the GPU toolchain
  rather than to answer a user request, and the reason to hand CPU users a
  portability layer is performance, which this pass does not chase because
  every lane builds at the portable baseline. Revisit when target
  optimization turns on, or when someone asks for Kokkos on CPU.
- tau carries one version (decided 2026-07-14). The two-version rule exists
  so a user whose code pins an older release can still build; nobody pins a
  profiler, because profiling is work you do with whatever the current tool
  is. Same reasoning as miniforge3.
- tau in the GPU lane is its own build, `+mpi +gpu_runtime`, rather than the
  MPI lane's `+mpi` (decided 2026-07-14). The plain build cannot see kernels,
  which makes it useless to a GPU user. The variants are additive, so the
  GPU-lane build profiles MPI codes, GPU codes, and MPI+GPU codes alike:
  one build per lane, not two in the GPU lane. Two tau roots of one version
  in a single lane would also be a hard render error, since nothing but
  variants would distinguish their module names.

## Build posture for this pass

- No target optimization: every lane builds at the portable baseline
  (x86_64_v3). If it builds portable, it builds optimized; optimization is
  a per-lane flag to turn on later, not a structural change.
- Concretization runs with unify false: lanes deliberately carry multiple
  versions of the same package, which strict unification would collapse or
  reject.
- Expected reuse check at first concretize: the numpy roots should reuse
  the two python installs rather than concretizing private pythons. If
  the install tree shows more than two pythons, add a require pin; the
  lockfile makes this obvious.
