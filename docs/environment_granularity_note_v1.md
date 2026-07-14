# Environment granularity: one environment per lane (v1)

| Document control | |
|---|---|
| Date | 2026-07-14 |
| Status | Decision note; answers a recurring team question |
| Prompted by | Arthur's interop question and the Spack 1.2 jobserver discussion |

## The question

Are all builds in a lane a single Spack environment, or does each package get
its own? And since lanes overlap (the GPU lane carries the MPI roster, common
packages appear everywhere), could everything collapse into one spack.yaml
with spec groups, especially now that Spack 1.2 can parallelize package
builds inside a single install?

## Current shape

One Spack environment per lane, never one per package. A lane's environment
concretizes as a whole, so everything a lane contains is solved together and
is mutually consistent by construction. Environments do not share YAML; they
share configuration by reference, through the same included scopes.

## How overlap stays coherent

Two lanes listing the same root spec is the normal case, not an accident.
Coherence comes from content addressing, not coordination:

- Every environment includes the same pinned inputs by reference: compiler
  and MPI externals from the fact sheet, the same toolchain definitions, the
  same pinned package recipe generation, the same target scope.
- Identical spec plus identical configuration concretizes to the identical
  hash. The second lane to mention `hdf5+mpi` reuses the first lane's install
  from the shared install tree or build cache. The overlap is the same
  artifact on disk; there is nothing to drift and nothing extra to build.
- The lockfiles are the proof. The concretize gates (externals used and never
  fetched, zero MPI nodes in the serial lock, netcdf chains resolving their
  paired hdf5, the expected python reuse count) check coherence in the lock,
  never assume it from the render.

Interop is promised only where a user can actually stand: one compiler
surface, Foundation and Core, the common packages, and exactly one lane. That
composition is one compiler column and one concretization. Combinations we
cannot guarantee, such as two lanes at once or two compilers mixed, are
blocked by module conflicts instead of left to convention.

## What Spack 1.2 changes, and what it does not

Spack 1.2 ships a jobserver-based installer (concurrent package builds inside
one `spack install`, sharing a job pool), concretization groups (named spec
groups in one environment with independent solve preferences), and
concretization caching. Together these remove most of the build-speed
argument for sharding into many environments.

They do not replace the other things the lane boundary provides:

1. **Per-lane lockfile as the release and rebuild unit.** The runtime
   transition gate classifies revalidate/pin/rebuild per lane, and the SOP's
   rebuild unit is the affected lane. One shared lock would need graph
   filtering to recover any of that.
2. **Purity gates.** "The serial lock contains zero MPI nodes" is a one-line
   check against a lane lockfile. In a single environment it becomes a
   per-group graph query.
3. **Module exposure boundaries.** Lane module roots fall out of the
   environment graph. Emulating lanes inside one environment means a
   maintained include whitelist per lane instead; the renderer could compute
   those, but the complexity moves rather than shrinks.
4. **Blast radius.** Lanes concretize and fail independently. In one
   environment, a solver conflict introduced by a GPU root can block
   re-locking the serial lane.
5. **Solver scale.** The E4S guidance the deck cites still holds: flat
   mega-environments are the known anti-pattern. Groups mitigate this; they
   do not repeal it.
6. **Multi-CPE fan-out** (committed v1 goal) multiplies lanes by programming
   environment release. Lane-per-environment absorbs that; one environment
   for everything gets combinatorial.

## Decision and upgrade posture

Keep one environment per lane. Adopt Spack 1.2 inside that model when the
pin moves: the jobserver speeds up each lane's install and the concretization
cache speeds up re-renders, without giving up per-lane evidence. Moving the
`spack.version` pin is a deliberate platform decision with its own
compatibility check against the CPE toolchain model, not a side effect of
this note.
