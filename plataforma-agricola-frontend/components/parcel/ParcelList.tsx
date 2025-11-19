// components/ParcelList.tsx
import { StyleSheet, View, Text, FlatList, ActivityIndicator, RefreshControl } from "react-native";
import React from 'react';
import { Parcel } from '@/types/parcels';
import { ParcelItem } from './ParcelItem';

interface ParcelListProps {
    parcels: Parcel[];
    loading: boolean;
    refreshing: boolean;
    onRefresh: () => void;
}

export function ParcelList({ parcels, loading, refreshing, onRefresh }: ParcelListProps) {
    if (loading) {
        return (
            <View style={styles.centered}>
                <ActivityIndicator size="large" color="#0000ff" />
                <Text>Cargando parcelas...</Text>
            </View>
        );
    }

    if (parcels.length === 0) {
        return (
            <View style={styles.centered}>
                <Text style={styles.noParcelsText}>No tienes parcelas registradas aún.</Text>
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
            </View>
        );
    }

    return (
        <FlatList
            data={parcels}
            keyExtractor={(item) => item.id.toString()}
            renderItem={({ item }) => <ParcelItem parcel={item} />}
            contentContainerStyle={styles.listContainer}
            refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
            }
        />
    );
}

const styles = StyleSheet.create({
    centered: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
    },
    noParcelsText: {
        textAlign: 'center',
        marginTop: 20,
        fontSize: 16,
        color: '#777',
    },
    listContainer: {
        paddingBottom: 20, // Espacio al final de la lista
    }
});