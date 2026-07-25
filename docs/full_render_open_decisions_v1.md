# Full render: open decisions for the build_all posture (v1)

| Document control | |
|---|---|
| Date | 2026-07-25 |
| Status | Handoff note. Groundwork is committed; the remaining work needs the decisions below settled first. |
| Scope | `externals.compilers: build_all` in the full render only. The static catalog path is complete and needs none of this. |

## Why this exists

The pilot builds from the static catalog, where building your own compiler is
already possible: leave the compiler scope out of `include::` and name the
compiler in the specs. The full render has no equivalent yet. The schema has
advertised `externals.compilers` with a `build_all` value for some time, but no
render code read it, so the value did nothing.

Groundwork for it is committed in stack-composer. What is left is one slice
that cannot be finished without a decision.

## What is already done

Three changes, each covered by tests:

1. **Compiler selection no longer requires profile presence.**
   `resolve_compilers` in `render/plan.py` resolved every requested compiler
   against `profile.compiler_providers`, the machine's observed inventory. A
   compiler we intend to build is not installed yet, so it can never appear
   there and every selection was rejected. Under `build_all` the stack's refs
   are now taken verbatim. The posture is read by `compilers_are_stack_built`.

2. **Lanes carry `compiler_source`.** Set to `stack` or `platform` in
   `make_lane`. It records where the compiler comes from so later layers do not
   have to re-derive it.

3. **No platform-module prerequisite for a stack-built compiler.**
   `render/platform_modules.py` emitted `unresolved-platform-module` for any
   compiler absent from the profile, because lane modules `prereq` the platform
   modules behind site-external providers. A compiler we build has no platform
   module, so that check now skips when `compiler_source` is `stack`.

A `build_all` stack renders end to end after these.

## What is not done

**The rendered lane does not build the compiler.** Its `specs` block contains
the payload only, with no compiler root, so nothing tells Spack to build the
named compiler and nothing binds the payload to it.

## The decision that blocks it

The two lane kinds bind their compiler differently today, and `build_all` has
to pick one shape or reconcile them.

An MPI lane binds through a rendered toolchain:

```yaml
specs:
  - hdf5@1.14.5+mpi+fortran %gcc1330_craympich8129
```

A serial lane binds nothing at all:

```yaml
specs:
  - hdf5@1.14.5~mpi+fortran
```

Toolchains are rendered for MPI providers (`configs/mpi/<provider>/toolchains.yaml`)
and not for compiler-only lanes. So the options are:

1. **Render a compiler toolchain for every lane, then reference it.** Most
   consistent, and it makes the serial lane's compiler explicit for the first
   time. It changes rendered output for existing lanes that do not use
   `build_all`, so it needs a deliberate blessing rather than a quiet
   improvement.

2. **Emit a direct `%<compiler-ref>` on payload specs under `build_all` only.**
   Smallest change and touches nothing else, but it leaves two binding styles
   in the tree and a third under the new posture.

3. **Add the compiler as a concretization-group root and leave binding alone.**
   Builds the compiler but does not guarantee the payload uses it, so a serial
   lane could still concretize against something else. Not recommended on its
   own; it only works combined with 1 or 2.

Whichever is chosen, the specs block gains groups:

```yaml
specs:
- group: compiler
  specs: [gcc@14.3.0]
- group: apps
  needs: [compiler]
  specs: [...]
```

`group` and `needs` require Spack 1.2 or newer, which the pilot already
standardizes on.

## Secondary observations, both worth a look

- **Serial lanes do not pin a compiler in their specs.** This predates
  `build_all` and is not caused by it. Whether `environments/gcc/serial` and
  `environments/cce/serial` reliably concretize against their own compiler
  today, or rely on Spack preference plus the vendor scope, was not chased
  down. Worth confirming before the first full render regardless of this
  posture.

- **Where the built compiler's version is named.** The stack schema forbids a
  top-level `compilers` key; site selection lives in `defaults.yaml` and a
  per-build override in `builds[].compilers`. That is the place to name the
  version to build, and it matches how compilers are already chosen.

## Not in scope here

Whether a stack-built compiler should be paired with a platform MPI is settled
and does not need revisiting: keep the compiler at or above the MPI's build
baseline, never below. The full render already errors when no MPI flavor
accepts a lane's compiler (`mpi_flavor_compiler_unsupported`). The reasoning is
in `cray_mpich_gcc_compatibility_v1.md`.
