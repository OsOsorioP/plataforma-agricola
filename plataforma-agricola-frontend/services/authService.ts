import apiClient from "./apiService";
import { AuthContextProps } from "../types/auth";

export const login = async (
  email: string,
  password: string
): Promise<AuthContextProps> => {
  try {
    const response = await apiClient.post<AuthContextProps>("/auth/login", {
      email: email,
      password: password,
    });
    return response.data;
  } catch (error: any) {
    const msg = error?.response?.data?.msg || "Login failed";
    throw new Error(msg);
  }
};

export const register = async (
  email: string,
  password: string,
  username: string,
  avatar?: string | null
): Promise<AuthContextProps> => {
  try {
    const response = await apiClient.post<AuthContextProps>("/auth/register", {
      email: email,
      password: password,
      full_name: username,
      avatar: avatar,
    });
    return response.data;
  } catch (error: any) {
    console.error("Error during register:", error);
    const msg = error?.response?.data?.msg || "Register failed";
    throw new Error(msg);
  }
};
