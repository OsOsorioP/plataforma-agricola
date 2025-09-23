// app/(auth)/signup/index.tsx
import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { Alert, View, Text, TextInput, Button, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { registerUser } from '@/services/auth'; // Importa la función de registro

export default function Register() {
    const router = useRouter();
    const { login, isLoading } = useAuth(); // Usamos login para después del registro
    const [email, setEmail] = useState('');
    const [fullName, setFullName] = useState(''); // Añadido para el campo full_name
    const [password, setPassword] = useState('');
    const [isRegistering, setIsRegistering] = useState(false); // Estado para el registro

    const handleRegister = async () => {
        if (!email.trim() || !password.trim()) {
            Alert.alert('Error', 'Email y contraseña son obligatorios.');
            return;
        }
        setIsRegistering(true);
        try {
            await registerUser({ email, password, full_name: fullName.trim() || undefined });
            Alert.alert('Éxito', 'Usuario registrado correctamente. Por favor, inicia sesión.');
            router.replace('/(auth)/signin'); // Redirigir a login después del registro
        } catch (error: any) {
            console.error('Error de registro:', error);
            Alert.alert('Error de Registro', error.response?.data?.detail || 'Algo salió mal durante el registro.');
        } finally {
            setIsRegistering(false);
        }
    };

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Registrarse</Text>
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
                placeholder="Nombre Completo (opcional)"
                value={fullName}
                onChangeText={setFullName}
            />
            <TextInput
                style={styles.input}
                placeholder="Contraseña"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
            />
            <Button title={isRegistering ? "Registrando..." : "Registrarse"} onPress={handleRegister} disabled={isRegistering} />
            <Button title="Ya tengo cuenta" onPress={() => router.replace('/(auth)/signin')} />
        </View>
    );
};

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 20 },
  title: { fontSize: 24, marginBottom: 20, textAlign: 'center' },
  input: { borderWidth: 1, borderColor: '#ccc', padding: 10, marginBottom: 10, borderRadius: 5 },
});