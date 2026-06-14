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
11. [Application authentication](#application-authentication)
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
- `bcrypt` — password hashing for app users

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

> **Note:** The CLI requires **login** before use. On first run (empty `app_users` table), you are prompted to create an administrator. After `make seed`, demo accounts are available — see [Application authentication](#application-authentication).

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

## Application authentication

The CLI uses **local username/password** authentication with **bcrypt** hashes stored in PostgreSQL. Login is required before any menu appears. The `GYM_DB_*` variables are **database** credentials only—they are not app login accounts.

### Roles

| Role | Profile link | Access |
|------|--------------|--------|
| **`admin`** | None | Full CRUD, enrollment, attendance, user management |
| **`trainer`** | `trainers.id` | Own classes, rosters, attendance for those classes |
| **`member`** | `members.id` | Own classes, own attendance, self enroll/unenroll |

App login accounts (`app_users`) are separate from gym **profiles** (`trainers`, `members`). A trainer or member account must link to an existing profile row.

### First run

1. `make run` → `init_schema()` creates `app_users` if missing.
2. If no users exist, the CLI prompts for the **first administrator** (username + password).
3. Sign in and use the menu for your role.

### Demo accounts (`make seed`)

After seeding demo data (`GYM_DB_NAME=gymdb`, then `make seed`):

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | admin |
| `ana.trainer` | `trainer123` | trainer (linked to Ana Ruiz) |
| `juan.member` | `member123` | member (linked to Juan Pérez) |

Do not use these passwords in production.

### Schema

```sql
CREATE TABLE IF NOT EXISTS app_users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'trainer', 'member')),
    trainer_id INTEGER REFERENCES trainers(id) ON DELETE SET NULL,
    member_id INTEGER REFERENCES members(id) ON DELETE SET NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Layer placement

| Layer | Module | Responsibility |
|-------|--------|------------------|
| **Infrastructure** | `db.py` | `app_users` in `init_schema()` |
| **Domain** | `models.py` | `UserRole`, `AppUser` |
| **Data access** | `repository.py` | User CRUD and lookup |
| **Service** | `service.py` | `authenticate()`, `register_app_user()`, role checks |
| **Presentation** | `cli.py` | Login, bootstrap admin, role-based menus |

Authorization for enrollment and attendance is enforced in **`service.py`** when an `actor` is passed (trainer/member portals). Admin menus are gated by role at the CLI; seed and tests call service functions without `actor` where appropriate.

### Security

- Passwords hashed with **bcrypt** (`requirements.txt`).
- Terminal input via **`getpass`** (no echo).
- Generic error on failed login: `Usuario o contraseña inválidos`.
- **`active`** flag; admins can deactivate accounts (not their own).

### Tests

Auth tests live in [`tests/test_auth.py`](tests/test_auth.py). Run:

```bash
make test
pytest tests/test_auth.py -v
```

### Why not OAuth?

OAuth/OIDC fits web APIs and corporate SSO. This CLI uses direct login; a future REST layer could reuse `authenticate()` or add OIDC without changing enrollment logic.

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
| `tests/test_auth.py` | Authentication: login, roles, bootstrap admin, enrollment/attendance authorization. |
| `tests/test_service.py` | Service: enrollment, capacity, schedules, attendance. |
| `tests/test_trainer_crud.py` | Trainer CRUD and profile validation (email, phone, specialty, bio, experience). |
| `tests/test_member_crud.py` | Member CRUD: create, read, list, update, delete, and cascade on delete. |
| `tests/test_class_crud.py` | Class CRUD: create, read, list, update, delete, field validation, and capacity rules. |
| `tests/test_enrollment_crud.py` | Enrollment list, `is_enrolled`, `unenroll_member`. |
| `tests/test_attendance_crud.py` | Attendance CRUD and listing by class/member. |

### Fixtures

- **`clean_db`** (autouse): before each test, `init_schema()` and `TRUNCATE ... RESTART IDENTITY` on `attendance`, `enrollments`, `class_schedules`, `classes`, `app_users`, `members`, `trainers`. Defined in each test file.

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

