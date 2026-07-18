# MPI and compiler consistency across DSRCs (v1)

| Document control | |
|---|---|
| Date | 2026-07-14 |
| Status | Design note for team discussion; nothing here is decided |
| Prompted by | What CSE is actually supposed to be: a consistent user environment across all DSRCs |

## The question

CSE exists to give users a consistent environment on every DSRC system. The
current model consumes each system's compilers and MPI as externals, which
means the environment is consistent in shape but not in substance: the same
lane names sit on top of a different MPI and a different compiler build on
every machine. The pilot chose that deliberately, and for the pilot it is
right. This note asks what the longer-term promise should be.

The tension is the same one the vendor math-library question carries, applied
to the two biggest components. Externals maximise platform integration: the
site's MPI knows its fabric, its scheduler, and its GPUs. Building our own
maximises consistency: the same compiler and the same MPI everywhere, at the
cost of proving fabric, launch, and GPU integration ourselves on each system.

## Who this is for, and what is promised

CSE's lanes serve end users who build and run their own code on these
systems. App managers with their own software are a different audience: they
have the platform catalog, they build and expose their packages however they
choose, and they never enter a lane. The consistency promise is owed to the
first group only.

For that user, consistency means **the same functionality, reached the same
way, on every system**. The same front door and lane names; the same roster
of capabilities (a working MPI, HDF5, NetCDF, FFTW, BLAS, the same versions);
the same workflow of load, compile, link, and run. Their source builds the
same way everywhere. What sits underneath, cray-mpich here and Open MPI
there, is a platform fact the promise deliberately does not extend to. Same
functionality, not same implementations by name.

**Binary consistency is out of scope.** The same artifact running on every
system would require one MPI implementation everywhere or ABI substitution,
and no user need for it has been identified: this is a build-and-run
environment, not a binary distribution channel. The mechanism is recorded in
route 2 below in case a need ever appears, and until one does it is not the
plan.

The visible seams in functional consistency today, in rough order of user
impact: the scheduler (srun on the Slurm systems, PBS on Wheat, which changes
how jobs launch), the compiler version behind each surface, and capability
gaps between MPI implementations (GPU-awareness, MPI standard level). The
first is a site property the lanes cannot hide. The other two are ours to
close, which is what the rest of this note is about.

## Compilers: build them

This half is low risk. A compiler is self-contained: no fabric, no scheduler,
no launch path. Spack's compilers-as-dependencies model makes a stack-built
compiler ordinary, and the renderer already treats compiler selection as
policy.

A pinned **CSE GCC**, one exact version on every DSRC, is the strongest
consistency anchor available: same compiler, same flags, same rosters,
everywhere. It also resolves the Intel question on its own terms. The Intel
environment exists because CSEinit predates the AMD fleet; with the last two
Intel-CPU systems sunsetting, the consistent pair becomes CSE GCC everywhere
plus the system's own blessed surface (CCE on the Crays, potentially AOCC on
the AMD systems). That is the two-surface shape the pilot already presents.

## MPI: three routes

**Route 1, today's: the native provider per system.** cray-mpich on the
Crays, the site MPI elsewhere. Best integration, best performance, GPU-aware
paths supported by the vendor. No binary consistency. The reasons recorded in
the learnings doc for keeping cray-mpich on Slingshot 11 all still hold.

**Route 2: a stock MPICH lane with ABI substitution on the Crays.** The
MPICH ABI Compatibility Initiative gives MPICH, Intel MPI, and cray-mpich a
shared binary interface, and HPE ships a compatibility layer (the
`cray-mpich-abi` module) so a binary built against stock MPICH runs over
cray-mpich by swapping the library path at run time. The pattern: users build
in a plain MPICH lane that is identical on every system; on the Crays the
runtime resolves to cray-mpich underneath, with Slingshot and the launch
integration intact. On the Spack side, splicing (`concretizer:splice`) is the
matching install-time mechanism: substitute an ABI-compatible provider
without rebuilding. Splicing is newer machinery and needs a validation pass
before we lean on it. Tailwind worth noting: the MPI Forum's standard ABI
effort points the ecosystem at exactly this pattern, and MPICH 4.2+
implements it, so this bet gets safer with time.

**Route 3: our own OpenMPI over Slingshot 11.** Possible through libfabric's
CXI provider; the learnings doc maps the intra-node choices (OFI BTL versus
LNX). This buys consistency of a different flavour: one MPI we own on every
system. The costs: OpenMPI has its own ABI, so no vendor compatibility layer
exists and we own fabric validation on every machine; and GPU-aware MPI on
the Crays reopens the GTL problem.

Route 1 is the plan: the native provider delivers the functionality promise
with the platform's own integration. Route 3 is the fallback where a system
lacks a suitable native MPI, and the capability floor is the test either
way: GPU-aware MPI where the hardware calls for it, and a common MPI
standard level. Route 2 stays recorded because the mechanism is real, but it
serves binary portability, which is out of scope until a user need appears.

## What this changes in the model

Structurally, almost nothing. The lanes are provider-parameterised, `mpi:
source` already has a build path (the smoke system builds OpenMPI today), and
compilers are policy. Every route above is a defaults change plus validation,
not a renderer change. The "never built" section of the build rationale is
rewritten to say what it actually is: pilot policy, per system, revisitable.

## What needs proving before any of it

On Blueback, in rough order of information value:

1. A stack-built GCC at the pinned version: build one lane with it end to
   end and compare against the platform GCC lane. This is the compiler half
   of the functionality promise.
2. The capability floor across the four systems: MPI standard level and
   GPU-aware MPI availability per system, recorded as facts next to the
   fact sheets.
3. OpenMPI over CXI: build, run the fabric checks, measure enough to know
   whether it is a viable fallback where a native MPI falls short.
4. Only if a binary-portability need ever surfaces: `cray-mpich-abi` against
   a stock-MPICH-built binary, and Spack splicing on a small case.

## Decision needed

Agree the functionality floor: which capabilities every system's lanes must
provide, and whether one pinned CSE GCC anchors the compilers. The interface
and workflow are delivered; the floor and the compiler pin are the open
parts. Binary consistency stays out of scope until someone names a user who
needs it.
