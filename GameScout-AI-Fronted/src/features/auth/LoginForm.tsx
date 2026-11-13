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

  return <section className="auth-split-shell" aria-labelledby="auth-title">
    <div className="auth-showcase-card">
      <div className="auth-showcase-badge">
        <span>PAZAR &amp; OYUNCU İSTİHBARAT MOTORU</span>
      </div>

      <h1 id="auth-title">Oyuncu Yorumlarından Sıradaki Oyunu Keşfedin.</h1>
      <p className="auth-showcase-lead">
        GameScout AI; mağaza incelemelerini ve oyuncu topluluklarını tarar, oyuncuların mevcut oyunlardaki şikayetlerini yakalar ve <strong>“Şu Oyun Yapılabilir!”</strong> diyerek kanıtlı oyun konseptleri çıkarır.
      </p>

      <div className="auth-feature-list">
        <div className="auth-feature-item">
          <div className="auth-feature-icon auth-feature-icon--blue" aria-hidden="true"></div>
          <div>
            <h3>Apple App Store &amp; Google Play Yorumları</h3>
            <p>Düşük puanlı oyuncu yorumlarındaki şikayetleri ve eksik mekanik taleplerini ayrıştırır.</p>
          </div>
        </div>

        <div className="auth-feature-item">
          <div className="auth-feature-icon auth-feature-icon--orange" aria-hidden="true">◉</div>
          <div>
            <h3>Reddit Topluluk Tartışmaları (r/AndroidGaming, r/iosgaming)</h3>
            <p>Oyuncuların “keşke şöyle bir oyun olsa” dediği organik tartışmaları ve karşılanmamış alt tür taleplerini tespit eder.</p>
          </div>
        </div>

        <div className="auth-feature-item">
          <div className="auth-feature-icon auth-feature-icon--emerald" aria-hidden="true">⚡</div>
          <div>
            <h3>Yerel Ollama AI Sentezi</h3>
            <p>Toplanan kanıtları çekirdek oynanış döngüsü, gelir modeli, prototip planı ve doğrudan alıntılarla raporlar.</p>
          </div>
        </div>
      </div>
    </div>

    <div className="auth-card-wrapper">
      <form className="auth-card" onSubmit={submit} aria-busy={busy} noValidate>
        <div className="auth-card__header">
          <span className="eyebrow">KULLANICI GİRİŞİ</span>
          <h2>Oturum Açın</h2>
          <p>Piyasa taramalarını başlatmak ve fırsat raporlarını incelemek için hesabınızla giriş yapın.</p>
        </div>

        {sessionNotice && !error && <StatusMessage kind="error" message={sessionNotice} />}
        {error && <StatusMessage kind="error" message={error} />}

        <div className="field">
          <label htmlFor="login-email">E-posta</label>
          <div className="input-with-icon">
            <span className="input-icon" aria-hidden="true">✉</span>
            <input
              id="login-email"
              type="email"
              autoComplete="username"
              placeholder="ornek@sirketiniz.com"
              value={email}
              onChange={event => setEmail(event.target.value)}
              disabled={busy}
              required
            />
          </div>
        </div>

        <div className="field">
          <label htmlFor="login-password">Parola</label>
          <div className="input-with-icon">
            <span className="input-icon" aria-hidden="true">🔒</span>
            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              placeholder="Parolanız"
              value={password}
              onChange={event => setPassword(event.target.value)}
              disabled={busy}
              minLength={8}
              required
            />
          </div>
        </div>

        <button type="submit" className="auth-submit-btn" disabled={busy}>
          {busy ? 'Giriş Yapılıyor…' : 'Giriş Yap →'}
        </button>

        <p className="auth-security-note">
          🔒 Oturum doğrulaması doğrudan Laravel API (<code>/api/v1/auth/login</code>) üzerinden gerçekleştirilir.
        </p>
      </form>
    </div>
  </section>;
}
