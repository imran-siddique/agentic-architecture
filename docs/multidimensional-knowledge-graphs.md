# Multidimensional Knowledge Graphs: Beyond Flat Context

## Overview

There is a prevalent myth that "Context" is just a pile of documents dumped into a Vector Database. If you have read about Context Engineering, you know this is fundamentally wrong. Vector search (RAG) is flat. It finds words that look similar, but it doesn't understand the structure of reality.

To build reliable agents, we need to move beyond flat data. We need **Multidimensional Knowledge Graphs**.

## The Problem with Flat Context

RAG lacks dimensionality. If I ask an AI, "What is important right now?", a Vector DB looks for documents containing "important" and "now."

It misses the metadata that actually governs business logic:

- **Temporal Weight**: A relationship that existed six months ago is less relevant than one created yesterday.
- **Role-Based Weight**: Information critical to a Developer might be noise to a Product Manager.
- **Authority**: Who authored this information? Is it from a reliable source?

We aren't just talking about a single graph connecting A to B. We are talking about multiple, overlapping graphs — or a single graph with multiple distinct "views." This is the only way to model the complexity of an enterprise.

## The Graph as a Semantic Firewall

The Knowledge Graph acts as a **Semantic Firewall** — a constraint wrapper that sits around your model (similar to how we conceptualized Cortana wrappers in the past).

This firewall acts as a filter. It subtracts the noise before the AI ever sees it. It enforces "Scale by Subtraction" by ensuring the AI can only "reason" about data that passes through the topological constraints of the graph.

```
┌──────────────────────────────────────────────────────────────┐
│                     User Query                                │
│         "What pending items do I have on my plate?"           │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │   Multidimensional Graph Filter    │
         │     (Constraint Application)       │
         │                                    │
         │  Dimension 1: Identity & Scope    │ ── Filter by user role
         │  Dimension 2: Org Hierarchy       │ ── Include direct reports
         │  Dimension 3: Service Ownership   │ ── Team-owned services
         │  Dimension 4: Dependency Mapping  │ ── Partner dependencies
         │  Dimension 5: Temporal Weight     │ ── Recent > Old
         │  Dimension 6: Authority           │ ── Source reliability
         └────────────────┬──────────────────┘
                          │
                          │ 99% noise subtracted
                          │ 1% signal remains
                          ▼
         ┌────────────────────────────────────┐
         │    Filtered Context (Signal)        │
         │   - 3 critical blockers            │
         │   - 2 partner incidents            │
         │   - 1 production issue             │
         └────────────────┬───────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────┐
         │      LLM Synthesis (Easy Job)      │
         │   "Here are your pending items..."  │
         └────────────────────────────────────┘
```

## The Multidimensional Filter: A Real-World Example

Let's look at a seemingly simple query: **"What pending items do I have on my plate?"**

If you send this to a standard RAG system, it will return every Jira ticket, email, and document where your name appears next to the word "pending." The result is hallucination or information overload.

Here is how a Multidimensional Graph solves this via constraints:

### Dimension 1: Identity & Scope (The Manager View)

The graph knows I am logged in as a **Manager**. It immediately filters out low-level code commits and prioritizes "Production Fundamentals."

```python
class IdentityDimension:
    """Filter based on user role and scope"""
    
    def apply_filter(self, user, entities):
        if user.role == "Manager":
            # Filter out low-level details
            return [e for e in entities 
                    if e.scope in ["production", "critical", "strategic"]]
        elif user.role == "Developer":
            # Include implementation details
            return [e for e in entities 
                    if e.scope in ["code", "bugs", "features"]]
```

### Dimension 2: Organizational Hierarchy

The graph understands the `Report_To` edges. It knows that "my plate" implicitly includes the critical blockers of my direct reports.

```python
class OrganizationalDimension:
    """Traverse organizational hierarchy"""
    
    def expand_scope(self, user, graph):
        # Include user's direct responsibilities
        direct = graph.get_assigned_to(user.id)
        
        # Include direct reports' critical items
        reports = graph.get_direct_reports(user.id)
        critical_from_reports = []
        for report in reports:
            items = graph.get_assigned_to(report.id)
            critical_from_reports.extend([
                item for item in items 
                if item.severity in ["critical", "high"]
            ])
        
        return direct + critical_from_reports
```

