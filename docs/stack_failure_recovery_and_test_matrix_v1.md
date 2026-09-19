# Stack failure recovery and test coverage v1

**Date:** 2026-09-19  
**Status:** Operating assessment, implemented recovery controls, and remaining acceptance matrix.
**Production choice:** Undecided; assess all supported environment preparation paths.  
**Current constraint:** Finish the two remaining CCE systems; preserve completed builds.

## 1. Three preparation paths, one downstream lifecycle

These are alternatives, not three steps every build must run:

| Path | Authored inputs and preparation | Downstream execution |
| --- | --- | --- |
| Static catalog with authored environment | Inspector profile → `render-static` → reviewed catalog scopes; package manager authors `spack.yaml`, package choices and deployment configuration | Bare Spack or the selected build driver |
| Authored blueprint workspace, including current CSE trials | Reviewed static catalog + blueprint/templates + roster/policy + explicit values → `init-workspace` | Current CSE blueprint supplies `cse-build`; the assembler itself never builds |
| Standard full-render workspace | Profile + deployment + defaults + stack/package intent + templates/repos → `render` | `spack-build`, bare Spack, Ansible, `spacktools`, or another explicit downstream driver |

Full render does not require first running `init-workspace`, and the static
catalog consumer does not require full render. Choosing a workspace generator
does not choose the build driver. The supported
[blueprint-assembler decision](adr/0001-retain-workspace-blueprint-assembler.md)
and [build handoff](stack_build_handoff_note_v1.md) establish these boundaries.
The full-render implementation gaps remain relevant to testing that path, not
a reason to move current trials to it or choose it for production.

The common lifecycle is:

```text
review platform facts/configuration
  -> author package intent and any recipe corrections
  -> prepare and inspect a candidate environment
  -> solve and review the complete affected dependency graph
  -> acquire approved inputs
  -> build selected concrete packages
  -> validate packages, consumers and user entry points
  -> approve and publish under the selected policy
  -> verify publication and retain rollback evidence
```

The [shared SOP](software_stack_sop_v1.md) owns these operations. The
[CSE SOP](cse_software_stack_sop_v1.md) adds CSE policy; the trial
[runbook](runbook.md) selects concrete commands. Recovery returns to the earliest
stage whose inputs changed, retaining evidence from the failed attempt and
repeating dependent checks. It does not restart unrelated completed work.
For CSE, publication uses signed approved binaries and a cache-only destination
installation. Shared SOP §10 also permits direct publication of a validated
installation where the applicable policy allows it; cache-only publication
is not imposed on every independent catalog consumer by the architecture.

Catalog preparation and catalog publication are distinct. For current CSE
operations, CSE SOP §10.2 retains its rule to publish the reviewed catalog after
restricted stack validation/build-cache checks. Independent catalog consumers
use the published artifact under shared SOP §§6 and 10.2. Alternative
preparation paths do not silently waive the current CSE publication policy.

Older text calling `init-workspace` temporary, or full render the predetermined
production path, must be read against the supported-assembler decision and
the owner's current decision to keep production selection open. No existing
trial topology, locks, package policies or command interface changes as a
result of this assessment.

## 2. What the current workspace pre-check actually checks

Existing cluster workspaces retain the verifier they were generated with. The
table immediately below describes that original deployed trial baseline. The
updated source has the generic inventory gate described after the table; source
updates do not automatically replace a cluster's controls.

The [trial launcher](../../stack-content/pilots/cse-pilot/templates/cse-build.j2)
calls `verify_workspace_inputs`, which runs the generated
`scripts/verify-lockfiles.py --workspace-only`, before dispatching the requested
action. This is a Stack Content blueprint control, not a generic Composer
feature or a Spack requirement.

The [verifier template](../../stack-content/pilots/cse-pilot/templates/scripts/verify-lockfiles.py.j2)
has two distinct jobs:

