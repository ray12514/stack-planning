# ReFrame site practices and reporting research v1

**As of:** 2026-09-06  
**Scope:** Primary-source review of how HPC sites organize ReFrame validation and results, with an implementation recommendation for independent CSE trials followed by full CSE, system MPI/GPU, and selected user-software validation.

## Decision summary

Start with ReFrame as a downstream acceptance harness for already installed software. Keep the validation suite in its own repository, encode each target cluster in ReFrame configuration, and keep tests portable. Do **not** make ReFrame's Spack build-system integration a prerequisite: tests can load CSE modules, run installed executables, compile small probes with the exposed compiler/MPI wrappers, and submit through the native scheduler.

For the first CSE trials, retain four native products from every run: the versioned JSON run report, JUnit XML, performance logs, and ReFrame output/stage artifacts. Publish JUnit into the CI interface and a short generated Markdown summary linking to the full artifacts. This gives release reviewers a useful result without operating a database or dashboard.

Add a trend service only after repeated runs create a real comparison need. ReFrame's SQLite result store is suitable for local history on a filesystem with reliable locking. For shared, multi-system history, import the versioned JSON report into a relational store such as PostgreSQL and query it from Grafana, while preserving the raw report as the evidence record. JSC's LLview continuous-benchmark feature is a credible alternative when Git-hosted CSV/JSON is a better organizational fit. Neither Grafana nor LLview is a capability shipped by ReFrame.

## What ReFrame ships today

