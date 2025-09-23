import { StyleSheet, View, Text, FlatList, ActivityIndicator, Button, Alert, RefreshControl, TextInput } from "react-native";
import { useCallback, useEffect, useState } from "react";
import { getParcels, createParcel } from "@/services/parcels";
import { Parcel, ParcelCreate } from '@/types/parcels';

export default function ParcelScreen() {
    const [parcels, setParcels] = useState<Parcel[]>([]);
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);
    const [refreshing, setRefreshing] = useState(false);

    // Formulario para nueva parcela
    const [newParcelName, setNewParcelName] = useState('');
    const [newParcelLocation, setNewParcelLocation] = useState('');
    const [newParcelArea, setNewParcelArea] = useState('');

    const fetchParcels = async () => {
        try {
            const data = await getParcels();
            setParcels(data);
        } catch (error: any) {
            console.error('Error fetching parcels:', error);
            Alert.alert('Error', error.response?.data?.detail || 'No se pudieron cargar las parcelas.');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchParcels();
    }, []);

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        fetchParcels();
    }, []);

    const handleCreateParcel = async () => {
        if (!newParcelName.trim() || !newParcelArea.trim()) {
            Alert.alert('Error', 'El nombre y el área son obligatorios.');
            return;
        }
        const area = parseFloat(newParcelArea);
        if (isNaN(area) || area <= 0) {
            Alert.alert('Error', 'El área debe ser un número positivo.');
            return;
        }

        setCreating(true);
        try {
            const parcelData: ParcelCreate = {
                name: newParcelName,
                location: newParcelLocation.trim() || undefined, // Envía undefined si está vacío
                area: area,
            };
            await createParcel(parcelData);
            Alert.alert('Éxito', 'Parcela creada correctamente.');
            // Limpiar formulario
            setNewParcelName('');
            setNewParcelLocation('');
            setNewParcelArea('');
            // Recargar la lista de parcelas
            fetchParcels();
        } catch (error: any) {
            console.error('Error creating parcel:', error);
            Alert.alert('Error', error.response?.data?.detail || 'No se pudo crear la parcela.');
        } finally {
            setCreating(false);
        }
    };

    if (loading) {
        return (
            <View style={styles.centered}>
                <ActivityIndicator size="large" color="#0000ff" />
                <Text>Cargando parcelas...</Text>
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Mis Parcelas</Text>

            {/* Formulario para crear nueva parcela */}
            <View style={styles.formContainer}>
                <TextInput
                    style={styles.input}
                    placeholder="Nombre de la parcela"
                    value={newParcelName}
                    onChangeText={setNewParcelName}
                />
                <TextInput
                    style={styles.input}
                    placeholder="Ubicación (opcional)"
                    value={newParcelLocation}
                    onChangeText={setNewParcelLocation}
                />
                <TextInput
                    style={styles.input}
                    placeholder="Área (m²)"
                    value={newParcelArea}
                    onChangeText={setNewParcelArea}
                    keyboardType="numeric"
                />
                <Button
                    title={creating ? 'Creando...' : 'Crear Parcela'}
                    onPress={handleCreateParcel}
                    disabled={creating}
                />
            </View>

            <Text style={styles.subtitle}>Listado de Parcelas</Text>
            {parcels.length === 0 ? (
                <Text style={styles.noParcelsText}>No tienes parcelas registradas aún.</Text>
            ) : (
                <FlatList
                    data={parcels}
                    keyExtractor={(item) => item.id.toString()}
                    renderItem={({ item }) => (
                        <View style={styles.parcelItem}>
                            <Text style={styles.parcelName}>{item.name}</Text>
                            <Text>Ubicación: {item.location || 'N/A'}</Text>
                            <Text>Área: {item.area} m²</Text>
                        </View>
                    )}
                    refreshControl={
                        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
                    }
                />
            )}
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        padding: 20,
        backgroundColor: '#f5f5f5',
    },
    centered: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    title: {
        fontSize: 26,
        fontWeight: 'bold',
        marginBottom: 20,
        textAlign: 'center',
        color: '#333',
    },
    subtitle: {
        fontSize: 20,
        fontWeight: 'bold',
        marginTop: 30,
        marginBottom: 15,
        color: '#555',
    },
    formContainer: {
        backgroundColor: '#fff',
        padding: 15,
        borderRadius: 10,
        marginBottom: 20,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 3,
        elevation: 3,
    },
    input: {
        height: 45,
        borderColor: '#ddd',
        borderWidth: 1,
        borderRadius: 8,
        paddingHorizontal: 15,
        marginBottom: 10,
        backgroundColor: '#f9f9f9',
    },
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
    noParcelsText: {
        textAlign: 'center',
        marginTop: 20,
        fontSize: 16,
        color: '#777',
    },
});