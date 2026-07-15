# Manual build walkthrough (v1)

| Document control | |
|---|---|
| Date | 2026-07-14 |
| Status | Draft for the Blueback demo |
| Audience | App managers and anyone who wants to build their own software |

## What this is

Building your own software against a system's supported compilers and MPI, by
hand, with ordinary Spack commands. No curated stack, no renderer, no
coordination with anyone. The platform catalog hands you the machine's facts as
ready-to-include Spack configuration. Everything above that is yours.

This is the answer to "I know what I want to build, I do not want to be in a
lane." It is a first-class path, not a fallback. The curated stack exists for
users who would rather never run a Spack command; the catalog exists for people
who would rather run their own.

## What the catalog gives you

One directory per system per release, generated from that system's reviewed
fact sheet:

```text
<system>/static/<release>/
  README.md                                  the include block for this system
  manifest.yaml                              every scope, plus the recommended defaults
  scopes/common/                             site externals (openssl, curl, fabric userspace)
  scopes/compilers/<name>/<version>/         the compiler as an external, plus its toolchain
  scopes/mpi/<provider>/<version>/<compiler>-<version>/
                                             the MPI flavor built for that compiler
  scopes/gpu/<toolkit>/<version>/            the GPU toolkit as an external
  reports/static-plan.yaml                   what was selected and what was left out, and why
```

Every scope is ordinary Spack configuration. Nothing in it is specific to the
curated stack, and nothing in it requires our tooling to consume. A scope looks
like this:

```yaml
packages:
  cray-mpich:
    buildable: false
    externals:
    - spec: cray-mpich@<version>
      prefix: /opt/cray/pe/mpich/<version>/ofi/gnu/<compiler-version>
      modules:
      - cray-mpich/<version>
    variants: +wrappers
  mpi:
    buildable: false
    require:
    - cray-mpich
```

That is the whole trick. `buildable: false` plus a prefix and the module chain
means Spack uses the machine's MPI instead of building one, and `require`
points the `mpi` virtual at it. The value of the catalog is that someone
already worked out the exact prefix, the exact module chain, and the compiler
pairing, and that a person reviewed those facts before they were published.

## Walkthrough: Blueback, GCC surface

### 1. Find the catalog

It is published with the system's stack source, under
`systems/blueback/static/<release>/`.

### 2. Read the include block

```bash
cat systems/blueback/static/<release>/README.md
```

The README is generated for this system and names the exact scopes for each
surface, with absolute paths. Copy the block for the GCC surface rather than
typing paths by hand: the versions in those paths are the ones the machine
actually has, and they move when the programming environment moves.

### 3. Write an environment

An ordinary `spack.yaml`. The include block came from the README; the specs are
whatever you want.

```yaml
spack:
  include:
  - <catalog>/scopes/common
  - <catalog>/scopes/compilers/gcc/<version>
  - <catalog>/scopes/mpi/cray-mpich/<version>/gcc-<version>
  specs:
  - mytool@1.2 +mpi
```

Include only what you need. A serial build takes the common and compiler
scopes and stops there. A GPU build adds the GPU scope.

### 4. Concretize, then check before installing

```bash
spack -e . concretize
```

Read the output before you install anything. The check that matters: the
compiler, `cray-mpich`, and any GPU toolkit must appear as **externals being
used**, not as packages to build. If Spack proposes to download and build an
MPI, the include block did not take effect, and the fix is in the environment
rather than anywhere downstream. Stop and fix it there.

### 5. Install

```bash
spack -e . install
```

### 6. Expose it, if you want to

Write a modulefile per version and put it in a directory that is already on the
system's module path, or that your users add themselves. The curated stack does
not need to know, and nothing about it changes.

## Reusing what the curated stack already built

If the curated stack is installed on the machine, you do not have to rebuild
its packages to depend on them. Point Spack at its install tree as an
**upstream**:

```yaml
# ~/.spack/upstreams.yaml
upstreams:
  cse-stack:
    install_tree: <the install tree from the deployment overlay>
```

Spack then treats those installs as already present. It reuses them in place,
builds only what is missing, and puts what it builds in your own tree. The
curated tree stays read-only to you, which is why this works without anyone
granting write access to a published release, and why your builds never appear
in someone else's release manifest.

Concretize again with the upstream configured and watch what happens to a
dependency the curated stack already carries, such as HDF5.

**This is the check that matters, for us more than for you.** If your build
reuses the curated HDF5 without rebuilding it, the catalog is complete: every
pin that decides the hash (compiler reference, MPI flavor, CPU target, package
recipe generation) is in those scopes. If it rebuilds instead, something is
missing from the catalog, and we would rather find that here than have a user
find it. Report a rebuild as a bug against the catalog.

## What you own, what the site owns

| Owned by the site | Owned by you |
|---|---|
| The fact sheet: which compilers, MPIs, and GPU toolkits exist, and where | Which of them you use |
| The catalog: those facts as reviewed, include-ready Spack config | Your `spack.yaml`, your specs, your versions |
| The curated stack's install tree, if you choose to reuse it | Your own install tree, your modulefiles, your users |

The catalog is the seam. It exists so that software built outside the curated
stack still matches the machine, without its author having to rediscover the
machine's facts or coordinate with anybody.
