# Routing before reasoning

> Merged from three earlier documents: The Inference Trap, The Compute-to-Lookup
> Ratio, and The Guardrail Router. They described one pattern from three angles.

> The numbers in this document are worked examples on stated assumptions, or
> design targets. None of them are measurements. See the evidence standard in
> [CONTRIBUTING.md](../../CONTRIBUTING.md#evidence-standard).

## The problem

Engineers reach for a reasoning model on requests that are retrieval problems.
Ask a system "what is 2 + 2" and watch it verify the axioms of arithmetic, and
you are not looking at intelligence, you are looking at an architecture that
never decided what deserves computation.

This happens because there is no decision point. Requests arrive, the model is
the only component that can answer anything, so the model answers everything.
Latency, cost, and non-determinism then scale with total traffic rather than
with the share of traffic that actually needed a model.

Underneath is a misconception worth naming: that AI and search are independent,
or that AI replaces search. Better retrieval precedes better reasoning. If you
want an agent to summarise a page, you give it the page. You do not ask it to
find the page by thinking about it.

## The mechanism

Put a component in front of the model whose only job is to classify the request
and choose a path. It does not answer. It decides who answers.

```
                      Request
                         |
                         v
              +----------------------+
              |   Guardrail router   |   classification, no generation
              |  "does this need     |
              |     reasoning?"      |
              +----------+-----------+
                         |
          +--------------+--------------+
          |                             |
          v                             v
   Retrieval path                Reasoning path
   cache, index, graph,          novel synthesis only
   database                      result written back
                                 to the retrieval tier
```

Three things make this more than a cache lookup.

**Classification is cheap.** Pattern match first, small classifier second, model
never. A classifier that costs a model call has moved the trap, not removed it.

```python
def classify(request: str) -> str:
    # Fast pattern match, roughly a millisecond
    result = pattern_classifier.classify(request)
    if result.confidence > 0.9:
        return result.category

    # Small model only for the uncertain tail
    return ml_classifier.classify(request)
```

**The budget is enforced, not hoped for.** A ratio you only measure is a ratio
that drifts. Make it a constraint that can refuse.

```python
class ConstraintEnforcer:
    """Hard limit on the share of requests allowed to reason."""

    def __init__(self, max_reasoning_ratio: float = 0.2) -> None:
        self.max_reasoning_ratio = max_reasoning_ratio
        self.reasoning_count = 0
        self.total_count = 0

    def can_use_reasoning(self) -> bool:
        if self.total_count == 0:
            return True
        return (self.reasoning_count / self.total_count) < self.max_reasoning_ratio

    def record(self, used_reasoning: bool) -> None:
        self.total_count += 1
        if used_reasoning:
            self.reasoning_count += 1
```

**Reasoning results are written back.** Every answer the model produces becomes
a lookup for the next caller. The ratio improves on its own, or you learn that
your traffic is genuinely novel, which is also worth knowing.

## Implementation detail

The material below is retained from the three source documents.

### The tiers behind the retrieval path

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent Request                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   Intent Classifier  │  <-- classification
          │    (Fast LLM/Model)   │
          └──────────┬───────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐         ┌──────────────┐
│  Query Router │         │ Direct Lookup│  <-- retrieval
│               │         │   Operations │
└───────┬───────┘         └──────┬───────┘
        │                        │
        ▼                        ▼
┌────────────────────────────────────────┐
│        Knowledge Store Layer           │
│  ┌──────────┐  ┌──────────┐  ┌──────┐│
│  │ Vector DB│  │  SQL DB  │  │Cache ││  <-- retrieval
│  └──────────┘  └──────────┘  └──────┘│
└────────────────────────────────────────┘
        │
        ▼
┌────────────────┐
│ Response       │
│ Assembly       │  <-- classification
└────────────────┘
```

### Filling the retrieval path

#### Pre-compute what you can

Instead of computing answers on-demand, pre-compute and index:

```python
# Bad: Compute-heavy approach
def get_user_recommendations(user_id):
    user_data = llm.analyze_user_profile(user_id)  # Expensive
    preferences = llm.extract_preferences(user_data)  # Expensive
    recommendations = llm.generate_recommendations(preferences)  # Expensive
    return recommendations

# Good: Lookup-heavy approach
def get_user_recommendations(user_id):
    # Pre-computed embeddings stored in vector DB
    user_embedding = vector_store.get_user_embedding(user_id)  # Fast
    similar_users = vector_store.similarity_search(user_embedding, k=10)  # Fast
    recommendations = cache.get_aggregated_preferences(similar_users)  # Fast
    return recommendations
```

#### Structure knowledge for traversal

Structure information for rapid traversal:

```python
# Knowledge graph allows O(1) or O(log n) lookups
class KnowledgeGraph:
    def get_entity_relationships(self, entity_id):
        # Direct index lookup
        return self.adjacency_index[entity_id]
    
    def find_path(self, start, end, max_hops=3):
        # Pre-computed shortest paths
        return self.path_cache.get(f"{start}:{end}")
```

#### Cache in tiers

Cache at multiple levels:

```
┌─────────────────────┐
│   L1: Memory Cache   │  <-- Hot data, millisecond access
├─────────────────────┤
│   L2: Redis Cache    │  <-- Warm data, sub-10ms access
├─────────────────────┤
│ L3: Vector Store     │  <-- Semantic search, ~100ms
├─────────────────────┤
│ L4: Primary DB       │  <-- Full data, ~100-500ms
├─────────────────────┤
│ L5: LLM Computation  │  <-- Last resort, 1-10s
└─────────────────────┘
```

#### Index unstructured data once

Convert unstructured data to structured, searchable indices:

```python
# Embed and index documents once
documents = load_documents()
embeddings = embedding_model.encode(documents)
vector_store.index(embeddings, metadata=documents)

# Fast semantic lookup (90% of queries)
def answer_question(question):
    query_embedding = embedding_model.encode(question)
    relevant_docs = vector_store.search(query_embedding, top_k=5)
    
    # Only use LLM for final synthesis (10% of work)
    answer = llm.synthesize(question, relevant_docs)
    return answer
```

### A complete router

The main routing logic that ties everything together:

```python
class GuardrailRouter:
    """
    Main router that decides between lookup and reasoning.
    
    Target Ratio: 80-90% lookup, 10-20% reasoning
    """
    
    def __init__(self, 
                 lookup_handler, 
                 reasoning_handler,
                 max_reasoning_ratio=0.2):
        self.classifier = RequestClassifier()
        self.constraints = ConstraintEnforcer(max_reasoning_ratio)
        self.lookup_handler = lookup_handler
        self.reasoning_handler = reasoning_handler
        
        # Metrics
        self.metrics = {
            'total_requests': 0,
            'lookup_requests': 0,
            'reasoning_requests': 0,
            'constraint_blocks': 0,
            'total_latency': 0,
            'total_cost': 0
        }
    
    def route(self, request: str):
        """
        Main routing logic.
        
        1. Classify the request
        2. Check constraints
        3. Route to appropriate handler
        4. Track metrics
        """
        self.metrics['total_requests'] += 1
        start_time = time.time()
        
        # Step 1: Try lookup first (always)
        lookup_result = self.lookup_handler.try_lookup(request)
        if lookup_result.found:
            # Fast path - found in lookup
            self.constraints.record_lookup()
            self.metrics['lookup_requests'] += 1
            self._record_metrics(time.time() - start_time, lookup_result.cost)
            return lookup_result.data
        
        # Step 2: Classify if reasoning might be needed
        should_reason = self.classifier.should_use_reasoning(request)
        
        if not should_reason:
            # Lookup expected but not found - return error or fallback
            self.constraints.record_lookup()
            self.metrics['lookup_requests'] += 1
            return self._handle_lookup_miss(request)
        
        # Step 3: Check if reasoning is allowed
        if not self.constraints.can_use_reasoning():
            # Over reasoning budget - force to lookup
            self.metrics['constraint_blocks'] += 1
            self.constraints.record_lookup()
            self.metrics['lookup_requests'] += 1
            return self._handle_constraint_block(request)
        
        # Step 4: Use reasoning (allowed and necessary)
        reasoning_result = self.reasoning_handler.process(request)
        self.constraints.record_reasoning()
        self.metrics['reasoning_requests'] += 1
        self._record_metrics(time.time() - start_time, reasoning_result.cost)
        
        # Step 5: Cache reasoning result for future lookups
        self.lookup_handler.cache(request, reasoning_result.data)
        
        return reasoning_result.data
    
    def _handle_lookup_miss(self, request: str):
        """
        Handle case where lookup was expected but not found.
        """
        return {
            'error': 'Information not found',
            'request': request,
            'suggestion': 'This appears to be a factual query. Please add to knowledge base.'
        }
    
    def _handle_constraint_block(self, request: str):
        """
        Handle case where reasoning is blocked by constraints.
        """
        return {
            'error': 'Reasoning quota exceeded',
            'request': request,
            'current_ratio': self.constraints.get_ratio(),
            'max_ratio': self.constraints.max_reasoning_ratio,
            'suggestion': 'System is over reasoning budget. Improve knowledge base coverage.'
        }
    
    def _record_metrics(self, latency: float, cost: float):
        """Record performance metrics"""
        self.metrics['total_latency'] += latency
        self.metrics['total_cost'] += cost
    
    def get_metrics(self):
        """
        Get comprehensive metrics.
        """
        total = self.metrics['total_requests']
        if total == 0:
            return {'status': 'No requests processed yet'}
        
        lookup_ratio = self.metrics['lookup_requests'] / total
        reasoning_ratio = self.metrics['reasoning_requests'] / total
        avg_latency = self.metrics['total_latency'] / total
        avg_cost = self.metrics['total_cost'] / total
        
        return {
            'total_requests': total,
            'lookup_count': self.metrics['lookup_requests'],
            'reasoning_count': self.metrics['reasoning_requests'],
            'lookup_ratio': lookup_ratio,
            'reasoning_ratio': reasoning_ratio,
            'target_met': reasoning_ratio <= self.constraints.max_reasoning_ratio,
            'constraint_blocks': self.metrics['constraint_blocks'],
            'avg_latency_ms': avg_latency * 1000,
            'avg_cost': avg_cost,
            'total_cost': self.metrics['total_cost']
        }
```

### What the operator sees

```
╔══════════════════════════════════════════════════════════════╗
║              Guardrail Router Dashboard                      ║
╠══════════════════════════════════════════════════════════════╣
║ Ratio Status                                                 ║
║   Current: 8% reasoning, 92% lookup     [✓ Target Met]      ║
║   Target:  ≤10% reasoning               [Within Bounds]      ║
║                                                              ║
║ Volume (Last Hour)                                           ║
║   Total Requests:     10,000                                 ║
║   Lookup:              9,200 (92%)                           ║
║   Reasoning:             800 (8%)                            ║
║   Constraint Blocks:      12 (0.1%)                          ║
║                                                              ║
║ Performance                                                  ║
║   Avg Latency:        150ms                                  ║
║   P95 Latency:        500ms                                  ║
║   P99 Latency:      2,100ms  (reasoning calls)               ║
║                                                              ║
║ Cost                                                         ║
║   Total Cost:         $12.00                                 ║
║   Per Request:      $0.0012                                  ║
║   Savings vs All-Reasoning: $88.00 (88%)                     ║
║                                                              ║
║ Quality                                                      ║
║   Cache Hit Rate:      85%                                   ║
║   Lookup Miss Rate:     7%                                   ║
║   Constraint Blocks:  0.1%                                   ║
╚══════════════════════════════════════════════════════════════╝
```

### When reasoning earns its cost

Reasoning should be reserved for tasks that truly require synthesis, such as:

1. **Novel Problem Solving**: Problems that have never been solved before
2. **Complex Synthesis**: Combining multiple pieces of information in new ways
3. **Creative Generation**: Generating truly novel content
4. **Adaptation**: Modifying existing solutions for new contexts

### When it does not

Reasoning should NOT be used for:

1. **Factual Lookup**: "What is the capital of France?"
2. **Documentation Queries**: "How do I call this API?"
3. **Historical Data**: "What happened in 1969?"
4. **Cached Results**: "Show me recommendations for user X" (if already computed)
5. **Structured Queries**: "Get all orders from last month"

## The invariant

> When the reasoning budget is exhausted, no request reaches the reasoning path,
> regardless of how the request is phrased.

That is testable without a model: drive the router past its budget and assert
the reasoning engine was never called.

Everything else this pattern is credited with, latency, cost, predictability,
follows from the routing ratio and from your unit prices. Those are
measurements you take, not properties you inherit.

### What the budget does not do

Writing the test for the invariant above surfaced its limit, so it belongs here
rather than in a footnote.

A blocked request is recorded as a lookup. That lowers the ratio, which restores
headroom, so a caller who is refused and simply asks again eventually reaches
the reasoning path. The budget is a **rate limit with immediate recovery**, not
an access control.

That is correct for a cost control and wrong for a security boundary. If
something must never happen, it belongs in a capability check that does not
recover, not in a ratio. See [Silent execution](./silent-execution.md).

`tests/test_routing_invariants.py::test_a_denied_caller_gets_through_by_retrying`
pins this, so it cannot quietly become something people rely on.

## The test

`tests/test_routing_invariants.py` covers:

- The budget engages at all, so the rest of the suite is not vacuous.
- While the budget is spent, four phrasings, two of which read as social
  engineering, all fail to reach the reasoning engine. Asserted against a spy on
  the handler, not against the returned dict.
- A blocked request says why rather than answering.
- The retry path above, deliberately.
- A known answer never reaches the reasoning path.
- A reasoning result is written back and serves the next caller, asserted by
  call count rather than by output.
- An unclassifiable request takes the cheap path.
- A factual miss returns nothing rather than reasoning about it.

## When not to use this

- **Genuinely novel traffic.** If most requests have never been asked before,
  the router adds a hop and returns nothing. Measure your repeat rate first.
- **Correctness dominates cost.** A stale cache hit that looks fresh is worse
  than a slow correct answer. Routing needs an invalidation story before it
  needs a ratio.
- **Small volume.** At a hundred requests a day the router is more code to
  maintain than the spend it saves.
- **The classifier is the hard part.** If deciding whether a request needs
  reasoning is itself a reasoning problem, you have not simplified anything.

## What to measure

| Signal | Why it matters |
|---|---|
| Reasoning share of requests | The ratio the constraint exists to hold |
| p50 and p99 latency, split by route | A fast average can hide a slow reasoning tail |
| Cost per completed task | Cost per call falls trivially by refusing to answer |
| Cache hit rate, and staleness of hits | A high hit rate on stale data is a failure wearing a success costume |
| Rate the constraint fired | If it never fires, it is not a constraint |

## Anti-patterns

**No router.** Every request goes to the model, and the ratio is whatever the
traffic happens to be.

**Router without constraints.** The ratio is measured, reported, and never
enforced. It drifts up, because every individual decision to reason looks
locally reasonable.

**Classifier that reasons.** Deciding the route costs a model call, so the
expensive step now runs on every request including the cheap ones.

**Ignoring the metrics you collect.** The dashboard shows 40% reasoning, has
shown 40% for two quarters, and nobody owns it.

## Reference implementations

| Component | Where it exists as running code |
|---|---|
| Policy evaluation outside the model process | [cMCP](https://github.com/agentrust-io/cmcp), a policy-enforcing MCP proxy |
| Capability scoping for what an agent may call | [Agent Manifest](https://github.com/agentrust-io/agent-manifest) |
| Policy kernel and enforcement patterns | [Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit) |

None of these is a router. They are where the enforcement half of this pattern
is implemented and maintained, which is the half people skip.

## Run the example

```bash
python examples/guardrail_router_example.py
python examples/compute_to_lookup_example.py
```

Both are simulations. They call no model, and every latency and cost they print
is a constant in the file.

## Related patterns

- [Grounded context](./grounded-context.md), for building the retrieval path and policing what it returns
- [Silent execution](./silent-execution.md), for what happens after the route is chosen
- [The Evidence Plane](../evidence-plane.md), for making the decision checkable afterwards

The remaining patterns have not been merged into this catalog yet. The
[catalog index](../README.md) tracks which are done.
