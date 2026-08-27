# Examples

This directory contains runnable examples of the patterns. Each file is
dependency-free and self-contained so you can read the whole mechanism in one
place.

**None of these examples call a model, and none of them measure anything.**
Latencies and costs printed by an example are constants written into that file
so the control flow is readable. Each example prints this at startup.

Only `evidence_plane_example.py` is covered by tests that can fail. Everything
else is a walkthrough.

## Available Examples

### 0. Evidence Plane (`evidence_plane_example.py`)

Demonstrates signed receipts that bind an actor, policy decision, action, and artifact digest. The tests show that altered claims, substituted artifacts, unknown keys, and denied actions fail verification.

**Run:**
```bash
python examples/evidence_plane_example.py
python -m unittest tests.test_evidence_plane -v
```

This is a dependency-free teaching example. Its shared-secret HMAC must be replaced by asymmetric, protected key custody in production.

### 1. Guardrail Router (`guardrail_router_example.py`)

Demonstrates how to implement a Guardrail Router that prevents the Inference Trap by intelligently routing requests between lookup and reasoning operations.

**Features:**
- Request classification using pattern matching
- Constraint enforcement to maintain 80-90% lookup ratio
- Multi-tier lookup system (cache, vector DB, database)
- Automatic caching of reasoning results
- Comprehensive metrics tracking

**Run:**
```bash
python examples/guardrail_router_example.py
```

**What you will see:**
- The lookup ratio the router held under the sample request mix
- A routing decision for every request, and the rule that produced it
- The constraint refusing a reasoning call once the budget is spent
- A simulated cost and latency total, derived from constants in the file

### 2. Compute-to-Lookup Ratio (`compute_to_lookup_example.py`)

Demonstrates how to implement a multi-tier lookup system that achieves the 90/10 target ratio.

**Features:**
- Multi-tier caching (L1: Memory, L2: Redis, L3: Vector Store, L4: Database, L5: LLM)
- Automatic fallback strategy
- Metrics tracking for compute-to-lookup ratio
- Performance and cost analysis

**Run:**
```bash
python examples/compute_to_lookup_example.py
```

**What you will see:**
- Which tier answered each query, and the fallthrough order
- The lookup ratio produced by the sample query mix
- A simulated cost and latency breakdown per tier

### 3. Headless Agent / Silent Swarm (`headless_agent_example.py`)

Demonstrates how headless agents communicate through structured data rather than natural language.

**Features:**
- Type-safe task and result protocols
- Specialized agents for different capabilities
- Workflow orchestration without language
- Structured telemetry and metrics
- Performance comparison with conversational approach

**Run:**
```bash
python examples/headless_agent_example.py
```

**What you will see:**
- A workflow completing with zero model calls in the coordination layer
- Typed results at every hop, with nothing to parse
- A conversational baseline printed as assumptions, with no ratio computed
  from them, because a ratio of two guesses is a guess

### 4. Silent Swarm (`silent_swarm_example.py`)

Demonstrates the "Function Over Form" principle with security-focused agent architecture separating "The Face" from "The Hands".

**Features:**
- Experience Agent (The Face): Can talk, no tools
- Specialized Agents (The Hands): Can execute, no talk
- Authorization Gateway with Security by Silence
- Code Review example showing function over form
- Jailbreak-resistant architecture

**Run:**
```bash
python examples/silent_swarm_example.py
```

**What you will see:**
- A code review returning a structured result with no prose
- The authorization gateway refusing a request without explaining itself
- The structural comparison the example can actually make: how many components
  accept free text and hold a capability at the same time

### 5. Semantic Firewall (`semantic_firewall_example.py`)

Demonstrates how to use multidimensional knowledge graphs to block hallucinations before they reach users.

**Features:**
- Multidimensional knowledge graph (entities, relationships, temporal, confidence)
- Six validation rules (entity existence, relationship validity, temporal consistency, confidence threshold, source verification, contradiction detection)
- Temporal relationship validation
- Proactive hallucination prevention
- Clear audit trail with reasons for blocking

**Run:**
```bash
python examples/semantic_firewall_example.py
```

**What you will see:**
- An expired relationship blocked, for example "Steve Jobs is CEO of Apple"
- An unknown entity blocked
- A current fact allowed, and a historical one allowed with temporal context
- The reason attached to every block

The example passes its own cases because those cases were written for it. It
tells you the rules fire, not that the rules are sufficient.

### 6. Multidimensional Knowledge Graphs (`multidimensional_kg_example.py`)

Demonstrates how to build and query multidimensional knowledge graphs with constraint-based filtering.

**Features:**
- Six-dimensional knowledge graph (Identity & Scope, Organizational Hierarchy, Service Ownership, Dependencies, Temporal Weight, Authority)
- Constraint-based filtering, which removes candidates deterministically
- Graph traversal for complex queries
- Comparison with flat RAG approach
- Real-world query examples

**Run:**
```bash
python examples/multidimensional_kg_example.py
```

**What you will see:**
- A query answered by traversing constraints rather than by similarity
- The candidate count after each dimension is applied
- A side-by-side with the flat retrieval approach on the same sample graph

