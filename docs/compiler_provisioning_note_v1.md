# Compiler Provisioning Note (v1)

Status: design note, direction approved 2026-07-10. Implementation is
deliberately deferred until after the four-system build-out; the stack
schema's kind enum and the planner are unchanged until that pass. This note
is the spec that pass implements against.

## Problem

Today a build that requests a compiler the profile does not report is
skipped (`compiler_unavailable`). That is the right default, but it is the
whole story: there is no supported way to say "this compiler does not exist
on the system yet: build it, then build with it." Spack 1.x is fully
capable of building compilers (compilers are ordinary package nodes), so
the gap is planning policy, not mechanism.

## Decision

Compiler provisioning is an **explicit, separate build**, never an implicit
fallback.

A payload lane whose toolchain names an uninstalled compiler must never
cause Spack to build that compiler as a side effect. Three reasons:

1. It hides the most expensive build in the stack inside whichever payload
   lane concretizes first.
2. Lanes build independently and in parallel; an implicit compiler build is
   a race between every lane that names it.
3. The externals tripwire, "Spack building something the system already
   provides means the inputs were wrong," only works if a compiler build
   is never a legitimate surprise.

Production precedent: NASA JSC's stack runs a dedicated compilers
environment as stage one of an ordered fan-out, before anything consumes
the compilers.

## Shape

- A new build kind, `compiler`. The build lists the compiler spec(s) to
  provision (e.g. `gcc@14.3.0`). The lane builds **with the system
  compiler** at the **portable baseline target**, like foundation.
- **Not a profile fact.** The profile stays observed-only. A stack-built
  compiler carries the existing provenance class **Spack-built**; it is
  recorded in the release manifest, never written back into the fact sheet.
- **Consumption is through the shared install tree**, not a fabricated
  external: with `reuse: true`, a payload toolchain naming `gcc@14.3.0`
  resolves to the installed node. No packages.yaml entry pretends it is a
  system external.
- **Ordering rule:** the build driver runs kinds in order:
  `compiler` → `core` → `serial`/`mpi`/`gpu`. By the time any payload lane
  concretizes, the provisioned compiler is installed and in the buildcache.
  Compiler artifacts key into the foundation-style cache lane
  (OS/glibc/spack-generation/baseline target), so later renders and sibling
  systems on the same boundary reuse instead of rebuild.
- **Availability rule (planner):** "compiler available" becomes *reported
  by the profile OR provided by a `compiler` build in this stack*. When
  neither holds, the error names both remedies: not on the system; add a
  `kind: compiler` build or change the compiler selection.

## Verification obligations (for the implementation pass)

- Payload lanes must **reuse** the provisioned compiler: a second gcc in the
  install tree after a payload concretize is a failure, visible in the
  lockfiles.
- The tripwire stays: an *unplanned* compiler appearing in any payload
  lane's concretization is still stop-and-fix.
- The GPU/MPI compatibility narrowing must treat a provisioned compiler
  like any other compiler ref (it has no platform flavors; platform MPI
  lanes on Cray still bind to reported flavors only).

## Why this is worth having

Beyond the obvious (a site whose blessed compiler is older than what a
stack needs), this is the missing prerequisite for the **shared
compiler-agnostic Core** recorded in
`foundation_core_view_semantics_note_v1.md`: building our own GCC once
removes Core's dependence on whatever GCC version each machine happens to
ship, which is what makes a cross-system shared Core honest.

## Scope of the implementation pass (later)

Stack schema kind enum gains `compiler`; `build_kind` treats it as explicit
only (never inferred); planner availability rule and error message; build
driver ordering; manifest provenance entries; lane/module docs gain the
kind (a compiler lane is internal; it never gets a public lane module);
tests first, per the usual discipline.
