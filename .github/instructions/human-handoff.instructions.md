---
applyTo: "backend/**/*.py"
---

# Employee clarification and representative handoff

- If a required input is missing and the employee can reasonably provide it, ask one focused question at a time. Preserve previously validated answers and do not ask again unless the value is ambiguous or has become invalid.
- If a required business rule, approved reference value, eligibility decision, or authorized exception is missing, ambiguous, contradictory, or requires human judgment, do not guess. Create or update a durable representative request.
- Before creating a representative request, check whether an equivalent open request already exists for the same conversation/reason so retries do not create duplicates.
- Persist the request, conversation state, reason for escalation, required clarification, status, timestamps, and the minimum context needed for the representative to respond. Avoid copying unnecessary personal data or entire uploaded documents.
- Tell the employee in clear Hebrew that the question requires representative review, that no final calculation is being presented yet, and what happens next. Do not promise a response time unless an approved SLA exists.
- The representative view must show pending requests, the reason for handoff, the minimum relevant context, status, and a way to provide a structured answer. Restrict access server-side to authorized representatives.
- Store the representative's answer, source/justification when applicable, effective date, and identity/audit metadata according to the approved data model. Validate the response before using it in a calculation.
- When the representative responds, resume the saved case from its durable business state. Revalidate the answer and all dependent inputs before calculating or responding to the employee.
- If the representative's answer is incomplete or conflicts with approved rules, keep the case pending and ask for clarification. Do not silently treat a free-text response as a new global policy.
- Keep ADK session/checkpoint state separate from the durable case/request record. The process must survive a backend restart and must not depend only on in-memory agent state.
- Test employee clarification, request creation, duplicate retries, representative authorization, response validation, restart/resume, and safe employee messaging with synthetic data.
