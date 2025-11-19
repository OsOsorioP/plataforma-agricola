import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY:str = os.getenv("GOOGLE_API_KEY")
OPENWEATHER_API_KEY:str = os.getenv("OPENWEATHER_API_KEY")

SECRET_KEY:str = os.getenv("SECRET_KEY")
ALGORITHM:str = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES:int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

DATOS_GOV_API_KEY:str = os.getenv("DATOS_GOV_API_KEY")
DATOS_GOV_USER:str = os.getenv("DATOS_GOV_USER")
DATOS_GOV_PASSWORD:str = os.getenv("DATOS_GOV_PASSWORD")

if not GOOGLE_API_KEY:
    raise ValueError("No se encontró la GOOGLE_API_KEY en el entorno. Asegúrate de tener un archivo .env válido.")