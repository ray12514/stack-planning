# Baseline module sets (v1)

Status: parked follow-on design. The current profile reports observed loaded
modules and verified providers but does not implement `baseline_module_sets`.
Do not use the proposed YAML below in the Initial Conversion Trials.

## Purpose

Cluster Inspector should be able to report the module set that represents the
site's normal starting point for building software. Stack Composer can then use
that fact when a stack asks for a system-derived default, without probing the
machine itself or guessing from a long list of available modules.

This separates two concerns:

- **Cluster Inspector** reports observed or site-declared platform facts.
- **Stack Composer** decides how a requested stack uses those facts.

## Sources

Baseline module sets may come from two sources.

1. **Observed default shell**
   - Cluster Inspector records the modules already loaded in a clean login or
     compute shell.
   - This is useful when the site's default environment is the supported build
     baseline.
   - The source should be marked `observed`.

2. **Maintainer-provided file**
   - The site/package maintainer provides a small YAML file naming the supported
     baseline module set.
   - This is useful when the login default is noisy, incomplete, or not the
     desired software-build baseline.
   - The source should be marked `site-file`.

Both can exist at the same time. The profile should keep them distinct so
Stack Composer policy can choose one intentionally.

## Proposed profile shape

```yaml
baseline_module_sets:
  - name: observed-login
    role: login
    source: observed
    modules:
      - gcc/13.3.1
      - openmpi/5.0.8/gcc-13.3.1
    compiler:
      name: gcc
      version: 13.3.1
    mpi:
      name: openmpi
      version: 5.0.8
    confidence: probed

  - name: site-supported-build
    role: compute
    source: site-file
    modules:
      - gcc/13.3.1
      - openmpi/5.0.8/gcc-13.3.1
    compiler:
      name: gcc
      version: 13.3.1
    mpi:
      name: openmpi
      version: 5.0.8
    confidence: declared
```

The `compiler` and `mpi` fields are derived convenience fields. The modules are
the source of truth; derived fields should only be emitted when Cluster
Inspector can match the module set to reported compiler/MPI providers.

## Proposed Cluster Inspector interface

```bash
cluster-inspector probe-system \
  --system raider \
  --baseline-module-set baseline-modules.yaml \
  --output system.frag.yaml
```

Example input file:

```yaml
baseline_module_sets:
  - name: site-supported-build
    role: compute
    modules:
      - gcc/13.3.1
      - openmpi/5.0.8/gcc-13.3.1
```

Cluster Inspector should also be able to emit the current observed module set
without this file. The file is an override/declaration mechanism, not the only
way to get a baseline.

## Proposed Stack Composer policy

The existing `baseline` policy remains the lean reference default:

- Cray: gcc-family platform compiler where available.
- Generic Linux: gcc-family compiler where available.
- MPI: preferred provider from defaults, newest version when configured.

A new future policy value should consume baseline module-set facts explicitly:

```yaml
defaults:
  compilers: system-default
  mpi:
    provider: system-default
```

Meaning:

- Use the selected `baseline_module_sets` record from the profile.
- Resolve compiler/MPI from that record.
- Fail clearly if the selected baseline module set names modules that do not
  correspond to verified compiler/MPI providers.

This should be separate from `baseline`; otherwise a site-specific observed
default could silently change the portable behavior of existing stacks.

## Validation rules

Cluster Inspector should validate:

- every declared module name is syntactically usable by the local module tool;
- declared modules can be loaded together in a clean shell;
- compiler/MPI derived from the baseline are also present in the normal
  `compiler_providers` and `mpi_providers` inventory;
- the module set is tagged by source (`observed` or `site-file`).

Stack Composer should validate:

- `system-default` is only accepted when at least one baseline module set is
  present;
- ambiguity is explicit: if multiple baseline module sets are present, the
  stack/defaults must select one by name or role;
- no probing happens during render.

## Implementation order

1. Add the profile schema field and Cluster Inspector merge support.
2. Emit observed module sets from `probe-system` and/or `probe-node`.
3. Add `--baseline-module-set` file input.
4. Add Stack Composer `system-default` policy and validation.
5. Add Raider and Blueback fixture tests using both observed and file-declared
   baseline module sets.
