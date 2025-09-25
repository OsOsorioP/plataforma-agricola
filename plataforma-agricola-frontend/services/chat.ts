import apiClient from "./api";
import { ChatRequest, ChatResponse } from "@/types/chat";

export const sendChatMessage = async (
  message: string,
  imageUri: string | null 
): Promise<ChatResponse> => {
  try {
    const response = await apiClient.post<ChatResponse>("/chat/", {
      message: message,
      image_base64: imageUri
    });
    return response.data;
  } catch (error) {
    console.error("Error sending chat message:", error);
    throw error;
  }
};
