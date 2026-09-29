# Package-overlay semantics and operating controls for pinned Spack 1.2.2

| Document control | Value |
|---|---|
| Date | 2026-09-19 |
| Status | Primary-source research note; not an operator procedure, deployment approval, or target-system acceptance record |
| Local baseline examined | Spack `v1.2.2` / `3e19345b6e12f5ff1b874f4059622fc6a1fd804a`; `spack-packages` `v2026.06.0`; local `cse_trials` API v2 repository |
| Method | Official Spack documentation and source at the pinned tags, official post-release fixes, and the current CSE pilot files |

## Finding

The CSE overlay mechanism is a supported Spack composition pattern: put the
local repository before `builtin`, resolve unqualified packages from the first
matching repository, and subclass a class imported from the pinned `builtin`
namespace. That pattern does not by itself provide a complete correction
lifecycle. Spack 1.2.2 preserves an existing lock unless reconcretization is
forced, can reuse installed or cached dependencies, omits resource payloads
from its content hash, and has a post-release namespace bug affecting hashes of
shadowed packages. The resulting lifecycle controls are an explicit admission
record, positive and negative scope checks, freshening of every affected node,
source-build and runtime evidence, signed artifact promotion, and a retained
prior release for rollback. Apply them now only to the two unfinished CCE
systems. The other trial environments are completed evidence and should be
preserved; the broader controls belong in the next planned refresh.

