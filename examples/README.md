# Examples

Canonical reference fixture corpus for the Spack stack generation system.
Currently empty; populated by Phase 0b and Phase 0c.

## Layout

- `reference/science-stack/` — canonical self-contained reference stack
  fixture. Populated by:
  - **Phase 0b** — starter template set under `templates/v6/`
    (`contract.yaml`, `stack-defaults.yaml`, `configs/*` scope tree,
    `environments/<lane_kind>/spack.yaml.j2`).
  - **Phase 0c** — end-to-end golden fixture: one `profile.yaml`, one
    `stack.yaml`, and the expected rendered workspace as checked-in
    bytes. This is the conformance test the `stack-composer render`
    implementation must reproduce.

## Where the supporting helper script lives

- `scripts/spack-build` — reference local single-machine build script
  that drives Spack across the rendered workspace's lanes. Documented
  in `docs/stack_composer_design_v1.md` § Companion Script: `spack-build`.
  Ships in this repo as the canonical reference; sites may copy and
  adapt it.

## Status

- [ ] Phase 0b — templates/v6/
- [ ] Phase 0c — golden fixture
- [ ] `scripts/spack-build` reference script

These land here in `stack-planning` as canonical reference content. They
are intentionally *not* in the implementation repos (`stack-composer`,
`cluster-inspector`) — those repos copy or generate from these.
