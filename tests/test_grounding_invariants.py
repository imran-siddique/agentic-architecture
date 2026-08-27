"""Executable checks for the semantic firewall.

docs/semantic-firewall.md states a bounded claim: every claim the extractor
turns into a checkable fact is checked against the graph before release. It also
states two gaps. Both the claim and the gaps are tested here, because a gap that
is only written in prose is a gap nobody remembers.
"""

import unittest
from datetime import datetime, timedelta

from examples.semantic_firewall_example import (
    Entity,
    Fact,
    MultidimensionalKnowledgeGraph,
    Relationship,
    SemanticFirewall,
)

NOW = datetime(2026, 1, 1)


def build_graph():
    kg = MultidimensionalKnowledgeGraph()
    acme = Entity(id="acme", name="Acme", type="organization")
    current = Entity(id="chen", name="Chen", type="person")
    former = Entity(id="rivera", name="Rivera", type="person")
    for entity in (acme, current, former):
        kg.add_entity(entity)

    kg.add_relationship(Relationship(
        subject=current, predicate="ceo_of", object=acme,
        valid_from=NOW - timedelta(days=365), confidence=0.99, sources=["filing-2025", "press-2025"],
    ))
    kg.add_relationship(Relationship(
        subject=former, predicate="ceo_of", object=acme,
        valid_from=NOW - timedelta(days=3650), valid_until=NOW - timedelta(days=365),
        confidence=0.99, sources=["filing-2016", "press-2016"],
    ))
    return kg, acme, current, former


def fact_for(subject, obj, relationship, text, confidence=0.99):
    return Fact(entities=[subject, obj], relationship=relationship,
                original_text=text, confidence=confidence)


class FirewallTests(unittest.TestCase):
    def setUp(self):
        self.kg, self.acme, self.current, self.former = build_graph()
        self.firewall = SemanticFirewall(self.kg)

    def _validate(self, fact, text="claim"):
        self.firewall._extract_facts = lambda _text, fact=fact: [fact]
        return self.firewall.validate(text)

    def test_a_supported_current_claim_passes(self):
        rel = self.kg.get_relationships("chen", "ceo_of", "acme")[0]
        result = self._validate(fact_for(self.current, self.acme, rel, "Chen is CEO of Acme"))
        self.assertTrue(result.passed, result.reason)

    def test_an_expired_relationship_is_blocked(self):
        rel = self.kg.get_relationships("rivera", "ceo_of", "acme")[0]
        result = self._validate(fact_for(self.former, self.acme, rel, "Rivera is CEO of Acme"))
        self.assertFalse(result.passed)
        self.assertTrue(result.reason, "a block must say why")

    def test_an_unknown_entity_is_blocked(self):
        ghost = Entity(id="nobody", name="Nobody", type="person")
        rel = Relationship(subject=ghost, predicate="ceo_of", object=self.acme,
                           valid_from=NOW, confidence=0.99, sources=["invented", "also-invented"])
        result = self._validate(fact_for(ghost, self.acme, rel, "Nobody is CEO of Acme"))
        self.assertFalse(result.passed)

    def test_a_single_sourced_claim_is_blocked(self):
        # Rule 4 requires two sources. A fact that is otherwise perfect fails
        # on provenance alone, which is the point of the rule.
        lone = Relationship(subject=self.current, predicate="ceo_of", object=self.acme,
                            valid_from=NOW - timedelta(days=30), confidence=0.99,
                            sources=["one-source"])
        fact = fact_for(self.current, self.acme, lone, "Chen is CEO of Acme")
        self.assertFalse(self._validate(fact).passed)

    def test_a_low_confidence_claim_is_blocked(self):
        rel = self.kg.get_relationships("chen", "ceo_of", "acme")[0]
        fact = fact_for(self.current, self.acme, rel, "Chen is CEO of Acme", confidence=0.1)
        self.assertFalse(self._validate(fact).passed)

    def test_the_threshold_is_configurable_and_is_actually_read(self):
        rel = self.kg.get_relationships("chen", "ceo_of", "acme")[0]
        fact = fact_for(self.current, self.acme, rel, "Chen is CEO of Acme", confidence=0.75)
        self.assertTrue(self._validate(fact).passed)
        self.firewall.min_confidence = 0.95
        self.assertFalse(self._validate(fact).passed)


class DocumentedGapTests(unittest.TestCase):
    """docs/semantic-firewall.md names two limits. If either stops being true,
    that document needs rewriting, so both are pinned here."""

    def setUp(self):
        self.kg, self.acme, self.current, self.former = build_graph()
        self.firewall = SemanticFirewall(self.kg)

    def test_a_claim_the_extractor_misses_passes_through_unchecked(self):
        # Gap one: the firewall protects what extraction hands it, nothing more.
        self.firewall._extract_facts = lambda _text: []
        result = self.firewall.validate("Acme was founded on Mars by a talking horse.")
        self.assertTrue(
            result.passed,
            "extraction coverage now bounds this differently; update the doc",
        )

    def test_a_wrong_fact_in_the_graph_is_enforced_as_confidently_as_a_right_one(self):
        # Gap two: the firewall inherits the correctness of the knowledge.
        liar = Entity(id="liar", name="Liar", type="person")
        self.kg.add_entity(liar)
        wrong = Relationship(subject=liar, predicate="ceo_of", object=self.acme,
                             valid_from=NOW - timedelta(days=10),
                             confidence=0.99, sources=["a-bad-source", "another-bad-source"])
        self.kg.add_relationship(wrong)
        fact = fact_for(liar, self.acme, wrong, "Liar is CEO of Acme")
        self.firewall._extract_facts = lambda _t, fact=fact: [fact]
        self.assertTrue(
            self.firewall.validate("Liar is CEO of Acme").passed,
            "the firewall started distinguishing true from merely-present facts",
        )


if __name__ == "__main__":
    unittest.main()
