# Roadmap

## Current baseline: v3.0.8

HAL YieldOS is a read-only Functional Yield Evidence Layer.

Current stable capabilities:

- 5-domain demo generation (robot, semiconductor, space, memory, semiforge/FYFab)
- strict validation (53-point contract check)
- robot pilot-ready pack
- semiconductor pilot-ready pack with SemFab confidence explanation
- Recovery Compiler intake/export generation (candidate-only, no execution)
- public demo script
- GitHub public documentation suite

## Near-term

- Improve sample data clarity and coverage
- Add more synthetic semiconductor edge cases
- Add more synthetic robot degradation cases
- Improve report readability
- Improve schema documentation
- Add optional architecture diagrams
- Add GitHub Actions CI
- Add more installed-wheel smoke tests

## Mid-term

- Design-partner pilot preparation
- Better schema versioning
- Stronger evidence lineage viewer
- More explicit missing-evidence workflows
- Enhanced Functional Passport comparison across time
- More domain-specific confidence explanations

## Long-term

- Separate HAL Recovery Compiler integration boundary
- Human-approved handoff workflows
- Enterprise deployment packaging
- Larger synthetic benchmark suite
- Formal public specification for Functional Yield Evidence Packs

## Non-goals

The following are explicitly outside the scope of HAL YieldOS — now and in the future:

- hardware control of any kind
- robot actuation
- semiconductor recipe modification
- firmware flashing
- automatic recovery
- safety certification
- root-cause certification
- yield guarantee
- timing closure
- running Recovery Compiler inside YieldOS
- replacing MES, SCADA, APC, FDC, or ROS

HAL YieldOS is not a hardware control system, not a recipe optimizer, not a safety certification tool, and not an autonomous recovery system.

---

*HAL YieldOS v3.0.8*
