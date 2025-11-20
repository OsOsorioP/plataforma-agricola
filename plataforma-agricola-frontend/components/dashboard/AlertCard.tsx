import { StyleSheet, View, TouchableOpacity } from 'react-native'
import React from 'react'
import { Alert } from '@/types/dashboard'
import Typo from '../ui/Typo'
import { colors, radius, spacingX, spacingY } from '@/constants/theme'
import Ionicons from '@expo/vector-icons/Ionicons'
import { verticalScale } from '@/utils/styling'

interface AlertCardProps {
    alert: Alert;
    onPress?: () => void;
}

export default function AlertCard({ alert, onPress }: AlertCardProps) {
    // Color según el tipo de riesgo
    const getIconAndColor = () => {
        switch (alert.risk_type) {
            case 'HELADA': return { icon: 'snow', color: '#3b82f6' }; // Azul
            case 'OLA_DE_CALOR': return { icon: 'sunny', color: '#ef4444' }; // Rojo
            case 'PLAGA': return { icon: 'bug', color: '#eab308' }; // Amarillo
            default: return { icon: 'alert-circle', color: colors.neutral400 };
        }
    }

    const { icon, color } = getIconAndColor();

    return (
        <TouchableOpacity style={styles.card} onPress={onPress}>
            <View style={[styles.iconContainer, { backgroundColor: color + '20' }]}>
                <Ionicons name={icon as any} size={verticalScale(24)} color={color} />
            </View>
            <View style={styles.content}>
                <Typo size={16} fontWeight="600" color={colors.text}>{alert.risk_type}</Typo>
                <Typo size={14} color={colors.neutral400} style={{marginTop: 4}}>
                    {alert.message}
                </Typo>
                <Typo size={12} color={colors.neutral300} style={{marginTop: 8}}>
                    {new Date(alert.timestamp).toLocaleDateString()}
                </Typo>
            </View>
        </TouchableOpacity>
    )
}

const styles = StyleSheet.create({
    card: {
        backgroundColor: colors.white,
        borderRadius: radius.full, // O un radio menor si prefieres tarjetas cuadradas
        padding: spacingX._15,
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: spacingY._10,
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 3.84,
        elevation: 2,
        borderCurve: 'continuous'
    },
    iconContainer: {
        padding: spacingX._10,
        borderRadius: 50,
        marginRight: spacingX._15,
    },
    content: {
        flex: 1,
    }
})