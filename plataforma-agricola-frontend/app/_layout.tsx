// app/_layout.tsx
import { Stack } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ActivityIndicator, View, StyleSheet} from 'react-native';
import { useAuth, AuthProvider } from '@/context/AuthContext';

function InitialLoadingScreen() {
  const { isLoading } = useAuth();
  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#0000ff" />
      </View>
    );
  }
  return null;
}


export default function RootLayout() {
  return (
    <SafeAreaProvider style={styles.container}>

        <AuthProvider>
          <InitialLoadingScreen />
          <Stack screenOptions={{
            headerShown: false,
          }}>
            <Stack.Screen name="(auth)" options={{ headerShown: false }} />
            <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
            <Stack.Screen name="+not-found" />
          </Stack>
        </AuthProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container:{
    flex:1
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
})