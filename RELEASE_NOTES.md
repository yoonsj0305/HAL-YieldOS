## v3.0.11 - Release Artifact Hygiene Enforcement + Dirty Archive Prevention Patch

- Added `scripts/check_release_artifact.py` for release zip hygiene validation before GitHub upload.
- Added dirty archive detection: rejects cache folders, build folders, output folders, nested zips, wheels, tarballs, and dist_v* folders.
- Integrated release artifact hygiene validation into `scripts/build_release.py` via `validate_release_artifact()`.
- Added `tests/test_release_artifact_hygiene_enforcement.py` — 18 tests for dirty archive regression, exit codes, and workflow existence.
- Added manual GitHub Actions release-hygiene workflow (`.github/workflows/release-hygiene.yml`).
- Updated `docs/GITHUB_UPLOAD_CHECKLIST.md` to require official `build_release.py` artifacts and forbid manually zipped working directories.
- Updated `docs/GITHUB_RELEASE_CHECKLIST.md` — added artifact hygiene section.
- Updated `docs/GITHUB_CI.md` — added release-hygiene workflow documentation.
- Updated `docs/GITHUB_LAUNCH_NOTES.md` — added release artifact section.
- Preserved launch guard cross-platform path hotfix from v3.0.10.
- Preserved GitHub Actions tests and public-demo workflows from v3.0.9.
- Preserved GitHub launch baseline documentation from v3.0.8.
- Preserved GitHub public release readiness documentation from v3.0.7.
- Preserved SemFab confidence propagation from v3.0.6.
- Preserved Semiconductor Confidence Passport Exposure from v3.0.5.
- Preserved Semiconductor Confidence Missing Metrics patch from v3.0.4.
- Preserved Semiconductor Pilot Contract Alignment from v3.0.3.
- Preserved Recovery Compiler export and handoff manifest.
- Preserved Robot Pilot-Ready Pack strict validation.
- Preserved Functional Yield Essence metadata.
- No Recovery Compiler execution, recovery profile generation, recipe control, tool control, hardware control, timing closure, autonomous recovery, root-cause certification, or yield guarantee features were added.

---
## v3.0.10 - Launch Guard Cross-Platform Path Hotfix + CI Self-Consistency Patch

- Fixed cross-platform path bug in `scripts/check_launch_guard.py`: replaced `rel.replace("/", "\\")` with `ROOT.joinpath(*rel.split("/"))` via new `repo_path()` helper.
- Added `tests/test_launch_guard_cross_platform_paths.py` — 8 tests verifying `repo_path()` exists, uses `joinpath`, resolves paths correctly, and has no backslash-replace path construction.
- Updated `docs/GITHUB_CI.md` — added cross-platform path handling section.
- Updated `docs/GITHUB_UPLOAD_CHECKLIST.md` — updated release tag, title, and asset to v3.0.10.
- Preserved GitHub CI smoke test baseline from v3.0.9.
- Preserved GitHub public release readiness documentation from v3.0.7.
- Preserved SemFab confidence propagation from v3.0.6.
- Preserved Semiconductor Confidence Passport Exposure from v3.0.5.
- Preserved Semiconductor Confidence Missing Metrics patch from v3.0.4.
- Preserved Semiconductor Pilot Contract Alignment from v3.0.3.
- Preserved Recovery Compiler export and handoff manifest.
- Preserved Robot Pilot-Ready Pack strict validation.
- Preserved Functional Yield Essence metadata.
- Preserved default pytest / cli_e2e / release-heavy / installed-wheel / packaging marker stability.
- No Recovery Compiler execution, recovery profile generation, recipe control, tool control, hardware control, timing closure, autonomous recovery, root-cause certification, or yield guarantee features were added.

---
## v3.0.9 - GitHub CI Smoke Test + Launch Guard Patch

- Added GitHub Actions tests workflow with pytest, doctor --deep, and launch guard.
- Added manual public-demo GitHub Actions workflow.
- Added `scripts/check_launch_guard.py` — fast local and CI guard for public launch boundaries.
- Added `docs/GITHUB_CI.md` — CI documentation for tests and public-demo workflows.
- Added `docs/GITHUB_UPLOAD_CHECKLIST.md` — checklist for GitHub repository setup and first release.
- Updated README CI badge to linked format.
- Preserved GitHub launch baseline documentation from v3.0.8.
- Preserved GitHub public release readiness documentation from v3.0.7.
- Preserved SemFab confidence propagation from v3.0.6.
- Preserved Semiconductor Confidence Passport Exposure from v3.0.5.
- Preserved Semiconductor Confidence Missing Metrics patch from v3.0.4.
- Preserved Semiconductor Pilot Contract Alignment from v3.0.3.
- Preserved Recovery Compiler export and handoff manifest.
- Preserved Robot Pilot-Ready Pack strict validation.
- Preserved Functional Yield Essence metadata.
- Preserved default pytest / cli_e2e / release-heavy / installed-wheel / packaging marker stability.
- No Recovery Compiler execution, recovery profile generation, recipe control, tool control, hardware control, timing closure, autonomous recovery, root-cause certification, or yield guarantee features were added.

---
## v3.0.8 - GitHub Final Polish + Repo Launch Patch

- Finalized README first-screen presentation for GitHub launch.
- Added README badges for PoC, read-only mode, candidate-only outputs, human review, no hardware control, Python, license, and CI.
- Added GitHub repository metadata guide (`docs/GITHUB_REPO_METADATA.md`).
- Added `ROADMAP.md` with current baseline, near/mid/long-term plans, and explicit non-goals.
- Added architecture documentation (`docs/ARCHITECTURE.md`), rebuilt from v3.0.8 baseline with Recovery Compiler boundary.
- Added documentation index (`docs/DOCS_INDEX.md`).
- Added GitHub launch notes (`docs/GITHUB_LAUNCH_NOTES.md`).
- Added GitHub Actions CI workflow (`.github/workflows/tests.yml`).
- Improved public demo script output: generates `output/public_demo/INDEX.md` after successful run.
- Improved first-run demo user experience (clear section headers, safety statement).
- Preserved GitHub public release readiness documentation from v3.0.7.
- Preserved SemFab confidence propagation from v3.0.6.
- Preserved Semiconductor Confidence Passport Exposure from v3.0.5.
- Preserved Semiconductor Confidence Missing Metrics patch from v3.0.4.
- Preserved Semiconductor Pilot Contract Alignment from v3.0.3.
- Preserved Recovery Compiler export and handoff manifest.
- Preserved Robot Pilot-Ready Pack strict validation.
- Preserved Functional Yield Essence metadata.
- Preserved default pytest / cli_e2e / release-heavy / installed-wheel / packaging marker stability.
- No Recovery Compiler execution, recovery profile generation, recipe control, tool control, hardware control, timing closure, autonomous recovery, root-cause certification, or yield guarantee features were added.

---
## v3.0.7 - GitHub Public Release Readiness + Pilot Demo Packaging Patch

- Rewrote README.md for GitHub public visibility: core question, what YieldOS is/isn't, domain pack table, 5-minute quickstart, standard output bundle reference, CLI reference, sample data paths, evidence compression ratio, testing, key docs table, limitations, license/citation.
- Added `docs/PUBLIC_SAFETY_BOUNDARY.md`: non-control guarantee, candidate-only outputs table, human-review-required section, domain-specific boundaries, forbidden claims list, enforcement table.
- Added `docs/GITHUB_RELEASE_CHECKLIST.md`: 12-section checklist for pre-release verification.
- Added `docs/DEMO_GUIDE.md`: 7 demo sections including semiconductor pilot-pack, robot pilot-pack, SemFab confidence explanation, FYFab seed; includes "what not to demo" section.
- Added `docs/PILOT_ONE_PAGER.md`: external-facing one-pager with problem statement, pilot domains (semiconductor + robot), safety boundary table, pilot success criteria.
- Added `docs/SAMPLE_OUTPUTS_GUIDE.md`: all 22 standard output files, semiconductor extra outputs, pilot-pack outputs, missing metrics explanation.
- Added `docs/REPOSITORY_MAP.md`: top-level structure and package layout reference.
- Added `CONTRIBUTING.md`: project boundary, welcome contributions, not-accepted list, PR guidelines.
- Added `SECURITY.md`: supported versions, vulnerability reporting, safety boundary warning, data handling.
- Added `CITATION.cff`: CFF 1.2.0 citation file with abstract, keywords, and preferred-citation block.
- Added `.github/ISSUE_TEMPLATE/` with bug_report.md, sample_data_request.md, documentation.md, config.yml.
- Added `.github/PULL_REQUEST_TEMPLATE.md` with safety boundary checklist.
- Added `.gitignore` excluding output/, dist/, build/, __pycache__/, .pytest_cache/, *.pyc, *.zip, .env, .venv/.
- Added `scripts/run_public_demo.py`: automated public demo runner (all 5 domains, semiconductor + robot pilot-packs, safety validation, recovery_profile.json absence check).
- No new analyzer features, no hardware control, recipe control, root-cause certification, or yield guarantee added.

---
## v3.0.6 - SemFab Confidence Passport/Report Writer Propagation Patch

- Propagated `confidence_explanation` to `functional_passport.json` in the general SemFab analyze flow (not just pilot-pack).
- Post-patched `report.html` and `report.md` with the semiconductor confidence section inside `write_all()` in `report_writer.py`, so all flows (demo, regular analyze, pilot-pack) produce consistent output.
- Removed redundant `confidence_explanation` patching from `cmd_semiconductor_pilot_pack` (write_all now handles it); pilot-pack retains only its pilot-specific `semiconductor_pilot_context` and export note patches.
- `semiconductor_confidence_report.json` confidence data is now the single source of truth consumed by both `functional_passport.json` and the HTML/MD report sections.
- No hardware control, recipe control, root-cause certification, or yield guarantee added.

