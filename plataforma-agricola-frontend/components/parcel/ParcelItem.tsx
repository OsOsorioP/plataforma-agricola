import { StyleSheet, View, Text } from "react-native";
import { Parcel } from '@/types/parcels'; 

interface ParcelItemProps {
    parcel: Parcel;
    onPress?: () => void;
}

export function ParcelItem({ parcel }: ParcelItemProps) {
    return (
        <View style={styles.parcelItem}>
            <Text style={styles.parcelName}>{parcel.name}</Text>
            <Text>Área: {parcel.area} m²</Text>
            <Text>Ubicación: {parcel.location || 'N/A'}</Text>
            {/* <Text>Geometría: {parcel.geometry ? 'Registrada' : 'Faltante'}</Text> */}
        </View>
    );
}

const styles = StyleSheet.create({
    parcelItem: {
        backgroundColor: '#fff',
        padding: 15,
        borderRadius: 10,
        marginBottom: 10,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.08,
        shadowRadius: 2,
        elevation: 2,
    },
    parcelName: {
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 5,
        color: '#444',
    },
});