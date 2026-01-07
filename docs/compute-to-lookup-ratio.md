# The Compute-to-Lookup Ratio: Why 90% of Your Agent's Work Should Be "Dumb" Lookup, Not "Smart" Reasoning

## Overview

The **Compute-to-Lookup Ratio** is a foundational principle in agentic architecture that challenges the conventional wisdom of AI system design. Rather than focusing on complex reasoning and computation, effective agents should prioritize efficient information retrieval and lookup operations.

## The 90/10 Rule

**Core Principle**: In well-designed agentic systems, approximately 90% of the agent's operations should be simple lookup and retrieval tasks, while only 10% should involve complex reasoning or computation.

### Why This Matters

1. **Performance & Latency**: Lookup operations are orders of magnitude faster than LLM inference
   - Database query: ~10-100ms
   - Vector similarity search: ~50-200ms
   - LLM inference: ~1-10 seconds

2. **Cost Efficiency**: Computational reasoning is expensive
   - Lookup operations: fractions of a cent
   - LLM inference: $0.001-$0.10 per request
   - At scale, the difference is dramatic

3. **Reliability**: Lookups are deterministic and predictable
   - No hallucinations in database queries
   - Consistent results from indexed data
   - Easier to debug and trace

4. **Scalability**: Lookup operations scale horizontally with ease
   - Add read replicas for databases
   - Distribute vector stores
   - Cache aggressively

## Architecture Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent Request                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   Intent Classifier   │  ◄── 10% Computation
          │    (Fast LLM/Model)   │
          └──────────┬───────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐         ┌──────────────┐
│  Query Router │         │ Direct Lookup│  ◄── 90% Lookup
│               │         │   Operations │
└───────┬───────┘         └──────┬───────┘
        │                        │
        ▼                        ▼
┌────────────────────────────────────────┐
│        Knowledge Store Layer           │
│  ┌──────────┐  ┌──────────┐  ┌──────┐│
│  │ Vector DB│  │  SQL DB  │  │Cache ││  ◄── 90% Lookup
│  └──────────┘  └──────────┘  └──────┘│
└────────────────────────────────────────┘
        │
        ▼
┌────────────────┐
│ Response       │
│ Assembly       │  ◄── 10% Computation
└────────────────┘
```

## Implementation Strategies

### 1. Pre-compute Everything Possible

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

### 2. Build Comprehensive Knowledge Graphs

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

### 3. Aggressive Caching Strategy

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

### 4. Semantic Indexing

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

## Metrics to Track

### Compute-to-Lookup Ratio (CLR)

```
CLR = (Time spent in LLM calls) / (Total request time)

Target: CLR < 0.1 (10%)
```

### Operation Breakdown

Track percentage of operations by type:
- **Lookup operations**: Database queries, vector searches, cache hits
- **Compute operations**: LLM calls, complex algorithms, data transformations

### Cost Analysis

```
Cost per request = (Lookup costs) + (Compute costs)

Ideal distribution:
- Lookup: 90% of operations, 10% of cost
- Compute: 10% of operations, 90% of cost
```

## Real-World Examples

### Example 1: Customer Support Agent

**Bad Approach** (Compute-heavy):
```python
def handle_support_ticket(ticket):
    # Everything goes through LLM
    ticket_analysis = llm.analyze(ticket)  # 2s
    knowledge_search = llm.search_knowledge(ticket_analysis)  # 3s
    solution = llm.generate_solution(knowledge_search)  # 2s
    # Total: 7 seconds, expensive
```

**Good Approach** (Lookup-heavy):
```python
def handle_support_ticket(ticket):
    # Fast semantic lookup
    ticket_embedding = embed(ticket.text)  # 50ms
    similar_tickets = vector_store.search(ticket_embedding)  # 100ms
    solutions = db.get_solutions(similar_tickets)  # 50ms
    
    # Only use LLM if no good match found
    if max(similar_tickets.scores) < 0.8:
        solution = llm.generate_solution(ticket, solutions)  # 2s (rare)
    else:
        solution = solutions[0]  # 0ms (common)
    # Average: 200ms, 10x faster, 10x cheaper
```

### Example 2: Code Assistant

**Bad Approach**:
```python
def suggest_code(context):
    # LLM generates from scratch every time
    suggestion = llm.generate_code(context)  # 5s, expensive
```

**Good Approach**:
```python
def suggest_code(context):
    # Lookup from indexed codebase
    context_embedding = embed(context)  # 50ms
    similar_code = code_index.search(context_embedding, top_k=10)  # 150ms
    
    # LLM only adapts existing code
    suggestion = llm.adapt_code(similar_code[0], context)  # 1s
    # Total: 1.2s, much more accurate
```

## Benefits of High Lookup Ratio

### 1. Predictable Performance
- Consistent response times
- Easy to capacity plan
- Clear performance characteristics

### 2. Lower Costs
- Database operations: $0.0001 per query
- Vector search: $0.001 per query
- LLM inference: $0.01-$0.10 per request

### 3. Better Reliability
- No hallucinations from database
- Version-controlled knowledge
- Deterministic behavior

### 4. Easier Debugging
- Clear data lineage
- Query logs are traceable
- No black-box reasoning

### 5. Privacy & Security
- Data stays in your infrastructure
- No sensitive data in LLM prompts
- Compliance-friendly

## Implementation Checklist

- [ ] Audit current system to measure compute-to-lookup ratio
- [ ] Identify computational bottlenecks
- [ ] Build comprehensive vector embeddings for semantic search
- [ ] Implement multi-tier caching strategy
- [ ] Pre-compute common query results
- [ ] Create knowledge graphs for structured relationships
- [ ] Reserve LLM usage for synthesis and adaptation only
- [ ] Monitor and optimize the ratio continuously
- [ ] Set up cost tracking per operation type
- [ ] Establish performance SLAs based on lookup operations

## Anti-Patterns to Avoid

### ❌ LLM-First Design
```python
# Every operation hits the LLM
def process(input):
    return llm.process(input)
```

### ❌ No Caching
```python
# Recomputing same results
def get_answer(question):
    return expensive_computation(question)  # No cache check
```

### ❌ Unstructured Knowledge
```python
# Dumping raw text into LLM context
def answer(question):
    all_docs = load_all_documents()  # Thousands of docs
    return llm.answer(question, all_docs)  # Inefficient
```

### ✅ Lookup-First Design
```python
# Lookup first, compute only when necessary
def process(input):
    cached = cache.get(input)
    if cached:
        return cached
    
    result = db.lookup(input)
    if result:
        return result
    
    # Last resort
    result = llm.process(input)
    cache.set(input, result)
    return result
```

## Conclusion

The Compute-to-Lookup Ratio is not about eliminating intelligent reasoning—it's about using it strategically. By structuring your agentic systems to prioritize fast, reliable lookups, you create systems that are:

- **10x faster**: Lookups are orders of magnitude quicker
- **10x cheaper**: Reduce LLM costs by 90%
- **10x more reliable**: Fewer hallucinations and errors
- **Infinitely more scalable**: Lookups scale horizontally with ease

Remember: The smartest agents aren't the ones that think the hardest—they're the ones that know where to look.

## Further Reading

- [Semantic Firewall Architecture](./semantic-firewall.md)
- [Headless Agent Patterns](./headless-agent.md)
- [Cognitive Systems Architect Role](./cognitive-systems-architect.md)
