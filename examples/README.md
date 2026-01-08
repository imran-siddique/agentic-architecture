# Examples

This directory contains working code examples demonstrating the key agentic architecture patterns.

## Available Examples

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

**Expected Output:**
- System should achieve 80-90% lookup ratio
- 70-90% cost savings vs all-reasoning approach
- Average latency under 500ms
- Detailed breakdown of routing decisions
- Demonstration of constraint enforcement

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

**Expected Output:**
- System should achieve >90% lookup ratio
- Average latency under 500ms
- Detailed breakdown by cache tier
- Cost comparison showing 10-100x savings

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

**Expected Output:**
- Complete workflow execution without any LLM calls
- 10-100x performance improvement over conversational
- 90%+ cost reduction
- Structured metrics showing deterministic behavior

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

**Expected Output:**
- Code review returning structured results without personality
- Authorization checks blocking unauthorized requests
- 10x faster performance vs conversational approach
- 95% cost reduction through minimal LLM usage
- 90% smaller attack surface

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

**Expected Output:**
- 100% correct validation of test cases
- Expired relationships blocked (e.g., "Steve Jobs is CEO of Apple")
- Unknown entities blocked
- Valid current facts allowed
- Historical facts validated with temporal context

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
```

## Key Insights

### Performance

These examples demonstrate:
- **Avoiding the Inference Trap**: Intelligent routing prevents unnecessary reasoning
- **10-100x speedup**: Through lookup optimization and eliminating language overhead
- **90%+ cost reduction**: By minimizing expensive LLM calls
- **Predictable performance**: Deterministic behavior with structured data
- **Zero hallucinations**: Through structural validation

### Architecture Patterns

Each example shows how to:
1. **Prevent the Inference Trap**: Route intelligently between lookup and reasoning
2. **Structure data for optimal retrieval**: Multi-dimensional indexing
3. **Design type-safe protocols**: Eliminate ambiguity
4. **Implement fallback strategies**: Graceful degradation
5. **Track structured metrics**: Observability without log parsing
6. **Optimize compute-to-lookup ratio**: Target 80-90% lookup, 10-20% reasoning
7. **Validate facts proactively**: Block hallucinations before generation

## Integration

These examples can be combined to build complete systems:

```python
from examples.guardrail_router_example import GuardrailRouter
from examples.compute_to_lookup_example import MultiTierLookupSystem
from examples.headless_agent_example import SilentSwarm, HeadlessAgent
from examples.semantic_firewall_example import SemanticFirewall, MultidimensionalKnowledgeGraph

# Combine patterns for optimal system
class OptimalAgenticSystem:
    def __init__(self):
        self.lookup_system = MultiTierLookupSystem()
        self.agent_swarm = SilentSwarm()
        self.knowledge_graph = MultidimensionalKnowledgeGraph()
        self.firewall = SemanticFirewall(self.knowledge_graph)
        self.router = GuardrailRouter(max_reasoning_ratio=0.2)
        
    def process_request(self, query):
        # Use Guardrail Router to prevent Inference Trap
        routing_decision = self.router.route(query)
        
        if routing_decision['reasoning_used']:
            # Reasoning path: Use silent swarm for complex processing
            workflow = self.decompose_to_tasks(query)
            results = self.agent_swarm.execute_workflow(workflow)
        else:
            # Lookup path: Fast retrieval
            results = routing_decision['data']
        
        # Validate through semantic firewall
        validation = self.firewall.validate(results)
        if not validation.passed:
            # Hallucination detected - return safe fallback
            return self.generate_fallback_response(validation.reason)
        
        return results
```

## Further Reading

- [The Inference Trap Documentation](../docs/inference-trap.md)
- [Guardrail Router Documentation](../docs/guardrail-router.md)
- [Compute-to-Lookup Ratio Documentation](../docs/compute-to-lookup-ratio.md)
- [Semantic Firewall Documentation](../docs/semantic-firewall.md)
- [Headless Agent Documentation](../docs/headless-agent.md)
- [Silent Swarm Documentation](../docs/silent-swarm.md)
- [Cognitive Systems Architect Documentation](../docs/cognitive-systems-architect.md)
