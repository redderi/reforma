import os
from dotenv import load_dotenv

load_dotenv()
SMTP_HOST: str = os.getenv("SMTP_HOST")
SMTP_PORT: str = os.getenv("SMTP_PORT")
SMTP_USER: str = os.getenv("SMTP_USER")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")
EMAIL_FROM: str = os.getenv("EMAIL_FROM")
