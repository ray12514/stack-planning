# Cluster Inspector reliability and module hierarchy

Status: implemented with regression and lab acceptance, September 2026.
Release qualification and target-system acceptance remain separate gates.

This note refines the existing Inspector design. It does not change
`profile-v1.json`, Stack Composer's render contract, or the active CSE trial
workspace layout.

## Accepted artifacts and failed observations

`profile`, `merge`, and `verify` use the same profile schema and semantic
acceptance rules. A complete profile includes build and runtime node coverage.
Incomplete fragments remain available through the lower-level probe commands;
they are not silently promoted into an accepted profile.

Each YAML input contains exactly one document. Trailing documents, including
trailing empty documents, are errors rather than ignored input. Shape validation
must examine the same document that the command subsequently consumes.
Unknown typed-fragment fields are rejected before model conversion can discard
them. Existing profiles that meet both schema and semantic requirements remain
accepted. Stricter validation may reject incomplete or malformed inputs that
earlier commands accepted; this does not require regenerating existing reviewed
profiles or workspaces.

An inventory whose clean baseline failed cannot supply an XALT reverse map.
The diagnostic inventory may still be saved, but export returns an error and
does not open or replace an existing map. An inventory with no verified modules
also cannot be promoted. Failed individual modules remain visible diagnostics;
the command reports when a map covers only verified entries.

## Hierarchical module discovery

Module discovery must distinguish a module name from its activation context.
A compiler gateway can expose an MPI root, and an MPI gateway can expose an
application root. A module visible only in a child root is discovered with the
ordered prerequisite chain that exposed it.

Use module-tool observations to establish these relationships. Tool metadata
may supply candidates and prerequisite chains, but does not by itself verify a
provider. Verification still uses the controlled non-login shell, loads the
recorded chain, and verifies the resulting commands and prefixes.

Traversal and verification remain bounded and deterministic. Cycles, repeated
roots, failed gateways, and traversal limits must have explicit diagnostics.
The same leaf name in different compiler/MPI contexts must not silently merge
two distinct installations.

The profile uses its existing provider `modules` fields for activation chains.
The separate diagnostic module inventory may carry an optional `load_modules`
list. Flat inventories retain their current shape. XALT retains its existing
reverse-map format; contextual ambiguity must be reported rather than hidden.
Attribute a module's paths relative to its prerequisite context so that loading
HDF5 does not make HDF5 the owner of its compiler or MPI paths.

The current implementation carries hierarchy chains through generic and Cray
compiler/MPI verification and through the full inventory. GPU toolkit profile
records retain their existing single-module field; extending that contract
requires separate design and consumer acceptance. Do not equate inventory
coverage with GPU-lane readiness.

## Execution and release checks

Optional worker, deadline, and progress controls configure observation work,
not stack policy. Progress goes to stderr and cannot corrupt YAML or JSON
artifacts. Cancellation must reach local probes and requested scheduler steps;
a deadline must not promote partial observations into accepted output.

The deadline reaches the local launcher process group and is forwarded to the
remote node probe. Scheduler-owned remote cleanup must still be qualified on
each target. Inspector does not cancel the operator's enclosing allocation or
claim to interrupt kernel-blocked filesystem reads.

Maintained tests cover flat and hierarchical Lmod/Tcl inventories, negative CLI
cases, scheduler transport, and unchanged-profile Composer compatibility.
Private lab state and real-system recordings are not published as fixtures.
Only reviewed, sanitized inputs belong in the maintained corpus.

Executable packaging follows the portable-tools transition plan. Preparing
offline build checks and release artifacts does not authorize publishing a
release, choosing a final GitLab namespace, or creating signing credentials.

## Existing workspaces

An Inspector update does not regenerate or migrate a Composer workspace.
Existing reviewed profiles, rendered YAML, lockfiles, install trees, and caches
remain untouched. A new inspection writes to a separate candidate path; the
operator reviews any added or changed facts before adopting them.

Compatibility acceptance uses temporary renders from the same accepted inputs
and compares the resulting bytes. It must not reconcretize or refresh a live
trial workspace merely to test an Inspector change.
