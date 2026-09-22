# Isolated recovery hardening implementation

Status: implementation branch, 2026-09-19. Production selection remains open.

The `codex/recovery-hardening` worktrees under `Development/stack-recovery`
snapshot the current working sources for isolated implementation. Verified
changes are also copied back to the existing `codex/simplified-render-plan`
working branches so ongoing trial maintenance can use them. Pre-existing work
on those branches is preserved. Updating source does not deploy a generated
workspace change.
No new control, recipe, pin or lock is deployed to an existing trial by this
work. The two remaining CCE trials may receive individually qualified fixes
later; completed package stores and lock sets remain retained evidence.
The preservation boundary is the actual cluster environments. The local HPC
lab is disposable and should use small, bounded fixtures rather than rebuild
the complete CSE roster to test a workflow.

## Accepted implementation boundaries

1. The control-refresh command gains explicit `presentation`, `controls` and
   `all` scopes and a dry-run. Presentation scope updates only declared module
   entrance/presentation trees. It must not rewrite environment manifests,
   locks, recipes, catalog, source caches, views or installed prefixes.
2. Refresh stages the complete selected payload before mutation, retains all
   previous controls and their identities, and rolls the whole selected set
   back if any commit fails. Failed rollback retains a named recovery record
   and blocks unnoticed continuation. Successful refresh also retains a
   record permitting explicit restoration. This is recoverable multi-file
   replacement with quiesced readers, not a filesystem-wide atomic switch or
   a portable power-loss guarantee. Concurrent refreshes are rejected.
3. The CSE overlay verifier consumes a reviewed source-controlled JSON inventory
   beside the package repositories. It records repository namespace/API,
   package/support-file paths and SHA-256 identities. Missing, unrecorded,
   changed or escaping/symlinked inputs fail before candidate build actions.
   An explicit candidate-inventory command writes a separate review artifact;
   normal checks never accept current mutable bytes as their own baseline.
   This replaces Dakota/HDF5-specific text checks, not the CSE graph policy.
4. The builtin package repository uses an exact full commit as its executable
   pin; the tag remains explanatory admission evidence. The new inputs apply
   to newly generated candidates. They do not advance an existing trial's
   runtime/repository or silently regenerate its locks.
5. Generic full render honors each local repository's declared before/after
   builtin priority, preserving authored order within each group, and emits
   API-v2 repositories beneath the required `spack_repo/<namespace>` path.
   Static catalogs emit an empty common scope when needed so recommended
   includes exist. Spack selection is exercised separately in real-Spack lab
   tests.
6. The integration harness uses separate workspaces, stores, stages, cache,
   module roots and test signing keys inside the development HPC lab. It tests
   actual Spack solving/building/reuse and induced failures. No fake Spack is
   used to claim lifecycle acceptance. Small fixture packages establish the
   generic cycle; CCE/Fortran, physical fabric and site module qualification
   still require the actual target systems.
7. The `modules` builder action regenerates views and all applicable named
   package-module sets from existing locked installs, without fetching,
   installing or concretizing. Module sets sharing a tree must not erase one
   another. Presentation publication remains a separate action.
8. New candidates scope mutable recipe/patch indices to their resolved overlay
   paths and reviewed inventory identity. Reusing a package store is independent
   of sharing mutable recipe caches. Candidate overlay changes must not inherit
   a stale namespace patch index from an earlier candidate.

The agreed public test seams are generated workspace output, the overlay
verification/candidate CLI, control-refresh/restore, and downstream real
Spack operation through the lab harness. Each defect is captured by a failing
case before its implementation. Broader full-render Spack 1.2 work is assessed
through the harness; a passing minimal fixture is not a claim that every
producer/MPI/GPU contract is complete.

## Package reuse and module updates

Keeping locks preserves requested concrete identities. Reuse additionally
requires the referenced prefixes and Spack database to remain available and
valid, with their external/compiler runtime assumptions still satisfied.
Updating source code or module presentation need not change those identities.
Changing package intent/recipes/providers requires the explicit candidate
solve and affected-consumer review from the SOP. Never delete old locks or
prefixes to make a test pass.

