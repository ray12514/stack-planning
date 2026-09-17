# Spack 1.2 signing, SBOM, and security note

Status: supporting reference for the software stack SOP. This note separates
Spack 1.2 behavior from the CSE operating policy built on top of it.

The findings below were checked against the official Spack `v1.2.0` tag. The
relevant documentation and source files are unchanged in the `v1.2.1` patch
release.

## Build-cache signing and trust

Spack uses its own GPG keyring; it does not automatically use keys in a user's
normal GPG keyring. A new Spack installation starts with an empty keyring. A
public key can be deliberately added with:

```console
spack gpg trust <verified-public-key-file>
```

`spack buildcache keys --install --trust` is a convenience command that
downloads keys published by configured mirrors, installs them in Spack's
keyring, and trusts all of them. It is appropriate only when every key served
by that controlled mirror is intended to be trusted. The behavior and commands
are documented in Spack's [build-cache key
section](https://github.com/spack/spack/blob/v1.2.0/lib/spack/docs/binary_caches.rst#L220-L309)
and implemented by the [`gpg`
command](https://github.com/spack/spack/blob/v1.2.0/lib/spack/spack/cmd/gpg.py#L16-L120)
and [`buildcache keys`
command](https://github.com/spack/spack/blob/v1.2.0/lib/spack/spack/cmd/buildcache.py#L197-L210).

For a URL-style build cache, `spack mirror add --signed ...` or `spack mirror
set --signed ...` records that signing is required when pushing and signature
verification is required when installing. `spack buildcache push --signed`
overrides the mirror setting for one push. `--key <fingerprint>` selects the
signing key. The bypasses are `spack buildcache push --unsigned` and `spack
install --no-check-signature`; they should not be used in the normal release
path. See the official [signing
documentation](https://github.com/spack/spack/blob/v1.2.0/lib/spack/docs/binary_caches.rst#L281-L309)
and the exact [push selection
logic](https://github.com/spack/spack/blob/v1.2.0/lib/spack/spack/cmd/buildcache.py#L506-L533).

The signature is on each package's spec manifest. That manifest refers to the
package archive and spec metadata as content-addressed SHA-256 blobs, so a
verified manifest authenticates the checksums used to retrieve those objects.
Spack 1.2 does **not** sign the build-cache index manifest. The SOP must not
describe the entire mirror index as signed. See Spack's [package-signing
description](https://github.com/spack/spack/blob/v1.2.0/lib/spack/docs/signing.rst#L130-L173)
and [build-cache layout
caveat](https://github.com/spack/spack/blob/v1.2.0/lib/spack/docs/binary_caches.rst#L676-L704).

`spack gpg verify` is deprecated in 1.2 and exits with an instruction to use
`gpg --verify`. Normal Spack installation from a signed mirror performs the
package-manifest verification automatically. `spack buildcache check-index
--verify all` checks whether the index, package manifests, and referenced blobs
are present and consistent; it is not a substitute for signature verification.
See the [`gpg verify`
implementation](https://github.com/spack/spack/blob/v1.2.0/lib/spack/spack/cmd/gpg.py#L183-L194)
and [`check-index`
implementation](https://github.com/spack/spack/blob/v1.2.0/lib/spack/spack/cmd/buildcache.py#L1031-L1162).

### Recommended CSE policy

This is site policy inferred from the Spack behavior above:

- Maintain one dedicated CSE release-signing identity.
- Restrict the private key to authorized release operators and keep it out of
  shared consumer workspaces.
- Publish the public key and its full fingerprint through a controlled channel.
  Verify the fingerprint before running `spack gpg trust`.
- Mark the release mirror `signed`. Prohibit unsigned pushes and installation
  without signature checking in normal promotion and publication.
- Record the signing-key fingerprint with each release. Treat rotation or
  revocation as a release-management event.
- Run `spack buildcache check-index --verify all <mirror>` as an additional
  mirror-consistency check, not as the cryptographic trust decision.

## SBOM behavior

SBOM generation is automatic in Spack 1.2; it is not an on-demand export step.
After a non-external package installation, a post-install hook writes:

```text
<installation-prefix>/.spack/sbom/spdx-2.3.json
```

`spack location -i <package>` prints the installation prefix. Spack 1.2 emits
SPDX 2.3 only. Its documentation says the result contains the NTIA minimum
elements where the package metadata supplies them. See the official [SBOM
documentation](https://github.com/spack/spack/blob/v1.2.0/lib/spack/docs/advanced_topics.rst#L35-L51)
and the [v1.2.0 release
notes](https://github.com/spack/spack/releases/tag/v1.2.0).

The JSON describes the installed package and its concretized dependency graph.
Fields include package name and version, supplier when known, download location,
declared license, available source checksum or Git commit, and dependency
relationships. It sets `filesAnalyzed` to `false`. The generator explicitly
skips an external root spec, so system-provided externals require a parallel
inventory. These details come from the complete [Spack 1.2 SBOM
generator](https://github.com/spack/spack/blob/v1.2.0/lib/spack/spack/hooks/sbom_generate.py#L24-L148).

The SBOM should be retained as a release artifact, but copying it from every
package prefix into a release-record directory is a CSE procedure, not an
automatic Spack aggregation feature.

## CVE and installation-integrity boundaries

Spack 1.2 does not provide a CVE-matching or vulnerability-scanning command.
`spack audit` checks configuration, package recipes, HTTPS use, and external
detection. Its complete command list contains no vulnerability or CVE
subcommand. See the official [`spack audit`
implementation](https://github.com/spack/spack/blob/v1.2.0/lib/spack/spack/cmd/audit.py#L16-L57).

`spack verify manifest` detects files that were added, removed, or changed after
installation. `spack verify libraries` detects missing libraries and accidental
system-library dependencies. These are integrity and linkage checks, not
vulnerability scans. See Spack's [installation verification
documentation](https://github.com/spack/spack/blob/v1.2.0/lib/spack/docs/advanced_topics.rst#L53-L104).

The SOP requires an organization-approved vulnerability source or scanner to
assess the complete inventory:

1. the SPDX files produced for Spack-installed application packages;
2. a separately maintained inventory of system externals; and
3. the pinned Spack checkout and vendored libraries, its starting Python and host
   prerequisites, and bootstrap tools and their dependencies, including tools
   used for signing and managed installation.

The application lockfile and package SPDX files do not automatically cover the
third category. Follow [shared SOP Sections 4.4–4.5](software_stack_sop_v1.md#44-check-the-spack-version-and-repositories)
for intake assessment before execution, controlled provisioning, installed-tool
inventory and scanning, and independent acceptance before production use.
`spack bootstrap status` checks readiness; it does not assess vulnerabilities.
Record scanner coverage gaps and map vendored or custom-versioned components to
upstream identities when required. Malware checks and vulnerability matching
serve different purposes; retain both as required by the site.

For an actionable finding, the release record should identify the exact Spack
spec and DAG hash or the exact external package, disposition the finding, and
retain the scan result or reference. A corrected Spack package follows the
normal path: update inputs, concretize a new lockfile, rebuild, validate, sign,
and publish a new release. An affected system external remains blocked until
the system owner updates it or an approved non-external replacement is selected
and validated.
An affected Spack/bootstrap runtime follows the toolchain readmission procedure;
assess which builds and releases were exposed and revalidate or rebuild according
to the finding. Continue advisory review for retained toolchain versions even
when their pins remain unchanged.
