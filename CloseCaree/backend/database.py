
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

CAMINHO_ENV = Path(__file__).resolve().parent / ".env"

load_dotenv(CAMINHO_ENV)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "closecare")
DB_USER = os.getenv("DB_USER", "closecare_app")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not DB_PASSWORD:
    raise RuntimeError(
        "Configure DB_PASSWORD no arquivo backend/.env"
    )

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)

class Base(DeclarativeBase):
    pass


def get_db():
    with Session(engine) as session:
        yield session