| Mode | Actual checks | What a pass does not prove |
| --- | --- | --- |
| `--workspace-only` | Read Dakota and HDF5 recipes/patches, require specific declarations and patch fragments; inspect generated managed-GCC producer, `needs`, reuse and toolchain configuration | All overlay files are approved/complete; Spack selected their classes; patches apply; packages build or run |
| Full verification | Repeat input checks; require the expected eight lockfiles and check authored compiler/provider, target, package/version/chain and shared-hash invariants | Those concrete packages are installed correctly; scientific output is correct; public modules work; arbitrary new package policies were checked |

For Dakota, the pre-check recognizes the existing Boost.System correction. For
HDF5, it recognizes the `2.1.0+mpi+fortran+hl` MPI Fortran module-directory
correction. It checks recipe/patch text, not HDF5 execution. Its success message
is broader than this package coverage: the repository has six overlays but
the package-specific pre-check handles only these two.

### Does every new overlay require another check in `cse-build`?

Spack can use a new overlay as soon as the complete recipe is in the registered
repository and the affected candidate is correctly solved. No new launcher
branch is inherently required. In the original verifier, that new package does **not**
automatically acquire the Dakota/HDF5 safety checks.

Every correction needs a regression check for the defect and evidence for its
scope. That does not mean embedding more package names and patch strings in
the launcher. The implemented separation is:

1. **Generic input verification:** expected repository identity/order, complete
   reviewed file inventory, digests and local support files, selected recipe
   class, and input revision corresponding to the candidate locks.
2. **Graph verification:** resolved versions/variants/providers and the affected
   dependency/consumer hashes satisfy the authored requirements. Shared-producer
   rules come from the selected environment contract; the eight-environment
   CSE layout is not universal policy.
3. **Package regression and runtime checks:** reproduce the original defect,
   prove it fixed, and exercise affected consumers plus an unaffected control.

The current source's `scripts/verify-overlay-inputs.py` reads the reviewed JSON
inventory and checks every repository/support-file identity without importing
recipes. Its `--candidate OUTPUT` mode writes a separate review artifact;
normal checks never approve current bytes automatically. New package admission
therefore needs an inventory update and defect regression, not another package
name in the launcher. Actual Spack class selection and input-to-lock provenance
remain separate downstream checks. Candidate recipe caches include the resolved
repository paths and inventory identity, avoiding stale patch indices when a
same-namespace overlay is moved or changed.

The updated launcher requires the helper and admitted inventory. Refresh checks
those prerequisites before adopting controls. Existing trials can update
presentation separately; new admission controls are qualified in a candidate.

The same three kinds of evidence apply to authored, initialized and fully
rendered environments. A bare-Spack operator must run the chosen checks
explicitly; using Spack directly does not invoke `cse-build`'s checks.

### Existing locks and surface selection are separate concerns

The current `cse-build concretize` creates missing locks and preserves existing
ones. Rerunning it after editing a variant or recipe is not a recovery of an
existing lock. The overlay procedure's explicit affected-lock solve and graph
comparison are necessary.

The updated launcher's `--surface` option narrows `status`, `fetch`, `install`
and the new installed-package `modules` action;
it does not narrow `concretize` or `verify`. Full verification requires all
eight trial locks. After a targeted diagnostic solve, run the full trial
verifier only against a coherent candidate set; do not copy or rewrite
completed locks just to satisfy it. An intentional graph change that no
longer fits the trial invariants needs an explicit policy/candidate decision.

The launcher also checks the Spack **tool** checkout's exact commit and clean
state. That is separate from the builtin **package repository**, whose trial
configuration was tag-based. Newly generated pilot and v6 candidates use the
full builtin commit. This does not advance an existing workspace's pin.
Neither identity check establishes package runtime correctness.

## 3. Failure and re-entry matrix

“New candidate” below means preserving the old input/lock/evidence set and
following the runbook's semantic-change release rule. It does not mean
rebuilding every package or replacing completed environments. The
[overlay operating map](package_overlay_operating_model_v1.md) supplies the
source/deployed path map and affected-environment evidence record.

