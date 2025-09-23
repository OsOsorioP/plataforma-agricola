// app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useAuth } from '@/context/AuthContext'; // Importa useAuth
import { Button } from 'react-native'; // Para el botón de logout

export default function TabLayout() {
    const { logout } = useAuth(); // Obtiene la función logout del contexto

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
                    title: 'Chat', // Cambiado de Home a Chat para ser más claro
                    tabBarIcon: ({ color, focused }) => (
                        <Ionicons name={focused ? 'chatbox-sharp' : 'chatbox-outline'} color={color} size={24} />
                    ),
                    headerRight: () => ( // Añade un botón de logout en el header
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
                    headerRight: () => ( // También puedes añadirlo aquí
                        <Button onPress={logout} title="Salir" color="#fff" />
                    ),
                }}
            />
        </Tabs>
    );
}