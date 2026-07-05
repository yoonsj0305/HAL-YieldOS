# Security Policy

## Supported Versions

| Version | Status |
|---------|--------|
| 3.0.7 | Current PoC release |
| < 3.0.7 | Not actively maintained |

HAL YieldOS is a **research/PoC project** and is not yet certified for production industrial systems.

---

## Reporting Vulnerabilities

To report a security vulnerability, please open a GitHub issue with the label `security`.

If the vulnerability is sensitive, contact the maintainer directly at:
**yoonsj0305@gmail.com**

Please include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigation

We will acknowledge within 7 days and aim to address confirmed vulnerabilities in the next patch release.

---

## Important Safety Boundary

HAL YieldOS is designed as a **read-only, offline evidence layer**.

**Do not connect YieldOS directly to production industrial control systems.**

YieldOS must not be used to:

- Control equipment, robots, or spacecraft
- Send commands to production systems
- Modify semiconductor recipes
- Execute recovery profiles
- Flash firmware
- Operate safety-critical systems

YieldOS reads sanitized data files. It does not open network connections to industrial systems, PLCs, SCADA, or DCS.

---

## Data Handling

When using YieldOS with real industrial data:

- **Sanitize inputs** — remove proprietary recipe parameters, process secrets, and calibration constants before analysis
- **Anonymize operator identifiers** — hash or replace operator names and IDs
- **Do not commit real customer data** — the `samples/` directory must contain only synthetic or fully anonymized data
- **Do not include real wafer IDs, lot IDs, or device serial numbers** in sample data committed to the repository

See [docs/ANONYMIZATION_GUIDE.md](docs/ANONYMIZATION_GUIDE.md) for the full anonymization checklist.

---

## Output Safety

YieldOS outputs are **candidate evidence for human review**. They are not:

- Safety certifications
- Operational decisions
- Hardware commands
- Production qualifications
- Yield guarantees

Do not use YieldOS outputs directly to authorize hardware operations without independent human review.

---

*HAL YieldOS v3.0.7*
