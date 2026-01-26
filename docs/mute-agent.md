# The Mute Agent

> **Capability-Based Execution: Return NULL, Don't Hallucinate**

## The Problem

Traditional AI agents try to be helpful by answering everything. This "helpfulness" becomes a liability when:
- Agents fabricate answers outside their training
- Users can't distinguish confident knowledge from confident hallucination
- Errors cascade through multi-agent systems
- Trust erodes as users discover false confidence

## The Solution: Capability-Based Execution

The Mute Agent pattern implements a simple principle: **agents return NULL for out-of-scope requests instead of hallucinating**.

```python
class MuteAgent:
    def __init__(self, capabilities: CapabilityManifest):
        self.capabilities = capabilities
    
    def execute(self, request: Request) -> Response | None:
        # Check capability BEFORE attempting execution
        if not self.capabilities.can_handle(request):
            return None  # Silent, not sorry
        
        # Only execute what we CAN do
        return self._execute_capability(request)
```

## Core Principles

### 1. Capability Manifests

Every agent declares what it CAN do, not what it might try:

```python
capabilities = CapabilityManifest(
    can_read=["user_profile", "order_history"],
    can_write=["preferences"],
    can_execute=["calculate_shipping", "apply_discount"],
    cannot=["*"]  # Everything else returns NULL
)
```

### 2. NULL is Better Than Fabrication

```
Traditional Agent:
  User: "What's the weather in Paris?"
  Agent: "It's currently 22°C and sunny in Paris." 
         # (Hallucinated - agent has no weather capability)

Mute Agent:
  User: "What's the weather in Paris?"
  Agent: NULL
         # Silence indicates: "I cannot answer this"
```

### 3. Explicit Over Implicit

```python
# Bad: Implicit capability (tries everything)
def handle_request(request):
    return llm.complete(request.prompt)  # Will fabricate if needed

# Good: Explicit capability (only does what's declared)
def handle_request(request):
    if not capabilities.covers(request):
        return NULL
    return execute_within_boundaries(request)
```

## Implementation Pattern

### The Capability Check Layer

```python
class CapabilityGate:
    def __init__(self, manifest: CapabilityManifest):
        self.manifest = manifest
    
    def check(self, action: str, resource: str) -> bool:
        """Returns True only if capability is explicitly granted."""
        return self.manifest.has_permission(action, resource)
    
    def guard(self, func):
        """Decorator that enforces capability checks."""
        @wraps(func)
        def wrapper(action: str, resource: str, *args, **kwargs):
            if not self.check(action, resource):
                return NullResponse(
                    reason="CAPABILITY_NOT_GRANTED",
                    requested_action=action,
                    requested_resource=resource
                )
            return func(action, resource, *args, **kwargs)
        return wrapper
```

### POSIX-Inspired Permissions

Like Unix file permissions, but for AI capabilities:

```python
class AgentPermissions:
    READ = 0b100    # Can retrieve information
    WRITE = 0b010   # Can modify state
    EXECUTE = 0b001 # Can trigger actions
    
    def __init__(self, mask: int):
        self.mask = mask
    
    def can_read(self) -> bool:
        return bool(self.mask & self.READ)
    
    def can_write(self) -> bool:
        return bool(self.mask & self.WRITE)
    
    def can_execute(self) -> bool:
        return bool(self.mask & self.EXECUTE)
```

### Policy Enforcement

```python
class PolicyEnforcer:
    """Deterministic rules, not probabilistic guardrails."""
    
    def __init__(self, policies: list[Policy]):
        self.policies = policies
    
    def evaluate(self, request: Request) -> PolicyDecision:
        for policy in self.policies:
            result = policy.evaluate(request)
            if result.action == "DENY":
                return PolicyDecision(
                    allowed=False,
                    reason=result.reason,
                    policy_id=policy.id
                )
        return PolicyDecision(allowed=True)
```

## The 0% Violation Guarantee

Traditional prompt-based safety relies on the LLM understanding and following instructions. This fails:

| Approach | Safety Violations |
|----------|-------------------|
| Prompt Engineering | 26.67% |
| System Prompts | 18.33% |
| **Mute Agent (Capability-Based)** | **0%** |

The difference: **Capabilities are checked BEFORE the LLM runs.**

```
Prompt-Based Safety:
  Request → LLM (interprets safety) → Response (may violate)

Mute Agent Safety:
  Request → Capability Check → [DENY or LLM] → Response (guaranteed safe)
```

## Multi-Agent Considerations

In multi-agent systems, Mute Agents prevent cascading hallucinations:

```python
class MultiAgentOrchestrator:
    def route_request(self, request: Request) -> Response:
        for agent in self.agents:
            response = agent.execute(request)
            if response is not None:
                return response
        
        # No agent could handle it - that's information, not failure
        return NullResponse(
            reason="NO_CAPABLE_AGENT",
            tried_agents=[a.id for a in self.agents]
        )
```

## When to Use NULL vs Error

| Situation | Response |
|-----------|----------|
| Agent lacks capability | `NULL` |
| Request is malformed | `Error` |
| External service failed | `Error` with retry info |
| User lacks permission | `NULL` or `PermissionDenied` |
| Request is out of scope | `NULL` |

## Real-World Example

```python
# E-commerce Support Agent
support_agent = MuteAgent(
    capabilities=CapabilityManifest(
        can_read=["order_status", "shipping_info", "return_policy"],
        can_write=["support_ticket", "refund_request"],
        can_execute=["initiate_return", "escalate_to_human"],
        # Implicitly cannot: modify_order, access_payment_info, etc.
    )
)

# User: "Can you change my credit card?"
result = support_agent.execute(ModifyPaymentRequest(...))
# Returns: NULL (not "Sure, I'll help with that!" followed by failure)

# The NULL tells the orchestrator to route to the correct agent
# or inform the user this requires a different channel
```

## Benefits

1. **Predictable Behavior**: Know exactly what an agent will and won't do
2. **Trust Through Honesty**: Silence is better than false confidence
3. **Audit Trail**: Every NULL is logged with capability context
4. **Composable Systems**: Agents with clear boundaries integrate cleanly
5. **Security by Design**: Cannot be jailbroken into doing unsupported actions

## Key Insight

> "An agent that returns NULL when uncertain is infinitely more valuable than one that confidently hallucinates."

The most reliable agent is one that knows when to say nothing.

---

**Related Patterns:**
- [Semantic Firewall](./semantic-firewall.md) - Structural hallucination prevention
- [Control Planes vs Prompts](./control-planes-vs-prompts.md) - Deterministic safety
- [Silent Swarm](./silent-swarm.md) - Security by silence
