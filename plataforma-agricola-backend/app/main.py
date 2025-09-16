from fastapi import FastAPI
from app.api import users, parcels

app = FastAPI(
    title="Plataforma Multiagrente para Agricultura Sostenible",
    description="API para gestionar la interacción entre agricultores y agentes de IA.",
    version="0.1.0"
)

app.include_router(router=users.router, prefix="/users", tags=["Users"])
app.include_router(router=parcels.router, prefix="/parcels", tags=["Parcels"])

@app.get("/")
def read_root():
    """
    Endpoint de bienvenida
    """
    return {"message":"Esta funcionando."}