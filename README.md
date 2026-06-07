# Gym1

A **command-line (CLI)** gym management system in Python with **PostgreSQL** persistence. It supports creating trainers, members, and classes; enrolling members while enforcing **capacity** and **schedule conflicts**; recording **attendance**; and listing classes.

**Stack:** Python 3, `psycopg2`, `python-dotenv`, `pytest`.

---

## Table of contents

1. [Prerequisites](#prerequisites)
2. [Quick start](#quick-start)
3. [PostgreSQL setup](#postgresql-setup)
4. [Environment variables](#environment-variables)
5. [Makefile](#makefile)
6. [Installation](#installation)
7. [Running the application](#running-the-application)
8. [Data seeding](#data-seeding)
9. [Software architecture model](#software-architecture-model)
10. [Module structure (technical design)](#module-structure-technical-design)
11. [Application authentication (planned)](#application-authentication-planned)
12. [Tests](#tests)
13. [Agent development](#agent-development)
14. [Team roles 3 collaborators](#Team-roles-3-collaborators)  
---

## Prerequisites

- **Python 3** (3.10+ recommended)
- **PostgreSQL** reachable from the machine where the app runs
- The `psql` client or an equivalent tool to create users and databases (optional but useful)

---

## Quick start

1. Clone the repository and change into the project directory.

2. Create a virtual environment and install dependencies:

   ```bash
   make setup
   ```

   Or manually:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Create the database and user in PostgreSQL (see [PostgreSQL setup](#postgresql-setup)).

4. Copy the environment template and adjust if needed:

   ```bash
   cp .env.example .env
   ```

   See [Environment variables](#environment-variables). Defaults in `config.py` apply when `.env` is missing.

5. Run the CLI:

   ```bash
   make run
   ```

   Or with the virtual environment activated:

   ```bash
   python cli.py
   ```

   The first run creates the required tables (`init_schema`).

6. *(Optional)* Load demo data — set `GYM_DB_NAME=gymdb` in `.env`, then run `make seed` (see [Data seeding](#data-seeding)).

7. Use the interactive menu to operate the system.

---

## PostgreSQL setup

Example user and database creation:

```sql
CREATE USER gymuser WITH PASSWORD 'gympass';
CREATE DATABASE gymdb OWNER gymuser;
GRANT ALL PRIVILEGES ON DATABASE gymdb TO gymuser;
\q
```

For **pytest**, use a separate database so `TRUNCATE` never touches production data:

```sql
CREATE DATABASE gymdb_test OWNER gymuser;
```

Then set `GYM_DB_NAME=gymdb_test` in `.env` (see [`.env.example`](.env.example)).

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

Example `.env` for local development (LAN server at `192.168.1.34`):

```bash
GYM_DB_HOST=192.168.1.34
GYM_DB_PORT=5432
GYM_DB_NAME=gymdb
GYM_DB_USER=gymuser
GYM_DB_PASSWORD=gympass
```

A template is committed as [`.env.example`](.env.example) (uses `gymdb_test` for safe testing).

---

## Makefile

Short commands from the project root (defined in [`Makefile`](Makefile)). They use `.venv/bin/python` so you do not need to activate the virtual environment first.

| Command | Action |
|---------|--------|
| `make setup` | Create `.venv` and `pip install -r requirements.txt` |
| `make test` | Run the full pytest suite (`pytest -q`) |
| `make run` | Start the CLI |
| `make check-db` | Verify PostgreSQL connectivity (`DB OK` or connection error) |
| `make seed` | Load demo data into the database (`seed.py --reset`) |

Requires `make` on your system (`sudo apt install make` on Debian/Ubuntu if missing).

---

## Installation

```bash
make setup
```

Or manually:

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

From the project root (no need to activate the virtual environment first):

```bash
make run
```

Or manually:

```bash
source .venv/bin/activate
python cli.py
```

The main menu:

1. **Trainers** — add, list, view profile, update, delete, list classes by trainer  
2. **Members** — member CRUD and related lists  
3. **Classes** — class CRUD (day, time slot, capacity, trainer)  
4. **Enrollment** — enroll / unenroll members in classes  
5. **Attendance** — record and manage attendance  

Business-rule errors are shown as clear messages (`BusinessError`, input validation) without crashing the application.

### Trainer profile

Trainers have a full profile (not just a name). Fields are collected in the **Trainers** submenu and stored in PostgreSQL.

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Trainer’s full name |
| `email` | Yes | Unique contact email (validated) |
| `phone` | Yes | Phone number (min. 7 digits) |
| `specialty` | Yes | Main discipline (e.g. Yoga, CrossFit) |
| `bio` | No | Short biography / background text |
| `years_experience` | No | Integer ≥ 0 if provided |

**CLI:** option **1** prompts all fields; option **3** shows the full profile; option **2** lists ID, name, specialty, and email.

**Layers:** `models.Trainer` → `repository` (SQL) → `service` (validation, duplicate email) → `cli.py` (`prompt_trainer_fields`, `show_trainer_profile`).

Existing databases on the server get new columns via migrations in `init_schema()` (backfill for old trainer rows).

> **Note:** Application-level staff login is **not implemented yet**. See [Application authentication (planned)](#application-authentication-planned) for the recommended design (local username/password, roles, and why OAuth is deferred).

---

## Data seeding

Use [`seed.py`](seed.py) to populate the database with **demo data** for local development and demos. All inserts go through the **service layer** (same validation rules as the CLI).

### What gets created

| Entity | Count | Examples |
|--------|-------|----------|
| Trainers | 3 | Ana Ruiz (Spinning), Carlos Vega (Yoga), Laura Méndez (CrossFit) |
| Members | 4 | Juan Pérez, María López, Pedro Sánchez, Sofía Torres |
| Classes | 4 | Spinning, Yoga, CrossFit, Evening Spin |
| Enrollments | 7 | Members assigned to classes (capacity and schedule rules enforced) |
| Attendance | 3 | Sample attendance for enrolled members |

### Requirements

- PostgreSQL reachable with `GYM_DB_*` configured in [`.env`](.env.example).
- Use **`GYM_DB_NAME=gymdb`** for seeding — the script **refuses `gymdb_test`** (reserved for pytest, which truncates tables on every test).

### Commands

From the project root:

```bash
make seed
```

Or directly:

```bash
.venv/bin/python seed.py --reset
```

| Flag / behavior | Description |
|-----------------|-------------|
| `--reset` | `TRUNCATE` all gym tables, then insert demo data (what `make seed` runs) |
| No flag, DB empty | Seeds demo data |
| No flag, data exists | Prints a message and exits without changes; use `--reset` to replace |

After seeding, run `make run` and use the menus — lists should show trainers, members, classes, enrollments, and attendance.

Tests for seeding live in [`tests/test_seed.py`](tests/test_seed.py) (calls `seed_data()` against `gymdb_test` after truncate; does not run the CLI entry point).

---

## Software architecture model

**Layered** (N-tier) architecture with the **Repository** pattern and a **service layer**:

| Layer | Module(s) | Responsibility |
|------|-----------|----------------|
| **Presentation** | `cli.py`, `ui.py`, `colors.py` | Menu, input, and output. `ui.py` holds shared display helpers; `colors.py` defines ANSI codes and `c()`. No business logic. |
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

- **`db.py`** — PostgreSQL connection. `get_connection()` as a context manager (commit/rollback). `init_schema()` creates the `trainers`, `members`, `classes`, `enrollments`, and `attendance` tables if they do not exist, and runs `ALTER TABLE` migrations (e.g. trainer profile columns on existing DBs). Called when the CLI starts and in tests.

- **`models.py`** — `Trainer` (name, email, phone, specialty, bio, years_experience), `Member`, and `GymClass` as `@dataclass` with static typing.

- **`repository.py`** — Persistence: `create_trainer`, `create_member`, `create_class`, `get_*`, `list_classes`, metrics (`count_enrollments`, `is_member_enrolled`, `list_member_classes`), `enroll_member`, `mark_attendance`. Uses `RealDictCursor` to map rows to dataclasses. No business rules.

- **`service.py`** — `BusinessError` exception. Trainer profile validation (email, phone, specialty, years_experience). High-level functions: create operations with time validation; `enroll_member` (existence, capacity, duplicates, overlap with the member’s other classes); `mark_attendance` only when enrolled; `list_classes`.

- **`cli.py`** — `main()`: `init_schema()`, menu loop, input parsing and service calls; handles `BusinessError` and `ValueError`. Trainer flows use `prompt_trainer_fields()` and `show_trainer_profile()`.

- **`ui.py`** — Shared terminal UI helpers (banner, tables, prompts) used by `cli.py`.

- **`colors.py`** — ANSI constants and `c(text, color)` for terminal messages.

- **`conftest.py`** — Adds project root to `sys.path` for pytest. Provides `create_test_trainer()` (and `create_test_member()`) helpers with auto-generated unique emails for tests.

- **`tests/`** — Service and persistence tests (see [Tests](#tests)).

---

## Application authentication (planned)

The CLI currently has **no application-level authentication**: anyone who can run `python cli.py` and reach PostgreSQL can use every menu option. The `GYM_DB_*` variables are **database** credentials only—they do not identify gym staff.

This section documents the **recommended approach** for adding staff authentication, based on architectural review of this project (CLI scope, layered design, and team workflow). Implementation is planned; details below are the target design.

### App users vs gym members

| Concept | Purpose | Status |
|---------|---------|--------|
| **App user (staff/admin)** | Operates the system (registers trainers, enrolls members, records attendance) | **Planned** — new `app_users` table |
| **Gym member** | Takes classes; already modeled as `Member` in `models.py` | **Exists** — not the same as login accounts in v1 |

Do not merge staff accounts and gym members in the first version. Member self-service login (e.g. “my classes”) is a separate feature for later.

### Recommended approach: local login with hashed passwords

For this CLI gym admin tool, the best fit is **username + password** stored in PostgreSQL with **bcrypt** (or **argon2-cffi**) hashing—not OAuth, JWT, or SSO.

| Approach | Fit for Gym1 |
|----------|----------------|
| **Local auth (recommended)** | Login at CLI startup; simple; matches layered architecture; easy to test with pytest |
| **OAuth / OIDC** | Better when you add a web UI, REST API, or corporate SSO—not the default for a local CLI |
| **JWT sessions** | Useful once there is an HTTP API; unnecessary for a single in-memory `current_user` after CLI login |

**Why not OAuth here?** OAuth is designed for delegated access via an identity provider (Google, Microsoft, etc.) over browser redirects and tokens. A local CLI can use OAuth (device flow or PKCE), but it adds client registration, token storage, and IdP dependency without much benefit for a single-gym staff tool. If the project later exposes a **web API** or needs **SSO**, add **OpenID Connect** at that layer and map IdP identity to `app_users`.

### Target schema

```sql
CREATE TABLE IF NOT EXISTS app_users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'staff',  -- e.g. 'admin' | 'staff'
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Add an `AppUser` dataclass in `models.py` (id, username, role, active—**never** return plain passwords from the repository).

### Layer placement

Follow the existing dependency flow: **CLI → service → repository → database**.

| Layer | Module | Responsibility |
|-------|--------|------------------|
| **Infrastructure** | `db.py` | Add `app_users` to `init_schema()` |
| **Domain** | `models.py` | `AppUser` dataclass |
| **Data access** | `repository.py` | `create_app_user`, `get_app_user_by_username`, etc. |
| **Service** | `service.py` | `authenticate()`, optional `register_app_user()`, `require_role()` |
| **Presentation** | `cli.py` | Login loop before the main menu; pass `current_user` into service calls |

Password comparison and hashing live in the **service** layer (or a small dedicated module called from service). The repository returns stored hashes; it does not implement bcrypt details.

### User flow (planned)

1. `init_schema()` (as today).
2. Prompt for username and password (`getpass` for masked input).
3. Call `service.authenticate()`; on failure, show a **generic** message (“Invalid username or password”) and retry or exit.
4. On success, keep `current_user` in memory and show the main menu.
5. Optional: **Logout** clears `current_user` and returns to login.

### Roles and authorization

- **Authentication** — who you are (login).
- **Authorization** — what you may do (roles).

Suggested roles:

| Role | Access |
|------|--------|
| **`admin`** | Full CRUD plus user management |
| **`staff`** | Day-to-day operations (enroll, attendance, lists); optional blocks on destructive deletes |

Enforce roles in **`service.py`** (e.g. `require_role(actor, "admin")` at the start of sensitive functions), not only by hiding menu items in the CLI. That keeps authorization testable without running the full menu.

### Security basics

- Hash passwords with **bcrypt** or **argon2-cffi**—never plaintext, never plain SHA256/MD5.
- Use **`getpass`** for password input in the terminal.
- Use the same error message for unknown user and wrong password.
- Use an **`active`** flag to disable accounts without deleting rows.
- Do not confuse **`GYM_DB_USER` / `GYM_DB_PASSWORD`** (PostgreSQL connection) with application staff accounts.

### Bootstrap: first admin

Before anyone can log in, create one admin user via one of:

1. One-time SQL insert with a precomputed bcrypt hash.
2. A manual **`seed_admin.py`** script run once after deploy.
3. First-run prompt when `app_users` is empty: “Create admin account?”

Document the chosen method here when implemented. Do not commit real passwords to the repository.

### Dependencies (when implemented)

Add to `requirements.txt`:

```text
bcrypt>=4.0,<5.0
```

(or `argon2-cffi` as an alternative).

### Testing (when implemented)

- Extend the autouse **`clean_db`** fixture to `TRUNCATE app_users` (respect FK order if added later).
- Add tests for: successful login, wrong password, inactive user, duplicate username, role checks on protected operations.
- Keep auth logic in the service layer so tests call `authenticate()` directly without the CLI.
- Run the full suite after changes: `make test`

### Future evolution

| Change | Auth evolution |
|--------|----------------|
| **REST API** (FastAPI/Flask) | Session cookies or JWT after the same `authenticate()`; or OIDC at the API |
| **Web UI** | Reuse the same service auth; add a browser login page |
| **Corporate SSO** | OIDC in front of the API; map IdP `sub` / email to `app_users` |
| **Member portal** | Separate credentials or link to `members`; still not OAuth by default |

Design **`authenticate(username, password) -> AppUser`** in the service layer so the identity source can change later without rewriting enrollment or attendance logic.

### Suggested work split

| Person | Tasks |
|--------|--------|
| **A — Core** | Schema, `AppUser` model, repository methods, `authenticate` / hashing / role checks in service |
| **B — UI/CLI** | Login screen, logout, wire `current_user`; hide admin-only menu options by role |
| **C — Quality + Docs** | Auth tests, `clean_db` updates, bootstrap docs, keep this section in sync with code |

---

## Tests

They exercise business logic and the repository against a **real PostgreSQL database** (same configuration as the app unless you override it in `.env`).

### Requirements

- PostgreSQL running with the same settings as the application.
- Dependencies installed (`pytest` is in `requirements.txt`).

### `conftest.py`

Adds the project root to `sys.path` so `db`, `service`, `repository`, etc. import correctly without installing the project as a package.

Use **`create_test_trainer()`** in tests instead of calling `service.create_trainer()` directly — it supplies unique emails and default phone/specialty. Example:

```python
from conftest import create_test_trainer

trainer = create_test_trainer("Ana", email="ana@gym.com")
```

### Layout

| File | Contents |
|------|----------|
| `tests/test_service.py` | Service: enrollment, capacity, schedules, attendance. |
| `tests/test_trainer_crud.py` | Trainer CRUD and profile validation (email, phone, specialty, bio, experience). |
| `tests/test_member_crud.py` | Member CRUD: create, read, list, update, delete, and cascade on delete. |
| `tests/test_class_crud.py` | Class CRUD: create, read, list, update, delete, field validation, and capacity rules. |
| `tests/test_enrollment_crud.py` | Enrollment list, `is_enrolled`, `unenroll_member`. |
| `tests/test_attendance_crud.py` | Attendance CRUD and listing by class/member. |

### Fixtures

- **`clean_db`** (autouse): before each test, `init_schema()` and `TRUNCATE ... RESTART IDENTITY` on `attendance`, `enrollments`, `classes`, `members`, `trainers`. Defined in each test file.

### Notable cases

#### `tests/test_service.py`

| Test | What it checks |
|------|----------------|
| `test_enroll_member_capacity_and_overlap` | Enrollment with capacity; rejection when full; rejection on same-day schedule overlap. |
| `test_mark_attendance_requires_enrollment` | Attendance only after enrollment; row in `attendance` after enrolling. |

#### `tests/test_trainer_crud.py`

| Test | What it checks |
|------|----------------|
| `test_create_trainer` | Successful trainer creation with full profile. |
| `test_create_trainer_empty_name` | Rejects blank or whitespace-only names. |
| `test_create_trainer_invalid_email` | Rejects malformed email. |
| `test_create_trainer_invalid_phone` | Rejects phone with too few digits. |
| `test_create_trainer_empty_specialty` | Rejects blank specialty. |
| `test_create_trainer_duplicate_email` | Rejects duplicate email on create. |
| `test_create_trainer_negative_experience` | Rejects negative `years_experience`. |
| `test_get_trainer` / `test_get_trainer_not_found` | Read by id; returns `None` when missing. |
| `test_list_trainers` | Lists all trainers in order. |
| `test_update_trainer` | Updates profile fields while keeping the same id. |
| `test_update_trainer_not_found` / `test_update_trainer_empty_name` | Update errors for missing trainer and empty name. |
| `test_update_trainer_duplicate_email` | Rejects email already used by another trainer. |
| `test_delete_trainer` | Deletes an existing trainer. |
| `test_delete_trainer_not_found` | Delete error when trainer does not exist. |
| `test_list_classes_by_trainer` | Lists classes assigned to a trainer. |
| `test_delete_trainer_with_classes` | Blocks delete when the trainer still has assigned classes. |

#### `tests/test_member_crud.py`

| Test | What it checks |
|------|----------------|
| `test_create_member` | Successful member creation. |
| `test_create_member_empty_name` | Rejects blank or whitespace-only names. |
| `test_get_member` / `test_get_member_not_found` | Read by id; returns `None` when missing. |
| `test_list_members` | Lists all members in order. |
| `test_update_member` | Updates name while keeping the same id. |
| `test_update_member_not_found` / `test_update_member_empty_name` | Update errors for missing member and empty name. |
| `test_delete_member` | Deletes an existing member. |
| `test_delete_member_not_found` | Delete error when member does not exist. |
| `test_delete_member_cascades_enrollments` | Deleting a member removes related enrollment rows (`ON DELETE CASCADE`). |

#### `tests/test_class_crud.py`

| Test | What it checks |
|------|----------------|
| `test_create_class` | Successful class creation. |
| `test_create_class_empty_name` | Rejects blank or whitespace-only names. |
| `test_create_class_invalid_trainer` | Rejects creation when the trainer does not exist. |
| `test_create_class_invalid_time` | Rejects end time before or equal to start time. |
| `test_get_class` / `test_get_class_not_found` | Read by id; returns `None` when missing. |
| `test_list_classes` | Lists all classes in order. |
| `test_update_class` | Updates all class fields (name, trainer, schedule, capacity). |
| `test_update_class_not_found` | Update error when class does not exist. |
| `test_update_class_capacity_below_enrollments` | Blocks lowering capacity below current enrollment count. |
| `test_delete_class` | Deletes an existing class. |
| `test_delete_class_not_found` | Delete error when class does not exist. |
| `test_delete_class_cascades_enrollments` | Deleting a class removes related enrollment rows (`ON DELETE CASCADE`). |

### How to run

From the project root, run the full suite:

```bash
make test
```

Other examples (with the virtual environment active, or use `.venv/bin/python -m pytest`):

```bash
pytest
pytest -v
pytest tests/test_service.py
pytest tests/test_trainer_crud.py
pytest tests/test_member_crud.py
pytest tests/test_class_crud.py
pytest -k "attendance"
pytest -k "crud"
```

Or run a specific file with the virtual environment Python directly (no need to activate first):

```bash
.venv/bin/python -m pytest tests/test_class_crud.py -v
```
```bash
pytest tests/test_trainer_crud.py::test_list_classes_by_trainer -q
```
```bash
python3 -m pytest tests/test_member_crud.py::test_list_member_classes -q
```
```bash
.venv/bin/python -m pytest tests/test_enrollment_crud.py -v
```

```bash
pytest tests/test_attendance_crud.py -q
```


**Important:** tests run `TRUNCATE` on every case. Do not use a database you need to keep. Prefer `GYM_DB_NAME=gymdb_test` in `.env` and create that database on the server (see [PostgreSQL setup](#postgresql-setup)). If `gymdb_test` does not exist, tests fail with a connection error — use `GYM_DB_NAME=gymdb` only when that is safe for your environment.

---

## Agent development

This project includes scaffolding for [Cursor](https://cursor.com) and other AI coding agents.

**Start here:** [`AGENTS.md`](AGENTS.md) — setup, architecture layers, feature workflow, and constraints.

**Environment template:** copy [`.env.example`](.env.example) to `.env` and adjust `GYM_DB_*` if needed. The example uses `gymdb_test` on PostgreSQL at `192.168.1.34`.

**Makefile shortcuts** (from the project root):

| Command | Action |
|---------|--------|
| `make setup` | Create `.venv` and install dependencies |
| `make test` | Run the full pytest suite |
| `make run` | Start the CLI (`python cli.py`) |
| `make check-db` | Verify PostgreSQL connectivity |
| `make seed` | Load demo data (`seed.py --reset`; use `gymdb`, not `gymdb_test`) |

**Cursor rules** in [`.cursor/rules/`](.cursor/rules/) give the agent persistent context about architecture and test conventions.

**Adding a feature (layer order):** `models.py` → `repository.py` → `service.py` → `cli.py` / `ui.py` → `tests/`. Example: trainer profile fields follow this path; see [Trainer profile](#trainer-profile).

Example prompt when working with an agent:

> Add [feature]. Follow AGENTS.md layer boundaries. Run `make test` when done.

---
## Team roles 3 collaborators

| Person | Focus | Owns (primary files) | Responsibilities |
|---|---|---|---|
| **A — Core (business + data)** | Service + persistence | `service.py`, `repository.py`, `db.py`, `config.py`, `models.py` | Business rules, SQL queries, schema updates, dataclasses, env variables. |
| **B — UI/CLI** | Presentation layer | `cli.py`, `colors.py` | Menu options, input parsing, output formatting, user messages, catching/displaying `BusinessError`. |
| **C — Quality + Docs** | Tests + documentation | `tests/`, `conftest.py`, `README.md`, `AGENTS.md` | Tests/fixtures, CI mindset, onboarding docs, agent guide, collaboration rules, keeping docs in sync with changes. |

