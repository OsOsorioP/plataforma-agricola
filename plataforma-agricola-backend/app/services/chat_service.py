from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import GOOGLE_API_KEY
from app.agents.graph_builder import agent_graph

def run_agent_graph(user_query: str) -> str:
    """
    Ejecuta el grafo de agentes con la consulta del usuario.
    """
    try:
        initial_state = {"user_query": user_query, "agent_response": ""}
        
        final_state = agent_graph.invoke(initial_state)
        
        return final_state.get("agent_response", "No se pudo obtener una respuesta.")
        
    except Exception as e:
        print(f"Error al ejecutar el grafo de agentes: {e}")
        return "Lo siento, he tenido un problema para procesar tu solicitud a través del sistema de agentes."

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