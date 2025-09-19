import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY:str = os.getenv("GOOGLE_API_KEY")

SECRET_KEY:str = os.getenv("SECRET_KEY")
ALGORITHM:str = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES:int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

if not GOOGLE_API_KEY:
    raise ValueError("No se encontró la GOOGLE_API_KEY en el entorno. Asegúrate de tener un archivo .env válido.")