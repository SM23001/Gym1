# Gym1

Aplicación de gestión de gimnasio en CLI usando Python y PostgreSQL.

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

- `tests/`
  - **Responsabilidad**: validar casos críticos de la lógica de negocio.
  - Se usa `pytest`.
  - `tests/test_service.py`:
    - Fixture `clean_db`:
      - Llama a `init_schema()` y después hace `TRUNCATE` de todas las tablas relevantes, reiniciando los `SERIAL` para que los IDs sean predecibles en cada test.
    - `test_enroll_member_capacity_and_overlap`:
      - Verifica que:
        - Se puede inscribir un miembro en una clase con cupo disponible.
        - No se puede inscribir un segundo miembro cuando el cupo está completo.
        - El mismo miembro no puede inscribirse en otra clase que se solapa en horario el mismo día.
    - `test_mark_attendance_requires_enrollment`:
      - Impide marcar asistencia si el miembro no está inscrito.
      - Permite marcar asistencia si el miembro está inscrito y verifica que se generó un registro en la tabla `attendance`.

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

## Ejecutar tests unitarios

```bash
pytest
```

Cuidado: los tests limpian todas las tablas del esquema usado (TRUNCATE).

