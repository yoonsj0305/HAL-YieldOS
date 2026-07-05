## Summary

<!-- Describe what this PR changes and why. -->

## Change Type

- [ ] Bug fix
- [ ] Documentation
- [ ] Tests
- [ ] Sample data
- [ ] Report readability improvement
- [ ] Domain pack improvement
- [ ] Other:

## Safety Boundary

This PR preserves the YieldOS safety boundary:

- [ ] Does **not** add hardware control
- [ ] Does **not** add recipe control or modification
- [ ] Does **not** add robot commands
- [ ] Does **not** add satellite uplink commands
- [ ] Does **not** add autonomous recovery execution
- [ ] Does **not** claim safety certification
- [ ] Does **not** claim yield guarantee
- [ ] Does **not** claim certified root cause
- [ ] Does **not** generate `recovery_profile.json`
- [ ] Does **not** add external cloud or API dependencies

## Validation

- [ ] `python -m pytest -q` passes
- [ ] `yieldos doctor --deep` passes
- [ ] `yieldos demo --all --out output/demo_all` runs without errors
- [ ] `yieldos validate --case output/demo_all/semiconductor --strict` passes
- [ ] Strict validation checked for affected domains

## Notes

<!-- Any additional notes for reviewers. -->
