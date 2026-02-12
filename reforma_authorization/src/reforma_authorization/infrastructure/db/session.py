import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from reforma_authorization.infrastructure.db.base import Base 
from reforma_authorization.infrastructure.db.models import UserModel 

import os 
from dotenv import load_dotenv 

load_dotenv() 
DB_NAME: str = os.getenv("POSTGRES_DB", "postgres_db") 
DB_USER: str = os.getenv("POSTGRES_USER", "postgres") 
DB_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "1234") 
DB_HOST: str = os.getenv("POSTGRES_HOST", "localhost") 
DB_PORT: int = os.getenv("POSTGRES_PORT", 5432)

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

print("USER =", DB_USER)
print("PASSWORD =", DB_PASSWORD)
print("HOST =", DB_HOST)
print("DB =", DB_NAME)

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
        print(f"База {DB_NAME} создана!")
    else:
        print(f"База {DB_NAME} уже существует.")

    cur.close()
    conn.close()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

