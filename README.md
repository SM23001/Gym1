# Gym1

A **command-line (CLI)** gym management system in Python with **PostgreSQL** persistence. It supports creating trainers, members, and classes; enrolling members while enforcing **capacity** and **schedule conflicts**; recording **attendance**; and listing classes.

**Stack:** Python 3, `psycopg2`, `python-dotenv`, `pytest`.

---

## Table of contents

1. [Prerequisites](#prerequisites)
2. [Quick start](#quick-start)
3. [PostgreSQL setup](#postgresql-setup)
4. [Environment variables](#environment-variables)
5. [Installation](#installation)
6. [Running the application](#running-the-application)
7. [Software architecture model](#software-architecture-model)
8. [Module structure (technical design)](#module-structure-technical-design)
9. [Tests](#tests)
10. [Team roles 3 collaborators](#Team-roles-3-collaborators)  
---

## Prerequisites

- **Python 3** (3.10+ recommended)
- **PostgreSQL** reachable from the machine where the app runs
- The `psql` client or an equivalent tool to create users and databases (optional but useful)

---

## Quick start

1. Clone the repository and change into the project directory.

2. Create and activate a virtual environment, then install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Create the database and user in PostgreSQL (see [PostgreSQL setup](#postgresql-setup)).

4. Add a `.env` file at the project root with the `GYM_DB_*` variables (see [Environment variables](#environment-variables)), or rely on the defaults in `config.py` if they match your environment.

5. Run the CLI:

   ```bash
   python cli.py
   ```

   The first run creates the required tables (`init_schema`).

6. Use the interactive menu to operate the system.

---

## PostgreSQL setup

Example user and database creation:

```sql
CREATE USER gymuser WITH PASSWORD 'gympass';
CREATE DATABASE gymdb OWNER gymuser;
GRANT ALL PRIVILEGES ON DATABASE gymdb TO gymuser;
\q
```

Adjust names and passwords to match your security policy.

---

## Environment variables

You can define them in a `.env` file at the project root (loaded automatically with `python-dotenv`).

| Variable | Description |
|----------|-------------|
| `GYM_DB_HOST` | PostgreSQL server host |
| `GYM_DB_PORT` | Port (numeric) |
| `GYM_DB_NAME` | Database name |
| `GYM_DB_USER` | Username |
| `GYM_DB_PASSWORD` | Password |

**Default values** when variables are unset (see `config.py`):

| Variable | Default |
|----------|---------|
| `GYM_DB_HOST` | `192.168.1.34` |
| `GYM_DB_PORT` | `5432` |
| `GYM_DB_NAME` | `gymdb` |
| `GYM_DB_USER` | `gymuser` |
| `GYM_DB_PASSWORD` | `gympass` |

Example `.env` for local development:

```bash
GYM_DB_HOST=localhost
GYM_DB_PORT=5432
GYM_DB_NAME=gymdb
GYM_DB_USER=gymuser
GYM_DB_PASSWORD=gympass
```

---

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
# On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Main dependencies (`requirements.txt`):

- `psycopg2-binary` — PostgreSQL client
- `python-dotenv` — `.env` loading
- `pytest` — tests

---

## Running the application

```bash
source .venv/bin/activate
python cli.py
```

The menu includes, among other options:

1. Register trainer  
2. Register member  
3. Register class (day, time slot, capacity)  
4. Enroll member in class  
5. Record attendance  
6. List classes  

Business-rule errors are shown as clear messages (`BusinessError`, input validation) without crashing the application.

---

## Software architecture model

**Layered** (N-tier) architecture with the **Repository** pattern and a **service layer**:

| Layer | Module(s) | Responsibility |
|------|-----------|----------------|
| **Presentation** | `cli.py`, `colors.py` | Menu, input, and output. `colors.py` defines ANSI codes and the `c()` helper for colored text. No business logic. |
| **Application / Service** | `service.py` | Use cases, rules (capacity, schedule conflicts, validations), and delegation to the repository. |
| **Domain** | `models.py` | Entities (`Trainer`, `Member`, `GymClass`) as dataclasses; data only. |
| **Data access** | `repository.py` | Repository pattern on PostgreSQL (CRUD and queries). The service does not write SQL. |
| **Infrastructure** | `db.py`, `config.py` | Connection, configuration, and schema creation. |

**Dependency flow:** presentation depends on the service; the service depends on the repository and models; the repository depends on the database and models. That way you can swap the interface (e.g. to a REST API) or the storage engine without rewriting all business logic.

**Patterns:**

- **Repository:** `repository.py` as the persistence facade.  
- **Service layer:** `service.py` holds application logic; the CLI stays thin.

---

## Module structure (technical design)

- **`config.py`** — Database settings via `python-dotenv`. `Settings` class (`db_host`, `db_port`, `db_name`, `db_user`, `db_password`, `dsn` property). `get_settings()` is used from `db.py`.

- **`db.py`** — PostgreSQL connection. `get_connection()` as a context manager (commit/rollback). `init_schema()` creates the `trainers`, `members`, `classes`, `enrollments`, and `attendance` tables if they do not exist. Called when the CLI starts and in tests.

- **`models.py`** — `Trainer`, `Member`, and `GymClass` as `@dataclass` with static typing.

- **`repository.py`** — Persistence: `create_trainer`, `create_member`, `create_class`, `get_*`, `list_classes`, metrics (`count_enrollments`, `is_member_enrolled`, `list_member_classes`), `enroll_member`, `mark_attendance`. Uses `RealDictCursor` to map rows to dataclasses. No business rules.

- **`service.py`** — `BusinessError` exception. High-level functions: create operations with time validation; `enroll_member` (existence, capacity, duplicates, overlap with the member’s other classes); `mark_attendance` only when enrolled; `list_classes`.

- **`cli.py`** — `main()`: `init_schema()`, menu loop, input parsing and service calls; handles `BusinessError` and `ValueError`.

- **`colors.py`** — ANSI constants and `c(text, color)` for terminal messages.

- **`conftest.py`** — Adjusts `sys.path` for pytest from the project root.

- **`tests/`** — Service and persistence tests (see [Tests](#tests)).

---

## Tests

They exercise business logic and the repository against a **real PostgreSQL database** (same configuration as the app unless you override it in `.env`).

### Requirements

- PostgreSQL running with the same settings as the application.
- Dependencies installed (`pytest` is in `requirements.txt`).

### `conftest.py`

Adds the project root to `sys.path` so `db`, `service`, `repository`, etc. import correctly without installing the project as a package.

### Layout

| File | Contents |
|------|----------|
| `tests/test_service.py` | Service: enrollment, capacity, schedules, attendance. |

### Fixtures

- **`clean_db`** (autouse): before each test, `init_schema()` and `TRUNCATE ... RESTART IDENTITY` on `attendance`, `enrollments`, `classes`, `members`, `trainers`.

### Notable cases

| Test | What it checks |
|------|----------------|
| `test_enroll_member_capacity_and_overlap` | Enrollment with capacity; rejection when full; rejection on same-day schedule overlap. |
| `test_mark_attendance_requires_enrollment` | Attendance only after enrollment; row in `attendance` after enrolling. |

### How to run

From the project root with the virtual environment activated:

```bash
pytest
pytest -v
pytest tests/test_service.py
pytest -k "attendance"
```

**Important:** tests run `TRUNCATE` on every case. Do not use a database you need to keep; for a dedicated test DB you can set e.g. `GYM_DB_NAME=gymdb_test` in `.env`.

---
## Team roles 3 collaborators

| Person | Focus | Owns (primary files) | Responsibilities |
|---|---|---|---|
| **A — Core (business + data)** | Service + persistence | `service.py`, `repository.py`, `db.py`, `config.py`, `models.py` | Business rules, SQL queries, schema updates, dataclasses, env variables. |
| **B — UI/CLI** | Presentation layer | `cli.py`, `colors.py` | Menu options, input parsing, output formatting, user messages, catching/displaying `BusinessError`. |
| **C — Quality + Docs** | Tests + documentation | `tests/`, `conftest.py`, `README.md` | Tests/fixtures, CI mindset, onboarding docs, collaboration rules, keeping docs in sync with changes. |

---

## Contributors

Thanks to all the people who have contributed to this project!

| Contributor | GitHub Profile |
|---|---|
| **Fernando Edgardo Saz Márquez** | [@SM23001](https://github.com/SM23001) |
| **VersComp** | [@VersComp](https://github.com/VersComp) |
| **fsaz87** | [@fsaz87](https://github.com/fsaz87) |

