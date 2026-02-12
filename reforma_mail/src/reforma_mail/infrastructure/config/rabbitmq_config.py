import os
from dotenv import load_dotenv

load_dotenv()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
MAIL_EXCHANGE = os.getenv("MAIL_EXCHANGE")
EMAIL_VERIFICATION_ROUTING_KEY = os.getenv("EMAIL_VERIFICATION_ROUTING_KEY")
MAIL_QUEUE = os.getenv("MAIL_QUEUE")
MAIL_DLQ = os.getenv("MAIL_DLQ")