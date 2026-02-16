import os
from dotenv import load_dotenv

load_dotenv()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")

# payment-service

PAYMENT_EXCHANGE = os.getenv("PAYMENT_EXCHANGE")
ADD_BALANCE_ROUTING_KEY = os.getenv("ADD_BALANCE_ROUTING_KEY")