---
## v3.0.5 - Semiconductor Confidence Passport Exposure + Summary Field Alignment Patch

- Added `confidence_explanation` as top-level key in semiconductor functional passports.
- Exposed `missing_metrics` and `missing_metric_messages` (e.g. `gas_flow_sccm: no data`) in functional passports.
- Aligned `available_metrics_summary` with explicit v3.0.5 field names: `available_metric_count`, `watched_metric_count`, `drift_candidate_count`, `stable_count`, `insufficient_data_count`, `drift_candidate_metrics`, `stable_metrics`, `insufficient_data_metrics`, `summary_text`.
- Preserved v3.0.4 compatibility fields (`total_watched`, `available_count`, `missing_count`, `available`, `missing`).
- Updated `summary_text` format: e.g. "1/3 available metrics show drift (pressure_mTorr); 2 watched metrics have no data (gas_flow_sccm, endpoint_signal)".
- Preserved existing drift detection behavior, confidence scoring, semiconductor pilot-pack, Recovery Compiler export, handoff manifest, and all existing strict validation.
- No hardware control, recipe control, root-cause certification, or yield guarantee added.

---
## v3.0.4 — Semiconductor Confidence Missing Metrics Message Patch

**Release Date**: 2026-07-03

### Summary
Adds human-readable missing_metrics and vailable_metrics_summary fields to the semiconductor
confidence report, so reviewers can see exactly which process metrics lacked sufficient data and why
confidence is lower than nominal.

### Changes
- _build_confidence_report() now returns missing_metrics (list of WATCHED_METRICs with
  INSUFFICIENT_DATA) and vailable_metrics_summary (counts, lists, and summary_text)
- semiconductor_confidence_report.json: confidence_report section now includes both new fields
- unctional_passport.json: semiconductor_analysis_context now includes confidence_explanation
  with missing_metrics and vailable_metrics_summary
- eport.html: New "Semiconductor Process Confidence" section shows per-metric availability
- eport.md: New "## 8. Semiconductor Confidence" section with metric table
- No change to _detect_recent_trend(), drift thresholds, or confidence scoring logic

### Invariants Preserved
- hardware_execution_enabled: false
- human_review_required: true
- causal_claim_boundary: "candidate_only_not_certified_cause"
- All existing test cases pass unchanged (2466+)

---
# HAL YieldOS Release Notes

---

## v3.0.3 - Semiconductor Pilot Contract Alignment + Handoff Export Hardening

- Added explicit `semiconductor_pilot_context` to semiconductor pilot functional passports.
- Added top-level decision boundary fields (`allowed_decisions`, `forbidden_decisions`, `hardware_control_enabled`, `human_review_required`) to semiconductor pilot decision readiness reports.
- Aligned semiconductor pilot state snapshot with candidate state contract (`snapshot_type`, `candidate_state`, `linked_reports`, enriched safety block).
- Aligned semiconductor pilot OODA frame with review-only contract (act as structured dict with `automatic_action_enabled`, `hardware_control_enabled`, `recipe_control_enabled` all false).
- Added `semiconductor_recovery_compiler_export.json` — candidate-only export artifact for offline HAL Recovery Compiler testing.
- Added `semiconductor_handoff_manifest.json` — explicit list of allowed/forbidden handoff files.
- Linked Recovery Compiler intake preview to the new export and handoff manifest.
- Linked Recovery Compiler handoff boundary to the new export and handoff manifest.
- Added strict validation checks for all new semiconductor pilot contract fields.
- Updated case_manifest checksums after post-patching standard outputs.
- Preserved Recovery Compiler boundary: YieldOS does not generate recovery profiles.
- Preserved Semiconductor Pilot-Ready Pack from v3.0.2.
- Preserved Robot Pilot-Ready Pack strict validation.
- Preserved Functional Yield Essence metadata.
- Preserved default pytest / cli_e2e / release-heavy / installed-wheel / packaging marker stability.
- No Recovery Compiler execution, recovery profile generation, recipe control, tool control, hardware control, timing closure, autonomous recovery, root-cause certification, or yield guarantee features were added.

---

## v3.0.2 - Semiconductor Pilot Standard Bundle + Version Hygiene + Strict Boundary Patch

- Fixed stale v3.0.0/v3.0.1 documentation references; all current-version docs now reference v3.0.2.
- Fixed packaging marker tests to read current version dynamically from VERSION file.
- Updated semiconductor pilot-pack to generate the full standard YieldOS case bundle (22+ files) alongside semiconductor-specific pilot outputs.
- Added missing `state_snapshot.json`, `evidence_pack.json`, `ooda_frame.json`, `report.html`, `functional_passport.json`, `decision_readiness_report.json`, `data_quality_report.json`, `case_manifest.json`, and `source_data_manifest.json` outputs for semiconductor pilot-pack.
- Semiconductor pilot-pack strict validation now passes.
- Patched strict boundary scanner to distinguish active forbidden claims from safe negative boundary contexts for both robot and semiconductor pilot-packs.
- Fixed robot pilot-pack strict false-positive caused by `yield_guarantee` inside `not_sufficient_for` boundary statement.
- Preserved Semiconductor Pilot-Ready Pack from v3.0.1 (all 11 pilot-specific outputs maintained).
- Preserved Recovery Compiler intake preview and handoff boundary.
- Preserved Robot Pilot-Ready Pack from v3.0.0.
- Preserved Pilot Readiness score semantics and Functional Yield Essence metadata.
- Preserved default pytest / cli_e2e / release-heavy / installed-wheel / packaging marker stability.
- No recipe control, tool control, hardware control, timing closure, Recovery Compiler execution, autonomous recovery, root-cause certification, or yield guarantee features were added.

---

## v3.0.1 - Semiconductor Pilot-Ready Pack + Recovery Compiler Intake Boundary

- **`yieldos semiconductor pilot-pack`** command: generates 11 semiconductor-specific JSON reports + 1 MD summary from a structured `samples/pilot_semiconductor/` input directory.
- **New module**: `yieldos/domains/semfab/pilot_pack.py` — core generator for all 11 reports.
- **11 new pilot-pack outputs** per run:
  - `semiconductor_evidence_completeness_report.json` — required/optional file completeness, evidence score (0.0-1.0).
  - `semiconductor_wafer_die_summary.json` — die-level pass/fail/bin summary with candidate remaining/blocked die lists.
  - `semiconductor_functional_region_map.json` — chip_tile / wafer_region / die-level candidate classification.
  - `semiconductor_role_candidate_map.json` — 8 canonical role → remaining/reduced/blocked mapping.
  - `semiconductor_valid_conditions_report.json` — per-role valid operating conditions with what_not_to_do.
  - `semiconductor_process_evidence_report.json` — candidate process signals and correlations (not root-cause).
  - `semiconductor_human_review_packet.json` — structured reviewer checklist with forbidden_decisions.
  - `semiconductor_missing_evidence_request.json` — evidence gaps with why_needed_for_functional_yield.
  - `semiconductor_recovery_compiler_intake_preview.json` — handoff_status: READY/PARTIAL/NOT_READY based on chip_tile_map + workload_roles + recovery_constraints. **Never generates `recovery_profile.json`.**
  - `semiconductor_recovery_compiler_handoff_boundary.json` — explicit boundary: what YieldOS does vs. what the Recovery Compiler does.
  - `semiconductor_pilot_readiness_report.json` — overall pilot-readiness gate (scored 0.0-1.0), `PILOT_READY` / `PARTIAL_PILOT_READY` / `NOT_PILOT_READY`.
  - `semiconductor_pilot_case_summary.md` — plain-language summary.
- **12 sample files** in `samples/pilot_semiconductor/` (tool_log.csv, metrology.csv, test_results.csv, wafer_map.csv, lot_genealogy.csv, chamber_log.csv, inspection_notes.csv, recipe_context_redacted.json, chip_tile_map.json, workload_roles.json, recovery_constraints.json, README.md).
- **Field alias mapping** (`yieldos/domains/semfab/field_aliases.py`): auto-detects and remaps legacy column names to canonical semiconductor columns.
- **Unit normalization** (`yieldos/domains/semfab/unit_normalization.py`): heuristic unit check per canonical column with normalization candidates.
- **Strict validation auto-detection**: `yieldos validate --strict` auto-checks semiconductor pilot-pack outputs when `semiconductor_pilot_readiness_report.json` is detected. Forbidden-term scanner patches negative context keys (`forbidden_decisions`, `what_not_to_do`, `yieldos_does_not`, etc.) to prevent false positives.
- **Recovery Compiler Intake Boundary**: `hardware_control_enabled: false` and `human_review_required: true` hardcoded on all 11 reports. `recovery_profile.json` is never generated.
- **16 new test files** (155+ test cases) covering all 11 reports, CLI integration, safety boundaries, field aliases, and unit normalization.
- **`docs/SEMICONDUCTOR_PILOT_READY.md`** added.
- No AI model, hardware control, recipe execution, autonomous recovery, physical design signoff, timing closure, yield guarantee, root-cause certification, or safety certification features were added.

---

## v3.0.0 - Robot Pilot-Ready Edition

