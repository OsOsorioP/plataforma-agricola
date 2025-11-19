// screens/ParcelScreen.tsx (o como lo tengas en tu proyecto)
import { StyleSheet, View, Text, Button, Alert } from "react-native";
import { useCallback, useEffect, useState } from "react";
import { getParcels } from "@/services/parcelService";
import { Parcel } from '@/types/parcels';

import { ParcelList } from "@/components/parcel/ParcelList";
import { ParcelMapDraw } from "@/components/parcel/ParcelDrawMap";

type Tab = 'list' | 'create';

export default function ParcelScreen() {
    const [parcels, setParcels] = useState<Parcel[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [activeTab, setActiveTab] = useState<Tab>('list');

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
    }, [activeTab]);

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        fetchParcels();
    }, []);

    const handleParcelCreated = () => {
        setActiveTab('list');
        fetchParcels();
    };

    const renderContent = () => {
        if (activeTab === 'list') {
            return (
                <ParcelList
                    parcels={parcels}
                    loading={loading}
                    refreshing={refreshing}
                    onRefresh={onRefresh}
                />
            );
        }

        if (activeTab === 'create') {
            return (
                <ParcelMapDraw
                    onParcelCreated={handleParcelCreated}
                    onCancel={() => setActiveTab('list')}
                />
            );
        }

        return null;
    };

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Gestión de Parcelas</Text>

            <View style={styles.tabContainer}>
                <View style={styles.tabButton}>
                    <Button
                        title="Ver Parcelas"
                        onPress={() => setActiveTab('list')}
                        color={activeTab === 'list' ? '#1E90FF' : '#A9A9A9'}
                    />
                </View>
                <View style={styles.tabButton}>
                    <Button
                        title="Crear Parcela"
                        onPress={() => setActiveTab('create')}
                        color={activeTab === 'create' ? '#1E90FF' : '#A9A9A9'}
                    />
                </View>
            </View>

            <View style={styles.contentArea}>
                {renderContent()}
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        padding: 20,
        backgroundColor: '#f5f5f5',
    },
    title: {
        fontSize: 26,
        fontWeight: 'bold',
        marginBottom: 20,
        textAlign: 'center',
        color: '#333',
    },
    tabContainer: {
        flexDirection: 'row',
        justifyContent: 'space-around',
        marginBottom: 20,
        borderBottomWidth: 1,
        borderBottomColor: '#ddd',
        paddingBottom: 10,
    },
    tabButton: {
        flex: 1,
        marginHorizontal: 5,
    },
    contentArea: {
        flex: 1,
    },
});