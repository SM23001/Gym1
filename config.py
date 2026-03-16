from dataclasses import dataclass
import os
from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    @property
    def dsn(self) -> str:
        return (
            f"dbname={self.db_name} user={self.db_user} password={self.db_password} "
            f"host={self.db_host} port={self.db_port}"
        )


def get_settings() -> Settings:
    return Settings(
        db_host=os.getenv("GYM_DB_HOST", "localhost"),
        db_port=int(os.getenv("GYM_DB_PORT", "5432")),
        db_name=os.getenv("GYM_DB_NAME", "gymdb"),
        db_user=os.getenv("GYM_DB_USER", "gymuser"),
        db_password=os.getenv("GYM_DB_PASSWORD", "gympass"),
    )

