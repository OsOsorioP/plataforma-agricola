from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import AIMessage
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate

from app.core.config import GOOGLE_API_KEY
from app.graph.state import GraphState
from app.agents.common.tools import (
    get_parcel_details,
    list_user_parcels,
    lookup_parcel_by_name,
    update_parcel_info,
)
from app.agents.production.tools import knowledge_base_tool, get_parcel_health_indices
from app.utils.helper import normalize_agent_output
from app.prompts.loader import load_prompt

production_tools = [
    knowledge_base_tool,
    get_parcel_details,
    list_user_parcels,
    lookup_parcel_by_name,
    get_parcel_health_indices,
    update_parcel_info
]

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  
    temperature=0.2,
    google_api_key=GOOGLE_API_KEY
)

async def production_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Optimización de la Producción. Ahora puede recibir un diagnóstico."""
    print("-- Node ejecutandose: Production --")

    user_id = state.get("user_id", "N/A")
    info_next_agent = state.get(
        "info_next_agent", "Sin información específica del supervisor")
    
    prompt_template = ChatPromptTemplate.from_messages([(
        "system",
        load_prompt("water", "system.md")
    ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    prompt_production = prompt_template.partial(
        user_id=user_id,
        info_next_agent=info_next_agent,
    )

    agent = create_tool_calling_agent(
        llm=llm, 
        tools=production_tools, 
        prompt=prompt_production
    )
    
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=production_tools,
        verbose=True,
        max_iterations=7,
        handle_parsing_errors=True,
        return_intermediate_steps=False
    )

    try:
        response = await agent_executor.ainvoke({
            "messages": state["messages"]
        })
        
        response_content = normalize_agent_output(response["output"])

        print(
            f"\n-- Respuesta del production: {response_content} --\n")

        return {
            "messages": [AIMessage(content=response_content, name="production")],
            "list_agent": state.get("list_agent", []) + ["production"]
        }

    except Exception as e:
        error_message = f"Error en agente de producción: {str(e)}"
        print(f"-- ERROR: {error_message} --")

        return {
            "messages": [AIMessage(
                content="Disculpa, ocurrió un error al analizar tu consulta de producción. Por favor, intenta ser más específico sobre la parcela o el problema.",
                name="production"
            )],
            "list_agent": state.get("list_agent", []) + ["production"]
        }
