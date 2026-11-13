import { useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { importGames } from '../../api/games';
import { StatusMessage } from '../../components/StatusMessage';

export function ImportForm({ onImported }: { onImported: () => void }) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(''); setSuccess('');
    const file = fileInput.current?.files?.[0];
    if (!file) { setError('Bir JSON dosyası seçin.'); return; }
    if (file.size > 1024 * 1024) { setError('Dosya en fazla 1 MiB olabilir.'); return; }
    setBusy(true);
    try {
      const text = await file.text();
      try { JSON.parse(text); } catch { throw new Error('Dosya geçerli JSON içermiyor.'); }
      await importGames(text);
      setSuccess('Veri içe aktarıldı. Oyun listesi yenileniyor.');
      onImported();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Dosya içe aktarılamadı.');
    } finally { setBusy(false); }
  }

  return <section className="import-panel" aria-labelledby="import-title">
    <div><span className="eyebrow">VERİ KAYNAĞI</span><h2 id="import-title">Veri seti yükle</h2><p>Kaynağı bilinen JSON verisini incelemeye başlayın.</p></div>
    <form onSubmit={submit} aria-busy={busy}>
      <label htmlFor="json-file">JSON dosyası <span>(en fazla 1 MiB)</span></label>
      <input ref={fileInput} id="json-file" type="file" accept=".json,application/json" disabled={busy} />
      <button type="submit" disabled={busy}>{busy ? 'Yükleniyor…' : 'Veriyi içe aktar'}</button>
    </form>
    {error && <StatusMessage kind="error" message={error} />}
    {success && <StatusMessage kind="success" message={success} />}
  </section>;
}
