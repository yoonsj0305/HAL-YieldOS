"""
yieldos/pilot/sanitization.py

Generates the sanitization_checklist.json for `yieldos pilot init`.
Provides domain-specific steps the customer must complete before
sharing data for YieldOS pilot analysis.
"""
from __future__ import annotations

from .contracts import PilotContract

_UNIVERSAL_STEPS = [
    {
        "step": 1,
        "category": "PII_removal",
        "action": "Remove all personally identifiable information (PII)",
        "details": (
            "Remove: names, email addresses, employee IDs, badge numbers, "
            "usernames, phone numbers, IP addresses."
        ),
        "required": True,
        "verification": "Grep exported files for '@', common name patterns, and numeric employee IDs.",
    },
    {
        "step": 2,
        "category": "serial_number_removal",
        "action": "Remove or anonymize equipment serial numbers",
        "details": (
            "Replace specific equipment serial numbers with generic codes "
            "(e.g., TOOL_01, ROBOT_ARM_02). "
            "Maintain consistency: the same real serial = the same code throughout."
        ),
        "required": True,
        "verification": "Search for S/N patterns (all-caps + digits, 'SN:', 'Serial:').",
    },
    {
        "step": 3,
        "category": "credentials",
        "action": "Confirm no credentials, API keys, or tokens in data",
        "details": "Check JSON config files for password/token/key fields. Remove or redact.",
        "required": True,
        "verification": "grep -ri 'password\\|token\\|apikey\\|secret' <data_dir>",
    },
    {
        "step": 4,
        "category": "ip_protection",
        "action": "Verify no proprietary recipe parameters or trade secrets",
        "details": (
            "Process recipes, chemical formulas, and exact equipment settings "
            "may constitute trade secrets. Replace exact values with normalized ranges "
            "or anonymized codes where required by your IP policy."
        ),
        "required": False,
        "verification": "Consult your legal/IP team before sharing process recipe data.",
    },
    {
        "step": 5,
        "category": "format_validation",
        "action": "Validate CSV files have correct headers",
        "details": (
            "Open each CSV in a text editor. Confirm the first row matches "
            "the required columns listed in pilot_contract.json input_fields."
        ),
        "required": True,
        "verification": "head -1 <file>.csv | check against pilot_contract.json columns list",
    },
    {
        "step": 6,
        "category": "timestamp_format",
        "action": "Ensure timestamps are in ISO 8601 format (UTC preferred)",
        "details": (
            "YieldOS expects: YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DD HH:MM:SS. "
            "Do not strip timestamps — temporal analysis depends on them."
        ),
        "required": True,
        "verification": "Check timestamp column for consistent ISO 8601 format.",
    },
]


def _domain_specific_steps(domain: str) -> list[dict]:
    base_step = len(_UNIVERSAL_STEPS) + 1

    domain_steps: dict[str, list[dict]] = {
        "robot": [
            {
                "step": base_step,
                "category": "domain_specific",
                "action": "Anonymize joint identifiers if linked to robot serial",
                "details": "Replace joint IDs with J1, J2, ... if they embed serial number info.",
                "required": False,
                "verification": "Confirm joint_id values do not contain serial-traceable strings.",
            },
        ],
        "semiconductor": [
            {
                "step": base_step,
                "category": "domain_specific",
                "action": "Anonymize wafer lot IDs and tool chamber IDs",
                "details": (
                    "Replace lot IDs with sequential integers (LOT_001, LOT_002). "
                    "Replace chamber IDs with CHAMBER_A, CHAMBER_B, etc."
                ),
                "required": True,
                "verification": "Confirm no lot_id values trace back to customer order records.",
            },
        ],
        "space": [
            {
                "step": base_step,
                "category": "domain_specific",
                "action": "Redact command codes and uplink sequences",
                "details": (
                    "Replace raw command codes with 'CMD_REDACTED'. "
                    "Retain event_type and subsystem columns."
                ),
                "required": True,
                "verification": "Search event_log for hex command sequences or 'CMD_' patterns.",
            },
        ],
        "memory": [
            {
                "step": base_step,
                "category": "domain_specific",
                "action": "Remove device serial number from all files",
                "details": (
                    "Memory device serial numbers are traceable to customers. "
                    "Remove or replace with DEVICE_001."
                ),
                "required": True,
                "verification": "grep -ri 'serial\\|sn\\|device_id' <data_dir>",
            },
        ],
        "semiforge": [
            {
                "step": base_step,
                "category": "domain_specific",
                "action": "Confirm synthetic_defect_map.json contains only simulated data",
                "details": (
                    "SemiForge uses synthetic simulation. "
                    "If any real fab parameters were embedded, remove them now."
                ),
                "required": True,
                "verification": "Review defect_map generation script to confirm synthetic origin.",
            },
        ],
    }

    return domain_steps.get(domain, [])


def build_sanitization_checklist_md(contract: PilotContract) -> str:
    """
    Returns a Markdown sanitization_checklist.md string.
    """
    steps = list(_UNIVERSAL_STEPS) + _domain_specific_steps(contract.domain)
    required = [s for s in steps if s["required"]]
    optional = [s for s in steps if not s["required"]]

    lines = [
        f"# Data Sanitization Checklist — {contract.display_name}",
        "",
        "Complete **all REQUIRED steps** before exporting data for YieldOS pilot analysis.",
        "OPTIONAL steps are recommended at your legal/IP team's discretion.",
        "",
        f"Required steps: {len(required)} | Optional steps: {len(optional)}",
        "",
        "---",
        "",
        "## Required Steps",
        "",
    ]
    for s in required:
        lines += [
            f"### Step {s['step']}: {s['action']}",
            "",
            f"**Category**: `{s['category']}`",
            "",
            s["details"],
            "",
            f"**Verification**: `{s['verification']}`",
            "",
            "- [ ] Completed",
            "",
        ]
    if optional:
        lines += [
            "## Optional Steps",
            "",
        ]
        for s in optional:
            lines += [
                f"### Step {s['step']}: {s['action']}",
                "",
                f"**Category**: `{s['category']}`",
                "",
                s["details"],
                "",
                f"**Verification**: `{s['verification']}`",
                "",
                "- [ ] Completed (optional)",
                "",
            ]
    lines += [
        "---",
        "",
        "## Sign-Off",
        "",
        "After completing all required steps, the responsible data owner must confirm:",
        "",
        "> I have reviewed the sanitization checklist and confirm the exported data",
        "> does not contain PII, credentials, or unauthorized proprietary parameters.",
        "",
        "- **Name**: _______________________",
        "- **Date**: _______________________",
        "- **Signature**: _______________________",
    ]
    return "\n".join(lines)


def build_sanitization_checklist(contract: PilotContract) -> dict:
    steps = list(_UNIVERSAL_STEPS) + _domain_specific_steps(contract.domain)
    required_steps = [s for s in steps if s["required"]]
    optional_steps = [s for s in steps if not s["required"]]

    return {
        "schema": "hal.yieldos.pilot_sanitization_checklist.v1",
        "domain": contract.domain,
        "total_steps": len(steps),
        "required_steps_count": len(required_steps),
        "optional_steps_count": len(optional_steps),
        "instruction": (
            "Complete all REQUIRED steps before sharing data for pilot analysis. "
            "OPTIONAL steps are recommended by your IP/legal team's discretion."
        ),
        "steps": steps,
        "sign_off_prompt": (
            "After completing all required steps, a human responsible for the data "
            "export must confirm: 'I have reviewed the sanitization checklist and "
            "confirm the exported data does not contain PII, credentials, or "
            "un-authorized proprietary parameters.'"
        ),
    }
