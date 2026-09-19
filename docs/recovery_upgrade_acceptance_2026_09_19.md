# Locked workspace upgrade and delivery acceptance — 2026-09-19

This follows the [initial recovery implementation receipt](recovery_hardening_acceptance_2026_09_19.md).
It preserves the real cluster workspaces while testing maintenance on small
local fixtures. The production preparation path remains undecided.

## Implemented and locally verified

The explicit module-policy operation adopts only reviewed named views and paired
module settings. It requires an existing lock and active module configuration
scope, preserves non-view environment semantics, and guards all other local
configuration and frozen recipes during apply and restore. The separate overlay
admission operation verifies and installs only an inventory and trusted helper
against existing recipe bytes. Tag-only builtin configuration stays unchanged.

Independent review found two recovery defects before delivery: environment-local
package configuration was missing from restore guards, and interruption during
staging could leave an empty journal that blocked recovery. Both now have failing
regressions followed by fixes. Retained restoration does not back up external
view/module output roots; the operator must retain those separately before
regeneration.

The optional acceptance-and-push command records an explicit consumer command,
its output, exact roots and YAML/lock identities. Failure, timeout or changed
inputs blocks its signed push. Successful execution pushes those exact roots
with their non-external dependencies. This command does not activate modules
or change existing launcher defaults. Its automatic drift boundary is YAML and
lock bytes; included configuration, installed prefixes and external runtime must
remain quiescent and reviewed. OCI is refused because pinned Spack disables
signing for that destination type.

Stack Content's complete pilot suite passes **158 tests**, including **19** new
legacy upgrade cases, **24** existing transaction cases and **5** acceptance-gate
cases. Composer's required check passes **277 tests**, typing, dependency and
lint checks, including **11** added delivery regressions. These are local
regression results; real-Spack runtime evidence is recorded separately below.

## Older workspace rehearsals

The real historical input copy comes from the retained
`cse-gcc-oneapi-overnight-runtime/workspace`. Unlike the deliberately incomplete
tiny fixture, it already contains named views and older module settings. A copy
of its manifest, catalog, configurations, frozen recipes and environment inputs
passed **6 checks and 8 CLI commands**: module-policy preview/apply/restore and
inventory preview/admission/check/restore. The reviewed module change was
`autoload: none` to `direct` for GCC Core. All **243 original files and links**
remained unchanged. This proves historical input handling, not execution with
the historical compiler or its installed packages.

Evidence: `hpc-lab/results/stack-recovery/legacy-snapshot-inputs/report.json`,
input hashes, commands and `reproduce.py` in the sibling lab checkout.

The separate real-Spack older-shaped fixture deliberately omits view/module
policy and the overlay inventory/helper. It starts from an installed locked
consumer and dependency, then upgrades policy, regenerates the view and Tcl
module, loads the module and runs the consumer. Restore/reapply and inventory
admission/restore/reapply preserve lock bytes, specs, includes, tag-only common
repository configuration, recipe bytes, prefix locations, installed checksums
and timestamps. No solve or installation runs after the policy change.

The preliminary `20260919T232155Z-13664` run retained one fixture omission
failure (missing `scripts/` directory), followed by a passing bounded legacy
slice. Its resumed result is preliminary slice evidence. The final complete
run below establishes the uninterrupted result.

## Complete real-Spack run

The final run **`20260919T233912Z-16940` passed all 24 checks without resuming**.
Its recorded lifecycle time was **421.37 seconds**, within the 1,800-second outer
limit, with **103 command records** and **262 retained input files**. All recorded
runtime source digests still match the delivered implementation. Commands include
expected negative results; the 24 check outcomes are the acceptance assertions.
Evidence is retained under `hpc-lab/results/stack-recovery/20260919T233912Z-16940`
in both isolated and original lab checkouts. The final manifest SHA-256 is
`309f30d6b9dd245b679cc280c0969492e79a91c494a25c97af4f963ba919c309`.