Built packages may be exported to a private candidate build cache while module
and runtime validation continue. Cache presence is not release approval.
Sign/publish the accepted exact set under the CSE SOP only after its required
package, consumer, module and destination checks pass.

## Accepted follow-through: existing workspace upgrade and delivery

The next accepted rehearsal starts with a small installed, locked workspace.
Missing view/module files are an injected failure fixture: the retained older
trial workspace already contains named views and some module configuration.
Its actual gaps include older module policy, missing overlay inventory/helper,
and tag-only repository configuration. Replacing its environment YAML with a
new render would also change package specifications and is not an upgrade path.

The explicit `module-policy` refresh accepts a reviewed candidate tree with the
same workspace identity. It may change only named `spack.view` entries and the
paired environment `modules.yaml`. It preserves all non-view environment
semantics, old include order, lock bytes, shared configuration and recipes.
The module scope must already be included. Missing groups or named-view
references fail instead of guessing package intent. Every selected environment
must already have its lock; incomplete environments remain outside this action.
Apply and retained restore use the same protected-input guards and transaction
journal as control refresh. Regeneration and module/consumer qualification are
separate real-Spack actions against those installed identities.

Overlay inventory admission accepts an explicitly reviewed inventory and
trusted verifier against the recipes already frozen in the workspace. It may
add only the inventory and helper; it must not copy new recipes or rewrite
repository configuration. In particular, recording an old tag-only workspace
does not establish which commit that tag resolved to on a target machine.

A reusable acceptance-and-buildcache command executes an explicit argv against
a locked environment, retains output and YAML/lock hashes, and refuses signed
publication on consumer failure, timeout or input drift. Successful publication
selects exact locked roots and their dependencies. OCI destinations are refused
because the pinned Spack implementation disables signing for OCI. This gate
does not activate modules or advance any public pointer.

The local acceptance adds a dependency-only overlay, a resulting consumer DAG
change and runtime failure, both failing and succeeding publication gates, an
untrusted signing keyring, and corrupted cache content. After fixing findings,
one new uninterrupted run must pass the complete small-fixture lifecycle under
the 1,800-second outer timeout. A resumed troubleshooting run is not that proof.

Delivery uses the existing offline builder and exact committed Composer,
Content and Planning exports. A versioned archive includes matching tools,
offline helper dependencies, source revisions, checksums, verification and
explicit receiving commands. Source installation is separate from workspace
refresh; no existing trial deployment is performed by bundle creation.

## Operator workflow follow-through

The source now adds two downstream interfaces shipped with workspace controls:

- `workspace-overlay.py` applies or edits a complete recipe in the existing
  unfinished workspace, validates its inventory, records all-lock impact, and
  retains the previous files for recovery. `workspace-build.py` reconcretizes
  one explicitly selected environment with a saved lock and resumes that
  environment from its current lock. Other locks and installed prefixes are
  preserved; matching installed hashes are reused. Pending affected locks block
  later build actions until deliberately reconcretized. One shared maintenance
  lock serializes these operations and finite new-launcher actions. There is no
  additional operator workspace or mandatory approval-digest sequence.
  The isolated `overlay-recovery.py` path remains available for experiments and
  supplies shared runtime primitives; its earlier acceptance is labeled separately.
- `module-preview.py` inspects installed prefixes, named views and module policy,
  then generates an isolated preview. Policy/projection iterations reuse the same
  concrete package hashes. Missing lane prerequisites are reported for scoped
  control/policy maintenance; Composer/Spack upgrades are not a prerequisite to
  regenerate an already valid module policy.

Older generated launchers can use the standalone helpers from their prepared
shell. New controls delegate `overlay`, selected `concretize`/`resume`, and
`module-preview` actions to these same implementations. The previously sealed `recovery.2` delivery is unchanged and
predates these helpers; current source or a subsequent delivery is required.
Actual results and limitations are recorded in
[operator acceptance](recovery_operator_acceptance_2026_09_22.md).
