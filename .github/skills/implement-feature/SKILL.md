---
name: implement-feature
description: Implement a scoped feature safely, from requirements and design through tests and verification. Use when implementing or changing a feature.
---

# Implement a feature

Use this workflow for any non-trivial feature.

1. Read the relevant project rules and source requirements.
2. Locate existing implementation, interfaces, migrations, tests, and conventions before editing.
3. Write down:
   - expected behavior;
   - acceptance criteria;
   - required inputs and outputs;
   - error and missing-data behavior;
   - security/privacy impact;
   - tests to add.
4. Identify unresolved requirements. Ask the developer instead of inventing business behavior.
5. Propose the smallest implementation plan and list expected files to change.
6. Implement one layer at a time. Keep UI, API, domain services, persistence, and agent orchestration separate.
7. Add tests, including boundary and failure cases. Use synthetic data.
8. Run available formatting, linting, type checks, and tests. Do not claim a check passed unless it ran successfully.
9. Review the diff for unrelated edits, secrets, personal data, unsafe logs, broad permissions, and weakened tests.
10. Report:
    - files changed and why;
    - behavior implemented;
    - commands/checks run and exact outcomes;
    - known limitations and unresolved decisions;
    - any manual steps needed.

Do not deploy, publish, reset databases, delete user data, or introduce real employee data as part of this workflow.
