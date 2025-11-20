import { StyleSheet, View, ScrollView, RefreshControl, FlatList } from 'react-native'
import React, { useEffect, useState } from 'react'
import ScreenWrapper from '@/components/layout/ScreenWrapper'
import Header from '@/components/layout/Header'
import Typo from '@/components/ui/Typo'
import { colors, spacingX, spacingY } from '@/constants/theme'
import { useAuth } from '@/context/AuthContext'
import { getMyAlerts } from '@/services/dashboardService'
import { Alert } from '@/types/dashboard'
import AlertCard from '@/components/dashboard/AlertCard'
import Loading from '@/components/ui/Loading'
import { verticalScale } from '@/utils/styling'

export default function DashboardScreen() {
    const { user } = useAuth()
    const [alerts, setAlerts] = useState<Alert[]>([])
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)

    const loadData = async () => {
        try {
            const alertsData = await getMyAlerts()
            setAlerts(alertsData)
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
                    style={{marginBottom: spacingY._20}}
                />

                <ScrollView 
                    showsVerticalScrollIndicator={false}
                    refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
                >
                    {/* Sección de Resumen (KPIs Rápidos - Simulación Visual) */}
                    <View style={styles.section}>
                        <Typo size={20} fontWeight="700" style={{marginBottom: spacingY._15}}>
                            Estado de tus Cultivos
                        </Typo>
                        <View style={styles.statsRow}>
                            <View style={[styles.statCard, {backgroundColor: '#dcfce7'}]}>
                                <Typo size={24} fontWeight="bold" color="#166534">OK</Typo>
                                <Typo size={12} color="#166534">Salud General</Typo>
                            </View>
                            <View style={[styles.statCard, {backgroundColor: '#e0f2fe'}]}>
                                <Typo size={24} fontWeight="bold" color="#075985">{alerts.length}</Typo>
                                <Typo size={12} color="#075985">Alertas Activas</Typo>
                            </View>
                            <View style={[styles.statCard, {backgroundColor: '#fef9c3'}]}>
                                <Typo size={24} fontWeight="bold" color="#854d0e">--</Typo>
                                <Typo size={12} color="#854d0e">Cosecha Est.</Typo>
                            </View>
                        </View>
                    </View>

                    {/* Sección de Alertas */}
                    <View style={styles.section}>
                        <Typo size={18} fontWeight="600" style={{marginBottom: spacingY._10}}>
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

                    {/* Aquí iría la sección de KPIs detallados en el futuro */}
                     <View style={styles.section}>
                        <Typo size={18} fontWeight="600" style={{marginBottom: spacingY._10}}>
                            Métricas Recientes (KPIs)
                        </Typo>
                        <View style={styles.emptyState}>
                            <Typo size={14} color={colors.neutral400} style={{textAlign: 'center'}}>
                                Usa el chat para registrar métricas o conecta sensores para ver la evolución aquí.
                            </Typo>
                        </View>
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