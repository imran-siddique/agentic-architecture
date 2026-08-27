"""
Example: Semantic Firewall Implementation

This example demonstrates how to use multidimensional knowledge graphs
to block hallucinations before they reach users.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class Severity(Enum):
    """Severity levels for validation rules"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Entity:
    """Entity in knowledge graph"""
    id: str
    name: str
    type: str  # person, organization, product, etc.
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Relationship:
    """Relationship between entities"""
    subject: Entity
    predicate: str  # works_for, located_in, invented_by, etc.
    object: Entity
    valid_from: datetime
    valid_until: Optional[datetime] = None
    confidence: float = 1.0
    sources: List[str] = field(default_factory=list)


@dataclass
class Fact:
    """Extracted fact from LLM output"""
    entities: List[Entity]
    relationship: Relationship
    original_text: str
    confidence: float = 1.0


@dataclass
class ValidationResult:
    """Result from validation rules"""
    passed: bool
    reason: str = ""
    failed_rule: str = ""
    suggested_fix: str = ""


class MultidimensionalKnowledgeGraph:
    """
    Knowledge graph with multiple dimensions:
    - Entity-Relationship
    - Temporal
    - Confidence & Provenance
    - Semantic Context
    """
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []
    
    def add_entity(self, entity: Entity):
        """Add entity to knowledge graph"""
        self.entities[entity.id] = entity
    
    def add_relationship(self, relationship: Relationship):
        """Add relationship to knowledge graph"""
        self.relationships.append(relationship)
    
    def entity_exists(self, entity_id: str) -> bool:
        """Check if entity exists"""
        return entity_id in self.entities
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return self.entities.get(entity_id)
    
    def get_relationships(self, subject_id: str, predicate: str, object_id: str) -> List[Relationship]:
        """Get relationships matching criteria"""
        return [
            rel for rel in self.relationships
            if rel.subject.id == subject_id
            and rel.predicate == predicate
            and rel.object.id == object_id
        ]
    
    def is_relationship_valid(self, relationship: Relationship, at_time: datetime) -> bool:
        """Check if relationship is valid at given time"""
        if at_time < relationship.valid_from:
            return False
        if relationship.valid_until and at_time > relationship.valid_until:
            return False
        return True


