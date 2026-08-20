# Initial Conversion Trials Build Findings

Status: working record

This file records issues found while preparing, concretizing, building, and
verifying the four initial conversion-trial systems. It is a running technical
log, not a final incident report. Add an entry when an issue is observed; do
not wait for the build to finish.

Each entry identifies the observed symptom, root cause, immediate recovery,
and permanent mitigation. The disposition states where the durable fix
belongs. System-specific recovery remains in that system's Stack Content
runbook. Generic fixes belong in the CSE pilot templates, provider policy, or
the production renderer.

## Current findings

### ICT-001 — Trial CMake versions were absent from the pinned recipes

- Stage: preflight package policy
- Scope: all systems and compiler surfaces
- Status: mitigated
- Symptom: the approved CMake 3.31.12 and 4.4.2 roots could not be expressed
  using only the pinned `spack-packages` recipe generation.
- Root cause: those exact versions were not present in the pinned builtin
  recipe.
- Immediate recovery: none required in generated workspaces.
- Permanent mitigation: the `cse_trials` overlay extends the builtin CMake
  recipe with 3.31.12 as preferred and 4.4.2 as the second public version.
- Disposition: retain the overlay until the pinned recipe generation supplies
  the exact approved versions; then remove the redundant extension directly.

### ICT-002 — The builtin CCE compiler recipe did not cover the trial releases

- Stage: provider-policy preparation
- Scope: Cray CCE surfaces
- Status: mitigated; real CCE package builds still require validation
- Symptom: current site CCE releases could not all be represented by the
  pinned builtin package metadata.
- Root cause: the pinned recipe's release coverage and compiler metadata did
  not match the inspected CPE installations.
- Immediate recovery: none required in generated workspaces.
- Permanent mitigation: the `cse_trials` external-only CCE recipe carries
  versions 19.0.0, 20.0.0, and 21.0.0 while preserving the upstream compiler
  flags, wrapper paths, and implicit runtime-library metadata.
- Disposition: keep this isolated in the package overlay. Do not add CCE
  assumptions to generic Stack Composer code.

### ICT-003 — Architecture-specific Miniforge roots rejected microarchitecture targets

- Stage: concretization
- Scope: Core environments
- Status: mitigated
- Symptom: `miniforge3@26.1.1-3 target=x86_64_v3` had no matching version.
- Root cause: Miniforge is a prebuilt architecture-family distribution, not a
  source build for a Spack microarchitecture target.
- Immediate recovery: regenerate the affected workspace and reconcretize the
  Core environment.
- Permanent mitigation: render Miniforge with generic `target=x86_64` while
  retaining the reviewed portable target for source-built packages. The
  lockfile verifier enforces this exception.
- Disposition: generic package-class exception in trial package policy.

### ICT-004 — Cray MPICH ABI helper modules were mistaken for activation modules

- Stage: system discovery and static rendering
- Scope: Cray systems
- Status: mitigated
- Symptom: generated Cray MPICH module chains included
  `cray-mpich-abi*` helper modules.
- Root cause: provider discovery treated every related module as an activation
  module.
- Immediate recovery: apply the tracked provider exclusions through system
  hints, re-probe system facts, and regenerate the static catalog.
- Permanent mitigation: Cluster Inspector normalizes Cray MPICH activation
  modules and honors generic hint exclusions. The raw facts remain available
  as evidence.
- Disposition: generic Cray provider adapter plus system hint data; no manual
  edits to rendered catalogs.

### ICT-005 — A compiler prefix named the executable directory incorrectly

- Stage: GCC Core installation on Blueback
- Scope: inspected Cray-native GCC externals
- Status: mitigated
- Symptom: a configure probe reported that the C compiler could not create an
  executable even though the selected stage passed script and binary execution
  probes.
- Root cause: the inspected compiler prefix ended at the executable directory,
  and generated compiler paths appended another `bin` component.
- Immediate recovery: correct the inspected profile, rerender the static
  catalog, refresh the workspace controls, and reconcretize affected locks.
- Permanent mitigation: Cluster Inspector canonicalizes compiler driver
  directory prefixes before emitting provider facts. Blueback's runbook keeps
  the build-stage and compiler-environment probes used to distinguish this
  failure from a `noexec` filesystem.
- Disposition: generic provider-path normalization in Cluster Inspector.

### ICT-006 — GCC LAPACK inherited the Cray compiler-family marker

- Stage: GCC Common installation on Blueback
- Scope: a source-built GCC process launched from an ambient Cray programming
  environment
- Status: resolved in the active build; permanent template fix pending commit
- Symptom: LAPACK 3.12.1 invoked GNU `gfortran` with the CCE-only
  `-sinteger64` option.
- Root cause: the process used the Spack-built GCC but inherited
  `PE_ENV=CRAY`. LAPACK uses that marker to select the ILP64 Fortran option.
- Immediate recovery: unset `PE_ENV` and resume the shared-surface install. No
  reconcretization is required; completed prefixes are reused.
