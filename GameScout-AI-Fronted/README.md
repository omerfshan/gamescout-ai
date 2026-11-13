# GameScout Dashboard

React + TypeScript ile **Otonom AI Oyun Fırsat Araştırmacısı** (`POST /api/v1/scout/runs`, `GET /api/v1/scout/latest`), kullanıcı oturumu (`login/session`), sentetik demo JSON yükleme ve kullanıcıya ait oyun kataloğu (`GET /api/v1/games`).

Kullanıcı herhangi bir tür seçmeden veya dosya yüklemeden tek tıkla App Store, Google Play ve Reddit oyuncu topluluklarını AI (Yerel Ollama veya harici OpenAI/Gemini API) ile tarayabilir; insanların hangi türden nasıl bir oyun istediğini ve hangi oyunun yapılabileceğini kanıt yorumlarıyla görebilir.

## Katmanlar

- `src/domain`: `scout.ts`, `auth.ts` ve `game.ts` veri sözleşmeleri.
- `src/api`: `client.ts` (Bearer token, 401 dinleyicisi, JSON hata modeli), `scout.ts`, `auth.ts` ve `games.ts` uç adaptörleri.
- `src/features/scout`: `OpportunityScoutPanel.tsx` ile Otonom AI Piyasa & Oyun Fırsat Araştırmacısı ekranı.
- `src/features/auth`: `LoginForm.tsx` ile kullanıcı girişi akışı.
- `src/features/games`: `GamesPage.tsx`, `ImportForm.tsx` ve `GameCard.tsx` ile kullanıcıya özel katalog ve JSON import akışı.
- `src/components`: ortak sunum bileşenleri (`StatusMessage.tsx`).

## Çalıştırma ve Doğrulama

```bash
cd GameScout-AI-Fronted
npm install
npm run typecheck
npm run build
npm run dev
```

Doğrulama durumu:
- `npm run typecheck` (`tsc --noEmit`) çalıştırıldı ve hatasız geçti.
- `npm run build` (`tsc --noEmit && vite build`) çalıştırıldı ve üretim paketi (`dist/`) başarıyla oluşturuldu.
