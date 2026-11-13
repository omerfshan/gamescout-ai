const AUTH_TOKEN_STORAGE_KEY = 'gamescout.auth.token';

let memoryToken: string | null = null;
const unauthorizedListeners = new Set<() => void>();

export class ApiError extends Error {
  constructor(public readonly code: string, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export function getAuthToken(): string | null {
  try {
    const stored = window.sessionStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
    if (stored && stored.trim().length > 0) {
      memoryToken = stored;
      return stored;
    }
  } catch {
    // Ignore storage access errors in restricted environments.
  }
  return memoryToken;
}

export function setAuthToken(token: string | null): void {
  const normalized = token && token.trim().length > 0 ? token.trim() : null;
  memoryToken = normalized;
  try {
    if (normalized) {
      window.sessionStorage.setItem(AUTH_TOKEN_STORAGE_KEY, normalized);
    } else {
      window.sessionStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    }
  } catch {
    // Ignore storage access errors in restricted environments.
  }
}

export function clearAuthToken(): void {
  setAuthToken(null);
}

export function onUnauthorized(handler: () => void): () => void {
  unauthorizedListeners.add(handler);
  return () => {
    unauthorizedListeners.delete(handler);
  };
}

function buildHeaders(custom?: HeadersInit, token?: string | null): Record<string, string> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (custom) {
    if (custom instanceof Headers) {
      custom.forEach((value, key) => {
        headers[key] = value;
      });
    } else if (Array.isArray(custom)) {
      for (const [key, value] of custom) {
        headers[key] = value;
      }
    } else {
      Object.assign(headers, custom);
    }
  }
  if (token && !('Authorization' in headers) && !('authorization' in headers)) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export async function requestJson(path: string, init?: RequestInit): Promise<unknown> {
  const activeToken = getAuthToken();
  const headers = buildHeaders(init?.headers, activeToken);
  let response: Response;
  try {
    response = await fetch(path, { credentials: 'same-origin', ...init, headers });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new ApiError('NETWORK_UNAVAILABLE', 'Sunucuya ulaşılamadı. Laravel API bağlantısını kontrol edin.');
  }
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new ApiError('INVALID_RESPONSE', 'Sunucu geçerli JSON döndürmedi.');
  }
  if (!response.ok) {
    if (response.status === 401 && activeToken) {
      clearAuthToken();
      unauthorizedListeners.forEach(listener => listener());
    }
    const error = typeof body === 'object' && body !== null && 'error' in body ? body.error : null;
    if (typeof error === 'object' && error !== null && 'code' in error && 'message' in error &&
        typeof error.code === 'string' && typeof error.message === 'string') {
      throw new ApiError(error.code, error.message);
    }
    throw new ApiError(`HTTP_${response.status}`, 'İstek tamamlanamadı.');
  }
  return body;
}
