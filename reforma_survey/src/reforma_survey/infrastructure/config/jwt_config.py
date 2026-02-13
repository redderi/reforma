import os 
from dotenv import load_dotenv 

load_dotenv() 
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY") 
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256") 
ACCESS_TOKEN_EXPIRE_MINUTES: int = int( os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30) ) 

if not JWT_SECRET_KEY: 
    raise RuntimeError("JWT_SECRET_KEY is not set")