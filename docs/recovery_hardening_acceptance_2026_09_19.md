# Recovery implementation and local acceptance — 2026-09-19

The preservation boundary is the environments on the real clusters. The local
HPC lab is disposable. The implementation and tests use a tiny C library and
consumer to exercise recovery; they do not rebuild the CSE roster. Production
preparation remains undecided.

## Source delivery

Implementation is retained on `codex/recovery-hardening` in the
`Development/stack-recovery` worktrees. Verified changes are copied back into
the existing `codex/simplified-render-plan` working trees for Stack Composer,
Stack Content and Stack Planning. Their pre-existing work is preserved; those
original working trees are not silently reset or committed as one combined
change. The lab harness is also delivered to the original `hpc-lab` working
tree on `main`.

`Development/stack-recovery/baseline.json` records the source snapshots and
`source-sync.json` records the copied implementation files and hashes. No
cluster checkout, generated cluster workspace, lock, store, cache or published
module tree was updated by this work.

## Implemented behavior

- Control refresh supports presentation-only, controls-only and combined
  scopes, preview, whole-selection rollback, retained restore records and
  interrupted-operation recovery. It rejects protected build inputs,
  symlinks, overlapping paths, missing dependencies and unrelated later edits.
- Reviewed overlay inventories cover all six pilot recipes and support files.
  Candidate inventory creation is an explicit separate review step. Mutable
  recipe cache identity includes resolved repository paths and the admitted
  inventory, preventing stale same-namespace patch indices.
- Newly generated builtin references use the exact reviewed commit. Existing
  trial pins and locks are not advanced by changing source code.
- `cse-build compute modules --surface shared|platform` preflights installed
  locked prefixes and regenerates views and applicable named module sets. It
  does not fetch, install or solve. Sets sharing the Core tree preserve each
  other's modules. Publishing entrance modules remains separate.
- Full render honors repository priority and materializes API-v2 repositories
  at their required `spack_repo/<namespace>` path. Static catalogs retain the
  recommended common scope even when its package map is empty.

The executable cluster procedure is
[CONTROL-REFRESH.md](../../stack-content/pilots/cse-pilot/CONTROL-REFRESH.md).
The maintained local harness and its prerequisites are described in
[stack-recovery-acceptance.md](../../hpc-lab/docs/stack-recovery-acceptance.md).

## Local regression evidence

Stack Content's complete pilot suite passes **134 tests**, including 24
refresh/restore/recovery cases, generic inventory/cache tests, and five
generated-launcher module cases. The latter exercise the external command
boundary with controlled Spack responses; they are not source-build evidence.
The real module/build results below are separate evidence.

Stack Composer's required `scripts/check.sh` passes **266 tests**, dependency
consistency, typing, Ruff, shell syntax and diff checks. New public regressions
cover repository precedence, API-v2 and dotted namespace materialization, and
empty catalog scope availability.

## Real Spack lifecycle evidence

The run uses Spack `1.2.2` at
`3e19345b6e12f5ff1b874f4059622fc6a1fd804a` and builtin packages at
`d4f7c711a6a42f1c4d551c8fd10fce9a11340a81`. GCC 13.3 compiles actual fixture
sources. Detailed commands and outcomes are retained under
`hpc-lab/results/stack-recovery/20260919T201619Z-87418/manifest.json` in the
isolated checkout. Failed attempts remain visible in that evidence.

The run was resumed at specific stages while correcting harness and renderer
defects. This is aggregate per-case evidence, not a claim of a single clean
run from a fully torn-down lab. The maintained harness supports a fresh run
and bounded stage resumption.

Final manifest status is **passed**, with **16 distinct checks** and no
remaining selected checks. Its 104 command records include expected negatives
and failed development attempts, not 104 successful cases.

| Executed case group | Observed result |
| --- | --- |
| Partial build and overlay recovery | The dependency built before the deliberate consumer compile failure. A reviewed patch plus explicit new solve changed the consumer hash and passed the build; dependency hash, prefix and library timestamp were retained. |
| Overlay admission and selection | Inventory passed after a real recipe import; missing patch and wrong repository were rejected. Full render imported the authored zlib marker from the emitted API-v2 repository ahead of builtin. |
| Version/variant update | Version 2.0 with the feature enabled produced a distinct hash and executable output `recovery=42 feature=1`. |
| Modules | Real Tcl modules loaded and ran the consumer; an additional named set sharing the tree preserved the first set's module. |
| Static catalog and authored initialization | Inspector facts fed static render; an authored blueprint consumed selected scopes, initialized, solved and installed the fixture. Empty recommended scopes were verified present. |
| Full render | The reviewed local profile and adapted lab OS template produced an environment that solved, built in a separate fresh store and ran `recovery=42 feature=0`. |
| Presentation maintenance | Preview, apply and CLI restore preserved the existing lock, environment YAML, workspace manifest, builder control and separate accepted public snapshot. |
| Cache publication/consumption | Four v3 manifests had valid GPG signatures. A separate empty store installed with `--cache-only` and ran the consumer; an empty mirror failed with no source-build fallback. |

The small fixture therefore covers both generated preparation paths and
independently authored Spack environments. It does not run the entire eight
environment CSE blueprint, `spack-build` publication chain or every R1–R12 case
as one integrated test.

### Acceptance boundaries

The full-render lab fixture adds an explicit empty Ubuntu 24 scope to a private
copy of the templates because maintained production content currently covers
RHEL and SLES. This is an adaptation for the observed lab OS, not production
Ubuntu support. Raw Inspector output is preserved; the reviewed full-render
fixture selects actual GCC/OpenMPI facts and excludes existing mock vendor
compiler surfaces in the lab. Fixture source builds establish the general overlay and
package-intent recovery cycle; they do not qualify CCE, Fortran ABI, physical
MPI fabrics, scheduler interruption or any production scientific result.

The public pointer in this test is a local fixture. Real CSE publication still
requires its reviewed exact artifact set, signing/trust distribution,
cache-only destination acceptance, clean user-module tests and native launch
checks. Existing cluster workspaces keep their old launcher until a deliberate
qualified refresh; new helper prerequisites must be admitted before installing
new admission controls.

The [R1–R12 matrix](stack_failure_recovery_and_test_matrix_v1.md) remains the
broader acceptance target. Still distinct from these small cases are a
transitive recipe-change scenario, interrupted acquisition/offline recovery,
consumer failure after a successful installation, corrupt/untrusted cache
artifacts, post-activation release rollback and a fully fresh target rebuild.
These are not reported as passed by the current fixture run.

## Cluster rollout order

1. Keep each real system's recorded catalog, values, environment files, locks,
   install database and prefixes. Export approved exact hashes to a candidate
   buildcache if desired; successful export does not finish module acceptance.
2. Update preparation sources/tools independently of generated workspaces.
   Review a separate render against recorded inputs before adopting controls.
3. For completed environments, validate their existing module/view policy,
   use presentation-only refresh where sufficient, and regenerate package
   modules from installed locks. A source update does not fill missing legacy
   module configuration automatically; review that configuration delta before
   applying a new helper. Keep package input changes out of this maintenance.
4. On the two unfinished CCE systems, resume unchanged installs normally.
   When a package/variant/recipe change is required, create the affected
   candidate, admit its overlay inventory, solve explicitly, inspect the graph
   difference and run the native defect/consumer tests. Keep completed graphs
   available throughout.
5. Complete target module, consumer, signing/trust and cache-only destination
   checks, then promote under the CSE SOP. Local fixture success does not
   choose a production preparation path or activate a cluster release.
