# Foundation And Core View Semantics Note v1

## Status

Current design note. Foundation is ambient in the user-facing view; Core tools
are the loadable layer. The Initial Conversion Trials build both layers per
compiler surface and verify reuse only within that surface.

## Context

The stack model already separates package intent by lane kind. Serial, MPI, and GPU lanes are for packages that require those build surfaces. MPI-capable libraries and applications such as HDF5, NetCDF, PNetCDF, TAU, and GPU-enabled packages do not belong in a shared foundation or Core layer merely because many lanes depend on them.

The unresolved question is narrower: how should the stack expose, reuse, and constrain low-level build tools and ABI-stable dependencies that can be shared across compiler/MPI/GPU lanes?

Examples include two distinct groups that this note must not blur:

```text
Core tools (user-loadable):     cmake, ninja, pkgconf, git, python, miniforge
Foundation libraries (ambient): zlib, xz, zstd, bzip2
```

These packages are built once per compiler surface at the baseline CPU target,
then reused by the Common, Serial, and MPI environments on that same compiler
surface.

## Working definitions

### Foundation layer

The foundation layer is the lowest shared layer: **ABI-stable libraries that
are ambient in the user-facing view**, per the v6 master design, "the user's
compiler picks them up without an explicit choice." They are single-version
per release generation, pinned with `require:` lines in the common scope,
because the user-link path (a fresh compile, where RPATH has not happened yet)
must be unambiguous. The membership discriminator is v6's rule: *does a user
`-l` this directly*, not "is it low-level." OpenSSL, for example, stays a
private RPATH-isolated transitive dependency and needs no pin. Foundation is
optimized for portability and reuse, not for target-specific performance.

A foundation package should generally be:

- independent of MPI provider;
- independent of GPU runtime;
- safe to reuse across payload lanes on the same compiler surface as a build
  tool or low-level dependency;
- built for a baseline CPU target such as `x86_64_v2` or `x86_64_v3`, not for a specific compute-node microarchitecture;
- narrow enough that version policy remains understandable.

### Core lane

A Core lane is compiler-adjacent stack infrastructure holding the **loadable
tool layer**: build and user tools such as cmake, ninja, pkgconf, git, and the
miniforge/python user environment (the v6 `core-foundation` package set).
Core tools are user-facing: users load them (as modules or via the lane
view's front door) the way ALCF users `module load cmake` from spack-pe-base.
Core version policy is explicit in the roster. Multiple public tool versions
are allowed when they are intentional and have distinct modules. The Initial
Conversion Trials expose CMake 3.31.12 and 4.4.2, while package builds pin
CMake 3.31.12. Core builds at the portable baseline target, not the payload
target. A prebuilt architecture-specific distribution is different from a
source-built Core tool: Miniforge uses the generic `x86_64` family target and
has no compiler-language dependency.

The current pre-v1 deployment shape owns Foundation and Core per compiler
surface. Foundation and Core are groups inside each surface's Core environment.
The Common, Serial, and MPI environments repeat that surface's compiler,
Foundation, and required build-tool groups and use Spack 1.2 `needs` to make
those producers available for exact reuse:

```text
shared GCC producer -> GCC Foundation -> GCC Core
                    \-> GCC Common/Serial/MPI payload groups

platform compiler external -> platform Foundation -> platform Core
                           \-> platform Common/Serial/MPI payload groups
```

There is no separate public Foundation environment or lane. Cross-environment
reuse is accepted only when the repeated producer hashes match across the
environments on that compiler surface. The shared Spack store and build cache
then avoid rebuilding those exact hashes. The trial's current front-door
exposure may prepend the shared GCC Foundation view for both compiler surfaces;
that is an exposure choice and does not make the platform surface consume the
GCC-built Foundation during concretization.

## Visibility policy

The two layers have opposite exposure shapes, and neither is "internal":

- **Foundation libraries are ambient**: projected into the user-facing lane
  view so a user's own compile links them without an explicit choice. They do
  **not** get per-package modules: a module implies a choice, and foundation
  is exactly the layer where there is no choice (single pinned version).
- **Core tools are loadable**: exposed for users to pick up explicitly
  (module-exposed or front-door view), like any user-facing tool.

Recommended default:

```text
foundation package visibility: ambient in the lane view; never per-package modules
core package visibility: user-loadable (module or front-door view)
payload package visibility: public according to stack/module policy
```

This gives users the tools they reach for by name, gives their compiles the
ambient single-version link surface, and avoids per-package module sprawl for
libraries nobody "loads."

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

The concretizer should reuse Foundation and build-tool packages when the stack
explicitly pins them. Each independent environment on the shared GCC surface
repeats the exact stack-built compiler producer group. Each platform environment
uses the exact selected external compiler and builds its own Foundation and
build-tool roots. `needs` orders stack-built producers and makes their concrete
results available; a conditional compiler toolchain on Foundation, Core, and
payload roots actually selects the surface. Soft language-provider preferences
alone are insufficient because Spack may select the external seed compiler.
The lockfile gate verifies one shared GCC producer hash and matching
Foundation/build-tool hashes within each compiler surface. Restricted and
publication installs reuse those hashes through the shared store and configured
build cache.

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

This note does not move MPI-capable, GPU-capable, or performance-sensitive scientific libraries into foundation/Core. Those remain in serial, MPI, or GPU payload lanes according to package-set intent and lane kind. Packages that are payload (not compiler-agnostic) yet usable from every lane are handled by lane-agnostic exposure (one serial-lane build, module-visible in every payload lane), decided 2026-07-13 in `lane_and_module_model_v1.md`, not by promotion into Core.
