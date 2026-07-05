# HAL YieldOS — Domain Packs

Five domain packs are included. Each operates in shadow-only mode.

## robot

**Adapter**: `robotics`  
**Input**: `robot_telemetry.csv` (joint positions, velocities, error rates, torque)  
**Required human roles**: maintenance_engineer, operations_manager  
**Valid conditions**: same robot configuration, same payload class, same operating envelope

Identifies remaining roles: low_speed_operation_candidate, inspection_only_mode, remote_supervised_mode, background_monitoring.

## space

**Adapter**: `satellite`  
**Input**: `satellite_telemetry.csv` (power, thermal, attitude, comms SNR)  
**Required human roles**: ground_operations_engineer, mission_manager  
**Valid conditions**: same mission profile, same power budget assumption, no new fault flag after analysis

Identifies remaining roles: safe_hold_eligible, minimal_comms_candidate, beacon_only_mode, reduced_payload_operation.

## semiconductor

**Adapter**: `semiconductor_fab`  
**Input**: directory with `tool_log.csv`, `wafer_yield.csv`, `metrology.csv`  
**Required human roles**: process_engineer, quality_manager  
**Valid conditions**: same lot context, same tool log window, no recipe change inferred or applied

Identifies process drift evidence and wafer-level functional impact for targeted lot disposition.

## semiforge

**Adapter**: `semiforge_crossbar`  
**Input**: `config.json` (array geometry, defect rate, distribution model)  
**Required human roles**: device_physicist, yield_engineer  
**Valid conditions**: same simulation config, same defect distribution model, no new measurement-based defect map

Reclassifies dark functional cells in crossbar arrays using Monte Carlo percolation analysis.

## memory

**Adapter**: `memory_device`  
**Input**: directory with `block_health.csv` and `device_info.json`  
**Required human roles**: storage_engineer, quality_manager  
**Valid conditions**: same device health snapshot, no new uncorrectable error event, same ECC policy assumption

Identifies functional blocks, ECC health, endurance headroom, and capacity recovery potential.

---

## Robot Skill Memory Layer (v2.6.0)

**CLI**: `yieldos robot skill-demo --out <dir>`  
**Inputs**: `robot_telemetry.csv`, `operator_notes.csv`, `maintenance_notes.csv`  
**Additional outputs**: `operator_skill_note.json`, `human_intervention_timeline.json`, `skill_to_evidence_map.json`

Extends the `robot` domain pack by capturing skilled worker observations as Functional Yield evidence.
Extends `functional_passport.json` with `human_skill_context`, `candidate_validity_conditions`,
`advisory_not_to_do`, `validity_boundary = "candidate_context_not_certification"`.

**Allowed intervention types**: `manual_stop_observed`, `manual_reset_observed`, `payload_removed_observed`,
`inspection_performed`, `maintenance_note_added`, `unknown_human_intervention`

**Claim boundaries**:
- Operator notes: `human_observation_no_root_cause_certification`
- Intervention events: `observed_intervention_not_yieldos_action`
- Evidence mappings: `candidate_only`

HAL does not replace skilled workers.
HAL preserves their field judgment as evidence-backed functional yield data.

---

## Physical Reality Gap (v2.6.1)

**CLI**: `yieldos robot skill-demo --out <dir>` (included automatically)  
**Additional inputs**: `sim_expectation.csv` (simulation expectations per task)  
**Additional outputs**: `sim_to_real_gap_report.json`, `force_compliance_event_log.json`

Extends Robot Skill Memory by comparing simulation expectations against real failure outcomes.

**sim_to_real_gap_report.json** (schema: `hal.yieldos.robot.sim_to_real_gap_report.v1`):
- Identifies tasks where simulation predicted success but real outcome was failure
- Lists candidate gap factors for each event
- `claim_boundary = "candidate_only_sim_to_real_gap"` on each event

**force_compliance_event_log.json** (schema: `hal.yieldos.robot.force_compliance_event_log.v1`):
- Logs observed torque anomalies, force spikes, slip events, and contact instability events
- Compares observed vs. simulation-expected thresholds
- `claim_boundary = "candidate_physical_event_only"` on each event

