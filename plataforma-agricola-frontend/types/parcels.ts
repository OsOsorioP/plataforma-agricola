export type CropType = 
  | 'maiz' 
  | 'trigo' 
  | 'soja' 
  | 'cafe' 
  | 'arroz' 
  | 'papa' 
  | 'tomate' 
  | 'hortalizas' 
  | 'platano' 
  | 'otros';

export type DevelopmentStage = 
  | 'preparacion' 
  | 'siembra' 
  | 'germinacion' 
  | 'crecimiento' 
  | 'floracion' 
  | 'maduracion' 
  | 'cosecha';

export interface ParcelBase {
  name: string;
  location?: string;
  area: number;
  geometry: string;
  
  // Nuevos campos opcionales - Información del cultivo
  crop_type?: CropType | string;
  development_stage?: DevelopmentStage | string;
  planting_date?: string;
  
  // Nuevos campos opcionales - Características del suelo
  soil_type?: string;
  soil_ph?: number;
  
  // Nuevos campos opcionales - Sistema de riego
  irrigation_type?: string;
  
  // Nuevos campos opcionales - Estado actual
  health_status?: string;
  current_issues?: string;
}

export interface ParcelCreate extends ParcelBase {}

export interface ParcelUpdate {
  name?: string;
  crop_type?: CropType | string;
  development_stage?: DevelopmentStage | string;
  planting_date?: string;
  soil_type?: string;
  soil_ph?: number;
  irrigation_type?: string;
  health_status?: string;
  current_issues?: string;
}

export interface Parcel extends ParcelBase {
  id: number;
  owner_id: number;
  created_at: string;
  updated_at: string;
}

// Opciones para los selects del formulario
export const CROP_OPTIONS = [
  { label: 'Maíz', value: 'maiz' },
  { label: 'Trigo', value: 'trigo' },
  { label: 'Soja', value: 'soja' },
  { label: 'Café', value: 'cafe' },
  { label: 'Arroz', value: 'arroz' },
  { label: 'Papa', value: 'papa' },
  { label: 'Tomate', value: 'tomate' },
  { label: 'Hortalizas', value: 'hortalizas' },
  { label: 'Plátano', value: 'platano' },
  { label: 'Otros', value: 'otros' },
];

export const STAGE_OPTIONS = [
  { label: 'Preparación del suelo', value: 'preparacion' },
  { label: 'Siembra', value: 'siembra' },
  { label: 'Germinación', value: 'germinacion' },
  { label: 'Crecimiento vegetativo', value: 'crecimiento' },
  { label: 'Floración', value: 'floracion' },
  { label: 'Maduración', value: 'maduracion' },
  { label: 'Cosecha', value: 'cosecha' },
];

export const SOIL_OPTIONS = [
  { label: 'Arcilloso', value: 'arcilloso' },
  { label: 'Arenoso', value: 'arenoso' },
  { label: 'Franco', value: 'franco' },
  { label: 'Limoso', value: 'limoso' },
  { label: 'No sé', value: '' },
];

export const IRRIGATION_OPTIONS = [
  { label: 'Riego por goteo', value: 'goteo' },
  { label: 'Aspersión', value: 'aspersion' },
  { label: 'Inundación', value: 'inundacion' },
  { label: 'Pivot', value: 'pivot' },
  { label: 'Secano (sin riego)', value: 'secano' },
  { label: 'No sé', value: '' },
];

export const HEALTH_STATUS_OPTIONS = [
  { label: 'Excelente', value: 'excelente' },
  { label: 'Bueno', value: 'bueno' },
  { label: 'Regular', value: 'regular' },
  { label: 'Malo', value: 'malo' },
];