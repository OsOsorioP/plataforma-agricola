import apiClient from "./api";
import { ChatRequest, ChatResponse } from "@/types/chat";

export const sendChatMessage = async (
  message: string
): Promise<ChatResponse> => {
  try {
    const response = await apiClient.post<ChatResponse>("/chat/", {
      message: message,
    });
    return response.data;
  } catch (error) {
    console.error("Error sending chat message:", error);
    throw error;
  }
};
