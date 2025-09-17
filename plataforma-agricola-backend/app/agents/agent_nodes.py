from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import GOOGLE_API_KEY
from app.agents.graph_state import GraphState

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=GOOGLE_API_KEY)

def monitoring_agent_node(state: GraphState) -> dict:
    """
    Nodo del Agente de Monitoreo. Por ahora, actúa como un agente general.
    
    Args:
        state: El estado actual del grafo.
        
    Returns:
        Un diccionario con las actualizaciones para el estado.
    """
    user_query = state["user_query"]
    
    # Aquí ira lógica más compleja del agente en el futuro.
    # Por ahora, simplemente responde a la consulta del usuario.
    
    # Se crea un prompt mas específico
    prompt = f"""
    Eres un asistente experto en agricultura para la plataforma Agrosmi.
    Un agricultor te ha hecho la siguiente pregunta: "{user_query}"
    
    Proporciona una respuesta clara, concisa y útil.
    """
    
    response = llm.invoke(prompt)
    
    return {"agent_response": response.content}