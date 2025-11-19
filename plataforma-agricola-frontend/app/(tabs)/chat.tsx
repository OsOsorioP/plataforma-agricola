import { StyleSheet, View, FlatList, Image, TouchableOpacity, KeyboardAvoidingView, Platform, Alert } from "react-native";
import Ionicons from '@expo/vector-icons/Ionicons';
import { useEffect, useState } from "react";
import * as ImagePicker from 'expo-image-picker';
import ScreenWrapper from "@/components/layout/ScreenWrapper";
import { colors, radius, spacingX, spacingY } from "@/constants/theme";
import { useAuth } from "@/context/AuthContext";
import { scale, verticalScale } from "@/utils/styling";
import Header from "@/components/layout/Header";
import MessageItem from "@/components/chat/MessageItem";
import Input from "@/components/ui/Input";
import { MessageProps } from "@/types/components";
import Loading from "@/components/ui/Loading";
import { chatHistory, sendChatMessage } from "@/services/chatService";

export default function Index() {
  const [messages, setMessages] = useState<MessageProps[]>();
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<ImagePicker.ImagePickerAsset | null>(null)

  const { user: currentUser, signOut } = useAuth()

  useEffect(() => {
    loadChatHistory()
  }, [loading])

  const onPickFile = async () => {
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      //allowsEditing: true,
      aspect: [4, 3],
      quality: 0.6,
      base64: true,
    });
    if (!result.canceled) {
      setSelectedFile(result.assets[0])
    }
  }

  const loadChatHistory = async () => {
    const response = await chatHistory()
    setMessages(response)
  }

  const onSend = async () => {
    setLoading(true);
    try {
      let messageCurrent = null
      if (selectedFile) {
        messageCurrent = { id: currentUser?.id, content: message, sender: 'user', isMe: true, attachement: selectedFile.base64 };
      } else {
        messageCurrent = { id: currentUser?.id, content: message, sender: 'user', isMe: true };
      }
      const response = await sendChatMessage(
        messageCurrent.content,
        selectedFile ? selectedFile.base64 : null
      )

      setMessages(response)
    } catch (error: any) {
      Alert.alert("Error", "Failed to send message")
      console.error(error)
    } finally {
      setLoading(false);
      setMessage("");
      setSelectedFile(null);
    }
  };

  return (
    <ScreenWrapper showPattern={true}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={styles.container}
      >
        <Header
          title={"Agrosmi"}
          style={{ backgroundColor: '#fff', padding: scale(4) }}
          leftIcon={
            <Image source={require("@/assets/images/logo.png")} style={styles.logo} resizeMode="contain" />
          }
          rightIcon={
            <TouchableOpacity style={{ marginBottom: verticalScale(7) }} onPress={signOut}>
              <Ionicons name="ellipsis-vertical-sharp" size={verticalScale(22)} color={colors.white} />
            </TouchableOpacity>
          }
        />
        <View style={styles.content}>
          <FlatList
            data={messages}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.messagesContent}
            renderItem={({ item }) => (
              <MessageItem item={item} />
            )}
            keyExtractor={(item, index) => item.id?.toString() || index.toString()}
          />
        </View>
        <View style={styles.footer}>
          <Input
            value={message}
            onChangeText={setMessage}
            containerStyle={{ paddingLeft: spacingX._10, paddingRight: scale(65), borderWidth: 0 }}
            editable={!loading}
            placeholder="Escribe tu mensaje..."
            multiline
            icon={
              <TouchableOpacity style={styles.inputIcon} onPress={onPickFile} disabled={loading}>
                <Ionicons name="add-outline" size={verticalScale(22)} color={colors.black} />
                {
                  selectedFile && selectedFile.uri && (
                    <Image
                      source={{ uri: selectedFile.uri }}
                      style={styles.selectedFile}
                    />
                  )
                }
              </TouchableOpacity>
            }
          />
          <View style={styles.inputRightIcon}>
            <TouchableOpacity style={styles.inputIcon} onPress={onSend}>
              {
                loading ? (
                  <Loading size={"small"} color={colors.black} />
                ) :
                  <Ionicons name="send" size={verticalScale(22)} color={colors.black} />
              }
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  inputIcon: {
    backgroundColor: colors.primary,
    borderRadius: radius.full,
    padding: 8,
  },
  inputRightIcon: {
    position: "absolute",
    right: scale(10),
    top: verticalScale(15),
    paddingLeft: spacingX._12,
    borderLeftWidth: 1.5,
    borderLeftColor: colors.neutral300
  },
  selectedFile: {
    position: "absolute",
    height: verticalScale(38),
    width: verticalScale(38),
    borderRadius: radius.full,
    alignSelf: "center"
  },
  content: {
    backgroundColor: 'transparent',
    flex: 1,
    overflow: "hidden",
    paddingHorizontal: spacingX._20
  },
  settingIcon: {
    padding: spacingY._10,
    backgroundColor: colors.neutral400,
    borderRadius: radius.full,
  },
  messagesContent: {
    // padding: spacingX._15
    paddingTop: spacingY._20,
    paddingBottom: spacingY._10,
    gap: spacingY._12,
  },
  footer: {
    paddingTop: spacingY._7,
    paddingBottom: verticalScale(10),
  },
  logo: {
    height: verticalScale(35),
    aspectRatio: 1,
  }
})
