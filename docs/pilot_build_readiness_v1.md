# Pilot build readiness (v1)

| Document control | |
|---|---|
| Date | 2026-07-18 |
| Status | Prep notes for the build-team discussion; the team hears all of this as proposals, not decisions |
| Rule | Only items that block the first install belong in "decide to start"; everything else trails the builds |

## Ready to propose

- **Pilot systems**: Blueback, Fran, Raider, Wheat. Fran is scheduled for
  Q3 FY26, so the working order is Blueback, Raider, Wheat, then Fran when
  it arrives.
- **Package set and versions**: the roster is selected, pinned against one
  package-recipe generation, at the newest supported release plus its
  immediate predecessor. Variants are recorded per package.
- **Baseline CPU target**: one portable target per system across every compiler
  surface and lane. Select the highest target common to the system's CPU-only
  build/runtime nodes, capped at `x86_64_v3`; fall back to `x86_64_v2` or
  `x86_64` only when the inspected system requires it. Per-lane tuning is a
  later rebuild, not part of these trials.
- **Acceptance criteria, in substance**: the five checks below already exist
  across the runbook gates and the SOP promotion gate. They need adoption as
  the named pilot gate, not invention.
  1. Packages build successfully.
  2. Representative C, C++, and Fortran applications compile and run.
  3. MPI packages run across multiple nodes.
  4. Installed software can be reproduced from the saved configuration.
  5. Pilot packages install and test cleanly from the build cache.

## Decide to start

1. **Which GCC on each system.** The platform's own GCC per system, or one
   pinned CSE GCC built everywhere. Everything hashes off this choice.
   Recommendation: platform GCC for the pilot, since it is proven on
   Blueback and costs nothing; run the pinned CSE GCC as the side
   experiment from the consistency note rather than putting a compiler
   build on the pilot's critical path.
2. **MPI pairing on Raider and Wheat.** cray-mpich on the Crays is settled.
   Raider and Wheat need their fact sheets to confirm which site MPI pairs
   with which GCC, and at which version. The external-versus-build fork
   only opens if a fact sheet comes back without a usable pairing. Launch
   validation, single and multi node, belongs to acceptance, not here.
3. **Fact sheet and deployment overlay per system.** Nothing builds until a
   system has a reviewed fact sheet and an installer-chosen overlay
   (install tree, caches, module and view roots). Blueback has both from
   run #1. Raider, Wheat, and Fran need owners and dates.
4. **Adopt the acceptance checks.** Sign off the five as the pilot gate so
   that "done" is defined before the first build starts.

## Can wait, on purpose

Module packaging and exposure polish (the design is settled; the details
tune as builds land), vendor math libraries beside OpenBLAS, the Serial-lane
question, performance targeting, and everything else on the open-questions
slide. None of it blocks an install.
