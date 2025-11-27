from sentinelhub import SHConfig
from shapely.geometry import shape, mapping
import json
import numpy as np
from sentinelhub import (
    SentinelHubRequest, DataCollection, SHConfig,
    BBox, CRS, MimeType
)
import matplotlib.pyplot as plt

# ==========================================================
# CONFIGURACIÓN SENTINEL HUB
# ==========================================================


def configure_sh_config() -> SHConfig:
    """Configura el objeto SHConfig de sentinelhub-py para usar el token CDSE."""
    config = SHConfig()
    config.sh_client_id = "6f8d2b81-c7b5-4e29-b63e-be52e32244cb"
    config.sh_client_secret = "O0wMGdyeyBCSxGeFZ3GDSLT4O7P8IfT9"
    return config

config = configure_sh_config()

# ==========================================================
# UTILIDAD: EJECUTAR UN REQUEST MÓDULAR PARA ÍNDICES
# ==========================================================

def run_request(evalscript: str, geojson_str: str, date_from: str, date_to: str, size=(512, 512)):
    geom = shape(json.loads(geojson_str))
    bbox = BBox(geom.bounds, crs=CRS.WGS84)

    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(date_from, date_to),
                mosaicking_order="mostRecent"
            )
        ],
        responses=[
            SentinelHubRequest.output_response("default", MimeType.TIFF)
        ],
        bbox=bbox,
        size=size,
        config=config
    )

    data = request.get_data()[0].squeeze()
    return data


# ==========================================================
# UTILIDAD: CALCULAR ESTADÍSTICAS BÁSICAS
# ==========================================================
def stats(arr):
    arr = arr.astype(float)
    arr = arr[~np.isnan(arr)]
    return {
        "mean": float(np.mean(arr)),
        "max": float(np.max(arr)),
        "min": float(np.min(arr)),
        "std": float(np.std(arr)),
        "p10": float(np.percentile(arr, 10)),
        "p50": float(np.percentile(arr, 50)),
        "p90": float(np.percentile(arr, 90)),
    }


# ==========================================================
# 1️⃣ NDVI – Normalized Difference Vegetation Index
# Mide vigor, salud y biomasa de la vegetación.
# Vegetación sana → NDVI alto.
# ==========================================================
def get_ndvi(bbox, date_from, date_to):
    evalscript = """
    //VERSION=3
    function setup(){return{input:["B04","B08"],output:{bands:1,sampleType:"FLOAT32"}}}
    function evaluatePixel(s){return[(s.B08 - s.B04) / (s.B08 + s.B04)];}
    """
    ndvi = run_request(evalscript, bbox, date_from, date_to)
    return [ndvi, stats(ndvi)]


# ==========================================================
# 2️⃣ NDWI – Water Index
# Mide contenido de humedad superficial y agua libre.
# Verde (B03) vs NIR (B08).
# ==========================================================
def get_ndwi(bbox, date_from, date_to):
    evalscript = """
    //VERSION=3
    function setup(){return{input:["B03","B08"],output:{bands:1,sampleType:"FLOAT32"}}}
    function evaluatePixel(s){return[(s.B03 - s.B08) / (s.B03 + s.B08)];}
    """
    ndwi = run_request(evalscript, bbox, date_from, date_to)
    return [ndwi, stats(ndwi)]


# ==========================================================
# 3️⃣ EVI – Enhanced Vegetation Index
# Mejor que NDVI en zonas con mucha vegetación o aerosoles.
# ==========================================================
def get_evi(bbox, date_from, date_to):
    evalscript = """
    //VERSION=3
    function setup(){return{input:["B02","B04","B08"],output:{bands:1,sampleType:"FLOAT32"}}}
    function evaluatePixel(s){
        return [2.5 * ((s.B08 - s.B04) / (s.B08 + 6*s.B04 - 7.5*s.B02 + 1))];
    }
    """
    evi = run_request(evalscript, bbox, date_from, date_to)
    return [evi, stats(evi)]


