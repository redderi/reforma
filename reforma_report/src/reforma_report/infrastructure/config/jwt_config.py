import os
from dotenv import load_dotenv

load_dotenv()
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not set")
