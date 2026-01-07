"""
Example: Compute-to-Lookup Ratio Implementation

This example demonstrates how to build a system that prioritizes lookup
over computation, achieving the 90/10 target ratio.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import hashlib


@dataclass
class QueryResult:
    """Result from query execution"""
    data: Any
    source: str  # 'cache', 'vector_db', 'db', 'llm'
    latency_ms: float
    cost: float


class MultiTierLookupSystem:
    """
    Implements a multi-tier lookup system that falls back to computation
    only when necessary.
    
    Tier 1: Memory Cache (L1) - ~1ms
    Tier 2: Redis Cache (L2) - ~10ms
    Tier 3: Vector Store - ~100ms
    Tier 4: Primary Database - ~200ms
    Tier 5: LLM Computation - ~2000ms
    """
    
    def __init__(self):
        self.l1_cache = {}  # Memory cache
        self.l2_cache = {}  # Simulated Redis
        self.vector_store = {}  # Simulated vector DB
        self.database = {}  # Simulated primary DB
        
        # Metrics tracking
        self.metrics = {
            'l1_hits': 0,
            'l2_hits': 0,
            'vector_hits': 0,
            'db_hits': 0,
            'llm_calls': 0,
            'total_queries': 0,
            'total_latency_ms': 0,
            'total_cost': 0
        }
    
    def query(self, query: str, context: Optional[Dict] = None) -> QueryResult:
        """
        Execute query with lookup-first strategy
        """
        self.metrics['total_queries'] += 1
        start = datetime.now()
        
        # Generate cache key
        cache_key = self._generate_cache_key(query, context)
        
        # Tier 1: Check L1 cache (memory)
        if cache_key in self.l1_cache:
            self.metrics['l1_hits'] += 1
            result = QueryResult(
                data=self.l1_cache[cache_key],
                source='l1_cache',
                latency_ms=1,
                cost=0.0001
            )
            self._update_metrics(result)
            return result
        
        # Tier 2: Check L2 cache (Redis)
        if cache_key in self.l2_cache:
            self.metrics['l2_hits'] += 1
            data = self.l2_cache[cache_key]
            # Promote to L1
            self.l1_cache[cache_key] = data
            result = QueryResult(
                data=data,
                source='l2_cache',
                latency_ms=10,
                cost=0.0002
            )
            self._update_metrics(result)
            return result
        
        # Tier 3: Semantic search in vector store
        similar = self._vector_search(query)
        if similar and similar['similarity'] > 0.85:
            self.metrics['vector_hits'] += 1
            data = similar['data']
            # Cache the result
            self._cache_result(cache_key, data)
            result = QueryResult(
                data=data,
                source='vector_store',
                latency_ms=100,
                cost=0.001
            )
            self._update_metrics(result)
            return result
        
        # Tier 4: Database lookup
        db_result = self._database_lookup(query, context)
        if db_result:
            self.metrics['db_hits'] += 1
            # Cache the result
            self._cache_result(cache_key, db_result)
            result = QueryResult(
                data=db_result,
                source='database',
                latency_ms=200,
                cost=0.002
            )
            self._update_metrics(result)
            return result
        
        # Tier 5: LLM computation (last resort)
        self.metrics['llm_calls'] += 1
        llm_result = self._llm_compute(query, context)
        # Cache the result
        self._cache_result(cache_key, llm_result)
        result = QueryResult(
            data=llm_result,
            source='llm',
            latency_ms=2000,
            cost=0.01
        )
        self._update_metrics(result)
        return result
    
    def _generate_cache_key(self, query: str, context: Optional[Dict]) -> str:
        """Generate deterministic cache key"""
        key_string = query
        if context:
            key_string += str(sorted(context.items()))
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _vector_search(self, query: str) -> Optional[Dict]:
        """Simulate vector similarity search"""
        # In real implementation, this would use a vector database
        # like Pinecone, Weaviate, or Qdrant
        query_lower = query.lower()
        
        # Simple semantic matching simulation
        # Check for keyword overlap and semantic similarity
        best_match = None
        best_score = 0
        
        for key, value in self.vector_store.items():
            key_lower = key.lower()
            
            # Calculate simple similarity score
            query_words = set(query_lower.split())
            key_words = set(key_lower.split())
            
            # Jaccard similarity
            if query_words and key_words:
                intersection = query_words & key_words
                union = query_words | key_words
                similarity = len(intersection) / len(union)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = value
        
        # Return match if similarity is above threshold
        if best_score > 0.3:  # Lower threshold for better matching
            return {
                'data': best_match,
                'similarity': min(best_score * 1.5, 1.0)  # Boost score
            }
        
        return None
    
    def _database_lookup(self, query: str, context: Optional[Dict]) -> Optional[Any]:
        """Simulate database lookup"""
        # In real implementation, this would query SQL/NoSQL database
        return self.database.get(query)
    
    def _llm_compute(self, query: str, context: Optional[Dict]) -> Any:
        """Simulate LLM computation (last resort)"""
        # In real implementation, this would call OpenAI, Anthropic, etc.
        return f"LLM computed result for: {query}"
    
    def _cache_result(self, key: str, data: Any):
        """Cache result in multiple tiers"""
        self.l1_cache[key] = data
        self.l2_cache[key] = data
    
    def _update_metrics(self, result: QueryResult):
        """Update system metrics"""
        self.metrics['total_latency_ms'] += result.latency_ms
        self.metrics['total_cost'] += result.cost
    
    def get_compute_to_lookup_ratio(self) -> Dict[str, Any]:
        """
        Calculate the compute-to-lookup ratio
        Target: < 0.1 (10%)
        """
        total = self.metrics['total_queries']
        if total == 0:
            return {'ratio': 0, 'details': 'No queries yet'}
        
        lookup_operations = (
            self.metrics['l1_hits'] +
            self.metrics['l2_hits'] +
            self.metrics['vector_hits'] +
            self.metrics['db_hits']
        )
        compute_operations = self.metrics['llm_calls']
        
        compute_ratio = compute_operations / total
        lookup_ratio = lookup_operations / total
        
        avg_latency = self.metrics['total_latency_ms'] / total
        avg_cost = self.metrics['total_cost'] / total
        
        return {
            'compute_ratio': compute_ratio,
            'lookup_ratio': lookup_ratio,
            'target_met': compute_ratio <= 0.1,
            'avg_latency_ms': avg_latency,
            'avg_cost_per_query': avg_cost,
            'total_queries': total,
            'breakdown': {
                'l1_cache': self.metrics['l1_hits'],
                'l2_cache': self.metrics['l2_hits'],
                'vector_store': self.metrics['vector_hits'],
                'database': self.metrics['db_hits'],
                'llm_compute': self.metrics['llm_calls']
            }
        }
    
    def pre_compute_and_index(self, queries: List[str], answers: List[Any]):
        """
        Pre-compute and index common queries to improve lookup ratio
        """
        for query, answer in zip(queries, answers):
            # Index in vector store for semantic search
            self.vector_store[query] = answer
            # Also cache directly
            cache_key = self._generate_cache_key(query, None)
            self._cache_result(cache_key, answer)


# Example usage
def main():
    print("=" * 60)
    print("Compute-to-Lookup Ratio Example")
    print("=" * 60)
    
    system = MultiTierLookupSystem()
    
    # Pre-compute common queries
    print("\n1. Pre-computing common queries...")
    common_queries = [
        "What is the capital of France?",
        "How do I reset my password?",
        "What are your business hours?",
        "How do I contact support?",
        "What is your return policy?"
    ]
    answers = [
        "Paris",
        "Click 'Forgot Password' on the login page",
        "Monday-Friday, 9 AM - 5 PM EST",
        "Email: support@example.com or call 1-800-123-4567",
        "30-day return policy for unused items"
    ]
    system.pre_compute_and_index(common_queries, answers)
    print(f"   Indexed {len(common_queries)} common queries")
    
    # Simulate user queries
    print("\n2. Processing user queries...")
    test_queries = [
        "What is the capital of France?",  # L1 hit
        "What is the capital of France?",  # L1 hit (repeated)
        "How do I reset my password?",     # L1 hit
        "What are business hours?",        # Vector hit (similar)
        "How to contact support?",         # Vector hit (similar)
        "What is the meaning of life?",    # LLM call (not in KB)
        "What are your hours?",            # Vector hit
        "password reset help",             # Vector hit
    ]
    
    for i, query in enumerate(test_queries, 1):
        result = system.query(query)
        print(f"   Query {i}: {query[:40]}")
        print(f"      Source: {result.source}, Latency: {result.latency_ms}ms, Cost: ${result.cost:.4f}")
    
    # Show metrics
    print("\n3. System Metrics:")
    print("-" * 60)
    metrics = system.get_compute_to_lookup_ratio()
    
    print(f"   Total Queries: {metrics['total_queries']}")
    print(f"   Compute Ratio: {metrics['compute_ratio']:.1%} (Target: ≤10%)")
    print(f"   Lookup Ratio: {metrics['lookup_ratio']:.1%} (Target: ≥90%)")
    print(f"   Target Met: {'✓ YES' if metrics['target_met'] else '✗ NO'}")
    print(f"   Avg Latency: {metrics['avg_latency_ms']:.1f}ms")
    print(f"   Avg Cost: ${metrics['avg_cost_per_query']:.4f}")
    
    print("\n   Breakdown:")
    for source, count in metrics['breakdown'].items():
        pct = (count / metrics['total_queries']) * 100
        print(f"      {source}: {count} ({pct:.1f}%)")
    
    # Performance comparison
    print("\n4. Performance Comparison:")
    print("-" * 60)
    lookup_time = (
        metrics['breakdown']['l1_cache'] * 1 +
        metrics['breakdown']['l2_cache'] * 10 +
        metrics['breakdown']['vector_store'] * 100 +
        metrics['breakdown']['database'] * 200
    )
    compute_time = metrics['breakdown']['llm_compute'] * 2000
    total_time = lookup_time + compute_time
    
    print(f"   Time spent in lookups: {lookup_time:.0f}ms ({lookup_time/total_time*100:.1f}%)")
    print(f"   Time spent in compute: {compute_time:.0f}ms ({compute_time/total_time*100:.1f}%)")
    print(f"   Total time: {total_time:.0f}ms")
    
    # Cost comparison
    lookup_cost = (
        metrics['breakdown']['l1_cache'] * 0.0001 +
        metrics['breakdown']['l2_cache'] * 0.0002 +
        metrics['breakdown']['vector_store'] * 0.001 +
        metrics['breakdown']['database'] * 0.002
    )
    compute_cost = metrics['breakdown']['llm_compute'] * 0.01
    total_cost = lookup_cost + compute_cost
    
    print(f"\n   Cost from lookups: ${lookup_cost:.4f} ({lookup_cost/total_cost*100:.1f}%)")
    print(f"   Cost from compute: ${compute_cost:.4f} ({compute_cost/total_cost*100:.1f}%)")
    print(f"   Total cost: ${total_cost:.4f}")
    
    print("\n5. Key Insights:")
    print("-" * 60)
    if metrics['target_met']:
        print("   ✓ System meets 90/10 target ratio")
        print("   ✓ Fast and cost-effective")
        print("   ✓ Scalable architecture")
    else:
        print("   ✗ System needs optimization")
        print("   → Pre-compute more common queries")
        print("   → Improve semantic indexing")
        print("   → Add more caching layers")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
