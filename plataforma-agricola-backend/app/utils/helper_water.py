# ============================================================================
# FUNCIONES AUXILIARES PARA EXTRAER DATOS DE KS3
# ============================================================================

import json
import re


def extract_water_calculation_from_tools(tool_outputs: list) -> dict:
    """
    Extrae datos de cálculo hídrico de las respuestas de las herramientas
    """
    data = {
        'etc_theoretical': None,
        'p_eff': None,
        'v_agent': None,
        'crop_type': None,
        'development_stage': None,
        'soil_type': None,
        'irrigation_type': None,
        'ndwi_value': None,
        'days_since_planting': None,
    }
    
    for output in tool_outputs:
        try:
            if isinstance(output, str):
                parsed = json.loads(output)
            else:
                parsed = output
            
            # Extraer de calculate_water_requirements
            if 'etc_mm_day' in parsed:
                data['etc_theoretical'] = parsed['etc_mm_day']
                data['crop_type'] = parsed.get('crop_type')
                data['development_stage'] = parsed.get('growth_stage')
                
                # CAMBIO CRÍTICO: Extraer el valor NETO
                water_reqs = parsed.get('water_requirements', {})
                data['v_agent'] = water_reqs.get('net_ideal_liters_per_day')  # ESTE ES EL CORRECTO
                
                # También guardar P_eff si viene aquí
                if 'effective_precipitation_mm_day' in parsed:
                    data['p_eff'] = parsed['effective_precipitation_mm_day']
            
            # Extraer de get_precipitation_data
            if 'daily_average_mm' in parsed:
                data['p_eff'] = parsed['daily_average_mm']
            
            # Extraer de get_parcel_details
            if 'soil_type' in parsed:
                data['soil_type'] = parsed.get('soil_type')
                data['irrigation_type'] = parsed.get('irrigation_type')
            
            # Extraer NDWI
            if 'NDWI_stats' in parsed:
                data['ndwi_value'] = parsed['NDWI_stats'].get('mean')
        
        except:
            continue
    
    return data


def extract_calculation_from_message(message: str) -> dict:
    """
    Extrae datos de cálculo del mensaje de respuesta del agente
    """
    data = {}
    
    # Patrones para extraer valores numéricos
    patterns = {
        'v_agent': r'(\d+(?:,\d+)?)\s*litros?/d[ií]a',
        'etc': r'ETc[:\s]*(\d+\.?\d*)\s*mm',
        'p_eff': r'precipitaci[óo]n[:\s]*(\d+\.?\d*)\s*mm',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            value_str = match.group(1).replace(',', '')
            data[key] = float(value_str)
    
    return data