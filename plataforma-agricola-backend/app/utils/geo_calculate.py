import json
import numpy as np
from datetime import date
from app.cdse_auth import CDSE_AUTHENTICATOR
from shapely.geometry import shape, mapping
from sentinelhub import SentinelHubRequest, DataCollection, BBox, CRS, MimeType, SHConfig

def configure_cdse_sh_config(token: str) -> SHConfig:
    """Configura el objeto SHConfig de sentinelhub-py para usar el token CDSE."""
    config = SHConfig()
    return config


def calculate_average_ndvi(geojson_str: str, date_from: date, date_to: date) -> float:
    """
    Función interna que llama a la API de CDSE/Sentinel Hub para calcular el NDVI promedio.
    """
    # 1. Obtener el Token
    try:
        cdse_token = CDSE_AUTHENTICATOR.get_token()
        sh_config = configure_cdse_sh_config(cdse_token)
    except Exception as e:
        print(f"Error de autenticación o configuración: {e}")
        return -999.0

    # 2. Configurar y Ejecutar la Solicitud (Lógica Conceptual)
    try:
        geom = shape(json.loads(geojson_str))
        bbox = BBox(geom.bounds, crs=CRS.WGS84)

        # Script de Evaluación para NDVI
        evalscript_ndvi = """
        // Script de evaluación para el procesamiento de Sentinel-2 L2A (B4=Rojo, B8=NIR)
        function setup() {
            return {
                input: [{ bands: ["B4", "B8"] }],
                output: { bands: 1, sampleType: "FLOAT32" }
            };
        }

        function evaluatePixel(samples) {
            let ndvi = (samples.B8 - samples.B4) / (samples.B8 + samples.B4);
            return [ndvi];
        }
        """

        # Solicitud al servicio de procesamiento (Requiere la configuración real)
        request = SentinelHubRequest(
            evalscript=evalscript_ndvi,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_range=(date_from.isoformat(), date_to.isoformat()),
                    # Puedes agregar 'maxcc=0.1' para un máximo de 10% de cobertura de nubes
                )
            ],
            responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
            bbox=bbox,
            geometry=mapping(geom), # Recorta a la geometría de la parcela
            config=sh_config
        )
        
        # 3. Llamada al API real (Comentar/Descomentar según la prueba)
        data = request.get_data() 
        ndvi_array = data[0].squeeze() 
        
        # 4. Procesamiento
        valid_ndvi = ndvi_array[(ndvi_array > 0.1) & (np.isfinite(ndvi_array))]
        
        if valid_ndvi.size == 0:
            return 0.0
        
        average_ndvi = np.mean(valid_ndvi)
        return float(average_ndvi)

    except Exception as e:
        print(f"Error en la solicitud de datos satelitales (CDSE/SH): {e}")
        return -999.0