# CSE Platform Compatibility Fingerprinting Concept v1

| Document control | |
|---|---|
| Date | 2026-08-21 |
| Status | Parked future architecture; not approved for implementation |
| Activation gate | Complete the Initial Conversion Trials and adopt their stack-confidence, reproducibility, runtime, and build-cache acceptance evidence |
| Intended future use | CSE SOP support for promotion to restricted, disconnected, or air-gapped sister systems |

## 1. Decision summary

CSE should eventually identify the portions of a software stack that are
binary-compatible across sister HPC systems. The mechanism should be a set of
stable, lane-specific Platform Compatibility IDs derived from a small,
canonical compatibility contract rather than from the complete Cluster
Inspector inventory.

This is a follow-on to the existing platform runtime fingerprint and platform
runtime transition gate. It does not replace the Initial Conversion Trials,
their acceptance tests, or the current restricted-build and cache-only
publication procedure. Those trials must first establish confidence in:

- reproducible concretization from retained lockfiles;
- successful C, C++, Fortran, Serial, and multi-node MPI execution;
- controlled compiler, MPI, launcher, fabric, and runtime-provider selection;
- signed build-cache production and cache-only installation; and
- release evidence sufficient to explain what was built, tested, and
  published.

No profile-schema, Cluster Inspector, Stack Composer, artifact-promotion, or
SOP implementation change is authorized by this document. The concept is
parked until the activation gate is deliberately opened.

## 2. Purpose

The future workflow should answer a deliberately narrow question:

> Can an already-approved CSE binary artifact be considered a candidate for
> direct promotion to this system and runtime lane?

It should not claim that two systems are identical, prove that an arbitrary
binary will run, or replace runtime acceptance testing. Exact compatibility-ID
equality is intended to be strong, conservative evidence for promotion. A
non-match does not by itself prove incompatibility.

The immediate architectural goals are to preserve the correct ownership seams,
define the eventual data contract, and record what must be investigated before
implementation.

## 3. Relationship to the current CSE model

The current model already records a **Platform Runtime Set** and reviews a
**Platform Runtime Transition** after a system or vendor update. The transition
compares the runtime set approved for a release with the candidate runtime set,
then decides per lane whether to revalidate, remain pinned, rebuild, or hold
promotion.

Platform Compatibility IDs should become a deterministic representation of the
same evidence, extended for sister-system comparison. They must not create a
second, competing compatibility model.

The eventual promotion envelope is:

```text
CSE artifact
  resolved lane identity
  Platform Compatibility ID
  Spack concrete DAG / lock identity
  artifact checksum and signature
  validation evidence
```

Each identity answers a different question:

| Identity | Question answered |
|---|---|
| Platform Compatibility ID | Does the target expose the normalized runtime contract required by this lane? |
| Spack lock / concrete DAG identity | Is this the exact software configuration approved for the release? |
| Artifact checksum and signature | Are these the exact reviewed binary bytes from the controlled build process? |
| Validation evidence | Did the required compile, runtime, MPI, cache-only, and consumer checks pass? |

## 4. Terminology

### 4.1 Compute observation

A compute observation is the normalized set of runtime-relevant facts collected
by Cluster Inspector while its probe is executing on one compute node. Login
host facts may be retained as inventory and build-host evidence, but they are
not authoritative for application binary compatibility.

### 4.2 Node capability class

A node capability class is a group of compute nodes with identical normalized
compatibility observations. Scheduler partitions, queues, constraints, and
resource labels help select nodes for inspection but do not define the class.

### 4.3 Lane compatibility contract

A lane compatibility contract is the policy-aware, canonical description of
the runtime surface selected for one resolved CSE lane. It includes only facts
that materially affect execution of that lane's binaries.

Because a system may provide several compilers, MPI implementations, MPI
versions, or GPU runtimes, final compatibility IDs belong to resolved lane
variants rather than to an undifferentiated `Serial`, `MPI`, or `GPU` label.

Examples include:

```text
gcc1250-serial
gcc1250-craympich910
gcc1250-craympich910-rocm700-gfx942
```

`Serial`, `MPI`, and `GPU` remain useful lane families and may be shown as
aliases when only one relevant variant exists.

