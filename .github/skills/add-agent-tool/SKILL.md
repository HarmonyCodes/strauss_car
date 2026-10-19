---
name: add-agent-tool
description: Add a narrow, typed, testable Google ADK tool that delegates to deterministic application services. Use when adding or changing an ADK tool.
---

# Add a Google ADK tool safely

1. Confirm the user-facing capability and its acceptance criteria.
2. Identify the domain/application service that should own the behavior. If none exists, implement and test that service first.
3. Define a narrow typed input/output contract. Validate every argument independently of the LLM.
4. Enforce authorization and data minimization inside the service/tool boundary; never trust the agent prompt as access control.
5. Make the tool deterministic where possible. Do not add arbitrary SQL, unrestricted shell, broad filesystem, or unrestricted network capabilities.
6. Define behavior for missing, ambiguous, stale, invalid, or conflicting inputs. Return an explicit status instead of fabricating a value.
7. Keep side effects explicit. For operations that create a representative request or alter persistent state, ensure idempotency or duplicate protection where appropriate.
8. Return structured results with source/version metadata and warnings, not just a free-form paragraph.
9. Unit-test the domain service and tool adapter separately. Include invalid arguments, unauthorized access, and missing-data tests.
10. Add an agent-level test/evaluation for when the tool should and should not be called.
11. Verify the result is safe to show to the employee and contains no internal errors, secrets, or unnecessary personal data.
12. Report tests run, unresolved business-rule questions, and any persistence/resume implications.