An earlier startup attempt, `20260919T232809Z-16165`, failed before building when
container Git could not follow the host worktree's absolute metadata pointer.
The harness now records source commits on the host and actual file digests in
the container. That failed attempt remains in the evidence; it is not counted
as the final uninterrupted run.

The preliminary `20260919T232914Z-16252` run passed all **24 distinct checks**
across **103 commands**, with one targeted resume after correcting the fixture's
cache-blob location. Signed v3 manifests live under `v3/manifests`; their content
blobs live under the mirror-level `blobs` directory. The corrected negative
modifies the consumer archive selected by its signed manifest checksum, then
requires the resulting install to fail checksum validation in a fresh store.

| Additional case | Observed result |
| --- | --- |
| Dependency-only overlay | Dependency and consumer hashes both changed while the consumer recipe stayed identical. Installation succeeded, but the consumer rejected the changed result (43 instead of 42); the accepted original still returned 42. |
| Failed consumer before publication | The reusable gate retained the failed runtime output and exact lock evidence, attempted no push and created no destination cache. |
| Accepted consumer before publication | The gate pushed the exact recorded root with dependencies; GnuPG verified all four signed manifests. |
| Empty trust home | Cache-only installation failed signature verification and left the consumer absent. No mirror keys were automatically trusted. |
| Corrupted consumer archive | With the trusted key retained, altered archive bytes failed checksum validation; the consumer was absent from the new store and installed database. |
| Preserved baseline | Original YAML/lock hashes, dependency prefix and timestamp, plus the accepted public module snapshot, stayed unchanged. |

The original small lifecycle cases also pass: partial build and root overlay
repair, version/variant change, missing patch and wrong repository, real module
load, Inspector/static catalog/authored initialization, full render into a fresh
store, scoped presentation restore, signed publication and separate cache-only
consumption. Spack remains pinned to `1.2.2` at
`3e19345b6e12f5ff1b874f4059622fc6a1fd804a`, with builtin packages at
`d4f7c711a6a42f1c4d551c8fd10fce9a11340a81`.

The serial lab fixture uses real GCC and an explicit empty Ubuntu scope in its
private template copy. Raw Inspector observations are retained, with mock vendor
providers excluded from the reviewed fixture. This is neither production Ubuntu
support nor qualification of the full eight-environment CSE blueprint.

## Delivery and target qualification

The versioned receiver bundle uses exact committed source exports and the
existing offline builder. It includes matching Composer and `spack-build`,
Content and Planning, hash-locked helper wheels, source/file manifests,
checksums, a stdlib verifier and explicit receiving commands. A separate release
receipt records the actual archive checksum, source commits and rebuild proof.

Assembly qualification caught a helper import attempting to create bytecode
inside the sealed source export. The input-inventory check rejected that
assembly. The bundler now suppresses bytecode writes before loading its helper,
with a public captured-source CLI regression. Fresh capsules and builds replace
the rejected attempt; generated files are not admitted into its sealed manifest.
This packaging correction changes no rendering or maintenance runtime code.

Use the delivered [maintenance procedure](../../stack-content/pilots/cse-pilot/CONTROL-REFRESH.md)
and [acceptance gate procedure](../../stack-content/pilots/cse-pilot/BUILDCACHE-ACCEPTANCE.md).
Installing a versioned tool directory does not refresh a generated workspace.
Verified source deltas are also carried back to the original working branches,
preserving their pre-existing edits. No remote source update, buildcache upload
or cluster deployment occurs as part of these local rehearsals.

Remaining target work is the actual two CCE environments, their installed module
coverage, compiler/Fortran/MPI consumers and native launch paths, signing/trust
distribution and destination acceptance. The broader matrix also retains
interrupted acquisition/offline recovery, scheduler/node failure, post-activation
release rollback and full lab teardown/reconstruction as distinct tests. A fresh
private workspace inside an already running lab is not a cold lab rebuild.
