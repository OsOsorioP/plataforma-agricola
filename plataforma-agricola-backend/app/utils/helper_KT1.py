# ============================================================================
# FUNCIONES AUXILIARES PARA KT1
# ============================================================================

def classify_query_type(query: str, has_image: bool) -> str:
    """
    Clasifica el tipo de consulta para análisis de orquestación
    """
    query_lower = query.lower()
    
    response = ""
    
    if has_image:
        return "diagnostico_visual"
    
    # Consultas de riego
    if any(word in query_lower for word in ['agua', 'riego', 'regar', 'humedad', 'sequia']):
        response = "riego"
    
    # Consultas de producción
    if any(word in query_lower for word in ['salud', 'cultivo', 'planta', 'enfermedad', 'plaga', 'fertilizar']):
        response = "produccion"
    
    # Consultas de precios
    if any(word in query_lower for word in ['precio', 'vender', 'mercado', 'costo']):
        response = "precio"
    
    # Consultas de riesgo
    if any(word in query_lower for word in ['riesgo', 'helada', 'clima', 'alerta']):
        response = "riesgo"
    
    # Consultas de sostenibilidad
    if any(word in query_lower for word in ['organico', 'sostenible', 'certificacion', 'bio']):
        response = "sostenibilidad"
    
    # Multi-dominio si tiene múltiples palabras clave
    keywords_found = 0
    for category in [['agua', 'riego'], ['salud', 'planta'], ['precio'], ['organico'], ['']]:
        if any(word in query_lower for word in category):
            keywords_found += 1
    
    if keywords_found >= 2:
        response = "multi_dominio"
    
    return response


def calculate_minimum_nodes(query_type: str, has_image: bool) -> int:
    """
    Calcula el número mínimo de nodos necesarios para resolver la consulta
    """
    # Mapeo de tipo de consulta a número mínimo de nodos
    minimum_nodes = {
        "diagnostico_visual": 5, # Supervisor -> Vision -> Supervisor -> FINISH
        "riego": 3,              # Supervisor -> Water -> Supervisor -> FINISH
        "produccion": 3,         # Supervisor -> Production -> Supervisor -> FINISH
        "precio": 3,             # Supervisor -> Supply Chain -> Supervisor -> FINISH
        "riesgo": 3,             # Supervisor -> Risk -> Supervisor -> FINISH
        "sostenibilidad": 3,     # Supervisor -> Sustainability -> Supervisor -> FINISH
        "multi_dominio": 5,      # Supervisor -> Agent1 -> Supervisor -> Agent2 -> Supervisor -> FINISH
        "general": 3,            # Por defecto
    }
    
    return minimum_nodes.get(query_type, 3)


def _contains_chemical_recommendation(message_content: str) -> bool:
    """
    Detecta si un mensaje contiene recomendación de químicos
    (Reutilizado del código original)
    """
    content = normalize_message_content(message_content).lower()
    
    chemical_keywords = [
        "clorpirifos", "paraquat", "glifosato", "imidacloprid", "endosulfan",
        "metamidofos", "carbofuran", "monocrotofos", "aldicarb",
        "pesticida", "insecticida", "fungicida", "herbicida", "nematicida",
        "urea", "superfosfato", "cloruro de potasio", "sulfato de amonio",
        "aplicar químico", "producto químico", "fertilizante sintético"
    ]
    
    return any(keyword in content for keyword in chemical_keywords)


def _should_validate_sustainability(last_agent: str, message_content: str, agent_history: list) -> bool:
    """
    Determina si se necesita validación de sostenibilidad
    """
    if "sustainability" in agent_history:
        return False
    
    if last_agent in ["production", "risk"] and _contains_chemical_recommendation(message_content):
        return True
    
    return False


def normalize_message_content(msg):
    """
    Normaliza contenido del mensaje para procesamiento
    """
    if msg is None:
        return ""
    if isinstance(msg, str):
        return msg
    if isinstance(msg, list):
        parts = []
        for item in msg:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                elif "content" in item:
                    parts.append(str(item["content"]))
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return " ".join(parts)
    if isinstance(msg, dict):
        return " ".join([f"{k}: {v}" for k, v in msg.items()])
    return str(msg)