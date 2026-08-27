## What this changes

<!-- One or two sentences. What is different after this merges? -->

## Claim labels

`CONTRIBUTING.md` asks every statement to be one of three kinds. Confirm the
ones this PR touches:

- [ ] **Invariant**: enforced by code in `examples/` and covered by a test in `tests/`.
- [ ] **Measurement**: includes the command, the fixture or workload, the environment, and the raw result.
- [ ] **Design target**: written as a goal the adopter must validate, not as an achieved result.
- [ ] This PR adds no quantitative or security claims.

## Checks

```bash
python -m compileall -q examples tests
python -m unittest discover -s tests -v
ruff check examples tests
```

- [ ] All three pass locally.
- [ ] Any new example is dependency-free and runs to completion under `python examples/<name>_example.py`.
- [ ] No em dashes in prose.
