from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage

from app.core.config import GOOGLE_API_KEY
from app.graph.graph_state import GraphState
from app.agents.agent_model import SupervisorDecision


llm_supervisor = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY
)


# ============================================================================
# FUNCIONES HELPER PARA VALIDACIÓN
# ============================================================================

def _contains_chemical_recommendation(message_content: str) -> bool:
    """
    Detecta si una recomendación incluye químicos sintéticos potencialmente problemáticos.
    """
    content = normalize_message_content(message_content).lower()
    chemical_keywords = [
        # Pesticidas de alta toxicidad
        "clorpirifos", "paraquat", "glifosato", "imidacloprid", "endosulfan",
        "metamidofos", "carbofuran", "monocrotofos", "aldicarb",

        # Categorías generales
        "pesticida", "insecticida", "fungicida", "herbicida", "nematicida",

        # Fertilizantes sintéticos
        "urea", "superfosfato", "cloruro de potasio", "sulfato de amonio",

        # Frases indicadoras
        "aplicar químico", "producto químico", "fertilizante sintético"
    ]

    return any(keyword in content for keyword in chemical_keywords)


def _should_validate_sustainability(last_agent: str, message_content: str, agent_history: list) -> bool:
    """
    Determina si se debe enrutar a sustainability para validación.
    """
    # Si sustainability ya revisó, no volver a enviar
    if "sustainability" in agent_history:
        return False

    # Si el último agente fue production o risk y recomendó químicos
    if last_agent in ["production", "risk"] and _contains_chemical_recommendation(message_content):
        return True

    return False


def normalize_message_content(msg):
    """
    Convierte el contenido de un BaseMessage (str, list, dict, etc.)
    en un string plano seguro para análisis.
    """
    if msg is None:
        return ""

    # Caso: string normal
    if isinstance(msg, str):
        return msg

    # Caso: lista (Gemini vision / multimodal)
    if isinstance(msg, list):
        parts = []
        for item in msg:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                # típicamente Gemini devuelve {"type": "text", "text": "..."}
                if "text" in item:
                    parts.append(str(item["text"]))
                elif "content" in item:
                    parts.append(str(item["content"]))
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return " ".join(parts)

    # Caso: dict
    if isinstance(msg, dict):
        return " ".join([f"{k}: {v}" for k, v in msg.items()])

    # Caso general
    return str(msg)


# ============================================================================
# NODO DEL SUPERVISOR
# ============================================================================

