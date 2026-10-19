---
applyTo: "frontend/**/*.ts,frontend/**/*.tsx,frontend/**/*.css,frontend/**/*.html"
---

# Frontend conventions

- Use React 18 functional components and hooks. Use TypeScript; avoid `any` unless narrowly justified and documented.
- The frontend handles presentation, form state, loading/error states, and API communication only. Business rules and financial calculations belong to the backend.
- Communicate with the backend through a centralized typed API client. Do not call internal services or a database from the browser.
- Do not store salary slips, tokens, secrets, or sensitive employee data in localStorage/sessionStorage. Keep sensitive values in memory only when possible and clear them when no longer needed.
- Do not log request bodies, salary values, or uploaded document contents to the browser console.
- Render model-generated text as text, not trusted HTML. Avoid `dangerouslySetInnerHTML`; if ever required, justify and sanitize it.
- Show the user which values were extracted and ask them to confirm before calculations.
- Distinguish confirmed results, incomplete calculations, warnings, and requests waiting for a representative. Never display a provisional value as final.
- Support Hebrew and RTL layout deliberately. Use semantic HTML, keyboard-accessible controls, visible focus, and clear error messages.
- Avoid putting sensitive data in URLs, query strings, analytics, telemetry, or client-side error reports.
- Keep components focused and move reusable API/data logic into typed hooks or service modules.
