# Full render: open decisions for the build_all posture (v1)

| Document control | |
|---|---|
| Date | 2026-07-25 |
| Status | Design decision recorded; full-render implementation remains pending. |
| Scope | `externals.compilers: build_all` in the full render only. The static catalog path is complete and needs none of this. |

## Why this exists

The Initial Conversion Trials build from the static catalog, where building a compiler is
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

## Resolved design

The full renderer uses explicit compiler constraints, compiler-plus-MPI
toolchains, and one producer/`needs` model for stack-built compilers.

An MPI lane binds through a rendered compiler-plus-MPI toolchain:

```yaml
specs:
  - hdf5@2.1.0+mpi+fortran %gcc1250_craympich910
```

A serial lane carries an explicit compiler constraint:

```yaml
specs:
  - hdf5@2.1.0~mpi+fortran %gcc@12.5.0
```

For `build_all`, every environment repeats the exact compiler producer group.
Downstream groups use `needs: [compiler]` to order and expose that producer and
a conditional compiler toolchain to select it:

```yaml
specs:
- group: compiler
  specs: [gcc@14.3.0]
- group: apps
  needs: [compiler]
  specs:
  - matrix:
    - [...]
    - ['%cse_shared']
```

`needs` alone does not select the producer, and soft provider preferences may
still choose the external compiler that built it. Do not substitute a legacy
`%gcc@14.3.0` shorthand for the conditional toolchain. External compiler lanes
retain their existing explicit compiler constraint or compiler-plus-MPI
toolchain. `group`, `needs`, and conditional toolchains require Spack 1.2 or
newer, which the trial already standardizes on.

## Secondary observations, both worth a look

- **Serial lanes must bind a compiler.** A stack-built Serial lane orders its
  producer through `needs` and selects it with a conditional toolchain. An
  external Serial lane retains its explicit compiler constraint.

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