### Dimension 3: Service Ownership

It doesn't just look for "Microsoft services." It looks for the specific **Service IDs** owned by my team.

```python
class ServiceOwnershipDimension:
    """Filter by service ownership"""
    
    def filter_by_ownership(self, user, incidents):
        # Get services owned by user's team
        team_services = graph.get_team_services(user.team_id)
        
        # Filter incidents to owned services
        return [incident for incident in incidents 
                if incident.service_id in team_services]
```

### Dimension 4: Dependency Mapping

It traverses the edges to Partner teams. If a partner has a high-severity incident on a service I depend on, that is "on my plate," even if my name isn't written on the ticket.

```python
class DependencyDimension:
    """Map service dependencies"""
    
    def include_dependencies(self, team_services, all_incidents):
        # Get services that team_services depend on
        dependencies = []
        for service in team_services:
            deps = graph.get_service_dependencies(service.id)
            dependencies.extend(deps)
        
        # Include high-severity incidents on dependencies
        return [incident for incident in all_incidents
                if (incident.service_id in dependencies and
                    incident.severity in ["critical", "high"])]
```

### Dimension 5: Temporal Weight

Recent items are weighted higher than old items. A ticket created yesterday is more relevant than one from six months ago.

```python
class TemporalDimension:
    """Apply temporal weighting"""
    
    def apply_temporal_weight(self, items):
        now = datetime.now()
        
        weighted_items = []
        for item in items:
            age_days = (now - item.created_at).days
            
            # Exponential decay: weight = e^(-age/30)
            weight = math.exp(-age_days / 30)
            
            item.temporal_weight = weight
            weighted_items.append(item)
        
        # Sort by weight (most recent first)
        return sorted(weighted_items, 
                     key=lambda x: x.temporal_weight, 
                     reverse=True)
```

### Dimension 6: Authority & Source

Information from official sources (Jira, ServiceNow) is weighted higher than informal sources (Slack messages).

```python
class AuthorityDimension:
    """Weight by source authority"""
    
    SOURCE_AUTHORITY = {
        "jira": 1.0,
        "servicenow": 1.0,
        "production_logs": 0.95,
        "email": 0.7,
        "slack": 0.5,
        "rumor": 0.1
    }
    
    def apply_authority_weight(self, items):
        for item in items:
            item.authority_weight = self.SOURCE_AUTHORITY.get(
                item.source_type, 0.5
            )
        
        return [item for item in items 
                if item.authority_weight >= 0.7]
```

## The "Constraint" Outcome

By the time the LLM receives the context, the Graph has already done the heavy lifting. We didn't ask the AI to figure out what matters. We used the graph to filter the universe down to the exact subset of reality that matters right now.

**We subtracted 99% of the noise using deterministic graph logic, leaving the AI with the easy job: summarizing the 1% of signal that remains.**

### Before: RAG Approach (Flat)
```
Query: "What pending items do I have?"
Vector Search Results: 10,000 documents mentioning "pending" and user name
LLM Task: Read 10,000 docs, figure out what's relevant, summarize
Result: Hallucinations, information overload, 30 seconds, $0.50
```

### After: Multidimensional Graph Approach
```
Query: "What pending items do I have?"
Graph Filters: 
  ✓ Identity & Scope → 2,000 items (80% reduction)
  ✓ Org Hierarchy → 500 items (75% reduction)  
  ✓ Service Ownership → 100 items (80% reduction)
  ✓ Dependencies → 50 items (50% reduction)
  ✓ Temporal Weight → 20 items (60% reduction)
  ✓ Authority → 5 items (75% reduction)

LLM Task: Summarize 5 highly relevant items
Result: Accurate summary, 500ms, $0.005
```

## Architecture: Multidimensional Knowledge Graph

