"""
InputValidationResult — domain-specific input validation contract.

Each domain analyzer must produce an input_validation dict using
build_input_validation() and return it in result["input_validation"].
ReportWriter writes it directly to input_validation.json.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .meta import SAFETY_BLOCK, SCHEMA_VERSION, generated_by

SCHEMA = "hal.yieldos.input_validation.v1"

ALLOWED_STATUS = ("PASSED", "FAILED")
ALLOWED_DATA_LEVEL = ("MINIMUM_RUNNABLE", "BELOW_MINIMUM", "EMPTY", "INVALID_SCHEMA")


def build_input_validation(
    *,
    case_id: str,
    domain_pack: str,
    domain_adapter: str,
    status: str,
    data_level: str,
    found_inputs: List[str],
    missing_inputs: List[str],
    record_counts: Dict[str, Any],
    blocking_reasons: List[str],
    warnings: Optional[List[str]] = None,
) -> dict:
    """
    Build a structured input_validation dict.

    status must be PASSED or FAILED.
    data_level must be one of MINIMUM_RUNNABLE | BELOW_MINIMUM | EMPTY | INVALID_SCHEMA.
    """
    if status not in ALLOWED_STATUS:
        raise ValueError(f"status must be one of {ALLOWED_STATUS}, got '{status}'")
    if data_level not in ALLOWED_DATA_LEVEL:
        raise ValueError(f"data_level must be one of {ALLOWED_DATA_LEVEL}, got '{data_level}'")
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "domain_pack": domain_pack,
        "domain_adapter": domain_adapter,
        "status": status,
        "data_level": data_level,
        "found_inputs": found_inputs,
        "missing_inputs": missing_inputs,
        "record_counts": record_counts,
        "blocking_reasons": blocking_reasons,
        "warnings": warnings or [],
        "safety_boundary": SAFETY_BLOCK,
        "generated_by": generated_by(),
    }
