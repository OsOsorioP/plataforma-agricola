from typing import List, Dict, Set
import re


def detect_chemical_in_message(message: str) -> List[Dict]:
    """
    Detecta si un mensaje contiene recomendación de químico
    Retorna: List of {'name': str, 'category': str, 'eiq': float} o una lista vacía
    """
    print("\n Detectar Quimico \n")
    chemicals_db = {
        'clorpirifos': {'category': 'Ib', 'eiq': 49.8},
        'imidacloprid': {'category': 'II', 'eiq': 37.3},
        'diazinon': {'category': 'Ib', 'eiq': 46.5},
        'cipermetrina': {'category': 'II', 'eiq': 30.9},  
        'thiocyclam hidrogenoxalato': {'category': 'II', 'eiq': 40.0},
        'paraquat': {'category': 'Ia', 'eiq': 62.1},
        'glifosato': {'category': 'III', 'eiq': 15.3},
        'carbofuran': {'category': 'Ia', 'eiq': 64.2},
        'mancozeb': {'category': 'II', 'eiq': 22.7},
        'lambda-cihalotrina': {'category': 'II', 'eiq': 35.8},
        'thiamethoxam': {'category': 'II', 'eiq': 28.9},
        'benomil': {'category': 'II', 'eiq': 51.3},
        'metalaxil': {'category': 'III', 'eiq': 28.4},
        'abamectina': {'category': 'II', 'eiq': 32.4},
        'spinosad': {'category': 'III', 'eiq': 18.6},
        'malathion': {'category': 'II', 'eiq': 33.1},
        'piretrinas': {'category': 'III', 'eiq': 15.0},
        'azadiractina': {'category': 'III', 'eiq': 8.5},
    }

    message_lower = message.lower()
    detected_chemicals = []

    for chemical_name, data in chemicals_db.items():
        # Se usa re.search para encontrar la palabra completa (evita "mid" en "imidacloprid")
        if re.search(r'\b' + re.escape(chemical_name) + r'\b', message_lower):
            # Asegurar que no se dupliquen por si hay múltiples menciones
            if chemical_name not in [d['name'].lower() for d in detected_chemicals]:
                print(f" Quimico detectado: {chemical_name}\n")
                detected_chemicals.append({
                    'name': chemical_name.capitalize(),
                    'category': data['category'],
                    'eiq': data['eiq']
                })

    # Si detectas químicos, retorna la lista. La lógica genérica es más compleja
    # y puede causar falsos positivos, por lo que es mejor confiar en la lista.
    if detected_chemicals:
        return detected_chemicals

    print("Quimico no detectado\n")
    return []  # Retorna lista vacía si no encuentra


def detect_veto_in_output(output: str) -> bool:
    """
    Detecta si el Sustainability Agent vetó la recomendación
    """
    veto_keywords = [
        'rechazo', 'veto', 'no recomiendo', 'no apropiado',
        'altamente tóxico', 'prohibido', 'desaconsejo',
        'no aprobar', 'no permitido', 'alternativa', 'no recomendado',
        'no es apto', 'no es apropiado', 'no sostenible',
    ]

    output_lower = output.lower()
    return any(keyword in output_lower for keyword in veto_keywords)


def extract_alternative_from_output(output: str) -> List[str]:
    """
    Extrae todas las alternativas orgánicas/biológicas propuestas del output.
    Retorna: Lista de strings con las alternativas.
    """
    output_lower = output.lower()
    detected_alternatives: Set[str] = set()

    ORGANIC_EIQ = {
        'bacillus thuringiensis': 6.1,
        'beauveria bassiana': 4.2,
        'chrysoperla': 3.8,
        'trichogramma': 3.5,
        'jabón potásico': 2.1,
        'caldo bordelés': 8.3,
        'bicarbonato': 3.8,
        'extracto': 5.0,  # Valor genérico para extractos
        'trampa': 0.0,
        'crisopas': 3.8,
        'mariquitas': 3.5,
        'avispa parasitoide': 4.0,
        'aceite de neem': 8.5,
        'trampas cromáticas': 0.0,
        'control biológico': 4.0,  # Valor promedio
    }

    ALTERNATIVES_KEYWORDS = list(ORGANIC_EIQ.keys())

    # 1. Búsqueda por palabras clave
    for keyword in ALTERNATIVES_KEYWORDS:
        if keyword in output_lower:
            detected_alternatives.add(keyword.capitalize())

    # 2. Búsqueda por sección (ej. "Alternativa(s) Ecológica(s)")
    match = re.search(
        r'alternativa\(s\) ecológica\(s\)(.*?)(?=\n\d\.|\Z)', output_lower, re.DOTALL)
    if match:
        section_content = match.group(1)
        lines = [line.strip()
                 for line in section_content.split('\n') if line.strip()]
        for line in lines:
            alt_match = re.search(r'[\d\-\*\.]+\s*(.*)', line)
            if alt_match:
                text = alt_match.group(1).strip().capitalize()
                # Filtrar textos muy cortos o genéricos
                if len(text) > 10 and text not in detected_alternatives:
                    detected_alternatives.add(text)

    # Asegurar que no haya duplicados y ordenar
    return sorted(list(detected_alternatives))


def calculate_eiq_for_alternative(alternative: str) -> float:
    """
    Calcula/estima EIQ de la alternativa orgánica
    """
    # Alternativas orgánicas conocidas con EIQ bajo
    organic_eiq = {
        'bacillus thuringiensis': 6.1,
        'beauveria bassiana': 4.2,
        'chrysoperla': 3.8,
        'trichogramma': 3.5,
        'neem': 8.5,
        'jabón potásico': 2.1,
        'caldo bordelés': 8.3,
        'bicarbonato': 3.8,
        'extracto': 5.0,  # Valor genérico para extractos
        'trampa': 0.0,
        'crisopas': 3.8,
        'mariquitas': 3.5,
        'avispa parasitoide': 4.0,
        'aceite de neem': 8.5,
        'trampas cromáticas': 0.0,
        'control biológico': 4.0,  # Valor promedio
        'extracto de ajo': 5.0,
    }

    alternative_lower = alternative.lower()

    for key, eiq in organic_eiq.items():
        if key in alternative_lower:
            return eiq

    # EIQ por defecto para alternativas orgánicas
    return 5.0


def extract_veto_reason(output: str) -> str:
    """
    Extrae la razón del veto
    """
    reasons = []

    keywords = {
        'altamente tóxico': 'Alta toxicidad',
        'neurotóxico': 'Neurotoxicidad',
        'cancerígeno': 'Potencial carcinógeno',
        'prohibido': 'Químico prohibido',
        'categoría ia': 'Categoría Ia - Extremadamente tóxico',
        'categoría ib': 'Categoría Ib - Altamente tóxico',
        'daña polinizadores': 'Daño a polinizadores',
        'residualidad': 'Alta residualidad en suelo',
    }

    output_lower = output.lower()
    for keyword, reason in keywords.items():
        if keyword in output_lower:
            reasons.append(reason)

    return '; '.join(reasons) if reasons else 'Impacto ambiental significativo'
