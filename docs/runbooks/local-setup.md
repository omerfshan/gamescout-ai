# GameScout AI — Yerel Kurulum ve Çalıştırma Rehberi (Runbook)

Bu çalışma kılavuzu (runbook), **GameScout AI** projesinin yerel macOS ARM64 (`darwin-arm64`) geliştirme ortamında hazırlanmasını, gerekli araçların proje içine izole biçimde kurulmasını ve **Kullanıcı Girişi → Sentetik Demo JSON İçe Aktarımı → Kullanıcıya Ait Oyun Kataloğu** dikey diliminin uçtan uca çalıştırılmasını açıklar.

---

## 1. Gerekli Geliştirme Araçları

Projenin üç servis katmanı için aşağıdaki araçlar kullanılır:

| Araç | Sürüm / Kapsam | Mevcut Ortam Durumu | Kullanım Alanı |
|---|---|---|---|
| `node` & `npm` | Node.js LTS (`v22.14.0`) ve npm (`10.9.2`) | `.orchestra/tools/node/bin` altında kurulu (`node v22.14.0`, `npm 10.9.2`) | `GameScout-AI-Fronted` (React 18, TypeScript, Vite tip denetimi ve derleme) |
| `php` & `composer` | PHP `8.2+` (`8.3.17` taşınabilir CLI) ve Composer `2.11.2` | `.orchestra/tools/bin` altında kurulu (`php 8.3.17`, `composer 2.11.2`) | `GameScout-AI-Backend` (Laravel 12, Sanctum 4, PHPUnit testleri ve API sunucusu) |
| `postgresql` (`psql`) / `sqlite3` | PostgreSQL `15+` veya yerel SQLite `3.x` | `sqlite3` mevcut (`/usr/bin/sqlite3`), `psql` kurulu değil (otomatik SQLite geri dönüşü aktif) | `GameScout-AI-Backend` kullanıcı ve oyun kataloğu veritabanı katmanı ve orkestrasyon durum deposu |
| `python3` | Python `3.11+` | Mevcut (`Python 3.15.2`) | `GameScout-AI-AI-Service` deterministik Discovery CLI ve orkestrasyon betikleri |
| `ollama` | Ollama macOS (`qwen2.5:3b` yerel model) | `--install-ollama` ile `.orchestra/tools/bin/ollama` altına kurulur | Yerel yapay zeka destekli pazar analizi ve yapılandırılmış JSON sentezi (`127.0.0.1:11434`) |

> **Mevcut Ortam Notu:** Bu çalışma ortamında `python3` ve `sqlite3` sistemde, `node` (`v22.14.0`), `npm` (`10.9.2`), `php` (`8.3.17`) ve `composer` (`2.11.2`) ise `.orchestra/tools/` dizininde hazır durumdadır. Yeni bir ortamda bu araçlar eksikse `bash scripts/setup_dev_tools.sh --install-tools` komutu resmi macOS ARM64 taşınabilir sürümleri `sudo` gerektirmeden `.orchestra/tools/` dizinine indirir. Sistem dizinlerine dokunulmaz.

---

## 2. Araç Durumu Kontrolü ve Kurulum Adımları

Tüm komutlar proje kök dizininde (`/Users/omerfaruksahan/Projects/gamescout-ai`) çalıştırılır.

### 2.1. Mevcut Araçları Kontrol Etme (`--check`)

Çevrimdışı olarak hangi araçların sistemde veya `.orchestra/tools/` altında bulunduğunu görmek için:

```bash
bash scripts/setup_dev_tools.sh --check
```

Bu komut hiçbir ağ isteği yapmaz; `node`, `npm`, `php`, `composer`, `psql`, `python3` ve `sqlite3` araçlarının durumunu yazdırıp `0` çıkış kodu ile sonlanır.

### 2.2. Eksik Taşınabilir Araçları İndirme (`--install-tools`)

Sistemde eksik olan `node`/`npm`, `php` ve `composer` araçlarını `.orchestra/tools/` dizinine indirmek ve kurmak için:

```bash
bash scripts/setup_dev_tools.sh --install-tools
```

- **Node.js & npm:** `.orchestra/tools/node/bin` altına Node.js `v22.14.0` (`darwin-arm64`) indirilir.
- **PHP CLI:** Sistemde `/opt/homebrew/bin/php` varsa bağlanır; yoksa `.orchestra/tools/bin/php` altına taşınabilir PHP 8.3 CLI (`macos-aarch64`) indirilir.
- **Composer:** `.orchestra/tools/bin/composer` olarak indirilir ve çalıştırılabilir yapılır.

