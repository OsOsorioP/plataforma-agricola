from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage

from app.core.config import GOOGLE_API_KEY
from app.graph.graph_state import GraphState

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", temperature=0, google_api_key=GOOGLE_API_KEY)


async def sustainability_agent_node(state: GraphState) -> dict:
    """
    Nodo del Agente de Sostenibilidad. Revisa las recomendaciones o el plan de tratamiento..
    """
    print("-- Node ejecutandose: sustainability --")
    prompt = f"""Eres un experto en agricultura sostenible y prácticas ecológicas.
    
    Tarea: Revisar recomendaciones agrícola o planes de tratamiento propuesto.

    Analízala desde una perspectiva de sostenibilidad.
    - Si la recomendación o plan ya es sostenible, apruébala y explica brevemente por qué.
    - Si NO es sostenible (ej. sugiere un pesticida químico fuerte), recházala y propón una alternativa orgánica o de bajo impacto.
    
    Información Clave:
    - Id del usuario actual: {state.get("user_id")}
    - Información clave: {state.get("info_next_agent")}
    """

    response = await llm.ainvoke(prompt)

    print(response.content)

    return {
        "messages": [AIMessage(content=response.content, name="sustainability")],
        "agent_history": state.get("agent_history", []) + ["sustainability_agent"]
    }
