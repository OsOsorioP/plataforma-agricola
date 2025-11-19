import { Platform } from "react-native";

export const API_URL = Platform.OS === 'android' ? process.env.EXPO_PUBLIC_API_BASE_URL : process.env.EXPO_PUBLIC_API_BASE_URL_2;
console.log("Esta es la url: ", API_URL)