- Permanent mitigation: `cse-build` clears ambient `PE_ENV`, removes a loaded
  `PrgEnv-*` umbrella module, and lets Spack activate the reviewed external
  compiler module chain. The GCC seed compiler's module chain is now included
  in workspace module-state preparation.
- Validation: a reduced LAPACK flag-selection reproducer failed with GNU
  Fortran under `PE_ENV=CRAY` and passed with the marker removed. The Stack
  Content pilot test suite passes with a regression for this condition.
- Disposition: generic build-process hygiene in the workspace template, with
  Blueback recovery documented in its system runbook.

### ICT-007 — Repeated producer roots initially resolved to parallel dependency hashes

- Stage: lockfile verification and preflight builds
- Scope: repeated compiler environments
- Status: mitigated; continue verifying every regenerated lock set
- Symptom: roots could select an extra Python, a different Boost MPI build, or
  a Dakota dependency that did not reuse the approved producer hash.
- Root cause: `concretizer:unify:false` correctly permits independent public
  roots, but unconstrained transitive edges may select another valid producer.
- Immediate recovery: update explicit dependency constraints and reconcretize
  the affected environments.
- Permanent mitigation: pin Ninja and Dakota to Python 3.12.13; bind Dakota to
  the approved LAPACK, Boost MPI, CMake, and lane MPI producers; verify the
  repeated producer hashes across all locks.
- Disposition: package policy plus lockfile assertions. Do not replace
  `unify:false` with global unification.

### ICT-008 — GCC producer identity changed when Binutils was implicit

- Stage: preflight installation and lock verification
- Scope: shared GCC producer
- Status: mitigated
- Symptom: a concrete GCC producer without managed Binutils could be reused
  even though the trial required the `+binutils` compiler producer.
- Root cause: leaving the variant unspecified allowed another valid GCC
  concrete spec.
- Immediate recovery: regenerate the workspace and reconcretize all locks that
  contain the shared GCC producer.
- Permanent mitigation: every repeated GCC producer explicitly requests
  `+binutils`, and the lockfile verifier rejects a producer without the managed
  Binutils edge.
- Disposition: shared-compiler producer policy and lockfile verification.

### ICT-009 — Cray MPICH clean build environment omitted its libfabric runtime

- Stage: GCC MPI installation on Blueback
- Scope: `fftw@3.3.11+mpi` in the shared GCC 12.5.0 / external
  Cray MPICH 9.1.0 environment
- Status: mitigated in renderer policy; Blueback retry pending
- Symptom: FFTW configure finds
  `/opt/cray/pe/mpich/9.1.0/ofi/gnu/12.3/bin/mpicc`, but its `MPI_Init`
  compile/link probe fails. Direct fallback probes with `-lmpi` and `-lmpich`
  also fail.
- Confirmed boundaries: GCC Core, Common, and Serial completed on the same
  compute context. Both a direct native-wrapper probe and the exact Spack FFTW
  build-environment probe selected GCC 12.5 and the GNU-flavor Cray MPICH
  prefix, then failed with `libfabric.so.1` not found and unresolved
  `FABRIC_1.x` symbols from `libmpi_gnu.so`.
- Root cause: the external Cray MPICH record identified the correct MPI prefix
  but did not carry the selected platform libfabric runtime directory into
  Spack's clean package build environment.
- Immediate recovery: pull the renderer and content updates, rerender the
  static catalog, refresh the workspace, and freshly reconcretize only the
  affected MPI environment. Core, Common, and Serial prefixes remain valid.
- Permanent mitigation: the Cray MPICH provider adapter derives the selected
  libfabric prefix from the inspected platform runtime facts and emits
  `extra_attributes.environment.prepend_path.LD_LIBRARY_PATH` on the external
  MPI record. The adapter owns only the Cray product-tree `lib64` layout; it
  does not hard-code a system or libfabric version.
- Validation: static and full renderer regressions verify that the selected
  libfabric prefix is carried into the external Cray MPICH scope. The final
  gate is a successful Blueback MPI probe and FFTW install after rerendering.
- Disposition: generic Cray MPI provider policy. Do not add an FFTW recipe
  exception, global `LD_LIBRARY_PATH`, `--dirty`, or a Blueback-only version.

## Recording the next finding

For each new failure, capture the following before editing a manifest or
package recipe:

1. system, node context, compiler surface, and environment;
2. failed root and concrete hash;
3. first causal error from the current Spack log, not only the final
   `make: Error 2` or `failed to install` summary;
4. selected compiler, loaded modules, `PE_ENV`, build stage, and Spack version;
5. whether the recovery changes only process state, workspace controls,
   concrete DAGs, or installed prefixes; and
6. the regression or verification gate that prevents recurrence.

Do not add a system-specific exception until the evidence shows that generic
provider policy, package policy, or build-process hygiene cannot represent the
required behavior.
