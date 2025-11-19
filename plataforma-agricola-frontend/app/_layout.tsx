// app/_layout.tsx
import { Stack } from 'expo-router';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { StyleSheet, useColorScheme } from 'react-native';
import { AuthProvider } from '@/context/AuthContext';

export default function RootLayout() {
  let colorScheme = useColorScheme()

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colorScheme === 'light' ? "#333" : "#fff" }}>
      <SafeAreaProvider style={styles.container}>
        <AuthProvider>
          <Stack screenOptions={{
            headerShown: false,
          }}>
            <Stack.Screen name="index" />
            <Stack.Screen name="(auth)" />
            <Stack.Screen name="(tabs)" />
            <Stack.Screen name="+not-found" />
          </Stack>
        </AuthProvider>
      </SafeAreaProvider>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff'
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
})