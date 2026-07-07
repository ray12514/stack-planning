# Default selection policy (v1)

Status: active. Companion to `stack_generation_structure_v1.md` § Resolution;
this note defines how `defaults.yaml` expresses site-wide compiler/MPI
selection so ordinary systems render with **no per-stack authoring**.

## Goals

A site should be able to declare once, in `defaults.yaml`:

- prefer a named MPI provider when the system reports it, and fall back to
  whatever MPI the profile actually reports when it does not;
- resolve one provider name reported at multiple versions by policy
  (newest) instead of hard-erroring;
- fall through the source ladder — platform/site external first, Spack-built
  last — without inventing per-system stacks.

The reference baseline both template sets ship: **gcc-family compilers**
(PrgEnv-gnu on Cray, plain gcc elsewhere) and the **newest reported version
of the preferred MPI provider** (cray-mpich on Cray platforms, openmpi on
generic Linux, falling back to any reported MPI implementation).

## MPI selection (`defaults.yaml` → `mpi_selection`)

- `provider` — preferred provider name. When the profile reports it, it wins
  over profile order. When the profile does not report it, `source: auto`
  falls back to the first reported renderable provider (respecting
  `provider_family_priority`), and only builds the preferred provider from
  source when the profile reports no MPI at all. A **per-build** `mpi:`
  override naming an unreported provider still means "build exactly that" —
  an explicit build request is intent, not preference.
- `version_policy` — how one provider name reported at multiple versions
  resolves. `explicit` (default): `mpi.version` is required, anything else is
  the hard `mpi_ambiguous` error (undeclared ambiguity stays an authoring
  defect). `newest`: the highest version wins and is recorded in the render
  plan. Platform-family providers (one coherent product tree, e.g. Cray PE)
  always resolve newest; the knob exists for site/system externals.
- `provider_family_priority` — unchanged: provider-family preference when
  multiple *different-name* providers are reported.
- Source ladder: `source: auto` already encodes external-first
  (platform/site provider reported by the profile) → Spack-built fallback.
  No new knob; `source: build` remains the explicit override.

## Spack-built compilers

Spack 1.x treats compilers as ordinary package nodes: a toolchain entry or
spec constraint (`%c=gcc@14.3.0`) does not require the compiler to be
installed or external at render time — the concretizer builds the compiler
first when nothing satisfies the constraint. The renderer therefore does not
need a compiler-source knob to *permit* Spack-built compilers; it must only
avoid emitting an external pin or `buildable: false` for a compiler the
profile does not report. Stacks may list not-yet-built compiler versions.

## Compiler family preference (already implemented)

`defaults.yaml` `compilers:` already carries this policy: `baseline` (the
lean default) selects gcc when the profile reports it, else the first
reported compiler; `all` fans out; an explicit list narrows. Cray platform
renders additionally prefer the platform compiler for baseline. Nothing new
is needed for the gcc-everywhere reference default.

## Non-goals

- No compatibility-matrix-driven GPU/MPI coupling here (tracked separately,
  see `cpe_rocm_compatibility_note_v1.md`).
- No stack-authoring surface changes: `stack.yaml` stays spec-native; all of
  this lives in `defaults.yaml`.
