import { StyleSheet, View, Text, KeyboardAvoidingView, Platform, FlatList, Image, TextInput, TouchableOpacity, ActivityIndicator } from "react-native";
import Ionicons from '@expo/vector-icons/Ionicons';
import { useState } from "react";
import { sendChatMessage } from '@/services/chat';
import * as ImagePicker from 'expo-image-picker';
import { Message } from "@/types/chat";

export default function Index() {
  const [messages, setMessages] = useState<Message[]>([{ id: '1', text: '!Hola¡ Soy tu asistente Agrosmi. ¿En qué puedo ayudarte hoy?', sender: 'ai' }]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [imagenUri, setImageUri] = useState<string | null>(null)
  const [imageBase64, setImageBase64] = useState<string | null | undefined>(null);

  const pickImage = async () => {
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images', 'videos'],
      allowsEditing: true,
      aspect: [4, 3],
      quality: 0.6,
      base64: true,
    });

    if (!result.canceled) {
      setImageUri(result.assets[0].uri);
      setImageBase64(result.assets[0].base64)
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: Message = { id: Date.now().toString() + 'user', sender: 'user', text: inputMessage, imageUrl:imagenUri };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await sendChatMessage(inputMessage, imageBase64 ? imageBase64 : null);
      const aiMessage: Message = { id: Date.now().toString() + 'ai', sender: 'ai', text: response.reply };
      setMessages((prevMessages) => [...prevMessages, aiMessage]);
    } catch (error) {
      console.error('Error sending chat message:', error);
      const errorMessage: Message = { id: Date.now().toString() + 'error', sender: 'ai', text: 'Lo siento, hubo un error al obtener la respuesta.' };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    } finally {
      setLoading(false);
      setImageUri(null);
      setImageBase64(null);
    }
  };

  const renderMessage = ({ item }: { item: Message }) => (
    <View style={[styles.messageBubble, item.sender === 'user' ? styles.userBubble : styles.aiBubble]}>
      <Text style={item.sender === 'user' ? styles.userText : styles.aiText}>{item.text}</Text>
      {item.imageUrl && (
        <Image source={{ uri: item.imageUrl }} style={styles.chatImage} />
      )}
    </View>
  );

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.container}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 60 : 90}
    >
      <FlatList
        data={messages}
        renderItem={renderMessage}
        keyExtractor={item => item.id}
        style={styles.messageList}
      />

      {loading && (
        <View style={styles.typingIndicatorContainer}>
          <Text style={styles.typingIndicatorText}>AgriAgent está escribiendo...</Text>
          <ActivityIndicator size="small" color="#666" />
        </View>
      )}

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={inputMessage}
          onChangeText={setInputMessage}
          placeholder="Escribe tu mensaje..."
          editable={!loading}
          multiline
        />
        <TouchableOpacity
          style={[styles.sendButton, loading && styles.sendButtonDisabled]}
          onPress={pickImage}
          disabled={loading}
        >
          <Ionicons name={'grid-outline'} size={15} color={'#e1e1e1'} />
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.sendButton, loading && styles.sendButtonDisabled]}
          onPress={handleSendMessage}
          disabled={loading}
        >
          <Ionicons name={'arrow-up-outline'} size={15} color={'#e1e1e1'} />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#25292e',
    alignItems: 'center',
    justifyContent: 'center',
  },
  imageContainer: {
    flex: 1,
  },
  footerContainer: {
    flex: 1 / 3,
    alignItems: 'center',
  },
  messageList: {
    flex: 1,
    padding: 10,
  },
  messageContainer: {
    borderRadius: 20,
    padding: 15,
    marginVertical: 5,
  },
  userMessageContainer: {
    backgroundColor: '#007bff',
    alignSelf: 'flex-end',
  },
  aiMessageContainer: {
    backgroundColor: '#ffffff',
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  messageText: {
    fontSize: 16,
    color: '#333',
  },
  userMessageText: {
    fontSize: 16,
    color: '#fff'
  },
  aiMessageText: {
    fontSize: 16,
    color: '#333'
  },
  typingIndicatorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingLeft: 20,
    paddingBottom: 5
  },
  typingIndicatorText: {
    color: '#666',
    marginRight: 10
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 10,
    borderWidth: 1,
    borderRadius: 20,
    alignItems: 'flex-end',
  },
  input: {
    flex: 1,
    minHeight: 45,
    maxHeight: 150,
    flexGrow: 1,
    flexShrink: 1,
    borderColor: '#ccc',
    borderRadius: 20,
    paddingHorizontal: 15,
    alignItems: 'center'
  },
  sendButton: {
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: 16,
    height: 24,
    width: 24,
    borderColor: 'gray',
  },
  sendButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  sendButtonDisabled: {
    backgroundColor: '#a0c8ff'
  },

  messageBubble: {
    padding: 10,
    borderRadius: 15,
    marginBottom: 10,
    maxWidth: '80%',
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#007bff',
  },
  aiBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#e0e0e0',
  },
  userText: {
    color: 'white',
  },
  aiText: {
    color: 'black',
  },
  chatImage: {
    height: 150,
    borderRadius: 10,
    marginTop: 5,
  },
})
