// src/api/parcels.ts
import apiClient from './api';
import { Parcel, ParcelCreate } from '../types/parcels';

export const createParcel = async (parcelData: ParcelCreate): Promise<Parcel> => {
  try {
    const response = await apiClient.post<Parcel>('/parcels/', parcelData);
    return response.data;
  } catch (error) {
    console.error('Error creating parcel:', error);
    throw error;
  }
};

export const getParcels = async (): Promise<Parcel[]> => {
  try {
    const response = await apiClient.get<Parcel[]>('/parcels/');
    return response.data;
  } catch (error) {
    console.error('Error fetching parcels:', error);
    throw error;
  }
};