The current starter pin is [ReFrame 4.10.3](https://github.com/reframe-hpc/reframe/releases/tag/v4.10.3), released 2026-08-27 and also published on [PyPI](https://pypi.org/project/reframe-hpc/4.10.3/). The initial source-level reporting audit used tag 4.10.2; the relevant defaults and implementations were rechecked against the installed 4.10.3 package and its version-matched documentation. Release 4.10.3 is a bug-fix release that includes fixes for a possible database index-creation deadlock, multi-metric failure reporting, and an unset `httpjson` authorization header. Use 4.10.3 for the starter environment and link documentation to that exact version; earlier search snapshots that labelled `stable` as 4.10.1 were stale.

| Product | Shipped behavior | Planning implication |
|---|---|---|
| JSON run report | ReFrame writes a detailed report under its report directory; `--report-file` sets the path and accepts `{sessionid}`. The default location also maintains a `latest.json` link. Report consumers are instructed to inspect `session_info.data_version` and `session_info.version`; the schema is shipped as `reframe/schemas/runreport.json`. | Treat JSON as the canonical machine-readable result. Retain it unchanged and make importers schema/version aware. Use a session-specific filename rather than overwriting `latest.json`. |
| JUnit XML | `--report-junit=FILE` emits JUnit XML; retries appear as individual test suites. The 4.10.3 generator does not export performance values. | Feed the CI test-results view. Do not make JUnit the canonical archive because it does not carry the complete ReFrame record. |
| Output and stage artifacts | Successful tests copy generated job scripts, stdout, stderr, and related files to the output tree. Failed tests retain their stage directory for diagnosis. | Archive both locations or selected contents with an explicit retention policy. Links from a summary are more useful than copying logs into prose. |
| Performance logs | The built-in file handler appends delimited records under `perflogs/<system>/<partition>/<test-base-name>.log`, rotating the file when its header changes. In 4.10.3 it records all tests, including sanity-only checks; performance cases add value, unit, reference, and thresholds. `--performance-report` exposes summaries/comparisons. | Preserve metric name, value, unit, reference, thresholds, test variant, partition, environment, and time. A missing metric is not a zero. |
| Result database | ReFrame 4.10.3 ships opt-in result storage (`storage.enable` defaults to false). SQLite is the only backend, with session/testcase inspection and performance comparison commands. It requires working file locks and warns that unsuitable network filesystems can hang. | Use it for single-runner or local analysis only after confirming locking. Do not place one shared database casually on a cluster filesystem. |
| Logging integrations | ReFrame performance log handlers include files, streams/syslog, Graylog, and `httpjson`; the latter POSTs a JSON log record and supports headers, extra fields, and retry/backoff behavior. | This is a producer hook, not a dashboard or durable result service. Introduce it only with a defined receiver, authentication, idempotency, and failure handling. |

These behaviors are documented in the version-matched upstream [tutorial](https://reframe-hpc.readthedocs.io/en/v4.10.3/tutorial.html), [command reference](https://reframe-hpc.readthedocs.io/en/v4.10.3/manpage.html), [configuration reference](https://reframe-hpc.readthedocs.io/en/v4.10.3/config_reference.html), and [run-report schema](https://github.com/reframe-hpc/reframe/blob/v4.10.3/reframe/schemas/runreport.json). Configure result storage explicitly and test that configuration against the pinned ReFrame release.

## Current and historical site practice

### CSCS: separate public suite, environment metadata, native scheduler, CI bridge

CSCS maintains the active public [cscs-reframe-tests repository](https://github.com/eth-cscs/cscs-reframe-tests). Its current layout separates checks, CI integration, system configuration, containers, utilities, and uenv-specific checks. That is strong evidence for keeping the suite independent from the software-stack repository while putting cluster interaction in configuration and shared helpers.

For Alps user environments, CSCS documents that ReFrame tests run automatically after an image build and on daily, weekly, and upgrade workflows. An image carries `extra/reframe.yaml` metadata describing features and compiler commands; ReFrame uses that metadata to select eligible tests. Tests may build against packages in the image or run a prebuilt application directly. The [CSCS Alps uenv ReFrame tutorial](https://eth-cscs.github.io/alps-uenv/pkg-reframe/) therefore demonstrates a useful separation: software metadata declares capabilities, while the validation repository owns test logic.

CSCS's cloud CI runner submits ReFrame jobs through FirecREST. Its documented default invocation includes `--report-junit=report.xml`, so the CI interface can display test outcomes even though compute runs occur on the cluster. The same documentation notes that the cloud runner has no direct cluster-filesystem access and synchronizes stage data through FirecREST. This is a concrete reason to keep result upload explicit rather than assuming that the CI service can browse a shared filesystem. See [CSCS CI/CD: ReFrame runner](https://docs.cscs.ch/services/cicd/).

The repository's current [`reframe_reporter`](https://github.com/eth-cscs/cscs-reframe-tests/tree/main/reframe_reporter) is a Markdown **eligibility/coverage** reporter. It calls `reframe --describe`, enriches results with uenv recipe and image-inventory metadata, and produces matrices across systems, modes, or tags. It is useful prior to execution to expose gaps in intended coverage; it is not a runtime-results history or performance dashboard.

Two retrieval cautions matter. The current repository exposes `main`, while the uenv tutorial still tells readers to clone an `alps` branch; current repository state should win over that stale example. Also, the older [CSCS container-recipes repository](https://github.com/eth-cscs/container-recipes) demonstrates GitLab build/test/deploy templates with ReFrame but was archived on 2026-05-20, so it is historical guidance rather than a foundation for new work.

### EESSI: portable test library, explicit scales, central dashboard

The active [EESSI test-suite repository](https://github.com/EESSI/test-suite) is a standalone, installable ReFrame suite. Its [v1.0.0 release](https://github.com/EESSI/test-suite/releases/tag/v1.0.0), published 2026-07-29, includes factored common configuration, process-binding validation, and support for testing programming environments from multiple EESSI versions in one run. It also vendors `hpctestlib` because ReFrame 4.10 and later no longer ship that library. That last change is a reminder to own or pin shared test helpers instead of relying on incidental framework contents.

EESSI's documentation gives reusable portability practices:

- Put site topology, scheduler resources, partitions, features, and programming environments in [site-specific ReFrame configuration](https://www.eessi.io/docs/test-suite/ReFrame-configuration-file/). EESSI recommends a separate configuration per system for readability and uses one prefix to co-locate output, stage, performance logs, and regular logs.
- Use tags for purpose and scale. The [usage guide](https://www.eessi.io/docs/test-suite/usage/) defines a small `CI` subset and scaling categories from a core or GPU through multinode cases, and combines them with system, partition, and test-name filters.
- Keep checks topology aware. The [portable-test guidance](https://www.eessi.io/docs/test-suite/writing-portable-tests/) maps abstract scales to system topology and device types to partitions, discovers modules instead of hard-coding exact names, and uses run-only checks where installed applications already exist.

EESSI operates [dashboard.eessi.io](https://dashboard.eessi.io/). A current [SURF service description](https://servicedesk.surf.nl/wiki/spaces/WIKI/pages/269419321/Visualization+projects) identifies an internal instance for Snellius and the public EESSI instance, implemented with a Vue frontend, Python backend, and MariaDB API and maintained in the MultiXscale work. EESSI's [2025 webinar material](https://www.eessi.io/docs/training-events/2025/EESSI-webinars-MayJune-2025-001-Introduction-to-EESSI-20250505.pdf) describes system monitoring, cross-system performance comparison, and regression analysis. This verifies a live service and its role, but the reviewed first-party sources do not expose a public, maintained deployment repository. Treat it as proof that a central service is useful at federation scale, not as an off-the-shelf component for CSE.

### NERSC: strong historical production evidence, no verified current public implementation

Upstream ReFrame's historical [production use cases](https://reframe-hpc.readthedocs.io/en/v3.7.1/usecases.html) describe NERSC integrating ReFrame with internal GitLab and publishing collected results through Elasticsearch, Logstash, and Kibana, with daily and weekly test classes. NERSC's [2019 annual report](https://www.nersc.gov/assets/Uploads/Elements/FileList/Annual-Reports/2019-NERSC-Annual-Report.pdf) likewise describes automated ReFrame performance tests tied to internal GitLab and Slurm. Its [2021 annual report](https://www.nersc.gov/assets/Uploads/Elements/FileList/Annual-Reports/2021-NERSC-Annual-Report.pdf) says the suite was applied to software deployed on Perlmutter.

These sources support the pattern of scheduled tiers, CI orchestration, scheduler-native execution, and a separate search/visualization stack. They do not establish the state of NERSC's private pipeline in 2026, and no current public NERSC ReFrame implementation was verified in this review. It should therefore be cited as historical production evidence, not copied as a current reference architecture.

NERSC's current [job monitoring documentation](https://docs.nersc.gov/jobs/monitoring/) exposes scheduler accounting through `jobstats`, while its [performance-tools documentation](https://docs.nersc.gov/tools/performance/) covers application profilers. These tools illustrate the right boundary: ReFrame decides whether a validation case passed and records its measured values; scheduler and profiler services explain resource behavior.

### JSC/Jülich: adjacent benchmark and telemetry system, not verified ReFrame adoption

No current first-party source reviewed here verifies that JSC uses ReFrame. JSC does maintain two useful adjacent systems:

- [JUBE](https://github.com/FZJ-JSC/JUBE) defines reproducible YAML/XML benchmark workflows, including parameter combinations and scheduler execution. Its [tutorial](https://apps.fz-juelich.de/jsc/jube/docu/tutorial.html) documents unique run directories containing configuration, work packages, logs, stdout/stderr, analysis, and result files.
- [LLview continuous benchmarks](https://apps.fz-juelich.de/jsc/llview/docu/benchmarks/) pulls CSV and JSON result artifacts from Git and renders tables and curves with job IDs and commit metadata. Its [configuration reference](https://apps.fz-juelich.de/jsc/llview/docu/benchmarks/configuration/) supports metric extraction, grouping, annotations, pass/warn/fail state, and static, regression, and outlier validators. The ingestion bridge is documented in the [LLview installation guide](https://apps.fz-juelich.de/jsc/llview/docu/install/benchmarks/).

LLview is a plausible trend-view alternative if CSE exports an explicit CSV/JSON contract into a Git repository. It is not a native ReFrame integration. Its documentation also makes an operational point that applies to any importer: an aborted benchmark still needs to emit a result record if persistent failure history is expected.

LLview's [job-report metrics](https://apps.fz-juelich.de/jsc/llview/docu/jobreport/metrics_list/) include CPU load and memory, GPU utilization and power, filesystem I/O, and interconnect measurements. Correlation by scheduler job ID can connect those system conditions to a ReFrame test without conflating telemetry with the test's pass/fail contract.

## Dashboard choices and maintenance status

| Option | Verified status | Appropriate use |
|---|---|---|
| ReFrame native reports and perflogs | Shipped and documented upstream | First implementation and durable raw evidence. |
| ReFrame SQLite result store | Shipped; local SQLite only, with explicit locking warning | Lightweight comparisons on a controlled host/filesystem. |
| CSCS `reframe_reporter` | Active code in CSCS's test-suite repo | Pre-run coverage/eligibility matrices, not result trends. |
| EESSI dashboard | Live service; current SURF description identifies its architecture and maintenance context | Reference model for federation-scale reporting; no verified public deployment repo found. |
| LLview continuous benchmarks | Current JSC documentation and public JSC repository | Git-based CSV/JSON performance trends after building an adapter. |
| Grafana with PostgreSQL | Grafana's built-in PostgreSQL data source supports time-series/table queries, variables, annotations, and alerting | Preferred general-purpose shared trend view if CSE already operates Grafana/PostgreSQL. |
| “ReFrame Web” / “RFM dashboard” | No maintained upstream product with either name was documented or listed in the reviewed official ReFrame/CSCS repositories | Require an exact repository, owner, recent release, and deployment evidence before considering it. |

Grafana is a query and visualization layer, not the test-results system of record. Its [data-source documentation](https://grafana.com/docs/grafana/latest/datasources/) distinguishes Grafana from the systems it queries; the [built-in PostgreSQL data source](https://grafana.com/docs/grafana/latest/datasources/postgres/) supports both time-series and tabular queries. Prometheus can remain the system and service telemetry source, and Loki can retain operational logs. High-cardinality release/test/variant results fit a relational schema more naturally than a metrics store; join or link the two planes through session UUID and scheduler job ID.

Native VictoriaMetrics ingestion in Prometheus exposition format is only an [open ReFrame enhancement request](https://github.com/reframe-hpc/reframe/issues/3662), filed 2026-05-12; it is not present in 4.10.3. No released first-party Prometheus exporter or OpenTelemetry integration was found. Treat those paths as site-owned adapters unless a later pinned release documents otherwise.

## Recommended implementation for CSE validation

### Phase 1: independent trials with useful reports and no service

1. Create an independent validation repository with `checks/`, `config/`, `resources/` or small source probes, and shared helpers. Pin ReFrame and record both its version and report `data_version`.
2. Model the cluster in configuration: partitions, scheduler/launcher, compiler environments, module commands, CPU/GPU features, time limits, and scheduler resources. Let test files express required features and behavior rather than site names.
3. Consume the installed CSE release as a user would. Load modules, call installed binaries and MPI wrappers, compile small ABI/link/run probes, and run through the system scheduler. A test that needs a third-party source build may use normal ReFrame compile phases; it does not require ReFrame to drive the CSE Spack environment.
4. Define a bounded `smoke`/`CI` tier for each candidate release and separate scheduled tags for broader compatibility, performance, multinode, and destructive or scarce-resource cases. Begin with the CSE trial surface; expand the same framework to system MPI/GPU and selected user software only after the core workflow is dependable.
5. Give every invocation a session identifier and immutable artifact directory, for example `<release>/<system>/<partition>/<timestamp>-<session-id>/`. Emit at least:
   - `run-report-<session-id>.json`;
   - `report.xml` for the CI test view;
   - `perflogs/` CSV when tests expose performance variables;
   - output artifacts and retained failure stages;
   - a generated Markdown summary with pass/fail/error/skip counts, release and system identity, the exact suite and CSE revisions, and links to artifacts.
6. Capture provenance explicitly: release identifier, installed module collection or exact module list, compiler/MPI/GPU environment, ReFrame and suite revisions, system/partition, scheduler job IDs, and invocation. Record absence as unknown/not-produced rather than filling fields or metrics with zero.
7. Make release gating depend on named required checks, not aggregate percentages. Test selection and skipped/inapplicable cases must be reviewable so an empty or accidentally filtered suite cannot pass a release.

This initial design uses only files and the CI results interface. Store the raw bundle on reliable shared storage or an artifact/object service under a stated retention policy. It is enough to answer “what ran, against which release, what failed, and where is the evidence?” without creating a reporting platform first.

### Phase 2: local comparisons, then a shared trend service

Enable ReFrame's SQLite result storage for operator comparison only after validating the pinned version and filesystem locking. Keep per-run JSON even when SQLite is enabled.

When several systems or recurring runs require a shared view, add an idempotent importer with this shape:

- validate the report schema and reject or quarantine unsupported `data_version` values;
- archive the raw JSON by content hash/session ID before transformation;
- upsert immutable sessions, test cases, retries, and performance measurements into PostgreSQL;
- normalize dimensions such as release, system, partition, programming environment, test, parameterized variant, result, metric, unit, timestamp, suite revision, and scheduler job ID;
- keep thresholds and references alongside measured values so a dashboard does not invent pass/fail from a chart;
- expose read-only Grafana views for release qualification, failure history, and metric trends, with links back to raw artifacts and CI jobs.

If an organization already operates Git-based benchmark publishing, evaluate LLview instead of building Grafana dashboards. In either case, the adapter is a separately tested contract. ReFrame's `httpjson` logging can later reduce ingestion latency, but the retained run report remains the recovery and audit source.

### Telemetry complement

Use ReFrame to record functional assertions and application-level performance variables. Use the scheduler/accounting and node-observability stack for CPU, memory, GPU, network, filesystem, power, and job state. Propagate the ReFrame session/test identifier and scheduler job ID into both sides. This allows an operator to see that a metric regressed and then inspect node conditions without allowing a telemetry outage to rewrite a validation result.

## Claims deliberately not made

- This review does not claim current NERSC ReFrame operations beyond the latest public NERSC evidence found (2021).
- It does not claim JSC ReFrame adoption; JUBE and LLview are adjacent, first-party systems.
- It does not claim that the EESSI dashboard is available as a maintained public deployment package.
- It does not treat CSCS's `reframe_reporter` as a runtime-results dashboard.
- It does not present proposed VictoriaMetrics/Prometheus support as shipped, nor does it invent performance baselines, alert thresholds, or adoption counts.

## Primary sources

- ReFrame: [repository](https://github.com/reframe-hpc/reframe), [4.10.3 release](https://github.com/reframe-hpc/reframe/releases/tag/v4.10.3), [PyPI 4.10.3](https://pypi.org/project/reframe-hpc/4.10.3/), [4.10.3 tutorial](https://reframe-hpc.readthedocs.io/en/v4.10.3/tutorial.html), [4.10.3 command reference](https://reframe-hpc.readthedocs.io/en/v4.10.3/manpage.html), [4.10.3 configuration reference](https://reframe-hpc.readthedocs.io/en/v4.10.3/config_reference.html), [open VictoriaMetrics proposal](https://github.com/reframe-hpc/reframe/issues/3662).
- CSCS: [test suite](https://github.com/eth-cscs/cscs-reframe-tests), [`reframe_reporter`](https://github.com/eth-cscs/cscs-reframe-tests/tree/main/reframe_reporter), [Alps uenv/ReFrame tutorial](https://eth-cscs.github.io/alps-uenv/pkg-reframe/), [CI/CD service documentation](https://docs.cscs.ch/services/cicd/).
- EESSI/SURF: [test suite](https://github.com/EESSI/test-suite), [installation/configuration](https://www.eessi.io/docs/test-suite/installation-configuration/), [usage](https://www.eessi.io/docs/test-suite/usage/), [portable tests](https://www.eessi.io/docs/test-suite/writing-portable-tests/), [dashboard](https://dashboard.eessi.io/), [SURF visualization-project description](https://servicedesk.surf.nl/wiki/spaces/WIKI/pages/269419321/Visualization+projects).
- NERSC: [2019 annual report](https://www.nersc.gov/assets/Uploads/Elements/FileList/Annual-Reports/2019-NERSC-Annual-Report.pdf), [2021 annual report](https://www.nersc.gov/assets/Uploads/Elements/FileList/Annual-Reports/2021-NERSC-Annual-Report.pdf), [current job monitoring](https://docs.nersc.gov/jobs/monitoring/).
- JSC: [JUBE](https://github.com/FZJ-JSC/JUBE), [LLview continuous benchmarks](https://apps.fz-juelich.de/jsc/llview/docu/benchmarks/), [LLview benchmark configuration](https://apps.fz-juelich.de/jsc/llview/docu/benchmarks/configuration/), [LLview job metrics](https://apps.fz-juelich.de/jsc/llview/docu/jobreport/metrics_list/).
- Grafana: [data sources](https://grafana.com/docs/grafana/latest/datasources/), [PostgreSQL data source](https://grafana.com/docs/grafana/latest/datasources/postgres/).
