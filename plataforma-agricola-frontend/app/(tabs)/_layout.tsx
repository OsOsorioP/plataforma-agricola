import { Tabs } from 'expo-router';
import Ionicons from '@expo/vector-icons/Ionicons';
import { colors } from '@/constants/theme';
import { verticalScale } from '@/utils/styling';

export default function TabLayout() {

    return (
        <Tabs
            screenOptions={{
                tabBarActiveTintColor: colors.primary,
                headerStyle: {
                    backgroundColor: colors.black,
                },
                headerShadowVisible: false,
                headerTintColor: '#fff',
                tabBarStyle: {
                    backgroundColor: '#ffffff',
                },
                headerShown: false
            }}
        >
            <Tabs.Screen
                name="chat"
                options={{
                    title: 'Chat',
                    tabBarIcon: ({ color, focused }) => (
                        <Ionicons name={focused ? 'chatbox-sharp' : 'chatbox-outline'} color={color} size={verticalScale(24)} />
                    ),
                }}
            />

            <Tabs.Screen
                name="parcel"
                options={{
                    title: 'Parcelas',
                    tabBarIcon: ({ color, focused }) => (
                        <Ionicons name={focused ? 'map-sharp' : 'map-outline'} color={color} size={verticalScale(24)} />
                    ),
                }}
            />
        </Tabs>
    );
}