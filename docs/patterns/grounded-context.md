# Grounded context

> Merged from three earlier documents: Multidimensional Knowledge Graphs, The
> Semantic Firewall, and Recursive Ontologies. They were one pattern in three
> stages: build the structure, enforce it, keep it current.

> The numbers in this document are worked examples on stated assumptions, or
> design targets. None of them are measurements. See the evidence standard in
> [CONTRIBUTING.md](../../CONTRIBUTING.md#evidence-standard).

## The problem

Retrieval by similarity finds text that reads like the question. It has no
opinion about whether that text is true, current, in scope for the person
asking, or authoritative.

Ask "what is on my plate?" and a flat vector store returns documents containing
the words. It cannot tell that half belong to a team you left, that two are
superseded, that one is a draft nobody approved, and that the most relevant item
never uses the phrase at all. So the model receives a pile of plausible context
and does the only thing it can with a pile: it reconciles it into a confident
answer.

Two failures follow, and they are usually treated as separate problems:

1. **The model claims things the corpus does not support.** Detecting that after
   generation is too late, and the detector has the same grounding problem the
   generator had.
2. **The corpus goes stale.** Someone changes team, a service is renamed, a
   policy is superseded. Nothing tells the retrieval layer, so it keeps
   confidently returning the old world.

## The mechanism

Three stages, which is why this used to be three documents.

**Stage one: structure the context so it can be filtered deterministically.**
Not a pile of documents with a similarity score, but a graph with dimensions you
can apply as constraints: who is asking and what they may see, where they sit in
the organisation, what they own, what depends on what, how old something is, and
which source outranks which. Each dimension removes candidates by a rule, not by
a score.

**Stage two: check the output against the same structure before release.** The
graph that decided what the model could see also decides what the model is
allowed to claim. A claim about an entity that does not exist, a relationship
that has expired, or a fact carrying a single source fails a rule and never
reaches the user.

**Stage three: treat retrieval failures as signals rather than errors.** When an
agent asks for something the graph cannot answer, that is information about a
gap. Route it to a component that detects patterns across those failures and
rebuilds the affected region of the graph. The alternative is a manual curation
backlog that loses to reality.

```
   Request ---> dimensional filters ---> candidate set ---> model
                       ^                                      |
                       |                                      v
               rebuild affected                 claims ---> validation rules
               region of graph                               |
                       ^                              pass   |   fail
                       |                                     v
               analyst detects <--- failure signals <--- blocked, with a reason
               patterns
```

The loop is the point. Without stage three the structure decays. Without stage
two the structure is advisory. Without stage one there is nothing to enforce.

## Implementation detail

The material below is retained from the three source documents, arranged by
stage.

## Stage one: structure the context

### Six dimensions, worked through one query

Let's look at a seemingly simple query: **"What pending items do I have on my plate?"**

If you send this to a standard RAG system, it will return every Jira ticket, email, and document where your name appears next to the word "pending." The result is hallucination or information overload.

Here is how a Multidimensional Graph solves this via constraints:

#### Dimension 1: Identity & Scope (The Manager View)

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

#### Dimension 2: Organizational Hierarchy

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

#### Dimension 3: Service Ownership

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

#### Dimension 4: Dependency Mapping

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

#### Dimension 5: Temporal Weight

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

#### Dimension 6: Authority & Source

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

### What the filter chain leaves behind

By the time the LLM receives the context, the Graph has already done the heavy lifting. We didn't ask the AI to figure out what matters. We used the graph to filter the universe down to the exact subset of reality that matters right now.

**We subtracted 99% of the noise using deterministic graph logic, leaving the AI with the easy job: summarizing the 1% of signal that remains.**

#### Before: RAG Approach (Flat)
```
Query: "What pending items do I have?"
Vector Search Results: 10,000 documents mentioning "pending" and user name
LLM Task: Read 10,000 docs, figure out what's relevant, summarize
Result: Hallucinations, information overload, 30 seconds, $0.50
```

#### After: Multidimensional Graph Approach
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

### Graph structure and the filter chain

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

### Comparison: RAG vs. Multidimensional Graphs

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

## Stage two: enforce the structure

### The four graph dimensions the rules read

The core of the Semantic Firewall is a knowledge graph with multiple dimensions:

#### 1. Entity-Relationship Dimension

```python
# Traditional knowledge graph structure
class Entity:
    id: str
    type: str  # person, organization, concept, etc.
    properties: Dict[str, Any]
    
class Relationship:
    subject: Entity
    predicate: str  # works_for, located_in, invented_by
    object: Entity
    
# Example:
# (John Smith) -[works_for]-> (Acme Corp)
# (Acme Corp) -[located_in]-> (New York)
```

#### 2. Temporal Dimension

Track when facts are valid:

```python
class TemporalFact:
    relationship: Relationship
    valid_from: datetime
    valid_until: Optional[datetime]
    confidence: float
    
# Example:
# (John Smith) -[works_for]-> (Acme Corp)
# valid_from: 2020-01-01
# valid_until: 2023-06-30
# confidence: 0.95
#
# (John Smith) -[works_for]-> (Beta Inc)
# valid_from: 2023-07-01
# valid_until: None (current)
# confidence: 0.98
```

#### 3. Confidence & Provenance Dimension

Track certainty and sources:

```python
class VerifiedFact:
    fact: TemporalFact
    confidence_score: float  # 0.0 to 1.0
    sources: List[Source]
    verification_date: datetime
    
class Source:
    url: str
    source_type: str  # official_document, news_article, database
    reliability_score: float
    
# Facts with multiple high-quality sources get higher confidence
```

#### 4. Semantic Context Dimension

Understand relationships in different contexts:

```python
class ContextualRelationship:
    relationship: Relationship
    context: str  # professional, personal, historical
    domain: str  # technology, finance, healthcare
    
# Example:
# (Python) -[related_to]-> (Programming)
# context: technical, domain: computer_science
#
# (Python) -[related_to]-> (Snake)
# context: zoology, domain: biology
```

### Firewall Validation Rules

#### Rule 1: Entity Existence Check

```python
def validate_entity_existence(entity_id: str) -> bool:
    """
    Verify that entities mentioned in LLM output exist in knowledge graph
    """
    return knowledge_graph.entity_exists(entity_id)

# Example validation:
llm_output = "John Smith works at XYZ Corp"
entities = extract_entities(llm_output)  # ["John Smith", "XYZ Corp"]

for entity in entities:
    if not validate_entity_existence(entity):
        return BLOCKED  # Entity not in our knowledge base
```

#### Rule 2: Relationship Validity Check

```python
def validate_relationship(subject: str, predicate: str, object: str) -> bool:
    """
    Verify that the relationship exists and is valid
    """
    relationship = knowledge_graph.get_relationship(subject, predicate, object)
    if not relationship:
        return False
    
    # Check temporal validity
    if relationship.valid_until and relationship.valid_until < datetime.now():
        return False
    
    return True

# Example:
# LLM claims: "Steve Jobs is CEO of Apple"
# Firewall checks temporal validity -> BLOCKED (expired relationship)
```

#### Rule 3: Temporal Consistency Check

```python
def validate_temporal_consistency(facts: List[TemporalFact]) -> bool:
    """
    Ensure facts don't contradict each other temporally
    """
    for i, fact1 in enumerate(facts):
        for fact2 in facts[i+1:]:
            if fact1.conflicts_with(fact2):
                return False
    return True

# Example:
# Claim: "Person A was in New York and London at the same time"
# Firewall detects temporal impossibility -> BLOCKED
```

#### Rule 4: Confidence Threshold Check

```python
def validate_confidence(fact: VerifiedFact, threshold: float = 0.7) -> bool:
    """
    Only allow facts that meet minimum confidence threshold
    """
    return fact.confidence_score >= threshold

# Low-confidence facts are flagged or blocked
```

#### Rule 5: Source Verification

```python
def validate_sources(fact: VerifiedFact, min_sources: int = 2) -> bool:
    """
    Require multiple reliable sources for controversial claims
    """
    reliable_sources = [s for s in fact.sources if s.reliability_score > 0.8]
    return len(reliable_sources) >= min_sources
```

#### Rule 6: Contradiction Detection

```python
def detect_contradictions(new_fact: TemporalFact) -> bool:
    """
    Check if new fact contradicts existing knowledge
    """
    contradicting_facts = knowledge_graph.find_contradictions(new_fact)
    
    if contradicting_facts:
        # Resolve based on recency, source quality, confidence
        return resolve_contradiction(new_fact, contradicting_facts)
    
    return True
```

### Advanced Patterns

#### Multi-Hop Validation

```python
def validate_multi_hop_reasoning(chain: List[Fact]) -> bool:
    """
    Validate chains of reasoning through knowledge graph
    """
    for i in range(len(chain) - 1):
        # Verify each step is valid
        if not validate_relationship(chain[i]):
            return False
        
        # Verify steps connect properly
        if chain[i].object != chain[i+1].subject:
            return False
    
    return True

# Example:
# Claim: "Python was created by Guido, who worked at Google"
# Validate: Python -> created_by -> Guido []
# Validate: Guido -> worked_at -> Google []
```

#### Probabilistic Validation

```python
def probabilistic_validate(facts: List[Fact]) -> float:
    """
    Calculate overall confidence of a multi-fact claim
    """
    # Combine individual fact confidences
    confidence = 1.0
    for fact in facts:
        confidence *= fact.confidence
    
    return confidence

# Only allow if combined confidence > threshold
```

#### Dynamic Threshold Adjustment

```python
class AdaptiveFirewall(SemanticFirewall):
    def adjust_threshold(self, context: Dict):
        """
        Adjust validation strictness based on context
        """
        if context.get('high_risk_domain'):
            self.min_confidence = 0.95  # Strict
        elif context.get('exploratory_query'):
            self.min_confidence = 0.6   # Lenient
        else:
            self.min_confidence = 0.7   # Default
```

## Stage three: keep the structure current

### The Feedback Loop: Agents as Telemetry

When an agent fails to find an answer, that is not an error. **It is a signal**.

#### Traditional Approach (Error)
```
Agent Query → Knowledge Graph → No match found → Agent hallucinates
Result: Bad output reaches users
```

#### Recursive Ontology Approach (Signal)
```
Agent Query → Knowledge Graph → No match found → Signal captured
                                               ↓
                                    Analyst System analyzes
                                               ↓
                                    Knowledge Graph updated
                                               ↓
                                    Agent succeeds on retry
```

#### Signal Types and Actions

| Signal Type | Example | Automated Action |
|-------------|---------|------------------|
| **Entity Missing** | "Could not resolve Project X" | Flag sector as "Incomplete" |
| **Relationship Unknown** | "No ownership link for Service Y" | Trigger relationship discovery |
| **Temporal Stale** | "Data last updated 6 months ago" | Mark graph as "Stale" |
| **Confidence Drop** | "Multiple contradictory sources" | Request human review |
| **Query Pattern** | "Same unknown entity queried 10x" | Prioritize for expansion |

#### Implementation Pattern

```python
class AgentTelemetry:
    """Capture agent failures as signals for knowledge evolution"""
    
    def __init__(self, analyst_system):
        self.analyst = analyst_system
        self.signals = []
    
    def capture_signal(self, signal_type: str, context: Dict):
        """
        Don't force the agent to hallucinate.
        Instead, capture the knowledge gap.
        """
        signal = {
            'type': signal_type,
            'timestamp': datetime.now(),
            'context': context,
            'severity': self._calculate_severity(signal_type, context)
        }
        
        self.signals.append(signal)
        
        # Real-time critical signals trigger immediate action
        if signal['severity'] == 'critical':
            self.analyst.trigger_immediate_update(signal)
        
        return signal
    
    def _calculate_severity(self, signal_type: str, context: Dict) -> str:
        """
        Severity based on:
        - Frequency: How often has this been signaled?
        - Impact: How many users/agents affected?
        - Confidence: How sure are we this is a gap?
        
        Thresholds (configurable per deployment):
        - Critical: >10 occurrences AND >5 agents affected
          (High volume indicates systemic issue requiring immediate attention)
        - High: >5 occurrences OR >3 agents affected
          (Moderate volume or multi-agent impact needs prompt handling)
        - Medium: >2 occurrences
          (Pattern emerging, should be addressed in batch)
        - Low: 1-2 occurrences
          (May be edge case, monitor for pattern)
        """
        frequency = context.get('occurrence_count', 1)
        impact = context.get('affected_agents', 1)
        
        if frequency > 10 and impact > 5:
            return 'critical'
        elif frequency > 5 or impact > 3:
            return 'high'
        elif frequency > 2:
            return 'medium'
        return 'low'
```

### Ephemeral Graphs: Just-in-Time Knowledge

One of the biggest mistakes we make is treating Knowledge Graphs like monolithic databases that live forever. They shouldn't.

True scale comes from making knowledge **Ephemeral** and **Event-Driven**.

#### The Three Types of Ephemeral Graphs

#### 1. The Org Graph (Event-Driven)
**Should be recreated only when an HR event triggers a change.**

```python
class OrgGraph:
    """
    Ephemeral organizational knowledge graph
    Rebuilt on HR events, not on a schedule
    """
    
    def __init__(self, event_bus):
        self.graph = None
        self.last_built = None
        self.event_bus = event_bus
        
        # Subscribe to HR events
        self.event_bus.subscribe('employee.hired', self.rebuild)
        self.event_bus.subscribe('employee.transferred', self.rebuild)
        self.event_bus.subscribe('employee.terminated', self.rebuild)
        self.event_bus.subscribe('org.restructure', self.rebuild)
    
    def rebuild(self, event):
        """
        Rebuild entire graph from source of truth
        Previous graph is discarded
        """
        print(f"Rebuilding OrgGraph due to: {event.type}")
        
        # Pull fresh data from HR system
        employees = hr_system.get_all_employees()
        departments = hr_system.get_all_departments()
        reporting_lines = hr_system.get_reporting_structure()
        
        # Build new graph
        self.graph = MultidimensionalKnowledgeGraph()
        
        for emp in employees:
            self.graph.add_entity(Entity(
                id=emp.id,
                name=emp.name,
                type='employee',
                properties={'title': emp.title, 'department': emp.department}
            ))
        
        for line in reporting_lines:
            self.graph.add_relationship(Relationship(
                subject=self.graph.get_entity(line.employee_id),
                predicate='reports_to',
                object=self.graph.get_entity(line.manager_id),
                valid_from=datetime.now(),
                sources=['hr_system']
            ))
        
        self.last_built = datetime.now()
        
        # Old graph is garbage collected
        # No migration, no sync, no complexity
    
    def get_graph(self):
        """
        Get current graph
        Rebuild if older than safety threshold (e.g., 24 hours)
        """
        if not self.graph or (datetime.now() - self.last_built) > timedelta(hours=24):
            self.rebuild(Event('safety_rebuild'))
        
        return self.graph
```

**Benefits**:
- Always current (rebuilt on every change)
- No sync complexity (single source of truth)
- Small and fast (only active employees)
- Self-healing (corrupted? Just rebuild)

#### 2. The Product Graph (Documentation-Driven)
**Should be rebuilt the moment a documentation PR is merged.**

```python
class ProductGraph:
    """
    Ephemeral product knowledge graph
    Rebuilt when documentation changes
    """
    
    def __init__(self, git_webhook):
        self.graph = None
        self.last_commit = None
        
        # Subscribe to Git events
        git_webhook.on('push', branch='main', path='docs/**', 
                       callback=self.rebuild_from_docs)
    
    def rebuild_from_docs(self, commit):
        """
        Parse documentation to build knowledge graph
        """
        print(f"Rebuilding ProductGraph from commit: {commit.sha[:7]}")
        
        self.graph = MultidimensionalKnowledgeGraph()
        
        # Parse documentation files
        doc_files = git.get_changed_files(commit, pattern='docs/**/*.md')
        
        for doc_file in doc_files:
            # Extract entities (products, features, APIs)
            entities = self._extract_entities_from_markdown(doc_file)
            
            for entity in entities:
                self.graph.add_entity(entity)
            
            # Extract relationships (depends_on, implements, deprecated_by)
            relationships = self._extract_relationships_from_markdown(doc_file)
            
            for rel in relationships:
                self.graph.add_relationship(rel)
        
        self.last_commit = commit.sha
        
        # Validate graph completeness
        coverage = self._calculate_coverage()
        if coverage < 0.95:
            self._signal_incomplete_docs(coverage)
    
    def _calculate_coverage(self) -> float:
        """
        What percentage of products have full documentation?
        """
        products = self.graph.get_entities_by_type('product')
        documented = [p for p in products if self._is_fully_documented(p)]
        return len(documented) / len(products) if products else 0.0
```

**Benefits**:
- Documentation IS the knowledge graph
- No documentation drift (graph reflects docs exactly)
- Continuous validation (gaps trigger alerts)
- Version controlled (graph state tied to commit)

#### 3. The Context Graph (Project-Lifetime)
**Should exist only for the duration of a project.**

```python
class ContextGraph:
    """
    Ephemeral context graph for a specific project/task
    Created on demand, destroyed when project ends
    """
    
    def __init__(self, project_id: str, ttl_hours: int = 720):  # 30 days default
        self.project_id = project_id
        self.graph = MultidimensionalKnowledgeGraph()
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(hours=ttl_hours)
        self.access_count = 0
    
    @classmethod
    def create_for_project(cls, project_id: str):
        """
        Create context graph with project-specific knowledge
        """
        context = cls(project_id)
        
        # Pull relevant entities from various sources
        context._load_project_team()
        context._load_project_dependencies()
        context._load_project_timeline()
        context._load_project_constraints()
        
        return context
    
    def _load_project_team(self):
        """Load team members assigned to this project"""
        team = project_system.get_team(self.project_id)
        
        for member in team:
            self.graph.add_entity(Entity(
                id=f"proj_{self.project_id}_user_{member.id}",
                name=member.name,
                type='team_member',
                properties={'role': member.role, 'allocation': member.allocation}
            ))
    
    def is_expired(self) -> bool:
        """Check if context should be destroyed"""
        if datetime.now() > self.expires_at:
            return True
        
        # Also expire if not accessed in 7 days
        if self.last_accessed and (datetime.now() - self.last_accessed) > timedelta(days=7):
            return True
        
        return False
    
    def extend_lifetime(self, additional_hours: int):
        """Extend lifetime if project is still active"""
        self.expires_at += timedelta(hours=additional_hours)
    
    def destroy(self):
        """
        Explicitly destroy the graph
        Called when project completes or is cancelled
        """
        print(f"Destroying ContextGraph for project {self.project_id}")
        self.graph = None
        # Cleanup any cached data
        cache.delete(f"context_graph:{self.project_id}")
```

**Benefits**:
- No accumulation of dead knowledge
- Focused and fast (only relevant entities)
- Automatic cleanup (expires with project)
- Resource efficient (no permanent storage)

### Human Wisdom: Statistical Supervision

If the system evolves itself, where does the human fit?

We cannot have humans reviewing every node update, that defeats the purpose of AI. But we cannot have AI rewriting its own logic without oversight, that creates drift.

The solution is **Sampling for Wisdom**.

#### The Statistical Supervision Pattern

```python
class StatisticalSupervisor:
    """
    Human-in-the-loop strategy based on statistical sampling
    Humans review a subset, AI handles the volume
    """
    
    def __init__(self, sample_rate: float = 0.05):
        self.sample_rate = sample_rate  # 5% default
        self.review_queue = []
        self.confidence_threshold = 0.95
    
    def should_review(self, update: GraphUpdate) -> bool:
        """
        Determine if this update needs human review
        """
        # Always review high-variance updates
        if update.confidence_variance > 0.3:
            return True
        
        # Always review critical entities
        if update.entity_type in ['financial', 'healthcare', 'legal']:
            return True
        
        # Statistical sampling for others
        return random.random() < self.sample_rate
    
    def queue_for_review(self, update: GraphUpdate):
        """
        Add update to human review queue
        """
        self.review_queue.append({
            'update': update,
            'queued_at': datetime.now(),
            'priority': self._calculate_priority(update),
            'context': self._gather_context(update)
        })
    
    def _calculate_priority(self, update: GraphUpdate) -> str:
        """
        Priority based on:
        - Confidence variance (how uncertain is the AI?)
        - Impact radius (how many queries affected?)
        - Criticality (what domain?)
        """
        if update.confidence_variance > 0.5 or update.impact_radius > 100:
            return 'high'
        elif update.confidence_variance > 0.3 or update.impact_radius > 50:
            return 'medium'
        return 'low'
    
    def process_human_feedback(self, update_id: str, approved: bool, feedback: str):
        """
        Learn from human decisions to improve sampling
        """
        update = self._get_update(update_id)
        
        # Record the decision
        decision = {
            'update_id': update_id,
            'approved': approved,
            'feedback': feedback,
            'confidence_variance': update.confidence_variance,
            'impact_radius': update.impact_radius,
            'entity_type': update.entity_type
        }
        
        self._record_decision(decision)
        
        # Use ML to learn what should be reviewed
        self._update_review_model(decision)
    
    def _update_review_model(self, decision: Dict):
        """
        Learn patterns in human approvals/rejections
        Adjust what gets sampled for review
        """
        # If humans consistently approve low-variance updates,
        # reduce sampling rate for that category
        
        # If humans frequently reject updates from a specific source,
        # increase review rate for that source
        
        pass  # ML model training logic
```

#### Review Dashboard Design

```python
class ReviewDashboard:
    """
    Human interface for reviewing graph updates
    """
    
    def get_next_review(self, reviewer_id: str) -> Dict:
        """
        Get next update for human review
        Prioritized by urgency and expertise match
        """
        reviews = self.supervisor.review_queue
        
        # Filter by reviewer expertise
        relevant = [r for r in reviews if self._matches_expertise(r, reviewer_id)]
        
        # Sort by priority
        relevant.sort(key=lambda r: (r['priority'], r['queued_at']))
        
        if not relevant:
            return None
        
        review = relevant[0]
        
        return {
            'update': review['update'],
            'context': review['context'],
            'similar_past_decisions': self._get_similar_decisions(review),
            'impact_analysis': self._analyze_impact(review),
            'recommendation': self._get_ai_recommendation(review)
        }
    
    def present_for_review(self, review: Dict) -> Dict:
        """
        Present update in reviewable format
        """
        return {
            'summary': self._summarize_update(review),
            'before_state': self._show_before(review),
            'after_state': self._show_after(review),
            'affected_queries': self._show_affected_queries(review),
            'confidence_score': review['update'].confidence,
            'sources': review['update'].sources,
            'actions': ['approve', 'reject', 'modify', 'defer']
        }
```

#### Wisdom vs. Volume

The key insight: **Humans provide the Wisdom, AI handles the Volume**.

| Aspect | Human Role | AI Role |
|--------|-----------|---------|
| **Volume** | Review 5% (sampled) | Process 95% (automated) |
| **Judgment** | Strategic intent | Tactical execution |
| **Speed** | Slow (careful) | Fast (automated) |
| **Scope** | High-risk/variance | Low-risk/standard |
| **Learning** | Provide examples | Extract patterns |

### The Analyst System: Orchestrating Self-Healing

```python
class AnalystSystem:
    """
    Background system that analyzes signals and triggers knowledge evolution
    """
    
    def __init__(self, telemetry: AgentTelemetry, supervisor: StatisticalSupervisor):
        self.telemetry = telemetry
        self.supervisor = supervisor
        self.healing_queue = PriorityQueue()
    
    def analyze_signals(self):
        """
        Periodically analyze accumulated signals
        Detect patterns and trigger healing actions
        """
        signals = self.telemetry.get_recent_signals(hours=24)
        
        # Group signals by type and context
        patterns = self._detect_patterns(signals)
        
        for pattern in patterns:
            if pattern.severity == 'critical':
                self._trigger_immediate_healing(pattern)
            else:
                self._queue_healing_action(pattern)
    
    def _detect_patterns(self, signals: List[Dict]) -> List[Pattern]:
        """
        Find meaningful patterns in agent failures
        """
        patterns = []
        
        # Pattern 1: Same entity missing repeatedly
        entity_misses = {}
        for signal in signals:
            if signal['type'] == 'entity_missing':
                entity_id = signal['context']['entity_id']
                entity_misses[entity_id] = entity_misses.get(entity_id, 0) + 1
        
        for entity_id, count in entity_misses.items():
            if count > 5:  # Threshold
                patterns.append(Pattern(
                    type='missing_entity',
                    severity='high',
                    entity_id=entity_id,
                    occurrences=count,
                    recommended_action='add_entity'
                ))
        
        # Pattern 2: Knowledge sector consistently stale
        sector_staleness = self._analyze_sector_staleness(signals)
        
        for sector, staleness in sector_staleness.items():
            if staleness > 0.7:  # 70% of queries in this sector fail
                patterns.append(Pattern(
                    type='stale_sector',
                    severity='critical',
                    sector=sector,
                    staleness=staleness,
                    recommended_action='rebuild_sector'
                ))
        
        # Pattern 3: Relationship type frequently unknown
        unknown_relationships = self._analyze_unknown_relationships(signals)
        
        for rel_type, count in unknown_relationships.items():
            if count > 10:
                patterns.append(Pattern(
                    type='missing_relationship_type',
                    severity='medium',
                    relationship_type=rel_type,
                    occurrences=count,
                    recommended_action='add_relationship_discovery'
                ))
        
        return patterns
    
    def _trigger_immediate_healing(self, pattern: Pattern):
        """
        Critical issues require immediate action
        No human review for time-sensitive fixes
        """
        print(f"CRITICAL: Immediate healing triggered for {pattern.type}")
        
        if pattern.type == 'stale_sector':
            # Rebuild entire sector from source of truth
            self._rebuild_sector(pattern.sector)
        
        elif pattern.type == 'missing_entity':
            # Attempt automatic entity discovery
            self._discover_entity(pattern.entity_id)
    
    def _queue_healing_action(self, pattern: Pattern):
        """
        Non-critical actions go through review process
        """
        update = self._create_update_from_pattern(pattern)
        
        # Check if human review needed
        if self.supervisor.should_review(update):
            self.supervisor.queue_for_review(update)
        else:
            # Auto-apply low-risk updates
            self._apply_update(update)
    
    def _rebuild_sector(self, sector: str):
        """
        Rebuild an entire knowledge sector
        Ephemeral approach: discard and rebuild from source
        """
        print(f"Rebuilding sector: {sector}")
        
        # Identify the source of truth
        source = self._get_source_for_sector(sector)
        
        # Pull fresh data
        data = source.fetch_all()
        
        # Rebuild graph sector
        graph_sector = self._build_sector_from_data(sector, data)
        
        # Replace old sector atomically
        self._replace_sector(sector, graph_sector)
        
        print(f"Sector {sector} rebuilt with {len(graph_sector.entities)} entities")
```

### Real-World Examples

#### Example 1: HR Event Triggers Org Graph Update

```python
# Employee gets promoted
hr_system.promote_employee(
    employee_id='emp_123',
    new_title='Senior Engineer',
    new_manager_id='emp_456'
)

# Event published
event_bus.publish(Event(
    type='employee.transferred',
    data={'employee_id': 'emp_123', 'new_manager_id': 'emp_456'}
))

# OrgGraph automatically rebuilds
# Next query about "Who does Alice report to?"
# Gets correct answer immediately
```

#### Example 2: Agent Signals Missing Entity

```python
# Agent tries to query
result = system.query(
    "What is the status of Project Phoenix?",
    context={'user_id': 'user_123'}
)

# Returns: knowledge_not_found
# Signal captured: missing entity "Project Phoenix"

# Analyst detects pattern (10 queries for same project)
# Triggers discovery: "Project Phoenix" found in project management system

# Auto-adds entity to knowledge graph
# Next query succeeds
```

#### Example 3: Documentation Update Propagates

```python
# Developer merges PR updating API documentation
git.merge_pr(
    pr_number=456,
    files=['docs/api/authentication.md']
)

# Git webhook triggers
git_webhook.emit('push', {
    'branch': 'main',
    'files': ['docs/api/authentication.md'],
    'commit': 'abc123'
})

# ProductGraph rebuilds from updated docs
# API changes immediately reflected in knowledge graph
# Agents now know about new authentication endpoints
```

## The invariant

> A claim the extractor turns into a checkable fact is released only if every
> validation rule passes against the graph. A rule that fails blocks the
> response and records why.

That is falsifiable, and it is tested. Expire a relationship, remove a source,
or raise a threshold, and the same input must stop passing.

## What this does not do

The invariant is narrow on purpose, and the two gaps it leaves are the most
important paragraphs in this document.

**A claim the extractor does not recognise passes through unchecked.** The
firewall protects what extraction hands it. Extraction coverage is therefore a
security property rather than an NLP quality metric, and it is the first number
to measure.

**A wrong fact in the graph is enforced exactly as confidently as a right one.**
This pattern inherits the correctness of your knowledge, it does not create it.
A poisoned or merely careless graph produces confidently grounded falsehoods,
and the audit trail will show every rule passing.

Neither gap is a reason to skip the pattern. Both are reasons not to describe it
as a guarantee of accuracy.

## The test

`tests/test_grounding_invariants.py` covers:

- A supported, current, multi-sourced claim passes.
- An expired relationship is blocked, with a reason attached.
- An unknown entity is blocked.
- A single-sourced claim is blocked on provenance alone, even when everything
  else about it is correct.
- A low-confidence claim is blocked, and the threshold is read from
  configuration rather than hardcoded.

Two further tests pin the gaps above, so that if either stops holding, CI fails
and this document is wrong:

- `test_a_claim_the_extractor_misses_passes_through_unchecked`
- `test_a_wrong_fact_in_the_graph_is_enforced_as_confidently_as_a_right_one`

## When not to use this

- **You do not have the knowledge.** The pattern moves the hard problem from
  generation to curation. If nobody in the organisation can say what is true, a
  graph will not settle it.
- **The domain has no stable entities.** Open-ended creative or exploratory work
  has nothing to bind claims to, and every rule fires as a false positive.
- **Refusal costs more than a wrong answer.** A high threshold shifts the failure
  mode from wrong answers to refused ones. That trade is not always an
  improvement, and in some settings it is worse.
- **You need it this quarter.** Stage one is weeks of modelling before anything
  works. Flat retrieval plus human review is the honest interim.
- **Coverage is thin.** A firewall over a graph that knows 10% of the domain
  blocks the 90% it has never heard of, and users route around it.

## What to measure

| Signal | Why it matters |
|---|---|
| Extraction coverage | The share of claims the firewall even sees. This bounds everything else |
| Block rate, split into correct and incorrect blocks | A high block rate is not a success until you know which kind it is |
| Candidate count after each dimension | Shows which filters do work and which are decoration |
| Graph freshness by region | A single average hides one rotten region |
| Signal to rebuild latency | How long a known gap stays open |
| Share of gaps healed without a human | Rising is good. Rising while accuracy falls is not |

## Anti-patterns

**Similarity as a substitute for scope.** Access control by cosine distance.

**A firewall over a graph nobody owns.** Every rule passes, the graph is wrong,
and the audit trail makes it worse by looking rigorous.

**Detection after generation.** A second model asked whether the first one lied,
with no more grounding than the first one had.

**Manual curation as the only update path.** The backlog grows faster than the
team, and the graph becomes a snapshot of the day someone last had time.

**Auto-healing with no sampling.** The system rewrites its own knowledge and
nobody inspects a slice of it, so drift compounds silently.

## Reference implementations

| Component | Where it exists as running code |
|---|---|
| Signed, checkable records of what an agent did and under which policy | [TRACE](https://github.com/agentrust-io/trace-spec) |
| Declared capability and scope for an agent, as a verifiable document | [Agent Manifest](https://github.com/agentrust-io/agent-manifest) |
| Policy evaluation outside the model process | [cMCP](https://github.com/agentrust-io/cmcp) |

None of these is a knowledge graph. They are the enforcement and evidence layers
this pattern needs once a block has to be provable to somebody else rather than
merely logged.

## Run the examples

```bash
python examples/multidimensional_kg_example.py
python examples/semantic_firewall_example.py
python examples/recursive_ontology_example.py
python -m unittest tests.test_grounding_invariants -v
```

The first three are simulations and call no model. The fourth is the part that
can fail.

## Related patterns

- [Routing before reasoning](./routing.md), for deciding what reaches this path
- [Silent execution](./silent-execution.md), for who is allowed to act on the result
- [The Evidence Plane](../evidence-plane.md), for making a block provable
