---
applyTo: "**/*test*.py,**/tests/**,**/*.test.ts,**/*.test.tsx,**/*.spec.ts"
---

# Testing requirements

- Every business-rule change must include tests for normal cases, boundaries, invalid inputs, and missing/ambiguous data.
- Test the deterministic calculation engine independently from the LLM and ADK.
- Use synthetic employee data and synthetic documents only.
- Test exact lookup keys, duplicate/missing vehicle matches, stale data, invalid configuration, and import validation.
- Test authorization boundaries: a user must not access another user's conversations, calculations, uploads, or representative requests.
- Test that sensitive values do not appear in logs or client-facing error messages.
- Test agent behavior for tool use, clarification instead of guessing, safe failure, and handoff/resume.
- Prefer fixed expected values and explicit tolerances only when the underlying rule requires them. Do not make tests pass by loosening assertions without explaining why.
- Do not mock the function under test. Mock external boundaries only.
- When a test fails, investigate the root cause. Do not delete or skip a failing test merely to obtain a green run.
- Report exact commands run and observed results. Distinguish tests not run from tests that passed.
