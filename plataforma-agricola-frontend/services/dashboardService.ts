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

export const getKPIHistory = async (parcelId: number, kpiName?: string): Promise<KPIMetric[]> => {
    try {
        let url = `/kpi/parcels/${parcelId}/history`;
        if (kpiName) {
            url += `?kpi_name=${kpiName}`;
        }
        const response = await apiClient.get<KPIMetric[]>(url);
        return response.data;
    } catch (error) {
        console.error("Error fetching KPI history:", error);
        return [];
    }
};