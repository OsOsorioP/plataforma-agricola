from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import users, parcels, chat, auth, mock_data, monitoring, alerts

app = FastAPI(
    title="Plataforma Multiagrente para Agricultura Sostenible",
    description="API para gestionar la interacción entre agricultores y agentes de IA.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True, 
    allow_methods=["*"],    
    allow_headers=["*"],    
    expose_headers=["Content-Type"]
)

app.include_router(router=users.router, prefix="/users", tags=["Users"])
app.include_router(router=parcels.router, prefix="/parcels", tags=["Parcels"])
app.include_router(router=chat.router, prefix="/chat", tags=["Chat"])
app.include_router(router=auth.router, tags=["Authentication"])
app.include_router(mock_data.router, prefix="/mock", tags=["Mock Data"])
app.include_router(monitoring.router, prefix="/admin", tags=["Admin"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])

@app.get("/")
def read_root():
    """
    Endpoint de bienvenida
    """
    return {"message":"Hello World."}