import { useEffect, useState } from 'react';
import { fetchCurrentUser, logout } from './api/auth';
import { clearAuthToken, getAuthToken, onUnauthorized } from './api/client';
import type { AuthSession, AuthUser } from './domain/auth';
import { LoginForm } from './features/auth/LoginForm';
import { GamesPage } from './features/games/GamesPage';

export default function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checkingSession, setCheckingSession] = useState<boolean>(() => getAuthToken() !== null);
  const [sessionNotice, setSessionNotice] = useState('');
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    return onUnauthorized(() => {
      setUser(null);
      setCheckingSession(false);
      setSessionNotice('Oturum süresi doldu veya geçersiz. Lütfen tekrar giriş yapın.');
    });
  }, []);

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      setCheckingSession(false);
      return;
    }
    const controller = new AbortController();
    setCheckingSession(true);
    fetchCurrentUser(controller.signal)
      .then(restoredUser => {
        if (!controller.signal.aborted) {
          setUser(restoredUser);
          setSessionNotice('');
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          clearAuthToken();
          setUser(null);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setCheckingSession(false);
        }
      });
    return () => controller.abort();
  }, []);

  function handleAuthenticated(session: AuthSession) {
    setSessionNotice('');
    setUser(session.user);
  }

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await logout();
      setSessionNotice('');
      setUser(null);
    } finally {
      setLoggingOut(false);
    }
  }

  return <div className="app-layout">
    <header className="top-navbar">
      <div className="top-navbar__inner">
        <a className="brand-logo" href="/" aria-label="GameScout AI ana sayfa">
          <span className="brand-logo__mark" aria-hidden="true">✦</span>
          <div className="brand-logo__text">
            <span className="brand-logo__title">GameScout <em>AI</em></span>
            <span className="brand-logo__subtitle">Otonom Pazar &amp; Oyun Fırsat İstihbaratı</span>
          </div>
        </a>

        {user && (
          <div className="top-navbar__right">
            <div className="navbar-user-controls" aria-label="Aktif araştırmacı oturumu">
              <div className="navbar-user-badge">
                <span className="navbar-user-avatar" aria-hidden="true">{user.name.charAt(0).toUpperCase()}</span>
                <div className="navbar-user-meta">
                  <strong>{user.name}</strong>
                  <span>{user.email}</span>
                </div>
              </div>
              <button
                type="button"
                className="navbar-logout-btn"
                onClick={handleLogout}
                disabled={loggingOut}
              >
                {loggingOut ? 'Çıkış yapılıyor…' : 'Çıkış Yap'}
              </button>
            </div>
          </div>
        )}
      </div>
    </header>

    <main id="main" className="main-workspace">
      {checkingSession ? (
        <div className="session-loader" role="status">
          <div className="radar-spinner" aria-hidden="true" />
          <p>Araştırmacı oturumu doğrulanıyor…</p>
        </div>
      ) : user ? (
        <GamesPage user={user} onLogout={handleLogout} />
      ) : (
        <LoginForm onAuthenticated={handleAuthenticated} sessionNotice={sessionNotice} />
      )}
    </main>

    <footer className="workspace-footer">
      <div className="workspace-footer__inner">
        <span><strong>GameScout AI</strong> · Kanıta Dayalı Otonom Oyun Fırsat İstihbaratı</span>
        <span>Apple App Store · Google Play · Reddit · Yerel Ollama LLM</span>
      </div>
    </footer>
  </div>;
}
