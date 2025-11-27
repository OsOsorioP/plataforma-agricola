import re

def extract_diagnosis_from_output(output: str) -> dict:
    """
    Extrae el diagnóstico y confianza del output del Vision Agent
    """
    data = {
        'diagnosis': None,
        'confidence': 0.5  # Default si no se encuentra
    }
    
    # Buscar diagnóstico principal
    patterns = [
        r'DIAGNÓSTICO PRINCIPAL[:\s]*([^\n]+)',
        r'Diagnóstico[:\s]*([^\n]+)',
        r'\*\*([^*]+)\*\*.*Confianza',  # Formato con bold
    ]
    
    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            data['diagnosis'] = match.group(1).strip()
            break
    
    # Si no encuentra patrón, usar primeras palabras después de emoji o marcador
    if not data['diagnosis']:
        # Buscar después de 🎯 o similar
        match = re.search(r'🎯[:\s]*([^\n]+)', output)
        if match:
            data['diagnosis'] = match.group(1).strip()
    
    # Buscar confianza
    confidence_patterns = [
        r'Confianza[:\s]*.*?(\d+)%',
        r'(\d+)%.*confianza',
        r'[🟢🟡🔴]\s*(\d+)%',
    ]
    
    for pattern in confidence_patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            data['confidence'] = int(match.group(1)) / 100.0
            break
    
    return data


def analyze_image_conditions(image_base64: str) -> dict:
    """
    Analiza condiciones básicas de la imagen
    """
    import base64
    
    # Decodificar para obtener tamaño
    try:
        image_bytes = base64.b64decode(image_base64)
        size_kb = len(image_bytes) // 1024
    except:
        size_kb = 0
    
    # Condiciones básicas (podría expandirse con análisis real)
    conditions = {
        'size_kb': size_kb,
        'format': 'jpeg',  # Asumido
        'quality': 'unknown',  # Requeriría análisis de imagen
        'lighting': 'unknown',
        'distance': 'unknown',
        'focus': 'unknown'
    }
    
    return conditions