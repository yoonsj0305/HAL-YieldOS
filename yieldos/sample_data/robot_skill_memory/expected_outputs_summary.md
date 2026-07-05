# Expected Outputs — Robot Skill Memory Demo

Running `yieldos robot skill-demo --out <dir>` on this sample data produces:

## Standard Bundle (22 files)

All standard YieldOS output bundle files are generated first via RobotAnalyzer.
The robot telemetry shows an escalating gripper anomaly that triggers:
- `state_snapshot.json`: `JOINT_PRECISION_DEGRADATION_CANDIDATE` or `FAULT_CANDIDATE`
- `evidence_pack.json`: 2-4 evidence objects (motor_current rising, imu_vibration rising, fault codes)
- `ooda_frame.json`: `act = "recommendation_only_no_hardware_action"`
- `functional_passport.json`: `hardware_execution_enabled = false`, `human_approval_required = true`

## Skill Memory Extras (3 files)

### operator_skill_note.json
- Schema: `hal.yieldos.robot.operator_skill_note.v1`
- Contains structured observations from 3 operator notes
- Each note has `claim_boundary = "human_observation_not_certified_root_cause"`
- Contains `linked_evidence_refs` pointing to evidence objects

### human_intervention_timeline.json
- Schema: `hal.yieldos.robot.human_intervention_timeline.v1`
- Contains 1 intervention event (manual_stop_observed from telemetry row 29)
- `intervention_type` is one of the allowed types only
- `hardware_action_executed_by_yieldos = false` in all entries

### skill_to_evidence_map.json
- Schema: `hal.yieldos.robot.skill_to_evidence_map.v1`
- Maps operator skill notes to evidence objects
- `claim_boundary = "candidate_only"` in all mappings

## Functional Passport Enrichment

The `functional_passport.json` is extended with:
```json
{
  "human_skill_context": {
    "operator_note_present": true,
    "maintenance_note_present": true,
    "human_intervention_observed": true,
    "skill_capture_status": "partial"
  },
  "candidate_validity_conditions": [...],
  "advisory_not_to_do": [...],
  "validity_boundary": "candidate_context_not_certification",
  "advisory_boundary": "advisory_human_review_only"
}
```

## Safety Invariants

- No file contains `send_ros_command`, `execute_recovery_auto`, or `autonomous_control_loop`
- `hardware_execution_enabled` is `false` everywhere
- All intervention types are from the allowed set only
- All claim_boundary values are `human_observation_not_certified_root_cause`, 
  `observed_intervention_not_yieldos_action`, or `candidate_only`
