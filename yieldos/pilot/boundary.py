"""
yieldos/pilot/boundary.py

Generates the boundary_statement.json output for `yieldos pilot init`.
Clearly states what YieldOS claims and does not claim for a given domain.
"""
from __future__ import annotations

from .contracts import PilotContract


def build_boundary_statement_md(contract: PilotContract) -> str:
    """
    Returns a Markdown pilot_boundary_statement.md string.
    Documents what YieldOS is and is not for this domain pilot.
    """
    lines = [
        f"# Pilot Boundary Statement — {contract.display_name}",
        "",
        "## What HAL YieldOS IS",
        "",
        "> A **read-only Functional Yield Evidence Layer**. YieldOS collects evidence,",
        "> scores functional yield, and prepares human-readable decision readiness reports.",
        "> It does not execute actions, control hardware, or certify outcomes.",
        "",
        "## Core Question",
        "",
        f"> {contract.organizing_question}",
        "",
        "## What YieldOS WILL Produce",
        "",
    ]
    for claim in contract.evidence_claims:
        lines.append(f"- {claim}")
    lines += [
        "",
        "## What YieldOS Will NOT Do",
        "",
    ]
    for claim in contract.blocked_claims:
        lines.append(f"- {claim}")
    lines += [
        "",
        "## Safety Constraints",
        "",
        "| Constraint | Value |",
        "|------------|-------|",
        "| read_only | true |",
        "| human_review_required | true |",
        "| automatic_decision_enabled | false |",
        "| approval_gate_required | true |",
        "| shadow_only | true |",
        "| causal_claim_boundary | candidate_only_not_certified_cause |",
        "",
        "## Pilot Scope",
        "",
        f"- **Domain**: {contract.domain}",
        f"- **Estimated pilot duration**: {contract.pilot_duration_hint}",
        f"- **Minimum records for valid analysis**: {contract.min_records}",
        "",
        "---",
        "",
        "_Human review and approval required before any operational decision._",
        "_HAL YieldOS — read-only Functional Yield Evidence Layer._",
    ]
    return "\n".join(lines)


def build_boundary_statement(contract: PilotContract) -> dict:
    """
    Returns a boundary_statement dict suitable for JSON serialization.
    Documents what YieldOS is and is not for this domain pilot.
    """
    return {
        "schema": "hal.yieldos.pilot_boundary_statement.v1",
        "domain": contract.domain,
        "display_name": contract.display_name,
        "organizing_question": contract.organizing_question,
        "what_yieldos_is": (
            "A read-only Functional Yield Evidence Layer. "
            "YieldOS collects evidence, scores functional yield, and prepares "
            "human-readable decision readiness reports. It does not execute "
            "actions, control hardware, or certify outcomes."
        ),
        "what_yieldos_is_not": [
            "Not a hardware controller or actuation system",
            "Not a root-cause analysis tool (candidates only, not certified causes)",
            "Not a safety certification platform",
            "Not a predictive maintenance scheduler",
            "Not an autonomous decision-making system",
            "Not a replacement for domain expert human review",
        ],
        "evidence_claims": contract.evidence_claims,
        "blocked_claims": contract.blocked_claims,
        "human_review_required": True,
        "automatic_decision_enabled": False,
        "approval_gate_required": True,
        "causal_claim_boundary": "candidate_only_not_certified_cause",
        "read_only": True,
        "shadow_only": True,
        "pilot_scope": (
            f"This pilot covers the '{contract.domain}' domain. "
            f"Estimated pilot duration: {contract.pilot_duration_hint}. "
            f"Minimum records for valid analysis: {contract.min_records}."
        ),
    }
