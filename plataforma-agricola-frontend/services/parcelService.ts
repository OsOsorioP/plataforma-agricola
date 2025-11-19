// src/api/parcels.ts
import apiClient from "./apiService";
import { Parcel, ParcelCreate } from "../types/parcels";

/**
 * Servicio para crear una nueva parcela.
 * Requiere autenticación (Manejada por apiClient/interceptor).
 * @param parcelData Los datos de la nueva parcela.
 * @returns La parcela creada con su ID y fecha.
 */
export const createParcel = async (
  parcelData: ParcelCreate
): Promise<Parcel> => {
  try {
    const response = await apiClient.post<Parcel>("/parcels/", parcelData);
    return response.data;
  } catch (error) {
    console.error("Error creating parcel:", error);
    throw error;
  }
};

/**
 * Servicio para obtener todas las parcelas del usuario actual.
 * Requiere autenticación.
 * @returns Una lista de objetos ParcelData.
 */
export const getParcels = async (): Promise<Parcel[]> => {
  try {
    const response = await apiClient.get<Parcel[]>("/parcels/", {});
    return response.data;
  } catch (error) {
    console.error("Error fetching parcels:", error);
    throw error;
  }
};
