"""
Example: Guardrail Router Implementation

This example demonstrates how to build a Guardrail Router that prevents
the "Inference Trap" by intelligently routing requests between fast lookup
and expensive reasoning operations.

Key Concepts:
- Request classification without expensive processing
- Constraint enforcement to maintain 80-90% lookup ratio
- Metrics tracking for optimization
- Automatic caching of reasoning results
"""

import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class LookupResult:
    """Result from lookup operation"""
    found: bool
    data: Any
    source: str  # 'cache', 'vector_db', 'database'
    confidence: float
    latency_ms: float
    cost: float


@dataclass
class ReasoningResult:
    """Result from reasoning operation"""
    data: Any
    latency_ms: float
    cost: float


class RequestClassifier:
    """
    Fast classification of requests into lookup vs. reasoning categories.
    Uses pattern matching for speed (~1-10ms).
    """
    
    # Define request patterns
    LOOKUP_PATTERNS = {
        'factual': [r'\bwhat is\b', r'\bwho is\b', r'\bwhen did\b', r'\bwhere is\b'],
        'documentation': [r'\bhow do i\b', r'\bhow to\b', r'\btutorial\b', r'\bguide\b'],
        'historical': [r'\bhistory of\b', r'\bpast\b', r'\bpreviously\b'],
        'status': [r'\bstatus\b', r'\bcurrent\b', r'\blatest\b', r'\bnow\b'],
    }
    
    REASONING_PATTERNS = {
        'synthesis': [r'\bcombine\b', r'\bmerge\b', r'\bintegrate\b', r'\bsynthesize\b'],
        'novel': [r'\bdesign\b', r'\bcreate\b', r'\bbuild\b', r'\barchitect\b'],
        'adaptation': [r'\bmodify\b', r'\badapt\b', r'\bchange\b', r'\bcustomize\b'],
        'analysis': [r'\banalyze\b', r'\bcompare\b', r'\bevaluate\b', r'\bassess\b'],
    }
    
    def classify(self, request: str) -> str:
        """
        Classify request type.
        Returns: 'lookup' or 'reasoning'
        """
        request_lower = request.lower()
        
        # Check lookup patterns
        for patterns in self.LOOKUP_PATTERNS.values():
            for pattern in patterns:
                if re.search(pattern, request_lower):
                    return 'lookup'
        
        # Check reasoning patterns
        for patterns in self.REASONING_PATTERNS.values():
            for pattern in patterns:
                if re.search(pattern, request_lower):
                    return 'reasoning'
        
        # Default to lookup (safer, cheaper)
        return 'lookup'


class ConstraintEnforcer:
    """
    Enforces hard limits on reasoning usage to maintain target ratio.
    """
    
    def __init__(self, max_reasoning_ratio: float = 0.2):
        self.max_reasoning_ratio = max_reasoning_ratio
        self.reasoning_count = 0
        self.lookup_count = 0
    
    @property
    def total_count(self) -> int:
        return self.reasoning_count + self.lookup_count
    
    def can_use_reasoning(self) -> bool:
        """
        Check if we're within reasoning budget.
        """
        if self.total_count == 0:
            return True
        
        current_ratio = self.reasoning_count / self.total_count
        
        # Allow reasoning if we're under the limit
        # Use a buffer to prevent hitting exactly at limit
        return current_ratio < (self.max_reasoning_ratio * 0.95)
    
    def record_lookup(self):
        """Record a lookup operation"""
        self.lookup_count += 1
    
    def record_reasoning(self):
        """Record a reasoning operation"""
        self.reasoning_count += 1
    
    def get_ratio(self) -> float:
        """Get current reasoning ratio"""
        if self.total_count == 0:
            return 0.0
        return self.reasoning_count / self.total_count
    
    def get_lookup_ratio(self) -> float:
        """Get current lookup ratio"""
        if self.total_count == 0:
            return 0.0
        return self.lookup_count / self.total_count


