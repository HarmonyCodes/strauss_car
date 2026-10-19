# Deployment options for the hackathon

## Practical starting point

- React frontend: Vercel.
- FastAPI + Google ADK backend: a Python-friendly service/runtime that supports the required request duration, streaming if needed, environment secrets, and restart behavior.
- PostgreSQL: a managed hosted PostgreSQL provider such as Neon or Supabase.

Vercel currently documents a Python runtime that can run FastAPI, but the runtime is documented as Beta. Evaluate request duration, streaming, deployment behavior, and ADK session/resume requirements before deciding to host the backend there.

## PostgreSQL

PostgreSQL remains a reasonable choice because the application has structured relationships between conversations, employee scenarios, calculations, and representative requests. The frontend must never connect directly to the database.

Vercel Postgres as a first-party product is no longer available for new projects. Vercel supports external database integrations through its Marketplace, including Neon and Supabase. Check current pricing, quotas, region, backups, and provider terms before selecting a plan.

## Environment and security

- Configure `DATABASE_URL` and model-provider credentials in the hosting platform's environment/secrets settings, not in source code.
- Use separate development/demo and production databases.
- Use least-privilege database credentials and TLS.
- For serverless traffic, use the database provider's recommended pooled connection string and keep a direct connection string for migrations/admin tasks where required.
- Never seed the hosted demo with real employee salary records.
- Define data retention and deletion for conversation data and representative cases.
