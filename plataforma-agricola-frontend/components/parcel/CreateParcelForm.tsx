// components/CreateParcelForm.tsx
import { StyleSheet, View, Text, TextInput, Button, Alert } from "react-native";
import React, { useState } from 'react';
import { createParcel } from "@/services/parcelService";
import { ParcelCreate } from '@/types/parcels';

interface CreateParcelFormProps {
    onParcelCreated: () => void;
    onCancel: () => void;
}

export function CreateParcelForm({ onParcelCreated, onCancel }: CreateParcelFormProps) {
    const [newParcelName, setNewParcelName] = useState('');
    const [newParcelArea, setNewParcelArea] = useState(0);
    const [newParcelGeometry, setNewParcelGeometry] = useState('');
    const [creating, setCreating] = useState(false);

    const simulateMapAreaCapture = () => {

    };


    const handleCreateParcel = async () => {
        if (!newParcelName.trim() || !newParcelGeometry.trim()) {
            Alert.alert('Error', 'El nombre y la geometría del área son obligatorios. ¡Capture el área en el mapa!');
            return;
        }

        setCreating(true);
        try {
            const parcelData: ParcelCreate = {
                name: newParcelName.trim(),
                geometry: newParcelGeometry,
                area: newParcelArea,
            };
            await createParcel(parcelData);
            Alert.alert('Éxito', 'Parcela creada correctamente. Se calculará el área y otros índices en el servidor.');

            setNewParcelName('');
            setNewParcelGeometry('');
            setNewParcelArea(0)
            onParcelCreated();
        } catch (error: any) {
            console.error('Error creating parcel:', error);
            Alert.alert('Error', error.response?.data?.detail || 'No se pudo crear la parcela.');
        } finally {
            setCreating(false);
        }
    };

    return (
        <View style={styles.formContainer}>
            <TextInput
                style={styles.input}
                placeholder="Nombre de la parcela (Ej: Lote 1)"
                value={newParcelName}
                onChangeText={setNewParcelName}
            />

            {/* ZONA CRÍTICA: MAPA GEOSPECIAL */}
            <View style={styles.mapCaptureArea}>
                <Text style={styles.mapLabel}>Geometría de la Parcela:</Text>
                {newParcelGeometry ? (
                    <Text style={styles.geometryText}>✅ Geometría Capturada</Text>
                ) : (
                    <Text style={styles.geometryText}>Esperando dibujo en el mapa...</Text>
                )}
                <Button
                    title="Abrir Mapa y Marcar Área"
                    onPress={simulateMapAreaCapture}
                    disabled={creating}
                    color="#4CAF50" // Color para destacar la acción principal
                />
                <Text style={styles.mapHint}>*Debe integrar un componente MapView aquí (ej: react-native-maps) para buscar, centrar y dibujar el polígono. Esta acción guardará el GeoJSON/WKT en el estado newParcelGeometry.</Text>
            </View>
            {/* FIN ZONA CRÍTICA */}

            <View style={styles.buttonGroup}>
                <Button
                    title="Cancelar"
                    onPress={onCancel}
                    disabled={creating}
                    color="#f44336"
                />
                <Button
                    title={creating ? 'Creando...' : 'Guardar Parcela'}
                    onPress={handleCreateParcel}
                    disabled={creating || !newParcelName.trim() || !newParcelGeometry}
                />
            </View>

        </View>
    );
}

const styles = StyleSheet.create({
    formContainer: {
        backgroundColor: '#fff',
        padding: 20,
        borderRadius: 10,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 3,
        elevation: 3,
    },
    input: {
        height: 50,
        borderColor: '#ddd',
        borderWidth: 1,
        borderRadius: 8,
        paddingHorizontal: 15,
        marginBottom: 15,
        backgroundColor: '#f9f9f9',
        fontSize: 16,
    },
    mapCaptureArea: {
        borderWidth: 1,
        borderColor: '#ccc',
        padding: 15,
        borderRadius: 8,
        marginBottom: 15,
        backgroundColor: '#e8f5e9',
    },
    mapLabel: {
        fontSize: 16,
        fontWeight: '600',
        marginBottom: 10,
        color: '#388E3C',
    },
    geometryText: {
        marginBottom: 10,
        color: '#1B5E20',
        fontStyle: 'italic',
    },
    mapHint: {
        fontSize: 12,
        color: '#777',
        marginTop: 10,
    },
    buttonGroup: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginTop: 20,
    }
});