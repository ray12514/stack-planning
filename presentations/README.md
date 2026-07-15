# Presentations

Stakeholder-facing material for the CSE stack. Detailed design stays in
`docs/`; these are the high-level tellings of it.

| File | What it is |
|---|---|
| `cse_lanes_model.pptx` | The lanes-model stakeholder deck (July 2026): CSE today → community prior art (NASA JSC, ALCF Polaris, Spack/E4S) → the lanes model → pilot scope → four-system test matrix → status. |
| `make_lanes_model_deck.py` | Regenerates `cse_lanes_model.pptx` beside the script (needs `python-pptx`; edit the source content and rerun the script). |
| `source-notes.md` | Digested notes from the source documents and official HPC Centers hardware inventory, with page-cited quotes, the four-system pilot rationale, and the convergence threads the deck draws on. |
| `cse_spack_editable_build_flows.pptx` | The original two-slide build-flow schematic (May 2026). Superseded by `cse_build_flow.pptx`; kept for provenance. |
| `cse_build_flow.pptx` | The redrawn build-flow schematic (light theme, two pilot surfaces per system, correct flow + reuse edges; Cray and Linux slides). Regenerate with `make_build_flow.py`. |
