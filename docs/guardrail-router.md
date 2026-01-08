# The Guardrail Router: Deciding Between Lookup and Reasoning

## Overview

The **Guardrail Router** is a critical architectural component that sits between user requests and your AI system, making intelligent decisions about whether a task requires expensive reasoning or can be solved with fast, reliable lookup operations.

This pattern is the practical solution to **The Inference Trap**—preventing engineers from using expensive reasoning models for simple retrieval tasks.

## The Problem

Modern AI systems often fall into one of two extremes:

1. **Always Reason**: Every request goes through expensive LLM reasoning
   - Result: Slow, expensive, unreliable
   
2. **Never Reason**: Only use cached/indexed data
   - Result: Can't handle novel queries

**What's missing**: A smart decision layer that routes requests appropriately.

## What is a Guardrail Router?

A Guardrail Router is a **decision module** that:

1. **Analyzes** incoming requests
2. **Classifies** them by type (lookup vs. reasoning)
3. **Routes** them to the appropriate handler
4. **Tracks** the lookup-to-reasoning ratio
5. **Enforces** constraints to prevent misuse

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       User Request                            │
│              "What is the capital of France?"                 │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
              ┌────────────────────────┐
              │   Guardrail Router     │
              │                        │
              │  1. Classify request   │  ◄── Fast classification
              │  2. Check constraints  │      (10-50ms)
              │  3. Route decision     │
              └────────┬───────────────┘
                       │
          ┌────────────┴─────────────┐
          │                          │
          ▼                          ▼
   ┌─────────────┐          ┌──────────────┐
   │   LOOKUP    │          │  REASONING   │
   │   PATH      │          │    PATH      │
   │             │          │              │
   │ • Cache     │          │ • Synthesis  │
   │ • Database  │          │ • Novel      │
   │ • Vector DB │          │   problems   │
   │ • Knowledge │          │ • Adaptation │
   │   Graph     │          │              │
   │             │          │ ↓            │
   │ 80-90%      │          │ Cache result │
   │ of traffic  │          │ for future   │
   └─────────────┘          └──────────────┘
        │                         │
        │                   10-20%
        │                   of traffic
        └────────┬────────────────┘
                 │
                 ▼
          ┌─────────────┐
          │  Response   │
          └─────────────┘
```

## Core Components

### 1. Request Classifier

Quickly categorizes requests without expensive processing:

```python
class RequestClassifier:
    """
    Fast classification of request types.
    Target: < 50ms classification time
    """
    
    REQUEST_CATEGORIES = {
        # Lookup categories (80-90%)
        'FACTUAL_QUERY': {
            'pattern': ['what is', 'who is', 'when did', 'where is'],
            'route': 'lookup',
            'examples': ['What is the capital of France?']
        },
        'DOCUMENTATION_QUERY': {
            'pattern': ['how do i', 'how to', 'tutorial', 'guide'],
            'route': 'lookup',
            'examples': ['How do I call the API?']
        },
        'HISTORICAL_QUERY': {
            'pattern': ['history of', 'past', 'previously', 'when did'],
            'route': 'lookup',
            'examples': ['When did Apollo 11 land?']
        },
        'STATUS_QUERY': {
            'pattern': ['status', 'current', 'latest', 'now'],
            'route': 'lookup',
            'examples': ['What is the current version?']
        },
        
        # Reasoning categories (10-20%)
        'SYNTHESIS': {
            'pattern': ['combine', 'merge', 'integrate', 'synthesize'],
            'route': 'reasoning',
            'examples': ['Combine these approaches into one solution']
        },
        'NOVEL_PROBLEM': {
            'pattern': ['design', 'create', 'build', 'architect'],
            'route': 'reasoning',
            'examples': ['Design a system that handles...']
        },
        'ADAPTATION': {
            'pattern': ['modify', 'adapt', 'change', 'customize'],
            'route': 'reasoning',
            'examples': ['Adapt this code for Python']
        },
        'ANALYSIS': {
            'pattern': ['analyze', 'compare', 'evaluate', 'assess'],
            'route': 'reasoning',
            'examples': ['Compare these two approaches']
        }
    }
    
    def classify(self, request: str) -> str:
        """
        Classify request type using pattern matching.
        Fast operation: ~1-10ms
        """
        request_lower = request.lower()
        
        # Check each category
        for category, config in self.REQUEST_CATEGORIES.items():
            for pattern in config['pattern']:
                if pattern in request_lower:
                    return category
        
        # Default: assume lookup (safer, cheaper)
        return 'FACTUAL_QUERY'
    
    def should_use_reasoning(self, request: str) -> bool:
        """
        Decide if request requires reasoning.
        """
        category = self.classify(request)
        config = self.REQUEST_CATEGORIES[category]
        return config['route'] == 'reasoning'
