# Database and Migrations

## Local workflow

1. Configure `DATABASE__URL` in `.env`.
2. Run migrations:

```bash
alembic upgrade head
```

3. Start API:

```bash
uvicorn backend.main:app --reload
```

## Rollback one migration

```bash
alembic downgrade -1
```

