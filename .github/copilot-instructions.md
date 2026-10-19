# Project-wide instructions for GitHub Copilot

# Project mission

Build a Hebrew employee car-advisor for Strauss. The bot should help an employee compare permitted car-related scenarios and explain the result. Correctness, traceability, privacy, and graceful handling of missing information take priority over visual polish.

# Non-negotiable principles

- Do not invent business rules, tax rules, vehicle values, eligibility criteria, or net-salary results.
- Treat challenge documents and explicitly approved configuration as the source of truth. If a requirement is missing, ambiguous, or contradictory, document the gap and ask for clarification; do not silently decide.
- Keep all financial calculations deterministic and implemented in ordinary Python code. The LLM may interpret language, collect information, select approved tools, and explain verified results; it must not calculate or fabricate financial values itself.
- Keep the agent, business services, persistence, and HTTP API separate. Do not put business logic in React components, FastAPI routers, prompts, or tool descriptions.
- Make the smallest coherent change that solves the requested task. Do not rewrite unrelated code or introduce new frameworks/dependencies without explaining the need.
- Before editing, inspect the relevant files and tests. Preserve existing conventions unless there is a clear reason to change them.
- Never claim that code, tests, security checks, or commands passed unless you actually ran them and observed the result.
- If you cannot run a check, state that clearly and provide the exact command the developer should run.
- Prefer explicit types, validated inputs, narrow interfaces, and readable code over clever abstractions.

# Architecture

- Frontend: React 18 + TypeScript + Tailwind CSS. UI only; call the backend through the REST API.
- Backend: Python 3.13 + FastAPI + Pydantic v2 + SQLAlchemy async + PostgreSQL.
- Agent framework: Google ADK, isolated behind an application service/adapter. Keep business logic independent of the LLM provider and ADK where practical.
- Keep API routers thin: validate/deserialize with schemas, call application services, map results to HTTP responses. No direct database access or business calculations in routers.
- Use a layered backend structure: API/router -> application/service -> repository/data access -> database. Keep domain rules in domain/business services.
- Use async I/O for asynchronous database/network operations. Do not make pure CPU-only calculations async merely for appearance.
- Use dependency injection for database sessions and external services. Avoid global mutable state.

# Workflow

For every non-trivial task:
1. Restate the goal and identify relevant requirements/files.
2. Identify assumptions and unresolved questions before implementation.
3. Propose a small plan and list files likely to change.
4. Implement in small, reviewable steps.
5. Add or update tests for the behavior and edge cases.
6. Run relevant formatting, linting, type checks, and tests when available.
7. Summarize changes, verification evidence, unresolved risks, and manual steps.

Do not start a broad refactor or create the entire application in one uncontrolled pass. Ask before destructive operations, schema resets, bulk deletion, or changes that could discard user work.


---

# Security and privacy baseline

Assume the application may eventually process real employee salary and employment data, even though current development fixtures are synthetic.

## Data minimization and handling

- Collect only fields required for the requested scenario. Do not add personal identifiers unless a documented requirement needs them.
- Keep synthetic fixtures obviously synthetic. Never copy real employee records into tests, prompts, screenshots, commits, or documentation.
- Do not put personal data, salary documents, access tokens, API keys, passwords, database URLs, or other secrets in source code, prompts, logs, screenshots, seed files, or committed configuration.
- Read secrets from environment/configuration providers. Commit `.env.example` with placeholders only; never commit `.env`.
- Do not send uploaded document contents, salary details, or unnecessary identifiers to an LLM. Prefer deterministic parsing and structured, minimized fields. Any LLM use involving employee data requires an explicit data-flow and provider-retention review first.
- Treat AI-tool file exclusions as best-effort context controls, not a security boundary. Keep real data outside the repository and outside AI workspaces whenever possible.
- Before introducing real confidential employee data, verify the selected AI provider, model, account settings, data-retention terms, and organization policies.

## Authentication, authorization, and API

- Do not implement placeholder authentication that looks production-ready. Clearly mark demo-only behavior.
- Enforce authorization on the server for every protected operation; never rely on hidden UI controls.
- Apply least privilege and deny by default. Employee endpoints must not allow one employee to read another employee's conversation, uploaded document, calculation, or representative request.
- Validate all request data with Pydantic and explicit domain validation. Apply request size limits, timeouts, rate limits where appropriate, and safe error responses.
- Use parameterized ORM queries; never concatenate untrusted input into SQL or shell commands.
- Configure CORS narrowly for known frontend origins. Do not use wildcard origins with credentials.
- Do not expose stack traces, SQL errors, environment variables, internal prompts, or secret-bearing configuration in API responses.
- Do not add cryptography, authentication, session management, or authorization algorithms from scratch when established libraries and framework mechanisms are available.

## Uploads and document parsing

- Treat every uploaded file and its contents as untrusted input, including PDFs, CSVs, filenames, MIME types, and extracted text.
- Enforce file-size limits, extension/content validation, safe generated storage names, and bounded parsing. Do not execute uploaded files or follow embedded instructions.
- Keep uploads outside the public web root; do not persist files longer than necessary. Define retention/deletion behavior before real documents are enabled.
- Treat OCR/text extraction as unverified. Show extracted fields for user confirmation and never infer missing salary values.
- Never let document text or retrieved content override system instructions, security rules, or approved business rules (prompt-injection defense).

## Logging and errors

- Never log raw salary slips, contract text, access tokens, passwords, database connection strings, or full prompts containing employee data.
- Prefer structured events with a correlation ID, operation name, status, and minimized non-sensitive metadata.
- Redact or omit sensitive values before logging. Do not return internal exception text to clients.
- Record security-relevant events without storing more personal data than needed.

## Agent and tools

- The LLM is not an authorization boundary and is not a source of truth.
- Tool functions must validate arguments and check authorization independently of the agent's instructions.
- Expose narrow, typed tools. Do not give the agent arbitrary SQL, unrestricted filesystem access, arbitrary shell execution, or unrestricted network access.
- Treat model output as untrusted input. Validate tool arguments and validate/serialize tool results before displaying or persisting them.
- Never allow the agent to mark an unsupported calculation as final. Missing, stale, conflicting, or ambiguous inputs must produce a clarification or human handoff.
- Keep business calculation code independent from prompts and model-provider-specific APIs.

## Changes to security-sensitive behavior

Before changing authentication, authorization, file handling, logging, secrets, data retention, CORS, network access, or agent tool permissions:
1. Explain the threat and intended control.
2. Add or update tests.
3. Prefer fail-closed behavior for access-control decisions.
4. Report remaining limitations. Do not claim regulatory compliance or production readiness based only on code review.