### 4.4 Platform Compatibility ID

A Platform Compatibility ID is the full digest of one complete canonical lane
compatibility contract. An incomplete contract has no promotable ID.

## 5. Ownership and module seams

The future design should preserve the current facts-versus-policy separation.

| Owner | Responsibility |
|---|---|
| Cluster Inspector | Execute probes on compute nodes; normalize observations; report node capability classes, completeness, evidence, and base capability identities. |
| Stack Composer | Resolve actual lanes from profile facts plus stack/default policy; select compiler, target, MPI provider/version/flavor, GPU runtime, and sanctioned platform externals; assemble final lane compatibility contracts. |
| CSE build/promotion workflow | Attach compatibility ID, lock identity, checksum/signature, and validation evidence to an artifact; compare approved requirements with target capabilities; record promote/revalidate/rebuild/hold decisions. |
| Stack Planning | Own the canonical contract schema, hashing rules, compatibility semantics, and SOP requirements. |

The intended flow is:

```text
Slurm/PBS adapter
       |
       v
compute-node observations -- Cluster Inspector --> node capability classes
                                                      |
profile facts + stack/default policy -----------------+
                                                      v
                                      resolved Stack Composer lanes
                                                      |
                                                      v
                                     lane compatibility contracts
                                                      |
                                                      v
                          artifact + lock + checksum + validation evidence
```

Cluster Inspector must not infer which installed external or provider CSE
intends to sanction. If operations require Cluster Inspector itself to print
the final IDs, it should accept an explicit resolved lane-plan input produced
by Stack Composer and hash that plan together with the observed compute facts.
That keeps policy out of the probe implementation.

The later implementation should concentrate normalization, completeness,
classification, and hashing in one deep compatibility module with a small
interface. Scheduler variation belongs behind Slurm and PBS adapters at a
separate execution seam.

## 6. Existing Cluster Inspector inputs

The current Go implementation already reports much of the source inventory.

| Lane family | Existing facts | Important limitation |
|---|---|---|
| Serial | OS name/version, glibc, CPU target and alternates, compiler providers, focused system externals | OS, glibc, providers, and externals are currently treated as system-wide login/build-host facts. |
| MPI | MPI provider name/version, compiler pairing, per-compiler flavors, fabric type, fabric drivers/userspace, and Slurm PMI/PMIx launcher capabilities | These are primarily inventory identities and currently lack a complete compute-side runtime ABI contract. |
| GPU | GPU vendor, accelerator architecture, driver version, CUDA compatibility availability, and installed toolkit modules | The live node probe does not yet establish a complete toolkit/driver boundary or GPU-aware MPI runtime surface. |
| Execution | `this`, `srun`, and `pbsdsh` runners invoke the same self-contained binary on the selected host | One operator-declared representative node is probed; there is no scheduler discovery, allocation orchestration, all-node coverage, or automatic equivalence grouping. |

Existing hostnames, node counts, filesystem capacity, module inventories, and
other operational facts remain useful evidence but must not automatically
enter a compatibility contract.

## 7. Additional observations required

### 7.1 Serial contract inputs

The future Serial observation should cover:

- compute-node architecture and supported CPU target set;
- the lane-selected CPU target, supplied by the resolved lane plan;
- ELF architecture and dynamic-loader interface;
- libc family and compatibility boundary;
- selected compiler runtime libraries when dynamically required, including
  relevant SONAME and symbol-version boundaries; and
- only the sanctioned platform runtime externals selected for the lane.

Post-build ELF inspection should eventually record the artifact's actual
`GLIBC_*`, `GLIBCXX_*`, `CXXABI_*`, `GFORTRAN_*`, `DT_NEEDED`, interpreter,
and unavoidable absolute-path requirements. These artifact requirements are
more precise than treating the build host's complete installed runtime as a
binary requirement.

### 7.2 MPI contract inputs

The MPI contract should inherit the Serial contract and add:

- MPI implementation and product version;
- selected compiler/MPI flavor pairing;
- `libmpi` SONAME and an appropriate ABI or build identity;
- launcher and process-manager requirements, including PMI, PMI2, PMIx, or
  PALS as applicable;
