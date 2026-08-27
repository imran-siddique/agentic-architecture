# Recursive Ontologies: Self-Updating Semantic Firewalls

> The numbers in this document are worked examples on stated assumptions, or
> design targets. None of them are measurements. See the evidence standard in
> [CONTRIBUTING.md](../CONTRIBUTING.md#evidence-standard).

## Overview

We have built the constraints (Part 1), the firewall (Part 2), and the headless protocols (Part 3). But static systems die. In a world where data changes every second, how do we keep our "Semantic Firewall" from becoming a legacy blocker?

The answer is **Recursive Ontologies**. The system must update itself.

## The Problem with Static Knowledge

Traditional knowledge graphs are treated like databases, immutable truths that need manual curation. This creates three critical problems:

1. **Knowledge Rot**: Information becomes stale as reality changes
2. **Manual Bottlenecks**: Every update requires human intervention
3. **Scale Failure**: The system cannot keep pace with data velocity

In production, this manifests as:
- Agents hallucinating because knowledge is outdated
- Firewall blocking valid queries due to missing entities
- System becoming a bottleneck rather than an enabler

## The Feedback Loop: Agents as Telemetry

When an agent fails to find an answer, that is not an error. **It is a signal**.

### Traditional Approach (Error)
```
Agent Query → Knowledge Graph → No match found → Agent hallucinates
Result: Bad output reaches users
```

### Recursive Ontology Approach (Signal)
```
Agent Query → Knowledge Graph → No match found → Signal captured
                                               ↓
                                    Analyst System analyzes
                                               ↓
                                    Knowledge Graph updated
                                               ↓
                                    Agent succeeds on retry
```

### Signal Types and Actions

| Signal Type | Example | Automated Action |
|-------------|---------|------------------|
| **Entity Missing** | "Could not resolve Project X" | Flag sector as "Incomplete" |
| **Relationship Unknown** | "No ownership link for Service Y" | Trigger relationship discovery |
| **Temporal Stale** | "Data last updated 6 months ago" | Mark graph as "Stale" |
| **Confidence Drop** | "Multiple contradictory sources" | Request human review |
| **Query Pattern** | "Same unknown entity queried 10x" | Prioritize for expansion |

### Implementation Pattern

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

## Ephemeral Graphs: Just-in-Time Knowledge

One of the biggest mistakes we make is treating Knowledge Graphs like monolithic databases that live forever. They shouldn't.

True scale comes from making knowledge **Ephemeral** and **Event-Driven**.

### The Three Types of Ephemeral Graphs

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

## Human Wisdom: Statistical Supervision

If the system evolves itself, where does the human fit?

We cannot have humans reviewing every node update, that defeats the purpose of AI. But we cannot have AI rewriting its own logic without oversight, that creates drift.

The solution is **Sampling for Wisdom**.

### The Statistical Supervision Pattern

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

### Review Dashboard Design

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

### Wisdom vs. Volume

The key insight: **Humans provide the Wisdom, AI handles the Volume**.

| Aspect | Human Role | AI Role |
|--------|-----------|---------|
| **Volume** | Review 5% (sampled) | Process 95% (automated) |
| **Judgment** | Strategic intent | Tactical execution |
| **Speed** | Slow (careful) | Fast (automated) |
| **Scope** | High-risk/variance | Low-risk/standard |
| **Learning** | Provide examples | Extract patterns |

## The Analyst System: Orchestrating Self-Healing

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

## System Integration: The Complete Architecture

```python
class RecursiveOntologySystem:
    """
    Complete self-updating semantic firewall system
    """
    
    def __init__(self):
        # Core components
        self.knowledge_graph = MultidimensionalKnowledgeGraph()
        self.semantic_firewall = SemanticFirewall(self.knowledge_graph)
        
        # Feedback loop components
        self.telemetry = AgentTelemetry(analyst_system=None)  # Set later
        self.supervisor = StatisticalSupervisor(sample_rate=0.05)
        self.analyst = AnalystSystem(self.telemetry, self.supervisor)
        
        # Connect telemetry to analyst
        self.telemetry.analyst = self.analyst
        
        # Ephemeral graph managers
        self.org_graph = OrgGraph(event_bus)
        self.product_graph = ProductGraph(git_webhook)
        self.context_graphs = {}  # project_id -> ContextGraph
    
    def query(self, agent_query: str, context: Dict) -> Dict:
        """
        Process agent query with feedback loop
        """
        # Get relevant ephemeral graphs
        graphs = self._get_relevant_graphs(context)
        
        # Try to answer from knowledge
        result = self._query_knowledge(agent_query, graphs)
        
        if result.found:
            # Validate through semantic firewall
            validation = self.semantic_firewall.validate(result.answer, context)
            
            if validation.passed:
                return {'success': True, 'answer': result.answer}
            else:
                # Firewall blocked - this is a signal
                self.telemetry.capture_signal('validation_failed', {
                    'query': agent_query,
                    'reason': validation.reason,
                    'failed_rule': validation.failed_rule
                })
                
                return {'success': False, 'reason': 'validation_failed'}
        
        else:
            # Knowledge not found - this is a signal
            self.telemetry.capture_signal('knowledge_missing', {
                'query': agent_query,
                'attempted_graphs': [g.name for g in graphs],
                'context': context
            })
            
            return {'success': False, 'reason': 'knowledge_not_found'}
    
    def _get_relevant_graphs(self, context: Dict) -> List[KnowledgeGraph]:
        """
        Determine which ephemeral graphs are relevant
        """
        graphs = []
        
        # Always include org graph if user context present
        if 'user_id' in context:
            graphs.append(self.org_graph.get_graph())
        
        # Include product graph if product context present
        if 'product' in context or 'service' in context:
            graphs.append(self.product_graph.get_graph())
        
        # Include project context if available
        if 'project_id' in context:
            ctx_graph = self._get_or_create_context_graph(context['project_id'])
            graphs.append(ctx_graph)
        
        return graphs
    
    def _get_or_create_context_graph(self, project_id: str) -> ContextGraph:
        """
        Get existing context graph or create new one
        """
        # Check if exists and not expired
        if project_id in self.context_graphs:
            ctx_graph = self.context_graphs[project_id]
            if not ctx_graph.is_expired():
                return ctx_graph.graph
            else:
                # Expired - destroy and recreate
                ctx_graph.destroy()
                del self.context_graphs[project_id]
        
        # Create new context graph
        ctx_graph = ContextGraph.create_for_project(project_id)
        self.context_graphs[project_id] = ctx_graph
        
        return ctx_graph.graph
    
    def run_healing_cycle(self):
        """
        Periodic background task to analyze signals and heal
        Run every 15 minutes
        """
        print("Running healing cycle...")
        
        # Analyze accumulated signals
        self.analyst.analyze_signals()
        
        # Cleanup expired context graphs
        self._cleanup_expired_contexts()
        
        # Generate health report
        report = self._generate_health_report()
        
        return report
    
    def _cleanup_expired_contexts(self):
        """Remove expired project context graphs"""
        expired = [
            pid for pid, ctx in self.context_graphs.items()
            if ctx.is_expired()
        ]
        
        for pid in expired:
            self.context_graphs[pid].destroy()
            del self.context_graphs[pid]
            print(f"Cleaned up expired context graph: {pid}")
```

## Key Metrics to Track

### 1. Knowledge Freshness
```python
freshness_score = (
    entities_updated_recently / total_entities
)
# Target: > 0.95 (95% of entities updated in last 30 days)
```

### 2. Self-Healing Rate
```python
healing_rate = (
    auto_healed_issues / total_issues_detected
)
# Target: > 0.90 (90% of issues auto-healed without human intervention)
```

### 3. Signal-to-Action Latency
```python
avg_latency = (
    sum(time_to_fix for all critical signals) / critical_signal_count
)
# Target: < 15 minutes for critical signals
```

### 4. Human Review Efficiency
```python
review_efficiency = (
    correct_human_decisions / total_human_reviews
)
# Target: > 0.95 (humans catching real issues 95%+ of time)
```

### 5. Ephemeral Graph Hit Rate
```python
hit_rate = (
    queries_answered_from_ephemeral / total_queries
)
# Target: > 0.80 (80% of queries answered from ephemeral graphs)
```

## Benefits of Recursive Ontologies

### 1. Self-Healing Knowledge
- **Automatic repair**: System detects and fixes knowledge gaps
- **No manual updates**: Evolves based on actual usage patterns
- **Friction-driven**: Updates triggered by real pain points

### 2. Always Current
- **Event-driven**: Graphs rebuild when source data changes
- **No staleness**: Ephemeral nature ensures freshness
- **Zero lag**: Updates propagate in real-time

### 3. Resource Efficient
- **Small graphs**: Only relevant knowledge loaded
- **Automatic cleanup**: Unused graphs garbage collected
- **Focused caching**: Cache only active entities

### 4. Statistically Supervised
- **Human wisdom**: Experts review high-risk changes
- **AI volume**: Automation handles routine updates
- **Continuous learning**: System learns from human feedback

### 5. Scalable Evolution
- **Distributed signals**: Every agent contributes telemetry
- **Parallel healing**: Multiple sectors updated concurrently
- **No coordination overhead**: Each graph independent

## Implementation Checklist

### Phase 1: Telemetry Foundation
- [ ] Implement AgentTelemetry system
- [ ] Define signal types and severities
- [ ] Set up signal storage and analysis
- [ ] Create signal visualization dashboard

### Phase 2: Ephemeral Graphs
- [ ] Implement OrgGraph with HR event triggers
- [ ] Implement ProductGraph with Git webhooks
- [ ] Implement ContextGraph with TTL management
- [ ] Set up automatic cleanup processes

### Phase 3: Analyst System
- [ ] Build pattern detection algorithms
- [ ] Implement healing action queue
- [ ] Create sector rebuild capabilities
- [ ] Set up periodic analysis cycles

### Phase 4: Statistical Supervision
- [ ] Implement sampling strategy
- [ ] Build review dashboard
- [ ] Create human feedback loop
- [ ] Train review prediction model

### Phase 5: Integration
- [ ] Connect all components
- [ ] Implement query routing
- [ ] Set up monitoring and alerting
- [ ] Deploy healing cycle scheduler

## Real-World Examples

### Example 1: HR Event Triggers Org Graph Update

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

### Example 2: Agent Signals Missing Entity

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

### Example 3: Documentation Update Propagates

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

## Conclusion

Recursive Ontologies transform static knowledge graphs into living, self-updating systems:

- **Agents become sensors**: Failures signal knowledge gaps
- **Graphs become ephemeral**: Built on-demand, destroyed when stale
- **Humans become auditors**: Strategic wisdom, not gatekeepers
- **Systems become self-healing**: Automatic evolution based on friction

This is the architecture that doesn't die. It evolves.

## Further Reading

- [Semantic Firewall](./semantic-firewall.md) - The foundation (Part 2)
- [Multidimensional Knowledge Graphs](./multidimensional-knowledge-graphs.md) - The structure (Part 1)
- [Cognitive Systems Architect](./cognitive-systems-architect.md) - The role that manages this
- [Headless Agent](./headless-agent.md) - The protocol for agent coordination (Part 3)
