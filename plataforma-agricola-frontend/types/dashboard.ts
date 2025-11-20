export interface Recommendation {
    id: number;
    parcel_id: number;
    agent_source: string;
    recommendation_text: string;
    status: 'pending' | 'applied' | 'discarded';
    timestamp: string;
}

export interface KPIMetric {
    id: number;
    parcel_id: number;
    kpi_name: string;
    value: number;
    timestamp: string;
}

export interface DashboardData {
    alerts: Alert[];
    recentRecommendations: Recommendation[];
    kpiSummary: KPIMetric[];
}

// Reutilizamos el tipo de alerta existente
export interface Alert {
    id: number;
    risk_type: string;
    message: string;
    timestamp: string;
    is_read: boolean;
}