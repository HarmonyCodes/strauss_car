---
name: security-review
description: Review a change for privacy, access control, injection, unsafe uploads, logging, and agent-tool risks. Use when handling sensitive data, authentication, authorization, uploads, external AI calls, or before a release.
---

# Security review workflow

Review the requested files and their callers, data stores, configuration, tests, and relevant diffs.

Check at least:

- Authentication and server-side authorization on every sensitive path.
- Cross-user access to conversations, calculations, files, and representative requests.
- Input validation, SQL injection, command injection, XSS, path traversal, unsafe deserialization, and excessive resource use.
- File upload size/type limits, safe storage, parsing limits, retention, and deletion behavior.
- Secret handling, `.env`/`.gitignore`, and accidental exposure in responses, logs, fixtures, or screenshots.
- Data minimization before sending anything to an LLM or external provider.
- Prompt injection from user messages, uploaded documents, retrieved content, and tool output.
- Agent tool permissions, argument validation, side effects, and authorization independent of the model.
- Unsafe CORS, missing timeouts, overly broad network access, and insecure defaults.
- Financial determinism, stale/missing data handling, and unsupported claims of a final result.
- Tests that demonstrate the controls and failure behavior.

Output findings by severity (Critical, High, Medium, Low), with file/line evidence, realistic impact, and a concrete remediation. Distinguish confirmed findings from questions that require product or infrastructure context.

Do not claim a full penetration test, compliance certification, or production readiness from a source review alone. Do not make code changes unless explicitly asked; this skill is primarily a review workflow.