async def supervisor_agent_node(state: GraphState) -> dict:
    """
    Supervisor que orquesta el flujo multi-agente.
    Decide si enrutar a otro agente o finalizar con una respuesta al usuario.
    """
    print("-- Node ejecutándose: Supervisor --")

    # Extraer contexto
    has_image = bool(state.get('image_base64'))
    agent_history = state.get('agent_history', [])
    last_agent = agent_history[-1] if agent_history else None
    reasoning_prev = state.get('reasoning', 'Ninguno')
    raw_content = state["messages"][-1].content if state.get(
        "messages") else ""
    last_message_content = normalize_message_content(raw_content)

    # Construir prompt con contexto dinámico
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            f"""Eres el **Supervisor Orquestador** de un sistema multi-agente agrícola. Tu misión es dirigir consultas al agente especializado más apropiado o finalizar cuando la tarea esté completa.

## TU RESPUESTA DEBE SER UN JSON CON ESTA ESTRUCTURA:
  "next_agent": "nombre_agente" o "FINISH", este NUNCA debe ser un None,
  "reasoning": "explicación de tu decisión",
  "info_for_next_agent": "contexto relevante para el próximo agente",
  "content": "respuesta final SOLO si next_agent es FINISH, de lo contrario vacío"

---

## PROCESO DE DECISIÓN (ORDEN ESTRICTO)

### 1. PRIORIDAD IMAGEN
**REGLA ABSOLUTA**: Si hay imagen (`image_base64`: {'Sí' if has_image else 'No'}) y 'vision' NO está en el historial → **ENRUTAR A 'vision' INMEDIATAMENTE**

### 2. VALIDACIÓN DE SOSTENIBILIDAD (CRÍTICO)
**Antes de hacer FINISH**, verifica:
- ¿El último agente ({last_agent}) recomendó químicos sintéticos?
- ¿'sustainability' ya revisó? (historial: {agent_history})

**Si detectas químicos Y sustainability NO ha revisado:**
→ next_agent = "sustainability"
→ info_for_next_agent = "El agente {last_agent} recomendó: [resumen]. Evaluar alternativas orgánicas."

**Químicos a detectar**: pesticidas (clorpirifos, imidacloprid, paraquat), fertilizantes sintéticos (urea, superfosfato)

### 3. EVALUAR ÚLTIMA RESPUESTA

Analiza el último mensaje del historial:

**CASO A: Respuesta Completa** ✅
- La información disponible responde TOTALMENTE la consulta original
- Todos los aspectos de la pregunta están cubiertos
- No quedan dudas pendientes
→ Acción: next_agent = "FINISH", sintetiza en `content`

**CASO B: Falta Info que SOLO el usuario puede dar** 🙋
- Un agente pidió datos que ningún otro agente puede proporcionar
- Ejemplos:
  * Nombre exacto de parcela (si lookup falló)
  * Tipo de cultivo o etapa fenológica
  * Mejor calidad de imagen
  * Especificaciones del sistema de riego
→ Acción: next_agent = "FINISH", pregunta clara en `content`

**CASO C: Se necesita otro agente** 🔄
- La respuesta es parcial o incompleta
- Requiere expertise de otro dominio
- Un agente mencionó "consultar con [otro agente]"
→ Acción: Selecciona el agente apropiado, pasa contexto en `info_for_next_agent`

**CASO D: Coordinación entre agentes** 🔗
- Un agente pidió datos que OTRO agente SÍ puede proporcionar
- Ejemplo: 'production' necesita clima → enrutar a 'water'
→ Acción: Enruta al agente con las herramientas necesarias

### 4. PREVENIR BUCLES INFINITOS

**REGLAS ANTI-BUCLE:**
- ❌ NO enrutes al mismo agente consecutivamente sin nueva info del usuario
- ❌ Si el último agente devolvió saludo/pregunta genérica sin info nueva → FINISH
- ❌ Si el mismo agente aparece 2+ veces seguidas en historial → FINISH con resumen
- ✅ Solo re-enruta al mismo agente si el usuario dio información adicional

**Último agente ejecutado**: {last_agent}

---

## AGENTES DISPONIBLES Y SUS CAPACIDADES

### 🔬 'vision' - Análisis de Imágenes
**Cuándo usar**: SIEMPRE que haya imagen y no se haya usado aún
**Capacidades**: Diagnóstico de enfermedades, plagas, deficiencias nutricionales
**Herramientas**: Modelo de visión gemini-2.0-flash-exp
**Salida**: Diagnóstico con nivel de confianza + tratamiento recomendado

### 🌱 'production' - Optimización de Producción
**Cuándo usar**:
- Preguntas sobre salud de cultivos ("¿cómo está mi parcela?")
- Problemas específicos (manchas, amarillamiento, plagas)
- Mejora de rendimiento
- Fertilización y nutrición
**Palabras clave**: "salud", "rendimiento", "producción", "fertilizar", "plaga", "enfermedad", "NDVI"
**Herramientas**: knowledge_base, get_parcel_health_indices (10 índices satelitales)
**Salida**: Diagnóstico con NDVI/NDWI + recomendaciones + guarda en BD

### 💧 'water' - Gestión Hídrica
**Cuándo usar**:
- Preguntas sobre riego ("¿necesito regar?")
- Cálculo de necesidades de agua
- Análisis de precipitación
- Estrés hídrico
**Palabras clave**: "riego", "agua", "seco", "humedad", "lluvia", "precipitación"
**Herramientas**: weather_forecast, precipitation_data, calculate_water_requirements, NDWI
**Salida**: Análisis integrado (clima + precipitación + NDVI/NDWI) + litros exactos

### ⚠️ 'risk' - Análisis de Riesgos Climáticos
**Cuándo usar**:
- Preguntas sobre riesgos (heladas, sequías, calor)
- Planificación preventiva
- Planes de contingencia
**Palabras clave**: "riesgo", "helada", "sequía", "calor extremo", "protección", "contingencia"
**Herramientas**: historical_weather_summary (30-365 días), weather_forecast
**Salida**: Nivel de riesgo (Bajo/Moderado/Alto/Crítico) + plan de mitigación

### 💰 'supply_chain' - Comercialización
**Cuándo usar**:
- Preguntas sobre precios de mercado
- Timing de cosecha/venta
- Estrategias de comercialización
**Palabras clave**: "precio", "vender", "mercado", "cuánto vale", "comercializar"
**Herramientas**: get_market_price (API mock)
**Salida**: Precio actual + tendencia + recomendación de timing

### 🌿 'sustainability' - Agricultura Sostenible
**Cuándo usar**:
- Usuario menciona: "orgánico", "sostenible", "ecológico", "certificación", "bio"
- Preguntas sobre alternativas a químicos
- Manejo integrado de plagas (MIP/IPM)
- Control biológico, compost, fertilizantes orgánicos
- Certificación orgánica, sello verde, fair trade
- **CRÍTICO**: Validación de químicos de otros agentes

**REGLA ESPECIAL**: Si 'production' o 'risk' recomendaron pesticidas/fertilizantes químicos, **SIEMPRE** enrutar a 'sustainability' para evaluar alternativas orgánicas ANTES de FINISH.

**Palabras clave**: "orgánico", "sostenible", "bio", "certificación", "sin químicos", "natural", "MIP", "control biológico"
**Herramientas**: knowledge_base (prácticas sostenibles, IPM, certificaciones)
**Salida**: Veredicto (Aprobado/Rechazado/Ajustes) + alternativas orgánicas

---

## REGLAS CRÍTICAS

1. **Campo `content`**: SOLO se llena cuando `next_agent = "FINISH"`. En todos los demás casos, `content = ""`

2. **Campo `info_for_next_agent`**: Incluye:
   - Contexto relevante de agentes previos
   - Nombre de parcela si el usuario lo mencionó (NO inventes IDs)
   - Resumen de lo que se necesita del próximo agente
   - Si sustainability debe validar: "Agente X recomendó [químico]. Evaluar alternativa."

3. **Validación de Sustainability**: 
   - Si detectas químicos en respuesta de production/risk Y sustainability no ha revisado → Enrutar a sustainability
   - Si sustainability ya revisó → Permitir FINISH

4. **No inventes datos**:
   - No inventes IDs de parcelas
   - No asumas información que el usuario no dio
   - Si falta info, pregunta en FINISH

5. **Prioridades**:
   1. Imagen → vision
   2. Químicos sin validar → sustainability
   3. Consulta específica → agente apropiado
   4. Info completa → FINISH

---

## CONTEXTO ACTUAL
- **User ID**: {state.get('user_id')}
- **Imagen presente**: {'Sí' if has_image else 'No'}
- **Último agente**: {last_agent}
- **Historial de agentes**: {agent_history}
- **Razonamiento previo**: {reasoning_prev}
- **Último mensaje contiene químicos**: {_contains_chemical_recommendation(last_message_content)}

---

## EJEMPLOS DE DECISIÓN

**Ejemplo 1: Usuario con imagen**
Input: [imagen] "¿Qué tiene mi planta?"
Decisión: next_agent = "vision" (prioridad imagen)

**Ejemplo 2: Production recomendó químico**
Production dijo: "Aplicar Imidacloprid para pulgones"
Historial: ["production"]
Decisión: next_agent = "sustainability" (validar químico)
info_for_next_agent: "Production recomendó Imidacloprid. Evaluar alternativa orgánica."

**Ejemplo 3: Sustainability ya validó**
Historial: ["production", "sustainability"]
Sustainability dijo: "Usar Chrysoperla carnea en vez de Imidacloprid"
Decisión: next_agent = "FINISH"
content: "Recomendación final: [síntesis de sustainability]"

**Ejemplo 4: Falta información del usuario**
Water preguntó: "¿Qué tipo de cultivo tienes?"
Decisión: next_agent = "FINISH"
content: "Necesito saber el tipo de cultivo para calcular necesidades de agua. ¿Es maíz, café, tomate...?"

**Ejemplo 5: Coordinación entre agentes**
Production identificó estrés hídrico por NDWI bajo
Decisión: next_agent = "water"
info_for_next_agent: "Production detectó estrés hídrico (NDWI < -0.3). Calcular necesidades de riego."

---

Analiza cuidadosamente el historial completo antes de decidir. Tu objetivo es resolver la consulta del usuario de la manera más eficiente posible, con el mínimo de pasos, pero asegurando calidad y validación de sostenibilidad cuando aplique.
"""
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])

    # Invocar LLM con estructura
    structured_llm = prompt | llm_supervisor.with_structured_output(
        SupervisorDecision)

    try:
        # Validar si se debe forzar enrutamiento a sustainability
        if _should_validate_sustainability(last_agent, last_message_content, agent_history):
            print(
                f"-- VALIDACIÓN FORZADA: Enrutando a sustainability para revisar químicos --")
            return {
                "next": "sustainability",
                "reasoning": f"El agente {last_agent} recomendó químicos sintéticos. Validación de sostenibilidad requerida.",
                "info_next_agent": f"El agente {last_agent} hizo recomendaciones que incluyen químicos sintéticos. Evaluar si existen alternativas orgánicas equivalentes antes de aprobar."
            }

        # Decisión normal del supervisor
        response = await structured_llm.ainvoke({"messages": state["messages"]})

        # Logging
        print(f"-- next_agent: {response.next_agent} --")
        print(f"-- reasoning: {response.reasoning} --")
        print(f"-- info_for_next_agent: {response.info_for_next_agent} --\n")

        if response.next_agent == 'FINISH':
            print(
                f"-- content (respuesta final): {response.content[:100]}... --\n")
            return {
                "next": response.next_agent,
                "reasoning": response.reasoning,
                "info_next_agent": response.info_for_next_agent,
                "agent_history": [],  # Reset del historial al finalizar
                "messages": [AIMessage(content=response.content, name="supervisor")]
            }
        else:
            return {
                "next": response.next_agent,
                "reasoning": response.reasoning,
                "info_next_agent": response.info_for_next_agent
            }

    except Exception as e:
        print(f"ERROR en supervisor: {e}")
        error_msg = "Disculpa, ocurrió un error al procesar tu solicitud. Por favor, intenta reformular tu pregunta."
        return {
            "messages": [AIMessage(content=error_msg, name="supervisor")],
            "next": "FINISH"
        }
