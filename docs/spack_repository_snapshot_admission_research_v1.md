# Spack repository snapshot admission: primary-source research note v1

| Document control | Value |
|---|---|
| Date | 2026-09-16 |
| Status | Research note; upstream facts and a proposed local control, not an operator procedure or a security certification |
| Scope | `spack/spack-packages` release snapshots and source identity for Spack 1.x |
| Method | Official Spack documentation, source, and GitHub release/ref records only |

## Finding

Spack made the community `builtin` recipes a separately fetched Git repository
in Spack 1.0. The v1.0 release notes say that Spack 1.0 used the
`v2025.07` package release by default and introduced the ability to update or
pin that repository independently of Spack core
([Spack v1.0 release notes](https://github.com/spack/spack/releases/tag/v1.0.0#separate-package-repository),
[pinning example](https://github.com/spack/spack/releases/tag/v1.0.0#updating-and-pinning-packages)).
Current repository documentation permits a branch, tag, or commit pin and says
that `spack repo update` makes the checkout match that configuration. A branch
or an unpinned repository advances, whereas a tag or commit remains at the
configured ref
([Spack 1.2.2 repository pinning](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/repositories.rst#L165-L182)).

A local minimum-age rule can use this separation as an intake delay, but Spack
does not prescribe a 90-day delay and the published history does not establish
a quarterly cadence. The proposed 90 elapsed days is therefore a **local CSE policy proposal**,
not an upstream guarantee, NIST requirement, or proof of safety.

## Verified release history as of 2026-09-16

The official repository has published only four package-repository releases.
The elapsed gaps between their publication timestamps are approximately 119
days 5 hours, 138 days 15 hours, and 80 days 10 hours. The March-named release
was published on April 2 and explicitly says it was released out of phase with
the Spack tool release. Selection logic must inspect actual release publication
timestamps rather than infer a calendar from tag names
([official release list](https://github.com/spack/spack-packages/releases),
[official release metadata API](https://api.github.com/repos/spack/spack-packages/releases?per_page=20),
[`v2026.03.0` release](https://github.com/spack/spack-packages/releases/tag/v2026.03.0)).

| Package-repository release | Published (UTC) | Full commit resolved from the official tag ref |
|---|---:|---|
| [`v2025.07.0`](https://github.com/spack/spack-packages/releases/tag/v2025.07.0) | 2025-07-18 18:43:00 | [`4b8bb3514838ce9e8bbc2ca7f98e62dbd7100c63`](https://github.com/spack/spack-packages/commit/4b8bb3514838ce9e8bbc2ca7f98e62dbd7100c63) |
| [`v2025.11.0`](https://github.com/spack/spack-packages/releases/tag/v2025.11.0) | 2025-11-15 00:04:13 | [`119680aeee8ea802c6111b7167583bddef97e82f`](https://github.com/spack/spack-packages/commit/119680aeee8ea802c6111b7167583bddef97e82f) |
| [`v2026.03.0`](https://github.com/spack/spack-packages/releases/tag/v2026.03.0) | 2026-04-02 15:30:13 | [`0e093dad700a9be836b0d4aefc4bb5183e4990bd`](https://github.com/spack/spack-packages/commit/0e093dad700a9be836b0d4aefc4bb5183e4990bd) |
| [`v2026.06.0`](https://github.com/spack/spack-packages/releases/tag/v2026.06.0) | 2026-06-22 01:58:36 | [`d4f7c711a6a42f1c4d551c8fd10fce9a11340a81`](https://github.com/spack/spack-packages/commit/d4f7c711a6a42f1c4d551c8fd10fce9a11340a81) |

The full hashes above are the commit objects returned by the repository's
[official tag-ref API](https://api.github.com/repos/spack/spack-packages/git/matching-refs/tags/v202).

At 2026-09-16 00:00 UTC, `v2026.06.0` had 85 days 22 hours of elapsed
publication age and `v2026.03.0` had 166 days 8 hours. Under an exact 90-day
threshold, the newer release becomes eligible at 2026-09-20 01:58:36 UTC;
until then, the immediately prior age-eligible snapshot is `v2026.03.0`. This is
a calculation under the proposed local rule, not an upstream recommendation
or a finding that the older snapshot passes security and compatibility review.

## Immutable identity recommendation

Record both the human-readable release tag and the full 40-character commit it
resolved to during admission, but configure the governed build to use the
commit:

```yaml
repos:
  builtin:
    git: https://github.com/spack/spack-packages.git
    commit: d4f7c711a6a42f1c4d551c8fd10fce9a11340a81
```

This matches Spack's own v1.0 commit-pin example and avoids treating a mutable
name as the build identity. Spack's source-provenance guidance says Git tags
can move, recommends pairing a package source tag with a full commit, and calls
the full commit the trusted identity for Git downloads
([Spack 1.2.2 Git source rules](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L917-L933),
[movable tags and commit pairing](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L988-L1018)).
For a package-repository admission record, retain the tag, release-publication
timestamp, resolved commit, resolution/observation timestamp, assessor, and
decision. Re-resolve the tag on every assessment; if it no longer resolves to
the recorded commit, treat it as changed content requiring a fresh decision.
The runtime `repos.yaml` should contain the full commit as the active pin, with
the tag kept in the admission record rather than relied on as identity.

Apply the same rule to every effective Git-backed overlay. Spack searches
repositories in precedence order and an earlier custom repository can replace
a `builtin` recipe, so aging only `spack-packages` does not age or approve the
recipe that is actually selected
([Spack 1.2.2 repository search and override rules](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/repositories.rst#L364-L410)).

## What an age gate can and cannot establish

The gate can prevent automatic uptake of post-snapshot recipe churn, make the
recipe baseline reproducible, and create time in which defects or malicious
changes may be reported. It can also focus a delta review: Spack 1.2 provides
`spack repo show-version-updates REPOSITORY FROM_REF TO_REF` to enumerate
checksum- or commit-backed versions added between two refs
([command implementation](https://github.com/spack/spack/blob/v1.2.2/lib/spack/spack/cmd/repo.py#L658-L732)).

It cannot establish that the snapshot is safe. In particular:

- A recipe or version merged just before the release tag has only the
  snapshot's age, not a longer implied maturity. Release notes explicitly say
  these snapshots bring new packages, version updates, and deprecations
  ([`v2026.06.0` release](https://github.com/spack/spack-packages/releases/tag/v2026.06.0)).
- Waiting does not prove review occurred or that a vulnerability has been
  discovered. It can also delay fixes: `v2026.06.0` says it added deprecations
  for CVEs, so mechanically remaining on the prior release may retain content
  upstream has already identified as vulnerable.
- The pin fixes recipe-repository bytes, not every source selected by those
  recipes. URL sources are protected by their recorded checksum, and Spack
  refuses checksum mismatches unless the operator disables the check. Git
  branches and tags remain mutable unless concretization/source policy binds
  them to a full commit
  ([Spack 1.2.2 checksum verification](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L542-L564),
  [Git version provenance](https://github.com/spack/spack/blob/v1.2.2/lib/spack/docs/packaging_guide_creation.rst#L618-L648)).
- The baseline age does not transfer to overlays, newly selected versions,
  patches or resources introduced locally, externals, binary caches, Spack
  core, bootstrap inputs, compilers, or system modules. Each needs its own
  identity, review, and applicable integrity controls.
- A commit pin gives identity and reproducibility; it does not attest benign
  behavior, authenticate the intentions of recipe authors, or replace source
  and vulnerability assessment.

## Recommended local policy shape

Use an exact rule: admit the newest official package-repository release whose
upstream publication timestamp is at least 90 elapsed days old; if it is not
eligible, consider the immediately prior **supported and otherwise acceptable**
eligible release. Do not make age the only admission criterion. Review current
security findings before selection, permit documented expedited updates for
fixes, and reject or quarantine a candidate whose tag-to-commit mapping or
content changed.

For each candidate, compare the selected full commit with the previous admitted
commit; inventory new and changed recipes and added versions reachable from
the intended concrete DAG; review their URLs, checksums/full commits, patches,
resources, and build hooks; pin every effective overlay independently; and
retain the effective repository order. Never use `--no-checksum` in a governed
build. These checks preserve the useful delay while avoiding the unsupported
claim that age alone proves safety.
