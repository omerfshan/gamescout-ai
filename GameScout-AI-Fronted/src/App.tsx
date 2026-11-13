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
    await logout();
    setSessionNotice('');
    setUser(null);
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="GameScout AI ana sayfa"><span className="brand-mark">G</span><span>GameScout<span className="brand-ai"> AI</span></span></a>
      <p className="sidebar-caption">Araştırmadan fikre.</p>
      <nav aria-label="Ana gezinme"><a href="#main" aria-current="page">◈ <span>Oyun keşfi</span></a></nav>
      <div className="sidebar-footer">
        <span className="status-dot" />
        {user ? <>{user.name}<small>{user.email}</small></> : <>Oturum bekleniyor<small>Kullanıcıya özel katalog</small></>}
      </div>
    </aside>
    <main id="main" className="main-content">
      {checkingSession ? (
        <p className="empty-state" role="status">Oturum doğrulanıyor…</p>
      ) : user ? (
        <GamesPage user={user} onLogout={handleLogout} />
      ) : (
        <LoginForm onAuthenticated={handleAuthenticated} sessionNotice={sessionNotice} />
      )}
      <footer className="page-footer">GameScout AI · Kaynak olmadan iddia yok.</footer>
    </main>
  </div>;
}
