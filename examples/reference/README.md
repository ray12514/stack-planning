# Reference Examples

This directory holds self-contained fixtures owned by `stack-planning`. They are
the canonical examples used to test schemas, rendering rules, and local build
workflow documentation without depending on any downstream deployment repository.

| Path | Purpose |
|---|---|
| `science-stack/` | Large multi-lane science-stack fixture used by v6 examples. |
| `scripts/spack-build` | Reference local single-machine bash script for building a rendered workspace. |

The reference fixture is intentionally generic. If a real deployment discovers a
new pattern, promote the pattern here only when it belongs in the generic model.