class SemanticFirewall:
    """
    Validates LLM outputs against knowledge graph to prevent hallucinations
    """
    
    def __init__(self, knowledge_graph: MultidimensionalKnowledgeGraph):
        self.kg = knowledge_graph
        self.min_confidence = 0.7  # Default threshold
    
    def validate(self, llm_output: str, context: Optional[Dict] = None) -> ValidationResult:
        """
        Validate LLM output against knowledge graph
        """
        context = context or {}
        
        # Extract facts from LLM output
        facts = self._extract_facts(llm_output)
        
        if not facts:
            # No facts to validate - allow simple responses
            return ValidationResult(passed=True)
        
        # Run validation rules
        for fact in facts:
            # Rule 1: Entity Existence Check
            result = self._check_entity_existence(fact)
            if not result.passed:
                return result
            
            # Rule 2: Relationship Validity Check
            result = self._check_relationship_validity(fact, context)
            if not result.passed:
                return result
            
            # Rule 3: Confidence Threshold Check
            result = self._check_confidence_threshold(fact)
            if not result.passed:
                return result
            
            # Rule 4: Source Verification
            result = self._check_source_verification(fact)
            if not result.passed:
                return result
        
        # Rule 5: Temporal Consistency Check
        result = self._check_temporal_consistency(facts)
        if not result.passed:
            return result
        
        # Rule 6: Contradiction Detection
        result = self._check_contradictions(facts)
        if not result.passed:
            return result
        
        return ValidationResult(passed=True)
    
    def _extract_facts(self, text: str) -> List[Fact]:
        """
        Extract structured facts from text
        
        NOTE: In production, this would use:
        - Named Entity Recognition (NER) models
        - Relation extraction models
        - Entity linking to knowledge graph
        
        This example overrides this method in main() for testing purposes
        to demonstrate the validation rules without requiring NLP models.
        """
        # Simplified extraction for demonstration
        # In this example, facts are manually constructed in main()
        # to demonstrate the validation capabilities
        facts = []
        
        # Production implementation would:
        # 1. Use NER to extract entities (e.g., spaCy, Stanford NER)
        # 2. Use relation extraction to identify relationships
        # 3. Link entities to knowledge graph IDs
        # 4. Build Fact objects with confidence scores
        
        return facts
    
    def _check_entity_existence(self, fact: Fact) -> ValidationResult:
        """Rule 1: Verify all entities exist in knowledge graph"""
        for entity in fact.entities:
            if not self.kg.entity_exists(entity.id):
                return ValidationResult(
                    passed=False,
                    reason=f"Unknown entity: {entity.name}",
                    failed_rule="entity_existence",
                    suggested_fix="Only use entities from verified knowledge base"
                )
        
        return ValidationResult(passed=True)
    
    def _check_relationship_validity(self, fact: Fact, context: Dict) -> ValidationResult:
        """Rule 2: Verify relationship is valid and current"""
        rel = fact.relationship
        current_time = context.get('timestamp', datetime.now())
        
        # Find matching relationships in knowledge graph
        matches = self.kg.get_relationships(
            rel.subject.id,
            rel.predicate,
            rel.object.id
        )
        
        if not matches:
            return ValidationResult(
                passed=False,
                reason=f"No relationship found: {rel.subject.name} {rel.predicate} {rel.object.name}",
                failed_rule="relationship_validity",
                suggested_fix="Verify relationship exists in knowledge graph"
            )
        
        # Check temporal validity
        valid_matches = [
            m for m in matches
            if self.kg.is_relationship_valid(m, current_time)
        ]
        
        if not valid_matches:
            return ValidationResult(
                passed=False,
                reason=f"Relationship no longer valid: {rel.subject.name} {rel.predicate} {rel.object.name}",
                failed_rule="relationship_validity",
                suggested_fix="Relationship may have expired"
            )
        
        return ValidationResult(passed=True)
    
    def _check_confidence_threshold(self, fact: Fact) -> ValidationResult:
        """Rule 3: Ensure fact meets confidence threshold"""
        if fact.confidence < self.min_confidence:
            return ValidationResult(
                passed=False,
                reason=f"Low confidence fact: {fact.confidence:.2f} < {self.min_confidence:.2f}",
                failed_rule="confidence_threshold",
                suggested_fix="Use only high-confidence facts"
            )
        
        return ValidationResult(passed=True)
    
    def _check_source_verification(self, fact: Fact) -> ValidationResult:
        """Rule 4: Verify fact has reliable sources"""
        min_sources = 2
        
        if len(fact.relationship.sources) < min_sources:
            return ValidationResult(
                passed=False,
                reason=f"Insufficient sources: {len(fact.relationship.sources)} < {min_sources}",
                failed_rule="source_verification",
                suggested_fix="Require multiple reliable sources"
            )
        
        return ValidationResult(passed=True)
    
    def _check_temporal_consistency(self, facts: List[Fact]) -> ValidationResult:
        """Rule 5: Ensure facts don't contradict temporally"""
        # Check for temporal impossibilities
        for i, fact1 in enumerate(facts):
            for fact2 in facts[i+1:]:
                # Check if same subject has contradictory relationships at same time
                if (fact1.relationship.subject.id == fact2.relationship.subject.id and
                    fact1.relationship.predicate == fact2.relationship.predicate and
                    fact1.relationship.object.id != fact2.relationship.object.id):
                    
                    # Check if time periods overlap
                    r1_start = fact1.relationship.valid_from
                    r1_end = fact1.relationship.valid_until or datetime.max
                    r2_start = fact2.relationship.valid_from
                    r2_end = fact2.relationship.valid_until or datetime.max
                    
                    # If periods overlap, it's a temporal contradiction
                    if not (r1_end < r2_start or r2_end < r1_start):
                        return ValidationResult(
                            passed=False,
                            reason=f"Temporal contradiction: {fact1.relationship.subject.name} cannot have two {fact1.relationship.predicate} relationships at once",
                            failed_rule="temporal_consistency",
                            suggested_fix="Check for overlapping time periods"
                        )
        
        return ValidationResult(passed=True)
    
    def _check_contradictions(self, facts: List[Fact]) -> ValidationResult:
        """Rule 6: Detect contradictions with existing knowledge"""
        for fact in facts:
            rel = fact.relationship
            
            # Find all existing relationships for this subject and predicate
            existing = [
                r for r in self.kg.relationships
                if (r.subject.id == rel.subject.id and 
                    r.predicate == rel.predicate and
                    r.object.id != rel.object.id)
            ]
            
            # Check if fact contradicts current knowledge
            for existing_rel in existing:
                # If existing relationship is currently valid and different, it's a contradiction
                if self.kg.is_relationship_valid(existing_rel, datetime.now()):
                    if existing_rel.object.id != rel.object.id:
                        return ValidationResult(
                            passed=False,
                            reason=f"Contradiction: {rel.subject.name} {rel.predicate} {existing_rel.object.name} (known), but claimed {rel.object.name}",
                            failed_rule="contradiction_detection",
                            suggested_fix="Verify against current knowledge base"
                        )
        
        return ValidationResult(passed=True)


