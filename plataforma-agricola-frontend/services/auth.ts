import apiClient from './api';
import * as SecureStore from 'expo-secure-store';
import { AuthToken, UserCreate, User } from '../types/auth';

export const login = async (email: string, password: string): Promise<AuthToken> => {
  try {
    const response = await apiClient.post<AuthToken>(
      '/token',
      new URLSearchParams({
        username: email,
        password: password,
      }).toString(),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );
    await SecureStore.setItemAsync('access_token', response.data.access_token);
    return response.data;
  } catch (error) {
    console.error('Error during login:', error);
    throw error;
  }
};

export const registerUser = async (userData: UserCreate): Promise<User> => {
  try {
    const response = await apiClient.post<User>('/users/', userData);
    return response.data;
  } catch (error) {
    console.error('Error during user registration:', error);
    throw error;
  }
};

export const logout = async (): Promise<void> => {
  await SecureStore.deleteItemAsync('access_token');
};

export const getStoredToken = async (): Promise<string | null> => {
  return await SecureStore.getItemAsync('access_token');
};