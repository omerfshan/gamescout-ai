# gamescout-ai

## Ürün kaynak kodu

| Dizin | İçerik | Doğrulama durumu |
|---|---|---|
| `GameScout-AI-Fronted/` | React/TypeScript: oturum açma (`LoginForm`), kullanıcı kapsamlı oyun listesi, filtre ve JSON import ekranı | `npm run typecheck` ve `npm run build` geçti (Node v22.14.0) |
| `GameScout-AI-Backend/` | Laravel: Domain/Application/Infrastructure/HTTP, Sanctum Bearer oturum (`login`/`me`/`logout`), kullanıcı kapsamlı import ve listeleme | `php artisan migrate --force --seed` ve `composer test` geçti (11/11 PHPUnit testi, 51 assertion, SQLite; PostgreSQL daemon henüz kurulu değil) |
| `GameScout-AI-AI-Service/` | Python: Domain/Application/Infrastructure, deterministik Discovery ve CLI | Birim ve kabul testleri geçti (8/8 birim + 5/5 kabul testi) |

Şu an çalıştırılabilen ürün parçası:

```bash
PYTHONPATH=GameScout-AI-AI-Service python3 -m gamescout_ai discover GameScout-AI-AI-Service/fixtures/discovery-demo.json --platform android --max-games 10
python3 -m unittest discover -s GameScout-AI-AI-Service/tests -v
python3 -m unittest discover -s tests -v
```

Giriş (`POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `POST /api/v1/auth/logout`) → demo JSON import (`POST /api/v1/imports`) → kullanıcıya ait oyun listesini gösterme (`GET /api/v1/games`) dikey dilimi hem frontend hem backend katmanlarında SOLID sınırlarıyla tamamlanmıştır. Çalışma zamanında tarayıcıdan uçtan uca çalıştırmak için eksik geliştirme araçlarının (`node`/`npm`, `php`/`composer`, `postgresql`) kurulması gerekir. Servis README'leri kurulum önkoşulları ve sınırları içerir.

Ürün kapsamı: [Project.md](Project.md). Ekip kuralları: [orchestration/RULES.md](orchestration/RULES.md).

Geliştirme orkestrasyonu: Codex başkanlığı, planlama ve inceleme; Antigravity geliştirme çalışanları,
SQLite görev hafızası, ayrı çalışma kopyaları, sınırlı düzeltme döngüsü ve ayrı
alanda entegrasyon. Kullanım ve sınırlar [docs/orchestration.md](docs/orchestration.md)
içindedir. Ana projeye otomatik commit, push veya deploy yapılmaz.

Python standart kütüphanesi dışında bağımlılık yoktur:

```bash
python3 scripts/orchestra_doctor.py
python3 scripts/orchestra.py init
python3 scripts/orchestra.py status
python3 -m unittest discover -s tests -v
```

`python3 scripts/orchestra_doctor.py --smoke` her sağlayıcıya küçük bir model
isteği gönderir ve hesap kotası kullanır.
