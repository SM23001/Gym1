# Gym1

## Cómo ejecutar la aplicación - 1 -2 -2
## Cómo ejecutar la aplicación - 1 -2

1. **Clona el repositorio y navega a la carpeta:**

    ```bash
    cd /home/verscomp/Cursor/Pruebas/Gym1
    ```

2. **Activa el entorno virtual:**

    ```bash
    source .venv/bin/activate
    ```

    *(Crea el entorno si es necesario: `python -m venv .venv` e instala las dependencias con `pip install -r requirements.txt`)*

3. **Ejecuta la aplicación CLI:**

    ```bash
    python cli.py
    ```

4. **Sigue las instrucciones del menú para operar el sistema de gestión de gimnasio.**













Aplicación de gestión de gimnasio en CLI usando Python y PostgreSQL.

## Modelo de arquitectura de software

Se ha implementado una **arquitectura en capas** (Layered Architecture / N-tier) con **patrón Repository** y **capa de servicio**:

| Capa | Módulo(s) | Responsabilidad |
|------|-----------|------------------|
| **Presentación** | `cli.py`, `colors.py` | Interfaz de usuario (menú, entradas, mensajes). No contiene lógica de negocio. |
| **Aplicación / Servicio** | `service.py` | Orquesta los casos de uso, aplica reglas de negocio (cupo, choques de horario, validaciones) y delega la persistencia en el repositorio. |
| **Dominio** | `models.py` | Entidades del negocio (`Trainer`, `Member`, `GymClass`). Solo datos, sin lógica. |
| **Acceso a datos** | `repository.py` | **Patrón Repository**: abstrae el almacenamiento en PostgreSQL (CRUD, consultas). El servicio no conoce SQL. |
| **Infraestructura** | `db.py`, `config.py` | Conexión a BD, configuración y creación del esquema. |

**Flujo de dependencias:** la dependencia va siempre hacia dentro (hacia el dominio y la infraestructura). La presentación depende del servicio; el servicio depende del repositorio y de los modelos; el repositorio depende de la BD y de los modelos. Así se puede cambiar la interfaz (por ejemplo pasar de CLI a API REST) o el almacenamiento (por ejemplo otro motor de BD) sin reescribir la lógica de negocio.

**Patrones utilizados:**
- **Repository**: `repository.py` actúa como fachada del almacenamiento; el servicio trabaja con entidades y operaciones de alto nivel.
- **Service layer**: `service.py` concentra la lógica de aplicación y las validaciones, dejando la presentación “tonta” y el repositorio solo como persistencia.

## Estructura de módulos (diseño técnico)

- `config.py`
  - **Responsabilidad**: obtener la configuración de base de datos.
  - Usa `python-dotenv` para cargar un archivo `.env` si existe.
  - Expone la clase `Settings` con las propiedades `db_host`, `db_port`, `db_name`, `db_user`, `db_password` y la propiedad calculada `dsn`.
  - Función principal: `get_settings()` que se usa desde `db.py`.

- `db.py`
  - **Responsabilidad**: encapsular la conexión a PostgreSQL.
  - Función `get_connection()`:
    - Construye el DSN a partir de `config.get_settings()`.
    - Devuelve un context manager que abre una conexión `psycopg2`, hace `commit` si todo va bien y `rollback` en caso de error.
  - Función `init_schema()`:
    - Ejecuta el DDL necesario para crear las tablas `trainers`, `members`, `classes`, `enrollments` y `attendance` si no existen.
    - Se llama al inicio de la aplicación (`cli.py`) y en los tests.

- `models.py`
  - **Responsabilidad**: representar las entidades de dominio en memoria.
  - Define `Trainer`, `Member` y `GymClass` como `@dataclass`, con tipos estáticos (`id`, `name`, horarios, cupo, etc.).
  - No contiene lógica de negocio, solo estructura de datos.

- `repository.py`
  - **Responsabilidad**: capa de acceso a datos (DAO/Repository) contra PostgreSQL.
  - Operaciones implementadas:
    - `create_trainer`, `create_member`, `create_class`.
    - `get_trainer`, `get_member`, `get_class`, `list_classes`.
    - Métricas y consultas auxiliares: `count_enrollments`, `is_member_enrolled`, `list_member_classes`.
    - Comandos: `enroll_member`, `mark_attendance`.
  - Utiliza `db.get_connection()` y cursores `RealDictCursor` para mapear filas a `dataclasses`.
  - No aplica reglas de negocio (por ejemplo choques de horario o cupo), solo ejecuta SQL.

