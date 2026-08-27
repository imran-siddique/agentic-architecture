# Quick Start Guide

Get started with agentic architecture patterns in 5 minutes.

## What You'll Learn

Four patterns for building agent systems that are easier to constrain,
observe, and verify. Each one states an invariant that can fail, and each has a
test suite that fails with it.

1. **[Routing before reasoning](./docs/patterns/routing.md)**: classify the request before you answer it, and enforce the reasoning budget as a constraint rather than a metric
2. **[Grounded context](./docs/patterns/grounded-context.md)**: filter by rule rather than by similarity, block claims the graph cannot support, and rebuild the graph from the failures it produces
3. **[Silent execution](./docs/patterns/silent-execution.md)**: language at the boundary, capability at the workers, never in the same component
4. **[Enforcement and evidence](./docs/patterns/enforcement-and-evidence.md)**: put the rule where the model cannot argue with it, then emit a receipt somebody else can check

Plus [The Cognitive Systems Architect](./docs/cognitive-systems-architect.md),
a role essay rather than a pattern.

Each pattern also says when not to use it, and what it does not do. Those
sections are usually the useful ones.

## 5-Minute Quick Start

### Step 1: Understand the Philosophy (1 minute)

The core insight: **If your agent is "thinking" for every request, you have not built an agent, you have built a philosophy major.**

But there's more: **If your knowledge graph needs manual updates, you have not built a system, you have built a maintenance nightmare.**

Without a routing decision:
```
User Query → LLM thinks hard for everything → Response (slow, expensive, unreliable)
```

With one:
```
User Query → Router → Does this need reasoning?
                          ↓                ↓
                    Retrieval path    Reasoning path
                    the large share   the small share, budgeted

The split, the latencies, and the prices are yours to measure. The point is
that there is a decision, and that it is visible and testable.
```

### Step 2: Run the Examples (2 minutes)

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/imran-siddique/agentic-architecture.git
cd agentic-architecture

# Run examples to see the patterns in action
python examples/guardrail_router_example.py
python examples/compute_to_lookup_example.py
python examples/multidimensional_kg_example.py
python examples/semantic_firewall_example.py
python examples/headless_agent_example.py
python examples/silent_swarm_example.py
python examples/recursive_ontology_example.py  # New: Self-updating systems
```

Each example prints a simulated walkthrough of its pattern. The latencies and
costs are constants written into the example so the control flow is readable.
They are not measurements of anything, and nothing here calls a model.

What the examples actually show you:
- How a router decides between the lookup path and the reasoning path
- How a validator rejects a claim the knowledge graph does not support
- How agents coordinate over typed messages instead of prose
- How a receipt fails verification when the artifact or the decision changes
- How a knowledge graph is rebuilt from failure signals

Only `examples/evidence_plane_example.py` is backed by tests that can fail.
See `tests/test_evidence_plane.py`.

### Step 3: Read One Concept (2 minutes)

Pick the concept most relevant to your current challenge:

**If you're using expensive reasoning for everything, or you need to decide
when reasoning is worth it, or you want to cut cost and latency:**
→ Read [Routing before reasoning](./docs/patterns/routing.md)

**If you need context precision, if you struggle with hallucinations, or if
your knowledge goes stale faster than anyone can curate it:**
→ Read [Grounded context](./docs/patterns/grounded-context.md)

**If inter-agent coordination is slow, or you want an agent architecture whose
security is structural rather than a prompt:**
→ Read [Silent execution](./docs/patterns/silent-execution.md)

**If safety currently lives in a prompt, or you need to prove to somebody else
that a policy actually ran:**
→ Read [Enforcement and evidence](./docs/patterns/enforcement-and-evidence.md)

**If you're designing a new system:**
→ Read [Cognitive Systems Architect](./docs/cognitive-systems-architect.md)

## Worked Scenarios

These are illustrations of how the patterns compose, not case studies. Nobody
ran these systems. Each one ends with what you would have to measure to know
whether it worked.

### Scenario 1: Customer Support Bot

**Problem**: Slow responses, hallucinated information, expensive LLM costs

**Solution**: Apply all three patterns
```python
# 1. Pre-compute common queries (Compute-to-Lookup)
support_kb.index_common_questions(tickets)

