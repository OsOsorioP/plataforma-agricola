import { MessageProps } from "@/types/components";
import apiClient from "./apiService";

export const sendChatMessage = async (
  message: string,
  image_base64: string | null | undefined
): Promise<MessageProps[]> => {
  try {
    const response = await apiClient.post<MessageProps[]>("/chat/", {
      message: message,
      image_base64: image_base64,
    });
    console.log(response.data);
    return response.data;
  } catch (error) {
    console.error("Error sending chat message:", error);
    throw error;
  }
};

export const chatHistory = async () => {
  try {
    const response = await apiClient.get<MessageProps[]>("/chat/history");
    console.log(response.data);
    return response.data;
  } catch (error) {
    console.error("Error loading chat history:", error);
    throw error;
  }
};
