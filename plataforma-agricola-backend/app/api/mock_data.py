from fastapi import APIRouter, HTTPException

router = APIRouter()

# Base de datos simulada de precios
MOCK_PRICES = {
    "tomate": {"price_usd_kg": 1.5, "trend": "estable"},
    "maíz": {"price_usd_kg": 0.3, "trend": "al alza"},
    "papa": {"price_usd_kg": 0.8, "trend": "a la baja"},
}

@router.get("/market-prices")
def get_market_prices(product_name: str):
    """
    Endpoint simulado que devuelve los precios de mercado para un producto.
    """
    product_key = product_name.lower()
    if product_key not in MOCK_PRICES:
        raise HTTPException(status_code=404, detail=f"No se encontraron precios para el producto: {product_name}")
    
    return MOCK_PRICES[product_key]