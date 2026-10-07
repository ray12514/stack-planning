# HPCMP compiler hardening policy alignment

Research note based on public primary sources, 7 October 2026. This assesses the summarized white-paper claim supplied for this task; it does not reproduce or rely on the private source document.

## Findings

### HPCMP model and workloads

The HPCMP's official computation-centers page says it delivers capabilities to DoW RDT&E and Acquisition Engineering through five DSRCs. It describes each as including large-scale HPC systems, high-speed networking, multi-petabyte archival storage, and customer support; it also identifies four Affiliated Resource Centers, an HPC Help Desk, and a Data Analysis and Visualization Center. This supports a multi-center program model, without implying that every user/system has the same stack. [HPCMP: Computation Centers](https://www.hpc.mil/solution-areas/computation-centers)

The official Computational Technology Areas page states that HPCMP supports hundreds of projects organized into twelve areas. Its full page lists structural mechanics; fluid dynamics; chemistry, biology, and materials science; electromagnetics and acoustics; climate/weather/ocean modeling; signal/image processing; forces modeling; electronics/networking/systems; environmental quality modeling; integrated modeling and test environments; space and astrophysical sciences; and data and decision analytics. [HPCMP: Computational Technology Areas](https://www.hpc.mil/solution-areas/technology-areas)

The official HPCMP computation-centers and CTA pages were accessible in full for this check. The HPC Centers `about`, software inventory, and specific system-guide pages returned 502 errors, so this note does not assert particular installed applications, compiler suites, or MPI implementations from search snippets. The policy implication here is limited to the documented multi-center model and the need to validate any proposed flag policy on its actual target system.

### What the hardening claim can reasonably mean

Spack can provide a central *build-configuration enforcement point* for builds that actually use the configured Spack compiler integration. In Spack 1.2, compiler definitions live as external compiler packages in `packages.yaml`; their `extra_attributes.flags` support `cflags`, `cxxflags`, `fflags`, `cppflags`, `ldflags`, and `ldlibs`. Spack documents these flags as applied to every spec that depends on that compiler. Spack toolchains can also package compiler constraints and compiler-flag constraints in named presets. [Spack 1.2 compiler configuration](https://spack.readthedocs.io/en/v1.2.0/configuring_compilers.html), [Spack 1.2 package settings](https://spack.readthedocs.io/en/v1.2.0/packages_yaml.html#configuring-system-compilers-as-external-packages), [Spack 1.2 toolchains](https://spack.readthedocs.io/en/v1.2.0/toolchains_yaml.html)

This supports a carefully bounded statement: an administrator can configure flags centrally and have Spack pass them to eligible builds using the designated compiler, then inspect concretization and build logs and validate resulting binaries. It does not prove that every source build honors the flags, that every dependency was rebuilt, or that prebuilt/external software has those properties. It is also not proof of compliance with a specific STIG control. Package build systems can replace or filter flags, invoke other compilers, or link in ways that need per-package treatment; users can also select other compiler or binary sources unless policy prevents it.

The Spack 1.2 compiler-configuration guide documents external compiler definitions in `packages.yaml`, and the package-settings guide documents compiler-specific `extra_attributes.flags` there. Spack 1.2 also still publishes a schema for `compilers.yaml`, so these pages do not support a claim that the older file is removed or unsupported; for a new Spack 1.2 setup, the documented external-package route is `packages.yaml`. For scoped compiler/flag presets, Spack 1.2 provides `toolchains.yaml`; toolchains are attached to specs and therefore are not automatically a site-wide mandatory policy unless the environment/build process requires them. [Spack 1.2 compiler configuration](https://spack.readthedocs.io/en/v1.2.0/configuring_compilers.html), [Spack 1.2 package settings](https://spack.readthedocs.io/en/v1.2.0/packages_yaml.html), [Spack 1.2 compiler schema](https://spack.readthedocs.io/en/v1.2.0/spack.schema.html), [Spack 1.2 toolchains](https://spack.readthedocs.io/en/v1.2.0/toolchains_yaml.html)

### Flag semantics and scope

The supplied set describes GNU/Linux ELF hardening measures, not a complete compliance control set:

| Flag | Meaning and scope |
|---|---|
| `-fPIE` | Generates position-independent code intended to be linked into executables. GCC distinguishes this from `-fPIC`, which is suitable for shared libraries. Use `-fPIE` with a final executable link using `-pie`; do not indiscriminately apply it to shared-library objects. |
| `-fstack-protector-strong` | Adds stack guards to functions with local arrays or references to local frame addresses (as well as the base protected cases). It instruments eligible functions; it does not protect every function or eliminate the underlying defect. |
| `-D_FORTIFY_SOURCE=2` | Enables glibc fortification checks for selected library calls and additional diagnostics; some calls can be replaced with checked variants when the compiler can determine object bounds. It depends on compiler/glibc support and optimization for useful coverage. Level 2 may reject some conforming-but-unsafe uses. |
| `-pie` | Requests position-independent executable output at the final GCC-driver link step. It is paired with executable code compiled using `-fPIE`. |
| `-Wl,-z,relro` | Passes the linker option to create a GNU_RELRO segment intended to become read-only after relocation, subject to loader/linker/platform behavior. |
| `-Wl,-z,now` | Passes the linker option to resolve dynamic symbols at startup/load time rather than lazily on first call; paired with RELRO, commonly called full RELRO. |

Sources: [GCC code-generation options](https://gcc.gnu.org/onlinedocs/gcc/Code-Gen-Options.html#Code-Gen-Options), [GCC instrumentation options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html), [glibc source fortification](https://sourceware.org/glibc/manual/latest/html_node/Source-Fortification.html), [GNU ld options](https://sourceware.org/binutils/docs/ld/Options.html).

The GCC 12.5 manual documents the individual PIE and stack-protector flags but does not document the `-fhardened` umbrella option. Therefore a GCC 12.5 test should pass and inspect the individual requested flags; do not assume the newer convenience umbrella is available in 12.5. Newer GCC documentation describes `-fhardened` as a Linux-specific option whose enabled flags may change between major releases. Neither that option nor its present flag set is evidence that HPCMP or DoD mandates these flags or that they are equivalent to a STIG baseline. [GCC 12.5 instrumentation options](https://gcc.gnu.org/onlinedocs/gcc-12.5.0/gcc/Instrumentation-Options.html), [GCC 12.5 code-generation options](https://gcc.gnu.org/onlinedocs/gcc-12.5.0/gcc/Code-Gen-Options.html), [current GCC hardening options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html#Instrumentation-Options)

### Policy and compliance limit

DISA describes STIGs as security implementation guidance for DoD IT systems, bridging NIST SP 800-53 and the RMF. The publicly accessible HPCMP pages reviewed here describe missions, supported systems, applications, and user services; they do not state a universal HPCMP requirement to compile all software with the six listed flags. Searches of public DoD/DISA material did not identify a primary source establishing that exact flag set as a blanket HPCMP-wide mandate. The defensible wording is therefore “a proposed hardening baseline/policy profile aligned with selected compiler/linker protections,” pending the actual applicable STIG control IDs, system categorization, and authorization decisions. Avoid saying “STIG-compliant” solely because Spack is configured with these flags. [DoD Cyber Exchange: STIGs](https://public.cyber.mil/stigs/)

Compliance evidence would need to show, at minimum, which packages and executable targets are in scope; that the intended compile and final-link commands received the correct flags; that exceptions were approved and documented; and that installed or reused binaries were checked independently. Compiler flags establish build intent; artifact inspection and system-specific control assessment establish what was produced and whether it meets the applicable requirement. No performance impact is asserted here; measure representative workloads before adopting a fleet-wide default.

For this repository's CSE releases, the project procedure separately requires recorded security scans and validated compiler-hardening settings, with failures and exceptions retained alongside functional/performance results ([CSE restricted build and acceptance](cse_software_stack_sop_v1.md#93-restricted-build-and-acceptance)). The shared SOP also requires functional, numerical, and performance testing before approving hardening that may affect scientific results or runtime behavior ([target-system build and test](software_stack_sop_v1.md#93-build-and-test-on-the-target-system)). These are repository release gates, not evidence of an HPCMP-wide mandate.

## Recommendations for a standalone GCC 12.5 proof

1. Treat this as a GNU/Linux proof of mechanism, separate from any DoD/HPCMP compliance determination. Pin and record the exact GCC 12.5 build, target triple, libc/glibc, linker/binutils, and host architecture.
2. Use a small C and C++ executable with optimization (for example, `-O2`) and the supplied compile flags; place `-pie -Wl,-z,relro -Wl,-z,now` on the final executable link command. Confirm the actual compile and link lines, and inspect ELF type and program headers/dynamic flags (`readelf -h -l -d` or equivalent) for PIE, GNU_RELRO, and NOW/BIND_NOW evidence. Test a shared-library target separately with `-fPIC`; do not infer its policy from an executable test.
3. Test a small Fortran/MPI case separately if the target workflow uses those tools. The GNU flags are not a cross-compiler policy; verify how the site's wrapper modules propagate flags and whether the Fortran compiler/link driver accepts them.
4. In a Spack 1.2 trial, configure the selected external GCC in `packages.yaml` and exercise the documented compiler `extra_attributes.flags`; use an explicit toolchain or isolated test environment when scoping experimental constraints. First inspect `spack config blame packages`/`spack config get packages`, `spack spec`, and verbose build output. Treat the test as demonstrating Spack propagation for selected builds only.
5. Exercise boundaries intentionally: a shared library, a package with custom build logic, an external package, and a reused buildcache binary. Record which are built, which flags appear in the effective commands, and which need separate policy/verification. Do not claim universal enforcement from a successful standalone executable.
6. Compare representative application correctness and performance only after the build-mechanism test; do not infer a blanket performance result from these flags or from a micro-test.

## Primary references

- [HPCMP computation centers](https://www.hpc.mil/solution-areas/computation-centers)
- [HPCMP computational technology areas](https://www.hpc.mil/solution-areas/technology-areas)
- [GCC 12.5 instrumentation options](https://gcc.gnu.org/onlinedocs/gcc-12.5.0/gcc/Instrumentation-Options.html)
- [GCC 12.5 code-generation options](https://gcc.gnu.org/onlinedocs/gcc-12.5.0/gcc/Code-Gen-Options.html)
- [Spack 1.2 compiler configuration](https://spack.readthedocs.io/en/v1.2.0/configuring_compilers.html)
- [Spack 1.2 compiler flag configuration](https://spack.readthedocs.io/en/v1.2.0/packages_yaml.html#configuring-system-compilers-as-external-packages)
- [Spack 1.2 toolchains](https://spack.readthedocs.io/en/v1.2.0/toolchains_yaml.html)
- [GCC code-generation flags](https://gcc.gnu.org/onlinedocs/gcc/Code-Gen-Options.html#Code-Gen-Options)
- [GCC hardening options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)
- [glibc fortification](https://sourceware.org/glibc/manual/latest/html_node/Source-Fortification.html)
- [GNU ld RELRO and NOW options](https://sourceware.org/binutils/docs/ld/Options.html)
- [DISA STIG library](https://public.cyber.mil/stigs/)
