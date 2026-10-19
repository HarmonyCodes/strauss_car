---
applyTo: "backend/**/*.py"
---

# Backend conventions

- Use Python 3.13, type hints for public functions and domain models, and Pydantic v2 for API boundaries.
- Use SQLAlchemy 2.x typed mappings and async sessions for database I/O.
- Keep routers thin. Routers must not contain business calculations, direct SQL, or multi-step orchestration.
- Keep domain/business services independent from FastAPI request objects and HTTP status codes.
- Keep repository/data-access code responsible for database queries, not business policy.
- Use explicit transaction boundaries. Roll back on failure and avoid committing from low-level helper functions.
- Do not share one AsyncSession concurrently across independent tasks.
- Avoid blocking I/O in async endpoints. Use an appropriate async client or move CPU/blocking work to a controlled worker.
- Validate external data at ingestion boundaries. Preserve source identifiers as strings when leading zeros or exact codes matter.
- Use UTC-aware timestamps internally and document timezone conversion at API/UI boundaries.
- Use stable domain exceptions and map them to safe HTTP responses in one place.
- Use configuration via a typed settings module. Fail startup for missing required production settings; do not silently fall back to insecure defaults.
- Never use `Base.metadata.drop_all()` or destructive database resets as an ordinary development shortcut.
- Use Alembic migrations for schema changes; never silently edit an already-applied migration.
- Keep monetary values in `Decimal` or integer minor units according to a documented convention. Do not use binary floating point for money.
- Make rounding rules explicit, centralized, documented, and tested. Do not round at arbitrary intermediate steps.
- Keep vehicle-catalog ingestion separate from runtime lookup. Validate source schema, row counts, duplicate keys, encoding, and import errors.
- Queries for vehicle-use values must use the full approved composite key from the source requirements; never match only by commercial model name.
- Write pytest tests for services and repositories. Use synthetic fixtures only.
