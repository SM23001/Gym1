# Gym1

Aplicación de gestión de gimnasio en CLI usando Python y PostgreSQL.

## Estructura de módulos

- `config.py`: carga la configuración de conexión a PostgreSQL desde variables de entorno.
- `db.py`: manejo de conexión y creación de tablas (`init_schema`).
- `models.py`: modelos de dominio (`Trainer`, `Member`, `GymClass`).
- `repository.py`: acceso a datos (CRUD contra PostgreSQL).
- `service.py`: lógica de negocio (cupo, choques de horario, asistencia).
- `cli.py`: interfaz de línea de comandos.
- `tests/`: tests unitarios con `pytest`.

## Configuración de PostgreSQL

Crear una base de datos y usuario, por ejemplo:

```sql
CREATE DATABASE gymdb;
CREATE USER gymuser WITH PASSWORD 'gympass';
GRANT ALL PRIVILEGES ON DATABASE gymdb TO gymuser;
```

Configura las variables de entorno (por ejemplo en un archivo `.env` en la raíz del proyecto):

```bash
GYM_DB_HOST=localhost
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

