"""
Example: Recursive Ontology System with Self-Updating Knowledge Graphs

This example demonstrates:
1. Agent telemetry capturing failures as signals
2. Ephemeral knowledge graphs (event-driven, temporary)
3. Statistical supervision (human-in-the-loop sampling)
4. Analyst system for self-healing

NOTE: This example includes a simplified MultidimensionalKnowledgeGraph class
for self-contained demonstration. In production, you would use a shared
knowledge graph library. Each example in this repository is intentionally
self-contained for educational clarity.
"""

import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class SignalType(Enum):
    """Types of signals agents can emit"""
    ENTITY_MISSING = "entity_missing"
    RELATIONSHIP_UNKNOWN = "relationship_unknown"
    KNOWLEDGE_STALE = "knowledge_stale"
    VALIDATION_FAILED = "validation_failed"
    QUERY_FAILED = "query_failed"


class Severity(Enum):
    """Signal severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Signal:
    """A signal emitted by an agent indicating a knowledge gap or issue"""
    type: SignalType
    timestamp: datetime
    context: Dict[str, Any]
    severity: Severity
    agent_id: str
    query: Optional[str] = None


@dataclass
class Pattern:
    """Detected pattern in agent signals"""
    type: str
    severity: str
    occurrences: int
    recommended_action: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphUpdate:
    """Proposed update to knowledge graph"""
    update_type: str  # add_entity, add_relationship, rebuild_sector
    confidence: float
    confidence_variance: float  # How uncertain is the AI?
    impact_radius: int  # How many queries affected?
    entity_type: str
    details: Dict[str, Any]
    sources: List[str] = field(default_factory=list)


@dataclass
class Entity:
    """Entity in knowledge graph"""
    id: str
    name: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Relationship:
    """Relationship between entities"""
    subject: Entity
    predicate: str
    object: Entity
    valid_from: datetime
    valid_until: Optional[datetime] = None
    confidence: float = 1.0
    sources: List[str] = field(default_factory=list)


class MultidimensionalKnowledgeGraph:
    """Basic knowledge graph implementation"""
    
    def __init__(self, name: str = "main"):
        self.name = name
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
    
    def add_entity(self, entity: Entity):
        """Add entity to knowledge graph"""
        self.entities[entity.id] = entity
        self.last_updated = datetime.now()
    
    def add_relationship(self, relationship: Relationship):
        """Add relationship to knowledge graph"""
        self.relationships.append(relationship)
        self.last_updated = datetime.now()
    
    def entity_exists(self, entity_id: str) -> bool:
        """Check if entity exists"""
        return entity_id in self.entities
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return self.entities.get(entity_id)
    
    def query(self, query: str, context: Dict) -> Optional[Any]:
        """Simple query interface"""
        # Simplified: In production, this would be semantic search
        query_lower = query.lower()
        
        # Try to find entities mentioned in query
        for entity in self.entities.values():
            if entity.name.lower() in query_lower:
                return {
                    'found': True,
                    'entity': entity,
                    'graph': self.name
                }
        
        return None


class AgentTelemetry:
    """
    Capture agent failures as signals for knowledge evolution
    Don't force hallucinations - signal knowledge gaps instead
    """
    
    def __init__(self):
        self.signals: List[Signal] = []
        self.analyst = None  # Set later to avoid circular dependency
    
    def capture_signal(self, 
                      signal_type: SignalType, 
                      context: Dict,
                      agent_id: str,
                      query: Optional[str] = None) -> Signal:
        """
        Capture a signal indicating a knowledge gap
        """
        severity = self._calculate_severity(signal_type, context)
        
        signal = Signal(
            type=signal_type,
            timestamp=datetime.now(),
            context=context,
            severity=severity,
            agent_id=agent_id,
            query=query
        )
        
        self.signals.append(signal)
        
        print(f"   📊 Signal captured: {signal_type.value} (severity: {severity.value})")
        
        # Real-time critical signals trigger immediate action
        if severity == Severity.CRITICAL and self.analyst:
            print("   🚨 CRITICAL signal - triggering immediate healing")
            self.analyst.handle_critical_signal(signal)
        
        return signal
    
    def _calculate_severity(self, signal_type: SignalType, context: Dict) -> Severity:
        """
        Calculate severity based on frequency and impact
        """
        frequency = context.get('occurrence_count', 1)
        impact = context.get('affected_agents', 1)
        
        if frequency > 10 and impact > 5:
            return Severity.CRITICAL
        elif frequency > 5 or impact > 3:
            return Severity.HIGH
        elif frequency > 2:
            return Severity.MEDIUM
        return Severity.LOW
    
    def get_recent_signals(self, hours: int = 24) -> List[Signal]:
        """Get signals from the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [s for s in self.signals if s.timestamp > cutoff]


class OrgGraph:
    """
    Ephemeral organizational knowledge graph
    Rebuilt on HR events, not on a schedule
    """
    
    def __init__(self):
        self.graph: Optional[MultidimensionalKnowledgeGraph] = None
        self.last_built: Optional[datetime] = None
        self.rebuild_count = 0
    
    def rebuild(self, event: str):
        """
        Rebuild entire graph from source of truth
        Previous graph is discarded - no migration complexity
        """
        print(f"\n   🔄 Rebuilding OrgGraph due to: {event}")
        self.rebuild_count += 1
        
        # Build new graph (simulated HR data)
        self.graph = MultidimensionalKnowledgeGraph(name="OrgGraph")
        
        # Simulate fetching from HR system
        employees = [
            {'id': 'emp_1', 'name': 'Alice Johnson', 'title': 'Senior Engineer', 'manager': None},
            {'id': 'emp_2', 'name': 'Bob Smith', 'title': 'Engineer', 'manager': 'emp_1'},
            {'id': 'emp_3', 'name': 'Carol White', 'title': 'Engineer', 'manager': 'emp_1'},
        ]
        
        for emp in employees:
            self.graph.add_entity(Entity(
                id=emp['id'],
                name=emp['name'],
                type='employee',
                properties={'title': emp['title']}
            ))
        
        # Add reporting relationships
        self.graph.add_relationship(Relationship(
            subject=self.graph.get_entity('emp_2'),
            predicate='reports_to',
            object=self.graph.get_entity('emp_1'),
            valid_from=datetime.now(),
            sources=['hr_system']
        ))
        
        self.graph.add_relationship(Relationship(
            subject=self.graph.get_entity('emp_3'),
            predicate='reports_to',
            object=self.graph.get_entity('emp_1'),
            valid_from=datetime.now(),
            sources=['hr_system']
        ))
        
        self.last_built = datetime.now()
        
        print(f"   ✓ OrgGraph rebuilt with {len(self.graph.entities)} employees")
        print(f"   ✓ Total rebuilds: {self.rebuild_count}")
    
    def get_graph(self) -> MultidimensionalKnowledgeGraph:
        """Get current graph, rebuild if needed"""
        if not self.graph:
            self.rebuild("initial_build")
        
        # Safety: rebuild if older than 24 hours
        if (datetime.now() - self.last_built) > timedelta(hours=24):
            self.rebuild("safety_rebuild")
        
        return self.graph


class ProductGraph:
    """
    Ephemeral product knowledge graph
    Rebuilt when documentation changes
    """
    
    def __init__(self):
        self.graph: Optional[MultidimensionalKnowledgeGraph] = None
        self.last_commit: Optional[str] = None
        self.rebuild_count = 0
    
    def rebuild_from_docs(self, commit: str):
        """
        Parse documentation to build knowledge graph
        Documentation IS the knowledge graph
        """
        # Safely truncate commit hash
        commit_short = commit[:min(len(commit), 7)]
        print(f"\n   📚 Rebuilding ProductGraph from commit: {commit_short}")
        self.rebuild_count += 1
        
        # Build new graph
        self.graph = MultidimensionalKnowledgeGraph(name="ProductGraph")
        
        # Simulate parsing docs
        products = [
            {'id': 'prod_auth', 'name': 'Authentication Service', 'type': 'service'},
            {'id': 'prod_api', 'name': 'API Gateway', 'type': 'service'},
            {'id': 'prod_db', 'name': 'Database', 'type': 'infrastructure'},
        ]
        
        for prod in products:
            self.graph.add_entity(Entity(
                id=prod['id'],
                name=prod['name'],
                type=prod['type'],
                properties={'documented': True}
            ))
        
        # Add dependencies
        self.graph.add_relationship(Relationship(
            subject=self.graph.get_entity('prod_api'),
            predicate='depends_on',
            object=self.graph.get_entity('prod_auth'),
            valid_from=datetime.now(),
            sources=['docs/architecture.md']
        ))
        
        self.last_commit = commit
        
        print(f"   ✓ ProductGraph rebuilt with {len(self.graph.entities)} products")
        print(f"   ✓ Total rebuilds: {self.rebuild_count}")
    
    def get_graph(self) -> MultidimensionalKnowledgeGraph:
        """Get current graph"""
        if not self.graph:
            self.rebuild_from_docs("initial_commit")
        
        return self.graph


class ContextGraph:
    """
    Ephemeral context graph for a specific project
    Exists only for the duration of a project
    """
    
    def __init__(self, project_id: str, ttl_hours: int = 720):
        self.project_id = project_id
        self.graph = MultidimensionalKnowledgeGraph(name=f"Context-{project_id}")
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(hours=ttl_hours)
        self.last_accessed = datetime.now()
        self.access_count = 0
        
        # Build project-specific knowledge
        self._build_project_context()
    
    def _build_project_context(self):
        """Load project-specific entities"""
        # Simulate loading project data
        team_members = [
            {'id': f'proj_{self.project_id}_user_1', 'name': 'Project Lead', 'role': 'lead'},
            {'id': f'proj_{self.project_id}_user_2', 'name': 'Developer', 'role': 'dev'},
        ]
        
        for member in team_members:
            self.graph.add_entity(Entity(
                id=member['id'],
                name=member['name'],
                type='team_member',
                properties={'role': member['role'], 'project': self.project_id}
            ))
    
    def is_expired(self) -> bool:
        """Check if context should be destroyed"""
        if datetime.now() > self.expires_at:
            return True
        
        # Also expire if not accessed in 7 days
        if (datetime.now() - self.last_accessed) > timedelta(days=7):
            return True
        
        return False
    
    def access(self):
        """Record access"""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def destroy(self):
        """Explicitly destroy the graph"""
        print(f"   🗑️  Destroying ContextGraph for project {self.project_id}")
        self.graph = None


class StatisticalSupervisor:
    """
    Human-in-the-loop strategy based on statistical sampling
    Humans provide Wisdom, AI handles Volume
    """
    
    def __init__(self, sample_rate: float = 0.05):
        self.sample_rate = sample_rate  # 5% default
        self.review_queue: List[Dict] = []
        self.confidence_threshold = 0.95
        self.decisions: List[Dict] = []
    
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
        """Add update to human review queue"""
        priority = self._calculate_priority(update)
        
        self.review_queue.append({
            'update': update,
            'queued_at': datetime.now(),
            'priority': priority
        })
        
        print(f"   👤 Queued for human review (priority: {priority})")
    
    def _calculate_priority(self, update: GraphUpdate) -> str:
        """Calculate review priority"""
        if update.confidence_variance > 0.5 or update.impact_radius > 100:
            return 'high'
        elif update.confidence_variance > 0.3 or update.impact_radius > 50:
            return 'medium'
        return 'low'
    
    def simulate_human_review(self, update: GraphUpdate) -> bool:
        """Simulate human approval (for demo purposes)"""
        # In production, this would be actual human review
        # For demo, approve if confidence > 0.7
        approved = update.confidence > 0.7
        
        decision = {
            'update_type': update.update_type,
            'approved': approved,
            'confidence': update.confidence,
            'timestamp': datetime.now()
        }
        self.decisions.append(decision)
        
        return approved


