import os
from dotenv import load_dotenv

load_dotenv()
INTERNAL_API_KEY  = os.getenv("INTERNAL_API_KEY", "INTERNAL_API_KEY")
SURVEY_SERVICE_URL = os.getenv("SURVEY_SERVICE_URL", "SURVEY_SERVICE_URL") 
