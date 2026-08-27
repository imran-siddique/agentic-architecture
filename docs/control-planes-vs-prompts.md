# Control Planes vs Prompts

> **Why Deterministic Infrastructure Beats Probabilistic Prompting**

> The numbers in this document are worked examples on stated assumptions, or
> design targets. None of them are measurements. See the evidence standard in
> [CONTRIBUTING.md](../CONTRIBUTING.md#evidence-standard).

## The Problem

The AI industry has a dangerous habit: trying to "prompt engineer" safety into existence.

```python
# This is how most teams implement AI safety
system_prompt = """
You are a helpful assistant. You MUST NOT:
- Reveal confidential information
- Execute dangerous commands
- Provide harmful advice

Always be safe and responsible.
"""
```

This doesn't work. Here's why:

### Prompts Are Suggestions, Not Laws

| Analogy | Why It Fails |
|---------|--------------|
| Web Security | You wouldn't secure a login page with: "Please don't hack this" |
| Database Access | You wouldn't protect data with: "Only return rows the user can see" |
| File System | You wouldn't prevent deletion with: "Be careful with rm commands" |

Yet this is exactly what we do with AI agents.

## The Solution: Control Plane Architecture

A **Control Plane** is infrastructure-level enforcement that operates BELOW the LLM layer:

```
┌─────────────────────────────────────────┐
│            User Request                  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         CONTROL PLANE                    │  ← Deterministic
│  ┌─────────────────────────────────┐    │
│  │  Permission Check               │    │
│  │  Policy Evaluation              │    │
│  │  Resource Boundaries            │    │
│  │  Audit Logging                  │    │
│  └─────────────────────────────────┘    │
└────────────────┬────────────────────────┘
                 │
        [ALLOWED or DENIED]
                 │
                 ▼ (only if ALLOWED)
┌─────────────────────────────────────────┐
│              LLM Layer                   │  ← Probabilistic
│         (Handles allowed tasks)          │
└─────────────────────────────────────────┘
```

## Core Principles

### 1. Permissions, Not Prompts

```python
# Bad: Prompt-based safety
prompt = "Do not access files outside /home/user"

# Good: Permission-based safety
class AgentPermissions:
    allowed_paths = ["/home/user"]
    
    def can_access(self, path: str) -> bool:
        return any(path.startswith(p) for p in self.allowed_paths)
```

### 2. Policies Are Code, Not Text

```python
# Bad: Policy in natural language
policy = "Only allow financial queries during business hours for tier-2+ users"

# Good: Policy as executable code
class FinancialQueryPolicy:
    def evaluate(self, request: Request, context: Context) -> Decision:
        if request.type != "financial_query":
            return Decision.SKIP
        
        if not context.is_business_hours():
            return Decision.DENY("Outside business hours")
        
        if context.user.tier < 2:
            return Decision.DENY("Requires tier 2+")
        
        return Decision.ALLOW
```

### 3. Kernel-Level Enforcement

The control plane operates like an OS kernel. The LLM is a user-space process:

```python
class AgentKernel:
    def __init__(self, policies: list[Policy], permissions: Permissions):
        self.policies = policies
        self.permissions = permissions
        self.audit_log = AuditLog()
    
    def syscall(self, agent_id: str, action: str, resource: str) -> Result:
        """All agent actions go through the kernel."""
        
        # 1. Check permissions (capability-based)
        if not self.permissions.check(agent_id, action, resource):
            self.audit_log.denied(agent_id, action, resource, "NO_PERMISSION")
            return Result.DENIED
        
        # 2. Evaluate policies (rule-based)
        for policy in self.policies:
            decision = policy.evaluate(action, resource)
            if decision.is_deny():
                self.audit_log.denied(agent_id, action, resource, decision.reason)
                return Result.DENIED
        
        # 3. Execute with audit trail
        self.audit_log.allowed(agent_id, action, resource)
        return self._execute(action, resource)
```

### 4. Audit Everything

```python
class AuditLog:
    def log_action(self, entry: AuditEntry):
        """Every action is logged with full context."""
        entry.timestamp = datetime.utcnow()
        entry.trace_id = current_trace_id()
        self.store.append(entry)
    
    def get_agent_history(self, agent_id: str) -> list[AuditEntry]:
        """Complete history of what an agent did."""
        return self.store.query(agent_id=agent_id)
    
    def find_violations(self, time_range: TimeRange) -> list[AuditEntry]:
        """Find any policy violations (should be empty with control plane)."""
        return self.store.query(
            time_range=time_range,
            status="DENIED"
        )
```

### 5. Rollback Capability

```python
class TransactionalExecution:
    def execute_with_rollback(self, action: Action) -> Result:
        """Every action can be undone."""
        
        # Capture state before
        snapshot = self.capture_state(action.affected_resources)
        
        try:
            result = action.execute()
            
            if result.needs_review:
                # Hold in pending state
                self.pending_actions.add(action, snapshot)
                return Result.PENDING_REVIEW
            
            return result
            
        except Exception as e:
            # Automatic rollback on failure
            self.restore_state(snapshot)
            return Result.FAILED(e)
    
    def rollback_action(self, action_id: str):
        """Manually rollback any past action."""
        action, snapshot = self.history.get(action_id)
        self.restore_state(snapshot)
        self.audit_log.rollback(action_id)
```

## Comparison: Prompts vs Control Planes

| Aspect | Prompt-Based | Control Plane |
|--------|--------------|---------------|
| Enforcement | Suggestions | Laws |
| Reliability | Depends on the model and the attack | Depends on the code, and is testable |
| Bypass | Jailbreaks work | Cannot bypass |
| Audit | Hope LLM logged it | Every action logged |
| Rollback | Not possible | Full undo capability |
| Testing | "Does this prompt work?" | Unit tests for policies |
| Compliance | "We told it to be safe" | Provable enforcement |

## Real-World Implementation

```python
class EnterpriseAgentControlPlane:
    def __init__(self):
        self.permission_manager = PermissionManager()
        self.policy_engine = PolicyEngine()
        self.audit_system = AuditSystem()
        self.transaction_manager = TransactionManager()
    
    def handle_request(self, request: AgentRequest) -> AgentResponse:
        # Gate 1: Authentication
        if not self.authenticate(request):
            return AgentResponse.UNAUTHORIZED
        
        # Gate 2: Permission check
        permissions = self.permission_manager.get(request.agent_id)
        if not permissions.allows(request.action, request.resource):
            self.audit_system.log_denied(request, "PERMISSION_DENIED")
            return AgentResponse.FORBIDDEN
        
        # Gate 3: Policy evaluation
        policy_result = self.policy_engine.evaluate(request)
        if policy_result.is_deny():
            self.audit_system.log_denied(request, policy_result.reason)
            return AgentResponse.POLICY_VIOLATION
        
        # Gate 4: Execute with transaction wrapper
        with self.transaction_manager.transaction() as txn:
            result = self.execute(request)
            
            if policy_result.requires_review:
                txn.hold_for_review()
                return AgentResponse.PENDING_REVIEW
            
            txn.commit()
            self.audit_system.log_success(request, result)
            return AgentResponse.success(result)
```

## The Numbers Don't Lie

| Safety approach | Where the rule lives | Bypass route |
|-----------------|----------------------|--------------|
| No safety measures | Nowhere | Any request |
| Prompt engineering | In the model's context | Jailbreaks |
| System prompts | In the model's context, higher priority | Prompt injection |
| Model-level training | In the weights | Distribution shift, novel attacks |
| **Control plane** | **In code, outside the model process** | **Only a bug in the control plane, or a path that skips it** |

The rows differ in kind, not degree. The first four put the rule somewhere the
model can be argued out of. The last puts it somewhere the model cannot reach.

Violation rates are deliberately absent from this table. Any number you have
seen for these approaches came from one attack suite against one model, and it
does not transfer. If you need a number, build the suite for your system and
publish the suite alongside it.

## When to Use Each

### Use Prompts For:
- Tone and style guidance
- Output formatting preferences
- Domain context and background
- Helpful suggestions and examples

### Use Control Plane For:
- Security boundaries
- Data access restrictions
- Action permissions
- Compliance requirements
- Audit requirements
- Anything that MUST be enforced

## Key Insight

> "You wouldn't secure a web app with strongly-worded comments. Don't secure AI agents with strongly-worded prompts."

Safety is not a suggestion. It is infrastructure.

---

**Related Patterns:**
- [The Mute Agent](./mute-agent.md) - Capability-based execution
- [Grounded context](./patterns/grounded-context.md) - Structure the context, enforce it, keep it current
- [Routing before reasoning](./patterns/routing.md) - Classify the request before answering it