- **`yieldos robot pilot-pack`** command: generates full Standard Output Bundle (22 files) + 9 robot-specific pilot-pack reports from a structured input directory.
- **New modules**: `yieldos/domains/robot/field_aliases.py` (canonical field mapping), `yieldos/domains/robot/unit_normalization.py` (unit preview).
- **New pilot-pack outputs** (9 files per run):
  - `robot_pilot_readiness_report.json` — overall pilot-readiness gate (scored 0.0-1.0).
  - `robot_evidence_completeness_report.json` — file/column/event completeness per slot.
  - `robot_role_reclassification_report.json` — canonical role → remaining/blocked mapping.
  - `robot_valid_conditions_report.json` — conditions under which remaining roles are valid.
  - `robot_human_review_packet.json` — structured reviewer checklist with priority items.
  - `robot_missing_evidence_request.json` — evidence gaps with why-needed-for-functional-yield.
  - `robot_pilot_case_summary.md` — plain-language pilot evidence summary.
  - `robot_field_mapping_report.json` (conditional) — field alias remapping report.
  - `robot_unit_normalization_report.json` — unit heuristic check per canonical column.
- **Enhanced `samples/pilot_robot/`**: 6 required CSVs, 20+ rows, 3 task IDs, slip/contact/intervention events.
- **Strict validation auto-detection**: `yieldos validate --strict` auto-checks pilot-pack outputs when `robot_pilot_readiness_report.json` is detected.
- **10 new test files** (35 test cases) covering CLI, output schemas, safety boundaries, field aliases, and unit normalization.
- **`docs/ROBOT_PILOT_READY.md`** added.
- Preserved all v2.9.5 release-heavy runtime optimizations.
- Preserved v2.9.4 outer release packaging hygiene.
- Preserved v2.9.3 Pilot Score semantics.
- No AI model, hardware control, recipe execution, autonomous recovery, physical design signoff, timing closure, yield guarantee, root-cause certification, or safety certification features were added.

---

## v2.9.5 - Release-Heavy Runtime Collapse Patch

- Collapsed release-heavy test runtime by building the release archive once per pytest session.
- Added shared `release_zip_path` session fixture in `tests/conftest.py` for release-heavy archive inspections.
- Updated release-heavy tests to reuse the same official release zip instead of rebuilding per test.
- Preserved root folder, manifest, checksum, and nested artifact hygiene checks.
- Preserved official release generation through `scripts/build_release.py`.
- Updated `docs/RELEASE_GUIDE.md` to document release-heavy runtime policy.
- Preserved outer release packaging hygiene from v2.9.4.
- Preserved Pilot Readiness score semantics from v2.9.3.
- Preserved canonical Pilot Readiness JSON schemas from v2.9.2.
- Preserved Functional Yield Essence metadata.
- Preserved semiconductor drift and confidence reports.
- Preserved default pytest / cli_e2e / installed-wheel / packaging marker stability.
- No AI model, hardware control, recipe execution, autonomous recovery, physical design signoff, timing closure, yield guarantee, root-cause certification, or safety certification features were added.

---

## v2.9.4 - Outer Release Packaging Hygiene Patch

- **Fixed outer release packaging hygiene**: official release zip generated only through `scripts/build_release.py`.
- **Release zip filename** now matches current version: `HAL-YieldOS-v2.9.4-poc-release.zip`.
- **Internal top-level release folder** now matches current version: `HAL-YieldOS-v2.9.4-poc-release/`.
  - Previously was `halyieldos/` (stale hardcode) — now derived dynamically from `VERSION`.
- **Final release zip hygiene scan** added to `build_release.py`: fails if stale artifacts, nested zips, or wrong root folder detected.
- **Old nested artifacts excluded**: `dist_v*/`, `output/`, `build/`, `dist/`, cache dirs, wheel files, and nested zip files.
- **CHECKSUMS.sha256** entries now use versioned release root prefix (`HAL-YieldOS-v2.9.4-poc-release/`).
- **MANIFEST.json** (release-generated) now includes `release_name` and `excluded_artifact_patterns` fields.
- **`--clean` flag** added to `build_release.py` to remove generated artifacts before build.
- **`--verify` flag** added to `build_release.py` to verify an existing zip's hygiene.
- **New test files** (`release_heavy` marker): `test_release_root_folder_name.py`, `test_release_no_nested_artifacts.py`, `test_release_manifest_checksum_exclusions.py`, `test_release_scan_function.py`.
- **`docs/RELEASE_GUIDE.md`** created with official packaging procedure.
- Preserved Pilot Readiness score semantics from v2.9.3.
- Preserved canonical Pilot Readiness JSON schemas from v2.9.2.
- Preserved Functional Yield Essence metadata.
- No AI model, hardware control, recipe execution, autonomous recovery, certification, or yield guarantee features added.

---

## v2.9.3 - Pilot Score Semantics + Pytest Warning Cleanup Patch

- **readiness_score_percent** added to `pilot_readiness_report.json` alongside `readiness_score`.
  - `readiness_score`: normalized 0.0–1.0 (unchanged).
  - `readiness_score_percent`: 0.0–100.0, always equals `round(readiness_score * 100, 2)`.
- **Score cap semantics** documented in `docs/PILOT_READINESS.md`:
  - Missing required file → score ≤ 0.70 (actual implementation: ≤ 0.40).
  - Missing required columns → score ≤ 0.60 (via INSUFFICIENT sufficiency_status).
  - MVR failure → score < 1.0 (proportional, not hard-capped).
- **Pytest warning cleanup**: removed `timeout` and `timeout_method` from `[tool.pytest.ini_options]` in `pyproject.toml`.
- **New test files**: `test_pilot_readiness_score_schema.py`, `test_pilot_readiness_score_caps.py`, `test_pilot_readiness_docs.py`.
- **docs/PILOT_READINESS.md** updated with "Readiness Score" section covering both fields and cap semantics table.
- No AI model, hardware control, recipe execution, autonomous recovery, certification, or yield guarantee features added.

---

## v2.9.2 - Pilot JSON Schema Strictness + Packaging Marker Patch

- **Canonical eadiness_status** added to pilot_readiness_report.json (primary field; status kept as compat alias).
- **Structured checks** in pilot_readiness_report.json: equired_files_present, equired_files_missing, optional_files_present, optional_files_missing, column_check, unit_check, minimum_viable_rows_check.
- **unctional_yield_readiness** block added (5 booleans: remaining, blocked, valid_conditions, evidence, human_review inputs ready).
- **sufficient_for / 
ot_sufficient_for** and hardware_control_enabled: false at top level of readiness report.
- **Canonical top-level sufficiency** in data_sufficiency_preview.json: sufficiency_status, sufficient_for, 
ot_sufficient_for, unctional_yield_gaps, claim_boundary.
- **Canonical missing arrays** in missing_data_request.json: missing_required_files, missing_required_columns, missing_units, minimum_viable_rows_failures, ecommended_optional_files, why_needed_for_functional_yield.
- **llowed_decisions / orbidden_decisions** added to pilot_decision_boundary.json; 8 required forbidden decisions enforced.
- **Missing-column strictness**: CSV files with missing required columns are now INSUFFICIENT (not SUFFICIENT) even when row count is high enough.
- **New test suite**: 	est_pilot_readiness_report_schema.py, 	est_pilot_data_sufficiency_preview_schema.py, 	est_pilot_missing_data_request_schema.py, 	est_pilot_decision_boundary_schema.py, 	est_pilot_readiness_semantics_strict.py, 	est_pilot_canonical_filenames.py.
- **Packaging marker smoke test** (	est_packaging_marker_smoke.py) — python -m pytest -m packaging now selects tests and returns exit code 0.
- **Pilot boundary docs** updated: docs/PILOT_READINESS.md reflects canonical v2.9.2 field names.
- Preserved all Functional Yield Essence metadata, Pilot canonical filenames from v2.9.1, semiconductor drift/confidence reports, robot external skill-demo, FYFab demo, default pytest stability.
- No AI model, hardware control, recipe execution, autonomous recovery, certification, or yield guarantee features added.

---
## v2.9.1 - Pilot Contract Naming + Readiness Semantics + Ruff Patch

- **Canonical pilot init output file names** (6 files):
  - `pilot_input_contract.json` (schema: `hal.yieldos.pilot.input_contract.v1`)
  - `sample_file_manifest.json` (new — per-file minimum_viable_rows and functional_yield_role)
  - `missing_data_request_template.json` (renamed from missing_data_request.json, new schema)
  - `sanitization_checklist.md` (Markdown, replaces sanitization_checklist.json as primary)
  - `pilot_boundary_statement.md` (Markdown, replaces boundary_statement.json as primary)
  - `README.md` (renamed from pilot_readme.md)
  - Old names retained as compatibility aliases.
- **Canonical pilot check output file names** (4 files):
  - `pilot_readiness_report.json` (schema: `hal.yieldos.pilot.readiness_report.v1`)
  - `missing_data_request.json` (new schema with `why_needed_for_functional_yield`)
  - `data_sufficiency_preview.json` (new — per-file `sufficiency_status`: SUFFICIENT/INSUFFICIENT/MISSING)
  - `pilot_decision_boundary.json` (new — safety boundary for this check run)
  - Old names retained as compatibility aliases.
- **Canonical readiness status values** (v2.9.1):
  - `READY_FOR_FUNCTIONAL_YIELD_PILOT`
  - `PARTIAL_FOR_FUNCTIONAL_YIELD_PILOT`
  - `NOT_READY_FOR_FUNCTIONAL_YIELD_PILOT`
  - `INVALID_INPUT`
  - Old values (`READY`, `PARTIAL`, `NOT_READY`) preserved in compat aliases with `status_v291` bridge key.