# ==========================================================
# 4️⃣ SAVI – Soil Adjusted Vegetation Index
# Reduce el efecto del suelo visible. Ideal para cultivos jóvenes.
# ==========================================================
def get_savi(bbox, date_from, date_to):
    evalscript = """
    //VERSION=3
    function setup(){return{input:["B04","B08"],output:{bands:1,sampleType:"FLOAT32"}}}
    function evaluatePixel(s){
        let L = 0.5;
        return [ ((s.B08 - s.B04) / (s.B08 + s.B04 + L)) * (1 + L) ];
    }
    """
    savi = run_request(evalscript, bbox, date_from, date_to)
    return [savi, stats(savi)]


# ==========================================================
# 5️⃣ MSAVI – Modified SAVI
# Minimiza interferencia del suelo aún más que SAVI.
# Excelente para suelos desnudos y cultivos iniciales.
# ==========================================================
def get_msavi(bbox, date_from, date_to):
    evalscript = """
    //VERSION=3
    function setup(){return{input:["B04","B08"],output:{bands:1,sampleType:"FLOAT32"}}}
    function evaluatePixel(s){
        return [(2*s.B08 + 1 - Math.sqrt((2*s.B08 + 1)**2 - 8*(s.B08 - s.B04))) / 2];
    }
    """
    msavi = run_request(evalscript, bbox, date_from, date_to)
    return [msavi, stats(msavi)]


# ==========================================================
# 6️⃣ BSI – Bare Soil Index
# Detecta niveles de suelo expuesto (erosión, degradación).
# ==========================================================
def get_bsi(bbox, date_from, date_to):
    evalscript = """
    //VERSION=3
    function setup(){return{input:["B02","B04","B08","B11"],output:{bands:1,sampleType:"FLOAT32"}}}
    function evaluatePixel(s){
        return [((s.B11 + s.B04) - (s.B08 + s.B02)) /
                ((s.B11 + s.B04) + (s.B08 + s.B02))];
    }
    """
    bsi = run_request(evalscript, bbox, date_from, date_to)
    return [bsi, stats(bsi)]


# ==========================================================
# 7️⃣ NBR – Normalized Burn Ratio
# Detecta áreas quemadas y estrés severo por calor.
# ==========================================================
def get_nbr(bbox, date_from, date_to):
    evalscript = """
    //VERSION=3
    function setup(){return{input:["B08","B12"],output:{bands:1,sampleType:"FLOAT32"}}}
    function evaluatePixel(s){
        return [(s.B08 - s.B12) / (s.B08 + s.B12)];
    }
    """
    nbr = run_request(evalscript, bbox, date_from, date_to)
    return [nbr, stats(nbr)]


# ==========================================================
# 8️⃣ GCI – Green Chlorophyll Index
# Relacionado con actividad fotosintética y nitrógeno.
# ==========================================================
def get_gci(bbox, date_from, date_to):
    evalscript = """
    //VERSION=3
    function setup(){return{input:["B03","B08"],output:{bands:1,sampleType:"FLOAT32"}}}
    function evaluatePixel(s){
        return [(s.B08 / s.B03) - 1];
    }
    """
    gci = run_request(evalscript, bbox, date_from, date_to)
    return [gci, stats(gci)]


# ==========================================================
# 9️⃣ LAI – Leaf Area Index
# Estima área foliar. Relacionado con biomasa y vigor.
# ==========================================================
def get_lai(bbox, date_from, date_to):
    evalscript = """
    //VERSION=3
    function setup(){return{input:["B08","B04"],output:{bands:1,sampleType:"FLOAT32"}}}
    function evaluatePixel(s){
        return [3.618 * ((s.B08 - s.B04) / (s.B08 + s.B04)) - 0.118];
    }
    """
    lai = run_request(evalscript, bbox, date_from, date_to)
    return [lai, stats(lai)]


# ==========================================================
# 🔟 FAPAR – Fracción de Radiación Fotosintéticamente Activa Absorbida
# Estima energía absorbida por el cultivo. Muy útil en productividad.
# ==========================================================
def get_fapar(bbox, date_from, date_to):
    evalscript = """
    //VERSION=3
    function setup(){return{input:["B04","B08"],output:{bands:1,sampleType:"FLOAT32"}}}
    function evaluatePixel(s){
        let ndvi = (s.B08 - s.B04) / (s.B08 + s.B04);
        return [0.5 * ndvi + 0.5];
    }
    """
    fapar = run_request(evalscript, bbox, date_from, date_to)
    return [fapar, stats(fapar)]
