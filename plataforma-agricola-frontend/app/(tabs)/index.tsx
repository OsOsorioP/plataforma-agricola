import { StyleSheet, View, Text, KeyboardAvoidingView, Platform, FlatList, TextInput, TouchableOpacity } from "react-native";
import type { ListRenderItemInfo } from "react-native";
//import Button from '@/components/Button';
//import ImageViewer from "@/components/ImageViewer";
import { useCallback, useState } from "react";

//const PlaceholderImage = require('@/assets/images/background-image.png')

type Props = {
  id: string;
  text: string;
  sender: string;
}

export default function Index() {
  const [messages, setMessages] = useState<Props[]>([{ id: '1', text: '!Hola¡ Soy tu asistente Agrosmi. ¿En qué puedo ayudarte hoy?', sender: 'ai' }]);
  const [inputText, setInputText] = useState<string>('');

  const handleSend = useCallback(() => {

    if (inputText.trim().length === 0) {
      return;
    }

    const userMessage: Props = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
    };

    setMessages(prevMessages => [...prevMessages, userMessage]);

    setInputText('');

    setTimeout(() => {
      const aiResponse = {
        id: Date.now().toString() + '-ai',
        text: 'Procesando tu solicitud...',
        sender: 'ai',
      };
      setMessages(prevMessages => [...prevMessages, aiResponse]);
    }, 1000);

  }, [inputText]);

  const renderMessage = ({ item }: ListRenderItemInfo<Props>) => (
    <View style={[
      styles.messageContainer,
      item.sender === 'user' ? styles.userMessageContainer : styles.aiMessageContainer
    ]}>
      <Text style={styles.messageText}>{item.text}</Text>
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

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Escribe tu mensaje..."
        />

        <TouchableOpacity style={styles.sendButton} onPress={handleSend}>
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
})
