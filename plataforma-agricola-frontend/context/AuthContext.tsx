import { createContext, useState, ReactNode, useContext, useEffect } from 'react';
import * as SecureStore from 'expo-secure-store';
import { login, register } from '@/services/authService';
import { useRouter } from 'expo-router';
import { AuthContextProps, DecodedTokenProps, UserProps } from '@/types/auth';
import { jwtDecode } from 'jwt-decode'
import { Alert } from 'react-native';

export const AuthContext = createContext<AuthContextProps>({
  token: null,
  user: null,
  signIn: async () => { },
  signUp: async () => { },
  signOut: async () => { },
  updateToken: async () => { },
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserProps | null>(null);
  const router = useRouter()

  useEffect(() => {
    loadToken();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadToken = async () => {
    const storedToken = await SecureStore.getItemAsync("token");
    if (storedToken) {
      try {
        const decoded = jwtDecode<DecodedTokenProps>(storedToken);
        if (decoded.exp && decoded.exp < Date.now() / 1000) {
          await SecureStore.deleteItemAsync("token")
          goToWelcomePage();
          return;
        }
        setToken(storedToken);
        setUser(decoded.user)
        goToHomePage();
      } catch (error: any) {
        const errorMsg = error?.message
        Alert.alert("Ocurrio un error: ", errorMsg)
        goToWelcomePage();
      }
    } else {
      goToWelcomePage();
    }
  }

  const goToHomePage = () => {
    setTimeout(() => {
      router.replace("/(tabs)/chat")
    }, 1500)
  }

  const goToWelcomePage = () => {
    setTimeout(() => {
      router.replace("/(auth)/welcome")
    }, 1500)
  }

  const updateToken = async (token: string | null) => {
    if (token) {
      setToken(token);
      await SecureStore.setItemAsync("token", token);
      // decode token (user)
      const decoded = jwtDecode<DecodedTokenProps>(token)
      console.log("decoded token: ", decoded)
      setUser(decoded.user)
    }
  }

  const signIn = async (email: string, password: string) => {
    const response = await login(email, password);
    await updateToken(response.token);
    router.replace("/(tabs)/chat")
  }

  const signUp = async (email: string, password: string, username: string, avatar?: string | null) => {
    const response = await register(email, password, username, avatar);
    await updateToken(response.token);
    router.replace("/(tabs)/chat")
  }

  const signOut = async () => {
    setToken(null);
    setUser(null);
    await SecureStore.deleteItemAsync("token");
    router.replace("/(auth)/welcome")
  }

  return (
    <AuthContext.Provider value={{ token, user, signIn, signUp, signOut, updateToken }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext)