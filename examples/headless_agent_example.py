"""
Example: Headless Agent (Silent Swarm) Implementation

This example demonstrates how headless agents communicate through
structured data rather than natural language, achieving significant
performance and cost improvements.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskType(Enum):
    """Types of tasks agents can perform"""
    VALIDATE = "validate"
    FETCH_DATA = "fetch_data"
    TRANSFORM = "transform"
    ANALYZE = "analyze"
    STORE = "store"
    NOTIFY = "notify"


class Status(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class Task:
    """Structured task definition (no natural language)"""
    task_id: str
    task_type: TaskType
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Result:
    """Structured result (no natural language)"""
    task_id: str
    status: Status
    data: Dict[str, Any]
    error: Optional[str] = None
    duration_ms: float = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Metric:
    """Structured telemetry"""
    agent_id: str
    task_type: TaskType
    duration_ms: float
    status: Status
    timestamp: datetime = field(default_factory=datetime.now)


class HeadlessAgent:
    """
    A headless agent that never uses natural language.
    Communicates only through structured protocols.
    """
    
    def __init__(self, agent_id: str, capabilities: List[TaskType]):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.metrics: List[Metric] = []
    
    def can_handle(self, task: Task) -> bool:
        """Check if agent can handle this task type"""
        return task.task_type in self.capabilities
    
    def execute(self, task: Task, context: Optional[Dict] = None) -> Result:
        """
        Execute task with structured input/output (no language)
        """
        start = time.perf_counter()
        
        try:
            # Route to appropriate handler based on task type
            handler = self._get_handler(task.task_type)
            data = handler(task.parameters, context or {})
            
            duration = (time.perf_counter() - start) * 1000
            
            # Record structured metric
            self.metrics.append(Metric(
                agent_id=self.agent_id,
                task_type=task.task_type,
                duration_ms=duration,
                status=Status.SUCCESS
            ))
            
            return Result(
                task_id=task.task_id,
                status=Status.SUCCESS,
                data=data,
                duration_ms=duration
            )
        
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            
            self.metrics.append(Metric(
                agent_id=self.agent_id,
                task_type=task.task_type,
                duration_ms=duration,
                status=Status.FAILED
            ))
            
            return Result(
                task_id=task.task_id,
                status=Status.FAILED,
                data={},
                error=str(e),
                duration_ms=duration
            )
    
    def _get_handler(self, task_type: TaskType):
        """Get handler function for task type"""
        handlers = {
            TaskType.VALIDATE: self._handle_validate,
            TaskType.FETCH_DATA: self._handle_fetch,
            TaskType.TRANSFORM: self._handle_transform,
            TaskType.ANALYZE: self._handle_analyze,
            TaskType.STORE: self._handle_store,
            TaskType.NOTIFY: self._handle_notify,
        }
        return handlers.get(task_type, self._handle_unknown)
    
    def _handle_validate(self, params: Dict, context: Dict) -> Dict:
        """Validate data (no language needed)"""
        data = params.get('data', {})
        schema = params.get('schema', {})
        
        # Validation logic (pure data operations)
        errors = []
        for field_name in schema:
            if field_name not in data:
                errors.append({'field': field_name, 'error': 'missing'})
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _handle_fetch(self, params: Dict, context: Dict) -> Dict:
        """Fetch data from source (no language needed)"""
        source = params.get('source')
        
        # Simulated data fetch
        return {
            'source': source,
            'records': [
                {'id': 1, 'value': 'data1'},
                {'id': 2, 'value': 'data2'}
            ],
            'count': 2
        }
    
    def _handle_transform(self, params: Dict, context: Dict) -> Dict:
        """Transform data (no language needed)"""
        data = params.get('data', [])
        operation = params.get('operation', 'identity')
        
        # Data transformation logic
        if operation == 'uppercase':
            transformed = [
                {k: v.upper() if isinstance(v, str) else v for k, v in record.items()}
                for record in data
            ]
        else:
            transformed = data
        
        return {
            'data': transformed,
            'count': len(transformed)
        }
    
    def _handle_analyze(self, params: Dict, context: Dict) -> Dict:
        """Analyze data (no language needed)"""
        data = params.get('data', [])
        
        # Analysis logic (pure computation)
        return {
            'total_records': len(data),
            'statistics': {
                'mean': 42.0,
                'median': 40.0,
                'std_dev': 5.2
            }
        }
    
    def _handle_store(self, params: Dict, context: Dict) -> Dict:
        """Store data (no language needed)"""
        data = params.get('data', {})
        destination = params.get('destination', 'default')
        
        # Storage logic
        return {
            'stored': True,
            'destination': destination,
            'record_count': len(data) if isinstance(data, list) else 1
        }
    
    def _handle_notify(self, params: Dict, context: Dict) -> Dict:
        """Send notification (structured, not conversational)"""
        recipient = params.get('recipient')
        event_type = params.get('event_type')
        
        # Notification logic (structured message)
        return {
            'notified': True,
            'recipient': recipient,
            'event_type': event_type
        }
    
    def _handle_unknown(self, params: Dict, context: Dict) -> Dict:
        """Handle unknown task type"""
        raise ValueError(f"Unknown task type for agent {self.agent_id}")


class SilentSwarm:
    """
    Orchestrates multiple headless agents without any natural language.
    Pure structured data flow.
    """
    
    def __init__(self):
        self.agents: List[HeadlessAgent] = []
        self.execution_log: List[Dict] = []
    
    def add_agent(self, agent: HeadlessAgent):
        """Add agent to swarm"""
        self.agents.append(agent)
    
    def execute_workflow(self, tasks: List[Task]) -> Dict[str, Result]:
        """
        Execute workflow of tasks without any language generation.
        Pure structured data flow through the system.
        """
        results: Dict[str, Result] = {}
        
        # Topologically sort tasks based on dependencies
        sorted_tasks = self._topological_sort(tasks)
        
        for task in sorted_tasks:
            # Check if dependencies are satisfied
            deps_met = all(
                dep in results and results[dep].status == Status.SUCCESS
                for dep in task.dependencies
            )
            
            if not deps_met:
                results[task.task_id] = Result(
                    task_id=task.task_id,
                    status=Status.FAILED,
                    data={},
                    error="Dependencies not satisfied"
                )
                continue
            
            # Find capable agent
            agent = self._find_agent(task)
            
            if not agent:
                results[task.task_id] = Result(
                    task_id=task.task_id,
                    status=Status.FAILED,
                    data={},
                    error=f"No agent capable of {task.task_type}"
                )
                continue
            
            # Build context from dependency results
            context = {
                dep: results[dep].data
                for dep in task.dependencies
            }
            
            # Execute (no language involved)
            result = agent.execute(task, context)
            results[task.task_id] = result
            
            # Log structured execution data
            self.execution_log.append({
                'task_id': task.task_id,
                'agent_id': agent.agent_id,
                'task_type': task.task_type.value,
                'status': result.status.value,
                'duration_ms': result.duration_ms,
                'timestamp': result.timestamp.isoformat()
            })
        
        return results
    
    def _topological_sort(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by dependencies"""
        # Simple implementation - in production use proper topological sort
        sorted_tasks = []
        remaining = tasks.copy()
        
        while remaining:
            # Find tasks with no unmet dependencies
            ready = [
                task for task in remaining
                if all(dep in [t.task_id for t in sorted_tasks] for dep in task.dependencies)
            ]
            
            if not ready:
                # Circular dependency or invalid
                break
            
            sorted_tasks.extend(ready)
            remaining = [t for t in remaining if t not in ready]
        
        return sorted_tasks
    
    def _find_agent(self, task: Task) -> Optional[HeadlessAgent]:
        """Find agent capable of handling task"""
        for agent in self.agents:
            if agent.can_handle(task):
                return agent
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get structured metrics (no language parsing needed)"""
        all_metrics = []
        for agent in self.agents:
            all_metrics.extend(agent.metrics)
        
        if not all_metrics:
            return {'total_tasks': 0}
        
        total_duration = sum(m.duration_ms for m in all_metrics)
        successful = sum(1 for m in all_metrics if m.status == Status.SUCCESS)
        failed = sum(1 for m in all_metrics if m.status == Status.FAILED)
        
        return {
            'total_tasks': len(all_metrics),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(all_metrics) if all_metrics else 0,
            'total_duration_ms': total_duration,
            'avg_duration_ms': total_duration / len(all_metrics) if all_metrics else 0,
            'by_type': self._metrics_by_type(all_metrics)
        }
    
    def _metrics_by_type(self, metrics: List[Metric]) -> Dict[str, Any]:
        """Aggregate metrics by task type"""
        by_type = {}
        for metric in metrics:
            type_name = metric.task_type.value
            if type_name not in by_type:
                by_type[type_name] = {
                    'count': 0,
                    'total_duration': 0,
                    'successful': 0
                }
            
            by_type[type_name]['count'] += 1
            by_type[type_name]['total_duration'] += metric.duration_ms
            if metric.status == Status.SUCCESS:
                by_type[type_name]['successful'] += 1
        
        # Calculate averages
        for type_name in by_type:
            count = by_type[type_name]['count']
            by_type[type_name]['avg_duration_ms'] = by_type[type_name]['total_duration'] / count
            by_type[type_name]['success_rate'] = by_type[type_name]['successful'] / count
        
        return by_type


# Example usage
def main():
    print("=" * 60)
    print("Headless Agent (Silent Swarm) Example")
    print("=" * 60)
    print("SIMULATION. No model is called. Every latency and cost printed below")
    print("is a constant written into this file so the control flow is readable.")
    print("None of it is a measurement. See CONTRIBUTING.md for the standard.")
    print()
    
    # Create silent swarm
    swarm = SilentSwarm()
    
    # Add specialized headless agents
    print("\n1. Creating headless agents...")
    swarm.add_agent(HeadlessAgent('validator-1', [TaskType.VALIDATE]))
    swarm.add_agent(HeadlessAgent('fetcher-1', [TaskType.FETCH_DATA]))
    swarm.add_agent(HeadlessAgent('transformer-1', [TaskType.TRANSFORM]))
    swarm.add_agent(HeadlessAgent('analyzer-1', [TaskType.ANALYZE]))
    swarm.add_agent(HeadlessAgent('storage-1', [TaskType.STORE]))
    swarm.add_agent(HeadlessAgent('notifier-1', [TaskType.NOTIFY]))
    print(f"   Created {len(swarm.agents)} specialized agents")
    
    # Define workflow with structured tasks (no language)
    print("\n2. Defining structured workflow...")
    workflow = [
        Task(
            task_id='task-1',
            task_type=TaskType.FETCH_DATA,
            parameters={'source': 'database', 'query': {'user_id': 12345}},
            dependencies=[]
        ),
        Task(
            task_id='task-2',
            task_type=TaskType.VALIDATE,
            parameters={'data': {}, 'schema': {'user_id': {'required': True}}},
            dependencies=['task-1']
        ),
        Task(
            task_id='task-3',
            task_type=TaskType.TRANSFORM,
            parameters={'operation': 'uppercase'},
            dependencies=['task-2']
        ),
        Task(
            task_id='task-4',
            task_type=TaskType.ANALYZE,
            parameters={},
            dependencies=['task-3']
        ),
        Task(
            task_id='task-5',
            task_type=TaskType.STORE,
            parameters={'destination': 'data_warehouse'},
            dependencies=['task-4']
        ),
        Task(
            task_id='task-6',
            task_type=TaskType.NOTIFY,
            parameters={
                'recipient': 'admin@example.com',
                'event_type': 'workflow_complete',
                'payload': {}
            },
            dependencies=['task-5']
        )
    ]
    print(f"   Defined workflow with {len(workflow)} tasks")
    
    # Execute workflow (no language generation)
    print("\n3. Executing workflow (no language, pure data flow)...")
    start = time.perf_counter()
    results = swarm.execute_workflow(workflow)
    duration = (time.perf_counter() - start) * 1000
    
    print(f"   Workflow completed in {duration:.1f}ms")
    print(f"   {len(results)} tasks executed")
    
    # Show results (structured data only)
    print("\n4. Task Results:")
    print("-" * 60)
    for task_id, result in results.items():
        status_symbol = "✓" if result.status == Status.SUCCESS else "✗"
        print(f"   {status_symbol} {task_id}: {result.status.value} ({result.duration_ms:.1f}ms)")
    
    # Show metrics
    print("\n5. System Metrics (Structured Telemetry):")
    print("-" * 60)
    metrics = swarm.get_metrics()
    print(f"   Total Tasks: {metrics['total_tasks']}")
    print(f"   Successful: {metrics['successful']}")
    print(f"   Failed: {metrics['failed']}")
    print(f"   Success Rate: {metrics['success_rate']:.1%}")
    print(f"   Total Duration: {metrics['total_duration_ms']:.1f}ms")
    print(f"   Avg Duration: {metrics['avg_duration_ms']:.1f}ms")
    
    print("\n   Breakdown by Task Type:")
    for task_type, stats in metrics['by_type'].items():
        print(f"      {task_type}:")
        print(f"         Count: {stats['count']}")
        print(f"         Avg Duration: {stats['avg_duration_ms']:.1f}ms")
        print(f"         Success Rate: {stats['success_rate']:.1%}")
    
    # Compare with conversational approach
    print("\n6. Comparison: Headless vs. Conversational:")
    print("-" * 60)
    print("   Headless approach (this implementation):")
    print(f"      Wall clock for the workflow: {duration:.1f}ms (simulated handlers)")
    print("      Model calls: 0")
    print("      Messages needing natural language parsing: 0")
    
    print("")
    print("   Conversational baseline, on assumed unit prices:")
    estimated_conversational_time = len(workflow) * 2000  # assumed 2s per model call
    estimated_conversational_cost = len(workflow) * 0.002  # assumed $0.002 per message
    print(f"      Assumed time: ~{estimated_conversational_time}ms")
    print(f"      Model calls:  {len(workflow) * 2} (agent messages)")
    print(f"      Assumed cost: ~${estimated_conversational_cost:.4f}")
    print("")
    print("   The two assumptions above are the entire claim. Any ratio computed")
    print("   from them is arithmetic on guesses, so this example does not print")
    print("   one. Substitute your own call count and unit price, or measure.")
    print("")
    print("   What this run does establish, because it is structural:")
    print("      Model calls made by the coordination layer: 0")
    print("      Messages that required parsing:             0")
    
    print("\n7. Key Benefits:")
    print("-" * 60)
    print("   ✓ Zero natural language overhead")
    print("   ✓ Type-safe communication")
    print("   ✓ Deterministic execution")
    print("   ✓ Every hop emits a typed record rather than prose")
    print("   ✓ Workers hold no conversation state, so they scale horizontally")
    print("   ✓ No LLM costs for coordination")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