- **Per-file `minimum_viable_rows` enforcement**: files below threshold → INSUFFICIENT → blocking for required files.
- **Score capping**: if any required file is MISSING, score capped at ≤ 0.4.
- **Option A**: built-in sample data minimum_viable_rows set low enough that all 5 sample domains return `READY_FOR_FUNCTIONAL_YIELD_PILOT`.
- **`functional_yield_mapping`** now included in `pilot_readiness_report.json`.
- **`why_needed_for_functional_yield`** included in all `missing_data_request.json` items.
- **JSON dict row counting**: for JSON dict files, counts the largest nested array (e.g. `defect_map`, `roles`) as effective row count.
- **3 new test files** (247 new tests):
  - `tests/test_pilot_init_contract_names.py` — canonical init output names for all 5 domains
  - `tests/test_pilot_check_contract_names.py` — canonical check output names for all 5 domains
  - `tests/test_pilot_readiness_semantics.py` — READY/PARTIAL/NOT_READY/INVALID semantics + row count checks
- **7 ruff issues fixed** (auto-fixed by `ruff --fix`).
- No AI model, hardware control, recipe execution, autonomous recovery, physical design signoff,
  timing closure, yield guarantee, root-cause certification, or safety certification features added.
- Version bumped to 2.9.1.

---

## v2.9.0 - Functional Yield Pilot Readiness Pack

- Added `yieldos/pilot/` module: PilotContract system for pre-analysis input validation.
- Five domain pilot contracts: robot, semiconductor, space, memory, semiforge.
- New CLI namespace: `yieldos pilot init --domain <domain> --out <dir>`.
  - Generates 6-file Pilot Init Pack: pilot_contract.json, input_requirements.json,
    missing_data_request.json, sanitization_checklist.json, boundary_statement.json, pilot_readme.md.
- New CLI namespace: `yieldos pilot check --domain <domain> --input <dir> --out <dir>`.
  - Generates 4-file Readiness Report: readiness_report.json, data_sufficiency.json,
    blocking_issues.json, next_steps.json.
- Sample pilot data folders for all 5 domains: samples/pilot_robot/, pilot_semiconductor/,
  pilot_space/, pilot_memory/, pilot_semiforge/.
- 7 new test files (30+ tests): test_pilot_contracts.py, test_pilot_init.py, test_pilot_check.py,
  test_pilot_missing_data_request.py, test_pilot_sanitization.py, test_pilot_boundaries.py,
  test_pilot_cli.py.
- docs/PILOT_READINESS.md: Pilot launch guide for enterprise customers.
- docs/DEVELOPER_VALIDATION.md: Updated for v2.9.0 pilot validation commands.
- Pilot module enforces all YieldOS safety invariants:
  - read_only=True, automatic_decision_enabled=False, human_review_required=True.
  - Blocks: certified_root_cause, hardware_control_commands, automatic_recovery_execution.
- No AI model, hardware control, recipe execution, autonomous recovery, physical design signoff,
  timing closure, yield guarantee, root-cause certification, or safety certification features added.
- Version bumped to 2.9.0.

---

## v2.8.10 - CLI E2E Teardown + Product Memory Demo Isolation Patch

- Created `yieldos/product_memory_runner.py` with `run_product_memory_rebinning_demo_direct()`.
- `run_product_memory_rebinning_demo_direct()` mirrors `cmd_memory_product_demo()` without spawning a subprocess.
- Rewrote `tests/test_product_memory_rebinning_demo.py` to use `product_memory_out` module-scoped fixture (direct runner).
- Removed `cli_e2e` marker from `test_product_memory_rebinning_demo.py` — now in default core suite.
- Created `tests/test_product_memory_cli_smoke.py` with one minimal CLI subprocess smoke test.
- `cli_e2e` marker now contains smoke tests only.
- `python -m pytest -q -m cli_e2e` exits normally.
- `python -m pytest -q` default suite exits normally.
- Preserved all functional-yield checks from the original product memory demo test.
- Preserved Functional Yield Essence metadata (functional_yield_organizing_principle, data_sufficiency, functional_yield_lineage_summary, human_review_preparation).
- Preserved semiconductor drift and confidence reports.
- Preserved robot recent-weighted aggregation.
- Preserved SemiForge direct-parameter simulation.
- Preserved FYFab Seed.
- Preserved release zip hygiene, including `.pytest_tmp/` exclusion.
- No AI model, hardware control, recipe execution, autonomous recovery, physical design signoff, timing closure, yield guarantee, root-cause certification, or safety certification features were added.
- Version bumped to 2.8.10.

---

## v2.8.9 - Full Pytest Runtime Budget + Final Suite Gate Patch

- Split pytest suite into fast default core validation and release-heavy validation.
- Added pytest markers: `release_heavy`, `installed_wheel`, `packaging`, `cli_e2e`, `slow`.
- Updated `pyproject.toml` addopts to exclude heavy markers from the default suite.
- Applied `release_heavy` to: `test_release_hygiene.py`, `test_release_hygiene_excludes_pytest_tmp.py`.
- Applied `cli_e2e` to: `test_cli_smoke.py`, `test_product_memory_rebinning_demo.py`, `test_pytest_hang_regression.py`.
- Applied `installed_wheel` to: `test_installed_doctor_deep.py`.
- Default `python -m pytest -q` exits normally — final summary always printed.
- Release-heavy tests are not deleted — run with `python -m pytest -q -m release_heavy`.
- CLI e2e tests run with `python -m pytest -q -m cli_e2e`.
- Installed-wheel tests run with `python -m pytest -q -m installed_wheel`.
- Added `docs/DEVELOPER_VALIDATION.md` documenting the two-tier validation strategy.
- Preserved `.pytest_tmp/` release zip exclusion from v2.8.8.
- Preserved Functional Yield Essence metadata.
- Preserved semiconductor drift and confidence reports.
- Preserved robot recent-weighted aggregation.
- Preserved SemiForge direct-parameter simulation.
- Preserved FYFab Seed.
- No AI model, hardware control, recipe execution, autonomous recovery, physical design signoff, timing closure, yield guarantee, root-cause certification, or safety certification features were added.
- Version bumped to 2.8.9.

---

## v2.8.8 - CLI Subprocess Collapse + Release Hygiene Patch

- Created `yieldos/demo_runner.py` with `run_domain_demo_direct()` and `run_all_domain_demos_direct()`.
- CLI `cmd_demo` now delegates to `demo_runner.py` (same logic, no duplication).
- Tests use `all_demo_cases` (module-scoped fixture) or `demo_case_factory` instead of per-test CLI subprocess calls.
- Rewrote 5 test files to use fixtures: `test_data_sufficiency_embedded.py`, `test_functional_passport_essence_fields.py`, `test_functional_yield_lineage_summary.py`, `test_human_review_preparation.py`, `test_semiconductor_report_persistence.py`.
- Created `tests/test_cli_smoke.py` with minimal CLI subprocess smoke tests.
- Simplified `test_pytest_hang_regression.py` (semiconductor removed, moved to smoke).
- Fixed release hygiene: `.pytest_tmp/` added to `EXCLUDE_DIRS` in `scripts/build_release.py`.
- Added `.mypy_cache/`, `htmlcov/`, `.coverage` to exclusions.
- Added `tests/test_release_hygiene_excludes_pytest_tmp.py`.
- Preserved Functional Yield Essence metadata from v2.8.7.
- Preserved semiconductor drift and confidence reports.
- Preserved robot recent-weighted aggregation.
- Preserved SemiForge direct-parameter simulation.
- Preserved FYFab Seed.
- No AI model, hardware control, recipe execution, autonomous recovery, physical design signoff, timing closure, yield guarantee, root-cause certification, or safety certification features were added.
- Version bumped to 2.8.8.

---

## v2.8.7 - Functional Yield Essence Guard + Full-Suite Isolation Patch

- Embedded Functional Yield Essence metadata into 5 core output files:
  - `functional_yield_organizing_principle` in `functional_passport.json`
  - `data_sufficiency` in `data_quality_report.json`
  - `functional_yield_lineage_summary` in `case_manifest.json`
  - `human_review_preparation` in `decision_readiness_report.json`
  - `functional_yield_event_summary` in `analysis_trace.json`
- Added `docs/FUNCTIONAL_YIELD_ESSENCE.md` — design rule document.
- Updated `YIELDOS_IS_NOT_AI.md`: constitution expanded to 8 principles (added "Functional yield remains the organizing principle").
- Updated `SAFETY_BOUNDARY.md`: added Functional Yield Claim Boundary section.
- Updated `MARKET_POSITIONING.md`: added Functional Yield Organizing Principle section.
- Updated `README.md`: added v2.8.7 description, link to FUNCTIONAL_YIELD_ESSENCE.md.
- Added 6 new test files:
  - `test_functional_yield_essence.py` — doc existence and content guard
  - `test_functional_passport_essence_fields.py` — FYOP in all domains
  - `test_data_sufficiency_embedded.py` — data_sufficiency in all domains
  - `test_functional_yield_lineage_summary.py` — lineage_summary in all domains
  - `test_human_review_preparation.py` — human_review_preparation in all domains
  - `test_no_generic_platform_drift.py` — docs must not claim generic platform
- Added strict validation checks in `yieldos/cli/main.py` for all Essence fields (applies to all domains in `--strict` mode).
- Standard output bundle remains 22 files (no new files added).
- No new domains, no AI models, no hardware control, no recipe changes, no yield guarantee, no root-cause certification, no safety certification.
- Version bumped to 2.8.7.

---

## v2.8.6 - Full Pytest Termination Patch