### 7. Recursive Ontologies (`recursive_ontology_example.py`)

Demonstrates self-updating knowledge systems with feedback loops and ephemeral graphs.

**Features:**
- Agent telemetry capturing failures as signals
- Ephemeral knowledge graphs (OrgGraph, ProductGraph, ContextGraph)
- Event-driven graph rebuilding
- Statistical supervision (5% human review, 95% auto)
- Analyst system for pattern detection and self-healing
- Automatic knowledge gap detection and filling

**Run:**
```bash
python examples/recursive_ontology_example.py
```

**What you will see:**
- Agent failures captured as signals (not errors)
- Automatic pattern detection from repeated failures
- OrgGraph rebuilds on HR events
- ProductGraph rebuilds on documentation changes
- ContextGraph created per-project with automatic expiration
- Self-healing actions triggered automatically
- Health reports showing system evolution

## Running All Examples

```bash
# Run all examples
python examples/guardrail_router_example.py
echo ""
python examples/compute_to_lookup_example.py
echo ""
python examples/headless_agent_example.py
echo ""
python examples/silent_swarm_example.py
echo ""
python examples/semantic_firewall_example.py
echo ""
python examples/multidimensional_kg_example.py
echo ""
python examples/recursive_ontology_example.py
echo ""
python examples/evidence_plane_example.py
```

On Windows, prefix with `PYTHONIOENCODING=utf-8`; the examples print characters
outside cp1252.

## Key Insights

### What these mechanisms change

- **Routing**: reasoning becomes a decision with a rule behind it, not a default
- **Latency and cost**: both follow the reasoning share rather than request volume
- **Predictability**: a typed contract fails loudly where prose fails quietly
- **Unsupported output**: a claim the graph cannot support is blocked before release,
  within the limits of what the extractor recognises
- **Staleness**: failure signals drive graph updates instead of a curation backlog

How much any of this is worth in your system is a measurement you have to take.
No number in this directory is transferable.

### Architecture Patterns

Each example shows how to:
1. **Prevent the Inference Trap**: Route intelligently between lookup and reasoning
2. **Structure data for optimal retrieval**: Multi-dimensional indexing
3. **Design type-safe protocols**: Eliminate ambiguity
4. **Implement fallback strategies**: Graceful degradation
5. **Track structured metrics**: Observability without log parsing
6. **Optimize compute-to-lookup ratio**: Target 80-90% lookup, 10-20% reasoning
7. **Validate facts proactively**: Block hallucinations before generation
8. **Enable self-healing**: Systems that update themselves based on agent feedback

## Integration

These examples can be combined to build complete systems:

```python
from examples.guardrail_router_example import GuardrailRouter
from examples.compute_to_lookup_example import MultiTierLookupSystem
from examples.headless_agent_example import SilentSwarm, HeadlessAgent
from examples.semantic_firewall_example import SemanticFirewall, MultidimensionalKnowledgeGraph
from examples.recursive_ontology_example import RecursiveOntologySystem

# Combine patterns for optimal system
class OptimalAgenticSystem:
    def __init__(self):
        self.lookup_system = MultiTierLookupSystem()
        self.agent_swarm = SilentSwarm()
        self.recursive_ontology = RecursiveOntologySystem()
        self.firewall = self.recursive_ontology.semantic_firewall
        self.router = GuardrailRouter(max_reasoning_ratio=0.2)
        
    def process_request(self, query, agent_id, context):
        # Use Guardrail Router to prevent Inference Trap
        routing_decision = self.router.route(query)
        
        if routing_decision['reasoning_used']:
            # Reasoning path: Use silent swarm for complex processing
            workflow = self.decompose_to_tasks(query)
            results = self.agent_swarm.execute_workflow(workflow)
        else:
            # Lookup path: Try recursive ontology system first
            results = self.recursive_ontology.query(query, agent_id, context)
            
            # If not found, signals are automatically captured
            if not results['success']:
                # System will self-heal for future queries
                return self.generate_fallback_response()
        
        # Validate through semantic firewall
        validation = self.firewall.validate(results)
        if not validation.passed:
            # Hallucination detected - return safe fallback
            return self.generate_fallback_response(validation.reason)
        
        return results
        
    # Background task: Run healing cycle every 15 minutes
    def run_maintenance(self):
        self.recursive_ontology.run_healing_cycle()
```

## Further Reading

- [The Inference Trap Documentation](../docs/inference-trap.md)
- [Guardrail Router Documentation](../docs/guardrail-router.md)
- [Compute-to-Lookup Ratio Documentation](../docs/compute-to-lookup-ratio.md)
- [Multidimensional Knowledge Graphs Documentation](../docs/multidimensional-knowledge-graphs.md)
- [Semantic Firewall Documentation](../docs/semantic-firewall.md)
- [Headless Agent Documentation](../docs/headless-agent.md)
- [Silent Swarm Documentation](../docs/silent-swarm.md)
- [Recursive Ontologies Documentation](../docs/recursive-ontologies.md)
- [Cognitive Systems Architect Documentation](../docs/cognitive-systems-architect.md)
