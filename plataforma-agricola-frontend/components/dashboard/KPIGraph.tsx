import { StyleSheet, View, Dimensions } from 'react-native'
import React from 'react'
import { LineChart } from "react-native-chart-kit";
import Typo from '../ui/Typo';
import { colors, spacingY } from '@/constants/theme';
import { KPIMetric } from '@/types/dashboard';
import { scale, verticalScale } from '@/utils/styling';

interface KPIGraphProps {
    data: KPIMetric[];
    title: string;
    color?: string;
}

export default function KPIGraph({ data, title, color = colors.primaryDark }: KPIGraphProps) {
    const screenWidth = Dimensions.get("screen").width

    if (!data || data.length === 0) {
        return (
            <View style={styles.container}>
                <Typo fontWeight="600" size={16}>{title}</Typo>
                <View style={styles.emptyState}>
                    <Typo size={14} color={colors.neutral400}>Consulta a tu asistente para generar datos.</Typo>
                </View>
            </View>
        )
    }

    // Mostrar solo los últimos 6 puntos para que se vea bien
    const recentData = data.slice(-6); 
    
    const chartData = {
        labels: recentData.map(d => {
            const date = new Date(d.timestamp);
            return `${date.getDate()}/${date.getMonth() + 1}/${date.getFullYear()}`;
        }),
        datasets: [{
            data: recentData.map(d => d.value),
            color: (opacity = 1) => color, 
            strokeWidth: 2 
        }],
    };

    return (
        <View style={styles.container}>
            <Typo fontWeight="600" size={16} style={{marginBottom: 10}}>{title}</Typo>
            <LineChart
                data={chartData}
                width={screenWidth - 75}
                height={200}
                chartConfig={{
                    backgroundColor: "#ffffff",
                    backgroundGradientFrom: "#ffffff",
                    backgroundGradientTo: "#ffffff",
                    decimalPlaces: 2, 
                    color: (opacity = 1) => color,
                    labelColor: (opacity = 1) => colors.neutral400,
                    style: { borderRadius: 16 },
                    propsForDots: { r: "4", strokeWidth: "2", stroke: color }
                }}
                bezier
                style={{ marginVertical: 8, borderRadius: 10 }}
            />
        </View>
    )
}

const styles = StyleSheet.create({
    container: {
        backgroundColor: colors.white,
        padding: verticalScale(15),
        borderRadius: scale(10),
        marginBottom: spacingY._15,
        elevation: 2,
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    emptyState: {
        height: 100,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: colors.neutral50,
        borderRadius: scale(10),
        marginTop: 10
    }
})