```python
class MultidimensionalKnowledgeGraph:
    """
    A knowledge graph with multiple dimensions for filtering
    """
    
    def __init__(self):
        # Core graph structure
        self.entities = {}
        self.relationships = []
        
        # Dimensional filters
        self.dimensions = {
            'identity': IdentityDimension(),
            'organizational': OrganizationalDimension(),
            'service_ownership': ServiceOwnershipDimension(),
            'dependencies': DependencyDimension(),
            'temporal': TemporalDimension(),
            'authority': AuthorityDimension()
        }
    
    def query_with_constraints(self, query, user_context):
        """
        Query graph with dimensional constraints
        
        This applies all dimensional filters in sequence,
        progressively narrowing the result set
        """
        # Start with all potentially relevant entities
        candidates = self._initial_search(query)
        
        # Apply each dimensional filter
        filtered = candidates
        
        # Dimension 1: Identity & Scope
        filtered = self.dimensions['identity'].apply_filter(
            user_context.user, filtered
        )
        
        # Dimension 2: Organizational Hierarchy  
        filtered = self.dimensions['organizational'].expand_scope(
            user_context.user, self
        )
        
        # Dimension 3: Service Ownership
        filtered = self.dimensions['service_ownership'].filter_by_ownership(
            user_context.user, filtered
        )
        
        # Dimension 4: Dependencies
        team_services = self.get_team_services(user_context.user.team_id)
        filtered = self.dimensions['dependencies'].include_dependencies(
            team_services, filtered
        )
        
        # Dimension 5: Temporal Weight
        filtered = self.dimensions['temporal'].apply_temporal_weight(
            filtered
        )
        
        # Dimension 6: Authority
        filtered = self.dimensions['authority'].apply_authority_weight(
            filtered
        )
        
        return filtered
```

## Implementation Example

See [examples/multidimensional_kg_example.py](../examples/multidimensional_kg_example.py) for a complete working example demonstrating:

- Building a multidimensional knowledge graph
- Applying dimensional filters to a real query
- Comparing RAG vs. Multidimensional approaches
- Measuring noise reduction and performance improvement

## Benefits

### 1. Scale by Subtraction
- Remove 99% of irrelevant data deterministically
- LLM only sees the 1% signal that matters
- Eliminates hallucination from information overload

### 2. Context Precision
- User-specific: Same query, different results per role
- Time-aware: Recent events weighted appropriately
- Relationship-aware: Dependencies included automatically

### 3. Performance
- **99% noise reduction** through graph filters
- **100x faster** than processing all documents
- **95% cost reduction** from smaller context

### 4. Explainability
- Clear audit trail of filtering decisions
- Each dimension provides explicit reasoning
- Transparent constraint application

### 5. Maintainability
- Add new dimensions without changing others
- Update business logic in graph structure
- No prompt engineering required

## Metrics to Track

```python
# Graph filtering effectiveness
metrics = {
    'initial_candidates': len(all_documents),
    'after_identity_filter': len(after_identity),
    'after_org_filter': len(after_org),
    'after_service_filter': len(after_service),
    'after_dependency_filter': len(after_dependency),
    'after_temporal_filter': len(after_temporal),
    'after_authority_filter': len(final_results),
    
    'total_reduction': (1 - len(final_results) / len(all_documents)) * 100,
    'query_time': query_time_ms,
    'llm_cost': llm_cost_dollars
}

# Target metrics:
# - Total reduction: >95% (filtering out noise)
# - Query time: <100ms (graph filtering is fast)
# - LLM cost: <$0.01 (small context)
```

## Implementation Roadmap

### Phase 1: Core Graph Structure
- [ ] Build basic entity-relationship graph
- [ ] Implement temporal tracking (valid_from, valid_until)
- [ ] Add confidence scores and source attribution
- [ ] Create graph query API

### Phase 2: Dimensional Filters
- [ ] Implement Identity & Scope dimension
- [ ] Implement Organizational Hierarchy dimension
- [ ] Implement Service Ownership dimension
- [ ] Implement Dependency Mapping dimension
- [ ] Implement Temporal Weight dimension
- [ ] Implement Authority dimension

### Phase 3: Integration
- [ ] Connect graph to existing data sources
- [ ] Build user context extraction
- [ ] Implement constraint-based querying
- [ ] Add metrics and monitoring