**Allowed candidate gap factors**: `payload_variation`, `floor_condition`, `surface_type`,
`lighting_gap`, `joint_torque_deviation`, `force_sensor_deviation`, `gripper_force_margin_low`,
`grip_slip`, `contact_instability`, `position_error_deviation`, `unknown_gap_factor`

**Allowed force event types**: `force_spike`, `torque_anomaly`, `slip_event`,
`grip_failure_candidate`, `contact_instability`, `excessive_payload_resistance`,
`position_error_deviation`, `unknown_physical_event`

**Safety invariants (unchanged)**:
- `hardware_execution_enabled = false`
- `human_review_required = true`
- `candidate_only = true`
- No robot control / no ROS commands / no confirmed root cause / no safety certification

---

## Robot Skill Memory Case Study (v2.6.2)

**CLI**: `yieldos robot skill-demo --out <dir>` (included automatically)  
**Additional outputs**: `robot_skill_memory_case_study.json`, `robot_skill_memory_case_study.md`,
`before_after_functional_reclassification.json`

The case study output summarizes a complete evidence chain:

simulation expectation → real-world failure → operator observation → physical event evidence →
human intervention → functional reclassification.

It is intended for human review, technical discussion, and pilot planning.

It is not a control report, safety qualification, or root-cause certification.

**Linked files**:
- `functional_passport.json` → `case_study_ref`, `before_after_ref`
- `ooda_frame.json` → `case_study_ref`
- `case_manifest.json` → `optional_outputs` section

---

## Pilot-Ready Robot Pack

Introduced in v2.7.0.

**CLI**: `yieldos robot import-check --input <folder> --out <dir>`  
**Optional**: `yieldos robot skill-demo --input <folder> --out <dir>`

Validates external robot log packages before analysis.

**New outputs**:
- `robot_import_check_report.json` — schema and privacy readiness check
- `pilot_readiness_report.json` — candidate pilot readiness assessment

**Schema**: `hal.yieldos.robot.import_check_report.v1`, `hal.yieldos.robot.pilot_readiness_report.v1`

**Claim boundary**: `pilot_readiness_not_production_approval`

**Safety boundary**:
- `hardware_execution_enabled = false`
- `human_review_required = true`
- `candidate_only = true`
- No analysis is performed during import-check
- No robot commands are issued
- `READY` status means structurally ready for analysis, not cleared for production

**New docs**:
- `docs/ROBOT_DATA_SCHEMA.md` — CSV schema guide
- `docs/ANONYMIZATION_GUIDE.md` — privacy guide
- `docs/PILOT_PROPOSAL_TEMPLATE.md` — 6-section pilot proposal template

---

## FYFab Seed

Introduced in v2.8.0.

**CLI**: `yieldos semiforge fyfab-demo --out <dir>`

A simulation-only pipeline that interprets an imperfect simulated fabricated structure
and generates candidate functional yield evidence.

**Input files** (from `sample_data/fyfab_seed/`):
- `fabricated_structure_grid.csv` — 128-cell synthetic substrate grid
- `defect_map.csv` — 18 observed candidate defects
- `material_regions.csv` — 4 material regions with candidate use roles
- `target_function_blocks.json` — 2 target functional blocks to map

**FYFab-specific outputs**:
- `fabricated_structure_map.json` — grid summary
- `defect_map_summary.json` — defect distribution
- `usable_cell_classification.json` — per-cell candidate roles
- `candidate_functional_regions.json` — grouped usable-cell regions
- `reconfiguration_candidate_map.json` — candidate mappings to target blocks
- `functional_yield_chip_passport.json` — chip-level functional passport
- `fyfab_case_study.json` — pipeline narrative

**Not claimed**:
- No real fabrication control
- No physical design signoff
- No timing closure
- No yield guarantee
- No process recipe execution

See `docs/FUNCTIONAL_YIELD_FAB_SEED.md` for full documentation.

---

> All domain packs: read-only, shadow analysis, candidate-only output, human review required.