# Example usage
def main():
    print("=" * 60)
    print("Semantic Firewall Example")
    print("=" * 60)
    print("SIMULATION. No model is called. Every latency and cost printed below")
    print("is a constant written into this file so the control flow is readable.")
    print("None of it is a measurement. See CONTRIBUTING.md for the standard.")
    print()
    
    # Build knowledge graph
    print("\n1. Building Knowledge Graph...")
    kg = MultidimensionalKnowledgeGraph()
    
    # Add entities
    apple = Entity(id="apple", name="Apple Inc.", type="organization")
    tim_cook = Entity(id="tim_cook", name="Tim Cook", type="person")
    steve_jobs = Entity(id="steve_jobs", name="Steve Jobs", type="person")
    iphone = Entity(id="iphone", name="iPhone", type="product")
    
    kg.add_entity(apple)
    kg.add_entity(tim_cook)
    kg.add_entity(steve_jobs)
    kg.add_entity(iphone)
    
    print(f"   Added {len(kg.entities)} entities")
    
    # Add relationships with temporal dimension
    print("\n2. Adding Relationships (with temporal dimension)...")
    
    # Steve Jobs was CEO until 2011
    kg.add_relationship(Relationship(
        subject=steve_jobs,
        predicate="ceo_of",
        object=apple,
        valid_from=datetime(1997, 1, 1),
        valid_until=datetime(2011, 8, 24),
        confidence=0.99,
        sources=["wikipedia", "apple.com"]
    ))
    
    # Tim Cook became CEO in 2011
    kg.add_relationship(Relationship(
        subject=tim_cook,
        predicate="ceo_of",
        object=apple,
        valid_from=datetime(2011, 8, 24),
        valid_until=None,  # Current
        confidence=0.99,
        sources=["wikipedia", "apple.com", "sec.gov"]
    ))
    
    # iPhone invented by Apple
    kg.add_relationship(Relationship(
        subject=apple,
        predicate="invented",
        object=iphone,
        valid_from=datetime(2007, 1, 9),
        valid_until=None,
        confidence=0.99,
        sources=["apple.com", "wikipedia"]
    ))
    
    print(f"   Added {len(kg.relationships)} relationships")
    
    # Create semantic firewall
    print("\n3. Initializing Semantic Firewall...")
    firewall = SemanticFirewall(kg)
    print("   Firewall ready with validation rules")
    
    # Test cases
    print("\n4. Testing Validation Cases:")
    print("-" * 60)
    
    test_cases = [
        {
            "name": "Valid current fact",
            "output": "Tim Cook is the CEO of Apple",
            "context": {"timestamp": datetime.now()},
            "should_pass": True
        },
        {
            "name": "Expired relationship",
            "output": "Steve Jobs is the CEO of Apple",
            "context": {"timestamp": datetime.now()},
            "should_pass": False
        },
        {
            "name": "Historical fact (valid in past)",
            "output": "Steve Jobs was the CEO of Apple",
            "context": {"timestamp": datetime(2010, 1, 1)},
            "should_pass": True
        },
        {
            "name": "Unknown entity",
            "output": "John Doe is the CEO of Apple",
            "context": {"timestamp": datetime.now()},
            "should_pass": False
        },
        {
            "name": "Simple greeting (no facts)",
            "output": "Hello, how can I help you?",
            "context": {},
            "should_pass": True
        }
    ]
    
    results = []
    for test in test_cases:
        # Create fact for testing
        if "Tim Cook" in test["output"]:
            fact = Fact(
                entities=[tim_cook, apple],
                relationship=kg.relationships[1],  # Tim Cook CEO relationship
                original_text=test["output"],
                confidence=0.95
            )
            firewall._extract_facts = lambda text, fact=fact: [fact] if "Tim Cook" in text else []
        elif "Steve Jobs" in test["output"]:
            fact = Fact(
                entities=[steve_jobs, apple],
                relationship=kg.relationships[0],  # Steve Jobs CEO relationship
                original_text=test["output"],
                confidence=0.95
            )
            firewall._extract_facts = lambda text, fact=fact: [fact] if "Steve Jobs" in text else []
        elif "John Doe" in test["output"]:
            unknown_person = Entity(id="john_doe", name="John Doe", type="person")
            fact = Fact(
                entities=[unknown_person, apple],
                relationship=Relationship(
                    subject=unknown_person,
                    predicate="ceo_of",
                    object=apple,
                    valid_from=datetime.now(),
                    confidence=0.95,
                    sources=[]
                ),
                original_text=test["output"],
                confidence=0.95
            )
            firewall._extract_facts = lambda text, fact=fact: [fact] if "John Doe" in text else []
        else:
            firewall._extract_facts = lambda text: []
        
        result = firewall.validate(test["output"], test["context"])
        results.append({
            "test": test,
            "result": result
        })
        
        status = "✓ ALLOWED" if result.passed else "✗ BLOCKED"
        expected = "✓" if test["should_pass"] else "✗"
        correct = "✓" if (result.passed == test["should_pass"]) else "✗ WRONG"
        
        print(f"\n   Test: {test['name']}")
        print(f"      Query: \"{test['output']}\"")
        print(f"      Status: {status}")
        print(f"      Expected: {expected}")
        print(f"      Correct: {correct}")
        
        if not result.passed:
            print(f"      Reason: {result.reason}")
            print(f"      Failed Rule: {result.failed_rule}")
    
    # Summary
    print("\n5. Summary:")
    print("-" * 60)
    total = len(results)
    correct = sum(1 for r in results if r["result"].passed == r["test"]["should_pass"])
    blocked = sum(1 for r in results if not r["result"].passed)
    
    print(f"   Total Tests: {total}")
    print(f"   Correct Validations: {correct}/{total} ({correct/total*100:.1f}%)")
    print(f"   Hallucinations Blocked: {blocked}")
    print(f"   Valid Responses Allowed: {total - blocked}")
    
    # Benefits
    print("\n6. Key Benefits of Semantic Firewall:")
    print("-" * 60)
    print("   ✓ Proactive Protection: Blocks hallucinations before reaching users")
    print("   ✓ Temporal Awareness: Validates time-based relationships")
    print("   ✓ Transparency: Clear reasons for blocking")
    print("   ✓ Knowledge Grounded: All facts verified against KB")
    print("   ✓ Confidence Tracking: Ensures high-quality outputs")
    print("   ✓ Multi-dimensional: Entity, temporal, confidence, source validation")
    
    # Architecture insight
    print("\n7. Architecture Insight:")
    print("-" * 60)
    print("   Traditional Approach:")
    print("      LLM generates → Hope it's correct → Show to user")
    print("      Result: Hallucinations reach users")
    
    print("\n   Semantic Firewall Approach:")
    print("      LLM generates → Validate against KB → Block if invalid")
    print("      Result: Only verified facts reach users")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