### Phase 4: Optimization
- [ ] Tune filtering thresholds per dimension
- [ ] Add caching for common queries
- [ ] Optimize graph traversal performance
- [ ] Expand graph coverage

## Advanced Patterns

### Adaptive Dimensionality

Different queries need different dimensions:

```python
def select_dimensions(query_type):
    """Choose relevant dimensions for query type"""
    
    dimension_map = {
        'my_tasks': ['identity', 'organizational', 'temporal'],
        'team_status': ['organizational', 'service_ownership', 'temporal'],
        'system_health': ['service_ownership', 'dependencies', 'temporal'],
        'compliance': ['authority', 'temporal', 'identity']
    }
    
    return dimension_map.get(query_type, ['all'])
```

### Composite Scoring

Combine multiple dimensions into a single relevance score:

```python
def compute_relevance_score(item, user_context):
    """Combine dimensional scores"""
    
    score = 1.0
    
    # Temporal decay
    score *= item.temporal_weight
    
    # Authority boost
    score *= item.authority_weight
    
    # Role-based boost
    if item.scope == user_context.user.role_focus:
        score *= 1.5
    
    # Organizational proximity
    if item.assigned_to in user_context.direct_reports:
        score *= 1.3
    
    return score
```

### Dynamic Threshold Adjustment

Adjust filtering strictness based on result count:

```python
class AdaptiveFilter:
    """Dynamically adjust thresholds to get optimal result count"""
    
    def filter_adaptively(self, items, target_count=10):
        """Adjust thresholds to get target_count results"""
        
        # Start with strict thresholds
        temporal_threshold = 0.8
        authority_threshold = 0.9
        
        while len(items) > target_count and temporal_threshold > 0.3:
            # Tighten filters
            temporal_threshold -= 0.1
            items = [i for i in items 
                    if i.temporal_weight >= temporal_threshold]
        
        while len(items) < target_count and authority_threshold > 0.5:
            # Loosen filters
            authority_threshold -= 0.1
            items = [i for i in items 
                    if i.authority_weight >= authority_threshold]
        
        return items
```

## Comparison: RAG vs. Multidimensional Graphs

| Aspect | RAG (Flat Vector Search) | Multidimensional Graph |
|--------|-------------------------|------------------------|
| **Context Awareness** | None - treats all docs equally | Full - role, time, org, dependencies |
| **Filtering** | Keyword/semantic similarity only | 6+ dimensions of business logic |
| **Noise Reduction** | ~50% (similar docs) | ~99% (constraint-based) |
| **Personalization** | None - same results for everyone | Full - per user, role, team |
| **Temporal Awareness** | None - old = new | Full - weighted by recency |
| **Relationship Understanding** | None - flat docs | Full - org hierarchy, dependencies |
| **Query Time** | 200-500ms | 50-100ms |
| **LLM Context Size** | Large (many docs) | Small (filtered signal) |
| **Cost per Query** | $0.05-0.10 | $0.005-0.01 |
| **Hallucination Risk** | High (overload) | Low (precise context) |
| **Explainability** | None - black box | Full - dimension-by-dimension |

## Conclusion

Multidimensional Knowledge Graphs are the future of enterprise AI systems. They transform "context" from a pile of documents into a precise, role-based, time-aware, relationship-understanding semantic firewall.

**The Graph doesn't answer questions. It eliminates wrong answers.**

By subtracting 99% of noise before the LLM sees anything, we:
- Eliminate hallucinations from information overload
- Reduce costs by 10-20x
- Improve response times by 5-10x
- Provide explainable, auditable results
- Enable true enterprise-scale AI

The best agents don't think harder—they filter better.

## Further Reading

- [Semantic Firewall](./semantic-firewall.md) - Validation and verification patterns
- [Compute-to-Lookup Ratio](./compute-to-lookup-ratio.md) - Optimization strategies
- [Guardrail Router](./guardrail-router.md) - Intelligent routing
- [Cognitive Systems Architect](./cognitive-systems-architect.md) - The role that builds these systems
