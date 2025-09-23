export interface ParcelBase {
  name: string;
  location?: string;
  area: number;
}

export interface ParcelCreate extends ParcelBase {}

export interface Parcel extends ParcelBase {
  id: number;
  owner_id: number;
}