# 2. Validate responses (Semantic Firewall)
response = support_agent.generate(query)
validation = firewall.validate(response)

# 3. Use headless agents for complex workflows
if validation.passed:
    workflow = [FetchTicket, AnalyzeHistory, SuggestSolution]
    result = silent_swarm.execute(workflow)
```

**What to measure**:
- Share of queries served from cache, and p50 and p99 latency for each route
- Rate at which the firewall blocks a response, and how many blocks were correct
- Cost per resolved ticket, not cost per call

### Scenario 2: E-commerce Recommendation

**Problem**: Recommendations take 3-5 seconds to generate

**Solution**: Pre-compute everything
```python
# Compute-to-Lookup Ratio pattern
# Pre-compute user embeddings nightly
user_embeddings = precompute_user_preferences()

# Real-time lookup (50ms)
def get_recommendations(user_id):
    embedding = user_embeddings[user_id]  # Lookup
    similar_users = vector_store.search(embedding)  # Lookup
    return cached_recommendations[similar_users]  # Lookup
```

**What to measure**:
- End to end latency, including the nightly precompute you now depend on
- Recommendation quality against your existing metric, since precomputation
  trades freshness for speed and that trade can lose you money
- Cost of the precompute job, which is real and often forgotten

### Scenario 3: Clinical Decision Support

**Problem**: Can't afford hallucinations in healthcare

**Solution**: Semantic Firewall with strict validation
```python
# Build medical knowledge graph
kg = MedicalKnowledgeGraph()
kg.add_validated_symptoms()
kg.add_validated_conditions()
kg.add_validated_treatments()

# Strict validation rules
firewall = SemanticFirewall(kg)
firewall.min_confidence = 0.98  # Very high threshold
firewall.min_sources = 3  # Multiple medical sources required

# Every response validated
diagnosis = medical_llm.diagnose(symptoms)
validation = firewall.validate(diagnosis)

if not validation.passed:
    # Block and log for review
    return safe_fallback_response()
```

**What this does and does not give you**:
- It blocks claims the graph cannot support. It does not make the graph correct,
  and a confidence threshold is not a safety argument.
- It produces an audit trail. Whether that trail satisfies a given regulator is
  a question for that regulator, not for this pattern.
- A high threshold shifts the failure mode from wrong answers to refused
  answers. In a clinical setting that trade needs its own review.

Do not deploy this pattern in a clinical setting on the strength of a
repository of architecture notes.

## Implementation Checklist

### Phase 0: Diagnosis (Day 1)
- [ ] Identify if you're falling into the Inference Trap
- [ ] Measure current reasoning vs lookup ratio
- [ ] Calculate cost of all-reasoning approach
- [ ] Identify queries that should be lookups

### Phase 1: Foundation (Week 1)
- [ ] Implement basic Guardrail Router
- [ ] Audit current system to measure compute-to-lookup ratio
- [ ] Identify top 100 most common queries
- [ ] Set up caching infrastructure (Redis or similar)
- [ ] Build initial knowledge graph with core entities

### Phase 2: Optimization (Week 2)
- [ ] Pre-compute common query results
- [ ] Implement semantic indexing for queries
- [ ] Add vector similarity search
- [ ] Fine-tune Guardrail Router classification
- [ ] Target: Achieve 80% lookup ratio

### Phase 3: Validation (Week 3)
- [ ] Implement semantic firewall
- [ ] Define validation rules for your domain
- [ ] Set confidence thresholds
- [ ] Track blocked hallucinations
- [ ] Monitor Guardrail Router metrics

### Phase 4: Agent Coordination (Week 4)
- [ ] Identify conversational bottlenecks between agents
- [ ] Design structured protocols for agent communication
- [ ] Convert high-frequency agent pairs to headless
- [ ] Measure performance improvements

### Phase 5: Monitoring (Ongoing)
- [ ] Set up structured telemetry
- [ ] Monitor compute-to-lookup ratio
- [ ] Track hallucination block rate
- [ ] Measure cost per request
- [ ] Optimize continuously

## Key Metrics to Track

### 1. Compute-to-Lookup Ratio
```
Target: ≤ 0.1 (10% compute, 90% lookup)
Current: _______
```

### 2. Response Latency
```
Target: p95 < 500ms
Current: _______
```

### 3. Cost per Request
```
Target: < $0.001
Current: _______
```

### 4. Hallucination Block Rate
```
Target: Block all hallucinations (100% validation)
Current: _______
```

### 5. Knowledge Coverage
```
Target: > 95% of queries covered in knowledge graph
Current: _______
```

## Anti-Patterns to Avoid

### Don't: Use LLM for Everything
```python
# Bad: Every query hits expensive LLM
def answer(question):
    return llm.generate(question)  # $0.01, 2000ms
