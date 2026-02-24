import os
from dotenv import load_dotenv

load_dotenv()
DB_NAME: str = os.getenv("POSTGRES_DB", "postgres_db")
DB_USER: str = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "1234")
DB_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT: int = os.getenv("POSTGRES_PORT", 5432)
DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