The configured pins were also the latest official releases when checked on
2026-09-19: the official APIs returned [Spack `v1.2.2`](https://api.github.com/repos/spack/spack/releases/latest)
and [`spack-packages` `v2026.06.0`](https://api.github.com/repos/spack/spack-packages/releases/latest).
That is an observation, not a reason to treat either pin as self-updating or
permanently supported. Current `develop` already contains a relevant fix that
is absent from `v1.2.2`.

## Repository selection and inheritance

Spack 1.2.2 searches the merged `repos.yaml` from highest-precedence scope to
lowest and top to bottom within a file; the first repository containing an
unqualified package wins. It repeats that search for dependencies. `spack spec
-N` can expose namespaces during an explicit candidate solve
([v1.2.2 repository search order](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/repositories.rst#L364-L410)).
The rendered order `cse_trials` then `builtin` is therefore semantically
significant, not presentation. For an existing trial lock, the preflight must
not solve an abstract root. Follow the operating procedure's configured
repository-location and loaded-class-file inspection, then inspect the locked
DAG with `spack -e <env> find -c -d -L -N -v`. Use an abstract `spack spec -NIl`
only when deliberately evaluating a candidate for a new lock. A package
directory's presence alone does not prove which recipe the lock selected.

API v2 repositories may import and subclass a package class through
`spack_repo.<namespace>.packages...`; Spack documents this as the way to make a
derivative recipe without copying the original
([v1.2.2 repository inheritance](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/repositories.rst#L565-L597)).
For CSE's subclass overlays, the effective recipe is consequently the tuple
of the Spack-core commit, pinned `builtin` commit, local-overlay commit, and
repository order. Removing an overlay or advancing `builtin` changes that
tuple and requires the same review as adding an overlay.

There is an important verification question. The v1.2.2 package hasher parses
the selected `package.py` source, and the cited function does not show recursive
hashing of Python files imported as parent recipe classes
([v1.2.2 canonical recipe hashing](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/util/package_hash.py#L337-L394)).
That is a source-based inference, not a controlled runtime result: inherited
directives may alter the concrete spec, and `content_hash()` also includes
source and applicable patch identities. Before relying on the claim, compare
the package and DAG hashes in a small v1.2.2 experiment that changes only an
inherited build method. Meanwhile, keep `builtin` immutable for a release, diff
every inherited base when advancing the pin, and do not treat an unchanged
overlay DAG hash alone as proof that inherited behavior is unchanged.

## Hashes, patches, lockfiles, and reuse

For a concrete spec, the v1.2.2 DAG hash includes build, link, run, and test
dependencies plus a package content hash
([hash descriptor](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/hash_types.py#L52-L67)).
The package content hash combines source identity, each applied patch's SHA-256
and patch level, and canonicalized recipe source
([`PackageBase.content_hash`](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/package_base.py#L1838-L1898)).
The concretizer injects applicable patch SHA-256 values into the spec
([patch assignment](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/spec.py#L5789-L5853)).
This supports a strong acceptance check: after a patch, recipe, or applicability
condition changes, the affected concrete node must have the intended namespace,
patch list, package hash, and DAG hash, and the lockfile delta must be reviewed.

Those hashes do not update an existing environment automatically. The
environment docs state that ordinary `spack concretize` leaves already
concretized specs unchanged and `spack concretize -f` is required to ignore the
existing concrete environment
([v1.2.2 reconcretization rule](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L758-L762)).
The CSE command `concretize -f --reuse-deps` means “fresh roots, reusable
dependencies”; installed packages and build caches remain eligible for
dependency reuse
([v1.2.2 reuse modes](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/build_settings.rst#L40-L69),
[CLI mapping](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/common/arguments.py#L643-L679)).
It is sufficient only when every changed overlay node is a root. If an overlay
is transitive, make it an explicit validation root, exclude it from each reuse
source, or use `--fresh`; then assert that its old hash was not selected.

Two pinned-version gaps require controls outside the hash:

- `PackageBase.content_hash()` contains an explicit `TODO: resources` and does
  not add resource payload identities to the hash
  ([v1.2.2 source](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/package_base.py#L1852-L1878)).
  Record and compare every applicable `resource()` URL/commit/checksum in the
  admission record, and force a clean source build when one changes.
- v1.2.2 looks up the recipe to hash by `spec.name`, rather than the fully
  qualified namespace. The upstream fix landed on 2026-07-23, after the
  v1.2.2 release, and changes both lookups to `spec.fullname`
  ([official fix `20a2306`](https://github.com/spack/spack/commit/20a23061245eff65fd609957e15e3ad06fd53eb7)).
  Until CSE advances or backports that fix, a hash comparison involving a
  fully qualified shadowed `builtin.<name>` while a higher-priority overlay is
  registered is not reliable. Compare the recipe and patch bytes directly and
  validate hashes in isolated repository configurations as well as in the
  effective overlay configuration.

## Scope guards and HPC validation

Package constraints can bind versions, variants, and compilers, and `when`
can make a requirement conditional. The v1.2.2 docs also warn that the solver
may avoid a conditional requirement's trigger when that improves its score
([package requirements](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packages_yaml.rst#L399-L508)).
Therefore a narrow `when=` on a patch or method is necessary but not sufficient
evidence of scope. For the two unfinished CCE systems, limit checks to their
affected CCE locks and preserve completed environments. During the next planned
refresh, evaluate each changed overlay with a candidate matrix containing:

- each intended version, compiler family, and relevant variant combination;
- the nearest excluded versions and the opposite variant states;
- every supported compiler surface, even when the reported defect occurred on
  only one surface; and
- the same package as both a root and, where applicable, a dependency.

The candidate result should show that intended cells select `cse_trials`, the
expected patch SHA or method path, and a new DAG hash, while excluded cells do
not receive the correction. This is especially material for compiler-specific
linker workarounds: a version-and-variant guard without a compiler guard applies
to every compiler that satisfies the spec.

Spack distinguishes build-time tests from post-install stand-alone tests
([v1.2.2 testing model](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_testing.rst#L34-L40)).
Build-time checks require `spack install --test=root`; stand-alone tests run
against installed packages with `spack test run`, and only packages that define
such methods appear in `spack test list`
([build-time invocation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_testing.rst#L112-L118),
[stand-alone test behavior](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_testing.rst#L942-L983)).
An install success or empty test list is not a validation result. Evidence for
a changed overlay should include a defect-shaped smoke test: compile/link/run
for libraries, the actual MPI/Fortran interface for module-path fixes, and a
dependent configure/build for build-tool or linker corrections. Run it from
the installed prefix on the target compiler/provider lane and retain logs.

## Buildcache, promotion, rollback, and security lifecycle

Spack creates buildcache artifacts from locally installed specs and signs their
metadata by default; consumers install artifacts whose keys they trust
([v1.2.2 buildcache creation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst#L27-L49),
[signing and trust](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst#L217-L288)).
For a new or refreshed release, do not publish an overlay artifact until the
source build and lane tests pass. Publish the exact accepted DAG hash to a
candidate cache, verify it by a cache-only install and rerun smoke tests, then
promote that immutable hash and update the index. Do not use `--unsigned` or
`--no-check-signature` for the release path. This is next-refresh policy; it is
not a request to republish completed trial environments.

Package signatures do not authenticate the cache catalog: v1.2.2 explicitly
says buildcache index manifests are not signed
([index-manifest limitation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst#L677-L704)).
Record the promoted index checksum or protect the publication channel
separately, and always verify the selected package signature and DAG hash.

Rollback should restore a retained release unit rather than mutate the failed
one in place: prior overlay and builtin commits, repository order, `spack.yaml`,
`spack.lock`, accepted buildcache hashes, signing-key fingerprint, modules/views,
and validation evidence. A lockfile contains fully concretized specs and can
recreate the same concrete specs on a compatible machine
([v1.2.2 lockfile model](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L44-L46),
[recreation guarantee](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L73-L121)).
Keep the previous cache artifacts and module tree addressable until the new
release has passed its soak period; switching the published release pointer
back is the rollback.

Pinning does not end maintenance. The official Spack security policy promises
updates for `develop` and the last two stable series, but its text still names
those series as `0.x`, even in the v1.2.2 tag; it does not clearly map that
promise onto 1.x lines
([v1.2.2 `SECURITY.md`](https://github.com/spack/spack/blob/v1.2.2/SECURITY.md#L1-L24)).
CSE should monitor Spack and `spack-packages` releases, advisories, and relevant
post-release fixes; assess the pinned core, builtin recipes, sources, resources,
patches, and buildcache keys separately; and allow an expedited reviewed update
when a security fix outweighs the normal pin-aging rule.

## Current CSE boundary and next-refresh controls

The pilot and the corrected customization inventory both carry six recipe
overlays (`cce`, `cmake`, `dakota`, `hdf5`, `ncurses`, and `zlib`). Only two
unfinished systems remain and both use CCE; completed trial systems and locks
should be preserved. The runtime repository template places the local
repository first but renders the builtin repository by tag, even though the
separate
[snapshot-admission note](spack_repository_snapshot_admission_research_v1.md)
recommends a full commit as runtime identity. Address that pin form during the
next planned refresh rather than changing completed trials.

Workspace initialization records a digest of the source template tree; it
does not create a separate, generic final manifest of overlay state after
manual on-site corrections. The next refresh should add or preserve explicit
per-correction evidence: recipe and supporting-file digests, repository/class
selection, locked-DAG output, old and new affected hashes, test logs, and the
accepted buildcache identity. Until then, use the package-specific manual
overlay record and the existing lock evidence for the two unfinished CCE
systems.

This research did not itself execute Spack 1.2.2 on a CSE target, inspect a live
shared store or cache, or validate a correction on Blueback, Raider, or another
cluster. It does not invalidate completed trial evidence. The proposed controls
apply to the two unfinished CCE systems where relevant and to the next planned
refresh.
