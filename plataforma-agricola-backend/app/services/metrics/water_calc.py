from app.services.metrics.logger import kpi_logger

from typing import LiteralString
import json
import re

# ============================================================================
# FUNCIONES AUXILIARES PARA EXTRAER DATOS DE KS3
# ============================================================================


def extract_water_calculation_from_tools(tool_outputs: list) -> dict:
    """Extrae datos de cálculo hídrico de las respuestas de las herramientas

    Args:
        tool_outputs (list): _description_

    Returns:
        dict: _description_
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

            if 'etc_mm_day' in parsed:
                data['etc_theoretical'] = parsed['etc_mm_day']
                data['crop_type'] = parsed.get('crop_type')
                data['development_stage'] = parsed.get('growth_stage')

                water_reqs = parsed.get('water_requirements', {})
                data['v_agent'] = water_reqs.get(
                    'net_ideal_liters_per_day')

                if 'effective_precipitation_mm_day' in parsed:
                    data['p_eff'] = parsed['effective_precipitation_mm_day']

            if 'daily_average_mm' in parsed:
                data['p_eff'] = parsed['daily_average_mm']

            if 'soil_type' in parsed:
                data['soil_type'] = parsed.get('soil_type')
                data['irrigation_type'] = parsed.get('irrigation_type')

            if 'NDWI_stats' in parsed:
                data['ndwi_value'] = parsed['NDWI_stats'].get('mean')

        except:
            continue

    return data


def extract_calculation_from_message(message: str) -> dict:
    """Extrae datos de cálculo del mensaje de respuesta del agente

    Args:
        message (str): _description_

    Returns:
        dict: _description_
    """
    
    data = {}

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


def _calculation_kpi_ks3(
    intermediate_steps: list, 
    user_id: int, 
    response_content: str | LiteralString
) -> None:
    """Calcula la kpi KS3

    Args:
        intermediate_steps (list): _description_
        user_id (int): _description_
        response_content (str | LiteralString): _description_
    """
    try:
        tool_outputs = [step[1] for step in intermediate_steps if step[1]]

        calc_data = extract_water_calculation_from_tools(tool_outputs)

        if not calc_data.get('v_agent'):
            message_data = extract_calculation_from_message(response_content)
            calc_data.update(message_data)

        required_fields = ['etc_theoretical', 'v_agent', 'p_eff']
        has_required = all(calc_data.get(field) is not None for field in required_fields)

        if has_required and calc_data.get('crop_type'):

            for output_data in tool_outputs:
                try:
                    parsed = json.loads(output_data) if isinstance(
                        output_data, str) else output_data
                    if 'parcel_id' in parsed:
                        parcel_id = parsed['parcel_id']
                        break
                except:
                    continue

        if parcel_id:
            kpi_logger.log_water_calculation(
                user_id=user_id,
                parcel_id=parcel_id,
                crop_type=calc_data['crop_type'],
                development_stage=calc_data.get(
                    'development_stage', 'unknown'),
                etc_theoretical=calc_data['etc_theoretical'],
                v_agent=calc_data['v_agent'],
                p_eff=calc_data['p_eff'],
                soil_type=calc_data.get('soil_type'),
                irrigation_type=calc_data.get('irrigation_type'),
                ndwi_value=calc_data.get('ndwi_value'),
                days_since_planting=calc_data.get('days_since_planting')
            )

            print(
                f"[KPI] ✓ Cálculo hídrico registrado para parcela {parcel_id}")
            print(
                f"[KPI]   ETc: {calc_data['etc_theoretical']:.2f} mm/día")
            print(f"[KPI]   V_agente: {calc_data['v_agent']:.0f} L/día")
        else:
            print(
                "[KPI-WARNING] Cálculo hídrico sin parcel_id, no registrado")
    except Exception as e:
        print(f"[KPI-WARNING] Error al registrar cálculo hídrico: {e}")