- selected fabric interface and provider, such as libfabric/CXI, verbs, or
  UCX; and
- other sanctioned MPI runtime dependencies, including Cray GTL where
  applicable.

The current discovery vocabulary for Cray PMI, PALS, GTL, libfabric, and UCX
is useful input, but later work must represent their selected runtime
relationships explicitly rather than relying on a flat installed inventory.

### 7.3 GPU contract inputs

The GPU contract should inherit the MPI contract and add:

- accelerator vendor and lane-selected architecture target;
- GPU runtime/toolkit ABI selected for the lane;
- normalized driver/runtime compatibility boundary;
- CUDA compatibility-package state when relevant; and
- GPU-aware MPI/fabric dependencies, such as Cray GTL CUDA/HSA support or UCX
  CUDA/ROCm support.

Passive evidence establishes a promotion candidate. End-to-end GPU-aware MPI,
collective, and direct-memory behavior remains an acceptance-test concern.

## 8. Compute inspection through Slurm and PBS

Scheduler metadata should select where probes run; the probe executed on the
compute node should supply the compatibility facts.

### 8.1 Slurm adapter

The Slurm adapter should eventually:

1. discover candidate nodes and useful selection metadata through `sinfo` or
   `scontrol`;
2. support an existing allocation or an explicitly requested allocation;
3. execute one probe task per selected node through `srun`;
4. retain partition, constraint, GRES, and state only as selection/evidence
   metadata; and
5. report expected, selected, observed, failed, and skipped node counts.

### 8.2 PBS adapter

The PBS adapter should eventually:

1. discover candidate nodes and resources through `pbsnodes`, preferring
   structured output where the installed PBS supports it;
2. obtain or consume an allocation matching the requested resource selection;
3. execute the local probe inside that allocation through `pbsdsh` or the
   site's approved launcher; and
4. distinguish PBS rank selection from resource-class selection.

`pbsdsh` alone does not select an arbitrary node class; it launches within an
existing allocation. The adapter must therefore own allocation context as well
as command syntax.

### 8.3 Coverage modes

At least two explicit coverage modes are expected:

- `sample`: inspect representative nodes for initial discovery; and
- `all`: inspect every selected node for drift and promotion evidence.

The output must state the coverage mode. A sampled report must not be presented
as proof that every node belongs to the reported classes.

## 9. Node equivalence and drift

Equivalence grouping should follow these rules:

1. Normalize each compute observation independently.
2. Refuse to create a promotable capability ID when a material field is
   unknown.
3. Compute the complete normalized identity for each node.
4. Group nodes by identical identity tuples.
5. Retain scheduler labels and node membership outside the digest.
6. Never collapse an outlier into the majority class.

If 191 nodes report one identity and one reports another, the output should
contain two classes and identify the second as drift evidence. Node count is
class metadata, not a hash input.

## 10. Compatibility-contract shape

The final schema should be strict, versioned, and readable beside its digest.
An illustrative MPI contract is:

```yaml
schema: cse-platform-compatibility/v1
lane_family: mpi
lane_key: gcc1250-craympich910
serial_contract_id: cse-pcid-v1-serial-sha256:<full-digest>
mpi:
  implementation: cray-mpich
  version: 9.1.0
  library:
    soname: libmpi.so.12
    abi_identity: <normalized-identity>
  process_manager:
    interface: pmi2
  fabric:
    interface: libfabric
    provider: cxi
    abi_identity: <normalized-identity>
```

A GPU contract should reference its complete MPI parent identity. A Serial
contract should include its selected CPU target, OS ABI, and selected dynamic
runtime requirements.

The final field list must be established through real artifact and runtime
evidence from the Initial Conversion Trials, not solely by completing this
illustrative schema.

## 11. Canonicalization and identifiers

The later contract should use canonical JSON bytes as the digest input. YAML is
for review, not hashing.

Required properties include:

- schema version and lane family included in a domain-separated preimage;
- lexicographically ordered object keys;
- schema-defined ordering for every set-like array;
- normalized architecture, provider, interface, SONAME, and version values;
- explicit absent-versus-empty rules;
- no floating-point fields;
- SHA-256 with the full digest retained; and
- fixed cross-language test vectors shared by producers and consumers.

