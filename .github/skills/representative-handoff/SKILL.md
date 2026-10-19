---
name: representative-handoff
description: Implement or review the employee-to-representative handoff, pending status, representative response, and conversation resumption. Use when building or changing escalation workflows.
---

# Representative handoff workflow

Use this workflow whenever changing a handoff, representative queue, or resume behavior.

1. Identify whether the missing item is employee-provided input or an approved business rule/reference/decision. Ask the employee for the former; escalate the latter when it cannot be resolved from an approved source.
2. Define the case state transitions explicitly (for example: collecting input, waiting for representative, ready to calculate, completed, or cancelled). Do not invent statuses if the project already defines them.
3. Design the persisted request/case contract before wiring the UI. Store only the minimum required context.
4. Ensure repeated tool calls or retries do not create duplicate open requests.
5. Enforce representative authorization in the backend for listing, reading, and responding to cases.
6. Validate representative responses, including required fields and effective date where applicable. Never turn an unverified free-text reply into a global business rule.
7. Keep the employee informed in clear Hebrew. While waiting, explicitly state that the final calculation is not yet available; do not show guessed net figures or promise an unapproved turnaround time.
8. Resume from durable persisted state after a response or backend restart. Do not rely only on in-memory ADK session state.
9. Add tests for missing employee data, missing business rules, duplicate escalation, unauthorized access, invalid representative response, successful resume, and restart recovery.
10. Run relevant tests and report exactly what passed, failed, or was not run.
