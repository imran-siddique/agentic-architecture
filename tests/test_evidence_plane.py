import copy
import unittest

from examples.evidence_plane_example import EvidenceIssuer, EvidenceVerifier


class EvidencePlaneTests(unittest.TestCase):
    def setUp(self):
        self.artifact = b"approved output"
        self.issuer = EvidenceIssuer("key-1", b"test-secret")
        self.verifier = EvidenceVerifier({"key-1": b"test-secret"})
        self.envelope = self.issuer.issue(
            receipt_id="r-1",
            action="report.publish",
            actor_id="agent://publisher/1",
            policy_id="policy://publishing/v1",
            policy_decision="allow",
            artifact=self.artifact,
        )

    def test_valid_receipt_is_accepted(self):
        self.assertTrue(self.verifier.verify(self.envelope, self.artifact))

    def test_tampered_claim_is_rejected(self):
        tampered = copy.deepcopy(self.envelope)
        tampered["claims"]["action"] = "admin.delete"
        self.assertFalse(self.verifier.verify(tampered, self.artifact))

    def test_different_artifact_is_rejected(self):
        self.assertFalse(self.verifier.verify(self.envelope, b"altered output"))

    def test_unknown_key_is_rejected(self):
        self.assertFalse(EvidenceVerifier({}).verify(self.envelope, self.artifact))

    def test_denied_action_cannot_be_attested(self):
        with self.assertRaises(PermissionError):
            self.issuer.issue(
                receipt_id="r-2",
                action="report.publish",
                actor_id="agent://publisher/1",
                policy_id="policy://publishing/v1",
                policy_decision="deny",
                artifact=self.artifact,
            )


if __name__ == "__main__":
    unittest.main()