Suggested identifier form:

```text
cse-pcid-v1-<serial|mpi|gpu>-sha256:<64-hex-digits>
```

The human-readable contract must travel with the ID. Operators must be able to
explain a match or mismatch without reverse-engineering an opaque digest.

Material unknowns produce:

```yaml
status: incomplete
platform_compatibility_id: null
missing:
- mpi.process_manager.interface
```

An optional observation digest may group incomplete nodes for diagnostics, but
it must not be accepted as a promotion compatibility ID.

## 12. Fields excluded from compatibility hashing

The following are excluded unless a later artifact requirement demonstrates
that a particular value materially affects execution:

- system, login-host, and node names;
- serial numbers and asset identifiers;
- node and class counts;
- scheduler partition, queue, reservation, allocation, and job identifiers;
- timestamps, durations, probe versions, commands, evidence text, and
  confidence labels;
- RAM size, free disk, inode count, build-stage paths, and throughput class;
- GPU count, memory capacity, and topology;
- descriptions and operator-chosen class names;
- module-system implementation and version;
- unused installed compiler, MPI, toolkit, and external inventory;
- OS minor and kernel patch versions when no selected runtime requires them;
- module names and installation prefixes when the artifact is relocatable and
  the logical runtime interface is sufficient; and
- filesystem paths that are not embedded or otherwise required at runtime.

Absolute runtime paths require special handling. Different prefixes should not
make otherwise ABI-compatible sister systems mismatch, but an artifact with an
unavoidable absolute interpreter or RPATH dependency genuinely requires that
path. Such requirements should come from artifact inspection rather than from
the complete platform inventory.

## 13. Comparison semantics

Compatibility has directional dimensions:

- a CPU may support targets below its native microarchitecture;
- a newer glibc may satisfy an older required symbol boundary;
- GPU drivers support bounded runtime/toolkit generations; and
- some MPI or provider interfaces preserve ABI while changing implementation
  details that still require revalidation.

Therefore:

- exact ID equality is sufficient evidence that two normalized contracts are
  identical under the chosen schema;
- exact equality is not proof that runtime acceptance tests will pass;
- a non-match is not proof of incompatibility;
- later requirement-versus-capability comparison may establish safe
  directional compatibility without ID equality; and
- unknown compatibility holds promotion.

The initial implementation should prefer conservative exact matching. More
permissive comparison belongs in a later, separately reviewed policy step.

## 14. Proposed future output

To avoid prematurely changing the closed `profile-v1.json` contract, the
initial implementation should consider a sibling durable artifact such as:

```text
compute-compatibility-v1.json
```

Illustrative Cluster Inspector output:

```yaml
schema_version: 1
system: system-a
coverage:
  mode: all
  expected_nodes: 224
  observed_nodes: 224
classes:
- class_id: cse-node-v1-sha256:<full-digest>
  count: 192
  capability_ids:
    serial: cse-cap-v1-serial-sha256:<full-digest>
    mpi: cse-cap-v1-mpi-sha256:<full-digest>
    gpu: null
  completeness:
    serial: complete
    mpi: complete
    gpu: not_applicable
  observations:
    serial: {}
    mpi: {}
    gpu: null
```

Stack Composer can then combine those observations with each resolved lane and
emit final lane contracts in its deterministic render-plan/release artifacts.

The later artifact record should resemble:

```yaml
lane: gcc1250-craympich910
platform_compatibility_id: cse-pcid-v1-mpi-sha256:<full-digest>
spack_lock_sha256: <full-digest>
artifact_sha256: <full-digest>
validation_record: <release-relative-path-or-identity>
```

The exact artifact location and schema remain deferred.

## 15. SOP use for restricted sister systems

Once implemented and accepted, the restricted-system SOP should use the
fingerprint as follows:

1. Inspect the connected build system's compute classes.
2. Resolve and retain the approved lane compatibility contracts.
3. Build, validate, sign, and record the exact lockfiles and artifacts there.
4. Transfer the self-contained Inspector, lane-plan input, lockfiles, signed
   build-cache artifacts, sources, keys, and validation metadata through the
   approved controlled-transfer process.