Mevcut terminal oturumunda bu araçları doğrudan kullanmak için `PATH` değişkenini güncelleyebilirsiniz:

```bash
export PATH="$PWD/.orchestra/tools/bin:$PWD/.orchestra/tools/node/bin:$PATH"
```

### 2.3. Yerel Yapay Zeka (Ollama + `qwen2.5:3b`) Kurulumu (`--install-ollama`)

`sudo` gerektirmeden resmi macOS Ollama taşınabilir ikilisini (`https://ollama.com/download/ollama-darwin.tgz`) `.orchestra/tools/bin/ollama` altına indirmek, `127.0.0.1:11434` üzerinde `ollama serve` başlatmak ve hızlı/hafif `qwen2.5:3b` modelini `.orchestra/tools/ollama/models` dizinine çekmek için:

```bash
bash scripts/setup_dev_tools.sh --install-ollama
```

### 2.4. Uygulamaları Hazırlama ve Doğrulama (`--setup-apps`)

Araçlar kurulduktan sonra hem Frontend hem Backend bağımlılıklarını yüklemek, yapılandırmak ve test etmek için:

```bash
bash scripts/setup_dev_tools.sh --setup-apps
```

Bu adım sırasıyla:
1. **`GameScout-AI-Fronted`** dizininde:
   - `npm install`
   - `npm run typecheck` (`tsc --noEmit`)
   - `npm run build` (`vite build`)
2. **`GameScout-AI-Backend`** dizininde:
   - `composer install --no-interaction`
   - `composer dump-autoload --no-interaction` (PSR-4 sınıf haritalarını günceller)
   - `.env` dosyası yoksa `.env.example` üzerinden oluşturma ve 32-bayt `APP_KEY` üretme
   - `127.0.0.1:5432` üzerinde PostgreSQL erişilebilir değilse otomatik olarak `DB_CONNECTION=sqlite` ve `database/database.sqlite` yapılandırmasına geçme
   - `php artisan migrate --force --seed`
   - `composer test` (PHPUnit test koşumu)

---

## 3. Servisleri Yerel Loopback Portlarında Başlatma

Güvenlik ve mimari kurallar gereği tüm servisler yalnızca yerel loopback (`127.0.0.1`) arayüzünde çalıştırılır. `scripts/setup_dev_tools.sh` betiği `.orchestra/tools` yollarını otomatik olarak `PATH`'e eklediği için yeni terminallerde manuel `export PATH=...` yapmanıza gerek yoktur.

### 3.0. Tek Komutla Tüm Yığını Başlatma (`--serve`)

Varsa yerel Ollama sunucusunu (`127.0.0.1:11434`), Laravel API sunucusunu (`127.0.0.1:8000`) ve Vite Frontend sunucusunu (`127.0.0.1:5173`) tek bir terminalden başlatmak için:

```bash
bash scripts/setup_dev_tools.sh --serve
```

Bu komut `.orchestra/tools/bin/ollama` (veya sistemdeki `ollama`) kuruluysa ve `11434` portu henüz dinlenmiyorsa `ollama serve` sürecini, ardından Backend'i arka planda ve Frontend'i ön planda başlatır; `Ctrl+C` (`INT`/`TERM`/`EXIT`) ile çıkıldığında arka plandaki süreçleri temiz biçimde sonlandırır.

Servisleri ayrı terminallerde başlatmak isterseniz:
- Yalnızca Backend (`127.0.0.1:8000`): `bash scripts/setup_dev_tools.sh --serve-backend`
- Yalnızca Frontend (`127.0.0.1:5173`): `bash scripts/setup_dev_tools.sh --serve-frontend`

### 3.1. Backend API Servisi (`127.0.0.1:8000`)

1. `GameScout-AI-Backend/.env` içindeki veritabanı ve demo kullanıcı ayarlarını doğrulayın:
   ```ini
   APP_URL=http://127.0.0.1:8000
   DB_HOST=127.0.0.1
   DB_PORT=5432
   DB_DATABASE=gamescout
   DB_USERNAME=gamescout_app
   DB_PASSWORD=REPLACE_LOCALLY
   DEMO_USER_EMAIL=demo@gamescout.local
   DEMO_USER_PASSWORD=demo-scout-2026
   ```
