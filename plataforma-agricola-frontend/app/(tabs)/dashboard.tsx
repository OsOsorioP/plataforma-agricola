import { StyleSheet, View, ScrollView, RefreshControl, FlatList } from 'react-native'
import React, { useEffect, useState } from 'react'
import ScreenWrapper from '@/components/layout/ScreenWrapper'
import Header from '@/components/layout/Header'
import Typo from '@/components/ui/Typo'
import { colors, spacingX, spacingY } from '@/constants/theme'
import { useAuth } from '@/context/AuthContext'
import { getMyAlerts, getKPIHistory } from '@/services/dashboardService'
import { Alert, KPIMetric } from '@/types/dashboard'
import { getParcels } from '@/services/parcelService'
import AlertCard from '@/components/dashboard/AlertCard'
import Loading from '@/components/ui/Loading'
import KPIGraph from '@/components/dashboard/KPIGraph';

import { verticalScale } from '@/utils/styling'

export default function DashboardScreen() {
    const { user } = useAuth()
    const [alerts, setAlerts] = useState<Alert[]>([])
    const [kpiData, setKpiData] = useState<KPIMetric[]>([])
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)

    const loadData = async () => {
        try {
            const alertsData = await getMyAlerts()
            setAlerts(alertsData)
            const parcels = await getParcels();
            if (parcels.length > 0) {
                const history = await getKPIHistory(parcels[0].id);
                setKpiData(history);
            }
        } catch (error) {
            console.error(error)
        } finally {
            setLoading(false)
            setRefreshing(false)
        }
    }

    useEffect(() => {
        loadData()
    }, [])

    const onRefresh = () => {
        setRefreshing(true)
        loadData()
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
                        <Typo size={20} fontWeight="700" style={{ marginBottom: spacingY._15 }}>
                            Estado de tus Cultivos
                        </Typo>
                        <View style={styles.statsRow}>
                            <View style={[styles.statCard, { backgroundColor: '#dcfce7' }]}>
                                <Typo size={24} fontWeight="bold" color="#166534">OK</Typo>
                                <Typo size={12} color="#166534">Salud General</Typo>
                            </View>
                            <View style={[styles.statCard, { backgroundColor: '#e0f2fe' }]}>
                                <Typo size={24} fontWeight="bold" color="#075985">{alerts.length}</Typo>
                                <Typo size={12} color="#075985">Alertas Activas</Typo>
                            </View>
                            <View style={[styles.statCard, { backgroundColor: '#fef9c3' }]}>
                                <Typo size={24} fontWeight="bold" color="#854d0e">--</Typo>
                                <Typo size={12} color="#854d0e">Cosecha Est.</Typo>
                            </View>
                        </View>
                    </View>

                    <View style={styles.section}>
                        <Typo size={18} fontWeight="600" style={{ marginBottom: spacingY._10 }}>
                            Alertas y Riesgos
                        </Typo>

                        {loading ? (
                            <Loading />
                        ) : alerts.length === 0 ? (
                            <View style={styles.emptyState}>
                                <Typo color={colors.neutral400}>No tienes alertas pendientes.</Typo>
                            </View>
                        ) : (
                            alerts.map(alert => (
                                <AlertCard key={alert.id} alert={alert} />
                            ))
                        )}
                    </View>

                    <View style={styles.section}>
                        <Typo size={18} fontWeight="600" style={{ marginBottom: spacingY._10 }}>
                            Evolución de Sostenibilidad
                        </Typo>

                        <KPIGraph
                            title="Salud del Suelo (NDVI)"
                            data={kpiData.filter(d => d.kpi_name === 'SOIL_HEALTH_NDVI')}
                            color={colors.green}
                        />


                        <KPIGraph
                            title="Eficiencia Hídrica"
                            data={kpiData.filter(d => d.kpi_name === 'WATER_EFFICIENCY')}
                            color={colors.primary}
                        />
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
    statsRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        gap: spacingX._10
    },
    statCard: {
        flex: 1,
        padding: spacingY._15,
        borderRadius: 20,
        alignItems: 'center',
        justifyContent: 'center',
        borderCurve: 'continuous'
    },
    emptyState: {
        padding: spacingY._20,
        backgroundColor: colors.white,
        borderRadius: 15,
        alignItems: 'center',
        borderStyle: 'dashed',
        borderWidth: 1,
        borderColor: colors.neutral300
    }
})