# Agent guide — Gym1

Command-line gym management in Python with PostgreSQL. Entry point: `python cli.py`.

## Database (required)

PostgreSQL runs on **192.168.1.34:5432** (LAN). The app and tests need network access to that host.

1. Copy env template: `cp .env.example .env`
2. Use **`gymdb_test`** for pytest (tests TRUNCATE all tables on every case)
3. Never point pytest at a production database

Create the test database once on the server if needed:

```sql
CREATE DATABASE gymdb_test OWNER gymuser;
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Or: `make setup`

## Verify changes

Always run after code changes:

```bash
make test
# or: .venv/bin/python -m pytest -q
```

Quick connectivity check:

```bash
make check-db
```

## Run the app

```bash
make run
# or: .venv/bin/python cli.py
```

## Architecture (do not violate)

| Layer | Modules | Responsibility |
|-------|---------|----------------|
| Presentation | `cli.py`, `ui.py`, `colors.py` | Menu, input, output. No business logic. |
| Service | `service.py` | Use cases, rules, `BusinessError`. No SQL. |
| Domain | `models.py` | Dataclasses only. |
| Repository | `repository.py` | SQL and persistence. No business rules. |
| Infrastructure | `db.py`, `config.py` | Connection, schema, settings. |

**Dependency flow:** CLI → service → repository → db. Never put SQL in `service.py` or business rules in `repository.py`.

## Adding a feature

Follow this order and match existing patterns:

1. `models.py` — entity if needed
2. `repository.py` — SQL functions
3. `service.py` — validation and business rules
4. `cli.py` / `ui.py` — menu and user messages
5. `tests/test_*_crud.py` or `tests/test_service.py` — copy fixture style from `test_trainer_crud.py`

## Team ownership

| Focus | Primary files |
|-------|---------------|
| Core (business + data) | `service.py`, `repository.py`, `db.py`, `config.py`, `models.py` |
| UI/CLI | `cli.py`, `ui.py`, `colors.py` |
| Quality + docs | `tests/`, `conftest.py`, `README.md`, `AGENTS.md` |

## Constraints

- Never commit `.env` (secrets stay local)
- Tests use real PostgreSQL — no mocks for persistence
- Keep CLI thin: catch `BusinessError` and `ValueError`, delegate to service
- Minimize scope: match existing naming, types, and patterns in each layer
