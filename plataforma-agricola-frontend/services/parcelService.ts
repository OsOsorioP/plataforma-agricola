// src/api/parcels.ts
import apiClient from "./apiService";
import { Parcel, ParcelCreate, ParcelUpdate } from "../types/parcels";

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
  } catch (error: any) {
    console.error("Error creating parcel:", error);
    throw new Error(error.response?.data?.detail || "No se pudo crear la parcela");
  }
};

/**
 * Servicio para obtener todas las parcelas del usuario actual.
 * Requiere autenticación.
 * @returns Una lista de objetos ParcelData.
 */
export const getParcels = async (): Promise<Parcel[]> => {
  try {
    const response = await apiClient.get<Parcel[]>("/parcels/");
    return response.data;
  } catch (error: any) {
    console.error("Error fetching parcels:", error);
    throw new Error(error.response?.data?.detail || "No se pudieron cargar las parcelas");
  }
};

/**
 * Obtiene detalles de una parcela específica
 */
export const getParcelById = async (parcelId: number): Promise<Parcel> => {
  try {
    const response = await apiClient.get<Parcel>(`/parcels/${parcelId}`);
    return response.data;
  } catch (error: any) {
    console.error("Error fetching parcel:", error);
    throw new Error(error.response?.data?.detail || "No se pudo cargar la parcela");
  }
};

/**
 * Actualiza información de una parcela existente
 * Útil para que el usuario actualice información del cultivo conforme avanza la temporada
 */
export const updateParcel = async (
  parcelId: number,
  parcelData: ParcelUpdate
): Promise<Parcel> => {
  try {
    const response = await apiClient.put<Parcel>(
      `/parcels/${parcelId}`,
      parcelData
    );
    return response.data;
  } catch (error: any) {
    console.error("Error updating parcel:", error);
    throw new Error(error.response?.data?.detail || "No se pudo actualizar la parcela");
  }
};

/**
 * Elimina una parcela
 */
export const deleteParcel = async (parcelId: number): Promise<void> => {
  try {
    await apiClient.delete(`/parcels/${parcelId}`);
  } catch (error: any) {
    console.error("Error deleting parcel:", error);
    throw new Error(error.response?.data?.detail || "No se pudo eliminar la parcela");
  }
};
