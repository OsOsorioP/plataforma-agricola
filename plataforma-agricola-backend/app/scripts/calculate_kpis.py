"""
Herramientas de Validación Manual para KPIs
Permite a expertos/evaluadores validar diagnósticos y recomendaciones
"""

import os
import sys
import csv
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..db.database import SessionLocal
from app.db import db_models


class ValidationTool:
    """
    Herramienta interactiva para validación manual de KPIs
    """
    
    def __init__(self):
        self.db = SessionLocal()
        self.validation_log = []
        
    def __del__(self):
        self.db.close()
    
    # =========================================================================
    # VALIDACIÓN DE DIAGNÓSTICOS (KT2)
    # =========================================================================
    
    def get_unvalidated_diagnostics(self, limit: int = 10) -> List[db_models.VisionDiagnostic]:
        """
        Obtiene diagnósticos sin validar (ground_truth = NULL)
        """
        return self.db.query(db_models.VisionDiagnostic).filter(
            db_models.VisionDiagnostic.ground_truth.is_(None)
        ).limit(limit).all()
    
    def validate_diagnostic_interactive(self):
        """
        Modo interactivo para validar diagnósticos uno por uno
        """
        print("\n" + "="*80)
        print("VALIDACIÓN INTERACTIVA DE DIAGNÓSTICOS (KT2)")
        print("="*80)
        
        unvalidated = self.get_unvalidated_diagnostics(limit=50)
        
        if not unvalidated:
            print("\n✓ No hay diagnósticos pendientes de validación")
            return
        
        print(f"\nEncontrados {len(unvalidated)} diagnósticos sin validar\n")
        
        for idx, diagnostic in enumerate(unvalidated, 1):
            print(f"\n{'='*80}")
            print(f"DIAGNÓSTICO {idx}/{len(unvalidated)}")
            print(f"{'='*80}")
            print(f"ID: {diagnostic.id}")
            print(f"Fecha: {diagnostic.timestamp}")
            print(f"Usuario: {diagnostic.user_id}")
            print(f"Parcela: {diagnostic.parcel_id or 'N/A'}")
            print(f"\nDIAGNÓSTICO DEL SISTEMA: {diagnostic.diagnosis}")
            print(f"Confianza: {diagnostic.confidence:.2%}")
            print(f"Tiempo de procesamiento: {diagnostic.processing_time:.2f}s")
            print(f"\nCondiciones de imagen:")
            if diagnostic.image_conditions:
                for key, value in diagnostic.image_conditions.items():
                    print(f"  - {key}: {value}")
            
            print("\n" + "-"*80)
            print("VALIDACIÓN:")
            print("1. Correcto")
            print("2. Incorrecto")
            print("3. Saltar (validar después)")
            print("4. Salir")
            
            choice = input("\nOpción: ").strip()
            
            if choice == "1":
                diagnostic.ground_truth = diagnostic.diagnosis
                diagnostic.is_correct = True
                self.db.commit()
                print("✓ Marcado como CORRECTO")
                self.validation_log.append({
                    "id": diagnostic.id,
                    "resultado": "correcto",
                    "timestamp": datetime.now().isoformat()
                })
                
            elif choice == "2":
                print("\nIngresa el diagnóstico CORRECTO (ground truth):")
                ground_truth = input("> ").strip()
                
                if ground_truth:
                    diagnostic.ground_truth = ground_truth
                    diagnostic.is_correct = False
                    self.db.commit()
                    print("✓ Marcado como INCORRECTO")
                    print(f"  Ground Truth: {ground_truth}")
                    self.validation_log.append({
                        "id": diagnostic.id,
                        "resultado": "incorrecto",
                        "ground_truth": ground_truth,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    print("✗ Ground truth vacío, saltando...")
                    
            elif choice == "3":
                print("⊙ Saltado")
                continue
                
            elif choice == "4":
                print("\nSaliendo...")
                break
            
            else:
                print("✗ Opción inválida")
        
        self._save_validation_log()
        print(f"\n✓ Validación completada. {len(self.validation_log)} diagnósticos procesados.")
    
    def validate_diagnostic_batch_csv(self, csv_path: str):
        """
        Validación por lotes desde archivo CSV
        
        Formato CSV esperado:
        diagnostic_id,ground_truth,is_correct
        123,"Tizón tardío",True
        124,"Deficiencia de nitrógeno",False
        """
        print(f"\nCargando validaciones desde: {csv_path}")
        
        if not os.path.exists(csv_path):
            print(f"✗ Archivo no encontrado: {csv_path}")
            return
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                diagnostic_id = int(row['diagnostic_id'])
                ground_truth = row['ground_truth'].strip()
                is_correct = row['is_correct'].lower() == 'true'
                
                diagnostic = self.db.query(db_models.VisionDiagnostic).filter(
                    db_models.VisionDiagnostic.id == diagnostic_id
                ).first()
                
                if diagnostic:
                    diagnostic.ground_truth = ground_truth
                    diagnostic.is_correct = is_correct
                    self.db.commit()
                    print(f"✓ Diagnóstico {diagnostic_id} actualizado")
                else:
                    print(f"✗ Diagnóstico {diagnostic_id} no encontrado")
        
        print(f"\n✓ Validación por lotes completada")
    
    def export_diagnostics_for_validation(self, output_path: str = "validation_diagnostics.csv"):
        """
        Exporta diagnósticos sin validar a CSV para revisión offline
        """
        unvalidated = self.get_unvalidated_diagnostics(limit=100)
        
        if not unvalidated:
            print("✓ No hay diagnósticos pendientes")
            return
        
        os.makedirs('validation_data', exist_ok=True)
        filepath = f'validation_data/{output_path}'
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['diagnostic_id', 'timestamp', 'user_id', 'parcel_id', 
                         'diagnosis', 'confidence', 'ground_truth', 'is_correct']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for d in unvalidated:
                writer.writerow({
                    'diagnostic_id': d.id,
                    'timestamp': d.timestamp.isoformat(),
                    'user_id': d.user_id,
                    'parcel_id': d.parcel_id or '',
                    'diagnosis': d.diagnosis,
                    'confidence': f"{d.confidence:.2f}",
                    'ground_truth': '',  # Para llenar manualmente
                    'is_correct': ''     # Para llenar manualmente
                })
        
        print(f"\n✓ Exportados {len(unvalidated)} diagnósticos a: {filepath}")
        print(f"\nInstrucciones:")
        print(f"1. Abre el archivo en Excel")
        print(f"2. Llena las columnas 'ground_truth' e 'is_correct'")
        print(f"3. Guarda el archivo")
        print(f"4. Ejecuta: validate_diagnostic_batch_csv('{filepath}')")
    
    # =========================================================================
    # VALIDACIÓN DE INTERVENCIONES (KS1, KS2)
    # =========================================================================
    
    def review_interventions(self, start_date: Optional[datetime] = None):
        """
        Revisar intervenciones para verificar si usuarios aceptaron alternativas
        """
        query = self.db.query(db_models.InterventionEvent).filter(
            db_models.InterventionEvent.was_vetoed == True,
            db_models.InterventionEvent.user_accepted.is_(None)
        )
        
        if start_date:
            query = query.filter(db_models.InterventionEvent.timestamp >= start_date)
        
        interventions = query.limit(20).all()
        
        if not interventions:
            print("\n✓ No hay intervenciones pendientes de seguimiento")
            return
        
        print(f"\nEncontradas {len(interventions)} intervenciones sin seguimiento\n")
        
        for idx, intervention in enumerate(interventions, 1):
            print(f"\n{'='*80}")
            print(f"INTERVENCIÓN {idx}/{len(interventions)}")
            print(f"{'='*80}")
            print(f"ID: {intervention.id}")
            print(f"Fecha: {intervention.timestamp}")
            print(f"Químico propuesto: {intervention.chemical_proposed}")
            print(f"Categoría: {intervention.chemical_category}")
            print(f"EIQ base: {intervention.eiq_base}")
            print(f"\nAlternativa propuesta:")
            print(f"{intervention.alternative_proposed}")
            print(f"\nEIQ alternativo: {intervention.eiq_alternative}")
            print(f"Reducción: {intervention.delta_eiq_percent:.1f}%")
            
            print("\n" + "-"*80)
            print("¿Usuario aceptó la alternativa?")
            print("1. Sí")
            print("2. No")
            print("3. Desconocido/Saltar")
            print("4. Salir")
            
            choice = input("\nOpción: ").strip()
            
            if choice == "1":
                intervention.user_accepted = True
                self.db.commit()
                print("✓ Marcado como ACEPTADO")
                
            elif choice == "2":
                intervention.user_accepted = False
                self.db.commit()
                print("✓ Marcado como RECHAZADO")
                
            elif choice == "3":
                print("⊙ Saltado")
                continue
                
            elif choice == "4":
                break
            
            else:
                print("✗ Opción inválida")
        
        print(f"\n✓ Seguimiento completado")
    
    # =========================================================================
    # VALIDACIÓN DE ALERTAS DE RIESGO (KE1)
    # =========================================================================
    
    def validate_risk_alerts(self):
        """
        Validar si alertas de riesgo fueron correctas y si se tomaron acciones
        """
        query = self.db.query(db_models.RiskAlert).filter(
            db_models.RiskAlert.actual_event_occurred.is_(None)
        )
        
        alerts = query.limit(20).all()
        
        if not alerts:
            print("\n✓ No hay alertas pendientes de validación")
            return
        
        print(f"\nEncontradas {len(alerts)} alertas sin validar\n")
        
        for idx, alert in enumerate(alerts, 1):
            print(f"\n{'='*80}")
            print(f"ALERTA {idx}/{len(alerts)}")
            print(f"{'='*80}")
            print(f"ID: {alert.id}")
            print(f"Fecha alerta: {alert.alert_sent_at}")
            print(f"Tipo de riesgo: {alert.risk_type}")
            print(f"Probabilidad: {alert.probability:.0%}")
            print(f"Pérdida proyectada: ${alert.projected_loss:,.2f}")
            print(f"Anticipación: {alert.hours_before_event}h")
            
            print("\n" + "-"*80)
            print("¿El evento ocurrió realmente?")
            print("1. Sí, ocurrió")
            print("2. No ocurrió")
            print("3. Saltar")
            print("4. Salir")
            
            choice = input("\nOpción: ").strip()
            
            if choice == "1":
                alert.actual_event_occurred = True
                
                print("\n¿Usuario tomó acción preventiva?")
                action_choice = input("(s/n): ").strip().lower()
                alert.user_action_taken = (action_choice == 's')
                
                if alert.user_action_taken:
                    print("Descripción de la acción:")
                    alert.action_description = input("> ").strip()
                    
                    print("\nPérdida real (USD, 0 si se evitó completamente):")
                    try:
                        alert.actual_loss = float(input("> ").strip())
                        alert.value_saved = max(0, alert.projected_loss - alert.actual_loss)
                    except:
                        print("✗ Valor inválido")
                else:
                    print("\nPérdida real (USD):")
                    try:
                        alert.actual_loss = float(input("> ").strip())
                        alert.value_saved = 0
                    except:
                        print("✗ Valor inválido")
                
                self.db.commit()
                print("✓ Alerta validada")
                
            elif choice == "2":
                alert.actual_event_occurred = False
                alert.value_saved = 0
                self.db.commit()
                print("✓ Marcado como falsa alarma")
                
            elif choice == "3":
                print("⊙ Saltado")
                continue
                
            elif choice == "4":
                break
            
            else:
                print("✗ Opción inválida")
        
        print(f"\n✓ Validación de alertas completada")
    
    # =========================================================================
    # GENERACIÓN DE PLANTILLAS
    # =========================================================================
    
    def generate_validation_templates(self):
        """
        Genera plantillas CSV vacías para validación manual
        """
        os.makedirs('validation_templates', exist_ok=True)
        
        # Plantilla para diagnósticos
        with open('validation_templates/diagnostics_template.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['diagnostic_id', 'diagnosis_sistema', 'ground_truth', 'is_correct', 'observaciones'])
            writer.writerow(['123', 'Tizón tardío', '', 'True/False', 'Opcional'])
        
        # Plantilla para intervenciones
        with open('validation_templates/interventions_template.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['intervention_id', 'chemical_proposed', 'alternative', 'user_accepted', 'observaciones'])
            writer.writerow(['123', 'Imidacloprid', 'Chrysoperla carnea', 'True/False', 'Opcional'])
        
        # Plantilla para alertas
        with open('validation_templates/alerts_template.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['alert_id', 'risk_type', 'event_occurred', 'action_taken', 'actual_loss', 'observaciones'])
            writer.writerow(['123', 'HELADA', 'True/False', 'True/False', '0.00', 'Opcional'])
        
        print("\n✓ Plantillas generadas en: ./validation_templates/")
        print("\nArchivos creados:")
        print("  - diagnostics_template.csv")
        print("  - interventions_template.csv")
        print("  - alerts_template.csv")
    
    def _save_validation_log(self):
        """
        Guarda log de validaciones realizadas
        """
        if not self.validation_log:
            return
        
        os.makedirs('validation_data', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f'validation_data/validation_log_{timestamp}.json'
        
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "validations": self.validation_log
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Log de validación guardado en: {filepath}")


# =========================================================================
# MENÚ INTERACTIVO
# =========================================================================

def interactive_menu():
    """
    Menú interactivo para validación manual
    """
    tool = ValidationTool()
    
    while True:
        print("\n" + "="*80)
        print("HERRAMIENTA DE VALIDACIÓN MANUAL DE KPIs")
        print("="*80)
        print("\n1. Validar diagnósticos (KT2)")
        print("2. Exportar diagnósticos para validación offline")
        print("3. Importar validaciones desde CSV")
        print("4. Revisar intervenciones (KS1/KS2)")
        print("5. Validar alertas de riesgo (KE1)")
        print("6. Generar plantillas CSV")
        print("7. Salir")
        
        choice = input("\nOpción: ").strip()
        
        if choice == "1":
            tool.validate_diagnostic_interactive()
        elif choice == "2":
            tool.export_diagnostics_for_validation()
        elif choice == "3":
            csv_path = input("Ruta del archivo CSV: ").strip()
            tool.validate_diagnostic_batch_csv(csv_path)
        elif choice == "4":
            tool.review_interventions()
        elif choice == "5":
            tool.validate_risk_alerts()
        elif choice == "6":
            tool.generate_validation_templates()
        elif choice == "7":
            print("\nSaliendo...")
            break
        else:
            print("\n✗ Opción inválida")


if __name__ == "__main__":
    interactive_menu()