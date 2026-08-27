"""A minimal evidence plane for verifiable agent actions.

This example deliberately separates an action result from the evidence used to
verify it. HMAC keeps the demo dependency-free; production systems should use
an asymmetric, hardware-backed signing key and publish its verification key.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict


def _canonical_json(value: Dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def artifact_digest(artifact: bytes) -> str:
    return "sha256:" + hashlib.sha256(artifact).hexdigest()


@dataclass(frozen=True)
class EvidenceReceipt:
    receipt_id: str
    action: str
    actor_id: str
    policy_id: str
    policy_decision: str
    artifact_digest: str
    issued_at: str
    key_id: str

    def claims(self) -> Dict[str, str]:
        return asdict(self)


class EvidenceIssuer:
    """Issues signed receipts only for explicitly allowed actions."""

    def __init__(self, key_id: str, signing_key: bytes):
        if not signing_key:
            raise ValueError("signing_key must not be empty")
        self.key_id = key_id
        self._signing_key = signing_key

    def issue(
        self,
        *,
        receipt_id: str,
        action: str,
        actor_id: str,
        policy_id: str,
        policy_decision: str,
        artifact: bytes,
    ) -> Dict[str, Any]:
        if policy_decision != "allow":
            raise PermissionError("refusing to attest an action that policy did not allow")

        receipt = EvidenceReceipt(
            receipt_id=receipt_id,
            action=action,
            actor_id=actor_id,
            policy_id=policy_id,
            policy_decision=policy_decision,
            artifact_digest=artifact_digest(artifact),
            issued_at=datetime.now(timezone.utc).isoformat(),
            key_id=self.key_id,
        )
        claims = receipt.claims()
        signature = hmac.new(self._signing_key, _canonical_json(claims), hashlib.sha256).hexdigest()
        return {"claims": claims, "signature": signature}


class EvidenceVerifier:
    """Verifies provenance, integrity, policy outcome, and artifact binding."""

    REQUIRED_CLAIMS = {
        "receipt_id",
        "action",
        "actor_id",
        "policy_id",
        "policy_decision",
        "artifact_digest",
        "issued_at",
        "key_id",
    }

    def __init__(self, trusted_keys: Dict[str, bytes]):
        self._trusted_keys = trusted_keys

    def verify(self, envelope: Dict[str, Any], artifact: bytes) -> bool:
        claims = envelope.get("claims")
        signature = envelope.get("signature")
        if not isinstance(claims, dict) or not isinstance(signature, str):
            return False
        if set(claims) != self.REQUIRED_CLAIMS:
            return False
        key = self._trusted_keys.get(claims["key_id"])
        if key is None or claims["policy_decision"] != "allow":
            return False
        if not hmac.compare_digest(claims["artifact_digest"], artifact_digest(artifact)):
            return False
        expected = hmac.new(key, _canonical_json(claims), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)


def main() -> None:
    artifact = b'{"status":"completed","records_updated":3}'
    issuer = EvidenceIssuer("demo-key-1", b"replace-this-demo-secret")
    envelope = issuer.issue(
        receipt_id="receipt-001",
        action="customer-records.update",
        actor_id="agent://crm-writer/7",
        policy_id="policy://crm/update/v3",
        policy_decision="allow",
        artifact=artifact,
    )
    verifier = EvidenceVerifier({"demo-key-1": b"replace-this-demo-secret"})
    print(json.dumps(envelope, indent=2))
    print("verified:", verifier.verify(envelope, artifact))


if __name__ == "__main__":
    main()
