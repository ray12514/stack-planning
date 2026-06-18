# science-stack Reference Fixture

`science-stack` is the canonical large-stack example for the v6 planning model.
It exercises package-set reuse, front-door modules, Cray and generic Linux
profiles, GPU selector narrowing, internal package repositories, and release
manifest generation.

Planned shape:

```text
science-stack/
  systems/
  stacks/
  templates/
  package-sets/
  package-repos/
  expected-rendered/
```

The schema validation examples under `../../schemas/.validation/` are the current
minimal data fixtures until the full rendered fixture is added.
