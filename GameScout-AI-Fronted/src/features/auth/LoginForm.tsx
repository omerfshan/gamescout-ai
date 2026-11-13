import { useState } from 'react';
import type { FormEvent } from 'react';
import { login } from '../../api/auth';
import type { AuthSession } from '../../domain/auth';
import { StatusMessage } from '../../components/StatusMessage';

interface Props {
  onAuthenticated: (session: AuthSession) => void;
  sessionNotice?: string;
}

export function LoginForm({ onAuthenticated, sessionNotice }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    const normalizedEmail = email.trim();
    if (!normalizedEmail) {
      setError('E-posta adresinizi girin.');
      return;
    }
    if (password.length < 8) {
      setError('Parola en az 8 karakter olmalıdır.');
      return;
    }
    setBusy(true);
    try {
      const session = await login({ email: normalizedEmail, password });
      setPassword('');
      onAuthenticated(session);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Oturum açılamadı.');
    } finally {
      setBusy(false);
    }
  }

  return <section className="auth-panel" aria-labelledby="auth-title">
    <div className="auth-panel__intro">
      <span className="eyebrow">ARAŞTIRMACI OTURUMU</span>
      <h1 id="auth-title">AI Oyun Fırsat Araştırmacısına erişmek için giriş yapın.</h1>
      <p>App Store, Google Play ve Reddit oyuncu yorumlarını tarayarak insanların hangi türde nasıl bir oyun beklediğini kanıtlarıyla keşfedin.</p>
      <p className="source-note">Doğrulama doğrudan Laravel API (<code>/api/v1/auth/login</code>) üzerinden yapılır.</p>
    </div>
    <form className="auth-form" onSubmit={submit} aria-busy={busy} noValidate>
      {sessionNotice && !error && <StatusMessage kind="error" message={sessionNotice} />}
      {error && <StatusMessage kind="error" message={error} />}
      <div className="field">
        <label htmlFor="login-email">E-posta</label>
        <input
          id="login-email"
          type="email"
          autoComplete="username"
          placeholder="arastirmaci@gamescout.ai"
          value={email}
          onChange={event => setEmail(event.target.value)}
          disabled={busy}
          required
        />
      </div>
      <div className="field">
        <label htmlFor="login-password">Parola</label>
        <input
          id="login-password"
          type="password"
          autoComplete="current-password"
          placeholder="En az 8 karakter"
          value={password}
          onChange={event => setPassword(event.target.value)}
          disabled={busy}
          minLength={8}
          required
        />
      </div>
      <button type="submit" disabled={busy}>{busy ? 'Giriş yapılıyor…' : 'Oturum aç'}</button>
    </form>
  </section>;
}
