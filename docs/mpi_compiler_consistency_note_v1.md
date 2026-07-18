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

## Two different promises

It helps to name what "consistent" means, because there are two versions and
they serve different users.

**Interface consistency.** The same front door, the same lane names, the same
rosters, and the same module names on every system, with the native provider
behind the `MPI` name. The lanes model already delivers this. A user who
learns `module load cse/GCC` then `MPI` on Raider needs no new knowledge on
Blueback. What changes underneath is a platform fact, not a user-facing one.

**Binary consistency.** The same build artifact runs on every system. This
matters to a narrower group: teams that ship prebuilt codes, containerised
workflows, and users who hop between systems mid-project. Interface
consistency does nothing for them, because their binaries are linked against
one specific MPI.

The two can coexist. Interface consistency stays the default story; binary
consistency can be an additional lane for the users who need it, not a
replacement for the native one.

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

Routes 2 and 3 are not exclusive with route 1. The likely end state is route
1 as the performance default with route 2 as the portability lane, if the
validation holds.

## What this changes in the model

Structurally, almost nothing. The lanes are provider-parameterised, `mpi:
source` already has a build path (the smoke system builds OpenMPI today), and
compilers are policy. Every route above is a defaults change plus validation,
not a renderer change. The "never built" section of the build rationale is
rewritten to say what it actually is: pilot policy, per system, revisitable.

## What needs proving before any of it

On Blueback, in rough order of information value:

1. `cray-mpich-abi` against a stock-MPICH-built binary: does the swap work,
   does the launch path behave, what breaks with GPU-aware codes.
2. Spack splicing on a small case: splice cray-mpich in place of mpich and
   diff the result against a native build.
3. OpenMPI over CXI: build, run the fabric checks, measure enough to know
   whether it is a viable default or an emergency fallback.
4. A stack-built GCC at the pinned version: build one lane with it end to
   end and compare against the platform GCC lane.

## Decision needed

Which consistency is CSE promising, to whom, and on what timeline. Interface
consistency is delivered; binary consistency is buildable; the two-surface
compiler story is cheap. The team owns the ordering.