| Failure or needed change | Fix belongs to | Return to SOP / repeat | Preserve and stop condition |
| --- | --- | --- | --- |
| Wrong/dirty Spack runtime, missing bootstrap input or unapproved repository identity | Tool/input admission or operational checkout replacement | §§4.4–5; verify approved exact identity before solving | Same-identity replacement can resume; advancing code/recipes is a reviewed input change |
| Wrong/missing compiler, MPI, external prefix or module facts | Observed profile/hints or reviewed platform inputs | §§5–6; review corrected facts and new catalog where consumed; prepare affected candidate and review its graph | Preserve original profile/catalog and completed locks; do not edit a shared released scope in place |
| Invalid input, unavailable template field, duplicate YAML or failed workspace promotion | Owning authored input/template or renderer defect | §7.5 workspace inspection; assemble into a separate output, then review before solving | A failed render must not replace existing output; successful overwrite is not a safe partial-build refresh |
| Workspace pre-check reports stale/missing known correction | Correct recipe payload or actual authored input; distinguish stale checker from invalid content | §7.6 for overlay; §7 for configuration; repeat input and selection checks | Do not bypass the gate or blanket-update all controls; diagnose its specific condition |
| Solve rejects a version/variant or finds conflicting constraints | Package intent, dependency policy, or a recipe defect if the source supports the request | §7 or §7.6, then §8; solve and inspect candidate graph | A source-code defect and an unsupported requested feature require different fixes |
| Solve succeeds with the wrong variant/version/provider chain | Authored specs/roster/package policy/toolchain selection | §7, then §8; compare all affected graph nodes and reapprove | Stop before installation; never edit the lock manually or treat installed prefixes as the intended graph |
| Independent review holds the candidate or requests changes | Evidence owner or the specific authored-input owner | §8.1; complete evidence for unchanged inputs, or create a new candidate if inputs/hashes change | Hold build/publication gates that require approval; do not treat a retry as approval |
| Requested variant/version changes after some packages are built | Authored package intent and any necessary recipe correction | §§7–8, then §9 for changed packages and affected consumers | New candidate; retain completed baseline; review shared dependencies and compare actual changes with declared scope |
| Missing source/resource/patch or interrupted download | Approved source acquisition/mirror | §9.1–2; fill required inputs for the existing approved lock | Same inputs can retry; changed checksum/source identity requires input review, not checksum bypass |
| Timeout, node loss, quota, temporary stage/access problem | Operational setup | §§5 and 9.3; retry failed command/concrete package in correct node context | Keep semantic inputs and locks unchanged; preserve the first failure log and stage evidence |
| Configure/compile/link failure needing a recipe/source correction | Package overlay, narrowly scoped to demonstrated cause | §7.6 → §8 → §9; select corrected recipe, recover candidate lock, verify actual source build, reproduce passing result | Preserve old package/lock; review transitive consumers; no global compiler/linker workaround without owning-input review |
| Corrected solve still selects old dependency or install skips existing hash | Reuse policy, selected namespace/hash, or unchanged effective inputs | §8; inspect why old graph remains before a new retry | `--no-cache` does not force reinstall; never delete shared prefixes or change an unrelated flag just to manufacture a new hash |
| Package installs but consumer, numerical result, MPI or API test fails | Diagnose recipe, package policy or provider/runtime owner | §9.3 diagnosis, then return to §6/7/7.6 if those inputs change | Hold acceptance and retain failed runtime evidence; successful installation alone is insufficient |
| Module/view presentation fails with unchanged DAG | Presentation templates/deployment policy | §9.3 and §§10–11 acceptance; repeat clean user-entry checks | Do not solve again merely to fix presentation; accepted presentation still needs a new reviewed release |
| Cache upload/signature/inventory verification fails | Publication transport, trust or evidence | §10.1; retry approved exact artifacts after correcting the failure | No success record on failed push; changed artifact identity returns to restricted acceptance |
| CSE/cache-only publication cannot find or verify an approved binary | Candidate cache completeness or publication input | §10.3; return missing artifact to restricted preparation | Stop; no source-build fallback and no publication-time reconcretization |
| Destination candidate fails target/user acceptance before activation | Preserve failed candidate; diagnose changed stage | §10.3; hold publication/default change and return to the owning stage | Prior accepted entrance remains active; there is no pointer change to roll back |
| Regression is found after activation/acceptance | Preserve failed release; diagnose changed stage | §§12–13 rollback to retained acceptable release; build new candidate from the owning stage | Rollback uses retained inputs, binaries, views/modules and evidence; do not repair accepted bytes in place |
| Security/integrity/signing-key event | Security and release authority under the existing SOP | §12 hold/quarantine/withdrawal and recorded recovery decision | Ordinary operational retry is not authorization to use suspect inputs, keys or artifacts |

