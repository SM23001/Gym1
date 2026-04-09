# Gym1

Sistema de gestión de gimnasio por **línea de comandos (CLI)** en Python, con persistencia en **PostgreSQL**. Permite dar de alta entrenadores, miembros y clases; inscribir miembros respetando **cupo** y **choques de horario**; registrar **asistencia**; y listar clases.

**Stack:** Python 3, `psycopg2`, `python-dotenv`, `pytest`.

---

## Tabla de contenidos

1. [Requisitos previos](#requisitos-previos)
2. [Inicio rápido](#inicio-rápido)
3. [Configuración de PostgreSQL](#configuración-de-postgresql)
4. [Variables de entorno](#variables-de-entorno)
5. [Instalación](#instalación)
6. [Ejecutar la aplicación](#ejecutar-la-aplicación)
7. [Modelo de arquitectura](#modelo-de-arquitectura-de-software)
8. [Estructura de módulos](#estructura-de-módulos-diseño-técnico)
9. [Tests](#tests)

---

## Requisitos previos

- **Python 3** (recomendado 3.10+)
- **PostgreSQL** accesible desde la máquina donde corre la app
- Cliente `psql` o herramienta equivalente para crear usuario y base de datos (opcional pero útil)

---

## Inicio rápido

1. Clona el repositorio y entra en la carpeta del proyecto.

2. Crea y activa un entorno virtual, e instala dependencias:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Crea la base de datos y el usuario en PostgreSQL (ver [Configuración de PostgreSQL](#configuración-de-postgresql)).

4. Crea un archivo `.env` en la raíz con las variables `GYM_DB_*` (ver [Variables de entorno](#variables-de-entorno)), o confía en los valores por defecto de `config.py` si encajan con tu entorno.

5. Ejecuta la CLI:

   ```bash
   python cli.py
   ```

   La primera ejecución crea las tablas necesarias (`init_schema`).

6. Usa el menú interactivo para operar el sistema.

---

## Configuración de PostgreSQL

Ejemplo de creación de usuario y base de datos:

```sql
CREATE USER gymuser WITH PASSWORD 'gympass';
CREATE DATABASE gymdb OWNER gymuser;
GRANT ALL PRIVILEGES ON DATABASE gymdb TO gymuser;
\q
```

Ajusta nombres y contraseñas según tu política de seguridad.

---

## Variables de entorno

Puedes definirlas en un archivo `.env` en la raíz del proyecto (cargado automáticamente con `python-dotenv`).

| Variable | Descripción |
|----------|-------------|
| `GYM_DB_HOST` | Host del servidor PostgreSQL |
| `GYM_DB_PORT` | Puerto (numérico) |
| `GYM_DB_NAME` | Nombre de la base de datos |
| `GYM_DB_USER` | Usuario |
| `GYM_DB_PASSWORD` | Contraseña |

**Valores por defecto** si no defines las variables (ver `config.py`):

| Variable | Por defecto |
|----------|-------------|
| `GYM_DB_HOST` | `192.168.1.34` |
| `GYM_DB_PORT` | `5432` |
| `GYM_DB_NAME` | `gymdb` |
| `GYM_DB_USER` | `gymuser` |
| `GYM_DB_PASSWORD` | `gympass` |

Ejemplo de `.env` para desarrollo local:

```bash
GYM_DB_HOST=localhost
GYM_DB_PORT=5432
GYM_DB_NAME=gymdb
GYM_DB_USER=gymuser
GYM_DB_PASSWORD=gympass
```

---

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
# En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Dependencias principales (`requirements.txt`):

- `psycopg2-binary` — cliente PostgreSQL
- `python-dotenv` — carga de `.env`
- `pytest` — tests

---

## Ejecutar la aplicación

```bash
source .venv/bin/activate
python cli.py
```

El menú incluye, entre otras opciones:

1. Alta de entrenador  
2. Alta de miembro  
3. Alta de clase (día, horario, cupo)  
4. Inscribir miembro en clase  
5. Registrar asistencia  
6. Listar clases  

Los errores de reglas de negocio se muestran como mensajes claros (`BusinessError`, validaciones de entrada) sin tumbar la aplicación.

---

## Modelo de arquitectura de software

Arquitectura en **capas** (N-tier) con **Repository** y **capa de servicio**:

| Capa | Módulo(s) | Responsabilidad |
|------|-----------|------------------|
| **Presentación** | `cli.py`, `colors.py` | Menú, entradas y salida. `colors.py` define códigos ANSI y el helper `c()` para texto coloreado. Sin lógica de negocio. |
| **Aplicación / Servicio** | `service.py` | Casos de uso, reglas (cupo, choques de horario, validaciones) y delegación al repositorio. |
| **Dominio** | `models.py` | Entidades (`Trainer`, `Member`, `GymClass`) como dataclasses; solo datos. |
| **Acceso a datos** | `repository.py` | Patrón Repository sobre PostgreSQL (CRUD y consultas). El servicio no escribe SQL. |
| **Infraestructura** | `db.py`, `config.py` | Conexión, configuración y creación del esquema. |

**Flujo de dependencias:** la presentación depende del servicio; el servicio del repositorio y los modelos; el repositorio de la BD y los modelos. Así se puede cambiar la interfaz (por ejemplo a una API) o el motor de datos sin reescribir toda la lógica.

**Patrones:**

- **Repository:** `repository.py` como fachada de persistencia.  
- **Service layer:** `service.py` concentra la lógica de aplicación; la CLI permanece delgada.

---

## Estructura de módulos (diseño técnico)

- **`config.py`** — Configuración de BD con `python-dotenv`. Clase `Settings` (`db_host`, `db_port`, `db_name`, `db_user`, `db_password`, propiedad `dsn`). Función `get_settings()` usada desde `db.py`.

- **`db.py`** — Conexión PostgreSQL. `get_connection()` como context manager (commit/rollback). `init_schema()` crea las tablas `trainers`, `members`, `classes`, `enrollments` y `attendance` si no existen. Se invoca al arrancar la CLI y en los tests.

- **`models.py`** — `Trainer`, `Member`, `GymClass` como `@dataclass` con tipos estáticos.

- **`repository.py`** — Persistencia: `create_trainer`, `create_member`, `create_class`, `get_*`, `list_classes`, métricas (`count_enrollments`, `is_member_enrolled`, `list_member_classes`), `enroll_member`, `mark_attendance`. Usa `RealDictCursor` para mapear a dataclasses. Sin reglas de negocio.

- **`service.py`** — Excepción `BusinessError`. Funciones de alto nivel: altas con validación de horarios; `enroll_member` (existencia, cupo, duplicados, solapamiento con otras clases del miembro); `mark_attendance` solo si hay inscripción; `list_classes`.

- **`cli.py`** — `main()`: `init_schema()`, bucle de menú, parseo de entrada y llamadas al servicio; manejo de `BusinessError` y `ValueError`.

- **`colors.py`** — Constantes ANSI y `c(text, color)` para mensajes en terminal.

- **`conftest.py`** — Ajuste de `sys.path` para pytest en la raíz del proyecto.

- **`tests/`** — Tests de servicio y persistencia (ver [Tests](#tests)).

---

## Tests

Comprueban la lógica de negocio y el repositorio contra una **base PostgreSQL real** (la misma configuración que la app, salvo que uses otra vía `.env`).

### Requisitos

- PostgreSQL en marcha con la misma configuración que la aplicación.
- Dependencias instaladas (`pytest` viene en `requirements.txt`).

### `conftest.py`

Añade la raíz del proyecto a `sys.path` para importar `db`, `service`, `repository`, etc., sin instalar el proyecto como paquete.

### Estructura

| Archivo | Contenido |
|---------|-----------|
| `tests/test_service.py` | Servicio: inscripción, cupo, horarios, asistencia. |

### Fixtures

- **`clean_db`** (autouse): antes de cada test, `init_schema()` y `TRUNCATE ... RESTART IDENTITY` sobre `attendance`, `enrollments`, `classes`, `members`, `trainers`.

### Casos destacados

| Test | Qué valida |
|------|------------|
| `test_enroll_member_capacity_and_overlap` | Inscripción con cupo; rechazo por cupo lleno; rechazo por choque de horario el mismo día. |
| `test_mark_attendance_requires_enrollment` | Asistencia solo con inscripción previa; registro en `attendance` tras inscribir. |

### Cómo ejecutar

Desde la raíz, con el venv activado:

```bash
pytest
pytest -v
pytest tests/test_service.py
pytest -k "attendance"
```

**Importante:** los tests hacen `TRUNCATE` en cada caso. No uses una base con datos que quieras conservar; para tests dedicados puedes usar por ejemplo `GYM_DB_NAME=gymdb_test` en `.env`.
