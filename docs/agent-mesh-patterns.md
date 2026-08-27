# Agent Mesh Patterns: Identity, Trust, Governance, Reward

> **Learnings from the AgentMesh and Agent-OS prototypes, both now merged into [microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit)**

## The Problem: Agent Identity Crisis

As AI agents proliferate in enterprise environments, a critical gap emerges:

```
Non-human identities now outnumber human identities 40:1 to 100:1.
AI agents are the fastest-growing, least-governed identity category.
```

Protocols like A2A (Google) give agents a common language. MCP gives agents tools. **Neither enforces trust.**

## The Four-Layer Mesh Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 4  │  Reward & Learning Engine                           │
│           │  Per-agent trust scores · Adaptive behavior         │
├───────────┼─────────────────────────────────────────────────────┤
│  LAYER 3  │  Governance & Compliance Plane                      │
│           │  Policy engine · Merkle audit logs · Compliance     │
├───────────┼─────────────────────────────────────────────────────┤
│  LAYER 2  │  Trust & Protocol Bridge                            │
│           │  A2A · MCP · IATP · Capability scoping              │
├───────────┼─────────────────────────────────────────────────────┤
│  LAYER 1  │  Identity & Zero-Trust Core                         │
│           │  Agent CA · Ephemeral creds · Human sponsors        │
└───────────┴─────────────────────────────────────────────────────┘
```

## Pattern 1: Human Sponsor Accountability

**Principle**: Every autonomous agent must trace back to a human who accepts responsibility.

```python
identity = AgentIdentity.create(
    name="data-analyst-agent",
    sponsor="alice@company.com",  # Human accountability
    capabilities=["read:data", "write:reports"],
)
```

**Why this matters**:
- Clear audit trail for regulatory compliance
- Instant revocation path when things go wrong
- Solves the "who's responsible" problem for AI actions

## Pattern 2: Narrowing Delegation Chains

**Principle**: When agents delegate to sub-agents, capabilities must ONLY narrow, never expand.

```python
# Parent has: ["read:data", "write:reports", "delete:temp"]
child = parent.delegate(
    capabilities=["read:data"],  # Subset only
)
```

**Cryptographic Enforcement**:
- Delegation chains are signed
- Expansion attempts fail verification
- Blast radius is automatically contained

## Pattern 3: Ephemeral Credentials (15-Minute TTL)

**Principle**: Agent credentials should be short-lived by default.

| Traditional Approach | Mesh Approach |
|---------------------|---------------|
| Long-lived API keys | 15-minute TTL by default |
| Manual rotation | Auto-rotation |
| Static permissions | Dynamic capability scoping |

**Implementation**:
```python
credential = await mesh.issue_credential(
    agent_id=identity.id,
    ttl_minutes=15,  # Default
    capabilities=["read:specific-dataset"],
)
```

## Pattern 4: Trust Score, Not Binary Access

**Principle**: Replace binary allow/deny with continuous trust scoring.

```python
score = engine.get_agent_score("did:mesh:my-agent")
# {
#   "total": 847,
#   "dimensions": {
#     "policy_compliance": 95,
#     "resource_efficiency": 82,
#     "output_quality": 88,
#     "security_posture": 91,
#     "collaboration_health": 84
#   }
# }
```

**Behavioral Scoring Dimensions**:
1. **Policy Compliance**: How well does the agent follow rules?
2. **Resource Efficiency**: Is it using resources responsibly?
3. **Output Quality**: Are results accurate and useful?
4. **Security Posture**: Does it minimize attack surface?
5. **Collaboration Health**: How well does it work with other agents?

## Pattern 5: Merkle-Chained Audit Logs

**Principle**: Audit logs must be tamper-evident.

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Action 1 │───▶│ Action 2 │───▶│ Action 3 │
│ Hash: A  │    │ Hash: B  │    │ Hash: C  │
│          │    │ Prev: A  │    │ Prev: B  │
└──────────┘    └──────────┘    └──────────┘
```

**Properties**:
- Any tampering breaks the chain
- Verifiable history without central authority
- Compliant with SOC 2, HIPAA audit requirements

## Pattern 6: Shadow Mode for Policy Testing

**Principle**: Test policies in observation mode before enforcement.

```python
policy_engine = PolicyEngine(mode="shadow")

# Policy logs what WOULD happen, but doesn't block
result = await policy_engine.evaluate(action)
# result.would_block = True
# result.reason = "PII export attempt detected"
```

**Benefits**:
- Safe rollout of new policies
- Understand impact before enforcement
- Train teams on policy violations

## Pattern 7: Protocol Bridge (A2A + MCP + IATP)

**Principle**: Unified trust model across all agent protocols.

```
┌─────────────────────────────────────────────────────┐
│                   Trust Bridge                       │
├─────────────────────────────────────────────────────┤
│    A2A          │     MCP          │     IATP       │
│  (Coordination) │   (Tools)        │   (Trust)      │
│                 │                  │                │
│  ──────────────── Unified Trust ─────────────────── │
└─────────────────────────────────────────────────────┘
```

**Key Insight**: The bridge normalizes trust verification regardless of underlying protocol.

## Integration with Agent-OS

AgentMesh builds on Agent-OS kernel primitives:

```python
# AgentMesh uses Agent-OS for IATP
pip install agentmesh-platform[agent-os]
```

| Component | Agent-OS | AgentMesh |
|-----------|----------|-----------|
| IATP Protocol | ✅ Core implementation | Uses via dependency |
| CMVK Verification | ✅ Core implementation | Uses for trust |
| Identity Management | Basic | Full CA + delegation |
| Governance | Policy engine | Full compliance suite |
| Audit | Basic logging | Merkle chains |

## Threat Model

| Threat | Defense Pattern |
|--------|-----------------|
| Prompt Injection | Output sanitization at Protocol Bridge |
| Credential Theft | Ephemeral credentials (15-min TTL) |
| Shadow Agents | Registration required, unregistered blocked |
| Delegation Escalation | Cryptographically narrowing chains |
| Cascade Failure | Per-agent trust scoring isolates blast radius |

## Production Checklist

- [ ] Every agent has a human sponsor
- [ ] Credentials are ephemeral (default 15-min TTL)
- [ ] Delegation chains only narrow
- [ ] All actions are audit-logged (Merkle)
- [ ] Trust scores are monitored
- [ ] Shadow mode tested before enforcement
- [ ] Protocol bridge handles all cross-agent comms

## Further Reading

- [Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit) - The maintained implementation of the mesh and kernel work described here
- [Control Planes vs Prompts](./control-planes-vs-prompts.md) - Why deterministic beats probabilistic
- [Mute Agent Pattern](./mute-agent.md) - Capability-based execution

---

*"Agents shouldn't be islands. But they also shouldn't be ungoverned."*
