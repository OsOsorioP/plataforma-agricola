from fastapi import FastAPI

app = FastAPI(
    title="Plataforma Multiagrente para Agricultura Sostenible",
    description="API para gestionar la interacción entre agricultores y agentes de IA.",
    version="0.1.0"
)

@app.get("/")
def read_root():
    """
    Endpoint de bienvenida
    """
    return {"message":"Esta funcionando."}