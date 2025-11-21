import { StyleSheet, View, Dimensions } from 'react-native'
import React from 'react'
import { LineChart } from "react-native-chart-kit";
import Typo from '../ui/Typo';
import { colors, radius, spacingY } from '@/constants/theme';
import { KPIMetric } from '@/types/dashboard';

interface KPIGraphProps {
    data: KPIMetric[];
    title: string;
    color?: string;
}

export default function KPIGraph({ data, title, color = colors.primaryDark }: KPIGraphProps) {
    const screenWidth = Dimensions.get("window").width;

    // Si no hay datos, mostramos un mensaje
    if (!data || data.length === 0) {
        return (
            <View style={styles.container}>
                <Typo fontWeight="600" size={16}>{title}</Typo>
                <View style={styles.emptyState}>
                    <Typo size={14} color={colors.neutral400}>Sin datos suficientes</Typo>
                </View>
            </View>
        )
    }

    // Preparamos los datos para la gráfica
    // Tomamos los últimos 6 registros para que no se sature
    const recentData = data.slice(-6); 
    
    const chartData = {
        labels: recentData.map(d => {
            const date = new Date(d.timestamp);
            return `${date.getDate()}/${date.getMonth() + 1}`; // Formato DD/MM
        }),
        datasets: [
            {
                data: recentData.map(d => d.value),
                color: (opacity = 1) => color, 
                strokeWidth: 2 
            }
        ],
    };

    return (
        <View style={styles.container}>
            <Typo fontWeight="600" size={16} style={{marginBottom: 10}}>{title}</Typo>
            
            <LineChart
                data={chartData}
                width={screenWidth - 40} // Ancho de pantalla menos padding
                height={220}
                chartConfig={{
                    backgroundColor: "#ffffff",
                    backgroundGradientFrom: "#ffffff",
                    backgroundGradientTo: "#ffffff",
                    decimalPlaces: 1, 
                    color: (opacity = 1) => color,
                    labelColor: (opacity = 1) => colors.neutral400,
                    style: {
                        borderRadius: 16
                    },
                    propsForDots: {
                        r: "4",
                        strokeWidth: "2",
                        stroke: color
                    }
                }}
                bezier // Hace la línea curva y suave
                style={{
                    marginVertical: 8,
                    borderRadius: 16
                }}
            />
        </View>
    )
}

const styles = StyleSheet.create({
    container: {
        backgroundColor: colors.white,
        padding: 15,
        borderRadius: radius.full, // O 20 si radius.full es muy redondo
        marginBottom: spacingY._15,
        elevation: 2,
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    emptyState: {
        height: 150,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: colors.neutral50,
        borderRadius: 10,
        marginTop: 10
    }
})