5. Inspect the restricted sister system's compute classes without network
   access.
6. Compare final lane compatibility IDs and contract content.
7. Promote only exact approved candidates; distinguish `not_applicable` from
   `incomplete` and `mismatch`.
8. Perform the required cache-only install and target-system runtime acceptance
   tests before publication.
9. Record the comparison and disposition per lane.

The fingerprint supports the decision; it does not authorize transfer, bypass
security review, replace signatures, or eliminate target-system acceptance.

## 16. Activation prerequisites

Do not begin implementation until the project explicitly confirms that the
following are sufficiently mature:

- the Initial Conversion Trials have completed on the intended trial systems;
- the named stack-confidence and acceptance gates have been adopted and used;
- approved lockfile retention and forced reconcretization behavior are stable;
- compiler, MPI, fabric, launcher, and unmanaged-runtime evidence from the
  trials has been reviewed;
- signed build-cache and cache-only publication have passed in practice;
- the Platform Runtime Set and transition evidence have been exercised during
  at least one real runtime change or equivalent controlled comparison; and
- a concrete restricted sister-system workflow exists to validate the design
  against, rather than designing only from hypothetical topology.

## 17. Later implementation sequence

When the activation gate opens, use this order:

1. Amend the authoritative Cluster Inspector and stack-generation design docs.
2. Define the strict observation and lane-contract schemas, exclusions,
   completeness rules, canonicalization algorithm, and test vectors.
3. Add compute-local OS/ABI, fabric, launcher, MPI-runtime, and GPU-runtime
   observations.
4. Add Slurm and PBS scheduler adapters with explicit coverage reporting.
5. Add node capability grouping and drift reporting.
6. Emit base capability identities from Cluster Inspector.
7. Emit policy-aware, per-resolved-lane compatibility contracts and IDs from
   Stack Composer, or have Cluster Inspector consume an explicit Composer lane
   plan.
8. Add post-build ELF requirement extraction and artifact manifest fields.
9. Add conservative exact-ID comparison to the promotion workflow.
10. Validate the complete process on one connected/restricted sister-system
    pair before incorporating it into the production SOP.

No Spack calls, artifact transfer, promotion automation, or schema change is
part of the current parked phase.

## 18. Open questions for activation review

The implementation review should resolve these from trial evidence:

1. Which runtime libraries need exact content/build identities versus SONAME
   and symbol-version boundaries?
2. Should the first release permit only exact IDs, or also a narrowly defined
   directional compatibility check?
3. How should an artifact's actual ELF requirements override conservative
   build-platform observations?
4. Which Slurm and PBS allocation modes are available on the target sister
   systems?
5. Is all-node coverage operationally affordable for every release, or should
   it run on a separate drift cadence?
6. Which member-node details may be retained under site security policy?
7. Should compatibility observations remain a sibling artifact or become part
   of a future profile schema after the contract is proven?
8. Where should final comparison decisions live in the CSE release record and
   approval workflow?

These are activation questions, not current trial blockers.

## 19. Related current documents

- [Cray PE acceptance checklist](cray_pe_acceptance_checklist_v1.md) and
  [generic Linux acceptance checklist](generic_linux_acceptance_checklist_v1.md)
  define the Initial Conversion Trials confidence and acceptance direction.
- [Initial Conversion Trials runbook](runbook.md) is the active trial procedure.
- [CSE software stack SOP](cse_software_stack_sop_v1.md) is the active
  restricted-build, signed-cache, and cache-only publication procedure.
- [Platform Runtime Set design](platform_runtime_set_design_v1.md) defines the
  coherent runtime selection this concept would fingerprint.
- [Stack generation orchestration](stack_generation_orchestration_note_v1.md)
  defines the current per-lane platform runtime transition decision.
- [Cluster Inspector design](cluster_inspector_stack_profile_design_v1.md) and
  [profile extraction map](cluster_inspector_profile_extraction_map_v1.md)
  define the current facts-only probe contract.
- [CSE Spack learnings](spack-learnings/CSE-Spack-Learnings.md) records the
  unmanaged-runtime evidence motivating the transition gate.
