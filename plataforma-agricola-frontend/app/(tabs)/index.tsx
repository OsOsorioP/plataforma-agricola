import { StyleSheet, View, Text, KeyboardAvoidingView, Platform, FlatList, TextInput, TouchableOpacity, ActivityIndicator } from "react-native";
import type { ListRenderItemInfo } from "react-native";
//import Button from '@/components/Button';
//import ImageViewer from "@/components/ImageViewer";
import { useCallback, useState } from "react";
import { sendMessageToChat } from "@/services/ChatService";

//const PlaceholderImage = require('@/assets/images/background-image.png')

type Props = {
  id: string;
  text: string;
  sender: string;
}

export default function Index() {
  const [messages, setMessages] = useState<Props[]>([{ id: '1', text: '!Hola¡ Soy tu asistente Agrosmi. ¿En qué puedo ayudarte hoy?', sender: 'ai' }]);
  const [inputText, setInputText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false)

  const handleSend = useCallback(async () => {

    if (inputText.trim().length === 0 || isLoading) {
      return;
    }

    const userMessage: Props = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
    };

    setMessages(prevMessages => [...prevMessages, userMessage]);

    setInputText('');

    setIsLoading(true);

    try {
      const response = await sendMessageToChat(userMessage.text);

      const aiResponse = {
        id: Date.now().toString() + '-ai',
        text: response.data.reply,
        sender: 'ai',
      };

      setMessages(prevMessages => [...prevMessages, aiResponse]);

    } catch (error) {
      console.error("Error al conectar con la API:", error);
      const errorMessage = {
        id: Date.now().toString() + '-error',
        text: 'Lo siento, no pude conectarme con mis servidores. Por favor, inténtalo de nuevo.',
        sender: 'ai',
      };

      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }

  }, [inputText, isLoading]);

  const renderMessage = ({ item }: ListRenderItemInfo<Props>) => (
    <View style={[
      styles.messageContainer,
      item.sender === 'user' ? styles.userMessageContainer : styles.aiMessageContainer
    ]}>
      <Text style={item.sender === 'user' ? styles.userMessageText : styles.aiMessageText}>{item.text}</Text>
    </View>
  );

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.container}
      keyboardVerticalOffset={90}
    >
      <FlatList
        data={messages}
        renderItem={renderMessage}
        keyExtractor={item => item.id}
        style={styles.messageList}
      />

      {isLoading && (
        <View style={styles.typingIndicatorContainer}>
          <Text style={styles.typingIndicatorText}>AgriAgent está escribiendo...</Text>
          <ActivityIndicator size="small" color="#666" />
        </View>
      )}

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Escribe tu mensaje..."
          editable={!isLoading}
        />
        <TouchableOpacity style={[styles.sendButton, isLoading && styles.sendButtonDisabled]} onPress={handleSend} disabled={isLoading}>
          <Text style={styles.sendButtonText}>Enviar</Text>
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
    maxWidth: '80%',
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
  inputContainer: {
    flexDirection: 'row',
    padding: 10,
    borderTopWidth: 1,
    borderTopColor: '#ccc',
    backgroundColor: '#fff',
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
  input: {
    flex: 1,
    height: 40,
    borderColor: '#ccc',
    borderWidth: 1,
    borderRadius: 20,
    paddingHorizontal: 15,
  },
  sendButton: {
    marginLeft: 10,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#007bff',
    borderRadius: 20,
    paddingHorizontal: 20,
  },
  sendButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  sendButtonDisabled: {
    backgroundColor: '#a0c8ff'
  }
})
