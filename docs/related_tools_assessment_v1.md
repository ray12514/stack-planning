# Related Tools Assessment v1 — Stackinator, spack-stack

Recorded 2026-07-02. Question assessed: should this project scrap its own
stack-generation direction and adopt one of these, adopt pieces, or neither?
Facts gathered from repos/docs 2026-07-02; assessment against our target
(curated package lanes for users to build against, on heterogeneous systems:
Cray EX and generic Linux, multi-CPE as a committed v1 goal, probe-driven
profiles from cluster-inspector).

## Verdict

**Keep our direction. Adopt two specific pieces; scrap nothing.** Neither tool
occupies our niche, and each independently validates parts of our design.

## Stackinator (CSCS/ETH, BSD-3-Clause)

Builds squashfs "uenv" images for HPE Cray EX from a recipe
(compilers/environments/config YAML); users mount at `/user-environment` and
consume views/modules, or point their own Spack at a shipped config scope via
`SPACK_SYSTEM_CONFIG_PATH`.

**Not a replacement because:** Cray-EX-only framing; one compiler version per
recipe and no multi-CPE mechanism (our v1 commitment); squashfs + bubblewrap +
mount-point-rpath'd images require site infrastructure (uenv CLI/Slurm plugin)
we cannot assume across target systems; no `toolchains.yaml` — older
packages.yaml/externals binding; single-site center of gravity (Alps).

**Adopt (high value): the CSCS `alps-cluster-config` Cray runtime packages.**
Their site Spack repo models `cray-mpich`, `cray-gtl`, `cray-pals`, `cray-pmi`
as ordinary buildable Spack packages. GTL is baked in via
`patchelf --add-needed libmpi_gtl_{hsa,cuda}.so` post-install plus wrapper
rewriting (`@@GTL_LIBRARY@@` → `-L... -Wl,-rpath,... -lmpi_gtl_*`) — explicitly
**no LD_PRELOAD**. This is separable ordinary `package.py` code, independent of
Stackinator core, and is the reference implementation for our
`cray_runtime_package_repo_note_v1.md` direction (that note already cites their
Balfrin packages.yaml). Also patches HIP soname for ROCm major bumps — directly
relevant to the CPE 26.03/ROCm 7 transition
(`cpe_rocm_compatibility_note_v1.md`).

**Validates (nothing to import):** their cluster-config/recipe split mirrors
our profile+deployment vs stack split; their shipped user-facing config scope
is prior art for our manual config catalog mode
(`manual_config_catalog_note_v1.md`).

## spack-stack (JCSDA/NOAA, CC0-1.0)

Unified Spack environments for a specific NWP package set (UFS/JEDI/GEOS),
consumed via hierarchical Lmod/Tcl modules; 21 hand-maintained tier-1 site
config directories plus a community tier-2.

**Not a replacement because:** it is a *content* project around a package set
we don't want, and its system abstraction is hand-curated per-site config
directories — the exact model our probe-driven `cluster-inspector` profile
replaces. No GTL handling at all; cray-mpich is a bare external; no
`toolchains.yaml`; multi-version = one environment per compiler version.

**Adopt (when module work resumes): the hierarchical module family pattern.**
Compiler modules at the root, MPI modules (`family("MetaMPI")`) nested under
compiler, packages under compiler+MPI — a battle-tested realization of our
compiler-init → lane → package chain (`lane_and_module_model_v1.md`).
Also note native Spack `upstreams:` chaining for reusing an installed
foundation across environments — relevant to per-compiler Core reuse.

## Positioning (why our niche is real)

Neither tool has: probe-generated system profiles; deterministic multi-lane
render (compiler × MPI × GPU) with Spack-native versioned toolchains;
multi-CPE coexistence as a goal; portability across Cray and generic Linux in
one model. Both still bind compiler/MPI with pre-toolchains mechanisms; we are
already on the mechanism Spack itself is moving to.

**Risk noted:** we carry maintenance alone versus their 13/31 contributors.
Mitigation is exactly the adoption list above — ride upstream Spack features
and borrow proven site-config patterns instead of inventing parallel ones.