class LookupHandler:
    """
    Handles all lookup operations with multi-tier strategy.
    """
    
    def __init__(self):
        self.cache = {}  # In-memory cache
        self.vector_store = {}  # Simulated vector database
        self.database = {}  # Simulated database
    
    def try_lookup(self, request: str) -> LookupResult:
        """
        Try to find answer through lookup operations.
        """
        # Tier 1: Exact cache match
        if request in self.cache:
            return LookupResult(
                found=True,
                data=self.cache[request],
                source='cache',
                confidence=1.0,
                latency_ms=1,
                cost=0.0001
            )
        
        # Tier 2: Semantic similarity search
        similar = self._semantic_search(request)
        if similar and similar['confidence'] > 0.85:
            return LookupResult(
                found=True,
                data=similar['data'],
                source='vector_store',
                confidence=similar['confidence'],
                latency_ms=100,
                cost=0.001
            )
        
        # Tier 3: Database lookup
        db_result = self._database_lookup(request)
        if db_result:
            return LookupResult(
                found=True,
                data=db_result,
                source='database',
                confidence=1.0,
                latency_ms=200,
                cost=0.002
            )
        
        # Not found
        return LookupResult(
            found=False,
            data=None,
            source='none',
            confidence=0.0,
            latency_ms=0,
            cost=0
        )
    
    def _semantic_search(self, request: str) -> Optional[Dict]:
        """Simulate semantic similarity search"""
        request_lower = request.lower()
        
        best_match = None
        best_score = 0
        
        for key, value in self.vector_store.items():
            # Simple word overlap similarity
            request_words = set(request_lower.split())
            key_words = set(key.lower().split())
            
            if request_words and key_words:
                intersection = request_words & key_words
                union = request_words | key_words
                similarity = len(intersection) / len(union)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = value
        
        if best_score > 0.3:  # Threshold
            return {
                'data': best_match,
                'confidence': min(best_score * 1.5, 1.0)
            }
        
        return None
    
    def _database_lookup(self, request: str) -> Optional[Any]:
        """Simulate database lookup"""
        return self.database.get(request)
    
    def cache_result(self, request: str, data: Any):
        """Cache a result for future lookups"""
        self.cache[request] = data
        self.vector_store[request] = data
    
    def add_to_knowledge_base(self, request: str, answer: Any):
        """Add known Q&A to knowledge base"""
        self.vector_store[request] = answer


class ReasoningHandler:
    """
    Handles expensive reasoning operations.
    Only used when absolutely necessary.
    """
    
    def process(self, request: str) -> ReasoningResult:
        """
        Simulate expensive LLM reasoning.
        In real implementation, this would call OpenAI, Anthropic, etc.
        """
        # Simulate processing time
        time.sleep(0.01)  # 10ms simulated processing
        
        # Generate result
        result = f"[Reasoning Result] Computed answer for: {request}"
        
        return ReasoningResult(
            data=result,
            latency_ms=2000,  # Typical LLM latency
            cost=0.01  # Typical LLM cost per request
        )


