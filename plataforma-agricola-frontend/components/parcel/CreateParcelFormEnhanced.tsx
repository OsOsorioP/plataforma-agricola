import React, { useState } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  Button, 
  Alert, 
  ScrollView, 
  StyleSheet,
  TouchableOpacity,
  Platform
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import DateTimePicker from '@react-native-community/datetimepicker';
import { 
  ParcelCreate, 
  CROP_OPTIONS, 
  STAGE_OPTIONS, 
  SOIL_OPTIONS, 
  IRRIGATION_OPTIONS 
} from '@/types/parcels';
import { createParcel } from '@/services/parcelService';

interface CreateParcelFormEnhancedProps {
  onParcelCreated: () => void;
  onCancel: () => void;
  geometryData: {
    geometry: string;
    area: number;
    location: string;
  };
}

export function CreateParcelFormEnhanced({ 
  onParcelCreated, 
  onCancel,
  geometryData 
}: CreateParcelFormEnhancedProps) {
  // Estado básico
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Estado de cultivo (NUEVO)
  const [cropType, setCropType] = useState('');
  const [developmentStage, setDevelopmentStage] = useState('');
  const [plantingDate, setPlantingDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  
  // Estado de suelo (NUEVO)
  const [soilType, setSoilType] = useState('');
  const [soilPh, setSoilPh] = useState('');
  
  // Estado de riego (NUEVO)
  const [irrigationType, setIrrigationType] = useState('');
  
  // Paso del formulario
  const [step, setStep] = useState(1);

  const handleSubmit = async () => {
    if (!name.trim()) {
      Alert.alert('Error', 'El nombre de la parcela es obligatorio');
      return;
    }

    setLoading(true);
    
    const parcelData: ParcelCreate = {
      name: name.trim(),
      location: geometryData.location,
      area: geometryData.area,
      geometry: geometryData.geometry,
      
      // Nuevos campos opcionales - Solo incluir si tienen valor
      crop_type: cropType || undefined,
      development_stage: developmentStage || undefined,
      planting_date: cropType ? plantingDate.toISOString() : undefined,
      soil_type: soilType || undefined,
      soil_ph: soilPh ? parseFloat(soilPh) : undefined,
      irrigation_type: irrigationType || undefined,
    };

    try {
      await createParcel(parcelData);
      Alert.alert(
        'Éxito', 
        'Parcela creada correctamente. El asistente IA ahora podrá darte recomendaciones más precisas.',
        [{ text: 'OK', onPress: onParcelCreated }]
      );
    } catch (error: any) {
      Alert.alert('Error', error.message || 'No se pudo crear la parcela');
    } finally {
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>1. Información Básica</Text>
      
      <Text style={styles.label}>Nombre de la Parcela *</Text>
      <TextInput
        style={styles.input}
        placeholder="Ej: Lote 1, Parcela Norte, Potrero Alto"
        value={name}
        onChangeText={setName}
      />

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>📍 Área calculada</Text>
        <Text style={styles.infoValue}>{geometryData.area.toFixed(2)} hectáreas</Text>
        <Text style={styles.infoSubtext}>({(geometryData.area * 10000).toFixed(0)} m²)</Text>
      </View>
      
      <View style={styles.buttonRow}>
        <Button title="Cancelar" onPress={onCancel} color="#999" />
        <Button 
          title="Siguiente" 
          onPress={() => setStep(2)} 
          disabled={!name.trim()}
        />
      </View>
    </View>
  );

  const renderStep2 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>2. Información del Cultivo</Text>
      <Text style={styles.subtitle}>(Opcional - ayuda al asistente IA)</Text>
      
      <Text style={styles.label}>¿Qué cultivo tienes plantado?</Text>
      <View style={styles.pickerContainer}>
        <Picker
          selectedValue={cropType}
          onValueChange={(value) => {
            setCropType(value);
            if (!value) {
              setDevelopmentStage('');
            }
          }}
          style={styles.picker}
        >
          <Picker.Item label="Selecciona un cultivo (opcional)" value="" />
          {CROP_OPTIONS.map(option => (
            <Picker.Item key={option.value} label={option.label} value={option.value} />
          ))}
        </Picker>
      </View>

      {cropType && (
        <>
          <Text style={styles.label}>¿En qué etapa está?</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={developmentStage}
              onValueChange={(value) => setDevelopmentStage(value)}
              style={styles.picker}
            >
              <Picker.Item label="Selecciona una etapa" value="" />
              {STAGE_OPTIONS.map(option => (
                <Picker.Item key={option.value} label={option.label} value={option.value} />
              ))}
            </Picker>
          </View>

          <Text style={styles.label}>Fecha de siembra</Text>
          <TouchableOpacity 
            style={styles.dateButton}
            onPress={() => setShowDatePicker(true)}
          >
            <Text style={styles.dateText}>
              📅 {plantingDate.toLocaleDateString('es-ES', { 
                day: 'numeric', 
                month: 'long', 
                year: 'numeric' 
              })}
            </Text>
          </TouchableOpacity>
          
          {showDatePicker && (
            <DateTimePicker
              value={plantingDate}
              mode="date"
              maximumDate={new Date()}
              onChange={(event, date) => {
                setShowDatePicker(Platform.OS === 'ios');
                if (date) setPlantingDate(date);
              }}
            />
          )}
        </>
      )}

      <View style={styles.helpBox}>
        <Text style={styles.helpText}>
          💡 <Text style={styles.helpBold}>¿Por qué importa?</Text>{'\n'}
          Con esta información, el asistente IA podrá calcular necesidades exactas de agua, 
          fertilizantes y detectar problemas específicos de tu cultivo.
        </Text>
      </View>

      <View style={styles.buttonRow}>
        <Button title="Atrás" onPress={() => setStep(1)} color="#999" />
        <Button title={cropType ? "Siguiente" : "Omitir"} onPress={() => setStep(3)} />
      </View>
    </View>
  );

  const renderStep3 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>3. Suelo y Riego</Text>
      <Text style={styles.subtitle}>(Opcional - mejora el análisis)</Text>
      
      <Text style={styles.label}>Tipo de suelo</Text>
      <View style={styles.pickerContainer}>
        <Picker
          selectedValue={soilType}
          onValueChange={(value) => setSoilType(value)}
          style={styles.picker}
        >
          <Picker.Item label="Selecciona tipo de suelo (opcional)" value="" />
          {SOIL_OPTIONS.map(option => (
            <Picker.Item key={option.value} label={option.label} value={option.value} />
          ))}
        </Picker>
      </View>

      <Text style={styles.label}>pH del suelo (0-14)</Text>
      <TextInput
        style={styles.input}
        placeholder="Ej: 6.5 (opcional)"
        value={soilPh}
        onChangeText={(text) => {
          // Solo permitir números y punto decimal
          const cleaned = text.replace(/[^0-9.]/g, '');
          setSoilPh(cleaned);
        }}
        keyboardType="decimal-pad"
      />

      <Text style={styles.label}>Sistema de riego</Text>
      <View style={styles.pickerContainer}>
        <Picker
          selectedValue={irrigationType}
          onValueChange={(value) => setIrrigationType(value)}
          style={styles.picker}
        >
          <Picker.Item label="Selecciona sistema de riego (opcional)" value="" />
          {IRRIGATION_OPTIONS.map(option => (
            <Picker.Item key={option.value} label={option.label} value={option.value} />
          ))}
        </Picker>
      </View>

      <View style={styles.helpBox}>
        <Text style={styles.helpText}>
          💡 <Text style={styles.helpBold}>¿Por qué importa?</Text>{'\n'}
          • <Text style={styles.helpBold}>Tipo de suelo:</Text> Determina retención de agua y nutrientes{'\n'}
          • <Text style={styles.helpBold}>pH:</Text> Afecta disponibilidad de nutrientes{'\n'}
          • <Text style={styles.helpBold}>Sistema de riego:</Text> Influye en eficiencia y programación
        </Text>
      </View>

      <View style={styles.buttonRow}>
        <Button title="Atrás" onPress={() => setStep(2)} color="#999" />
        <Button 
          title={loading ? "Guardando..." : "Crear Parcela"} 
          onPress={handleSubmit}
          disabled={loading}
          color="#4CAF50"
        />
      </View>
    </View>
  );

  return (
    <ScrollView style={styles.container}>
      {/* Barra de progreso */}
      <View style={styles.progressBar}>
        <View style={[styles.progressStep, step >= 1 && styles.progressStepActive]} />
        <View style={[styles.progressStep, step >= 2 && styles.progressStepActive]} />
        <View style={[styles.progressStep, step >= 3 && styles.progressStepActive]} />
      </View>

      <View style={styles.progressLabels}>
        <Text style={[styles.progressLabel, step === 1 && styles.progressLabelActive]}>
          Básico
        </Text>
        <Text style={[styles.progressLabel, step === 2 && styles.progressLabelActive]}>
          Cultivo
        </Text>
        <Text style={[styles.progressLabel, step === 3 && styles.progressLabelActive]}>
          Suelo
        </Text>
      </View>

      {step === 1 && renderStep1()}
      {step === 2 && renderStep2()}
      {step === 3 && renderStep3()}

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          ✨ Los campos opcionales son completamente voluntarios. {'\n'}
          Puedes agregar o actualizar esta información más tarde.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  progressBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  progressStep: {
    flex: 1,
    height: 4,
    backgroundColor: '#ddd',
    marginHorizontal: 2,
    borderRadius: 2,
  },
  progressStepActive: {
    backgroundColor: '#4CAF50',
  },
  progressLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  progressLabel: {
    flex: 1,
    textAlign: 'center',
    fontSize: 12,
    color: '#999',
  },
  progressLabelActive: {
    color: '#4CAF50',
    fontWeight: 'bold',
  },
  stepContainer: {
    gap: 15,
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 10,
    marginBottom: 20,
  },
  stepTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 5,
    color: '#333',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 10,
    fontStyle: 'italic',
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 5,
    color: '#333',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    backgroundColor: '#fff',
    overflow: 'hidden',
  },
  picker: {
    height: 50,
  },
  dateButton: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    backgroundColor: '#fff',
  },
  dateText: {
    fontSize: 16,
    color: '#333',
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
    gap: 10,
  },
  infoCard: {
    backgroundColor: '#e8f5e9',
    padding: 15,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#4CAF50',
  },
  infoTitle: {
    fontSize: 14,
    color: '#2e7d32',
    fontWeight: '600',
    marginBottom: 5,
  },
  infoValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1b5e20',
  },
  infoSubtext: {
    fontSize: 12,
    color: '#558b2f',
    marginTop: 2,
  },
  helpBox: {
    backgroundColor: '#fff3e0',
    padding: 15,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#ff9800',
    marginTop: 10,
  },
  helpText: {
    fontSize: 13,
    color: '#e65100',
    lineHeight: 20,
  },
  helpBold: {
    fontWeight: 'bold',
  },
  footer: {
    padding: 15,
    marginTop: 10,
    marginBottom: 20,
  },
  footerText: {
    fontSize: 12,
    color: '#999',
    textAlign: 'center',
    lineHeight: 18,
  },
});