### Worked example: a version or variant in a partially built chain

Suppose a CCE payload and its NetCDF/HDF5 dependency chain are partly built,
and inspection shows a selected version or variant does not match the intended
package policy. This is the sequence, regardless of preparation path:

1. Save the manifests, effective configuration, locks, package listing and
   failed/incorrect result. Identify every environment and consumer using the
   changed node; mark completed environments as protected.
2. Decide whether the pinned recipe already supports the desired version or
   variant. If it does, change package intent. If its behavior is defective,
   use the overlay procedure. Do not add an overlay simply to select an
   already supported variant.
3. Change the owning authored input: hand-authored environment/policy for
   catalog consumers; roster/values/templates for the blueprint; stack/package
   set/defaults for full render. Reuse the same reviewed platform catalog/facts
   unless they are actually wrong. A package version correction does not by
   itself require rerunning Inspector or publishing a new catalog.
4. Prepare a separate affected candidate. Solve explicitly, compare the entire
   affected graph, and verify namespace, requested variants/versions, compiler,
   MPI and consumer hashes. A narrow root request does not guarantee a narrow
   solve. Stop on an unexplained change to the protected set.
5. Build only the candidate's required changed concrete packages/consumers;
   reuse compatible unchanged exact binaries. Existing old installs remain
   available. Resolve workspace shared-hash invariants before resuming the
   launcher; do not change protected locks merely to silence it.
6. Run the defect check and consumers under the intended compiler/lane. Compare
   protected manifests/locks/presentation with the baseline and retain results.
7. Return through review and the applicable publication/public-entry acceptance
   gates for that candidate. For CSE this includes signing and cache-only
   installation. A new lock or successful local retry does not itself approve
   the release.

## 4. A control refresh has its own impact boundary

The current [refresh helper](../../stack-content/pilots/cse-pilot/scripts/refresh-workspace-controls.py)
updates the blueprint's declared files/trees. Its
[`test_refreshes_declared_controls_and_preserves_build_inputs`](../../stack-content/pilots/cse-pilot/tests/test_refresh_workspace_controls.py)
proves preservation of fixture `spack.yaml`/`spack.lock` bytes, but deliberately
replaces modulefiles and presentation content, including removal of old files.
Thus “preserves locks” does not mean “cannot affect completed users.”

The updated helper stages the complete selection and retains old controls,
fingerprints and a transaction record. Ordinary replacement failure rolls back
the complete selected set; incomplete rollback blocks further ordinary updates.
Public tests inject later file/tree failures, damaged records and competing
updates. `--restore-from` undoes an applied refresh, while `--recover-from`
recovers unfinished state after its underlying fault is corrected. Both refuse
unrelated later edits and protected build-input paths. `--scope presentation`
selects only the two presentation trees; `--dry-run` makes no workspace changes.
Quiesce readers/builders: multi-file replacement is not a filesystem-wide atomic
switch or a portable power-loss guarantee. See the executable
[operator procedure](../../stack-content/pilots/cse-pilot/CONTROL-REFRESH.md).

Before a planned refresh, stage the exact proposed controls separately, review
the allowlisted diff and changed presentation/configuration, and test the
result against copied existing state. Retain recoverable old controls and
confirm the candidate matches the system/release. A package overlay remains
a separate reviewed file update; a control refresh is not a variant, recipe,
runtime-pin or dependency-graph migration command.

For the two unfinished CCE systems, do not refresh completed compiler entrances
or other systems just because newer controls exist. Bring forward only a
necessary tested correction. No live refresh is performed by this assessment.

