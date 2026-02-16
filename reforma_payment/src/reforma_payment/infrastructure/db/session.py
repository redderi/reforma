import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from reforma_payment.infrastructure.config.db_config import (
    DATABASE_URL, 
    DB_HOST, 
    DB_NAME, 
    DB_PASSWORD, 
    DB_PORT, 
    DB_USER
)
from reforma_common.logger import log_info
from reforma_common.roles import UserRole
from reforma_common.user_status import UserStatus
from sqlalchemy.orm import sessionmaker
from reforma_payment.infrastructure.db.base import Base 
from reforma_payment.infrastructure.db.models import UserModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select

def create_database():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  

    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DB_NAME,))
    exists = cur.fetchone()
    if not exists:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
        log_info(f"База {DB_NAME} создана", service="auth-service")
    else:
        log_info(f"База {DB_NAME} уже существует", service="auth-service")

    cur.close()
    conn.close()

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)