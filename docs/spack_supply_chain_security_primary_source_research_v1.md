# Spack supply chain security: primary-source research note v1

| Document control | Value |
|---|---|
| Date | 2026-09-01 |
| Status | Research note supporting the software stack SOPs; not an operator procedure |
| Scope | Spack 1.2.2, the Initial Conversion Trials trust model, and a bounded RPM/DNF comparison |
| Method | Primary sources only: official Spack documentation and source, SLSA, DNF, and RPM |

## Executive assessment

The security concern is valid: a Spack package repository is executable input.
Spack loads `package.py` through Python's import machinery, and package methods
can execute programs during a build. A package recipe is therefore not
equivalent to passive repository metadata
([Spack repository loader](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/repo.py#L128-L176),
[imperative install example](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L1297-L1308)).

The appropriate control is not to fetch the current public recipe repository
and reread every transitive `package.py` for every build. The appropriate
control is to admit an exact recipe-repository revision, review the change from
the last admitted revision, freeze the concrete dependency graph, stage
verified sources once, build without outbound network access, validate, and
then sign and publish the resulting binaries. Manual review still belongs at
the admission boundary for new and changed reachable recipes, local overlays,
high-risk hooks, and exceptions. It is one control in a layered process, not a
claim that recipes require no review.

Spack supplies useful mechanisms for that process, but it does not turn an
unreviewed recipe or source into trusted software. A source checksum proves
that bytes match the digest admitted by the recipe. A build-cache signature
proves that the holder of a trusted signing key signed the cache object. An
SBOM describes components using the metadata available to Spack. None of those
facts, alone or together, proves that the recipe is non-malicious, that the
upstream source is free of vulnerabilities, or that the build process was
tamper-proof.

## Security properties and limits

| Control | What Spack 1.2.2 provides | Important limit |
|---|---|---|
| Recipe identity | Git-backed package repositories can be pinned to a commit or tag, and `spack repo update` enforces the configured pin ([repository pinning](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/repositories.rst#L165-L182)). The canonical recipe hash is an input to package hashes ([hash inputs](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L1805-L1819)). | A commit pin identifies recipe bytes; it does not approve their behavior. Repository search order can also replace a built-in recipe with an overlay, so the effective namespace and order must be reviewed ([search and override rules](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/repositories.rst#L364-L410)). |
| Source integrity | URL sources require a checksum and fail on mismatch. SHA-256 or stronger is recommended. Full VCS commits provide stable source identity; mutable branches and tags do not ([checksum rules](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L542-L564), [Git provenance rules](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L618-L648)). | A digest authenticates content relative to the admitted recipe, not the upstream publisher. A malicious change that alters both URL and digest still passes. Prohibit `--no-checksum` in governed builds. |
| Concrete selection | `spack.lock` records fully configured concrete specs. Already concretized specs remain unchanged unless reconcretization is requested ([manifest and lock](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L39-L47), [concretization behavior](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L301-L324)). | The lockfile is not a signature, approval record, source archive, or complete build-platform attestation. Spack qualifies lockfile reproduction to the same or a compatible machine ([lockfile recreation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L84-L121)). Externals remain site-owned inputs that require a parallel inventory and validation record. |
| Recipe and log retention | An environment records package recipes used at install time and retains links to build logs ([environment install records](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/environments.rst#L346-L374)). | Retention supports audit and reconstruction; it does not establish who approved the recipe or whether the execution environment was isolated. |
| Source staging | Source mirrors are explicitly intended for sites without Internet access. A concrete environment can be mirrored with `spack mirror create -a`, and mirror creation fetches and checksum-verifies eligible content ([mirror purpose and creation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/mirrors.rst#L12-L77), [concrete-environment mirror](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/mirrors.rst#L142-L165)). | A configured mirror does not itself prove that no network fallback occurred. The build environment needs an enforced egress denial at the host, scheduler, container, or network layer. Missing approved content should fail the build. |
| Binary promotion | Spack build caches contain installed prefixes and metadata. It signs packages and verifies signatures by default; mirrors can explicitly require signing ([build cache creation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst#L27-L38), [signing controls](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst#L229-L309)). `spack install --use-buildcache only` prevents fallback to a source build ([cache-only consumption](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/binary_caches.rst#L99-L137)). | A valid signature authenticates CSE's promotion decision and object integrity, not semantic safety. Prohibit unsigned pushes and `--no-check-signature`. Trust a verified CSE key fingerprint, not every key downloadable from a mirror. |
| Recipe/config audit | `spack audit` contains consistency checks for configuration, package directives and attributes, HTTPS use, and external detection ([audit classes](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/audit.py#L180-L223), [package checks](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/audit.py#L375-L405)). | These are lint and consistency checks. They are not malicious-code analysis, package-recipe approval, or CVE scanning. |
| SBOM | Spack 1.2 generates an SPDX 2.3 SBOM after installation. Entries contain package/version, available source checksum or Git commit, declared license, supplier/download metadata when known, and dependency relationships ([Spack 1.2 release](https://github.com/spack/spack/releases/tag/v1.2.0), [SBOM generator](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/hooks/sbom_generate.py#L53-L170)). | The generator sets `filesAnalyzed` to false, uses `NOASSERTION` when metadata is absent, and skips an external root. It emits per-installation inventory, not a vulnerability result, malware result, recipe-review record, or release-wide external inventory. |

## Recommended CSE control chain

The Initial Conversion Trials already have the right high-level separation.
The generalized policy should make the gates explicit:

1. **Admit tooling and recipes.** Pin the exact Spack version and commit, the
   exact `spack-packages` commit, and every overlay repository commit. Record
   effective repository order. Review the change from the previously approved
   baseline and manually review all new or changed recipes reachable from the
   selected roots, including patches, resources, lifecycle hooks, and local
   customizations.
2. **Resolve and review.** Concretize in the restricted management area. Retain
   `spack.yaml`, all effective configuration scopes, `spack.lock`, evaluated
   specs and hashes, recipe snapshots, and the review decision. A new
   concretization is a new candidate release, not an in-place mutation of an
   approved release.
3. **Stage sources.** Fetch the concrete DAG in the egress-enabled intake step.
   Require checksums for archives and full commits for VCS inputs. Populate an
   approved source mirror and record its inventory. Quarantine or reject any
   source that cannot satisfy those controls.
4. **Build without egress.** Build as an unprivileged CSE builder using only
   admitted repositories, the reviewed lock/configuration, and approved local
   sources. Enforce network denial outside Spack. Preserve logs and the exact
   package recipes used.
5. **Validate and inventory.** Run package tests, linkage and runtime checks,
   installation-integrity checks, malware and vulnerability tools approved by
   the organization, and system-external inventory checks. Collect the Spack
   SPDX files, but do not treat them as scan results.
6. **Promote through a separate signing role.** Only validated outputs reach
   the CSE signing identity. Sign the build-cache packages, record the key
   fingerprint and release manifest, and make publication immutable. Builders
   should not have routine access to the release private key.
7. **Consume cache-only.** Published consumers trust the verified CSE public
   key and install only from the signed approved build cache. They do not
   fetch public sources or execute public recipes as part of normal
   consumption.

This makes package-by-package review scalable without eliminating it. The
baseline review is amortized across releases; later reviews focus on the
reachable recipe and source delta. Automated graph, checksum, audit, SBOM,
signature, test, and vulnerability gates cover the entire candidate, while
manual analysis is concentrated where code or trust relationships changed.

## Provenance terminology

Spack records valuable provenance facts: concrete specs and hashes, recipe
snapshots, source checksums or commits, build logs, installed-package metadata,
SBOMs, and signed build-cache objects. The release record should retain all of
them.

It should not claim that Spack 1.2.2 automatically emits SLSA build
provenance. SLSA defines provenance as verifiable metadata describing where,
when, and how an artifact was produced, including the build platform and
external parameters ([SLSA provenance definition](https://slsa.dev/spec/v1.2/provenance),
[build-provenance requirements](https://slsa.dev/spec/v1.1/requirements)). The
Spack SPDX generator does not contain that build-platform attestation. If CSE
needs SLSA-level claims, the controlled GitLab/build service must generate and
sign a separate build attestation that binds output digests to the approved
inputs and builder identity.

## Bounded comparison with RPM and DNF

RPM/DNF and Spack place the main trust decision at different points.

DNF normally selects prebuilt RPMs from configured repositories. It exposes a
package-signature check with `gpgcheck`, a separate repository-metadata check
with `repo_gpgcheck`, and TLS verification controls. Distribution and RPM
security policy may strengthen the upstream defaults
([DNF configuration reference](https://dnf.readthedocs.io/en/latest/conf_ref.html#gpgcheck)).
RPM package headers and payloads contain signatures and digests, and RPM can
compare installed files with the metadata retained in its database
([RPM signatures and digests](https://rpm.org/docs/4.20.x/manual/signatures_digests.html),
[RPM verification](https://rpm.org/docs/6.0.x/man/rpm.8)).

That model moves source-recipe execution into a distribution's controlled
build pipeline, so the ordinary consumer verifies a signed binary rather than
running an RPM spec file. It does not make RPM content intrinsically safe.
RPM packages may contain scriptlets that run arbitrary programs during
installation, removal, or related transactions
([RPM scriptlets](https://rpm.org/docs/latest/manual/file_triggers.html)). A
valid RPM signature, like a valid Spack build-cache signature, establishes the
signing identity and content integrity; it does not prove benign behavior.

Spack commonly executes a Python recipe and the upstream project's build
system on the target build system. That creates a larger build-plane trust
surface than cache-only RPM consumption. The CSE restricted-fetch,
egress-denied-build, validation, signing, and cache-only-publication process
intentionally converts normal Spack use into a closer analogue of a governed
binary repository. The strongest response to the security concern is therefore
not that Spack is as safe as DNF by default. It is that CSE can establish the
same key governance and immutable binary-consumption boundary while retaining
the compiler, ABI, provider, and architecture precision that HPC builds need.

## Policy gaps to close explicitly

The SOP and release policy should name the authority for each of these items:

* approval and pinning of Spack core, `spack-packages`, and overlays;
* required review depth for new, changed, and high-risk recipes;
* source-mirror admission and retention;
* enforcement and evidence for no-network builds;
* treatment and inventory of system externals;
* vulnerability and malware tooling, exception handling, and rescan cadence;
* separation of builder and release-signing authority;
* signing-key creation, storage, rotation, revocation, and fingerprint
  distribution;
* immutable release replacement and rollback; and
* retention of lockfiles, configuration, recipes, logs, tests, SPDX files,
  external inventory, scan results, signatures, and release manifests.

These are organizational controls built around Spack. Spack provides many of
the technical artifacts, but it does not decide who is authorized to admit,
approve, sign, publish, revoke, or accept risk.
