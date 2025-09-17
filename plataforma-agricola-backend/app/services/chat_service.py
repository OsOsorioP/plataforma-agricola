from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import GOOGLE_API_KEY

def get_ai_response(user_query: str) -> str:
    """
    Función simple para obtener una respuesta de Gemini a una consulta.
    """
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=GOOGLE_API_KEY)
        
        response = llm.invoke(user_query)
        
        return response.content
        
    except Exception as e:
        print(f"Error al interactuar con la API de Gemini: {e}")
        return "Lo siento, he tenido un problema para procesar tu solicitud."