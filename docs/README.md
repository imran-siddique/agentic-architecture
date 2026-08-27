# Pattern catalog

Each pattern in `patterns/` follows the same shape, so you can read one and know
where to look in the next:

| Section | What it answers |
|---|---|
| The problem | What goes wrong without this, concretely |
| The mechanism | What the system does differently. Not the benefit, the mechanism |
| The invariant | One thing that must hold, phrased so it can fail |
| What this does not do | The limits of that invariant, stated rather than implied |
| The test | What a suite has to cover for the invariant to mean anything |
| When not to use this | At least one situation where this is the wrong choice |
| What to measure | The signals that tell you whether it worked here |
| Reference implementations | Where this exists as running code, and what that code does not do |

A pattern with no falsifiable invariant is advice. The pattern-proposal issue
template says the same thing.

## Patterns

`Consolidated` means the document lives in `patterns/` and follows the template
above. `Standalone` would mean a document still in its original form at its
original path. There are none left: all four families are through the template.

| Pattern | Family | Catalog state |
|---|---|---|
| [Routing before reasoning](./patterns/routing.md) | Decide what deserves computation | Consolidated |
| [Grounded context](./patterns/grounded-context.md) | Constrain with structure | Consolidated |
| [Silent execution](./patterns/silent-execution.md) | Silence and capability | Consolidated |
| [Enforcement and evidence](./patterns/enforcement-and-evidence.md) | Enforce and prove | Consolidated |

Eleven earlier documents are now stubs pointing at the consolidated pattern
that absorbed them, so links published before the merge still land somewhere
useful:

| Stub | Absorbed into |
|---|---|
| `inference-trap.md`, `guardrail-router.md`, `compute-to-lookup-ratio.md` | Routing before reasoning |
| `multidimensional-knowledge-graphs.md`, `semantic-firewall.md`, `recursive-ontologies.md` | Grounded context |
| `headless-agent.md`, `silent-swarm.md`, `mute-agent.md` | Silent execution |
| `control-planes-vs-prompts.md`, `evidence-plane.md` | Enforcement and evidence |

Eleven documents totalling roughly 5,800 lines became four totalling roughly
3,800, with every unique implementation section retained. The reduction is the
Overview, Benefits, Anti-Patterns, Conclusion, and Further Reading sections
that each document repeated.

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

Every consolidated pattern has a suite. That was not true before the catalog
existed, and it is the reason the template puts `The invariant` above `The
test` rather than after it.
