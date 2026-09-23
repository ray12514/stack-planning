# Same-workspace recovery and module iteration acceptance — 2026-09-22

The normal unfinished-trial correction loop is now implemented in Stack Content:
apply/edit the complete package directory in the existing workspace, explicitly
reconcretize one environment, and resume that environment. Retained installed
hashes are reused. An affected unselected lock remains unchanged and blocks a
later participating build until explicitly reconcretized. The helpers retain
before/after inputs and do not create a replacement operator workspace.

The [operator guide](../../stack-content/pilots/cse-pilot/OVERLAY-RECOVERY.md)
provides the current-launcher and older-launcher commands. The
[module presentation guide](../../stack-content/pilots/cse-pilot/MODULE-PRESENTATION.md)
checks existing controls and generates private lane/naming previews from current
installed locks. A valid existing module policy does not require a Composer or
Spack upgrade. Accepted/published release inputs remain immutable.

## Local source regressions

- Composer's required `scripts/check.sh`: **280 tests passed**, plus manifest,
  typing, Ruff, shell and whitespace checks.
- Content's complete pilot run: **263 cases executed; 260 initially passed**.
  Two launcher failures identified a configuration-reading check invoked through
  plain Python instead of the activated Spack Python. The launcher now uses
  `spack python`. The third failure was a macOS test assumption that setgid would
  always be cleared; the check now accepts either macOS behavior while requiring
  identical owner/group access, and still requires setgid on Linux.
- Final launcher/toolchain rerun: **52 passed**, including all three failures.
- Final selected-workspace helper run: **13 passed**, including four additional
  interruption cases that preserve later manual variant edits.
- Together these cover **267 distinct Content regression cases**. This is a
  complete run plus focused final reruns, not a claimed single uninterrupted
  267-case run.
- New helper Python 3.6 syntax, Ruff, documentation Bash syntax and whitespace
  checks passed. Common process-session cleanup also passed the local SIGTERM
  regression with a worker in a separate process group.

## Real Spack checks

The tiny GCC fixture uses Spack 1.2.2 at
`3e19345b6e12f5ff1b874f4059622fc6a1fd804a` and builtin packages at
`d4f7c711a6a42f1c4d551c8fd10fce9a11340a81`. No real CSE cluster was changed and no
full trial stack was rebuilt.

**Five same-workspace checks passed in four bounded phases:**

| Check | Result |
| --- | --- |
| Root recipe correction | Apply preserved locks; explicit selected solve changed one hash and retained five; resume succeeded; affected held environment refused a stale-lock build |
| Failed selected solve | A deliberate recipe conflict failed solving and restored the exact prior selected lock and manifest |
| Dependency correction | Consumer recipe stayed unchanged; dependency and consumer hashes changed; four hashes were retained; resume succeeded |
| Variant correction | Resume rejected stale intent; explicit selected solve and resume produced the requested feature |
| Final helper and legacy workspace | Final helper reused the installed prefix; first-use legacy root mismatch was rejected before install |

Protected unselected locks, configuration, installed prefix bytes/mtimes, existing
modules/views and the test public pointer remained unchanged. The receipt retains
**98 input files**, exact helper/harness digests and per-phase results:

`hpc-lab/results/stack-recovery/20260919T233912Z-16940/operator-cli/workspace-acceptance-summary.json`

Receipt SHA-256:
`5bcd73247e37904c5f344abf03ee46c050c84682d12a10ac60d012ae0beeec41`.
The final tested `workspace-build.py` SHA-256 is
`a4d7dfbe0bb0115490c496ac36a6f4f2e25b56674432b16d499cfcd449847bcd`.
Earlier phases retain their own source snapshots; the final variant/preflight
phases exercise this final helper without repeating earlier source builds.

A separate optional-candidate/module-preview receipt records five checks,
including two module naming iterations loaded through Lmod and process-session
termination/retry. That real SIGTERM test covers the shared runtime through the
optional candidate helper; this note does not claim a separate real
`workspace-build` interruption run. The generated launcher is covered by source
regressions; the real-Spack phases invoke its underlying public helpers directly.