```

### 2. Constraint Enforcer

Ensures the system stays within acceptable bounds:

```python
class ConstraintEnforcer:
    """
    Enforces hard limits on reasoning usage.
    """
    
    def __init__(self, max_reasoning_ratio=0.2):
        self.max_reasoning_ratio = max_reasoning_ratio
        self.reasoning_count = 0
        self.total_count = 0
    
    def can_use_reasoning(self) -> bool:
        """
        Check if we're within reasoning budget.
        """
        if self.total_count == 0:
            return True
        
        current_ratio = self.reasoning_count / self.total_count
        return current_ratio < self.max_reasoning_ratio
    
    def record_lookup(self):
        self.total_count += 1
    
    def record_reasoning(self):
        self.total_count += 1
        self.reasoning_count += 1
    
    def get_ratio(self):
        if self.total_count == 0:
            return 0
        return self.reasoning_count / self.total_count
```

### 3. Router Core

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

## Implementation Strategies

### Strategy 1: Pattern-Based Classification

Fast, simple, and effective for most cases:

```python
# Uses keyword patterns to classify
# Pros: Fast (<10ms), simple, interpretable
# Cons: Less flexible, may miss nuanced queries

classifier = PatternBasedClassifier()
if classifier.matches_lookup_pattern(request):
    return lookup(request)
else:
    return reason(request)
```

### Strategy 2: Small ML Model Classification

More accurate but slightly slower:

```python
# Uses small BERT model or similar
# Pros: More accurate, handles variations
# Cons: Slower (50-100ms), needs training

classifier = SmallMLClassifier()
category = classifier.classify(request)  # 50ms
if category in LOOKUP_CATEGORIES:
    return lookup(request)
else:
    return reason(request)
```

### Strategy 3: Hybrid Approach

Best of both worlds:

```python
# Use patterns first, ML as fallback
# Pros: Fast for common cases, accurate for edge cases
# Cons: More complex implementation

def classify(request):
    # Fast pattern match (1ms)
    pattern_result = pattern_classifier.classify(request)
    if pattern_result.confidence > 0.9:
        return pattern_result
    
    # ML classifier for uncertain cases (50ms)
    return ml_classifier.classify(request)
```

## Real-World Example

### E-commerce Support System

```python
class EcommerceSupportRouter(GuardrailRouter):
    """
    Guardrail router for e-commerce customer support.
    
    Lookup tasks (90%):
    - Order status
    - Tracking info
    - Return policy
    - Product specs
    - FAQs
    
    Reasoning tasks (10%):
    - Complex complaints
    - Unusual situations
    - Policy exceptions
    """
    
    def __init__(self):
        lookup = EcommerceLookupHandler()
        reasoning = CustomerServiceLLM()
        super().__init__(lookup, reasoning, max_reasoning_ratio=0.1)
        
        # Custom classification for e-commerce
        self.ecommerce_patterns = {
            'order_status': ['order', 'status', 'where is my'],
            'tracking': ['track', 'shipping', 'delivery'],
            'return': ['return', 'refund', 'exchange'],
            'product': ['product', 'item', 'specification'],
            'faq': ['how to', 'can i', 'do you']
        }
    
    def classify_ecommerce(self, request):
        """Domain-specific classification"""
        request_lower = request.lower()
        
        for category, patterns in self.ecommerce_patterns.items():
            if any(p in request_lower for p in patterns):
                return 'lookup'  # All e-commerce patterns are lookup
        
        return 'reasoning'  # Unknown = might need reasoning
    
    def route(self, request):
        """Override to add e-commerce specific logic"""
        
        # Try exact order number match
        if order_id := self.extract_order_id(request):
            return self.lookup_handler.get_order(order_id)
        
        # Use parent routing logic
        return super().route(request)
