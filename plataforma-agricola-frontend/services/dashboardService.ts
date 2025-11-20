import apiClient from "./apiService";
import { Alert, KPIMetric, Recommendation } from "@/types/dashboard";

// Obtener alertas
export const getMyAlerts = async (): Promise<Alert[]> => {
    try {
        const response = await apiClient.get<Alert[]>("/alerts/");
        return response.data;
    } catch (error) {
        console.error("Error fetching alerts:", error);
        return [];
    }
};

// Registrar una métrica manual (Simulación de sensor o bitácora)
export const logKPIMetric = async (parcelId: number, kpiName: string, value: number) => {
    try {
        const response = await apiClient.post(`/kpi/parcels/${parcelId}/metrics`, {
            kpi_name: kpiName,
            value: value
        });
        return response.data;
    } catch (error) {
        console.error("Error logging KPI:", error);
        throw error;
    }
};

// NOTA: Como no creamos un endpoint específico de "get all recommendations" en el backend todavía,
// vamos a asumir por ahora que las obtenemos a través de las parcelas o las alertas.
// Para este paso, nos centraremos en las ALERTAS que sí tienen endpoint.