# Security Policy

## What this repository is

This repository publishes architectural patterns and reference examples. The
code under `examples/` exists to make a pattern inspectable in a single file
with no dependencies. It is not a library, it is not published to any package
index, and it is not intended to be deployed.

Several examples deliberately use the simplest primitive that demonstrates the
idea rather than the primitive you should ship. `examples/evidence_plane_example.py`
signs receipts with HMAC, which means the issuer and the verifier share the
ability to sign. That is stated in `docs/patterns/enforcement-and-evidence.md` and is a teaching
choice, not a defect.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting on this repository:
**Security** tab, then **Report a vulnerability**. Do not open a public issue
for a suspected vulnerability.

Reports that are in scope:

- An example that would mislead a reader into an insecure design, where the
  document does not already name the limitation.
- A threat model in `docs/` that omits a control a reader would reasonably
  need, or claims a property the pattern does not provide.
- A supply-chain issue in the GitHub Actions workflows.

Reports that are out of scope:

- "This example is not production ready." That is the stated intent. If the
  gap is not documented, that is a documentation issue, and it is in scope
  under the first bullet.
- Findings from a scanner with no accompanying analysis of impact in the
  context of this repository.

## Response

Expect an initial response within seven days. Fixes ship as a normal pull
request with the reasoning in the description, since there is nothing here to
patch downstream.
