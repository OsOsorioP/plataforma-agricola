import { useAuth } from "@/context/AuthContext";
import { Alerts } from "@/types/alerts";
import { useEffect, useState } from "react";
import { ActivityIndicator, View, Text, StyleSheet, FlatList } from "react-native";
// import { getMyAlerts } from '../services/alerts';

export default function DashboardScreen() {
    const { token } = useAuth();
    const [alerts, setAlerts] = useState<Alerts[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchAlerts = async () => {
            try {
                // const response = await getMyAlerts(token);
                // setAlerts(response.data);
                // Simulamos una alerta para la prueba
                setAlerts([{ id: 1, risk_type: 'HELADA', message: '¡Alerta de Helada! Se pronostica una temperatura mínima de 1°C...', timestamp: new Date().toISOString() }]);
            } catch (error) {
                console.error(error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchAlerts();
    }, [token]);

    if (isLoading) {
        return <ActivityIndicator size="large" />;
    }

    return (
        <View style={styles.container}>
            <Text style={styles.title} >Alertas Proactivas</Text>
            <FlatList
                data={alerts}
                keyExtractor={(item) => item.id.toString()}
                renderItem={({ item }) => (
                    <View style={[styles.alertCard, styles.alertCardFrost]}>
                        <Text style={styles.alertType}>{item.risk_type}</Text>
                        <Text style={styles.alertMessage}>{item.message}</Text>
                        <Text style={styles.alertTime}>{new Date(item.timestamp).toLocaleString()}</Text>
                    </View>
                )}
                ListEmptyComponent={<Text>No tienes alertas nuevas.</Text>}
            />
        </View>
    )
}

const styles = StyleSheet.create({
    container: {},
    title: {},
    alertCard: {},
    alertCardFrost: {},
    alertType: {},
    alertMessage: {},
    alertTime: {},
});