class AnalystSystem:
    """
    Background system that analyzes signals and triggers knowledge evolution
    The brain of the self-healing system
    """
    
    def __init__(self, telemetry: AgentTelemetry, supervisor: StatisticalSupervisor):
        self.telemetry = telemetry
        self.supervisor = supervisor
        self.healing_actions: List[Dict] = []
    
    def analyze_signals(self):
        """
        Analyze accumulated signals to detect patterns
        """
        print("\n🔍 Analyzing signals...")
        
        signals = self.telemetry.get_recent_signals(hours=24)
        
        if not signals:
            print("   No signals to analyze")
            return []
        
        print(f"   Found {len(signals)} signals")
        
        # Detect patterns
        patterns = self._detect_patterns(signals)
        
        print(f"   Detected {len(patterns)} patterns")
        
        # Trigger healing actions
        for pattern in patterns:
            self._handle_pattern(pattern)
        
        return patterns
    
    def _detect_patterns(self, signals: List[Signal]) -> List[Pattern]:
        """Find meaningful patterns in agent failures"""
        patterns = []
        
        # Pattern 1: Same entity missing repeatedly
        entity_misses = defaultdict(int)
        for signal in signals:
            if signal.type == SignalType.ENTITY_MISSING:
                entity_id = signal.context.get('entity_id', 'unknown')
                entity_misses[entity_id] += 1
        
        for entity_id, count in entity_misses.items():
            if count > 2:  # Threshold for demo
                patterns.append(Pattern(
                    type='missing_entity',
                    severity='high',
                    occurrences=count,
                    recommended_action='add_entity',
                    metadata={'entity_id': entity_id}
                ))
        
        # Pattern 2: High failure rate in specific graph
        graph_failures = defaultdict(int)
        for signal in signals:
            graph = signal.context.get('graph', 'unknown')
            if signal.type == SignalType.QUERY_FAILED:
                graph_failures[graph] += 1
        
        for graph, count in graph_failures.items():
            if count > 3:  # Threshold for demo
                patterns.append(Pattern(
                    type='stale_graph',
                    severity='critical',
                    occurrences=count,
                    recommended_action='rebuild_graph',
                    metadata={'graph': graph}
                ))
        
        return patterns
    
    def _handle_pattern(self, pattern: Pattern):
        """Handle detected pattern"""
        print(f"\n   🔧 Handling pattern: {pattern.type} ({pattern.severity})")
        print(f"      Occurrences: {pattern.occurrences}")
        print(f"      Action: {pattern.recommended_action}")
        
        # Create update proposal
        update = GraphUpdate(
            update_type=pattern.recommended_action,
            confidence=0.85,
            confidence_variance=0.2,
            impact_radius=pattern.occurrences * 10,
            entity_type='general',
            details=pattern.metadata,
            sources=['analyst_system']
        )
        
        # Check if human review needed
        if self.supervisor.should_review(update):
            self.supervisor.queue_for_review(update)
            
            # Simulate human review
            approved = self.supervisor.simulate_human_review(update)
            
            if approved:
                print("      ✓ Human approved - applying update")
                self._apply_update(update)
            else:
                print("      ✗ Human rejected - update not applied")
        else:
            print("      ⚡ Auto-applying (low risk)")
            self._apply_update(update)
        
        # Record healing action
        self.healing_actions.append({
            'pattern': pattern,
            'update': update,
            'timestamp': datetime.now()
        })
    
    def _apply_update(self, update: GraphUpdate):
        """Apply the update to knowledge graph"""
        # In production, this would actually update the graph
        print(f"      ✓ Update applied: {update.update_type}")
    
    def handle_critical_signal(self, signal: Signal):
        """Handle critical signal immediately"""
        print("      🚨 Critical signal - immediate action required")
        
        # Take immediate action without waiting for batch analysis
        if signal.type == SignalType.ENTITY_MISSING:
            entity_id = signal.context.get('entity_id', 'unknown')
            print(f"      ⚡ Auto-discovering entity: {entity_id}")
            # In production: trigger entity discovery process


