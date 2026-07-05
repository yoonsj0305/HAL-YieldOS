# Anonymization Guide

HAL YieldOS v3.0.11 - Privacy and Anonymization Guide for Robot Operator Data

---

## Purpose

YieldOS only accepts pre-anonymized robot log packages. This guide describes how to
prepare an external log package so that all personal data is removed before import-check
or analysis.

YieldOS does not de-anonymize, process, or store personal data of any kind.

---

## Mandatory Anonymization Steps

### Step 1 ??Remove or hash operator identifiers

Replace all real operator identifiers with a consistent hash:

| Original column | Required replacement |
|-----------------|----------------------|
| `operator_name` | Remove entirely |
| `employee_id` | Replace with `operator_id_hash` (SHA-256 or random) |
| `raw_operator_id` | Remove entirely |
| `technician_name` | Remove entirely |

Example transformation:
```
Before: employee_id="EMP-00312", operator_name="John Smith"
After:  operator_id_hash="op_hash_b8f2"
```

The hash must be consistent per operator across all files in the package.

---

### Step 2 ??Redact note text

Replace all free-text note fields with pre-redacted summaries:

| Original column | Required replacement |
|-----------------|----------------------|
| `raw_note` | Remove entirely |
| `operator_note` | Replace with `note_text_redacted` |
| `maintenance_log` | Replace with `note_text_redacted` |

The `note_text_redacted` field must:
- Contain no real names, locations, or contact details.
- Use bracketed placeholders for any redacted content: `[REDACTED: brief category]`
- Have `redaction_status` set to `"redacted"` or `"demo_safe"`

---

### Step 3 ??Remove or hash location data

| Original column | Action |
|-----------------|--------|
| `factory_address` | Remove entirely |
| `customer_name` | Remove entirely |
| `site_id` (if raw) | Replace with a code (e.g. `site_A`) |

---

### Step 4 ??Remove biometric and contact data

The following columns must not appear in the package at all:

- `phone_number`
- `email`
- `home_address`
- `face_image` / `face_image_path`
- `voice_recording` / `voice_recording_path`
- `biometric_id` / `raw_biometric_id`

---

### Step 5 ??Set `contains_personal_data`

After completing Steps 1??:

- Set `contains_personal_data = false` for all rows.
- If any row still contains personal data that could not be redacted, set it to `true` and
  do not submit that package for YieldOS import-check until it is fully resolved.

---

## Transformation Reference Table

| Before | After |
|--------|-------|
| `operator_name = "John Smith"` | (column removed) |
| `employee_id = "EMP-003"` | `operator_id_hash = "op_hash_b8f2"` |
| `note_text = "gripper slipped near machine 12, line B"` | `note_text_redacted = "[REDACTED: gripper slip observation]"`, `redaction_status = "redacted"` |
| `factory_address = "123 Industrial Ave"` | (column removed) |
| `customer_name = "ACME Corp"` | (column removed) |
| `contains_personal_data = true` | resolve and set to `false` before submission |

---

## YieldOS Import-Check Caveat

YieldOS import-check is a structural and heuristic privacy check only. It:

- Detects known sensitive column names by name pattern (e.g. `operator_name`, `email`).
- Checks `contains_personal_data` field values.
- Does NOT perform NLP or deep content scanning.
- Does NOT guarantee that all personal data has been removed.

**Human review is always required before submitting real operator data for analysis.**

The import-check result `privacy_status: PASSED` means no obvious sensitive columns were
found, not that the data is certified privacy-compliant.

---

## Safety Boundary

- YieldOS is read-only. It does not modify, store, or transmit the original data.
- Anonymization must be completed before the data reaches YieldOS.
- YieldOS outputs are candidate observations, not certified findings.
