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
it, which is one numpy today. A user with genuinely unusual pairing needs uses
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
process, not ours. The build must use these — a build that starts compiling
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
- openblas stays in the serial payload despite having no MPI: it is
  compiler- and performance-sensitive, which fails the compiler-agnostic
  test for Core. It is declared lane-agnostic (2026-07-13): one serial-lane
  build whose modules are exposed in every payload lane of the compiler
  column, because MPI and GPU codes link BLAS/LAPACK constantly and lanes
  are exclusive — without the shared exposure an MPI user had no loadable
  BLAS at all.
- netlib-lapack is built alongside openblas (the usage list names lapack
  explicitly). openblas already provides LAPACK, so this gives users the
  reference implementation as well; flagged for team review since it puts
  two LAPACKs in the view. Lane-agnostic, same reasoning as openblas.
- gnuplot placement is decided (2026-07-13, was flagged core-vs-serial):
  it stays in the serial payload because it is **not compiler-agnostic** —
  it must be built with the surface's compiler to stay compatible with the
  lane libraries it links — so it fails the Core test the same way openblas
  does. Lane-agnostic exposure keeps it visible to every lane's users.
- boost is a dual-build package (decided 2026-07-13): it **can be built
  with an MPI backend**, so the stack builds it both ways — ~mpi in the
  serial lane and +mpi in the MPI lane, same clean module name, the loaded
  lane picks the build — exactly like HDF5 and FFTW. It was briefly
  considered lane-agnostic; being MPI-capable disqualifies it.
- kokkos is the GPU lane pilot content: unlike a profiler, it compiles
  device code, which is what actually proves the GPU toolchain works.

## Build posture for this pass

- No target optimization: every lane builds at the portable baseline
  (x86_64_v3). If it builds portable, it builds optimized — optimization is
  a per-lane flag to turn on later, not a structural change.
- Concretization runs with unify false: lanes deliberately carry multiple
  versions of the same package, which strict unification would collapse or
  reject.
- Expected reuse check at first concretize: the numpy roots should reuse
  the two python installs rather than concretizing private pythons. If
  the install tree shows more than two pythons, add a require pin — the
  lockfile makes this obvious.
