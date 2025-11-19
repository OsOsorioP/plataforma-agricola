import os
import requests
import time
from typing import Optional

TOKEN_URL = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
CLIENT_ID = 'cdse-public'

class CDSEAuth:
    """Clase para manejar la obtención y refresco del token de acceso CDSE."""
    
    def __init__(self):
        """Inicializa las credenciales desde variables de entorno."""
        self.username = os.getenv("CDSE_USERNAME")
        self.password = os.getenv("CDSE_PASSWORD")
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0
        
        if not self.username or not self.password:
            raise EnvironmentError("Las variables de entorno CDSE_USERNAME y CDSE_PASSWORD no están configuradas.")

    def get_token(self) -> str:
        """Retorna un token de acceso válido, refrescándolo si es necesario."""
        if self._access_token and self._token_expiry > time.time():
            return self._access_token
        
        print("Obteniendo nuevo token de acceso CDSE...")
        
        payload = {
            'client_id': CLIENT_ID,
            'username': self.username,
            'password': self.password,
            'grant_type': 'password'
        }
        
        try:
            response = requests.post(TOKEN_URL, data=payload)
            response.raise_for_status()
            
            data = response.json()
            token = data.get("access_token")
            expires_in = data.get("expires_in", 300)
            
            if token:
                self._access_token = token
                self._token_expiry = time.time() + expires_in - 60 
                return token
            else:
                raise ValueError("La respuesta de autenticación no contenía 'access_token'.")
                
        except requests.RequestException as e:
            raise ConnectionError(f"Error al conectar con el servicio CDSE para obtener el token: {e}")
        except Exception as e:
            raise Exception(f"Error desconocido durante la autenticación CDSE: {e}")

CDSE_AUTHENTICATOR = CDSEAuth()