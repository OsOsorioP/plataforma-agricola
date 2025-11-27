from langchain.tools import tool
from langchain_classic.tools.retriever import create_retriever_tool

from app.db.session import SessionLocal
from app.db.models.parcel import Parcel
from app.db.models.kpi import KPIMetric
from app.services.rag.store import vectorstore_service
from app.utils.helper import _safe_json_response 

from app.services.sentinel_service import (
    get_ndvi,
    get_nbr,
    get_bsi,
    get_evi,
    get_fapar,
    get_gci,
    get_lai,
    get_msavi,
    get_ndwi,
    get_savi,
)

from datetime import date


@tool
def get_parcel_health_indices(parcel_id: int, start_date: str, end_date: str) -> str:
    """
    Obtiene índices como NDVI mediante datos satelitales.
    Y guarda los resultados clave como KPIs históricos.

    Parámetros:
    - parcel_id: ID de la parcela
    - start_date: Fecha inicio 'YYYY-MM-DD'
    - end_date: Fecha fin 'YYYY-MM-DD'
    """
    db = SessionLocal()
    try:
        # Validar formato de fechas
        try:
            date_from = date.fromisoformat(start_date)
            date_to = date.fromisoformat(end_date)
        except ValueError:
            return _safe_json_response(False,
                                       error="Fechas inválidas. Usar formato ISO: YYYY-MM-DD",
                                       data={"example": "2025-01-15"})

        # Validar rango temporal
        if date_from > date_to:
            return _safe_json_response(False,
                                       error="La fecha de inicio debe ser anterior a la fecha de fin")

        days_diff = (date_to - date_from).days
        if days_diff > 365:
            return _safe_json_response(False,
                                       error="El rango máximo es 365 días",
                                       data={"days_requested": days_diff})

        # Obtener parcela
        parcel = db.query(Parcel).filter(
            Parcel.id == parcel_id
        ).first()

        if not parcel:
            return _safe_json_response(False, error=f"Parcela {parcel_id} no encontrada")

        if not parcel.geometry:
            return _safe_json_response(False,
                                       error=f"La parcela {parcel_id} no tiene geometría definida")

        # Calcular NDVI
        ndvi_results = get_ndvi(parcel.geometry, start_date, end_date)
        ndwi_results = get_ndwi(parcel.geometry, start_date, end_date)
        evi_results = get_evi(parcel.geometry, start_date, end_date)
        savi_results = get_savi(parcel.geometry, start_date, end_date)
        msavi_results = get_msavi(parcel.geometry, start_date, end_date)
        bsi_results = get_bsi(parcel.geometry, start_date, end_date)
        nbr_results = get_nbr(parcel.geometry, start_date, end_date)
        gci_results = get_gci(parcel.geometry, start_date, end_date)
        lai_results = get_lai(parcel.geometry, start_date, end_date)
        fapar_results = get_fapar(parcel.geometry, start_date, end_date)

        ndvi_mean = ndvi_results[1]['mean']
        ndwi_mean = ndwi_results[1]['mean']

        # Guardamos NDVI
        kpi_ndvi = KPIMetric(
            parcel_id=parcel.id,
            kpi_name="SOIL_HEALTH_NDVI",
            value=ndvi_mean
        )
        db.add(kpi_ndvi)

        # Guardamos NDWI (Eficiencia Hídrica)
        kpi_ndwi = KPIMetric(
            parcel_id=parcel.id,
            kpi_name="WATER_EFFICIENCY",
            value=ndwi_mean
        )
        db.add(kpi_ndwi)

        db.commit()

        return _safe_json_response(True, {
            "parcel_id": parcel_id,
            "parcel_name": parcel.name,
            "date_range": {
                "start": start_date,
                "end": end_date,
                "days": days_diff
            },
            "NDVI_stats": ndvi_results[1],
            "NDWI_stats": ndwi_results[1],
            "EVI_stats": evi_results[1],
            "SAVI_stats": savi_results[1],
            "MSAVI_stats": msavi_results[1],
            "BSI_stats": bsi_results[1],
            "NBR_stats": nbr_results[1],
            "GCI_stats": gci_results[1],
            "LAI_stats": lai_results[1],
            "FAPAR_stats": fapar_results[1]
        })

    except Exception as e:
        return _safe_json_response(False, error=f"Error al calcular índices: {str(e)}")
    finally:
        db.close()

retriever = vectorstore_service.get_retriever()
knowledge_base_tool = create_retriever_tool(
    retriever,
    "knowledge_base_search",
    "Busca información específica sobre prácticas agrícolas, manejo de cultivos, "
    "fertilizantes, control de plagas, técnicas de siembra, y optimización de producción "
    "en la base de conocimiento especializada."
)