import { API_URL } from "@/constants";
import axios from "axios";
import * as SecureStore from "expo-secure-store";

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use(
  async (config) => {
    const token = await SecureStore.getItemAsync("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response && error.response.status === 401) {
      console.log("Token expirado o no autorizado. Redirigiendo...");
      await SecureStore.deleteItemAsync("token");
    }
    return Promise.reject(error);
  }
);

export default apiClient;
