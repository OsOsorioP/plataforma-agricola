from langchain.tools import tool

from app.utils.helper import _safe_json_response

import requests


@tool
def get_market_price(product_name: str) -> str:
    """
    Obtiene precio de mercado actual y tendencia para un producto agrícola.
    Nota: Esta es una API mock local. En producción, usar API real de precios.
    """
    try:
        response = requests.get(
            f"http://127.0.0.1:8000/mock/market-prices",
            params={"product_name": product_name},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()

        return _safe_json_response(True, {
            "product": product_name,
            "price_usd_kg": data['price_usd_kg'],
            "trend": data['trend'],
            "last_update": data.get('last_update', 'N/A'),
            "summary": f"${data['price_usd_kg']} USD/kg - Tendencia: {data['trend']}"
        })

    except requests.exceptions.Timeout:
        return _safe_json_response(False, error="Timeout al consultar precios")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return _safe_json_response(False,
                                       error=f"No hay datos de precios para '{product_name}'")
        return _safe_json_response(False, error=f"Error HTTP: {e}")
    except Exception as e:
        return _safe_json_response(False, error=f"Error al obtener precios: {str(e)}")