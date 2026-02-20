import os
from dotenv import load_dotenv

load_dotenv()
ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@gmail.com")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "12345678")
