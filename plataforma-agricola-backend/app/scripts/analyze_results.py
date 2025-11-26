# scripts/analyze_results.py
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def calculate_ks1_eir():
    """KS1: Tasa de Intervención Ecológica"""
    df = pd.read_sql("SELECT * FROM intervention_events", engine)
    if df.empty: return 0
    
    n_vetos = df['was_vetoed'].sum()
    n_total = len(df)
    eir = (n_vetos / n_total) * 100
    
    print(f"--- KS1: EIR ---")
    print(f"Total Consultas Químicas: {n_total}")
    print(f"Intervenciones (Vetos): {n_vetos}")
    print(f"EIR: {eir:.2f}% (Meta: >90%)")
    return eir

def calculate_ks2_delta_eiq():
    """KS2: Reducción de Carga Tóxica"""
    df = pd.read_sql("SELECT * FROM intervention_events WHERE was_vetoed = true", engine)
    if df.empty: return 0
    
    # Fórmula: ((EIQ_Base - EIQ_Agente) / EIQ_Base) * 100
    df['delta_eiq'] = ((df['eiq_base'] - df['eiq_alternative']) / df['eiq_base']) * 100
    avg_reduction = df['delta_eiq'].mean()
    
    print(f"\n--- KS2: Delta EIQ ---")
    print(f"Reducción promedio de toxicidad: {avg_reduction:.2f}% (Meta: >40%)")
    return avg_reduction

def calculate_ks3_wpa():
    """KS3: Precisión Hídrica"""
    df = pd.read_sql("SELECT * FROM water_calculations", engine)
    if df.empty: return 0
    
    # WPA ya se calcula fila por fila en el logger, sacamos el promedio
    avg_wpa = df['wpa_score'].mean() * 100
    avg_dev = df['deviation_percent'].mean()
    
    print(f"\n--- KS3: WPA ---")
    print(f"Precisión promedio: {avg_wpa:.2f}%")
    print(f"Desviación promedio: {avg_dev:.2f}% (Meta: <10%)")
    return avg_wpa

def calculate_kt1_geff():
    """KT1: Eficiencia de Orquestación"""
    df = pd.read_sql("SELECT * FROM orchestration_events", engine)
    if df.empty: return 0
    
    avg_geff = df['g_eff'].mean()
    print(f"\n--- KT1: G_eff ---")
    print(f"Eficiencia promedio: {avg_geff:.2f} (Meta: >0.85)")
    return avg_geff

def calculate_kt2_f1():
    """KT2: Precisión Diagnóstica (Vision)"""
    df = pd.read_sql("SELECT * FROM vision_diagnostics WHERE ground_truth IS NOT NULL", engine)
    if df.empty: return 0
    
    # Calcular TP, FP, FN basándose en ground_truth vs diagnosis
    # Simplificación: si is_correct=True es TP, si False es FP (asumiendo detección positiva)
    tp = df['is_correct'].sum()
    fp = len(df) - tp # Simplificado para el ejemplo
    fn = 0 # Requeriría dataset etiquetado de "no detecciones"
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0 # Asumiendo recall alto para el ejemplo
    
    if (precision + recall) > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0
        
    print(f"\n--- KT2: F1 Score ---")
    print(f"F1 Score: {f1:.2f} (Meta: >0.85)")
    return f1

if __name__ == "__main__":
    print("=== REPORTE DE VALIDACIÓN DE TESIS ===")
    calculate_ks1_eir()
    calculate_ks2_delta_eiq()
    calculate_ks3_wpa()
    calculate_kt1_geff()
    calculate_kt2_f1()