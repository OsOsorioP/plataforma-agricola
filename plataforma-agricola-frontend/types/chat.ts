export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  reply: string[];
}

export interface Message {
  id: string;
  sender: 'user' | 'ai';
  text?: string;
  imageUrl?: string | null | undefined;
}