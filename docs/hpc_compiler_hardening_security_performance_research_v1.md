# HPC compiler hardening, security, and performance: research note v1

| Document control | Value |
|---|---|
| Date | 2026-09-02 |
| Status | Research note; proposed policy basis, not an operator procedure |
| Scope | Performance-sensitive HPC software built with GCC, Clang, or HPE CCE and executed through Slurm |
| Method | Primary sources only: NIST, CISA/NSA, GCC, glibc, GNU binutils, LLVM/Clang, HPE, Red Hat, Debian, Slurm, and NERSC |

## Executive assessment

Compute-node isolation lowers the likelihood and blast radius of some attacks,
especially cross-user attacks against memory left on a node. It does not make
buffer overflows or other memory-corruption defects irrelevant. During a job,
the application still runs with the user's identity and can reach every file,
service, device, and peer rank that the job is authorized to reach. A defect or
exploit can therefore corrupt scientific results, alter checkpoints, read or
destroy persistent data, compromise other ranks in a multi-node job, consume
the allocation, or form part of an exploit chain against a driver, kernel, MPI
component, or privileged node service.

Post-job sanitization addresses residual state for the next tenant. It cannot
undo corruption, disclosure, or resource damage that occurred during the job,
and it does not erase data deliberately staged back to persistent storage.
NIST treats compute-node sanitization as important but explicitly says it must
be balanced with utilization. NIST also recommends measuring security-tool
performance, avoiding one-size-fits-all controls, and tailoring controls by
HPC zone and mission
([NIST SP 800-223, sections 4.2 and 4.5](https://doi.org/10.6028/NIST.SP.800-223)).
The newer HPC overlay likewise calls for fine-grained controls that meet
security needs without compromising system performance
([NIST SP 800-234, section 1](https://doi.org/10.6028/NIST.SP.800-234)).

The defensible policy is therefore neither to mandate every compiler-hardening
flag for every package nor to waive hardening because nodes are exclusive. CSE
should maintain an explicit, compiler-specific release baseline; qualify that
baseline on every supported compiler, language, node class, and link model;
benchmark controls that can affect hot paths or startup at scale; keep heavy
diagnostic instrumentation in separate validation builds; and allow narrow,
documented exceptions when evidence shows a compatibility or performance
failure.

## What isolation does and does not establish

### Isolation is a useful control

Exclusive allocation prevents unrelated jobs from being intentionally
scheduled onto the same node under the applicable Slurm policy. Job cgroups
can also constrain cores, memory, and devices. Per-job local storage can be
purged after completion. These controls reduce direct cross-user memory
exposure and persistence on local scratch.

They are not all inherent properties of a Slurm allocation:

* Slurm states that it does not itself limit access to allocated compute nodes;
  sites must configure mechanisms such as PAM if they want that restriction.
  The compute-node `slurmd` also runs as root because it initiates and manages
  jobs
  ([Slurm administrator guide](https://slurm.schedmd.com/quickstart_admin.html)).
* Slurm cgroup restrictions are separately configured. Current defaults for
  `ConstrainCores`, `ConstrainDevices`, and `ConstrainRAMSpace` are `no`, and
  Slurm advises sites to configure `pam_slurm_adopt` so SSH sessions cannot
  escape job cgroups
  ([Slurm `cgroup.conf`](https://slurm.schedmd.com/cgroup.conf.html)).
* A job allocation is a claim on resources, not a process-security sandbox.
  Slurm includes the user's UID and GID in the job credential, performs MPI and
  network setup, changes to that user identity, and then executes the task
  ([Slurm job-launch design](https://slurm.schedmd.com/job_launch.html)).
* Node sharing and privacy controls are policy choices. Slurm supports
  oversubscription and Multi-Category Security, but the MCS plugin defaults to
  `mcs/none`
  ([Slurm MCS guide](https://slurm.schedmd.com/mcs.html)).

The site's assertion that users receive exclusive nodes and that local state
is erased after each allocation is valuable evidence. It should be verified in
the system configuration and acceptance tests rather than treated as a general
property of Slurm.

An ordinary application buffer overflow begins inside that process. It does
not automatically cross a virtual-memory boundary or grant access to another
user's allocation. If the application accepts only trusted inputs, runs as an
unprivileged user on an exclusive node, has no outbound network path, and can
write only disposable data, deliberate exploitation is materially less likely
and its impact is narrower. In that situation, accidental result corruption,
job failure, and wasted allocation may be more plausible than lateral movement.
Those facts should lower the risk rating; they should not be generalized to
applications that parse outside data, load plugins, use shared storage, launch
across nodes, or retain outputs.

Compiler hardening also has a limited role. A stack canary normally detects a
particular overwrite and aborts; it does not repair the defect or protect heap
objects. Fortification covers selected library calls when object sizes are
known. PIE, RELRO, non-executable stack, CET, and CFI make selected exploitation
techniques harder. None of them proves memory safety. The control decision must
therefore consider input trust, reachable assets, process privileges, and the
value of correct scientific output, not only node placement.

### Risk remains during the allocation

NIST identifies the following HPC-zone properties directly:

* compute nodes are used by multiple users or tenants over time;
* application bugs and misconfiguration can cause resource exhaustion,
  performance degradation, and system outages;
* accelerators, high-performance interconnects, special protocols, and direct
  memory access can be difficult to monitor and may bypass kernel protections;
* privilege boundaries may depend heavily on POSIX permissions and OS
  capabilities; and
* depending on configuration, root compromise on one compute node can have
  consequences across HPC zones.

These findings are in
[NIST SP 800-223, sections 3.2.2 and 3.2.3](https://doi.org/10.6028/NIST.SP.800-223).
They explain why a compute node should not be treated as disconnected simply
because no other user's process is running there.

The practical attack and failure paths include:

1. **Persistent data.** A compromised process has the user's permissions on
   shared home, project, scratch, and output files. It can alter inputs,
   checkpoints, provenance, and results before they are retained. NERSC's
   filesystem documentation provides a concrete example: local per-job storage
   is purged, but users explicitly stage results to persistent filesystems
   ([NERSC filesystems](https://docs.nersc.gov/filesystems/)).
2. **Multi-node jobs.** An MPI job intentionally connects ranks and configures
   the high-performance network across allocated nodes. Memory corruption in
   one rank can send malformed data to peers, poison distributed state, or
   crash the full allocation. HPE provides sanitizer tooling that launches
   instrumented programs through `srun` across multiple ranks, which reflects
   that memory defects must also be tested at job scale
   ([HPE sanitizers4hpc](https://cpe.ext.hpe.com/docs/25.03/debugging-tools/sanitizers4hpc/guides/user_guide.html)).
3. **Scheduler and service trust.** Slurm uses signed job-step credentials and
   authenticated RPCs between clients, controllers, and node daemons. The
   credential is forwarded as part of task launch
   ([Slurm administrator guide](https://slurm.schedmd.com/quickstart_admin.html),
   [Slurm authentication](https://slurm.schedmd.com/authentication.html)). A
   process compromise does not automatically defeat those controls, but it
   occurs inside a system that has privileged daemons and authenticated control
   paths rather than inside a standalone appliance.
4. **Kernel, driver, and device attack surface.** Applications make system
   calls and interact with MPI transports, GPU drivers, filesystems, and other
   vendor components. Application hardening cannot secure those components,
   but reducing control-flow hijacking opportunities removes one possible
   first step in an exploit chain.
5. **Integrity and availability without an adversary.** A buffer overwrite can
   silently change a numerical result or checkpoint. A hardening check that
   turns that corruption into an immediate failed job can protect scientific
   integrity even when no attacker is present. It may also make a latent defect
   visible earlier, before it consumes a larger allocation.

Isolation remains part of defense in depth. It changes the risk rating and may
justify a different flag profile for compute-only code than for login-node
tools or privileged services. It is not a substitute for secure builds,
testing, least privilege, signed artifacts, or reasonable compiler hardening.

## What the principal flags do

The spellings below describe GNU and Clang-compatible toolchains on ELF Linux.
They must not be copied untested into every vendor compiler, language frontend,
GPU-device compilation, static link, or package. The flag record must identify
the compiler family and version, language, host target, linker, libc, and link
model.

| Control | Security effect | Performance and compatibility considerations | Proposed disposition |
|---|---|---|---|
| `-fstack-protector-strong` | Adds a guard to functions that have local arrays, call `alloca`, or reference local frame addresses. It checks the guard on function exit and aborts on failure. It covers more functions than `-fstack-protector` but fewer than `-fstack-protector-all` ([GCC instrumentation options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)). | It adds entry and exit work to selected functions. It does not cover heap corruption, use-after-free, every overwrite, or corruption that does not reach the guard. Debian describes the strong variant as avoiding significant performance penalties, but CSE still needs representative HPC measurements ([Debian `dpkg-buildflags`](https://manpages.debian.org/bookworm/dpkg-dev/dpkg-buildflags.1.en.html)). It requires a compatible `__stack_chk_fail` provider and is inappropriate for some freestanding or `-nostdlib` builds. | Baseline for eligible hosted CPU code after toolchain qualification. Benchmark known hot routines with local arrays. |
| `-fstack-protector-all` | Protects every function, including functions that the strong heuristic would omit ([GCC instrumentation options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)). | It can add work to small and hot leaf functions that do not contain vulnerable stack objects. It is not automatically a stronger whole-program defense against non-stack defects. | Not a universal baseline. Use for high-risk packages or after package-level measurement. |
| `-D_FORTIFY_SOURCE=2` | Uses compiler-known object sizes to add diagnostics and hardened glibc calls for selected buffer and input operations; a failed runtime check aborts ([glibc source fortification](https://sourceware.org/glibc/manual/latest/html_node/Source-Fortification.html)). | It requires optimization to be effective; Debian documents `-O1` or higher. Coverage depends on the compiler knowing the object size and on the program calling fortified libc interfaces ([Debian `dpkg-buildflags`](https://manpages.debian.org/bookworm/dpkg-dev/dpkg-buildflags.1.en.html)). It does not generally harden Fortran or GPU kernels merely because the macro is globally defined. | Baseline for eligible optimized C and C++ code using compatible glibc headers. |
| `-D_FORTIFY_SOURCE=3` | Extends fortification by using dynamic object-size analysis ([glibc source fortification](https://sourceware.org/glibc/manual/latest/html_node/Source-Fortification.html)). | glibc explicitly warns that level 3 can affect performance when a frequently executed fortified call has a complex dynamic size expression. It also requires a sufficiently recent compiler and glibc. | Benchmark-required candidate, promoted to a baseline only per qualified compiler/libc and workload class. |
| `-fPIE -pie` | Makes a main executable position independent so the OS can randomize its code location. Shared libraries already use position-independent code through `-fPIC` ([Debian `dpkg-buildflags`](https://manpages.debian.org/bookworm/dpkg-dev/dpkg-buildflags.1.en.html)). | Compile and link options must agree. GCC notes that PIC behavior and costs are target-specific, with material code-generation differences on AArch64, PowerPC, SPARC, and other targets ([GCC code-generation options](https://gcc.gnu.org/onlinedocs/gcc/Code-Gen-Options.html)). Static linking, vendor wrappers, assembly, and unusual build systems require validation. | Baseline for exposed utilities. Benchmark-required for performance-critical executables by target and link model. `-fPIC` remains the normal requirement for shared libraries. |
| `-Wl,-z,relro` | Creates an ELF segment that the loader makes read-only after relocation, reducing Global Offset Table overwrite opportunities ([GNU `ld` options](https://sourceware.org/binutils/docs/ld/Options.html)). | This is primarily a link and load property. It does not make all relocation state read-only when lazy binding remains. Verify the resulting ELF object rather than assuming a build variable reached the final link. | Baseline for supported dynamically linked ELF outputs. |
| `-Wl,-z,now` | Resolves dynamic symbols when the program starts or a library is loaded rather than on first call, allowing stronger relocation protection ([GNU `ld` options](https://sourceware.org/binutils/docs/ld/Options.html)). | It shifts symbol-resolution cost to startup. The possible impact on short jobs and simultaneous launch of many MPI ranks is an inference from the linker behavior and must be measured at representative rank count. It can also reveal unresolved-symbol or plugin-loading assumptions sooner. | Baseline for management and exposed utilities. Benchmark-required for rank-launched compute executables and plugin-heavy applications. |
| `-fstack-clash-protection` | Probes stack growth a page at a time so a large allocation cannot jump over an OS stack guard page ([GCC instrumentation options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)). | GCC states that target support is incomplete. On some targets it protects dynamic allocation only, with limited static-allocation coverage. Large stack frames and language-specific allocation patterns must be tested. | Qualified baseline where compiler and target support are verified; otherwise benchmark and compatibility gate it. |
| `-fcf-protection=full` | On supported x86 GNU/Linux targets, GCC uses Intel CET mechanisms to protect indirect branches and returns against ROP, COP, and JOP-style redirection ([GCC instrumentation options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)). | GCC documents this as x86 GNU/Linux-specific. It is not a generic Cray, AArch64, GPU, or vendor-compiler flag. Every linked object and runtime combination must be compatible with the intended enforcement environment. | Benchmark-required, architecture-specific release control. Never place in a portable global profile. |
| Clang `-fsanitize=cfi` | Adds control-flow-integrity checks that abort on selected invalid control transfers ([Clang CFI](https://clang.llvm.org/docs/ControlFlowIntegrity.html)). | Most schemes require LTO and visibility changes. Cross-DSO support has restrictions; assembly or non-Clang functions and exported functions can require jump tables, with documented code-size and runtime overhead. This can conflict with plugin-heavy scientific software and mixed-vendor libraries. | Separate qualified release variant for selected exposed or high-risk applications. Not a default for the full HPC DAG. |
| `-Wl,-z,noexecstack` | Marks an ELF output as not requiring an executable stack ([GNU `ld` options](https://sourceware.org/binutils/docs/ld/Options.html)). | Hand-written assembly without the correct `.note.GNU-stack`, GNU nested-function trampolines, JITs, and other code-generation techniques need review. GCC documents that some nested-function trampolines require executable stack memory ([GCC trampoline internals](https://gcc.gnu.org/onlinedocs/gccint/Trampolines.html)). Silently forcing the mark can create a runtime failure; silently permitting executable stack weakens the control. | Baseline expectation, with an explicit compatibility failure and security review for any executable-stack exception. Prefer linker warning or error gates plus final-object inspection. |
| `-fstack-check` | Arranges for OS or runtime stack-overflow detection; GCC says it is primarily designed for Ada and is not generally sufficient for stack-clash protection ([GCC instrumentation options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)). | GCC documents changed allocation semantics, frame-size limitations, and inefficient fallback implementations that hamper performance. | Do not treat as a generic memory-security baseline. Use only for a language/runtime requirement established by testing. |
| ASan, TSan, MSan, UBSan | Instrument code to detect memory errors, data races, uninitialized use, and undefined behavior. HPE supports multi-rank sanitizer workflows for CCE and GNU builds ([HPE sanitizers4hpc](https://cpe.ext.hpe.com/docs/25.03/debugging-tools/sanitizers4hpc/guides/user_guide.html)). | Clang documents typical slowdowns of about 2x for ASan, 5x to 15x plus 5x to 10x memory for TSan, and 3x for MSan. Full sanitizer runtimes are testing tools and can have their own production-security limitations ([ASan](https://clang.llvm.org/docs/AddressSanitizer.html), [TSan](https://clang.llvm.org/docs/ThreadSanitizer.html), [MSan](https://clang.llvm.org/docs/MemorySanitizer.html), [UBSan](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html)). | Test-only validation builds. A UBSan trap or minimal-runtime production variant requires its own approval and benchmark. |

### Do not adopt `-fhardened` as an unexpanded universal contract

Current GCC defines `-fhardened` as a production-oriented bundle that includes
fortification, C++ assertions, automatic-variable initialization, PIE, full
RELRO, strong stack protection, stack-clash protection, and x86 control-flow
protection. GCC also states that the expansion may change between major
releases and that the option is currently GNU/Linux-only
([GCC instrumentation options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)).

That makes `-fhardened` useful evidence that these controls are not merely
debug instrumentation. It does not make the umbrella flag a stable CSE
contract. CSE should record the explicit, reviewed options for each compiler
version, or at minimum retain the output of `gcc --help=hardened` with the
release. A changing umbrella cannot be the sole evidence of a reproducible
policy across GCC, CCE, Intel, AOCC, NVHPC, host code, and device code.

Red Hat's current minimum for RHEL 9 C and C++ release builds includes `-O2`,
`-Wl,-z,now,-z,relro`, `-fstack-protector-strong`,
`-fstack-clash-protection`, and `_FORTIFY_SOURCE=2`, plus PIE for executables
and PIC for shared libraries
([Red Hat RHEL 9 compiler-hardening guidance](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/developing_c_and_cpp_applications_in_rhel_9/assembly_creating-c-or-cpp-applications_developing-applications)).
This is a credible GNU/glibc starting point. It is not proof that the exact
command line is correct for every performance-critical package or vendor
toolchain.

## Proposed risk-tiered policy

### Tier 1: qualified release baseline

Apply this profile to eligible hosted CPU code after one-time qualification of
the exact compiler, libc, linker, language frontend, architecture, and node
class:

* preserve the package's approved release optimization and architecture flags;
* use `-fstack-protector-strong`;
* use `_FORTIFY_SOURCE=2` for optimized C and C++ builds with compatible glibc;
* use `-Wl,-z,relro` for dynamically linked ELF outputs;
* require a non-executable stack unless a reviewed implementation requires an
  executable stack;
* use `-fstack-clash-protection` where the compiler and target provide the
  intended coverage; and
* retain useful format-security warnings for C and C++ builds, with a governed
  process for false positives.

This is a minimum, not a claim that every listed option is supported by every
compiler. An unsupported option is a failed qualification result, not a reason
to let a build tool ignore unknown flags.

Use a stronger default for CSE tools that run on shared login nodes, parse
untrusted input, communicate over networks, publish artifacts, or execute with
special authority. Their exposure differs from a closed, long-running
numerical kernel on an exclusive node.

### Tier 2: benchmark-required release controls

Consider the following only after the package and platform pass functional,
ABI, startup, scale, and performance validation:

* `_FORTIFY_SOURCE=3`;
* PIE for performance-critical main executables;
* `-Wl,-z,now` for rank-launched or plugin-heavy programs;
* stack-clash protection on a target where support or overhead is uncertain;
* `-fcf-protection=full` or the vendor's equivalent on supported hardware;
* Clang CFI with the required LTO and visibility model;
* `-fstack-protector-all`; and
* any additional vendor-specific control that affects optimization, code
  layout, linking, runtime libraries, or offload compilation.

Passing on a single-node microbenchmark is not enough for a library used by
MPI or GPU applications. The acceptance workload should include the scale and
link model in which users will consume it.

### Tier 3: test-only controls

Build separate validation artifacts with:

* AddressSanitizer and LeakSanitizer for memory errors and leaks;
* ThreadSanitizer for threaded CPU code where its limitations permit;
* MemorySanitizer where the relevant dependency closure can also be
  instrumented;
* UndefinedBehaviorSanitizer;
* compiler warnings and static analysis that are too disruptive for a release
  build; and
* language-appropriate bounds, initialization, and runtime checks.

Exercise representative MPI rank counts, OpenMP thread counts, I/O paths, and
CPU/GPU code paths. A test-only build is not published as the normal
performance module and must not populate the same build-cache identity as the
release variant.

### Tier 4: narrow exception process

An exception request must identify:

1. package, version, compiler, frontend, target, linker, libc, and link model;
2. the exact control to disable or modify;
3. the compile, link, runtime, numerical-correctness, ABI, or measured
   performance failure;
4. the smallest scope that resolves the failure, such as one package, one
   source file, one language, or one architecture;
5. compensating controls, such as stronger input restrictions, sanitizer test
   coverage, no-egress execution, read-only software mounts, or reduced file
   and network access;
6. the residual risk and data sensitivity;
7. the approving technical and security authorities; and
8. an expiration or review trigger tied to a compiler or package update.

"HPC performance" by itself is not sufficient evidence for an exception. A
repeatable result from a representative workload is. Conversely, a generic
security checklist is not sufficient evidence for imposing an unqualified
flag on every HPC package. NIST SSDF requires organizations to determine and
approve the compiler features to use, test that they work without causing
operational problems, continuously verify the approved configuration, and
make it available as configuration-as-code
([NIST SP 800-218, PW.6](https://doi.org/10.6028/NIST.SP.800-218)).

## Qualification and benchmark protocol

For each compiler-family profile:

1. **Record the complete toolchain.** Capture compiler drivers and versions,
   linker and libc versions, loaded modules, target, CPU or GPU architecture,
   optimization flags, LTO state, and static or dynamic link model.
2. **Probe support.** Compile and link small C, C++, and Fortran programs through
   the same wrappers used by Spack. Reject unknown or ignored options. For HPE
   CCE, load the exact CCE module and invoke `cc`, `CC`, and `ftn` as applicable.
   HPE discourages direct `clang` or `clang++` because those commands may miss
   the selected target and Cray libraries
   ([HPE CCE Clang reference](https://cpe.ext.hpe.com/docs/latest/getting_started/CPE-CCE-Clang-Reference.html)).
3. **Verify the artifact.** Inspect final executables and shared objects for the
   expected ELF properties. Do not accept presence in `CFLAGS` or `LDFLAGS` as
   proof that every package honored the option.
4. **Test compatibility.** Run package tests, downstream link tests, module-load
   tests, plugin and `dlopen` tests, mixed-language tests, and ABI checks.
5. **Test numerical correctness.** Compare accepted scientific outputs and
   tolerances. A hardening change that alters results is a release failure even
   if throughput improves.
6. **Measure representative performance.** Compare the proposed profile to the
   currently accepted optimized build using the same source, concrete DAG,
   compiler, target, inputs, node placement, affinity, rank/thread layout, and
   system state. Run enough repetitions to distinguish noise from regression.
7. **Measure the right dimensions.** Include steady-state throughput, wall
   time, MPI initialization and rank-launch time, collective latency or
   bandwidth where relevant, peak memory, CPU cycles or instructions, binary
   size, GPU kernel and transfer time, and I/O behavior. Evaluate short jobs
   separately from long-running kernels.
8. **Test scale.** Include single-node and representative multi-node runs. Test
   the production MPI launcher and provider, not only direct execution of one
   rank.
9. **Set thresholds before reviewing results.** CSE, application owners, and the
   ISSO should agree on numerical-correctness requirements and acceptable
   regression thresholds by workload class. This note does not invent a
   universal percentage because scheduler noise, job duration, startup costs,
   mission sensitivity, and allocation scale differ.
10. **Retain evidence.** Store the before/after commands, logs, raw measurements,
    summaries, binary inspection results, and approval with the release record.

NIST explicitly recommends benchmarking the performance penalty of HPC
security tools and tailoring security to different node categories
([NIST SP 800-223, section 4.5](https://doi.org/10.6028/NIST.SP.800-223)).
The benchmark is therefore part of the security decision, not an attempt to
avoid it.

## CCE and multi-vendor requirements

HPE CCE C and C++ are Clang/LLVM-based, but CSE must not infer that every
upstream Clang flag works identically through every CCE version or frontend.
HPE directs users to the loaded CCE documentation and compiler help, states
that the local man page is the more current source when documentation differs,
and requires Cray wrappers for the normal target and library integration
([HPE CCE Clang reference](https://cpe.ext.hpe.com/docs/latest/getting_started/CPE-CCE-Clang-Reference.html)).

For CCE qualification:

* load the exact `cce/<version>` and required target/provider modules;
* invoke the Cray PE wrappers, not an assumed compiler path;
* test C, C++, and Fortran independently;
* confirm which flags affect host code, device code, or only one frontend;
* inspect the actual compile and link commands;
* link against the intended Cray MPI and math/runtime libraries; and
* run multi-node validation with the production launcher and PMI/PMIx path.

The same rule applies to GCC, Intel, AOCC, NVHPC, and GPU compilers. The policy
defines security outcomes and evidence. A compiler-family mapping defines the
spelling used to achieve them.

## Recommended response to the ISSO request

CSE should accept the security objective and ask that the proposed flags be
handled as a reviewed control profile rather than as an opaque global string.
For every requested flag, the joint record should state:

| Required field | Decision question |
|---|---|
| Threat | Which memory-corruption or control-flow behavior does it mitigate? |
| Scope | Login tool, build tool, library, compute executable, host code, device code, or privileged service? |
| Support | Which compiler versions, languages, targets, linkers, and libc implementations implement it? |
| Evidence | How will the final artifact be inspected to prove that the control is present? |
| Compatibility | Which build, ABI, plugin, MPI, GPU, and numerical tests must pass? |
| Performance | Which representative workloads and scales must meet the agreed threshold? |
| Exception | Who accepts residual risk, what compensating control applies, and when is the exception reviewed? |

This preserves the security intent without treating an isolated compute node
as risk-free or treating a heterogeneous HPC software stack as if it were one
ordinary server executable.

## Source summary

* [NIST SP 800-223, HPC Security Architecture, Threat Analysis, and Security Posture](https://doi.org/10.6028/NIST.SP.800-223)
* [NIST SP 800-234, HPC Security Overlay](https://doi.org/10.6028/NIST.SP.800-234)
* [NIST SP 800-218, Secure Software Development Framework](https://doi.org/10.6028/NIST.SP.800-218)
* [CISA and NSA, Securing the Software Supply Chain for Developers](https://www.cisa.gov/sites/default/files/2023-12/ESF_SECURING_THE_SOFTWARE_SUPPLY_CHAIN_DEVELOPERS.pdf)
* [GCC instrumentation options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)
* [GCC code-generation options](https://gcc.gnu.org/onlinedocs/gcc/Code-Gen-Options.html)
* [glibc source fortification](https://sourceware.org/glibc/manual/latest/html_node/Source-Fortification.html)
* [GNU `ld` options](https://sourceware.org/binutils/docs/ld/Options.html)
* [Clang CFI](https://clang.llvm.org/docs/ControlFlowIntegrity.html)
* [Clang sanitizer documentation](https://clang.llvm.org/docs/)
* [Red Hat RHEL 9 compiler-hardening guidance](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/developing_c_and_cpp_applications_in_rhel_9/assembly_creating-c-or-cpp-applications_developing-applications)
* [Debian `dpkg-buildflags`](https://manpages.debian.org/bookworm/dpkg-dev/dpkg-buildflags.1.en.html)
* [HPE CCE Clang reference](https://cpe.ext.hpe.com/docs/latest/getting_started/CPE-CCE-Clang-Reference.html)
* [HPE sanitizers4hpc](https://cpe.ext.hpe.com/docs/25.03/debugging-tools/sanitizers4hpc/guides/user_guide.html)
* [Slurm administrator guide](https://slurm.schedmd.com/quickstart_admin.html)
* [Slurm job-launch design](https://slurm.schedmd.com/job_launch.html)
* [Slurm cgroup configuration](https://slurm.schedmd.com/cgroup.conf.html)
* [NERSC filesystems](https://docs.nersc.gov/filesystems/)