The original 24-check historical receipt remains unchanged at SHA-256
`309f30d6b9dd245b679cc280c0969492e79a91c494a25c97af4f963ba919c309`.
See the [lab acceptance procedure](../../hpc-lab/docs/stack-recovery-acceptance.md)
for reproduction and the retained evidence layout.

## Module entrance correction — 2026-09-23

The original preview guide incorrectly added a second lane `module use`, and
its combined preview module root exposed backing compiler/package names during
Lmod's recursive discovery. This was reproduced independently of package builds.
The corrected preview has a separate `entrances/cse/` root. Loading an entrance
automatically exposes individual Core/Common package modules and Serial/MPI
selectors; loading a lane exposes its packages. Core/Common are package groups,
not selectors users load. The guide and control-refresh procedure now test that
exact sequence.

Future `publish-modules` operations use `<recorded-module-root>/entrances/cse/`
for compiler entrances, keeping lane/package paths unchanged. The executable
publisher regression confirms that existing legacy entrance and package files
retain their bytes and timestamps. Existing generated launchers and site login
registrations require deliberate updates; no real cluster workspace or module
tree was changed by this correction.

The focused real-Lmod regression passed seven checks: compiler-only initial
discovery, GCC and platform CCE entrance routing, automatic Serial/MPI exposure,
selected package loading, sibling lane conflict, unload cleanup, and preserved
workspace input hashes. It uses actual entrance/lane templates and preview
routing with stub compiler/MPI/package modules, with **zero builds or solves**.
It does not qualify CCE execution. See the
[bounded reproduction procedure](../../hpc-lab/docs/stack-recovery-acceptance.md#compiler-entrance-and-lane-discovery).

The final focused Content run passed **71 tests and 14 subtests** across module
preview, toolchain/publisher templates, and Composer launcher tests. Ruff,
shell-script syntax, 29 operator-document Bash blocks, and whitespace checks
also passed.

The separate receipt is
`hpc-lab/results/module-preview-entrance/20260923-final/acceptance.json`, SHA-256
`9a2ca3c5cb606425c47ae796815125b3bed3a1956e353f8051d4bbd0024a36f2`.
Earlier historical receipts remain unchanged. The older lab harness entry paths
were updated for future runs; this correction does not claim a rerun of the
complete earlier lifecycle suite.

The same-day TModules follow-up ran the same Tcl entrance/lane templates under
**Tcl Environment Modules 5.3.0**, then repeated the strengthened check under
**Lmod 8.6.19**. Both passed eight assertion groups, explicitly including
individual Core/Common package availability and loading with no Core/Common
selectors. TModules is the primary target; Lmod is a secondary compatibility
check. The new receipts are
`hpc-lab/results/module-preview-entrance/20260923-tmodules-verified/acceptance.json`
and `20260923-lmod-verified/acceptance.json` under the same parent. The TModules
run used an already available offline image. Both used stub package/compiler/MPI
modules, performed zero builds/solves, and preserved workspace input hashes.
The earlier Lmod-only receipt remains unchanged.

## Remaining target-system work

Run the actual failing build with CCE on each remaining system. A corrected
configure/compile/link stage passing with the same compiler is the recovery
check; the tiny GCC fixture does not establish CCE success. Complete the existing
module/MPI/runtime and publication acceptance where applicable.

Root/version/variant drift is checked against the selected lock. New solve
receipts also fingerprint selected manifest intent while excluding modules,
views and operational settings. Included package/provider/concretizer policy
files still require explicit reconcretization after edits; historical locks do
not retain their former contents. Older/manual commands do not automatically
participate in the new maintenance lock or stale-lock gates.

The previously sealed `recovery.2` delivery is unchanged and predates these
helpers. Use reviewed current source or a later delivery. Updating source does
not update an existing generated workspace automatically. Production preparation
remains undecided; these CSE controls do not select full render as that path.
