// app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useAuth } from '@/context/AuthContext';
import { Button } from 'react-native';

export default function TabLayout() {
    const { logout } = useAuth(); 

    return (
        <Tabs
            screenOptions={{
                tabBarActiveTintColor: '#ffd33d',
                headerStyle: {
                    backgroundColor: '#25292e',
                },
                headerShadowVisible: false,
                headerTintColor: '#fff',
                tabBarStyle: {
                    backgroundColor: '#25292e',
                },
            }}
        >
            <Tabs.Screen
                name="index"
                options={{
                    title: 'Chat',
                    tabBarIcon: ({ color, focused }) => (
                        <Ionicons name={focused ? 'chatbox-sharp' : 'chatbox-outline'} color={color} size={24} />
                    ),
                    headerRight: () => (
                        <Button onPress={logout} title="Salir" color="#fff" />
                    ),
                }}
            />

            <Tabs.Screen
                name="parcel"
                options={{
                    title: 'Parcelas',
                    tabBarIcon: ({ color, focused }) => (
                        <Ionicons name={focused ? 'map-sharp' : 'map-outline'} color={color} size={24} />
                    ),
                    headerRight: () => (
                        <Button onPress={logout} title="Salir" color="#fff" />
                    ),
                }}
            />

            <Tabs.Screen
                name="alerts"
                options={{
                    title: 'Alertas',
                    tabBarIcon: ({ color, focused }) => (
                        <Ionicons name={focused ? 'map-sharp' : 'map-outline'} color={color} size={24} />
                    ),
                    headerRight: () => (
                        <Button onPress={logout} title="Salir" color="#fff" />
                    ),
                    
                }}
            />
        </Tabs>
    );
}