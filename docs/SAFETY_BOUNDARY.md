# HAL YieldOS — Safety Boundary Specification

## Core Principle

YieldOS is a **read-only shadow system**. It observes data. It never acts on hardware.

```
read-only
shadow-only
candidate-only RCA
recommendation-only recovery
no live hardware control
human review required before any operational action
```

---

## System-Level Safety Invariants

These invariants are enforced in code and cannot be overridden:

| Invariant | Enforced Value |
|-----------|----------------|
| `StateSnapshot.mode` | `read_only_shadow` |
| `EvidencePack.causal_claim_boundary` | `candidate_only_not_certified_cause` |
| `OODAFrame.act` | `recommendation_only_no_hardware_action` |
| `RecoveryCandidate.hardware_execution_enabled` | `false` |
| `RecoveryCandidate.execution_mode` | `recommendation_only` or `human_review_required` |
| `RecoveryCandidate.requires_human_review` | `true` |
| `RootCauseCandidate.claim_boundary` | `candidate_only` |

Attempting to create any object with these values overridden raises `ValueError` at construction time.

---

## Domain-Level Prohibitions

### Semiconductor Fab (semfab)

YieldOS MUST NOT:
- Modify process recipes
- Send equipment start/stop commands
- Adjust APC (Advanced Process Control) setpoints
- Modify lot dispositions in MES without human approval
- Certify root cause of yield loss

YieldOS MUST ONLY:
- Read tool logs, wafer maps, metrology, test results
- Detect statistical drift
- Produce ranked root cause candidates
- Request missing evidence from engineers

### Defect-Tolerant Computing (semiforge)

YieldOS MUST NOT:
- Execute real crossbar writes
- Reconfigure hardware routing tables
- Modify firmware parameters

YieldOS MUST ONLY:
- Run offline Monte Carlo simulations on supplied config
- Report functional yield estimates
- Produce defect pattern analysis

### Robot Telemetry (robot)

YieldOS MUST NOT:
- Send ROS commands
- Send torque or velocity commands
- Trigger calibration sequences
- Adjust PID parameters
- Initiate any motion

YieldOS MUST ONLY:
- Read telemetry CSV files
- Detect rising trends and fault codes
- Produce state snapshot and recovery candidates for human review

### Robot Skill Memory (v2.6.0)

YieldOS MUST NOT:
- Certify operator observations as root cause
- Issue any action based on operator notes alone
- Store personally identifiable information (PII) — all notes are pre-redacted
- Classify intervention_type outside the allowed set
- Use operator note confidence as a certified safety decision

YieldOS MUST ONLY:
- Preserve operator observations as `human_observation_no_root_cause_certification` evidence
- Record observed human interventions with `observed_intervention_not_yieldos_action`
- Map observations to sensor evidence with `candidate_only` claim boundary
- Extend functional_passport with `validity_boundary = "candidate_context_not_certification"`

Allowed intervention types (enforced in code):
- `manual_stop_observed`, `manual_reset_observed`, `payload_removed_observed`
- `inspection_performed`, `maintenance_note_added`, `unknown_human_intervention`

### Physical Reality Gap (v2.6.1)

YieldOS MUST NOT:
- Issue ROS commands based on gap analysis
- Automatically trigger recovery from force/torque deviation
- Certify gap factor as root cause of failure
- Claim simulation expectations as ground truth
- Execute any control action to close the sim-to-real gap

YieldOS MUST ONLY:
- Compare observed telemetry to simulation expectations in read-only mode
- Record observed force/torque/slip events with `candidate_physical_event_only` boundary
- Report sim-to-real gap candidates with `candidate_only_sim_to_real_gap` boundary
- Extend functional_passport with `physical_context_boundary = "candidate_context_not_certification"`

Allowed gap factors (enforced in code):
`payload_variation`, `floor_condition`, `surface_type`, `lighting_gap`,
`joint_torque_deviation`, `force_sensor_deviation`, `gripper_force_margin_low`,
`grip_slip`, `contact_instability`, `position_error_deviation`, `unknown_gap_factor`