class RecursiveOntologySystem:
    """
    Complete self-updating semantic firewall system
    Integrates all components for autonomous knowledge evolution
    """
    
    def __init__(self):
        # Core components
        self.knowledge_graph = MultidimensionalKnowledgeGraph(name="Core")
        
        # Feedback loop components
        self.telemetry = AgentTelemetry()
        self.supervisor = StatisticalSupervisor(sample_rate=0.05)
        self.analyst = AnalystSystem(self.telemetry, self.supervisor)
        
        # Connect telemetry to analyst
        self.telemetry.analyst = self.analyst
        
        # Ephemeral graph managers
        self.org_graph = OrgGraph()
        self.product_graph = ProductGraph()
        self.context_graphs: Dict[str, ContextGraph] = {}
        
        self.query_count = 0
    
    def query(self, agent_query: str, agent_id: str, context: Dict) -> Dict:
        """
        Process agent query with feedback loop
        """
        self.query_count += 1
        
        print(f"\n{'='*60}")
        print(f"Query #{self.query_count}: \"{agent_query}\"")
        print(f"Agent: {agent_id}")
        print(f"{'='*60}")
        
        # Get relevant ephemeral graphs
        graphs = self._get_relevant_graphs(context)
        
        print(f"   📊 Querying {len(graphs)} knowledge graphs:")
        for g in graphs:
            print(f"      - {g.name}")
        
        # Try to answer from knowledge
        result = None
        for graph in graphs:
            result = graph.query(agent_query, context)
            if result:
                print(f"   ✓ Found in {graph.name}")
                break
        
        if result:
            return {
                'success': True,
                'answer': result,
                'source_graph': result['graph']
            }
        else:
            # Knowledge not found - this is a signal!
            print("   ✗ Not found in any graph")
            
            # Extract entity ID from query (avoid redundant split)
            query_parts = agent_query.split()
            entity_id = query_parts[-1] if query_parts else 'unknown'
            
            self.telemetry.capture_signal(
                signal_type=SignalType.ENTITY_MISSING,
                context={
                    'entity_id': entity_id,
                    'attempted_graphs': [g.name for g in graphs],
                    'occurrence_count': 1
                },
                agent_id=agent_id,
                query=agent_query
            )
            
            return {
                'success': False,
                'reason': 'knowledge_not_found',
                'signal_captured': True
            }
    
    def _get_relevant_graphs(self, context: Dict) -> List[MultidimensionalKnowledgeGraph]:
        """Determine which ephemeral graphs are relevant"""
        graphs = [self.knowledge_graph]  # Always include core
        
        # Include org graph if user context present
        if 'user_id' in context:
            graphs.append(self.org_graph.get_graph())
        
        # Include product graph if product context present
        if 'product' in context or 'service' in context:
            graphs.append(self.product_graph.get_graph())
        
        # Include project context if available
        if 'project_id' in context:
            ctx_graph = self._get_or_create_context_graph(context['project_id'])
            graphs.append(ctx_graph.graph)
        
        return graphs
    
    def _get_or_create_context_graph(self, project_id: str) -> ContextGraph:
        """Get existing context graph or create new one"""
        if project_id in self.context_graphs:
            ctx_graph = self.context_graphs[project_id]
            if not ctx_graph.is_expired():
                ctx_graph.access()
                return ctx_graph
            else:
                # Expired - destroy and recreate
                ctx_graph.destroy()
                del self.context_graphs[project_id]
        
        # Create new context graph
        print(f"   🆕 Creating new ContextGraph for project: {project_id}")
        ctx_graph = ContextGraph(project_id=project_id)
        self.context_graphs[project_id] = ctx_graph
        
        return ctx_graph
    
    def run_healing_cycle(self):
        """
        Periodic background task to analyze signals and heal
        Run every 15 minutes in production
        """
        print("\n" + "="*60)
        print("🏥 HEALING CYCLE")
        print("="*60)
        
        # Analyze accumulated signals. The analyst queues healing actions as a side effect.
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
    
    def _generate_health_report(self) -> Dict:
        """Generate system health report"""
        signals = self.telemetry.get_recent_signals(hours=24)
        
        report = {
            'total_queries': self.query_count,
            'total_signals': len(signals),
            'signal_types': {},
            'healing_actions': len(self.analyst.healing_actions),
            'human_reviews': len(self.supervisor.review_queue),
            'active_context_graphs': len(self.context_graphs),
            'org_graph_rebuilds': self.org_graph.rebuild_count,
            'product_graph_rebuilds': self.product_graph.rebuild_count
        }
        
        # Count signal types
        for signal in signals:
            signal_type = signal.type.value
            report['signal_types'][signal_type] = report['signal_types'].get(signal_type, 0) + 1
        
        print("\n📈 HEALTH REPORT")
        print(f"   Total Queries: {report['total_queries']}")
        print(f"   Total Signals: {report['total_signals']}")
        print(f"   Healing Actions: {report['healing_actions']}")
        print(f"   Human Reviews Queued: {report['human_reviews']}")
        print(f"   Active Context Graphs: {report['active_context_graphs']}")
        print(f"   OrgGraph Rebuilds: {report['org_graph_rebuilds']}")
        print(f"   ProductGraph Rebuilds: {report['product_graph_rebuilds']}")
        
        if report['signal_types']:
            print("\n   Signals by Type:")
            for sig_type, count in report['signal_types'].items():
                print(f"      {sig_type}: {count}")
        
        return report
    
    def trigger_event(self, event_type: str, event_data: Dict):
        """Simulate external event triggering graph rebuild"""
        print(f"\n🔔 Event: {event_type}")
        
        if event_type == 'hr.employee_hired':
            self.org_graph.rebuild(f"employee_hired: {event_data.get('name', 'unknown')}")
        
        elif event_type == 'git.docs_updated':
            self.product_graph.rebuild_from_docs(event_data.get('commit', 'unknown'))