## 5. What is tested, and what still needs a lifecycle test

The repositories contain real executable local tests, but many exercise only
one boundary with synthetic data or a fake Spack process. That is useful
regression coverage and must not be presented as a real build/recovery cycle.

| Coverage area | Existing evidence | Limit |
| --- | --- | --- |
| Static catalog output and invalid provider pairing | [Static catalog tests](../../stack-composer/tests/test_static_catalog.py) | Generated files and fixture facts; no physical compiler/MPI acceptance |
| Recoverable output replacement | [I/O regressions](../../stack-composer/tests/test_io_regressions.py): promotion/write failure and failed-rollback recovery tests | Temporary filesystem and injected failures; not preservation after a successful overwrite of active build state |
| Input provenance and malformed generated YAML | Same I/O suite: initialized-input fingerprints, repo digest changes, duplicate/empty YAML rejection | Initialization-time evidence, not later live-overlay drift detection |
| Existing locks and downstream stage failure | Same suite: `test_existing_lock_requires_explicit_reconcretization`, `test_failed_stage_prevents_downstream_execution`, failed inventory/push tests | Executes `spack-build` with a fake Spack command; proves driver decisions, not a real solver or package build |
| Known overlay files and patch shape | [Overlay tests](../../stack-content/pilots/cse-pilot/tests/test_package_repo_overlays.py) | Syntax/text and synthetic patch inputs; no general new-overlay lifecycle |
| Trial input/graph guard failures | [Toolchain template tests](../../stack-content/pilots/cse-pilot/tests/test_toolchain_templates.py): incomplete overlays, stale producer, wrong compiler hash | Rendered verifier/synthetic inputs plus selected assertions; not eight freshly solved real environments |
| Control refresh, restore and recovery | [Refresh tests](../../stack-content/pilots/cse-pilot/tests/test_refresh_workspace_controls.py): 24 cases covering scope, identity, whole-selection rollback, interrupted recovery, damaged records and concurrent updates | Temporary filesystem fault injection; real module behavior is a separate lab slice |
| Generic overlay admission and cache identity | [Inventory tests](../../stack-content/pilots/cse-pilot/tests/test_overlay_inventory.py) | Exact bytes, support inputs and shell cache selection; does not prove source compilation |
| Modules on already installed locks | [Module action tests](../../stack-content/pilots/cse-pilot/tests/test_module_refresh.py): named sets, selected surface, missing DB install and missing prefix | Generated launcher command boundary; actual Spack module sets tested separately in lab |
| Installed consumer behavior | [HPC validation coverage](../../hpc-validation/docs/coverage.md) | Tests existing installations; it intentionally never solves/builds/changes locks, so it cannot establish the recovery cycle itself |

### Failure-injection acceptance target

Run this only in disposable candidate workspaces, with dedicated stores/caches,
stages and module roots. Mount or checksum the retained baseline so attempted
changes to protected artifacts fail the test. Use the admitted pinned Spack
and local test sources. Exercise all three preparation paths into the same
downstream acceptance scenarios; do not require their directory trees or
manifest formats to be identical.

