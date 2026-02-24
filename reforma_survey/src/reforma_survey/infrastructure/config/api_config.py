import os
from dotenv import load_dotenv

load_dotenv()
INTERNAL_API_KEY  = os.getenv("INTERNAL_API_KEY", "INTERNAL_API_KEY")