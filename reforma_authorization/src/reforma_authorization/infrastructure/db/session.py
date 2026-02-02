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
DB_NAME: str = os.getenv("DB_NAME", "reforma_authorization_db") 
USER: str = os.getenv("USER", "postgres") 
PASSWORD: str = os.getenv("PASSWORD", "1234") 
HOST: str = os.getenv("HOST", "localhost") 
PORT: int = os.getenv("PORT", 5432)
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:1234@localhost:5432/reforma_authorization_db")

conn = psycopg2.connect(
    dbname="postgres",
    user=USER,
    password=PASSWORD,
    host=HOST,
    port=PORT
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

