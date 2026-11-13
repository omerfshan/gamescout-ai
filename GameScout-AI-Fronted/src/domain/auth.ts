export interface AuthUser {
  id: number;
  name: string;
  email: string;
}

export interface AuthSession {
  user: AuthUser;
  token: string;
  token_type: 'Bearer';
}

export interface LoginCredentials {
  email: string;
  password: string;
}