- `service.py`
  - **Responsabilidad**: lógica de negocio de la gestión de gimnasio.
  - Define la excepción `BusinessError` para errores de reglas de negocio.
  - Expone funciones:
    - `create_trainer`, `create_member`, `create_class` (valida que la hora de fin sea > que la de inicio).
    - `enroll_member`:
      - Verifica que la clase y el miembro existan.
      - Comprueba que no se supere el `capacity` de la clase.
      - Evita inscribir dos veces al mismo miembro.
      - Previene **choques de horario**: usa `_overlaps` para comparar el intervalo horario/ día con las demás clases donde el miembro ya está inscrito.
    - `mark_attendance`:
      - Solo permite marcar asistencia si el miembro está inscrito en la clase.
    - `list_classes` para obtener el catálogo de clases.
  - Esta capa es independiente de la interfaz de usuario (CLI) y de los detalles concretos de SQL.

- `cli.py`
  - **Responsabilidad**: interfaz de línea de comandos para interactuar con el sistema.
  - En `main()`:
    - Llama a `init_schema()` al inicio para asegurar que las tablas existen.
    - Presenta un menú con opciones:
      1. Alta de entrenador.
      2. Alta de miembro.
      3. Alta de clase (pide día de la semana, horario y cupo).
      4. Inscribir miembro en clase.
      5. Registrar asistencia.
      6. Listar clases.
    - Traduce la entrada del usuario (strings) a tipos adecuados (enteros, horas) y delega en funciones de `service`.
    - Captura `BusinessError` y `ValueError` para mostrar mensajes claros al usuario y no interrumpir la aplicación.

- `conftest.py`
  - **Responsabilidad**: configuración global de pytest.
  - Añade la raíz del proyecto al `sys.path` para que los imports (`db`, `service`, `repository`, etc.) funcionen al ejecutar `pytest` desde la raíz del proyecto.

- `tests/`
  - **Responsabilidad**: validar casos críticos de la lógica de negocio (capa de servicio y persistencia).
  - Ver sección [Tests](#tests) más abajo para detalles.

## Configuración de PostgreSQL

Crear una base de datos y usuario, por ejemplo:

```sql
CREATE USER gymuser WITH PASSWORD 'gympass';
CREATE DATABASE gymdb OWNER gymuser;
GRANT ALL PRIVILEGES ON DATABASE gymdb TO gymuser;
\q
```

Configura las variables de entorno (por ejemplo en un archivo `.env` en la raíz del proyecto):

```bash
GYM_DB_HOST=192.168.1.10 / localhost
GYM_DB_PORT=5432
GYM_DB_NAME=gymdb
GYM_DB_USER=gymuser
GYM_DB_PASSWORD=gympass
```

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate  # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar la app CLI

```bash
python cli.py
```

La primera ejecución crea las tablas necesarias en la base de datos.

## Tests

Los tests comprueban la lógica de negocio y el uso del repositorio contra una base PostgreSQL real (la misma configurada en `.env` o por defecto).

### Requisitos

- PostgreSQL en marcha y accesible con la misma configuración que la aplicación.
- Dependencias instaladas (`pip install -r requirements.txt` incluye `pytest`).

### Configuración de pytest: `conftest.py`

En la raíz del proyecto, `conftest.py`:

- Inserta la raíz del proyecto en `sys.path` para que, al ejecutar `pytest`, los módulos `db`, `service`, `repository`, etc. se importen correctamente sin instalar el proyecto como paquete.

### Estructura de tests

| Archivo | Contenido |
|---------|-----------|
| `tests/test_service.py` | Tests de la capa de servicio (inscripción, cupo, horarios, asistencia). |

### Fixtures

- **`clean_db`** (autouse): se ejecuta antes de cada test.
  - Llama a `init_schema()` para asegurar que las tablas existen.
  - Ejecuta `TRUNCATE attendance, enrollments, classes, members, trainers RESTART IDENTITY` para dejar la BD limpia y con IDs predecibles en cada test.

### Casos de prueba

| Test | Qué valida |
|------|------------|
| **`test_enroll_member_capacity_and_overlap`** | Inscripción: un miembro se inscribe correctamente en una clase con cupo; un segundo miembro no puede inscribirse si el cupo está lleno (`BusinessError` "Cupo completo"); el mismo miembro no puede inscribirse en otra clase que se solapa en horario el mismo día (`BusinessError` "Choque de horario"). |
| **`test_mark_attendance_requires_enrollment`** | Asistencia: no se puede marcar asistencia si el miembro no está inscrito (`BusinessError`); tras inscribir al miembro, se puede marcar asistencia y se comprueba que existe al menos un registro en la tabla `attendance` para esa clase y miembro. |

### Cómo ejecutar los tests

Desde la raíz del proyecto (con el venv activado):

```bash
pytest
```

Opciones útiles:

```bash
pytest -v                  # salida verbose (nombre de cada test)
pytest tests/test_service.py   # solo tests del servicio
pytest -k "attendance"      # solo tests cuyo nombre contiene "attendance"
```

**Importante:** los tests usan la misma base de datos que la aplicación y hacen `TRUNCATE` de las tablas antes de cada test. No ejecutes los tests sobre una base con datos que quieras conservar, o usa una base dedicada (por ejemplo `GYM_DB_NAME=gymdb_test`).

