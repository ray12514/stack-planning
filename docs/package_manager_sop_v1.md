# CSE Stack — Package Manager SOP (v1 draft)

Status: draft for management review, 2026-07-09. This is the operator-facing
procedure. It describes the **outcomes** of the CSE tooling and the manual
flows a site package manager follows; it deliberately does not explain tool
internals (those live in the design docs listed at the end).

## 1. Purpose and audience

Audience: a site package manager who maintains HPC software for users and is
**not** expected to know Spack internals, stack-composer, or cluster-inspector.

What you operate:

1. A **site catalog repo** (`stack-content`) — the static repo of record.
   It holds, per system: the probed `profile.yaml`, the installer-chosen
   `deployment.yaml`, and runbook notes; plus the shared stacks, package
   sets, and templates every site uses.
2. A **rendered workspace** per stack — plain YAML the tools generate.
   Everything you build from is a readable file you can inspect.
3. The **published surface** users see: `CSE/<Compiler>/<Lane>` modules and
   views. Users never run a spack command.

## 2. Roles

| Who | Owns |
|---|---|
| Central stack team | Tools, templates, package sets, stack definitions, this SOP |
| Site package manager (you) | The system's profile + deployment entries in the catalog, running renders/builds on the system, publishing modules/views, smoke verification |
| Site users | `module load CSE/<Compiler>`, then one lane; nothing else |

Ownership rule that never bends: **install trees, cache paths, view/module
roots are chosen by the installer and recorded in `deployment.yaml` — no tool
ever derives them** (see deployment_inputs_and_ownership_v1.md).

## 3. Flow A — onboard a new system (once per system)

1. Copy the `cluster-inspector` binary to a login node (single static
   binary; no installs, no network, no Spack required).
2. Probe and merge (non-login shells; the tool handles module hygiene):

   ```bash
   ./cluster-inspector probe-system --system "$NAME" --output system.frag.yaml
   ./cluster-inspector probe-node   --output login.frag.yaml
   ./cluster-inspector merge --system-fragment system.frag.yaml \
       --node login.frag.yaml --output profile.yaml
   ./cluster-inspector verify profile.yaml     # expect: PASS schema, PASS semantic
   ```

3. Read the profile. It is the system's fact sheet: compilers, MPIs (with
   per-compiler flavors), GPU toolkits, fabric, filesystems. If a fact is
   wrong or missing, do not hand-edit the outputs downstream — fix it at the
   source with an `inspector-hints.yaml` entry and re-probe.
4. Write `deployment.yaml` from the site's choices (install tree, module
   root, view root, caches). The profile's `filesystem` section lists
   candidates; you choose.
5. Commit both under `systems/<name>/` in the catalog repo and open a PR.
   The system now exists for every flow below, and for every other operator.

## 4. Flow B — render, inspect, build (the routine)

1. On the system, pull the catalog repo. Validate before rendering:

   ```bash
   stack-composer validate --profile systems/<name>/profile.yaml \
       --deployment systems/<name>/deployment.yaml \
       --stack stacks/<stack>/stack.yaml \
       --templates templates --package-sets package-sets \
       --package-repos package-repos --report validate-report.yaml
   ```

   The report names every lane that will render and, for anything skipped,
   the exact reason per build. **Do not proceed past a failing validate.**
2. Render. The output is a self-contained workspace tree:
   `environments/<compiler>/<lane>/spack.yaml` per lane, `configs/` scopes,
   and `reports/render-plan.yaml` — the render's own record of every
   selection it made (which MPI version, which GPU toolkit, which
   toolchain). Read the plan before building; it answers "why did it pick
   that" without any tool knowledge.
3. Inspect against the system (the oracle step): the lane `packages.yaml`
   files must reference real prefixes (`/opt/cray/pe/...`, `/opt/rocm-...`).
   Runbook checklists live at `systems/<name>/runbook-notes.md`.
4. Build, one lane at a time, in any order (lanes are independent):

   ```bash
   spack -e environments/gcc/mpi-craympich concretize
   spack -e environments/gcc/mpi-craympich install
   ```

   Concretization must **use** the system externals (cuda/rocm/cray-mpich
   show as externals, not fetched source). Spack downloading a toolkit the
   system already has means the render was wrong — stop and report it;
   never patch the rendered files by hand.

## 5. Flow C — manual builds (Tier 0: no lanes, just the configs)

The rendered `configs/` scopes are standalone. A package manager (or power
user) can hand-author a minimal environment that reuses them:

```yaml
spack:
  include::
    - /path/to/workspace/configs/common
    - /path/to/workspace/configs/mpi/cray-mpich
  specs:
    - hdf5+mpi %gcc1430_craympich910
```

The toolchain names (`%gcc1430_craympich910`) are listed by
`stack-composer show` and defined in the included scope's
`toolchains.yaml`. This is the supported escape hatch for one-off builds:
same pinned externals, same compiler/MPI pairing, no lane machinery.

## 6. Flow D — publish and release

1. Regenerate views, refresh modules (rendered modulefiles: the
   `CSE/<Compiler>` surface loads Core automatically; foundation libraries
   are ambient in the view; users then choose exactly one of
   `Serial · MPI · GPU`, qualified only when the system has more than one
   MPI or GPU architecture).
2. Push build caches (foundation and payload lanes cache separately).
3. Record lockfiles and the release manifest; promote the release tag.
4. Smoke-verify as a user would: `module load CSE/GCC`, load one lane,
   compile a hello-world against HDF5, `srun`/`mpirun` a ring test.

## 7. Flow E — when things change

| Change | What you do |
|---|---|
| System upgrade (new CPE, new drivers) | Re-probe (Flow A steps 1–3), commit the new profile, re-render, rebuild affected lanes |
| New/changed stack or package set | Pull catalog, re-render, rebuild — profiles and deployment untouched |
| New site paths | Edit `deployment.yaml`, re-render |
| A fact the probe missed | `inspector-hints.yaml`, re-probe — never hand-edit profiles or rendered files |

## 8. Verification checkpoints (what "good" looks like)

- `cluster-inspector verify` → PASS schema + PASS semantic.
- `stack-composer validate` → `valid: true`; any skipped build has a reason
  you agree with; GPU lanes warn if the toolkit externals are missing.
- Rendered `packages.yaml` externals point at real system prefixes,
  `buildable: false` for platform toolkits.
- Concretize shows externals reused, not fetched.
- Post-publish: a fresh shell can `module load CSE/<Compiler>`, see exactly
  one lane's packages after loading it, and link zlib without choosing it.

## 9. Pointers (the detail behind each step)

- End-to-end map and stage-by-stage commands: `end_to_end_map_v1.md`
- Who owns which input: `deployment_inputs_and_ownership_v1.md`
- Render/build seam and workspace handoff: `stack_build_handoff_note_v1.md`
- Lanes, module naming, exposure: `lane_and_module_model_v1.md`,
  `foundation_core_view_semantics_note_v1.md`
- Per-system runbooks: `stack-content/systems/<name>/runbook-notes.md`

Open items for review: hosting/location of the catalog repo for sites
without GitHub access (see pre_v1_hosting_and_external_inventory_note_v1.md);
release cadence and who signs off a promotion; whether Flow C examples ship
in the catalog as ready-made snippets.
