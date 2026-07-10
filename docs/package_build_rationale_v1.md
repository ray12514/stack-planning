# Package Build Rationale

Status: 2026-07-10. Why the curated stack builds what it builds, the way it
builds it. Companion to the package sets in the catalog repo; when a decision
here changes, change the package set and this note together.

## Roots, not matrices

The package sets list explicit root specs, and the concretizer builds exactly
those roots. Nothing is cross-multiplied unless we write it out.

The python/numpy pairing is the worked example. Three pythons and two numpys
could mean nine builds; we build seven roots:

- python 3.14.5, 3.13.13, 3.12.13 (the three newest minor lines)
- numpy 2.5.1 against each of the three pythons (the newest numpy supports
  all three)
- numpy 2.4.6 against 3.13.13 only

Reasoning: numpy versions exist to serve python versions, not the other way
around. Each interpreter wants the newest numpy that supports it, which is
one numpy today. The single older pair covers the real request that occurs
("my code pins numpy below 2.5") without paying for six combinations nobody
asks for. A user with genuinely unusual pairing needs uses miniforge (in
Core for exactly this) and manages their own environment. If the team ever
wants the full matrix, it is a three-line matrix entry in the package set,
not a redesign.

The same principle pins the netcdf chains: each netcdf-c version is built
against one named hdf5 version (4.10.0 on 2.1.0, 4.9.3 on 1.14.6, 4.9.2 on
1.14.5), giving three coherent stacks instead of nine untested mixtures.

## Version policy

Three versions where the package recipes carry three usable ones; never
fewer than the latest two; one where only one makes sense:

- miniforge3: single version. It is an installer for user-managed
  environments; multiple versions of the installer serve nobody.
- netcdf-cxx4: single version because the upstream package has exactly one
  release the recipes know.
- dakota: two versions, not three. It is by far the heaviest build in the
  roster (a large Boost-anchored dependency tree), and the third-newest
  recipe pins git refs rather than a release tarball. Add it later if the
  team asks.
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
  test for Core.
- netlib-lapack is built alongside openblas (the usage list names lapack
  explicitly). openblas already provides LAPACK, so this gives users the
  reference implementation as well; flagged for team review since it puts
  two LAPACKs in the view.
- gnuplot placement (Core vs serial payload) is flagged for team review; it
  currently sits in the serial payload.
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
  the three python installs rather than concretizing private pythons. If
  the install tree shows more than three pythons, add a require pin — the
  lockfile makes this obvious.
