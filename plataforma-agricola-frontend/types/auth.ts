export interface UserProps {
  email: string;
  username: string;
  avatar?: string | null;
  id?: string;
}

export interface UserDataProps {
  username: string;
  email: string;
  avatar?: any;
}

export type AuthContextProps = {
  token: string | null;
  user: UserProps | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (
    email: string,
    password: string,
    username: string,
    avatar?: string
  ) => Promise<void>;
  signOut: () => Promise<void>;
  updateToken: (token: string) => Promise<void>;
};

export interface DecodedTokenProps {
  user: UserProps;
  exp: number;
  iat: number;
}
