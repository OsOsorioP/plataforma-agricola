import React, { useState, useEffect, useRef } from 'react';
import { StyleSheet, View, Button, Alert, ActivityIndicator, Text } from 'react-native';
import MapView, { Polygon, Marker } from 'react-native-maps';
import * as Location from 'expo-location';
import * as turf from '@turf/turf';
import { useRouter } from 'expo-router';
import { CreateParcelFormEnhanced } from './CreateParcelFormEnhanced';

interface ParcelMapDrawProps {
    onParcelCreated: () => void;
    onCancel: () => void;
}

interface region {
    latitude: number;
    longitude: number;
    latitudeDelta: number;
    longitudeDelta: number;
}

interface point {
    latitude: number;
    longitude: number;
}

export function ParcelMapDraw({ onParcelCreated, onCancel }: ParcelMapDrawProps) {
    const router = useRouter();
    const [isDrawing, setIsDrawing] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [locationLoading, setLocationLoading] = useState(true);
    const [showForm, setShowForm] = useState(false)
    const [geometryData, setGeometryData] = useState<{ geometry: string; area: number; location: string; }>({ geometry: "", area: 0, location: "" })

    const [initialRegion, setInitialRegion] = useState<region>();
    const [points, setPoints] = useState<point[]>([]);
    const [area, setArea] = useState(0);

    const mapRef = useRef(null);

    useEffect(() => {
        (async () => {
            let { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert('Permiso denegado', 'Se necesita permiso para centrar el mapa.');
                setInitialRegion({ latitude: 4.60971, longitude: -74.08175, latitudeDelta: 5, longitudeDelta: 5 });
                setLocationLoading(false);
                return;
            }
            let location = await Location.getCurrentPositionAsync({});
            setInitialRegion({
                latitude: location.coords.latitude,
                longitude: location.coords.longitude,
                latitudeDelta: 0.005,
                longitudeDelta: 0.005,
            });
            setLocationLoading(false);
        })();
    }, []);

    // Efecto para calcular el área
    useEffect(() => {
        if (points.length < 3) {
            setArea(0);
            return;
        }
        const turfPoints = points.map(p => [p.longitude, p.latitude]);
        turfPoints.push(turfPoints[0]);
        const turfPolygon = turf.polygon([turfPoints]);
        const calculatedAreaM2 = turf.area(turfPolygon);
        const calculatedAreaHa = calculatedAreaM2 / 10000;
        setArea(calculatedAreaHa);
    }, [points]);

    // Manejadores de eventos
    const handleMapPress = (e: { nativeEvent: { coordinate: point; }; }) => {
        if (isDrawing) {
            setPoints([...points, e.nativeEvent.coordinate]);
        }
    };

    const startDrawing = () => {
        setPoints([]);
        setIsDrawing(true);
        Alert.alert('Modo Dibujo', 'Toca el mapa para añadir los vértices de tu parcela.');
    };

    const finishDrawing = () => {
        if (points.length < 3) {
            Alert.alert('Error', 'Necesitas al menos 3 puntos para formar un polígono.');
            return;
        }
        setIsDrawing(false);
        Alert.alert('Dibujo Terminado', 'Ahora puedes poner el nombre y guardar tu parcela.');
    };

    const handleUndo = () => {
        setPoints(prev => prev.slice(0, -1));
    };

    const handleSave = async () => {


        setIsLoading(true);

        const coordinates = points.map(p => [p.longitude, p.latitude]);
        coordinates.push(coordinates[0]);
        const geometry = { type: "Polygon", coordinates: [coordinates] };
        const turfPolygon = turf.polygon(geometry.coordinates);
        const center = turf.centerOfMass(turfPolygon);
        const locationString = `${center.geometry.coordinates[1]},${center.geometry.coordinates[0]}`;

        const geometryData = {
            geometry: JSON.stringify(geometry),
            area: parseFloat(area.toFixed(4)),
            location: locationString
        };


        setShowForm(true);
        setGeometryData(geometryData);
    };

    if (locationLoading) {
        return (
            <View style={styles.centered}>
                <ActivityIndicator size="large" />
                <Text>Obteniendo tu ubicación...</Text>
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <Text style={styles.headerTitle}>Dibuja el Área de tu Parcela</Text>
            <MapView
                ref={mapRef}
                style={styles.map}
                initialRegion={initialRegion}
                onPress={handleMapPress}
                showsUserLocation={true}
                mapType='satellite'
                loadingEnabled={true}
            >
                {points.map((coord, index) => (
                    <Marker key={index} coordinate={coord} pinColor={index === 0 ? 'blue' : 'red'} />
                ))}
                {points.length >= 2 && (
                    <Polygon
                        coordinates={points}
                        strokeColor="#3A6A0B"
                        fillColor="rgba(58, 255, 68, 0.43)"
                        strokeWidth={2}
                    />
                )}
            </MapView>

            <View style={styles.controls}>
                <Text style={styles.statusText}>Puntos Trazados: {points.length} | Área: {area.toFixed(4)} ha</Text>

                <View style={styles.buttonRow}>
                    {!isDrawing ? (
                        <Button title="Empezar a Dibujar" onPress={startDrawing} color="#4CAF50" />
                    ) : (
                        <Button title="Terminar Dibujo" onPress={finishDrawing} color="#FF9800" />
                    )}
                    {points.length > 0 && (
                        <Button title="Deshacer Último" onPress={handleUndo} color="#9E9E9E" />
                    )}
                </View>

                {points.length >= 3 && !isDrawing && (
                    <>
                        <Button
                            title={isLoading ? "Guardando..." : "Guardar Parcela"}
                            onPress={handleSave}
                            disabled={isLoading}
                            color="#1E90FF"
                        />
                    </>
                )}
                {showForm && (
                    <CreateParcelFormEnhanced
                        geometryData={geometryData}
                        onParcelCreated={() => {
                            setShowForm(false);
                            onParcelCreated();
                        }}
                        onCancel={() => setShowForm(false)}
                    />
                )}
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f0f4f7',
    },
    headerTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        textAlign: 'center',
        padding: 15,
    },
    map: {
        flex: 3,
    },
    controls: {
        flex: 4,
        padding: 15,
        backgroundColor: '#fff',
        borderTopLeftRadius: 20,
        borderTopRightRadius: 20,
        marginTop: -10,
        gap: 10,
    },
    centered: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    input: {
        borderWidth: 1,
        borderColor: '#ccc',
        padding: 12,
        borderRadius: 8,
        fontSize: 16,
    },
    buttonRow: {
        flexDirection: 'row',
        justifyContent: 'space-around',
        gap: 10,
    },
    statusText: {
        textAlign: 'center',
        fontWeight: 'bold',
        color: '#3A6A0B',
        fontSize: 16,
    }
});