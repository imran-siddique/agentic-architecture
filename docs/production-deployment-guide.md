# Production Deployment Guide

> **Operational learnings from the Agent-OS and AgentMesh prototypes, both now merged into [microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit)**

> The numbers in this document are worked examples on stated assumptions, or
> design targets. None of them are measurements. See the evidence standard in
> [CONTRIBUTING.md](../CONTRIBUTING.md#evidence-standard).

## Overview

This guide covers production deployment patterns for agentic systems, including CI/CD, observability, and operational best practices.

## Repository Standards

### Essential Files Checklist

Every production agent repository should include:

```
repository/
├── .github/
│   ├── workflows/
│   │   └── ci.yml           # Multi-stage CI pipeline
│   └── dependabot.yml       # Automated dependency updates
├── src/                     # Source code
├── tests/                   # Test suite
├── docs/                    # Documentation
├── examples/                # Working examples
├── CONTRIBUTING.md          # Contribution guidelines
├── SECURITY.md              # Security policy
├── CHANGELOG.md             # Version history
├── LICENSE                  # License file
├── README.md                # Project overview
├── pyproject.toml           # Project configuration
└── .pre-commit-config.yaml  # Code quality hooks
```

### CI Pipeline Stages

A production-ready CI pipeline should include:

```yaml
# 7-stage pipeline (from Agent-OS)
jobs:
  test:      # Unit + integration tests with coverage
  lint:      # Code quality (ruff, mypy)
  security:  # SAST (bandit) + CVE scan (pip-audit)
  benchmark: # Performance regression tests
  build:     # Package build + validation
  publish:   # PyPI release on tags
  demo:      # Example validation
```

### Branch Protection

Enable these protections on `master`/`main`:

- [ ] Require pull request before merging
- [ ] Require at least 1 approval
- [ ] Require status checks to pass
- [ ] Require conversation resolution
- [ ] Do not allow bypassing settings

## Performance Guidelines

### Kernel Creation Benchmark

From Agent-OS: Kernel instantiation should be <50ms

```python
# Benchmark test
iterations = 100
start = time.perf_counter()
for _ in range(iterations):
    kernel = KernelSpace()
elapsed = time.perf_counter() - start

avg_ms = (elapsed / iterations) * 1000
assert avg_ms < 50, f"Kernel creation {avg_ms}ms exceeds 50ms threshold"
```

### Policy Enforcement

- Target: <10ms policy evaluation
- Use deterministic control planes, not LLM inference
- Cache policy decisions where safe

### Memory Footprint

- Minimal core dependencies
- Optional feature bundles
- Lazy loading for heavy modules

## Security Checklist

### Dependency Management

```yaml
# dependabot.yml - Weekly updates, grouped
updates:
  - package-ecosystem: "pip"
    schedule:
      interval: "weekly"
    groups:
      security-updates:
        patterns: ["*"]
        update-types: ["security"]
```

### Security Scanning

Run on every PR:

```bash
# SAST (Static Application Security Testing)
bandit -r src/ -ll

# CVE vulnerability scanning
pip-audit --strict

# Secret detection
detect-secrets scan
```

### Credential Management

- Never commit secrets
- Use environment variables or secret managers
- Rotate credentials regularly
- Prefer short-lived tokens

## Observability

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "agent_action",
    agent_id="did:mesh:my-agent",
    action="data_access",
    resource="customer_database",
    outcome="allowed",
    latency_ms=12,
)
```

### Metrics to Track

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Policy evaluation latency | <10ms | >50ms |
| Trust handshake latency | <100ms | >500ms |
| Credential rotation success | 100% | <99% |
| Audit log write latency | <5ms | >20ms |

### Health Checks

```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "checks": {
            "policy_engine": await policy_engine.health(),
            "credential_store": await cred_store.health(),
            "audit_log": await audit.health(),
        }
    }
```

## Scaling Patterns

### Horizontal Scaling

Agent mesh components scale horizontally:

```
┌─────────────────────────────────────────────────────┐
│                   Load Balancer                      │
├─────────────────────────────────────────────────────┤
│  Policy     │  Policy     │  Policy     │  Policy   │
│  Engine 1   │  Engine 2   │  Engine 3   │  Engine N │
├─────────────────────────────────────────────────────┤
│              Shared State (Redis/etcd)              │
└─────────────────────────────────────────────────────┘
```

### Caching Strategy

```python
# Cache policy decisions (with TTL)
@lru_cache_with_ttl(ttl_seconds=60)
def evaluate_policy(agent_id: str, action: str) -> PolicyDecision:
    return policy_engine.evaluate(agent_id, action)
```

### Circuit Breakers

Prevent cascade failures:

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=30)
async def call_external_service(request):
    return await external_service.call(request)
```

## Deployment Checklist

### Pre-Production

- [ ] All tests passing (including integration)
- [ ] Security scan clean
- [ ] Performance benchmarks within thresholds
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Breaking changes documented

### Production Release

- [ ] Tag with semantic version
- [ ] CI publishes to package registry
- [ ] Monitor error rates post-deploy
- [ ] Have rollback plan ready

### Post-Production

- [ ] Monitor metrics dashboards
- [ ] Review audit logs
- [ ] Collect feedback
- [ ] Plan next iteration

## Troubleshooting

### Common Issues

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| Slow policy evaluation | Complex rules | Simplify or cache |
| Trust handshake timeout | Network/firewall | Check connectivity |
| Credential rotation failure | CA unavailable | Check CA health |
| Audit log gaps | Write failures | Check storage |

### Debug Mode

```python
# Enable verbose logging
import logging
logging.getLogger("agentmesh").setLevel(logging.DEBUG)

# Enable request tracing
os.environ["AGENTMESH_TRACE"] = "1"
```

## Further Reading

- [Agent Governance Toolkit workflows](https://github.com/microsoft/agent-governance-toolkit/tree/main/.github/workflows) - Reference CI implementation
- [Agent Mesh Patterns](./agent-mesh-patterns.md) - Architecture patterns
- [Control Planes vs Prompts](./control-planes-vs-prompts.md) - Safety patterns

---

*Production systems require production practices. These patterns come from real deployments.*
