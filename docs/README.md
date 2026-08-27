# Pattern catalog

Each pattern in `patterns/` follows the same shape, so you can read one and know
where to look in the next:

| Section | What it answers |
|---|---|
| The problem | What goes wrong without this, concretely |
| The mechanism | What the system does differently. Not the benefit, the mechanism |
| The invariant | One thing that must hold, phrased so it can fail |
| What this does not do | The limits of the invariant, stated rather than implied |
| The test | What a suite has to cover for the invariant to mean anything |
| When not to use this | At least one situation where this is the wrong choice |
| What to measure | The signals that tell you whether it worked here |
| Reference implementations | Where this exists as running code, and what that code does not do |

A pattern with no falsifiable invariant is advice. The pattern-proposal issue
template says the same thing.

## Patterns

`Consolidated` means the document lives in `patterns/` and follows the template
above. `Standalone` means it is still in its original form at its original path,
and has not been through the template yet.

| Pattern | Family | Catalog state |
|---|---|---|
| [Routing before reasoning](./patterns/routing.md) | Decide what deserves computation | Consolidated |
| [Grounded context](./patterns/grounded-context.md) | Constrain with structure | Consolidated |
| [The Headless Agent](./headless-agent.md) | Silence and capability | Standalone |
| [The Silent Swarm](./silent-swarm.md) | Silence and capability | Standalone |
| [The Mute Agent](./mute-agent.md) | Silence and capability | Standalone |
| [Control Planes vs Prompts](./control-planes-vs-prompts.md) | Enforce and prove | Standalone |
| [The Evidence Plane](./evidence-plane.md) | Enforce and prove | Standalone |

Five earlier documents are now stubs pointing at the consolidated pattern that
absorbed them, so links published before the merge still land somewhere useful:
`inference-trap.md`, `guardrail-router.md`, `compute-to-lookup-ratio.md`,
`semantic-firewall.md`, `multidimensional-knowledge-graphs.md`, and
`recursive-ontologies.md`.

Three documents are not patterns and are not going into `patterns/`:

- [The Cognitive Systems Architect](./cognitive-systems-architect.md), a role essay
- [Agent Mesh Patterns](./agent-mesh-patterns.md), notes from two prototypes
- [Production Deployment Guide](./production-deployment-guide.md), operational practice

## Families

**Decide what deserves computation.** Classify the request before answering it,
and enforce a budget on the expensive path.

**Constrain with structure.** Use a graph, not a similarity score, to decide
what the model is allowed to see and allowed to claim, and rebuild that graph
from the failures it produces.

**Silence and capability.** Give language to the boundary and capability to the
workers, and never to the same component.

**Enforce and prove.** Put the rule where the model cannot argue with it, then
emit evidence somebody else can check.

## Which patterns have tests

| Suite | Pins |
|---|---|
| `tests/test_evidence_plane.py` | A receipt fails verification when the claim, artifact, key, or decision changes |
| `tests/test_routing_invariants.py` | No request reaches the reasoning path while the budget is spent, and the retry hole that leaves |
| `tests/test_silence_invariants.py` | No component both reads free text and holds a capability |
| `tests/test_grounding_invariants.py` | The six firewall rules, and the two limits the pattern claims |