- Fixed full-suite pytest termination behavior.
- Added `pytest-timeout>=2.0` as dev dependency with global `timeout = 120` and `timeout_method = "thread"` in `pyproject.toml`.
- Created `tests/helpers.py` with `run_yieldos_cli()` — a shared CLI subprocess helper with enforced `timeout` parameter (default 60 s).
- Consolidated all CLI subprocess calls in `test_product_memory_rebinning_demo.py`, `test_semiconductor_report_persistence.py`, and `test_pytest_hang_regression.py` to use `run_yieldos_cli()`.
- Added `_clear_yieldos_test_env` autouse fixture in `tests/conftest.py` to prevent environment-variable leakage between CLI tests.
- Eliminated all bare `subprocess.run()` calls from test files; subprocess calls now always go through `run_yieldos_cli()` with bounded timeouts.
- Updated `test_all_cli_timeouts_are_bounded` static check to verify no unguarded subprocess.run remains in the test suite.
- Improved test isolation: each test uses its own `tmp_path` or `tempfile.TemporaryDirectory()`.
- Preserved semiconductor `process_drift_report.json` persistence.
- Preserved semiconductor `semiconductor_confidence_report.json` persistence.
- Preserved robot recent-weighted aggregation.
- Preserved SemiForge direct-parameter simulation.
- Preserved FYFab Seed and Product Boundary documentation.
- Version bumped to 2.8.6.
- No AI model, hardware control, recipe execution, autonomous recovery, physical design signoff, timing closure, yield guarantee, root-cause certification, or safety certification features were added.

---

## v2.8.5 - Pytest Hang + Semiconductor Report Persistence Patch

- Fixed full-suite pytest hang by adding `timeout=120` to all CLI subprocess calls in `test_product_memory_rebinning_demo.py`.
- Added `tests/conftest.py` with autouse cleanup fixture for product-memory output directories.
- Added `tests/test_pytest_hang_regression.py` as a regression guard for CLI subprocess hang behavior.
- Persisted semiconductor `process_drift_report.json` as a release-grade output file.
- Persisted semiconductor `semiconductor_confidence_report.json` as a release-grade output file.
- Linked both semiconductor reports from `functional_passport.json` (`process_drift_report_ref`, `semiconductor_confidence_report_ref`).
- Added `semiconductor_analysis_context` block to `functional_passport.json` for semiconductor domain.
- Added `semiconductor_calibration_outputs` list to `analysis_trace.json` for semiconductor domain.
- Added `optional_outputs` section to `case_manifest.json` (all domain extra output files listed with sha256).
- Strengthened `validate --strict` to auto-detect and check semiconductor calibration outputs.
- Strict validation checks: safety_boundary, confidence_kind, passport refs, manifest optional_outputs, forbidden terms.
- Added `tests/test_semiconductor_report_persistence.py` (15 tests).
- Preserved robot recent-weighted aggregation and all existing robot tests.
- Preserved SemiForge direct-parameter simulation tests.
- Preserved FYFab Seed and Product Boundary documentation.
- Updated `MANIFEST.json` with semiconductor domain extra outputs.
- Version bumped to 2.8.5.
- No AI model, hardware control, recipe execution, autonomous recovery, physical design signoff, timing closure, yield guarantee, root-cause certification, or safety certification features were added.

---

## v2.8.4 - Analyzer Calibration + Confidence Semantics Patch

### Robot Analyzer — Recent-Weighted Mean
- Added `_col_recent_weighted_mean()` module-level function (recent_fraction=0.30, recent_weight=0.70).
- Health components (`motion_precision`, `thermal_margin`, `control_latency`, `power_stability`) now
  use recent-weighted mean instead of simple mean, preventing early normal readings from diluting
  late-stage degradation signals.
- Added `aggregation_method` metadata to `state.metrics` (kind, recent_fraction, recent_weight, note).

### Semiconductor Analyzer — Recent Trend Detection
- Added `_detect_recent_trend()` with DRIFT_CANDIDATE / STABLE_NORMAL / INSUFFICIENT_DATA statuses.
- Constants: `SEMICONDUCTOR_RECENT_TREND_FRACTION=0.30`, `SEMICONDUCTOR_RECENT_TREND_THRESHOLD=0.08`,
  `SEMICONDUCTOR_MIN_TREND_SAMPLES=8`.
- New `process_drift_report` field in `analyze()` output (schema: `yieldos.semfab.process_drift_report.v1`).

### Semiconductor Analyzer — Confidence Fix
- Fixed hardcoded `top_conf = 0.3` when no evidence objects found.
- Added `_build_confidence_report()` with data-driven scoring:
  - INSUFFICIENT_DATA → 0.30, PARTIAL_DATA → 0.45
  - SUFFICIENT + STABLE_NORMAL → 0.70, SUFFICIENT + DRIFT_CANDIDATE → 0.65
  - SUFFICIENT + CONFLICTING_SIGNALS → 0.50
- New `confidence_report` field in `analyze()` output (confidence_kind, score, data_status,
  signal_status, reasons, claim_boundary).

### SemiForge — Direct-Params Simulation
- Added `SemiForgeSimulationConfig` frozen dataclass for parameter validation.
- Added `run_semiforge_simulation_from_params()` convenience function (no config.json needed).
- Output includes `config_source = "direct_params"` and `array_size` fields.
- Existing `SemiForgeSimulator.simulate(config_path=...)` method unchanged.

### New Tests
- `tests/test_robot_recent_weighted_mean.py` (8 tests)
- `tests/test_semiconductor_recent_trend.py` (12 tests)
- `tests/test_semiconductor_confidence_semantics.py` (10 tests)
- `tests/test_semiforge_direct_params.py` (10 tests)

### Docs
- Updated all current-version references to v2.8.4.
- Added v2.8.4 calibration/confidence summary to README.
- FORBIDDEN_CURRENT_PHRASES extended with v2.8.3 stale zip entry.

---

## v2.8.3 - Final Docs Polish + Stable Baseline Lock

- Finalized v2.8.x documentation current-version consistency.
- Updated all current-version references to v2.8.3: KNOWN_LIMITATIONS, DELIVERY_GUIDE,
  TECHNICAL_SPEC, VALIDATION_METHOD, ANONYMIZATION_GUIDE, PILOT_PROPOSAL_TEMPLATE,
  ROBOT_DATA_SCHEMA, FUNCTIONAL_YIELD_FAB_SEED.
- Replaced version-specific future-interface notes ("does not exist in v2.8.1") with
  current-release-neutral language in FORGE_EXPORT_INTERFACE.md and PARTNER_AI_INTERFACE.md.
- Clarified historical feature introduction headings: removed version from heading,
  added "Introduced in v..." note below (KNOWN_LIMITATIONS, SAFETY_BOUNDARY, DOMAIN_PACKS, README).
- Added stable baseline statement to README: v2.8.3 locks the Product Boundary &
  FYFab Seed baseline.
- Added "Current stable baseline: HAL YieldOS v2.8.x" to ARCHITECTURE.md.
- Strengthened documentation consistency tests: dynamic CURRENT_VERSION detection,
  DOCS_REQUIRING_CURRENT_VERSION list, FORBIDDEN_CURRENT_PHRASES guard.
- Added future interface marking tests to test_product_boundary_terms.py.
- Preserved Product Boundary documentation: YieldOS is not an AI model.
- Preserved FYFab Seed simulation-only boundary.
- Preserved installed wheel `yieldos doctor --deep` support.
- No AI model, hardware control, recipe execution, autonomous recovery,
  physical design signoff, timing closure, yield guarantee, root-cause certification,
  or safety certification features were added.

---

## v2.8.2 - Docs Consistency + Test Robustness Patch

- Updated all stale current-version references in documentation to v2.8.2:
  `DELIVERY_GUIDE.md`, `TECHNICAL_SPEC.md`, `VALIDATION_METHOD.md`,
  `ANONYMIZATION_GUIDE.md`, `PILOT_PROPOSAL_TEMPLATE.md`, `ROBOT_DATA_SCHEMA.md`,
  `FUNCTIONAL_YIELD_FAB_SEED.md`.
- Fixed stale CLI reference in `VALIDATION_METHOD.md` and `DELIVERY_GUIDE.md`:
  `yieldos semiforge run` → `yieldos semiforge simulate`.
- Strengthened `tests/test_docs_version_consistency.py`:
  added yieldos/VERSION consistency check, 5-file version cross-check,
  stale-current-version pattern detection, and CLI alignment checks.
- Added new tests: `test_yieldos_version_file_is_282`, `test_yieldos_manifest_version_is_282`,
  `test_all_five_version_files_consistent`, `test_no_stale_current_version_in_docs`,
  `test_delivery_guide_cli_uses_simulate_not_run`, `test_validation_method_cli_uses_simulate`,
  `test_validation_method_no_stale_version_as_current`, `test_delivery_guide_no_old_zip_names`.
- Made installed-mode doctor version check robust: fallback to bundled VERSION then bundled
  MANIFEST.json when `importlib.metadata` is unavailable (non-editable-install environments).
- No new domain, no new analysis engine, no robot control, no hardware execution,
  no AI model, no Forge runtime dependency, no yield guarantee, no root-cause certification.

---

## v2.8.1 - Product Boundary & Hygiene Edition

- Clarified that HAL YieldOS is not an AI model.
- Repositioned YieldOS as an AI-ready Functional Yield Evidence Layer.
- Added `docs/YIELDOS_IS_NOT_AI.md` — full product boundary and constitution document.
- Added `docs/PARTNER_AI_INTERFACE.md` — partner AI integration guide (future interface).
- Added `docs/FORGE_EXPORT_INTERFACE.md` — Forge export interface guide (future interface).
- Updated `docs/MARKET_POSITIONING.md` with precise AI-ready positioning and forbidden terms.
- Added Japanese documentation: `docs/ja/ONE_PAGER.md`, `docs/ja/SAFETY_BOUNDARY.md`,
  `docs/ja/PARTNER_AI_INTEGRATION.md`.