2. Veritabanı tablolarını ve demo kullanıcısını oluşturun (`DatabaseSeeder` ile):
   ```bash
   cd GameScout-AI-Backend
   php artisan migrate --seed
   ```
3. Laravel geliştirme sunucusunu `127.0.0.1:8000` üzerinde başlatın:
   ```bash
   php artisan serve --host=127.0.0.1 --port=8000
   ```

### 3.2. Frontend Dashboard Servisi (`127.0.0.1:5173`)

Yeni bir terminalde `GameScout-AI-Fronted` dizinine geçerek Vite sunucusunu `127.0.0.1:5173` üzerinde başlatın:

```bash
cd GameScout-AI-Fronted
npm run dev -- --host 127.0.0.1 --port 5173
```

- Vite geliştirme sunucusu, tarayıcıdan yapılan `/api/v1/*` isteklerini otomatik olarak `http://127.0.0.1:8000` adresindeki Laravel API'sine yönlendirir (`vite.config.ts`).
- Tarayıcıya hiçbir zaman doğrudan veritabanı, Python servisi veya Ollama adresi açılmaz.

---

## 4. Uçtan Uca Kullanıcı Akışı (Giriş → JSON İçe Aktarım → Oyun Kataloğu)

Tarayıcıda `http://127.0.0.1:5173` adresini açtığınızda aşağıdaki uçtan uca akış çalışır:

### Adım 1: Demo Kullanıcı Girişi (`POST /api/v1/auth/login` & `GET /api/v1/auth/me`)
- Oturum açma ekranında (`LoginForm`), `.env` içinde tanımlı demo kullanıcı bilgileri (`demo@gamescout.local` ve belirlediğiniz parola) girilir.
- `POST /api/v1/auth/login` isteği Laravel Sanctum üzerinden kişisel erişim anahtarı (`Bearer` token) üretir.
- Frontend yalnızca opak oturum anahtarını `sessionStorage` (`gamescout.auth.token`) içinde tutar ve `GET /api/v1/auth/me` ile aktif kullanıcı kimliğini doğrular.

### Adım 2: Sentetik Demo JSON İçe Aktarımı (`POST /api/v1/imports`)
- Giriş yapıldıktan sonra kullanıcıya özel oyun kataloğu ekranı (`GamesPage` ve `ImportForm`) görüntülenir.
- `ImportForm` bileşeni metin yapıştırma alanı veya hazır şablon düğmesi yerine bir **dosya seçici** (`<input id="demo-file" type="file" accept=".json,application/json" />`, en fazla **1 MiB**) kullanır.
- Kullanıcı diskten geçerli bir `.json` dosyası (örneğin `GameScout-AI-AI-Service/fixtures/discovery-demo.json`) seçer ve **"Veriyi içe aktar"** düğmesine tıklar.
- İstemci, seçilen dosyanın boyutunu (≤ 1 MiB) ve geçerli JSON olup olmadığını kontrol ettikten sonra ham JSON içeriğini `POST /api/v1/imports` uç noktasına gönderir.
- Sunucu JSON gövdesini doğrular ve her oyunu aktif oturum sahibinin kullanıcı kimliği (`user_id`) ile ilişkilendirerek veritabanına kaydeder.
- Aynı yükleme içinde aynı `(platform, app_id)` çifti çelişkili verilerle tekrar ederse işlem (transaction) geri alınır ve `409 import_conflict` döner.

### Adım 3: Kullanıcıya Özel Oyun Kataloğu ve Filtreleme (`GET /api/v1/games`)
- İçe aktarım tamamlandığında veya sayfa yüklendiğinde `GET /api/v1/games` (veya platform filtresiyle `GET /api/v1/games?platform=android|ios`) çağrılır.
- Yalnızca oturum açmış kullanıcıya ait oyunlar döner; başka bir kullanıcının oyunları listelenmez.
- Her kartta (`GameCard`) oyunun sentetik demo verisi olduğunu belirten etiket (`meta.demo_label: "Sentetik demo"`) gösterilir.
- Kullanıcı **Çıkış Yap** (`POST /api/v1/auth/logout`) düğmesine bastığında Sanctum erişim anahtarı sunucuda iptal edilir ve `sessionStorage` temizlenir.
