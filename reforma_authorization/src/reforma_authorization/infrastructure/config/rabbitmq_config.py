import os 
from dotenv import load_dotenv 

load_dotenv() 
RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST") 
RABBITMQ_PORT: str = os.getenv("RABBITMQ_PORT") 
RABBITMQ_USER: str = os.getenv("RABBITMQ_USER") 
RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD") 