- Added 4-layer product structure to README (Core Evidence Engine / Domain Packs /
  Partner AI Interface / Forge Export Interface).
- Updated standard output bundle documentation from 17 to 22 core files in README.
- Clarified manifest file count semantics: `file_count_kind`, `generated_release_files`,
  `checksummed_file_count`, `zip_entry_count` fields added.
- Updated `docs/FUNCTIONAL_YIELD_FAB_SEED.md` version reference and strengthened
  simulation-only boundary statement.
- Updated `docs/ARCHITECTURE.md` test suite reference to `500+`.
- Cleaned current-version references: docs now say v2.8.1 (historical notes preserved).
- Added tests: `test_product_boundary_terms.py`, `test_manifest_count_semantics.py`,
  `test_ja_docs.py`, `test_output_bundle_count.py`.
- No AI model, robot control, hardware execution, process recipe execution,
  physical design signoff, timing closure, yield guarantee, root-cause certification,
  or safety certification features were added.

---

## v2.8.0 - Functional Yield Fab Seed Edition

- Added FYFab Seed demo under Semiforge (`yieldos semiforge fyfab-demo --out <dir>`).
- Added simulated fabricated structure input package (`sample_data/fyfab_seed/`).
- Added defect map summary, usable cell classification, candidate functional regions,
  candidate reconfiguration map, and Functional Yield Chip Passport outputs.
- Added FYFab case study output (`fyfab_case_study.json`).
- Added FYFab strict validation and inspect-output support.
- Preserved read-only, simulation-only, candidate-only boundaries.
- No fabrication control, process recipe execution, physical design signoff,
  timing closure, yield guarantee, or root-cause certification features were added.

---

## v2.7.1 - Installed Doctor Deep Patch

- Fixed `yieldos doctor --deep` in installed wheel environments.
- Added bundled manifest support: `yieldos/MANIFEST.json` and `yieldos/VERSION` are now
  included as package data and verified by `doctor --deep` in installed mode.
- Doctor now distinguishes `source` vs `installed` runtime mode and prints it.
- Installed mode uses `importlib.metadata` for version and `importlib.resources` for bundled
  manifest/sample data — no longer requires root `pyproject.toml` or `MANIFEST.json`.
- Installed mode verifies: package version, bundled `standard_output_bundle` (22 files),
  5 domains, package sample_data, `external_robot_log_package`.
- Extracted doctor deep checks into `_run_deep_checks()` for testability.
- `scripts/build_release.py` now syncs `yieldos/MANIFEST.json` and `yieldos/VERSION`
  from root files before building the zip, ensuring consistency.
- Fixed build-release file scanner to include `yieldos/MANIFEST.json` and `yieldos/VERSION`
  (previously excluded by filename match, now only root-level files are excluded).
- Added `tests/test_installed_doctor_deep.py` with 6 bundled-manifest and installed-mode tests.
- Updated `pyproject.toml` package-data to include `yieldos/MANIFEST.json` and `yieldos/VERSION`.
- Preserved v2.7.0 Pilot-Ready Robot Pack functionality unchanged.
- No robot control, ROS command, automatic recovery, root-cause certification, or safety
  certification features were added.

---

## v2.7.0 - Pilot-Ready Robot Pack

- Added `yieldos robot import-check --input <folder> --out <folder>` CLI command.
- Added `robot_import_check_report.json` — schema-and-privacy readiness check for external robot log packages.
- Added `pilot_readiness_report.json` — candidate pilot readiness assessment (not production approval).
- Added `yieldos/sample_data/external_robot_log_package/` — 5-file synthetic demo package (robot_02, task_arm_motion_087).
- Added `yieldos/domains/robot/import_check.py` module with `run_import_check()`.
- Extended `yieldos robot skill-demo` with optional `--input <folder>` to accept external packages.
- Extended `inspect-output` to display import-check report summary when present in output folder.
- Added `docs/ROBOT_DATA_SCHEMA.md` — schema guide for external robot log packages.
- Added `docs/ANONYMIZATION_GUIDE.md` — privacy/anonymization guide for robot operator data.
- Added `docs/PILOT_PROPOSAL_TEMPLATE.md` — 6-section template for proposing a pilot.
- Updated `MANIFEST.json` `domain_extra_outputs` with `robot_import_check` outputs.
- Updated `skill_memory.py` schema version: `2.6.2` → `2.7.0`.
- Absolute boundaries unchanged: no robot control, no ROS commands, no hardware execution,
  no root-cause certification, no safety certification, no automatic recovery.

---

## v2.6.2 - Robot Skill Memory Case Study Edition

- Added `robot_skill_memory_case_study.json` — complete evidence chain narrative in one JSON.
- Added `robot_skill_memory_case_study.md` — human-readable case study for external review.
- Added `before_after_functional_reclassification.json` — baseline vs. YieldOS reclassification comparison.
- Linked `functional_passport.json` to the case study via `case_study_ref` and `before_after_ref`.
- Linked `ooda_frame.json` to the case study via `case_study_ref`.
- Added `optional_outputs` section to `case_manifest.json` for case study files.
- Improved `inspect-output` to display case study summary when present.
- Renamed root-cause boundary string: `human_observation_not_certified_root_cause` →
  `human_observation_no_root_cause_certification` (avoids forbidden substring collisions).
- Preserved read-only, candidate-only, human-review-only safety boundary throughout.
- No robot control, ROS command, automatic recovery, root-cause certification, or safety
  certification features were added.

---

## v2.6.1 - Physical Reality Gap Edition

### Extension: Robot Skill Memory — Physical Reality Gap

Extends `yieldos robot skill-demo` with two new read-only evidence artifacts:

- `sim_to_real_gap_report.json` — compares simulation expectations against real outcomes where the simulator predicted success but the robot failed. Schema: `hal.yieldos.robot.sim_to_real_gap_report.v1`
- `force_compliance_event_log.json` — logs observed force, torque, slip, and contact anomaly events. Schema: `hal.yieldos.robot.force_compliance_event_log.v1`

### New: Sample Data

Added `yieldos/sample_data/robot_skill_memory/sim_expectation.csv` — simulation expectation values (expected max torque, force, gripper margin) for `task_payload_transport_042`.

Updated `robot_telemetry.csv` to include `joint_position_error_mm` column.

### New: functional_passport extensions

Extends `functional_passport.json` with:
- `physical_reality_context` (sim_to_real_gap_observed, force_compliance_events_present, surface_condition_sensitive, payload_variation_sensitive, grip_slip_observed, contact_instability_observed, context_capture_status)
- `physical_context_boundary = "candidate_context_not_certification"`

`skill_to_evidence_map.json` mappings now include:
- `linked_force_event_refs` — references to force compliance events
- `linked_gap_event_refs` — references to sim-to-real gap events

### New: Strict validation extended

`yieldos validate --strict` now auto-detects Robot Skill Memory outputs and validates:
- Physical gap output files exist
- All gap events: `claim_boundary = candidate_only_sim_to_real_gap`
- All force events: `event_type` in allowed set, `claim_boundary = candidate_physical_event_only`
- `functional_passport.json` contains `physical_reality_context`
- `safety_boundary.hardware_execution_enabled = false` in all new outputs

### Candidate gap factors (enforced in code)

`payload_variation`, `floor_condition`, `surface_type`, `lighting_gap`,
`joint_torque_deviation`, `force_sensor_deviation`, `gripper_force_margin_low`,
`grip_slip`, `contact_instability`, `position_error_deviation`, `unknown_gap_factor`

### Allowed force event types (enforced in code)

`force_spike`, `torque_anomaly`, `slip_event`, `grip_failure_candidate`,
`contact_instability`, `excessive_payload_resistance`, `position_error_deviation`, `unknown_physical_event`

### Absolute prohibitions (unchanged)

```
no robot control / no ROS commands / no joint commands / no motion planning execution
no automatic recovery / no closed-loop control / no real-time control / no hardware command
no safety certification / no confirmed root cause claim
```

HAL does not replace skilled workers.
HAL preserves their field judgment as evidence-backed functional yield data.

---

## v2.6.0 - Robot Skill Memory MVP

### New: Robot Skill Memory Layer

Adds `yieldos robot skill-demo --out <dir>` CLI command.

Generates the standard 22-file output bundle via RobotAnalyzer, then additionally produces:
- `operator_skill_note.json` — structured operator and maintenance observations (schema: `hal.yieldos.robot.operator_skill_note.v1`)
- `human_intervention_timeline.json` — observed human intervention events (schema: `hal.yieldos.robot.human_intervention_timeline.v1`)
- `skill_to_evidence_map.json` — maps skill notes to sensor evidence (schema: `hal.yieldos.robot.skill_to_evidence_map.v1`)

Extends `functional_passport.json` with:
- `human_skill_context` (operator_note_present, maintenance_note_present, human_intervention_observed, skill_capture_status)
- `candidate_validity_conditions` — conditions for analysis relevance
- `advisory_not_to_do` — actions requiring qualified human review
- `validity_boundary = "candidate_context_not_certification"`
- `advisory_boundary = "advisory_human_review_only"`

### New: Sample Data

Added `yieldos/sample_data/robot_skill_memory/`:
- `robot_telemetry.csv` (30 rows: gripper slip scenario with human intervention)
- `operator_notes.csv` (3 operator observations)
- `maintenance_notes.csv` (2 maintenance observations)

