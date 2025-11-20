from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

from app.core.config import GOOGLE_API_KEY
from app.graph.graph_state import GraphState

llm_supervisor = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, google_api_key=GOOGLE_API_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0, google_api_key=GOOGLE_API_KEY)

async def vision_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Visión. Ahora produce un diagnóstico para otros agentes."""
    print("-- Node ejecutandose: vision --")
    prompt = f"""
    Eres un fitopatólogo experto (especialista en enfermedades de plantas).
    Analiza la siguiente imagen de un cultivo junto con la pregunta del usuario.
    1. Identifica la planta en la imagen.
    2. Diagnostica cualquier posible enfermedad, plaga o deficiencia nutricional visible.
    3. Proporciona una recomendación clara y práctica para tratar el problema.
    4. Si no puedes hacer un diagnóstico claro, explícalo y sugiere qué tipo de información adicional o fotos necesitarías.
    """
    # 3. Tu salida debe ser únicamente el nombre del problema identificado.
    # 3. Proporciona una recomendación clara y práctica para tratar el problema.
    # 4. Si no puedes hacer un diagnóstico claro, explícalo y sugiere qué tipo de información adicional o fotos necesitarías.
    if state.get("image_base64"):
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{state['image_base64']}"
                },
            ]
        )
    elif (state.get("audio_base64")):
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "media",
                    "data": f"{state['audio_base64']}",
                    "mime_type": "audio/mpeg"
                },
            ]
        )

    response = await llm.ainvoke([message])
    print(response.content)
    return {
        "messages": [AIMessage(content=response.content, name="vision_agent")],
        "agent_history": state.get("agent_history", []) + ["vision_agent"]
    }
