export interface UserBase {
  email: string;
  full_name?: string;
}

export interface UserCreate extends UserBase {
  password: string;
}

export interface User extends UserBase {
  id: number;
  is_active: boolean;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}