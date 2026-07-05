# Pilot Proposal Template

HAL YieldOS v3.0.11 - Robot Skill Memory Pilot Proposal Template

Use this template to propose a pilot deployment of HAL YieldOS for robot skill memory
analysis. Fill in each section and submit for human review.

---

## Section 1 ??Pilot Overview

**Pilot Title:** [e.g. "Robot Arm Payload Transport ??Skill Memory Analysis Pilot"]

**Proposing Organization:** [Team / Department / Company]

**Proposed Pilot Duration:** [e.g. "4 weeks"]

**Target Robot(s):** [Anonymized robot ID(s) ??e.g. "robot_02, robot_03"]

**Target Task(s):** [Task identifier(s) ??e.g. "task_arm_motion_087"]

**Objective:**
Describe what you want to learn from a YieldOS skill memory analysis.
Example: "Determine whether sim-to-real gaps in joint torque can explain the observed
15% failure rate in payload arm motion tasks."

---

## Section 2 ??Data Availability

**Available Data Sources:**
- [ ] robot_telemetry.csv (required)
- [ ] operator_notes.csv (required)
- [ ] maintenance_notes.csv (required)
- [ ] sim_expectation.csv (optional but recommended)

**Data Period:** [Start date] ??[End date]

**Estimated Record Count:** [e.g. "~500 telemetry rows, 20 operator notes"]

**Anonymization Status:**
- [ ] All operator names replaced with hashes
- [ ] All note text pre-redacted
- [ ] All location/contact data removed
- [ ] `contains_personal_data = false` verified for all rows

**Import-Check Status:**
Run `yieldos robot import-check` and paste the result:
```
schema_status:    [PASSED / PASSED_WITH_WARNINGS / FAILED]
privacy_status:   [PASSED / PASSED_WITH_WARNINGS]
readiness_status: [READY / READY_WITH_LIMITATIONS / NOT_READY]
```

---

## Section 3 ??Analysis Scope

**Analysis Type Requested:**
- [ ] Robot Skill Memory Demo (full output bundle + case study)
- [ ] Sim-to-Real Gap Analysis
- [ ] Force Compliance Event Log
- [ ] Before-After Functional Reclassification

**Specific Questions:**
List the specific operational questions this pilot should address:
1. [Question 1]
2. [Question 2]
3. [Question 3]

**Out of Scope (explicitly not requested):**
- Safety certification ??YieldOS does not certify safety
- Root-cause certification ??YieldOS outputs are candidates only
- Automatic recovery execution ??YieldOS does not control robots
- Production deployment approval ??pilot outputs require human review

---

## Section 4 ??Human Review Plan

**Who will review YieldOS outputs?**
[Name / role of responsible human reviewer]

**Review Timeline:** [e.g. "Within 1 week of pilot completion"]

**Decision Authority:**
Who has authority to act on or reject the pilot findings?
[Name / role / approval process]

**Escalation Path:**
If YieldOS finds evidence of a systematic failure pattern, what is the escalation path?
[e.g. "Submit to safety team for independent verification before any operational change"]

---

## Section 5 ??Pilot Success Criteria

Define what a "successful pilot" looks like for your team:

| Criterion | Target |
|-----------|--------|
| Import-check passes | schema_status == PASSED |
| Skill memory analysis completes | state_snapshot.json generated |
| Case study generated | robot_skill_memory_case_study.json generated |
| Human review completed | Reviewer sign-off within [N] days |
| Actionable signal found | [e.g. "At least 1 candidate gap factor identified"] |

---

## Section 6 ??Post-Pilot Next Steps

**If pilot findings are positive:**
- [ ] Request extended dataset analysis (longer date range)
- [ ] Expand to additional robots / tasks
- [ ] Share candidate findings with safety team for independent review

**If pilot findings are inconclusive:**
- [ ] Request additional data collection (more telemetry columns)
- [ ] Adjust sim_expectation values
- [ ] Consult with YieldOS team on analysis scope

**What YieldOS does NOT provide as a next step:**
- Automated recovery execution
- Real-time control adjustment
- Hardware certification
- Root-cause confirmation

All post-pilot actions must be approved by qualified human reviewers before any
operational change is made.

---

*Template version: HAL YieldOS v3.0.11*
*YieldOS is a read-only, candidate-only, human-review-required evidence layer.*
*No outputs constitute safety certification or production deployment approval.*
