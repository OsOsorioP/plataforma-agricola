from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from pydantic.v1 import BaseModel, Field

from app.core.config import GOOGLE_API_KEY
from app.agents.graph_state import GraphState

class RouteQuery(BaseModel):
    """Enruta una consulta de usuario a un agente especialista."""
    destination: str = Field(
        description="El nombre del agente especialista al que se debe enrutar la consulta. Debe ser uno de: ['production', 'water', 'supply_chain', 'risk', 'general']"
    )

def get_router():
    """Crea y devuelve el enrutador de consultas."""
    prompt = PromptTemplate(
        template="""
        Eres un director de proyecto experto en una empresa de tecnología agrícola.
        Tu trabajo es analizar la siguiente pregunta de un agricultor y decidir qué departamento (agente especialista) es el más adecuado para responderla.

        Aquí están los departamentos disponibles:
        - 'production': Expertos en maximizar el rendimiento de los cultivos, sugerir prácticas de manejo, fertilizantes, etc.
        - 'water': Expertos en riego, gestión y conservación del agua.
        - 'supply_chain': Expertos en logística, inventario, transporte y venta de productos.
        - 'risk': Expertos en analizar riesgos climáticos (heladas, sequías) y proponer planes de contingencia.
        - 'general': Equipo de soporte general que puede responder preguntas sobre datos de parcelas o temas no cubiertos por los especialistas.

        Pregunta del usuario:
        "{query}"

        ¿A qué departamento deberías enrutar esta pregunta?
        """,
        input_variables=["query"],
    )

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=GOOGLE_API_KEY)
    structured_llm = llm.with_structured_output(RouteQuery)
    return prompt | structured_llm

query_router = get_router()

def router_node(state: GraphState) -> str:
    """
    Nodo enrutador que decide el siguiente paso.
    """
    result = query_router.invoke({"query": state["user_query"]})
    
    if result.destination:
        print(f"-- Node enrutador: Decisión ir a {result.destination} --")
        return result.destination
    else:
        return "end"
    
def image_pre_router(state: GraphState) -> str:
    """Decide si hay una imagen para enviar al agente de visión."""
    if state.get("image_base64"):
        print("-- Node enrutador imagen: enrutando a visión--")
        return "vision_agent"
    else:
        print("-- Node enrutador imagen: enrutando a router, no hay imagen--")
        return router_node(state)