### Safety Boundary (unchanged and enforced)

```
hardware_execution_enabled = false
human_review_required = true
candidate_only = true
read_only_shadow = true
```

Allowed intervention types (enforced in code):
`manual_stop_observed`, `manual_reset_observed`, `payload_removed_observed`,
`inspection_performed`, `maintenance_note_added`, `unknown_human_intervention`

Claim boundaries:
- Operator notes: `human_observation_not_certified_root_cause`
- Intervention events: `observed_intervention_not_yieldos_action`
- Evidence mappings: `candidate_only`

Absolute prohibitions preserved:
```
no auto repair / no robot control / no ROS commands / no closed-loop control
no safety certification claim / no confirmed root cause claim
no autonomous OODA control loop / no production decision automation
```

HAL does not replace skilled workers.
HAL preserves their field judgment as evidence-backed functional yield data.

### New: Docs

- `docs/DOMAIN_PACKS.md`: updated with Robot Skill Memory Layer section
- `docs/SAFETY_BOUNDARY.md`: extended with Robot Skill Memory boundary rules

### Tests

6 new tests in `tests/test_robot_skill_memory.py`:
- `test_robot_skill_memory_sample_exists`
- `test_robot_skill_demo_cli_runs`
- `test_robot_skill_demo_strict_validation`
- `test_robot_skill_functional_passport_has_skill_context`
- `test_robot_skill_safety_invariant`
- `test_robot_skill_source_manifest_includes_skill_files`

**Test count**: 459 passed, 2 skipped (optional SQBM)

---

## v2.5.3 - Release Polish

- Cleaned 55 lint issues with Ruff (unused imports, unsorted imports, unused variables, f-string without placeholders).
- Added `docs/KNOWN_LIMITATIONS.md` — explicit statement of what YieldOS does not do.
- Preserved all v2.5.2 pipeline coherence guarantees.
- Reconfirmed read-only, candidate-only, human-review-only safety boundary.
- No new control, execution, or certification features added.

**Test count**: 452 passed, 2 skipped (optional SQBM)

---

## v2.5.2

### Pipeline Coherence Patch

**P0 — Functional Passport case_id**
- `functional_passport.json`: added `case_id` field (was null/missing); now equals `state.case_id`
- `functional_passport.json`: added `evidence_pack_ref` (equals `evidence_pack.checksum`)

**P0 — Analysis Trace input_validation accuracy**
- `analysis_trace.json`: added top-level `input_validation` section mirroring `input_validation.json` status
- `analysis_trace.steps[0]` result now reflects actual `input_validation.json` status per domain (memory, semiconductor, semiforge use domain-specific record counts instead of `telemetry_samples`)

**P0 — Recovery Route Report embeds optimizer_info**
- `recovery_route_report.json`: added `optimizer_info` summary consistent with standalone `optimizer_info.json`
- `cli/main.py`: `_run_and_write()` now passes `optimizer_info_override` to `ReportWriter.write_all()`

**P0 — optimizer_info backend honesty**
- `optimizer_info.json`: added `backend_available` (bool) and `claim_boundary` (string)
- Both `OptimizerScheduler` and `SemiForgeSimulator._run_optimizer()` now emit these fields

**P0 — OODA Frame read-only identity**
- `ooda_frame.json`: added `ooda_mode="read_only_evidence_frame"`, `control_loop=false`, `hardware_action_enabled=false`, `human_review_required=true`
- `ooda_frame.json`: `evidence_pack_ref` is now always set to `evidence_pack.checksum`

**P1 — Pipeline coherence enhancements**
- `ooda_frame.json`: added `functional_yield_ref` (score + source pointer to `functional_yield_scorecard.json`)
- `recovery_candidates.json`: each candidate now has `route_membership` (rank, optimizer_used, fallback)
- `baseline_vs_yieldos.json`: memory domain now includes `capacity_breakdown_gb` from `memory_functional_capacity.json`
- `case_manifest.json`: added `cross_references` dict (key pipeline artifact → filename)
- `functional_passport.json`: `evidence_pack_ref` added (mirrors evidence_pack.checksum)

**Tests**
- New `tests/test_pipeline_coherence.py` (5 tests): passport case_id, analysis_trace iv mirror, optimizer_info fields, ooda_frame identity, cross-reference consistency

**Test count**: 451 passed, 2 skipped (optional SQBM)

---

## v2.5.1

### Release Integrity Patch

**P0 — Version hygiene**
- Version bump: 2.5.0 → 2.5.1
- `_get_version()` fallback changed from stale `"2.1.0"` to `"unknown"` (no more false version reporting when package is not installed)
- `MANIFEST.json` `created_at` updated to 2026-06-19

**P0 — Legacy script cleanup**
- `scripts/run_demo.py` replaced with a thin CLI wrapper (delegates to `yieldos demo --all`); no longer imports deleted domain modules
- `scripts/make_release_zip.py` disabled with `raise SystemExit` guard; use `scripts/build_release.py`

**P1 — `yieldos doctor --deep` release integrity checks**
- `--deep` flag added to `yieldos doctor` command
- Checks: VERSION/pyproject/MANIFEST version consistency, `standard_output_bundle` declared (22 files), sample data directories present, legacy artifacts absent (`run_demo.py` body removed, `make_release_zip.py` disabled)
- Prints PASS/WARN per check; exits non-zero if any check fails

**Test count**: 446 passed, 2 skipped (optional SQBM)

---

## v2.5.0

### Product Memory Rebinning Killer Demo

**New: Product demo sample and CLI command**

- `samples/product_memory_rebinning_demo/` — 128-block MLC NAND dataset (32 GB, 0.25 GB/block)
  - `block_health.csv`: 8 runtime_bad + 4 uncorrectable → 12 discard blocks; 16 approx_cache; 12 read_only_archive; 88 safe
  - `device_info.json`: NAND_DEMO_32GB_MLC with ECC/endurance/retention policy
  - `baseline_policy.json` (`hal.yieldos.demo.baseline_policy.v1`): binary pass/fail rules for comparison
  - `README.md`, `expected_outputs_summary.md`
- `yieldos/sample_data/product_memory_rebinning_demo/` — packaged copy used by CLI

**New CLI command: `yieldos memory product-demo --out <dir>`**

1. Loads `product_memory_rebinning_demo` sample data
2. Runs `MemoryAnalyzer` (functional_yield=0.6875, severity=medium)
3. Writes full Standard Output Bundle (25 files including memory extras)
4. Loads `baseline_policy.json` and enriches `baseline_vs_yieldos.json` with:
   - `baseline_policy_name`, `baseline_policy_rules`
   - `binary_verdict_detail` (explains runtime_bad trigger)
   - `recovered_functional_capacity_estimate` (safe/approx/read_only/discard breakdown)
   - `binary_policy_action_if_verdict_fail`
5. Updates `case_manifest.json` checksum after enrichment
6. Passes 59/59 strict validation

**Demo output:**
- `binary_policy_verdict: FAIL` — 12 discard blocks exceed max_runtime_bad_blocks=0
- `reclassification_occurred: true` — 88 safe blocks (22 GB) + 16 approx (4 GB) + 12 read_only (3 GB)
- `yieldos_functional_verdict: memory_bronze_cache_only`

**README.md updated** with Product Demo section and product-demo CLI command.

**New tests**: `tests/test_product_memory_rebinning_demo.py` (11 tests covering sample files, analyzer output, CLI command, enriched output, and strict validation)

**Test count**: 444 passed, 2 skipped (SQBM optional backend)

---

## v2.4.1

### Release Hygiene and CLI Consistency

**Packaging**
- Release zip now excludes `build/` directory (previously leaked compiled artifacts)
- `EXCLUDE_EXTS` expanded to also exclude `.whl` and `.tar.gz` from zip
- `scripts/make_release_zip.py` deprecated — use `scripts/build_release.py` for all builds

**Unified CLI — memory domain**
- `yieldos analyze --domain memory --input <dir> --out <dir>` now works (previously required `yieldos memory analyze`)
- Domain aliases added: `memory_device` → `memory`, `nand` → `memory`
- `yieldos run --domain memory` supported

**Documentation consistency**
- All docs updated to reflect 5 domains (was "4 domain demos" in some places)
- All version references updated to v2.4.1
- `docs/DELIVERY_GUIDE.md` updated with correct demo output paths and test counts
- `docs/VALIDATION_METHOD.md` updated with 5-domain table and 57-check validation count
- `docs/MARKET_POSITIONING.md` added

**Test suite**
- `tests/test_cli_unified_memory.py` — verifies `analyze --domain memory` end-to-end
- `tests/test_release_hygiene.py` — verifies zip excludes build/, dist/, stale artifacts
- `tests/test_docs_version_consistency.py` — verifies docs don't reference stale versions

**Test count**: 393 passed, 2 skipped (SQBM optional backend)

### Evidence Traceability (Task Pack 2)

**source_data_manifest.json — real input file metadata**
- `exists`, `sha256`, `byte_size`, `file_kind`, `rows`, `columns` (header list) per file
- Non-existing files recorded with `exists=false` and `warning` field
- `claim_boundary: input_hash_traceability_only` added
- `domain_adapter` field added
- Path stored as basename (not full absolute path)

**source_data_paths wired for all domains**
- Robot: telemetry CSV + optional maintenance/operation/environment logs
- Space: telemetry CSV + optional mission_profile.json
- Semiconductor: tool_log.csv, wafer_map.csv, metrology.csv, test_result.csv, lot_genealogy.csv
- SemiForge: config.json
- Memory: block_health.csv, device_info.json
- Demo command (`yieldos demo --all`) now also passes source_data_paths

