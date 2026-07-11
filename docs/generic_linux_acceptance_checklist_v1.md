# Generic Linux Acceptance Checklist

Apply this checklist after the common procedure in `runbook.md`. It covers
conventional Linux module trees, including Penguin-style systems; it does not
replace the common runbook.

## Profile facts

- [ ] Compiler identities are based on real compiler binaries, not umbrella or
      application modules that merely alter the environment.
- [ ] Alias modules and symlinked prefixes collapse only when they resolve to
      the same compiler identity.
- [ ] Every MPI provider/version is paired with the compiler that built it when
      that relationship is discoverable.
- [ ] Libfabric, UCX, PMIx, and scheduler integrations are classified as
      observed candidates; policy selects only compatible externals.
- [ ] Every discovered CUDA and ROCm toolkit generation has a real version,
      module, prefix, and compatible GPU architecture.

## Render and lockfiles

- [ ] Automatic selection chooses one coherent compiler/MPI/toolkit set; an
      explicit stack selection overrides it without changing profile facts.
- [ ] System and site externals are used only when policy allows them.
- [ ] Serial lockfiles contain no MPI implementation, including transitively.
- [ ] MPI lockfiles use one compiler-compatible MPI provider.
- [ ] GPU lockfiles use the selected external toolkit rather than fetching a
      second CUDA or ROCm generation.

## Runtime

- [ ] Serial and MPI compiler smoke tests run from clean module environments.
- [ ] Scheduler-launched multi-node MPI passes over the intended fabric.
- [ ] GPU compiler/runtime smoke tests pass on the target GPU node type.
- [ ] The `cse/<Compiler>` surface exposes exactly the expected lane selectors,
      and conflicting lane loads fail.
- [ ] Version-sensitive package module chains are tested: compatible chains
      load cleanly, and incompatible dependency mixes fail or are prevented.