```

### Do: Lookup First, Compute Last
```python
# Good: Tiered fallback strategy
def answer(question):
    if cached := cache.get(question):
        return cached  # $0.0001, 1ms
    
    if similar := vector_search(question):
        return similar  # $0.001, 100ms
    
    result = llm.generate(question)  # $0.01, 2000ms (rare)
    cache.set(question, result)
    return result
```

### Don't: Hope LLM Doesn't Hallucinate
```python
# Bad: No validation
def get_facts(query):
    facts = llm.extract_facts(query)
    return facts  # Might be hallucinated!
```

### Do: Validate Against Knowledge
```python
# Good: Validate all facts
def get_facts(query):
    facts = llm.extract_facts(query)
    validation = firewall.validate(facts)
    
    if validation.passed:
        return facts
    else:
        return fallback_to_known_facts()
```

### Don't: Use Natural Language Between Agents
```python
# Bad: Agents chat with each other
agent1.send("I found 5 customers matching criteria")
agent2.parse("5 customers")  # Expensive, error-prone
```

### Do: Use Structured Data
```python
# Good: Agents exchange typed data
agent1.send(CustomerSearchResult(
    customer_ids=[1, 2, 3, 4, 5],
    count=5
))  # Fast, type-safe, deterministic
```

## Getting Help

### Documentation
- [Compute-to-Lookup Ratio](./docs/patterns/routing.md) - Full guide
- [Semantic Firewall](./docs/patterns/grounded-context.md) - Validation patterns
- [Silent execution](./docs/patterns/silent-execution.md) - Silent swarm architecture
- [Cognitive Systems Architect](./docs/cognitive-systems-architect.md) - The new role

### Examples
- [examples/compute_to_lookup_example.py](./examples/compute_to_lookup_example.py) - Multi-tier caching
- [examples/headless_agent_example.py](./examples/headless_agent_example.py) - Silent swarms
- [examples/semantic_firewall_example.py](./examples/semantic_firewall_example.py) - Validation

### Community
- Open issues for questions
- Share your implementation experiences
- Contribute examples and patterns

## Next Steps

1. **Run the examples** to see the patterns in action
2. **Pick one pattern** to implement first (start with Compute-to-Lookup)
3. **Measure before and after** to quantify improvements
4. **Iterate and optimize** based on metrics
5. **Share your results** to help others

## Report what you find

There are no case studies here yet. When there are, they will name the
workload, the environment, and the measurement, because a quote without those
is not evidence.

If you run one of these patterns, open an
[experience report](https://github.com/imran-siddique/agentic-architecture/issues/new?template=experience-report.yml).
The parts worth reading are usually the parts that did not work.

## Remember

The goal is not to eliminate AI. It is to use it deliberately:
- **90% of work**: Fast, reliable lookups
- **10% of work**: Smart reasoning for novel cases
- **100% of output**: Validated against knowledge

**Start small, measure everything, optimize continuously.**

---

Ready to build faster, cheaper, and more reliable AI systems? Start with the examples!
