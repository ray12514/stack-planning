# Design vs implementation coverage

A grep-once map from every documented design behaviour and every
schema field to the code that implements it (or to "NOT
IMPLEMENTED"). Companion to `cray_pe_coupling_inventory.md`: that doc
enumerates *Cray-specific* coupling; this one enumerates
*design-vs-code drift* across the whole surface.

The audit was prompted by the front-door modulefile gap discovered
2026-06-20: the v6 design specifies front-door modulefile behaviour
in detail (§4380-4480), the schema declares `modules.exposure:
front_door`, and the renderer silently ignores both — no template
consumes the field. We wanted to know what else has the same shape.

This is a living doc. The acceptance criterion for any change that
adds or removes a design behaviour is "I updated this coverage."

## How to read this doc

Per row:
- **Design / schema reference** — file:line or schema field path.
- **Code consumer** — file:line where the behaviour is implemented, or
  `NOT IMPLEMENTED` if no consumer exists.
- **Severity** — adoption impact:
  - **CRITICAL** — documented behaviour the user is told to rely on
    that silently does nothing. Hits credibility on first try.
  - **HIGH** — design feature with detailed spec, no code; can be
    worked around but advertised.
  - **MEDIUM** — schema or design feature with partial implementation
    or advisory-only intent.
  - **LOW** — cosmetic, future-looking, or documented as deferred.

---

## 1. stack.yaml fields

### 1a. modules block (`stack.modules.*`)

| Field | Consumer | Severity |
|---|---|---|
| `modules.format` (tcl/lmod) | NOT IMPLEMENTED | CRITICAL |
| `modules.additional_formats` | NOT IMPLEMENTED | HIGH |
| `modules.exposure` (front_door/direct) | NOT IMPLEMENTED | CRITICAL |
| `modules.init_module` | NOT IMPLEMENTED | HIGH |
| `modules.module_root` | NOT IMPLEMENTED | HIGH |
| `modules.publish_root` | NOT IMPLEMENTED | HIGH |
| `modules.hierarchy_style` | NOT IMPLEMENTED | HIGH |
| `modules.expose_provenance` | NOT IMPLEMENTED | HIGH |
| `modules.platform_module_policy` (prereq/autoload) | NOT IMPLEMENTED | HIGH |

**No template anywhere consumes `stack.modules`.** No `modules.yaml`
scope is rendered. No front-door modulefile is generated. The data is
loaded into the render context (`render/context.py:21`) and discarded.
See v6 §4380-4480 for the full design that this row table contradicts.

### 1b. externals block (`stack.externals.*`)

| Field | Consumer | Severity |
|---|---|---|
| `externals.compilers` (prefer_platform/build_all/mixed) | NOT IMPLEMENTED | HIGH |
| `externals.mpi` | NOT IMPLEMENTED | HIGH |
| `externals.openssl` (system/stack_built) | NOT IMPLEMENTED | HIGH |
| `externals.curl` (system/stack_built) | NOT IMPLEMENTED | HIGH |
| `externals.fabric_userspace` | NOT IMPLEMENTED | HIGH |
| `externals.gpu_toolkit` | NOT IMPLEMENTED | HIGH |

The renderer always emits all profile-derived externals as
`buildable: false`. The stack's externals policy is supposed to gate
that (e.g., `gpu_toolkit: build_all` should suppress the
`configs/gpu/amd-rocm/packages.yaml` externals so Spack builds ROCm).
Phase 5 templates render externals unconditionally; the policy field
is silently ignored.

### 1c. buildcache block (`stack.buildcache.*`)

| Field | Consumer | Severity |
|---|---|---|
| `buildcache.signed` | `manifest/draft.py:71` | OK |
| `buildcache.spack_generation` (format string template) | NOT IMPLEMENTED | HIGH |
| `buildcache.foundation_lane` (format string template) | NOT IMPLEMENTED | HIGH |
| `buildcache.payload_lane` (format string template) | NOT IMPLEMENTED | HIGH |
| `buildcache.push_after_every_step` | NOT IMPLEMENTED | MEDIUM (passes through to spack-build's loop, not enforced at render) |

The buildcache routing format strings (e.g., `payload_lane:
"payload/{os_id}/glibc-{glibc}/{spack_generation}/{system}"`) are
load-bearing for buildcache key correctness, per v6 §"Build-Cache
Keying". Render doesn't expand or write these. spack-build doesn't
read them. Cross-system buildcache reuse will silently break the
moment two sites have the same spec but different lane keys.

### 1d. release block (`stack.release.*`)

| Field | Consumer | Severity |
|---|---|---|
| `release.save_lockfiles` | NOT IMPLEMENTED | MEDIUM (lockfile is always saved at publish) |
| `release.save_manifest` | NOT IMPLEMENTED | MEDIUM |
| `release.retain_previous` | NOT IMPLEMENTED | HIGH (no cleanup of N-previous releases anywhere) |
| `release.promotion` (gated_manual/auto) | NOT IMPLEMENTED | HIGH (no promotion gate enforcement) |

### 1e. foundation_pins block (`stack.foundation_pins.*`)

| Field | Consumer | Severity |
|---|---|---|
| `foundation_pins` (`zlib`, `xz`, `zstd`, ...) | NOT IMPLEMENTED | CRITICAL |

The foundation pins are documented as required version pins applied
to every lane to guarantee binary compatibility across compiler
flavors (v6 §"Foundation lane"). Render emits them nowhere. Pins
provide their reproducibility benefit only if they reach
`packages.yaml.<pkg>.require` or `packages.yaml.<pkg>.version`. They
don't.

### 1f. helpers block (`stack.helpers.*`)

| Field | Consumer | Severity |
|---|---|---|
| `helpers.inspector` (available/preferred/disabled) | NOT IMPLEMENTED | LOW (advisory) |
| `helpers.render` | NOT IMPLEMENTED | LOW (advisory) |
| `helpers.ansible` | NOT IMPLEMENTED | LOW (advisory) |

These are advisory flags telling downstream tooling which helpers are
available. May be intentional pass-throughs — no behaviour was ever
specified for them.

### 1g. covered cleanly

| Field | Consumer |
|---|---|
| `schema_version` | `model/stack.py` (schema validation) |
| `name` | manifest + scope identity |
| `profile_contract.schema_version` | `validate/checks.py::cross_check_profile_contract` |
| `templates.set` | `validate/checks.py:31`, `render/engine.py:44` |
| `spack.version` | `manifest/draft.py`, stack-defaults merge |
| `builds[*]` | `render/plan.py::lane_candidates_for_build` |
| `per_system[*]` | `validate/checks.py::validate_per_system_narrowing`, `render/plan.py::apply_narrowing` |
| `package_repositories[*]` | `validate/checks.py::validate_package_repositories`, `render/engine.py::materialize_package_repositories` |

---

## 2. template-contract.yaml fields

| Field | Consumer | Severity |
|---|---|---|
| `build_classes[*]` | `render/plan.py::lane_candidates_for_build` | OK |
| `toolchains[*].compiler` | `render/plan.py::compiler_candidates` | OK |
| `toolchains[*].mpi` | `render/plan.py::mpi_provider_for` | HIGH — partial implementation only. Current code selects one provider name before the compiler loop, defaults Cray systems to `cray-mpich`, and does not resolve per-lane MPI policy. The design target is contract-driven provider selection with default `mode: auto`: use a compiler-compatible external MPI when proven, otherwise build MPI with Spack for that lane, while preserving platform-required Cray MPICH policy for production Cray lanes. |
| `toolchains[*].gpu_toolkit` | `commands/explain.py::resolvable_toolchains` (read for filtering, NOT used by renderer to decide GPU scope inclusion) | MEDIUM |
| `toolchains[*].allowed_compilers` | `render/plan.py:149` | OK |
| `node_selectors[*].match` | `render/plan.py::matching_node_types` | OK |
| `gpu_selectors[*].vendor` | NOT READ (vendor selection inferred from arch_target prefix instead) | MEDIUM |
| `gpu_selectors[*].arch_target` | `render/plan.py::gpu_selectors_for` | OK |
| `gpu_selectors[*].spack` (variant attrs like amdgpu_target, cuda_arch) | NOT READ — variant naming is hardcoded in `model/package_set.py::expand_gpu_variant` | MEDIUM (works for current vendor set but a new vendor requires Python edit, not contract edit) |
| `target_policies[*]` | NOT IMPLEMENTED | HIGH (every lane's target is currently `lane.cpu.preferred` from the profile; the contract's target policy is meant to override that for `core` vs `payload` lanes — see v6 §"Target Policy") |

---

## 3. profile.yaml fields

Most profile fields are consumed in some way (per the per-tool work
in Phase 1-6a). Notable absences:

| Field | Consumer | Severity |
|---|---|---|
| `vendor_cray.libsci` | NOT READ (rendered scope doesn't emit libsci externals) | MEDIUM |
| `vendor_cray.aocc` / `vendor_cray.intel` (schema-new) | Read by `vendor/cray/packages.yaml.j2` (Phase 5) | OK |
| `vendor_cray.cray_mpich.flavors[*]` | Read by `mpi/cray-mpich/packages.yaml.j2` (Phase 5) + `render/platform_modules.py` | OK |
| `gpu_toolkit_modules.rocm.spack_components` | Read by `gpu/amd-rocm/packages.yaml.j2` (Phase 5) | OK |
| `gpu_toolkit_modules.cudatoolkit` | Read by `gpu/nvidia-cuda/packages.yaml.j2` (Phase 5) | OK |
| `gpu_toolkit_modules.nvhpc` (standalone NVHPC toolkit) | NOT READ — only `cudatoolkit` is emitted as a CUDA scope; NVHPC is exception-lane-only and not separately rendered | MEDIUM |
| `compilers_external[*]` | Read by `vendor/linux/packages.yaml.j2` (Phase 5) | OK |
| `mpi[*]` | Read by `mpi/openmpi/packages.yaml.j2` (currently openmpi-only; mpich/mvapich2 etc. would need new scope templates) | MEDIUM |
| `fabric.userspace` | NOT READ (renderer doesn't emit fabric userspace externals like libfabric/ucx) | HIGH (these are real Spack externals on most Cray/Slingshot deployments) |
| `os.minor`, `os.glibc` | Read by `manifest/draft.py` and probe context; OK for now | OK |
| `modules_system.tool`, `.version` | NOT READ at render — fixture assumes Lmod/Tcl works; not validated against the rendered modulefile format | MEDIUM (related to module-emission gap) |
| `filesystem.install_tree_candidates[*]` | NOT READ (renderer doesn't emit `config.yaml` scope with `install_tree`) | CRITICAL — Spack must be told where to install; today it uses Spack default `/home/spack/spack/opt`. The profile supplies candidate shared filesystems and lock/space facts; stack/site/deployment input must select the final install tree. A real deployment will install in the wrong place until that policy is rendered. |
| `filesystem.source_cache_candidate` | NOT READ | HIGH |
| `filesystem.buildcache_candidate` | NOT READ | HIGH |
| `node_types[*].build_stage` | NOT READ at render — would normally feed `config.yaml.build_stage` | HIGH |

---

## 4. Per-scope packages.yaml / config files NOT rendered today

The Phase 5 work built `configs/{vendor,mpi,gpu,target,os}/.../packages.yaml.j2`.
The v6 design names several additional scopes the fixture template
set should ship; none exist:

| Scope file | Design ref | Severity | What it should contain |
|---|---|---|---|
| `configs/common/concretizer.yaml.j2` | v6 §"Concretizer Posture Per Environment Kind" | HIGH | `unify: false` for stack lanes; `unify: when_possible` for narrow application lanes; `reuse: true` for build-time, `reuse: false` for CI generators |
| `configs/common/config.yaml.j2` | v6 §Render Step (the `config.yaml` Spack scope) | CRITICAL | `install_tree: ...` from explicit stack/site/deployment selection, validated against `profile.filesystem.install_tree_candidates`; `build_stage: ...` from `profile.node_types[*].build_stage`; `source_cache: ...`; `misc_cache: ...` |
| `configs/common/compilers.yaml.j2` | Spack convention (every site needs this for compiler discovery to work without `spack compiler find`) | CRITICAL | Compilers declared per profile facts (or, with Spack v1+, the `packages.yaml::extra_attributes.compilers` we already emit might be enough — needs verification with `spack -e <env> compiler list`) |
| `configs/common/mirrors.yaml.j2` | v6 §"Build-Cache Keying" + `stack.buildcache.spack_generation` etc. | HIGH | Mirror entries with expanded `{spack_generation}`/`{system}` substitutions for each declared buildcache and source-cache |
| `configs/common/modules.yaml.j2` | v6 §4380-4480 | HIGH | Module hierarchy style, projections, blacklist, prefix inspections; reads `stack.modules.*` |
| `templates/<set>/modules/<exposure>/front-door.<tcl\|lua>.j2` | v6 §4400-4431 | CRITICAL | Per-lane front-door modulefiles: MODULEPATH prepend, conflicts with sibling lanes, prereq lines for `lane.platform_module_prereqs`, identity setenv (release, lane, compiler) |
| `templates/<set>/configs/foundation/packages.yaml.j2` | v6 §"Foundation lane" + `stack.foundation_pins` | CRITICAL | Pin `zlib`, `xz`, `zstd` and any other foundation pins via `require: "@<version>"` so every lane resolves to the same pinned versions |

---

## 5. v6 design behaviors with no implementing code

Things the design specifies as required render behavior that no
fixture template or renderer Python implements:

| Behavior | Design ref | Severity |
|---|---|---|
| Foundation-pin scope rendering | v6 §"Per-Compiler Core, Not Shared Core" + `stack.foundation_pins` | CRITICAL — without it, independently concretized compiler Cores can drift from the reviewed foundation version policy |
| Per-compiler Core visibility with payload lanes | v6 §"GPU lane Core composition" (committed) | Covered by the Phase 9 front-door module work: payload front doors must prepend the matching compiler's Core module root. Build-time lockfile composition is deliberately not part of the committed per-compiler Core model. |
| MPI provider policy (`mode: auto` default, per-lane compatibility, external-vs-Spack decision) | `non_cray_mpi_provider_lanes_hardening_note_v1.md` §Desired provider policy + v6 §"Generic Linux HPC" / §"Cray MPICH provenance" | HIGH — current render chooses a provider name without resolving compatibility against the lane compiler and cannot represent "use external if compatible, otherwise build MPI." This belongs in Stack Composer render policy, not in `cluster-inspector`; `cluster-inspector` should only report provider facts and preconditions. |
| Lane runtime module requirements emitted as `prereq` / `depends-on` in front-door module | v6 §"Lane Runtime Module Requirements" | CRITICAL — `platform_module_prereqs` is computed; nothing writes it to a modulefile |
| Provenance in modulefiles | v6 §"Provenance In Modulefiles" | HIGH |
| Public package modules (vs. front-door modules) | v6 §"Public Package Modules" | HIGH |
| Buildcache mirror keying with `{spack_generation}` / `{os_id}` / `{glibc}` substitution | v6 §"Build-Cache Keying" | HIGH |
| Site-smoke-tests scaffolding | v6 §"Verification Stages" | MEDIUM (deferred per design — but no harness exists) |
| `skipped_builds[*]` with `reason_code: per_system_empty` | v6 §"Failure modes ..." | Implemented (Phase 1's `per_system_empty` work) |
| Deterministic byte-identical re-render | v6 §"Render Step Specification" invariants | Implemented (Phase 1 fixture test) |
| Atomic workspace rename via `.rendering` side path | Same | Implemented |
| `release-manifest.yaml` final-phase shape | v6 §"Final Manifest" + schema | Implemented |
| `validate-template-set --concretize` Spack hook | v1 Phase 2 design | Deferred (flag wired, raises "not implemented") |

---

## 6. Severity-ranked gap list (the punch list)

Adoption-blocking (CRITICAL) — fix before the first real deployment:

1. **`configs/common/config.yaml` rendering** — without it, Spack installs to its default path, not the install tree chosen by the site/package owner. The profile should provide candidate filesystem facts; stack/site/deployment input should choose the final path. Every adoption hits this on first install.
2. **`stack.foundation_pins` enforcement** via a `foundation/packages.yaml` scope. Without it, the reviewed foundation versions do not apply consistently to each compiler's independently concretized Core.
3. **Front-door modulefile emission** + `modules.yaml` scope. `stack.modules.exposure: front_door` silently does nothing today. Users are told to load `ScienceStack/GCC/...`; nothing is emitted.
4. **`compilers.yaml` scope** — verify whether Spack v1.1's compiler discovery from `packages.yaml::extra_attributes.compilers` is sufficient (it may be); if not, render a `compilers.yaml`.
5. **Foundation buildcache reuse** — build each compiler's Core lane first, push it to the profile-compatible foundation cache, and configure payload lanes to reuse compatible binaries. The committed v1 model does not include one lane's lockfile from another lane.

High-impact (HIGH) but not blocking:

6. **`stack.externals` policy enforcement** — `prefer_platform`/`build_all`/`mixed` policy should gate which externals scope is rendered. Today all externals always rendered as `buildable: false`.
7. **`stack.buildcache.{spack_generation,foundation_lane,payload_lane}` format-string expansion** → `mirrors.yaml` scope and manifest fields.
8. **`stack.release.{retain_previous,promotion}`** enforcement — no cleanup of N-previous releases; no promotion gate.
9. **`profile.filesystem.source_cache_candidate`/`buildcache_candidate`** consumption — they're probed but no scope reads them.
10. **`profile.fabric.userspace`** externals — libfabric/ucx are real Spack externals on Slingshot/IB sites.
11. **MPI provider policy and compatibility resolution** — `toolchains[*].mpi` should default to `mode: auto`: use compiler-compatible externals when proven, otherwise let Spack build MPI for that lane. Cray MPICH remains platform-required for production Cray lanes, but non-Cray providers on Cray-hosted systems must be contract-selected instead of hardcoded away.
12. **`contract.target_policies`** — per-build-class target override (core → `foundation`/`baseline_target` vs payload → `lane.cpu.preferred`). Today every lane uses `lane.cpu.preferred`.
13. **`configs/common/concretizer.yaml`** — `unify: false` policy from the design.
14. **`vendor_cray.libsci`** rendering (Cray scientific library externals).

Medium / advisory (MEDIUM):

15. `helpers.{inspector,render,ansible}` are unused; clarify whether they're advisory or document them as deferred.
16. `gpu_selectors[*].vendor` / `.spack` (in contract) are not read; vendor inferred from arch prefix instead.
17. `gpu_toolkit_modules.nvhpc` (standalone NVHPC toolkit) — not rendered as a scope.
18. `mpi[*]` scopes — only openmpi has a template; mpich, mvapich2, intel-mpi would need new scope templates.
19. Site-smoke-tests scaffolding — verification hooks exist in manifest but no harness emits site tests.

---

## 7. What to do with this list

Suggested ordering for a Phase 7+ campaign:

- **Phase 7 — Adoption-blocking scopes.** Items 1, 4, 5 from §6. Without these, the first real install lands in the wrong place and has no compiler discovery. ~2 days.
- **Phase 8 — Foundation pins + foundation lane.** Items 2, 12. ~2 days.
- **Phase 9 — Front-door modules.** Item 3. ~3 days (covered in detail in agent memory `project-module-emission-gap.md`).
- **Phase 10 — Externals policy + buildcache mirrors.** Items 6, 7. ~2 days.
- **Phase 6f — Pre-CPE2 MPI/vendor hardening.** Item 11. This can
  run before or alongside Phase 10 because it is mostly lane-planner
  and provider-policy work.
- **Phase 11 — Cleanup / cosmetic.** Items 13-19. ~2 days.

After Phase 7-9, the first real deployment is plausible. Phase 10-11
can land in parallel with adoption feedback.

Total runway from Phase 6a (today) to "ready for first real-system
adoption": **~7-10 focused days of work**. Less than a sprint.

The number was much smaller in my head before this audit. The Phase
4/5 fixture-vs-design drift wasn't an isolated incident; the same
pattern bit us in `modules.*`, `externals.*`, `buildcache.*`,
`release.*`, `foundation_pins`, and `filesystem.*` — every block of
the stack.yaml that doesn't directly map to a build_request has
silent-no-op fields.
