// src/context/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import { login as apiLogin, logout as apiLogout } from '@/services/auth'; // Asegúrate de que la ruta sea correcta
import { useRouter, useSegments } from 'expo-router';
import { Alert } from 'react-native';

interface AuthContextType {
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const segments = useSegments();

  // Cargar el token al iniciar la app
  useEffect(() => {
    const loadToken = async () => {
      try {
        const storedToken = await SecureStore.getItemAsync('access_token');
        if (storedToken) {
          setToken(storedToken);
        }
      } catch (e) {
        console.error("Failed to load auth token:", e);
      } finally {
        setIsLoading(false);
      }
    };
    loadToken();
  }, []);

  // Redirigir basado en el estado de autenticación
  useEffect(() => {
    if (!isLoading) {
      const inAuthGroup = segments[0] === '(auth)';

      if (token && inAuthGroup) {
        // Usuario logueado, redirigir a la app principal (tabs)
        router.replace('/(tabs)');
      } else if (!token && !inAuthGroup) {
        // Usuario no logueado, redirigir a la pantalla de login
        router.replace('/(auth)/signin'); // Asegúrate de que esta sea la ruta correcta a tu pantalla de login
      }
    }
  }, [token, isLoading, segments]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const authData = await apiLogin(email, password);
      await SecureStore.setItemAsync('access_token', authData.access_token);
      setToken(authData.access_token);
      router.replace('/(tabs)'); // Redirigir a la app principal
    } catch (error: any) {
      console.error('Login error:', error);
      Alert.alert('Error de Inicio de Sesión', error.response?.data?.detail || 'Credenciales incorrectas o error de red.');
      setToken(null); // Asegúrate de que el token se limpie si hay un error
      throw error; // Re-lanza el error para que el componente que llama pueda manejarlo
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await apiLogout();
      await SecureStore.deleteItemAsync('access_token');
      setToken(null);
      router.replace('/(auth)/signin'); // Redirigir a la pantalla de login
    } catch (e) {
      console.error("Failed to logout:", e);
      Alert.alert('Error al cerrar sesión', 'No se pudo cerrar la sesión correctamente.');
    } finally {
      setIsLoading(false);
    }
  };

  const value = {
    token,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}