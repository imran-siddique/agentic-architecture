# Pattern catalog

Each pattern in `patterns/` follows the same shape, so you can read one and
know where to look in the next:

| Section | What it answers |
|---|---|
| The problem | What goes wrong without this, concretely |
| The mechanism | What the system does differently. Not the benefit, the mechanism |
| The invariant | One thing that must hold, phrased so it can fail |
| The test | What a test suite has to cover for the invariant to mean anything |
| When not to use this | At least one situation where this is the wrong choice |
| What to measure | The signals that tell you whether it worked here |
| Reference implementations | Where this exists as running code, and what that code does not do |

A pattern with no falsifiable invariant is advice. The catalog says so on the
issue template too.

## Patterns

| Pattern | Family | Status |
|---|---|---|
| [Routing before reasoning](./patterns/routing.md) | Decide what deserves computation | Merged |
| [The Semantic Firewall](./semantic-firewall.md) | Constrain with structure | Not yet merged |
| [Multidimensional Knowledge Graphs](./multidimensional-knowledge-graphs.md) | Constrain with structure | Not yet merged |
| [Recursive Ontologies](./recursive-ontologies.md) | Constrain with structure | Not yet merged |
| [The Headless Agent](./headless-agent.md) | Silence and capability | Not yet merged |
| [The Silent Swarm](./silent-swarm.md) | Silence and capability | Not yet merged |
| [The Mute Agent](./mute-agent.md) | Silence and capability | Not yet merged |
| [Control Planes vs Prompts](./control-planes-vs-prompts.md) | Enforce and prove | Not yet merged |
| [The Evidence Plane](./evidence-plane.md) | Enforce and prove | Not yet merged |

Three documents are not patterns and are not going into `patterns/`:

- [The Cognitive Systems Architect](./cognitive-systems-architect.md), a role essay
- [Agent Mesh Patterns](./agent-mesh-patterns.md), notes from two prototypes
- [Production Deployment Guide](./production-deployment-guide.md), operational practice

## Families

**Decide what deserves computation.** Classify the request before answering it,
and enforce a budget on the expensive path.

**Constrain with structure.** Use a graph, not a similarity score, to decide
what the model is allowed to see and allowed to claim.

**Silence and capability.** Give language to the boundary and capability to the
workers, and never to the same component.

**Enforce and prove.** Put the rule where the model cannot argue with it, then
emit evidence that someone else can check.