Allowed force event types (enforced in code):
`force_spike`, `torque_anomaly`, `slip_event`, `grip_failure_candidate`,
`contact_instability`, `excessive_payload_resistance`, `position_error_deviation`, `unknown_physical_event`

### Satellite Telemetry (satellite)

YieldOS MUST NOT:
- Send uplink commands
- Switch operational modes
- Command payload instruments
- Trigger attitude maneuvers
- Issue any command to the spacecraft

YieldOS MUST ONLY:
- Read telemetry CSV files
- Detect threshold breaches and fault flags
- Compute mission readiness estimate
- Produce recovery candidates for ground team review

---

## Verification Protocol

Every output case can be validated with:

```bash
yieldos validate --case <output_dir>
```

The validator checks:
1. `evidence_pack.json` checksum integrity (SHA-256)
2. `causal_claim_boundary = candidate_only_not_certified_cause`
3. `mode = read_only_shadow`
4. `act` field contains no hardware command
5. `hardware_execution_enabled = false` in all recovery candidates
6. All required output files exist

---

## What "Candidate" Means

A root cause **candidate** is not a confirmed root cause. It is:
- A hypothesis supported by available evidence
- Ranked by confidence, not certainty
- Subject to engineer verification
- Incomplete without missing evidence items

YieldOS never uses the word "confirmed", "certified", or "proven" in root cause outputs.

---

## Human Review Gate

All recovery candidates carry `requires_human_review = true`. This means:

1. An engineer must read the evidence pack
2. An engineer must evaluate the root cause candidates
3. An engineer must decide whether to act on any recovery candidate
4. YieldOS never autonomously executes a recovery action

There is no bypass for this gate in YieldOS v1.

---

### Case Study Boundary (v2.6.2)

Case study outputs are narrative summaries of evidence.

They do not authorize action.
They do not control hardware.
They do not certify safety.
They do not certify root cause.

---

### Import Check Boundary

Introduced in v2.7.0.

Import-check is a structural and heuristic privacy check only.

- `schema_status: PASSED` means the file structure is valid for analysis.
- `pilot_readiness: READY` means the package is ready for YieldOS analysis.
- `privacy_status: PASSED` means no known sensitive column names were detected.

None of these statuses mean:
- Industrial validation
- Safety qualification
- Root-cause confirmation
- Production deployment approval
- A certified privacy audit

`hardware_execution_enabled = false` in all import-check outputs.
No robot commands are issued during import-check.

---

### FYFab Seed

Introduced in v2.8.0.

The FYFab Seed pipeline enforces the following hard boundaries:

- `hardware_execution_enabled = false` in all FYFab outputs
- `human_review_required = true` in all FYFab outputs
- `candidate_only = true` in the chip passport
- No fabrication equipment control of any kind
- No process recipe execution or modification
- No lithography, deposition, or etch control
- No physical design signoff claim
- No timing closure claim
- No yield guarantee

Forbidden terms in FYFab output JSON: `execute_recipe`, `modify_recipe`,
`control_deposition`, `control_etch`, `control_lithography`,
`physical_design_signoff_certified`, `timing_closure_certified`,
`yield_guarantee`, `certified_root_cause`, `confirmed_root_cause`.

---

## Permitted Action Names

Recovery candidate `action` fields must use names from this category:

```
recommend_inspection
request_missing_evidence
schedule_human_review
flag_anomaly
suggest_recovery
pull_log
hold_pending_review
schedule_maintenance
reduce_operating_parameter
delay_operation
```

The following action names are prohibited:

```
live_control
hardware_command
execute_hardware
send_robot_command
send_satellite_command
uplink_command
change_recipe
modify_recipe
equipment_start
equipment_stop
auto_calibration_execute
```

---

## Functional Yield Claim Boundary

The safety boundary exists to protect the Functional Yield claim boundary:
YieldOS can identify candidate usable functions and blocked functions, but it does not certify safety, execute recovery, or control hardware.

Every output is scoped to:
- what can still function (candidate)
- what must be blocked (candidate)
- under what valid conditions (advisory)
- based on what evidence (lineage-traced)

YieldOS does not cross into:
- certified operational capability
- automatic recovery execution
- root cause certification
- yield guarantee
- safety certification
