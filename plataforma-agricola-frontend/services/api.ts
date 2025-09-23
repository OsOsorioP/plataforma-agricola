import axios from "axios";
import * as SecureStore from "expo-secure-store";

const API_BASE_URL = process.env.EXPO_BASE_URL || "http://192.168.18.116:8000/";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor para añadir el token de autenticación a las solicitudes
apiClient.interceptors.request.use(
  async (config) => {
    const token = await SecureStore.getItemAsync("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores de autenticación (ej. token expirado)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response && error.response.status === 401) {
      // Opcional: Redirigir al usuario a la pantalla de login o refrescar el token
      console.log("Token expirado o no autorizado. Redirigiendo al login...");
      await SecureStore.deleteItemAsync("access_token");
      // Aquí podrías emitir un evento o usar un contexto para notificar a la app que el usuario debe loguearse de nuevo
    }
    return Promise.reject(error);
  }
);

export default apiClient;
