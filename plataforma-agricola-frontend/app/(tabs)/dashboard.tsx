import { StyleSheet, View, ScrollView, RefreshControl, TouchableOpacity } from 'react-native'
import React, { useEffect, useState } from 'react'
import ScreenWrapper from '@/components/layout/ScreenWrapper'
import Header from '@/components/layout/Header'
import Typo from '@/components/ui/Typo'
import { colors, spacingX, spacingY } from '@/constants/theme'
import { useAuth } from '@/context/AuthContext'
import { getMyAlerts, getKPIHistory } from '@/services/dashboardService' // Ya no importamos syncSatelliteData
import { Alert, KPIMetric } from '@/types/dashboard'
import { getParcels } from '@/services/parcelService'
import { Parcel } from '@/types/parcels'
import AlertCard from '@/components/dashboard/AlertCard'
import Loading from '@/components/ui/Loading'
import KPIGraph from '@/components/dashboard/KPIGraph';
import { scale } from '@/utils/styling'

export default function DashboardScreen() {
    const { user } = useAuth()
    const [alerts, setAlerts] = useState<Alert[]>([])
    const [parcels, setParcels] = useState<Parcel[]>([])
    
    const [selectedParcel, setSelectedParcel] = useState<Parcel | null>(null)
    
    const [kpiDataNDVI, setKpiDataNDVI] = useState<KPIMetric[]>([])
    const [kpiDataWater, setKpiDataWater] = useState<KPIMetric[]>([])
    
    const [loading, setLoading] = useState(true)
    const [graphLoading, setGraphLoading] = useState(false)
    const [refreshing, setRefreshing] = useState(false)

    const loadInitialData = async () => {
        try {
            const [alertsData, parcelsData] = await Promise.all([
                getMyAlerts(),
                getParcels()
            ]);
            
            setAlerts(alertsData);
            setParcels(parcelsData);

            if (parcelsData.length > 0 && !selectedParcel) {
                setSelectedParcel(parcelsData[0]);
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }

    useEffect(() => {
        const loadKPIs = async () => {
            if (!selectedParcel) return;
            
            setGraphLoading(true);
            try {
                const ndvi = await getKPIHistory(selectedParcel.id, 'SOIL_HEALTH_NDVI');
                const water = await getKPIHistory(selectedParcel.id, 'WATER_EFFICIENCY');
                setKpiDataNDVI(ndvi);
                setKpiDataWater(water);
            } catch (error) {
                console.error("Error cargando KPIs", error);
            } finally {
                setGraphLoading(false);
            }
        };

        loadKPIs();
    }, [selectedParcel]); 

    useEffect(() => {
        loadInitialData();
    }, []);

    const onRefresh = () => {
        setRefreshing(true);
        loadInitialData();
        if (selectedParcel) {
            const current = selectedParcel;
            setSelectedParcel(null); 
            setTimeout(() => setSelectedParcel(current), 10);
        }
    }

    return (
        <ScreenWrapper showPattern={true} bgOpacity={0.1}>
            <View style={styles.container}>
                <Header
                    title={`Hola, ${user?.username || 'Agricultor'}`}
                    style={{ marginBottom: spacingY._20 }}
                />

                <ScrollView
                    showsVerticalScrollIndicator={false}
                    refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
                >
                    <View style={styles.section}>
                        <Typo size={18} fontWeight="600" style={{ marginBottom: spacingY._10 }}>
                            Alertas Activas
                        </Typo>
                        {loading ? <Loading /> : alerts.length === 0 ? (
                            <View style={styles.emptyState}>
                                <Typo color={colors.neutral400}>Sin alertas pendientes.</Typo>
                            </View>
                        ) : (
                            alerts.map(alert => <AlertCard key={alert.id} alert={alert} />)
                        )}
                    </View>

                    <View style={styles.section}>
                        <Typo size={18} fontWeight="600" style={{ marginBottom: spacingY._10 }}>
                            Monitoreo Satelital
                        </Typo>

                        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{marginBottom: 15}}>
                            {parcels.map((p) => (
                                <TouchableOpacity 
                                    key={p.id}
                                    style={[
                                        styles.parcelChip, 
                                        selectedParcel?.id === p.id && styles.parcelChipSelected
                                    ]}
                                    onPress={() => setSelectedParcel(p)}
                                >
                                    <Typo 
                                        size={13} 
                                        fontWeight={selectedParcel?.id === p.id ? "600" : "400"}
                                        color={selectedParcel?.id === p.id ? colors.white : colors.text}
                                    >
                                        {p.name}
                                    </Typo>
                                </TouchableOpacity>
                            ))}
                        </ScrollView>

                        {graphLoading ? (
                            <View style={{height: 200, justifyContent:'center'}}><Loading /></View>
                        ) : (
                            <>
                                <KPIGraph
                                    title="Salud del Cultivo (NDVI)"
                                    data={kpiDataNDVI}
                                    color={colors.green}
                                />
                                <KPIGraph
                                    title="Eficiencia Hídrica (NDWI)"
                                    data={kpiDataWater}
                                    color={colors.primary}
                                />
                                <Typo size={12} color={colors.neutral400} style={{textAlign:'center', marginTop: 10}}>
                                    Datos generados automáticamente por el Asistente IA.
                                </Typo>
                            </>
                        )}
                    </View>
                </ScrollView>
            </View>
        </ScreenWrapper>
    )
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        paddingHorizontal: spacingX._20,
        paddingTop: spacingY._10
    },
    section: {
        marginBottom: spacingY._25
    },
    emptyState: {
        padding: spacingY._20,
        backgroundColor: colors.white,
        borderRadius: scale(15),
        alignItems: 'center',
        borderStyle: 'dashed',
        borderWidth: 1,
        borderColor: colors.neutral300
    },
    parcelChip: {
        paddingVertical: 8,
        paddingHorizontal: 16,
        backgroundColor: colors.neutral100,
        borderRadius: scale(10),
        marginRight: 10,
        borderWidth: 1,
        borderColor: colors.neutral200
    },
    parcelChipSelected: {
        backgroundColor: colors.black,
        borderColor: colors.black
    }
})