class GuardrailRouter:
    """
    Main Guardrail Router that prevents the Inference Trap.
    
    Routes requests between lookup and reasoning based on:
    1. Request classification
    2. Lookup availability
    3. Constraint enforcement
    
    Target: 80-90% lookup, 10-20% reasoning
    """
    
    def __init__(self, max_reasoning_ratio: float = 0.2):
        self.classifier = RequestClassifier()
        self.constraints = ConstraintEnforcer(max_reasoning_ratio)
        self.lookup_handler = LookupHandler()
        self.reasoning_handler = ReasoningHandler()
        
        # Metrics
        self.metrics = {
            'total_requests': 0,
            'lookup_requests': 0,
            'reasoning_requests': 0,
            'constraint_blocks': 0,
            'lookup_hits': 0,
            'lookup_misses': 0,
            'total_latency_ms': 0,
            'total_cost': 0,
            'lookup_latency_ms': 0,
            'reasoning_latency_ms': 0,
        }
    
    def route(self, request: str) -> Dict[str, Any]:
        """
        Main routing logic.
        
        Process:
        1. Try lookup first (always)
        2. Classify request if lookup fails
        3. Check constraints
        4. Route to reasoning if necessary and allowed
        5. Cache reasoning results
        """
        self.metrics['total_requests'] += 1
        start_time = time.time()
        
        # Step 1: Always try lookup first
        lookup_result = self.lookup_handler.try_lookup(request)
        
        if lookup_result.found:
            # Success - found in lookup
            self.constraints.record_lookup()
            self.metrics['lookup_requests'] += 1
            self.metrics['lookup_hits'] += 1
            self.metrics['lookup_latency_ms'] += lookup_result.latency_ms
            self._record_cost(lookup_result.cost)
            
            elapsed_ms = (time.time() - start_time) * 1000
            self.metrics['total_latency_ms'] += elapsed_ms
            
            return {
                'data': lookup_result.data,
                'source': lookup_result.source,
                'latency_ms': lookup_result.latency_ms,
                'cost': lookup_result.cost,
                'reasoning_used': False
            }
        
        # Step 2: Lookup failed - classify request
        self.metrics['lookup_misses'] += 1
        request_type = self.classifier.classify(request)
        
        if request_type == 'lookup':
            # Expected to be in knowledge base but wasn't found
            self.constraints.record_lookup()
            self.metrics['lookup_requests'] += 1
            
            elapsed_ms = (time.time() - start_time) * 1000
            self.metrics['total_latency_ms'] += elapsed_ms
            
            return {
                'data': None,
                'error': 'Information not available in knowledge base',
                'source': 'none',
                'latency_ms': elapsed_ms,
                'cost': 0,
                'reasoning_used': False,
                'suggestion': 'This appears to be a factual query. Consider adding to knowledge base.'
            }
        
        # Step 3: Request requires reasoning - check constraints
        if not self.constraints.can_use_reasoning():
            # Over reasoning budget - block
            self.metrics['constraint_blocks'] += 1
            self.constraints.record_lookup()
            self.metrics['lookup_requests'] += 1
            
            elapsed_ms = (time.time() - start_time) * 1000
            self.metrics['total_latency_ms'] += elapsed_ms
            
            return {
                'data': None,
                'error': 'Reasoning quota exceeded',
                'source': 'blocked',
                'latency_ms': elapsed_ms,
                'cost': 0,
                'reasoning_used': False,
                'current_ratio': self.constraints.get_ratio(),
                'max_ratio': self.constraints.max_reasoning_ratio,
                'suggestion': 'System is over reasoning budget. Improve knowledge base coverage.'
            }
        
        # Step 4: Use reasoning (allowed and necessary)
        reasoning_result = self.reasoning_handler.process(request)
        
        self.constraints.record_reasoning()
        self.metrics['reasoning_requests'] += 1
        self.metrics['reasoning_latency_ms'] += reasoning_result.latency_ms
        self._record_cost(reasoning_result.cost)
        
        elapsed_ms = (time.time() - start_time) * 1000
        self.metrics['total_latency_ms'] += elapsed_ms
        
        # Step 5: Cache result for future lookups
        self.lookup_handler.cache_result(request, reasoning_result.data)
        
        return {
            'data': reasoning_result.data,
            'source': 'reasoning',
            'latency_ms': reasoning_result.latency_ms,
            'cost': reasoning_result.cost,
            'reasoning_used': True,
            'note': 'Result cached for future lookups'
        }
    
    def _record_cost(self, cost: float):
        """Record cost metric"""
        self.metrics['total_cost'] += cost
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive router metrics.
        """
        total = self.metrics['total_requests']
        if total == 0:
            return {'status': 'No requests processed yet'}
        
        lookup_ratio = self.metrics['lookup_requests'] / total
        reasoning_ratio = self.metrics['reasoning_requests'] / total
        
        # Calculate averages
        avg_latency = self.metrics['total_latency_ms'] / total
        avg_cost = self.metrics['total_cost'] / total
        
        # Calculate lookup stats
        lookup_count = self.metrics['lookup_requests']
        avg_lookup_latency = (
            self.metrics['lookup_latency_ms'] / lookup_count 
            if lookup_count > 0 else 0
        )
        
        # Calculate reasoning stats
        reasoning_count = self.metrics['reasoning_requests']
        avg_reasoning_latency = (
            self.metrics['reasoning_latency_ms'] / reasoning_count 
            if reasoning_count > 0 else 0
        )
        
        # Calculate cache hit rate
        total_lookups = self.metrics['lookup_hits'] + self.metrics['lookup_misses']
        cache_hit_rate = (
            self.metrics['lookup_hits'] / total_lookups 
            if total_lookups > 0 else 0
        )
        
        # Calculate savings vs all-reasoning approach
        all_reasoning_cost = total * 0.01
        cost_savings = ((all_reasoning_cost - self.metrics['total_cost']) / all_reasoning_cost) * 100
        
        all_reasoning_time = total * 2000
        time_savings = ((all_reasoning_time - self.metrics['total_latency_ms']) / all_reasoning_time) * 100
        
        return {
            'total_requests': total,
            'lookup_count': self.metrics['lookup_requests'],
            'reasoning_count': self.metrics['reasoning_requests'],
            'lookup_ratio': lookup_ratio,
            'reasoning_ratio': reasoning_ratio,
            'target_met': reasoning_ratio <= self.constraints.max_reasoning_ratio,
            'constraint_blocks': self.metrics['constraint_blocks'],
            'cache_hit_rate': cache_hit_rate,
            'avg_latency_ms': avg_latency,
            'avg_lookup_latency_ms': avg_lookup_latency,
            'avg_reasoning_latency_ms': avg_reasoning_latency,
            'avg_cost': avg_cost,
            'total_cost': self.metrics['total_cost'],
            'cost_savings_pct': cost_savings,
            'time_savings_pct': time_savings,
            'breakdown': {
                'lookup_hits': self.metrics['lookup_hits'],
                'lookup_misses': self.metrics['lookup_misses'],
                'reasoning_used': self.metrics['reasoning_requests'],
                'constraint_blocks': self.metrics['constraint_blocks']
            }
        }
    
    def pre_populate_knowledge_base(self, qa_pairs: List[tuple]):
        """
        Pre-populate knowledge base with common Q&A pairs.
        This is critical for achieving high lookup ratio.
        """
        for question, answer in qa_pairs:
            self.lookup_handler.add_to_knowledge_base(question, answer)


def main():
    print("=" * 70)
    print("Guardrail Router Example: Preventing the Inference Trap")
    print("=" * 70)
    print("SIMULATION. No model is called. Every latency and cost printed below")
    print("is a constant written into this file so the control flow is readable.")
    print("None of it is a measurement. See CONTRIBUTING.md for the standard.")
    print()
    
    # Create router with 20% max reasoning ratio
    router = GuardrailRouter(max_reasoning_ratio=0.2)
    
    # Step 1: Pre-populate knowledge base
    print("\n1. Pre-populating Knowledge Base...")
    print("-" * 70)
    
    knowledge_base = [
        ("What is the capital of France?", "Paris"),
        ("What is 2 + 2?", "4"),
        ("How do I reset my password?", "Click 'Forgot Password' on the login page"),
        ("What are your business hours?", "Monday-Friday, 9 AM - 5 PM EST"),
        ("How do I contact support?", "Email: support@example.com or call 1-800-123-4567"),
        ("What is your return policy?", "30-day return policy for unused items"),
        ("Where is your headquarters?", "San Francisco, CA"),
        ("What is Python?", "Python is a high-level programming language"),
        ("Who is the CEO?", "Jane Smith"),
        ("When was the company founded?", "2020"),
    ]
    
    router.pre_populate_knowledge_base(knowledge_base)
    print(f"   Loaded {len(knowledge_base)} Q&A pairs into knowledge base")
    
    # Step 2: Process various types of requests
    print("\n2. Processing Requests...")
    print("-" * 70)
    
    test_requests = [
        # Lookup requests (should hit cache)
        "What is the capital of France?",
        "How do I reset my password?",
        "What are your business hours?",
        
        # Similar requests (should hit semantic search)
        "What is the capital city of France?",
        "How can I reset my password?",
        "What are the business hours?",
        
        # Simple factual (should be lookup but will miss)
        "What is the capital of Spain?",
        
        # Reasoning requests (novel problems)
        "Design a system that combines authentication and authorization",
        "Analyze the trade-offs between SQL and NoSQL databases",
        
        # More lookup requests
        "What is 2 + 2?",
        "Where is your headquarters?",
        
        # Reasoning request
        "Create a plan for migrating from monolith to microservices",
        
        # More lookups
        "What is Python?",
        "Who is the CEO?",
    ]
    
    for i, request in enumerate(test_requests, 1):
        result = router.route(request)
        
        print(f"\n   Request {i}: {request[:55]}")
        print(f"      Source: {result['source']}")
        print(f"      Reasoning: {'Yes' if result.get('reasoning_used') else 'No'}")
        print(f"      Latency: {result['latency_ms']:.1f}ms")
        print(f"      Cost: ${result['cost']:.4f}")
        
        if 'error' in result:
            print(f"      Error: {result['error']}")
    
    # Step 3: Show comprehensive metrics
    print("\n3. Router Metrics & Analysis")
    print("=" * 70)
    
    metrics = router.get_metrics()
    
    print("\n   Volume Metrics:")
    print(f"      Total Requests: {metrics['total_requests']}")
    print(f"      Lookup Requests: {metrics['lookup_count']} ({metrics['lookup_ratio']:.1%})")
    print(f"      Reasoning Requests: {metrics['reasoning_count']} ({metrics['reasoning_ratio']:.1%})")
    print(f"      Constraint Blocks: {metrics['constraint_blocks']}")
    
    print("\n   Ratio Analysis:")
    print(f"      Current Reasoning Ratio: {metrics['reasoning_ratio']:.1%}")
    print("      Target Reasoning Ratio: ≤20%")
    print(f"      Status: {'✓ TARGET MET' if metrics['target_met'] else '✗ OVER TARGET'}")
    
    print("\n   Performance Metrics:")
    print(f"      Avg Overall Latency: {metrics['avg_latency_ms']:.1f}ms")
    print(f"      Avg Lookup Latency: {metrics['avg_lookup_latency_ms']:.1f}ms")
    print(f"      Avg Reasoning Latency: {metrics['avg_reasoning_latency_ms']:.1f}ms")
    print(f"      Cache Hit Rate: {metrics['cache_hit_rate']:.1%}")
    
    print("\n   Cost Metrics:")
    print(f"      Total Cost: ${metrics['total_cost']:.4f}")
    print(f"      Avg Cost per Request: ${metrics['avg_cost']:.4f}")
    print(f"      Cost Savings vs All-Reasoning: {metrics['cost_savings_pct']:.1f}%")
    print(f"      Time Savings vs All-Reasoning: {metrics['time_savings_pct']:.1f}%")
    
    print("\n   Request Breakdown:")
    for key, value in metrics['breakdown'].items():
        pct = (value / metrics['total_requests']) * 100
        print(f"      {key.replace('_', ' ').title()}: {value} ({pct:.1f}%)")
    
    # Step 4: Key insights
    print("\n4. Key Insights")
    print("=" * 70)
    
    if metrics['target_met']:
        print("   ✓ Router successfully maintains target ratio")
        print("   ✓ System prevents the Inference Trap")
        print("   ✓ Requests routed efficiently between lookup and reasoning")
    else:
        print("   ✗ System exceeds reasoning budget")
        print("   → Recommendation: Expand knowledge base coverage")
        print("   → Recommendation: Review request classification rules")
    
    print("")
    print("   Simulated cost, on the constants at the top of this file:")
    print(f"      If every request had used reasoning: ${metrics['total_requests'] * 0.01:.2f}")
    print(f"      With the router:                     ${metrics['total_cost']:.2f}")
    print("")
    print("   Simulated latency, against an assumed 2000ms reasoning call:")
    print(f"      Avg response time: {metrics['avg_latency_ms']:.0f}ms")
    print("")
    print("   Both figures follow arithmetically from the constants. They tell you")
    print("   the router routed; they tell you nothing about your workload. The")
    print("   number that transfers is the ratio, and you have to measure yours.")
    
    print("\n5. Conclusion")
    print("=" * 70)
    print("   The Guardrail Router prevents the Inference Trap by:")
    print("   • Routing requests intelligently between lookup and reasoning")
    print("   • Enforcing hard constraints on reasoning usage")
    print("   • Caching reasoning results for future lookups")
    print("   • Maintaining 80-90% lookup ratio for optimal performance")
    print()
    print("   Result: request cost becomes a function of request class,")
    print("   and that classification is visible and testable.")
    print("=" * 70)


if __name__ == "__main__":
    main()
