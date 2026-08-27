# The Semantic Firewall: Using Multidimensional Knowledge Graphs to Block Hallucinations Before They Happen

> The numbers in this document are worked examples on stated assumptions, or
> design targets. None of them are measurements. See the evidence standard in
> [CONTRIBUTING.md](../CONTRIBUTING.md#evidence-standard).

## Overview

The **Semantic Firewall** is a defense-in-depth architecture pattern that prevents AI hallucinations by validating LLM outputs against structured knowledge representations before they reach end users. Unlike traditional approaches that detect hallucinations after generation, the Semantic Firewall blocks them proactively.

> **Note**: This document focuses on validation and verification patterns. For a comprehensive guide on using multidimensional knowledge graphs for context filtering and "Scale by Subtraction," see [Multidimensional Knowledge Graphs](./multidimensional-knowledge-graphs.md).

## The Hallucination Problem

Large Language Models (LLMs) can generate plausible-sounding but factually incorrect information. Traditional approaches include:

- **Post-generation detection**: Checking outputs after generation (too late)
- **Prompt engineering**: Asking the LLM to "be careful" (unreliable)
- **Fine-tuning**: Training on correct data (expensive, still not guaranteed)

The Semantic Firewall moves the check before the user rather than after, and
makes the check a property of the graph rather than of the model.

Be precise about the scope. It guarantees that **every claim the extractor
turns into a checkable fact is checked against the graph before release**. It
does not guarantee the output is true. Two gaps stay open: a claim the
extractor fails to recognise passes through unchecked, and a wrong fact in the
graph is enforced as confidently as a right one. The firewall inherits the
correctness of your knowledge, it does not create it.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        User Query                             │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Query Understanding  │
              │  & Intent Extraction  │
              └──────────┬───────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │  Multidimensional Knowledge   │
         │         Graph Query           │
         │                               │
         │  ┌─────────────────────────┐ │
         │  │ Entities & Relationships│ │
         │  ├─────────────────────────┤ │
         │  │   Temporal Dimension    │ │
         │  ├─────────────────────────┤ │
         │  │   Confidence Scores     │ │
         │  ├─────────────────────────┤ │
         │  │   Source Attribution    │ │
         │  └─────────────────────────┘ │
         └───────────┬───────────────────┘
                     │
                     ▼
         ┌───────────────────────────────┐
         │    SEMANTIC FIREWALL LAYER    │
         │                               │
         │  Validation Rules:            │
         │  ✓ Entity existence check     │
         │  ✓ Relationship validity      │
         │  ✓ Temporal consistency       │
         │  ✓ Confidence thresholds      │
         │  ✓ Source verification        │
         │  ✓ Contradiction detection    │
         └───────────┬───────────────────┘
                     │
            ┌────────┴────────┐
            │                 │
            ▼                 ▼
    ┌──────────────┐   ┌─────────────┐
    │   BLOCKED    │   │   ALLOWED   │
    │ (Potentially │   │  (Verified  │
    │ Hallucinated)│   │   Facts)    │
    └──────┬───────┘   └──────┬──────┘
           │                  │
           ▼                  ▼
    ┌──────────────┐   ┌─────────────┐
    │ Fallback     │   │ LLM Synthesis│
    │ Response     │   │ w/ Grounded  │
    │              │   │ Context      │
    └──────────────┘   └──────┬──────┘
                              │
                              ▼
                       ┌─────────────┐
                       │   Response  │
                       └─────────────┘
```

## Multidimensional Knowledge Graph

The core of the Semantic Firewall is a knowledge graph with multiple dimensions:

### 1. Entity-Relationship Dimension

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

### 2. Temporal Dimension

Track when facts are valid:

```python
class TemporalFact:
    relationship: Relationship
    valid_from: datetime
    valid_until: Optional[datetime]
    confidence: float
    
# Example:
# (John Smith) -[works_for]-> (Acme Corp)
#   valid_from: 2020-01-01
#   valid_until: 2023-06-30
#   confidence: 0.95
#
# (John Smith) -[works_for]-> (Beta Inc)
#   valid_from: 2023-07-01
#   valid_until: None (current)
#   confidence: 0.98
```

### 3. Confidence & Provenance Dimension

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

### 4. Semantic Context Dimension

Understand relationships in different contexts:

```python
class ContextualRelationship:
    relationship: Relationship
    context: str  # professional, personal, historical
    domain: str  # technology, finance, healthcare
    
# Example:
# (Python) -[related_to]-> (Programming)
#   context: technical, domain: computer_science
#
# (Python) -[related_to]-> (Snake)
#   context: zoology, domain: biology
```

## Firewall Validation Rules

### Rule 1: Entity Existence Check

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

### Rule 2: Relationship Validity Check

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

### Rule 3: Temporal Consistency Check

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

### Rule 4: Confidence Threshold Check

```python
def validate_confidence(fact: VerifiedFact, threshold: float = 0.7) -> bool:
    """
    Only allow facts that meet minimum confidence threshold
    """
    return fact.confidence_score >= threshold

# Low-confidence facts are flagged or blocked
```

### Rule 5: Source Verification

```python
def validate_sources(fact: VerifiedFact, min_sources: int = 2) -> bool:
    """
    Require multiple reliable sources for controversial claims
    """
    reliable_sources = [s for s in fact.sources if s.reliability_score > 0.8]
    return len(reliable_sources) >= min_sources
```

### Rule 6: Contradiction Detection

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

## Implementation Example

### Complete Semantic Firewall System

```python
class SemanticFirewall:
    def __init__(self, knowledge_graph: MultidimensionalKG):
        self.kg = knowledge_graph
        self.validation_rules = [
            self.check_entity_existence,
            self.check_relationship_validity,
            self.check_temporal_consistency,
            self.check_confidence_threshold,
            self.check_source_verification,
            self.detect_contradictions
        ]
    
    def validate(self, llm_output: str, context: Dict) -> ValidationResult:
        """
        Run all validation rules on LLM output
        """
        # Extract structured facts from LLM output
        extracted_facts = self.extract_facts(llm_output)
        
        # Run validation rules
        for rule in self.validation_rules:
            result = rule(extracted_facts, context)
            if not result.passed:
                return ValidationResult(
                    allowed=False,
                    reason=result.reason,
                    failed_rule=rule.__name__,
                    suggested_fix=result.suggested_fix
                )
        
        return ValidationResult(allowed=True)
    
    def extract_facts(self, text: str) -> List[Fact]:
        """
        Extract entities, relationships, and claims from text
        """
        # Use NER, relation extraction, and fact extraction
        entities = self.ner_model.extract(text)
        relationships = self.relation_extractor.extract(text, entities)
        
        facts = []
        for rel in relationships:
            # Ground each relationship in knowledge graph
            kg_entities = self.kg.resolve_entities(rel.entities)
            kg_relationship = self.kg.resolve_relationship(
                kg_entities, rel.predicate
            )
            
            if kg_relationship:
                facts.append(Fact(
                    entities=kg_entities,
                    relationship=kg_relationship,
                    original_text=rel.text
                ))
        
        return facts
    
    def check_entity_existence(self, facts: List[Fact], context: Dict) -> RuleResult:
        """
        Verify all entities exist in knowledge graph
        """
        for fact in facts:
            for entity in fact.entities:
                if not self.kg.entity_exists(entity.id):
                    return RuleResult(
                        passed=False,
                        reason=f"Unknown entity: {entity.name}",
                        suggested_fix="Use only known entities from knowledge base"
                    )
        
        return RuleResult(passed=True)
    
    def check_relationship_validity(self, facts: List[Fact], context: Dict) -> RuleResult:
        """
        Verify relationships are valid and current
        """
        current_time = context.get('timestamp', datetime.now())
        
        for fact in facts:
            rel = self.kg.get_relationship(
                fact.entities[0].id,
                fact.relationship.predicate,
                fact.entities[1].id
            )
            
            if not rel:
                return RuleResult(
                    passed=False,
                    reason=f"No relationship found: {fact.relationship}",
                    suggested_fix="Verify relationship exists in knowledge graph"
                )
            
            # Check temporal validity
            if not rel.is_valid_at(current_time):
                return RuleResult(
                    passed=False,
                    reason=f"Relationship no longer valid: {fact.relationship}",
                    suggested_fix=f"Relationship was valid until {rel.valid_until}"
                )
        
        return RuleResult(passed=True)
    
    def check_confidence_threshold(self, facts: List[Fact], context: Dict) -> RuleResult:
        """
        Ensure facts meet confidence requirements
        """
        min_confidence = context.get('min_confidence', 0.7)
        
        for fact in facts:
            if fact.confidence < min_confidence:
                return RuleResult(
                    passed=False,
                    reason=f"Low confidence fact: {fact} (confidence: {fact.confidence})",
                    suggested_fix="Use only high-confidence facts"
                )
        
        return RuleResult(passed=True)
```

### Usage Example

```python
# Initialize system
kg = MultidimensionalKnowledgeGraph()
firewall = SemanticFirewall(kg)

# LLM generates response
user_query = "Who is the CEO of Apple?"
llm_response = llm.generate(user_query)

# Validate through firewall
validation = firewall.validate(llm_response, context={
    'timestamp': datetime.now(),
    'min_confidence': 0.8
})

if validation.allowed:
    # Response is grounded in verified facts
    return llm_response
else:
    # Block potential hallucination
    logger.warning(f"Blocked response: {validation.reason}")
    
    # Generate fallback response using only verified facts
    verified_facts = kg.query(user_query)
    fallback_response = generate_safe_response(verified_facts)
    return fallback_response
```

## Benefits

### 1. Proactive Protection
- Blocks unsupported claims before they reach users rather than flagging them after
- No post-hoc detection pass needed
- The check is deterministic and testable, so it can be regression tested
- Bounded by extraction coverage and graph correctness, both of which you must measure

### 2. Transparency
- Clear audit trail of validated facts
- Traceable to source documents
- Explainable rejections

### 3. Continuous Improvement
- Blocked responses reveal knowledge gaps
- Feedback loop for knowledge graph expansion
- Systematic reduction in hallucination rate

### 4. Domain Adaptability
- Configure rules per domain
- Adjust confidence thresholds
- Custom validation logic

### 5. Compliance & Trust
- Verifiable fact-checking
- Source attribution
- Regulatory compliance

## Metrics to Track

```python
# Firewall effectiveness metrics
firewall_metrics = {
    'block_rate': blocked_responses / total_responses,
    'false_positive_rate': incorrectly_blocked / total_blocked,
    'false_negative_rate': undetected_hallucinations / total_responses,
    'avg_confidence': avg(all_facts.confidence),
    'knowledge_coverage': known_entities / mentioned_entities
}

# Target metrics:
# - Block rate: 5-15% (catching hallucinations)
# - False positive rate: <2% (not blocking correct info)
# - Knowledge coverage: >95% (comprehensive graph)
```

## Implementation Roadmap

- [ ] Build initial knowledge graph with core entities
- [ ] Implement entity extraction from LLM outputs
- [ ] Add relationship validation rules
- [ ] Integrate temporal dimension
- [ ] Add confidence scoring system
- [ ] Implement source tracking and attribution
- [ ] Build contradiction detection logic
- [ ] Create feedback loop for blocked responses
- [ ] Monitor and tune confidence thresholds
- [ ] Expand knowledge graph coverage continuously

## Advanced Patterns

### Multi-Hop Validation

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
# Validate: Python -> created_by -> Guido [✓]
# Validate: Guido -> worked_at -> Google [✓]
```

### Probabilistic Validation

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

### Dynamic Threshold Adjustment

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

## Conclusion

The Semantic Firewall provides a principled approach to preventing AI hallucinations through structural validation against multidimensional knowledge graphs. By validating facts before they reach users, systems can provide:

- **Guaranteed accuracy**: Only verified facts pass through
- **Transparent reasoning**: Clear audit trail of validations
- **Continuous learning**: Blocked responses guide knowledge expansion
- **Domain expertise**: Tailored validation rules per use case

The Semantic Firewall transforms AI systems from "creative but unreliable" to "constrained but trustworthy."

## Further Reading

- [Multidimensional Knowledge Graphs](./multidimensional-knowledge-graphs.md) - Beyond flat context: constraint-based filtering
- [Compute-to-Lookup Ratio](./compute-to-lookup-ratio.md) - Optimization strategies
- [Headless Agent Patterns](./headless-agent.md) - Efficient coordination
- [Cognitive Systems Architect Role](./cognitive-systems-architect.md) - The role that builds these systems
