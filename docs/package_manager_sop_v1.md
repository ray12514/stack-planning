# CSE Stack — Package Manager SOP (v1 draft)

Status: draft for management review, 2026-07-09. This is the operator-facing
procedure. It describes the **outcomes** of the CSE tooling and the manual
flows a site package manager follows; it deliberately does not explain tool
internals (those live in the design docs listed at the end).

## 1. Purpose and audience

Audience: a site package manager who maintains HPC software for users. No
knowledge of our tooling is required or expected — this procedure is written
in terms of the **artifacts**, all of which are plain, readable, versioned
files. (The tools that generate each artifact are listed in the appendix;
every artifact can also be produced or corrected by hand.)

What you operate:

1. The **site catalog repo** — the static repo of record. It holds, per
   system: the **system fact sheet** (`profile.yaml` — compilers, MPIs, GPU
   toolkits, fabric, filesystems, as observed on the machine), the
   installer-chosen `deployment.yaml`, the **platform configuration
   catalog** (below), and runbook notes; plus the shared stacks, package
   sets, and templates.
2. A **curated stack workspace** per stack — the generated build
   configuration for the CSE lanes. Everything you build from is a readable
   file you can inspect.
3. The **platform configuration catalog** per system and release —
   include-ready Spack configuration derived from the fact sheet alone: the
   system's compilers, MPIs, and GPU toolkits as pinned externals, a
   `manifest.yaml` naming the recommended compiler/MPI/GPU picks, and a
   README with a copy-paste include block. This is what **any** package
   manager — CSE or not — pulls to build correctly on the machine.
4. The **published surface** users see: `CSE/<Compiler>/<Lane>` modules and
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

1. Gather the system facts. The supported way is the **system probe** — a
   single static binary we provide (no installs, no network, no Spack
   required); the fact sheet is plain YAML, so it can equally be authored or
   corrected by hand and checked with the same verify step.
2. Probe and merge (non-login shells; the probe handles module hygiene):

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
6. Generate the system's static platform catalog and commit it alongside
   (the standing drill for every machine: probe, then render, then
   render-static):

   ```bash
   stack-composer render-static --profile systems/<name>/profile.yaml \
       --templates templates --output-root systems --release 2026.07 \
       --rendered-at <utc-timestamp> --source-repo <catalog-url> \
       --source-commit <sha>
   # writes systems/<name>/static/2026.07/{scopes/,manifest.yaml,README.md,reports/}
   ```

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

## 5. Flow C — manual builds from the static catalog (no lanes)

This is the expected day-to-day flow for a package manager building
something outside the curated stacks. Pull the catalog repo; everything you
need is under `systems/<name>/static/<release>/`:

1. Read `README.md` — it contains the recommended include block verbatim.
   `manifest.yaml` lists every available scope (each compiler at each
   version, each MPI per compiler flavor, each GPU toolkit generation) and
   the **recommendations**: which compiler, MPI, and GPU scope the site
   policy picks for this system. `reports/static-plan.yaml` records what was
   rendered and what was deliberately not, so nothing is a mystery.
2. Author a minimal environment from the recommendation:

   ```yaml
   spack:
     include:
       - <catalog>/scopes/common
       - <catalog>/scopes/compilers/gcc/14.3.0
       - <catalog>/scopes/mpi/cray-mpich/9.1.0/gcc-14.3.0
     specs:
       - hdf5 +mpi %gcc-14.3.0_craympich-9.1.0
   ```

   Every scope carries `buildable: false` pinned externals and the matching
   toolchain definitions, so a manual build gets the same compiler/MPI
   pairing discipline as the curated lanes — with none of the machinery.
3. Concretize and install as usual. Same tripwire as Flow B: externals must
   be **used**, never fetched.

### 5a. One-off packages by non-CSE package managers

The most common case: a package manager who is **not part of CSE** needs to
provide one package (often at several versions) to their users. They have
their own environments and their own module conventions — CSE's lanes and
module tree are ours, not theirs. The catalog is still their friend:

1. Build the package in their own environment, including the catalog scopes
   (step 2 above) so it links the system's blessed compilers, MPI, and
   externals instead of guessing at prefixes.
2. Generate its modulefile(s) — one per version if several — and place them
   in **their own shared directory that is already on the system's
   `MODULEPATH`**. This is entirely outside the CSE tree; users see the new
   package on the next `module avail` through the path they already had.
3. Nothing about CSE changes and nothing needs coordination with us — the
   catalog exists precisely so builds outside CSE still match the machine.

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

From the user's perspective the entire procedure is three commands:
`module load CSE/<Compiler>`, then exactly one lane
(`Serial · MPI · GPU`), then the package they want
(`module load hdf5/1.14.6`). Core tools appear with the surface;
foundation libraries are simply there when they link. That simplicity is
the product — every flow above exists to keep those three commands honest.

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

## 9. Appendix — which tool produces which artifact

Operators work with artifacts; these names only matter when something needs
fixing at the source:

| Artifact | Produced by |
|---|---|
| System fact sheet (`profile.yaml`) | the system probe (`cluster-inspector`) — or by hand |
| Curated stack workspace | the renderer (`stack-composer render`) |
| Platform configuration catalog | the renderer (`stack-composer render-static`) |
| Built packages, lockfiles | Spack, driven by the rendered files |
| Modules and views | generated with the workspace; published at release |

## 10. Pointers (the detail behind each step)

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
