// app/(auth)/signin/index.tsx
import { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '@/context/AuthContext';

export default function LoginScreen() {
    const router = useRouter();
    const { login, isLoading } = useAuth(); 

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleLogin = async () => {
        try {
            await login(email, password);
        } catch (error: any) {
            console.error(error)
        } finally {
        }
    };

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Iniciar Sesión</Text>
            <TextInput
                style={styles.input}
                placeholder="Email"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
            />
            <TextInput
                style={styles.input}
                placeholder="Contraseña"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
            />
            <Button title={isLoading ? "Cargando..." : "Entrar"} onPress={handleLogin} disabled={isLoading} />
            <Button title="Registrarse" onPress={() => router.replace('/(auth)/signup')} />
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, justifyContent: 'center', padding: 20, backgroundColor: '#f5f5f5' },
    title: { fontSize: 24, marginBottom: 20, textAlign: 'center', fontWeight: 'bold', },
    input: { height: 50, borderWidth: 1, borderColor: '#ccc', padding: 10, marginBottom: 10, borderRadius: 8, paddingHorizontal: 15, backgroundColor: '#fff', },
});