| Case | Deliberate failure/change | Required result |
| --- | --- | --- |
| R1 | Invalid input or failed output promotion in each generator | Prior output/evidence remains recoverable; no solve/install starts |
| R2 | New overlay absent from inventory, missing local patch, wrong repo order, or wrong selected class | Generic input gate rejects each case; expected complete candidate passes. A new package does not require new launcher branches |
| R3 | Unknown version, conflicting dependency constraint or unsupported variant | Solve fails; old lock and completed baseline remain; corrected authored input produces a reviewed candidate |
| R4 | Partially build a graph, then change one supported variant/version | New candidate shows intended graph delta; changed consumers rebuilt/tested; unchanged approved artifacts reused; protected environment bytes/entry points unchanged |
| R5 | Root recipe fix and separate transitive-dependency recipe fix | Correct recipe/patch selected and original failure passes; reuse never retains the defective node/ancestor; graph diff explains every change |
| R6 | Fetch interruption and missing offline resource/patch | Same-input retry resumes; missing inputs block; no unapproved network/source fallback |
| R7 | Controlled build failure/interruption after a dependency succeeds | Failed status/evidence retained; downstream acceptance/publication stops; targeted retry preserves completed prefix and locks |
| R8 | Correct install but intentionally failing consumer or wrong module entrance | Acceptance remains failed; no signing/promotion despite install success |
| R9 | Refresh wrong system/release, missing source file, or fail after one destination update | Reject identity errors before mutation; partial update is restored or clearly blocked with recoverable prior controls; locks and protected presentation remain unchanged |
| R10 | Missing/corrupt/wrong-hash binary in a cache-only publication | Installation stops; no source-build fallback or new solve; approved artifacts can be retried. Required for CSE and other policies selecting this publication mode |
| R11 | Destination entrance fails before activation; separately inject a later accepted-release regression | First case holds the candidate and leaves the prior default untouched; second exercises recorded rollback to the retained acceptable entrance; failed release stays separate |
| R12 | Reconstruct candidate from retained authored inputs and overlay record | Effective input/graph identity matches the accepted candidate; no hidden dependency on an edited source checkout, prior stage or LLM conversation |

For speed, use small fixture packages with intentional failures to establish
the generic cycle, then the actual failing CCE package and its consumers on
the remaining targets. A Linux fixture cannot establish CCE linker/Fortran
behavior. This matrix describes the complete target, not a claim that every
case has passed. The [implementation receipt](recovery_hardening_acceptance_2026_09_19.md)
maps the small local cases actually executed and the outstanding cases.

Keep implementation in its owning repository: generator transactions and
driver control flow in Composer; authored overlay/policy/refresh behavior in
Stack Content; cross-path Spack lifecycle in a maintained integration harness;
consumer/runtime acceptance in HPC Validation. The trial verifier's literal
eight-environment expectations should not become the universal test contract.

## 6. Initial assessment evidence, before implementation

The initial phase was a local code/document/test review. No live cluster workspace, installed prefix,
runtime pin, lockfile or module tree is changed. Focused execution results are
recorded below. Missing end-to-end evidence remains an acceptance gap, not a
reason to modify completed trials.

Executed during this assessment:

- **101 passed** in Composer: static catalog, initialization, full render,
  static publication, `spack-build`, I/O recovery, manifest publication and
  reference-fixture acceptance suites. Command from `stack-composer`:
  `env PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_static_catalog.py tests/test_workspace_init.py tests/test_render.py tests/test_publish_static.py tests/test_spack_build_script.py tests/test_io_regressions.py tests/test_publish_manifest.py tests/test_reference_fixture_acceptance.py`.
- **5 passed** in Composer using
  `env PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_validate_template_set.py`.
  One case explicitly confirms that `--concretize` is unimplemented, so this
  suite is not evidence of a real Spack solve.
- **7 passed** in selected Stack Content toolchain/launcher checks: incomplete
  overlays, stale GCC producer, duplicate downstream GCC constraint, preflight
  ordering, prepared-shell status, surface selection and rendered reuse policy.
  These are the corresponding `ToolchainTemplateTests.test_*` cases in the
  linked toolchain test file; their execution/fixture limitations are described
  above.
- **5 passed** using `python3 -m pytest -q pilots/cse-pilot/tests/test_refresh_workspace_controls.py`
  from Stack Content.
- **13 passed** using `python3 -m unittest pilots.cse-pilot.tests.test_package_repo_overlays`
  from Stack Content.

Those **131 baseline passing test cases** did not execute a real Spack
solve → partial install → changed variant/version/recipe → reviewed recovery
→ consumer test → cache-only publication cycle. They also do not establish
real CCE behavior. R2–R12 above identify the additional lifecycle evidence
needed beyond current unit/fixture coverage; R1 extends existing transaction
tests across each relevant preparation path. Subsequent implementation and
real local execution are recorded in the linked implementation receipt; use
that receipt for current results rather than this historical baseline count.
