# Contributing to Agentic Architecture

## Evidence standard

Treat architectural reasoning as a hypothesis until a reproducible artifact supports it.

- Label a statement as an invariant, measurement, or design target.
- For measurements, include the command, workload or fixture, environment, and raw result.
- For security properties, state the threat model and include at least one bypass or tampering test.
- Prefer a CI check over a prose-only process rule.
- Do not describe example output as a production benchmark.

Use Python 3.12 or newer. Before submitting, run:

```bash
python -m pip install ruff==0.16.3
python -m compileall -q examples tests
python -m unittest discover -s tests -v
python -m ruff check examples tests
```

In PowerShell, set `$env:PYTHONIOENCODING = 'utf-8'` before running examples.

If you add a pattern, add its invariant test. The existing suites show the
shape:

| Suite | Pins |
|---|---|
| `tests/test_evidence_plane.py` | A receipt fails verification when the claim, artifact, key, or decision changes |
| `tests/test_routing_invariants.py` | No request reaches the reasoning path while the budget is spent, and the retry hole that leaves |
| `tests/test_silence_invariants.py` | No component both reads free text and holds a capability |
| `tests/test_grounding_invariants.py` | The six firewall rules, and the two limits the doc claims |

Note the pattern in the last two: tests exist for the **limits** of a claim as
well as for the claim. A documented gap that nothing pins is a gap that gets
quietly closed or quietly widened, and either way the document becomes wrong.

Submit reproducible examples, implementation findings, or corrections to a documented claim.

## Ways to Contribute

### 1. Share Implementation Experiences
Have you implemented these patterns? We'd love to hear about:
- What worked well
- What was challenging
- Metrics and results
- Lessons learned

Open an issue with the `experience` label or submit a case study.

### 2. Propose New Patterns
Notice a pattern that's missing? To propose a new pattern:

1. Open an issue describing:
   - The problem it solves
   - The core insight
   - How it fits with existing patterns
2. If approved, submit a PR with a new doc in `docs/patterns/`

### 3. Improve Documentation
- Fix typos, clarify explanations
- Add diagrams (Mermaid preferred)
- Improve code examples
- Add translations

### 4. Submit Code Examples
Add examples to `examples/` that demonstrate patterns:
- Should be self-contained and runnable
- Include comments explaining the pattern
- Follow existing code style

## Documentation Style

### Pattern Documents

Use the [current pattern template](docs/README.md). Add new patterns under `docs/patterns/` with these sections:

- The problem
- The mechanism
- The invariant
- What this does not do
- The test
- When not to use this
- What to measure
- Reference implementations

Distinguish worked examples from measurements. A passing check proves only the property and cases it exercises.

### Code Style

- Python examples should be type-hinted
- Use clear, descriptive names
- Prefer simplicity over cleverness
- Include docstrings for public methods

## Pull Request Process

1. Fork the repo and create your branch from `main`
2. Add or update documentation as needed
3. Ensure any code examples run without errors
4. Update the README if adding new patterns
5. Submit a PR with a clear description

## Code of Conduct

- Be respectful and constructive
- Focus on the ideas, not the person
- Welcome newcomers
- Assume good faith

## Questions?

Open an issue with the `question` label.
