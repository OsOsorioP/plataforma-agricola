from fastapi import APIRouter
from app.api.v1.endpoints import auth, chat, parcels, kpi, users, alerts, monitoring, validation, mock_data

api_router = APIRouter()
api_router.include_router(router=users.router, prefix="/users", tags=["Users"])
api_router.include_router(router=parcels.router, prefix="/parcels", tags=["Parcels"])
api_router.include_router(router=chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(router=auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(mock_data.router, prefix="/mock", tags=["Mock Data"])
api_router.include_router(monitoring.router, prefix="/admin", tags=["Admin"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(kpi.router, prefix="/kpi", tags=["KPIs"])
api_router.include_router(validation.router, prefix="/validate", tags=["Validation"])
