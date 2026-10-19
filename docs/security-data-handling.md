# Security and data-handling baseline

## Current development stage

All employee records, salary values, and documents used for development and demonstrations must be synthetic. Label fixtures as synthetic and do not copy real records into the repository, prompts, logs, screenshots, or tests.

## Before enabling real employee data

This document is a design checklist, not a certification or legal opinion. Obtain the organization's security/privacy approval before introducing real data.

1. **Data inventory and purpose**
   - List every employee field, uploaded document, derived value, database table, log field, and external service that may receive the data.
   - Record the business purpose, access roles, retention period, deletion method, and owner for each category.
   - Minimize fields and avoid identifiers unless they are needed.

2. **AI provider and data flow**
   - Map what is sent to Google ADK's configured model/provider and any other external service.
   - Prefer sending only the minimum structured fields needed for the current turn; do not send the full payslip by default.
   - Verify provider terms, retention, region, access controls, and organizational approval before real data is processed.
   - Do not assume an IDE privacy setting substitutes for application-level data-flow approval.

3. **Access control**
   - Authenticate users before accessing employee-specific data.
   - Enforce authorization server-side for every read/write, including conversation IDs and file IDs.
   - Separate employee and representative permissions. Audit representative access to cases.
   - Use least-privilege service/database credentials.

4. **Storage and encryption**
   - Keep uploads private and outside public/static directories.
   - Define encryption in transit and at rest with the deployment owner.
   - Store secrets in an approved secret manager or protected environment configuration.
   - Define retention and deletion for originals, extracted text, derived salary data, sessions, backups, and logs.

5. **Logging and monitoring**
   - Do not log raw documents, salary values, full prompts, tokens, or connection strings.
   - Log security-relevant events with a correlation ID and minimized metadata.
   - Restrict access to logs and define retention.

6. **Uploads**
   - Enforce size limits and validate actual file content, not just the filename or MIME header.
   - Use generated storage names, bounded parsing, malware scanning where required, and safe error messages.
   - Treat extracted content as untrusted and potentially adversarial.
   - Ask the employee to confirm extracted values before calculation.

7. **Financial correctness**
   - Use approved, versioned rules and source data.
   - Store calculation inputs, source/config versions, status, and a reproducible breakdown, with personal data minimized.
   - If inputs or official source values are missing or ambiguous, stop and ask or hand off; never estimate silently.
   - Obtain approved reference cases and compare outputs before release.

8. **Release gates**
   - Automated tests and dependency/security scans pass.
   - Cross-user authorization tests pass.
   - Upload, logging, secret, prompt-injection, and tool-permission reviews are complete.
   - Backup, recovery, deletion, incident response, and monitoring are defined.
   - A designated security/privacy owner approves the real-data launch.

## Cursor development environment

Enable Cursor Privacy Mode and review the current Cursor/model-provider data handling before working with confidential code. Privacy Mode's training/retention guarantees do not mean prompts and code are never processed by the service. Keep real employee records out of the workspace. `.cursorignore` is only a best-effort context-exclusion control.
