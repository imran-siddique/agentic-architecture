# Examples

This directory contains working code examples demonstrating the key agentic architecture patterns.

## Available Examples

### 1. Compute-to-Lookup Ratio (`compute_to_lookup_example.py`)

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

### 2. Headless Agent / Silent Swarm (`headless_agent_example.py`)

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

## Running All Examples

```bash
# Run all examples
python examples/compute_to_lookup_example.py
echo ""
python examples/headless_agent_example.py
```

## Key Insights

### Performance

These examples demonstrate:
- **10-100x speedup**: Through lookup optimization and eliminating language overhead
- **90%+ cost reduction**: By minimizing expensive LLM calls
- **Predictable performance**: Deterministic behavior with structured data

### Architecture Patterns

Each example shows how to:
1. **Structure data for optimal retrieval**: Multi-dimensional indexing
2. **Design type-safe protocols**: Eliminate ambiguity
3. **Implement fallback strategies**: Graceful degradation
4. **Track structured metrics**: Observability without log parsing
5. **Optimize compute-to-lookup ratio**: Target 90% lookup, 10% compute

## Integration

These examples can be combined to build complete systems:

```python
from examples.compute_to_lookup_example import MultiTierLookupSystem
from examples.headless_agent_example import SilentSwarm, HeadlessAgent

# Combine patterns for optimal system
class OptimalAgenticSystem:
    def __init__(self):
        self.lookup_system = MultiTierLookupSystem()
        self.agent_swarm = SilentSwarm()
        
    def process_request(self, query):
        # Use lookup-first strategy
        result = self.lookup_system.query(query)
        
        if result.source != 'llm':
            # Fast path: Retrieved from cache/DB
            return result
        
        # Slow path: Use silent swarm for complex processing
        workflow = self.decompose_to_tasks(query)
        results = self.agent_swarm.execute_workflow(workflow)
        
        # Cache result for future lookups
        self.lookup_system.cache_result(query, results)
        
        return results
```

## Further Reading

- [Compute-to-Lookup Ratio Documentation](../docs/compute-to-lookup-ratio.md)
- [Semantic Firewall Documentation](../docs/semantic-firewall.md)
- [Headless Agent Documentation](../docs/headless-agent.md)
- [Cognitive Systems Architect Documentation](../docs/cognitive-systems-architect.md)
