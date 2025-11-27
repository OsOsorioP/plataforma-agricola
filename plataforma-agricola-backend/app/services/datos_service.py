"""
Futura implementación - si es conveniente 
"""
import pandas as pd
from sodapy import Socrata

from app.core.config import DATOS_GOV_API_KEY, DATOS_GOV_PASSWORD, DATOS_GOV_USER

# Example authenticated client (needed for non-public datasets):
client = Socrata(
                  domain="www.datos.gov.co",
                  app_token=DATOS_GOV_API_KEY,
                  username=DATOS_GOV_USER,
                  password=DATOS_GOV_PASSWORD
                )

# First 2000 results, returned as JSON from API / converted to Python list of
# dictionaries by sodapy.
results = client.get("66x9-24rb", limit=2000)

# Convert to pandas DataFrame
results_df = pd.DataFrame.from_records(results)