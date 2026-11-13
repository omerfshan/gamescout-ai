import { useState } from 'react';
import type { AuthUser } from '../../domain/auth';
import { OpportunityScoutPanel } from '../scout/OpportunityScoutPanel';

interface Props {
  user: AuthUser;
  onLogout: () => Promise<void>;
}

export function GamesPage({ user, onLogout }: Props) {
  const [loggingOut, setLoggingOut] = useState(false);

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await onLogout();
    } finally {
      setLoggingOut(false);
    }
  }

  return <>
    <header className="page-header">
      <div>
        <span className="eyebrow">OTONOM PAZAR ARAŞTIRMASI / AI KEŞİF</span>
        <h1>İnsanlar hangi oyunu bekliyor?<br />AI piyasayı tarasın ve söylesin.</h1>
        <p>App Store, Google Play ve Reddit oyuncu topluluklarındaki gerçek talepleri analiz ederek yapılabilir oyun fırsatlarını keşfet.</p>
      </div>
      <div className="header-aside">
        <div className="user-bar" aria-label="Aktif araştırmacı oturumu">
          <div>
            <strong>{user.name}</strong>
            <span>{user.email} · Araştırmacı hesabı</span>
          </div>
          <button type="button" className="secondary logout-button" onClick={handleLogout} disabled={loggingOut}>
            {loggingOut ? 'Çıkış yapılıyor…' : 'Çıkış yap'}
          </button>
        </div>
      </div>
    </header>

    <OpportunityScoutPanel />
  </>;
}