**case_manifest.json — complete file coverage**
- Now covers ALL written output files (was hardcoded subset of 14)
- Includes: input_validation, functional_yield_scorecard, functional_binning_result, ooda_frame, recovery_candidates, report.md, evidence_pack.md, source_data_manifest, data_quality_report, evidence_conflict_report, baseline_vs_yieldos, business_case_summary, domain extras
- `file_count` field added to manifest root
- `byte_size` added per-file entry

**Strict validation — manifest completeness checks**
- New: all manifest-listed files must exist on disk
- New: case_manifest must cover all 21 standard output keys
- Strict validation now reports 59 checks per domain (was 57)

**Semiconductor blocked_roles**
- `blocked_roles` now populated: `certified_root_cause`, `recipe_change`, `automatic_lot_hold`, `equipment_control`, `process_parameter_update`, `production_disposition`
- `remaining_roles` expanded to 6: adds `drift_investigation_support`, `yield_loss_triage`, `cross_step_correlation_review`

**New tests**: `tests/test_source_data_manifest.py` (10), `tests/test_case_manifest_completeness.py` (13), `tests/test_semiconductor_blocked_roles.py` (17)

**Test count**: 433 passed, 2 skipped (SQBM optional backend)

---

## v2.4.0

### Functional Passport Edition

- **Functional Passport v2** (`hal.yieldos.functional_passport.v2`): adds `passport_validity`, `approval_gate`, `evidence_strength`, `required_human_roles`, `role_confidence`
- **5 new standard output files**: `source_data_manifest.json`, `data_quality_report.json`, `evidence_conflict_report.json`, `baseline_vs_yieldos.json`, `business_case_summary.json`
- **Decision Readiness Inputs**: `--cvc`, `--authority`, `--envelope`, `--risk-policy` CLI flags on all domain subcommands
- **SAFE_ACTION_PREFIXES** corrected: `schedule_` and `flag_` moved to `FORBIDDEN_ACTION_PREFIXES`; safe prefixes are `recommend_`, `request_`, `suggest_`, `prepare_`, `simulate_`, `draft_`
- `docs/TECHNICAL_SPEC.md`, `docs/DOMAIN_PACKS.md`, `docs/MARKET_POSITIONING.md` added
- Standard Output Bundle expanded to 22 files
- Test count: 340 passed, 2 skipped

---

## v2.3.0

### Memory Functional Yield Domain

New domain `memory` analyzes NAND flash block health to estimate functional capacity.
HAL YieldOS **never** modifies firmware, remaps blocks, executes TRIM/secure-erase, or certifies data integrity.
All outputs are candidate recommendations for human review only.

**Inputs:**
- `block_health.csv` — per-block ECC, endurance, retention, temperature telemetry
- `device_info.json` — raw capacity, ECC thresholds, PE-cycle limits, retention policy

**Outputs (added to Standard Output Bundle):**
- `memory_functional_capacity.json` — safe/at-risk/archive/discard capacity breakdown, functional yield
- `memory_data_placement_recommendation.json` — 3-zone placement guidance (high_reliability / approximate_ai_cache / read_only_archive)
- `memory_bad_block_evidence_map.json` — bad blocks, at-risk blocks, ECC evidence

**Block classification (priority order):** discard > read_only_archive | approximate_cache > at_risk > safe

**Functional Passport tiers by FY:**
- ≥ 0.90 → `memory_gold_candidate`
- ≥ 0.70 → `memory_silver_candidate`
- ≥ 0.45 → `memory_bronze_candidate`
- < 0.45 → `memory_discard_review`

**CLI:**
```bash
yieldos memory analyze --input samples/memory_device --out output/memory --asset memdev_01
yieldos memory gen --out samples/memory_large --blocks 1024
yieldos demo --all --out output/demo_all_v230   # includes memory
```

**Sample data:** `samples/memory_device/` — 128-block NAND flash synthetic dataset

### SemiForge Formula Fix (r_alg double-counting)

`compute_r_alg` previously multiplied `(recovered/baseline) * r_conn`, then `compute_y_func`
multiplied by `r_conn` again — squaring its contribution. Fixed:

```python
# v2.3.0 — r_conn applied once only in y_func
r_alg = compute_r_alg(baseline_accuracy, damaged_accuracy, recovered_accuracy)
y_func = compute_y_func(r_conn, r_alg)  # = r_conn * r_alg
```

`compute_r_alg` signature changed to 3 args (dropped `r_conn`). Existing sweep and simulator callers updated.

### Validation

Strict validation updated: 54-point check (was 53) — added memory-domain recovery route prefixes.

### Test Suite

308 passed, 2 skipped (was 211 passed v2.1.0 → 296 passed v2.2.0 → 308 passed v2.3.0)

15 new tests in `tests/test_memory_domain.py` covering: synthetic generator, analyzer domain,
capacity accounting, evidence objects, passport roles, CLI analyze, strict validate, case manifest.

---

## v2.2.0

### Standard Output Bundle — v2 Extensions

Added `state_snapshot_hash` field to `evidence_pack.json` checksum payload for tamper-proof
cross-file integrity linking. All prior outputs remain compatible; `state_snapshot_hash` defaults
to `""` for backward-compatible seal verification.

### Regression Fixes

- `test_checksum_includes_causal_boundary` — test payload now includes `state_snapshot_hash`
- `test_cd_correlation_detected` — sweep metrology now generates ≥ `MIN_SUPPORT` rows per lot

---

## v2.1.0

### Standard Output Bundle

Every domain analysis now produces a 17-file Standard Output Bundle:
- `state_snapshot.json`, `evidence_pack.json`, `ooda_frame.json`, `recovery_candidates.json`
- `report.md`, `report.html`
- `input_validation.json`, `decision_readiness_report.json`
- `functional_yield_scorecard.json`, `functional_binning_result.json`
- `functional_passport.json`, `evidence_pack.md`
- `recovery_route_report.json`, `failure_scenario_record.json`
- `next_data_request.json`, `analysis_trace.json`, `case_manifest.json`

### Functional Passport

Each case now includes a `functional_passport.json` that describes:
- `remaining_roles` — what the asset can still do
- `blocked_roles` — what the asset cannot safely do
- `bin_class` — functional bin classification
- `decision_readiness` — readiness category (ACTION_INELIGIBLE / PASSPORT_ELIGIBLE / DECISION_READY / etc.)

### Strict Validation (`yieldos validate --strict`)

53-point strict validation covering:
- All 17 Standard Output Bundle files present
- Case manifest file checksums match
- Safety action prefix enforcement (SAFE_ACTION_PREFIXES)
- No dangerous execution terms in recovery candidates
- Functional passport safety fields
- Decision readiness category validity
- Analysis trace presence

### Domain Alias Stabilization

Canonical domains: `robot`, `space`, `semiconductor`, `semiforge`

Supported aliases:
- `satellite` → `space`
- `satguard` → `space`
- `sat` → `space`
- `semfab` → `semiconductor`
- `edge_ai` → `semiconductor`
- `dark_cell` → `semiforge`

### Unified Demo Command

Primary product demo path is now `yieldos demo`:
```bash
yieldos demo --all --out output/demo_all
yieldos demo --demo-domain robot --out output/demo_robot
```

### Safety Action Boundary (P0-1)

All `RecoveryCandidate` actions must start with a safe prefix:
`recommend_`, `request_`, `suggest_`, `prepare_`, `simulate_`, `draft_`
(Note: `schedule_` and `flag_` were later moved to FORBIDDEN_ACTION_PREFIXES in v2.4.0)

Dangerous execution terms are blocked in all recovery candidate text.

### No Live Control (unchanged, strengthened)

- `hardware_execution_enabled = false` — enforced in all outputs and validation
- `causal_claim_boundary = candidate_only_not_certified_cause` — enforced
- `requires_human_review = true` — enforced

---

## What Is NOT Included

- Live hardware control of any kind
- Certified root-cause determination
- Real fab, robot fleet, satellite, or memory device validation
- Production-grade false-positive / false-negative benchmarks
- SQLite registry (future roadmap)
- FY-Bench Lite (future roadmap)
- Design Partner mode (future roadmap)
- Distributed queue / Celery backend (future)
- Ed25519 block signing (future)

## Installation

```bash
pip install hal-yieldos
# or from source:
pip install -e .

yieldos version
yieldos doctor
yieldos demo --all --out output/demo_all
yieldos validate --case output/demo_all/robot --strict
yieldos memory analyze --input samples/memory_device --out output/memory --asset memdev_01
yieldos validate --case output/memory --strict
```

## What's Included

- **Standalone CLI** (`yieldos` command)
- **Domain 1 — Robot** (`robot`): OODA-loop evidence analysis of robot arm telemetry
- **Domain 2 — Space** (`space`): Subsystem health evidence analysis from satellite telemetry
- **Domain 3 — Semiconductor** (`semiconductor`): Shadow analysis of tool logs, metrology, wafer maps
- **Domain 4 — SemiForge** (`semiforge`): Functional yield simulation for crossbar compute arrays
- **Domain 5 — Memory** (`memory`): NAND flash block health → functional capacity estimation
- **Standard Output Bundle** — 17+ structured JSON/MD/HTML files per case
- **Functional Passport** — remaining/blocked roles, bin class, decision readiness
- **Strict validation** — 54-point case integrity check
- **SQBM optional optimizer backend** with greedy fallback
- **Synthetic data generators** for all 5 domains
- **Experience Graph** (append-only outcome ledger)
- **SemiForge sweep** (defect rate sensitivity analysis with corrected r_alg formula)
