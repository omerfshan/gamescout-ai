import { ApiError, clearAuthToken, requestJson, setAuthToken } from './client';
import type { AuthSession, AuthUser, LoginCredentials } from '../domain/auth';

export function isAuthUser(value: unknown): value is AuthUser {
  if (typeof value !== 'object' || value === null) return false;
  const user = value as Record<string, unknown>;
  return typeof user.id === 'number' && Number.isInteger(user.id) && user.id > 0 &&
    typeof user.name === 'string' && user.name.trim().length > 0 &&
    typeof user.email === 'string' && user.email.trim().length > 0;
}

export function isAuthSession(value: unknown): value is AuthSession {
  if (typeof value !== 'object' || value === null) return false;
  const session = value as Record<string, unknown>;
  return isAuthUser(session.user) &&
    typeof session.token === 'string' && session.token.trim().length > 0 &&
    session.token_type === 'Bearer';
}

export async function login(credentials: LoginCredentials): Promise<AuthSession> {
  const body = await requestJson('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: credentials.email.trim(),
      password: credentials.password,
      device_name: 'dashboard',
    }),
  });
  if (typeof body !== 'object' || body === null || !('data' in body) || !isAuthSession(body.data)) {
    throw new ApiError('INVALID_RESPONSE', 'Oturum yanıtı beklenen sözleşmeye uymuyor.');
  }
  setAuthToken(body.data.token);
  return body.data;
}

export async function fetchCurrentUser(signal?: AbortSignal): Promise<AuthUser> {
  const body = await requestJson('/api/v1/auth/me', { signal });
  if (typeof body !== 'object' || body === null || !('data' in body) || !isAuthUser(body.data)) {
    throw new ApiError('INVALID_RESPONSE', 'Kullanıcı yanıtı beklenen sözleşmeye uymuyor.');
  }
  return body.data;
}

export async function logout(): Promise<void> {
  try {
    await requestJson('/api/v1/auth/logout', { method: 'POST' });
  } catch {
    // Ignore network or 401 errors during logout teardown.
  } finally {
    clearAuthToken();
  }
}
