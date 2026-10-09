# Project rules for coding agents (NodiNajar)

- Science lives in src/compute. Every function there is deterministic and has a test in tests/. Run `pytest -q` before committing.
- No model or agent may compute or invent a number shown to users. Agents may explain numbers that come from stats.json.
- Alerts are fixed templates filled from computed values. Do not generate alert text with an LLM.
- Label NISAR output "PROVISIONAL". Label synthetic output "SYNTHETIC". Never remove these labels.
- Synthetic scenes use real NISAR pass dates only (docs/COVERAGE.md). Never show a pass date that NISAR did not make.
- The web demo must work offline from web/index.html (file://). Do not add runtime calls to external services without a cached fallback.
- Log any AI-generated code or text in docs/AI_USE.md.
- Licence: Apache-2.0. Cite every data source in README.md.