```

## Metrics and Monitoring

### Key Metrics to Track

```python
class RouterMetrics:
    """
    Comprehensive metrics for router performance.
    """
    
    def __init__(self):
        self.metrics = {
            # Volume metrics
            'total_requests': 0,
            'lookup_requests': 0,
            'reasoning_requests': 0,
            
            # Ratio metrics
            'current_ratio': 0.0,
            'target_ratio': 0.1,  # 10% reasoning
            
            # Performance metrics
            'avg_lookup_latency_ms': 0,
            'avg_reasoning_latency_ms': 0,
            'p95_latency_ms': 0,
            'p99_latency_ms': 0,
            
            # Cost metrics
            'total_cost': 0,
            'cost_per_request': 0,
            'lookup_cost': 0,
            'reasoning_cost': 0,
            
            # Quality metrics
            'constraint_blocks': 0,
            'lookup_misses': 0,
            'cache_hit_rate': 0,
            
            # Efficiency metrics
            'cost_savings': 0,  # vs. all-reasoning approach
            'latency_improvement': 0  # vs. all-reasoning approach
        }
    
    def calculate_savings(self):
        """
        Calculate savings vs. all-reasoning approach.
        """
        # If all requests used reasoning
        all_reasoning_cost = self.metrics['total_requests'] * 0.01  # $0.01 per reasoning
        all_reasoning_time = self.metrics['total_requests'] * 2000  # 2000ms per reasoning
        
        actual_cost = self.metrics['total_cost']
        actual_time = (
            self.metrics['lookup_requests'] * 100 +  # 100ms per lookup
            self.metrics['reasoning_requests'] * 2000  # 2000ms per reasoning
        )
        
        return {
            'cost_savings_pct': ((all_reasoning_cost - actual_cost) / all_reasoning_cost) * 100,
            'latency_improvement_pct': ((all_reasoning_time - actual_time) / all_reasoning_time) * 100,
            'cost_savings_dollars': all_reasoning_cost - actual_cost
        }
```

### Dashboard View

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

## Best Practices

### 1. Start with Strict Constraints

```python
# Begin with very low reasoning ratio
router = GuardrailRouter(
    lookup_handler=my_lookup,
    reasoning_handler=my_reasoning,
    max_reasoning_ratio=0.05  # Only 5% reasoning
)

# Gradually increase as needed
```

### 2. Comprehensive Knowledge Base

```python
# Pre-populate knowledge base with common queries
common_queries = [
    "What is the capital of France?",
    "How do I reset my password?",
    "What are your business hours?",
    # ... 1000s more
]

for query in common_queries:
    knowledge_base.add(query, answer)
```

### 3. Continuous Learning

```python
# Learn from reasoning results
def route(request):
    result = router.route(request)
    
    # If reasoning was used, cache for future
    if result.source == 'reasoning':
        knowledge_base.add(request, result.data)
        # Future same request = lookup
    
    return result
```

### 4. Monitor and Alert

```python
# Alert when ratio exceeds threshold
def check_health():
    metrics = router.get_metrics()
    
    if metrics['reasoning_ratio'] > 0.2:
        alert("Reasoning ratio too high: {:.1%}".format(
            metrics['reasoning_ratio']
        ))
    
    if metrics['lookup_miss_rate'] > 0.1:
        alert("Too many lookup misses - improve knowledge base")
```

## Anti-Patterns to Avoid

### ❌ No Router (Direct to LLM)

```python
# Bad: Every request goes to LLM
def handle(request):
    return llm.generate(request)  # Expensive, slow
```

### ❌ Router Without Constraints

```python
# Bad: Router decides but no limits
def route(request):
    if complex(request):
        return reason(request)  # No budget limit
```

### ❌ Ignoring Metrics

```python
# Bad: Not tracking what's happening
def route(request):
    # ... routing logic ...
    # No metrics tracking
    return result
```

## Implementation Checklist

- [ ] Define request categories for your domain
- [ ] Implement request classifier (start with pattern-based)
- [ ] Set up constraint enforcer with reasonable limits (10-20% reasoning)
- [ ] Build comprehensive lookup handlers
- [ ] Implement reasoning fallback
- [ ] Add metrics tracking
- [ ] Set up monitoring dashboard
- [ ] Define alerts for ratio violations
- [ ] Create knowledge base population strategy
- [ ] Plan continuous learning from reasoning results
- [ ] Test with production-like traffic
- [ ] Optimize based on metrics

## Conclusion

The Guardrail Router is the missing piece in modern AI architectures. It prevents The Inference Trap by:

1. **Intelligently routing** requests between lookup and reasoning
2. **Enforcing constraints** to maintain healthy ratios
3. **Tracking metrics** to enable optimization
4. **Caching results** to convert reasoning to lookup over time

**Result**: Systems that are 10x faster, 90% cheaper, and significantly more reliable.

**Remember**: If your agent is "thinking" for every request, you haven't built an agent—you've built a philosophy major. The Guardrail Router ensures you build an engineer instead.

## Further Reading

- [The Inference Trap](./inference-trap.md) - Understanding the problem
- [Compute-to-Lookup Ratio](./compute-to-lookup-ratio.md) - The 90/10 rule
- [Semantic Firewall](./semantic-firewall.md) - Validation and hallucination prevention
- [Headless Agent](./headless-agent.md) - Efficient agent coordination
