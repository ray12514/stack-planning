# Foundation And Core View Semantics Note v1

## Status

Design note / hardening target. This records intended semantics that are not fully settled in the current implementation.

## Context

The stack model already separates package intent by lane kind. Serial, MPI, and GPU lanes are for packages that require those build surfaces. MPI-capable libraries and applications such as HDF5, NetCDF, PNetCDF, TAU, and GPU-enabled packages do not belong in a shared foundation or Core layer merely because many lanes depend on them.

The unresolved question is narrower: how should the stack expose, reuse, and constrain low-level build tools and ABI-stable dependencies that can be shared across compiler/MPI/GPU lanes?

Examples include:

```text
cmake
ninja
pkgconf
zlib
xz
zstd
bzip2
```

These packages may be built once with a baseline compiler and baseline CPU target, then used as build tools or low-level dependencies by many payload lanes.

## Working definitions

### Foundation layer

The foundation layer is the lowest shared layer. It is optimized for portability and reuse, not for target-specific performance.

A foundation package should generally be:

- independent of MPI provider;
- independent of GPU runtime;
- safe to reuse across payload compilers as a build tool or low-level dependency;
- built for a baseline CPU target such as `x86_64_v2` or `x86_64_v3`, not for a specific compute-node microarchitecture;
- narrow enough that version policy remains understandable.

### Core lane

A Core lane is compiler-adjacent stack infrastructure. In the committed v1 model, each compiler's Core is a normal, independently concretized environment and carries the foundation roots directly. Reuse between Core and payload lanes happens through the foundation buildcache, not by including another lane's lockfile.

The design records two possible deployment shapes, but only Option B is committed for v1:

```text
Option A: separate foundation lane

foundation
   ↓
gcc/core
   ↓
gcc/serial, gcc/mpi, gcc/gpu

Option B: squeezed foundation + core

gcc/core
   ↓
gcc/serial, gcc/mpi, gcc/gpu
```

The separate foundation lane is a future, evidence-gated optimization. If it is adopted under Spack 1.2+, environment composition uses `spack: include: [/absolute/path/to/spack.lock]`; the deprecated `include_concrete:` key is not used. The squeezed per-compiler Core shape is the committed v1 deployment model.

## Visibility policy

Foundation packages should usually not be exposed as ordinary user-facing package modules.

They may exist in a build-time view or internal runtime view so that build environments can find tools such as `cmake`, `ninja`, or `pkgconf`, but they should not automatically appear as public modules next to application-facing packages unless a stack policy explicitly marks them public.

Recommended default:

```text
foundation package visibility: internal/build-only
core package visibility: internal unless explicitly public
payload package visibility: public according to stack/module policy
```

This avoids confusing users with implementation-detail modules while still letting Spack, build scripts, and package maintainers use those tools.

## View collision problem

A shared view can collide when multiple versions of the same dependency are present.

Example:

```text
foundation view contains zlib@1.3.1
payload dependency wants zlib@1.2.13
both provide libz.so with overlapping names
```

If both are projected into the same flat view path, the `bin/`, `lib/`, `include/`, and pkg-config namespaces can conflict. Even when the ABI is compatible, the visible view may not express which dependency a payload lane was concretized against.

Therefore, the stack must define explicit view semantics instead of assuming every installed dependency can be projected into one shared path.

## Recommended view semantics

Use distinct view classes rather than one universal view.

```text
foundation/build view:
  Internal. Exposes selected build tools and safe low-level dependencies.
  Used by build environments and lane composition.

lane payload view:
  Public or semi-public. Exposes packages selected for a specific compiler/MPI/GPU lane.
  Should not blindly merge every transitive dependency.

package/application module surface:
  User-facing. Exposes only packages intended for users.
```

The foundation/build view may use a stricter projection policy such as:

```text
{name}/{version}
```

or a lane/release-qualified path such as:

```text
foundation/{name}/{version}
```

Public payload views should avoid exposing conflicting transitive dependencies unless policy says they are public.

## Version policy

The stack needs an explicit policy for foundation package versions.

Possible policies:

### Single supported foundation version

For each foundation package, choose exactly one version per release generation.

Example:

```yaml
foundation_pins:
  cmake: 3.30.5
  ninja: 1.12.1
  zlib: 1.3.1
  xz: 5.6.3
```

This is simple and keeps the build-time view clean. It is the preferred first implementation.

### Multiple foundation versions with namespaced views

Allow multiple versions, but never project them into the same unqualified view.

Example:

```text
foundation/zlib/1.2.13
foundation/zlib/1.3.1
```

This is more flexible but requires stronger module/view semantics and clearer package-manager guidance.

### Payload-owned dependency escape hatch

If a payload package requires a different version of a low-level dependency, that dependency should remain in the payload lane install graph and not be forced into the foundation view.

This avoids pretending that every dependency version can be globally unified.

## Concretization policy

Foundation reuse must be a policy decision, not an accidental consequence of a view path.

The concretizer should reuse foundation packages when the stack explicitly pins them. In the committed v1 model, payload lanes reuse compatible foundation/Core artifacts through configured buildcache mirrors. A future shared-foundation experiment may use Spack 1.2 lockfile inclusion (`spack: include: [...]`), but it is not part of the current per-compiler Core design.

Do not rely on `PATH`, `LD_LIBRARY_PATH`, or a flat view alone to make payload lanes reuse foundation packages.

## Acceptance criteria

A future hardening pass should make these behaviors explicit:

1. Foundation/Core packages have visibility metadata: internal, build-only, or public.
2. Foundation package versions are pinned or otherwise governed by a documented policy.
3. Public payload views do not blindly expose every transitive dependency.
4. Build-time views are separated from user-facing module surfaces.
5. Multiple versions of the same low-level dependency either collapse by policy or live in namespaced views.
6. Payload lanes can carry their own dependency version when foundation reuse would be wrong.
7. Composer renders view/module configuration from this policy rather than assuming one global view is safe.
8. The release manifest records which foundation/Core packages were reused by each payload lane.

## Non-goal

This note does not move MPI-capable, GPU-capable, or performance-sensitive scientific libraries into foundation/Core. Those remain in serial, MPI, or GPU payload lanes according to package-set intent and lane kind.
