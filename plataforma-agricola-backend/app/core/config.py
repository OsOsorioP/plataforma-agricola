import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("No se encontró la GOOGLE_API_KEY en el entorno. Asegúrate de tener un archivo .env válido.")