def main():
    """Run the recursive ontology example"""
    print("="*60)
    print("RECURSIVE ONTOLOGY SYSTEM")
    print("Self-Updating Semantic Firewalls")
    print("="*60)
    print("SIMULATION. No model is called. Every latency and cost printed below")
    print("is a constant written into this file so the control flow is readable.")
    print("None of it is a measurement. See CONTRIBUTING.md for the standard.")
    print()
    
    # Create the system
    print("\n1. Initializing Recursive Ontology System...")
    system = RecursiveOntologySystem()
    print("   ✓ System initialized")
    
    # Scenario 1: Query finds answer in ephemeral graph
    print("\n2. Scenario: Query Answered from Ephemeral Graph")
    print("-"*60)
    result = system.query(
        agent_query="Who is Alice Johnson?",
        agent_id="agent_1",
        context={'user_id': 'user_123'}
    )
    print(f"   Result: {'✓ SUCCESS' if result['success'] else '✗ FAILED'}")
    
    # Scenario 2: Query fails, signal captured
    print("\n3. Scenario: Query Fails, Signal Captured")
    print("-"*60)
    result = system.query(
        agent_query="What is Project Phoenix?",
        agent_id="agent_2",
        context={'project_id': 'proj_phoenix'}
    )
    print(f"   Result: {'✓ SUCCESS' if result['success'] else '✗ FAILED'}")
    print(f"   Signal Captured: {result.get('signal_captured', False)}")
    
    # Multiple queries for same missing entity to trigger pattern detection
    print("\n4. Scenario: Repeated Failures Create Pattern")
    print("-"*60)
    for i in range(3):
        result = system.query(
            agent_query="What is Project Phoenix status?",
            agent_id=f"agent_{i+3}",
            context={'project_id': 'proj_phoenix'}
        )
    
    # Scenario 3: External event triggers graph rebuild
    print("\n5. Scenario: HR Event Triggers OrgGraph Rebuild")
    print("-"*60)
    system.trigger_event('hr.employee_hired', {'name': 'David Brown', 'title': 'Engineer'})
    
    # Scenario 4: Documentation update triggers ProductGraph rebuild
    print("\n6. Scenario: Documentation Update Triggers Rebuild")
    print("-"*60)
    system.trigger_event('git.docs_updated', {'commit': 'abc123', 'files': ['docs/api.md']})
    
    # Run healing cycle
    print("\n7. Scenario: Automated Healing Cycle")
    print("-"*60)
    system.run_healing_cycle()
    
    # Final Summary
    print("\n" + "="*60)
    print("SUMMARY: Key Benefits Demonstrated")
    print("="*60)
    print("\n✓ Feedback Loop:")
    print("  - Agent failures captured as signals")
    print("  - No hallucinations - system signals knowledge gaps")
    print("  - Signals drive automatic knowledge evolution")
    
    print("\n✓ Ephemeral Graphs:")
    print("  - OrgGraph rebuilt on HR events")
    print("  - ProductGraph rebuilt on doc changes")
    print("  - ContextGraph created per-project, auto-expires")
    print("  - No staleness - always current")
    
    print("\n✓ Statistical Supervision:")
    print("  - 95% auto-healed, 5% human reviewed")
    print("  - Humans provide wisdom, AI handles volume")
    print("  - High-risk updates always reviewed")
    
    print("\n✓ Self-Healing:")
    print("  - Pattern detection from signals")
    print("  - Automatic knowledge updates")
    print("  - System evolves based on actual usage")
    
    print("\n" + "="*60)
    print("Architecture Insight:")
    print("-"*60)
    print("Traditional Approach:")
    print("  Static KB → Becomes stale → Manual updates → Bottleneck")
    
    print("\nRecursive Ontology Approach:")
    print("  Agent signals → Pattern detection → Auto-healing → Always current")
    print("\nThe system doesn't die. It evolves.")
    print("="*60)


if __name__ == "__main__":
    main()
