# GameScout Laravel API — Dikey Dilimler (Giriş → Otonom Pazar Keşfi → Demo JSON İçe Aktarım → Oyun Listesi)

Katmanlı kaynak kodu (`SOLID` uyumlu):
- `Domain/Auth`, `Domain/Games` ve `Domain/Scout`: saf değer nesneleri (`AuthenticatedUser`, `AuthSession`, `GameData`), port arayüzleri (`UserAuthenticator`, `GameCatalog`, `MarketScoutRunner`, `ScoutReportStore`) ve alan istisnaları (`InvalidCredentials`, `ImportConflict`).
- `Application/Auth`, `Application/Games` ve `Application/Scout`: kullanım senaryoları (`LoginUser`, `GetAuthenticatedUser`, `LogoutUser`, `ImportDemoGames`, `ListGames`, `RunMarketScout`, `GetLatestScoutReport`).
- `Infrastructure/Auth`, `Infrastructure/Games` ve `Infrastructure/Scout`: Sanctum/veritabanı/Python CLI adaptörleri (`SanctumUserAuthenticator`, `PgsqlGameCatalog`, `DbScoutReportStore`, `PythonCliMarketScoutRunner`).
- `Http`: ince controller'lar (`AuthController`, `GameController`, `ScoutController`), `FormRequest` doğrulaması ve `LimitJsonBody` JSON gövde denetimi.

## Uç noktalar (`/api/v1`)

- `POST /api/v1/auth/login`: e-posta ve parola doğrular, Sanctum kişisel erişim anahtarı (`Bearer`) ve kullanıcı bilgisini döndürür (`401 invalid_credentials`, `422 validation_failed`).
- `GET /api/v1/auth/me` (`auth:sanctum`): geçerli oturumun kullanıcı bilgisini döndürür.
- `POST /api/v1/auth/logout` (`auth:sanctum`): aktif erişim anahtarını iptal eder.
- `GET /api/v1/scout/latest` (`auth:sanctum`): kullanıcının en son çalıştırdığı otonom pazar keşif raporunu ve aktif AI motor bilgisini (`ollama` / `openai` / `gemini` / `heuristic`) döndürür.
- `POST /api/v1/scout/runs` (`auth:sanctum`): `GameScout-AI-AI-Service` pazar keşif motorunu çalıştırır (yerel Ollama LLM veya API anahtarı yapılandırılmışsa gerçek LLM sentezi, aksi halde deterministik kantitatif sentez), 3 aksiyon alınabilir oyun konsepti + MVP yol haritası üretir ve kullanıcıya özel kaydeder.
- `POST /api/v1/imports` (`auth:sanctum`): sentetik JSON demo verisini doğrular, aynı kullanıcı/platform/uygulama kimliğini tekilleştirir; çelişkide transaction geri alınır ve `409 import_conflict` döner.
- `GET /api/v1/games?platform=android|ios` (`auth:sanctum`): yalnızca oturum sahibinin oyunlarını döndürür.

## AI Motoru Ayarları (`.env`)

- **Yerel Açık Kaynak LLM (Ollama)**: `AI_PROVIDER=auto` (veya `ollama`), `OLLAMA_BASE_URL=http://127.0.0.1:11434`, `OLLAMA_MODEL=qwen2.5:3b` (veya `qwen2.5:7b` / `llama3.1:8b`).
- **OpenAI / Gemini / Harici API**: `AI_PROVIDER=openai` veya `gemini`, `AI_API_KEY=...`, `AI_MODEL=...`.

## Çalıştırma ve doğrulama durumu

Bu ortamda yerel izole araç zinciri (`.orchestra/tools/bin` altında PHP 8.3.17 ve Composer) ile `composer install`, `php artisan migrate --force --seed` ve `composer test` (`phpunit`) çalıştırılmış ve doğrulanmıştır (`13 tests — OK`). PostgreSQL sunucusu (`psql`/`postgres`) bu ortamda kurulu olmadığından yerel veritabanı ve otomatik testler SQLite sürücüsü (`DB_CONNECTION=sqlite`) ile doğrulanmıştır.
