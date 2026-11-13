# GameScout uygulama modeli

Ürün çalışırken ihtiyaçları ve oyun konseptlerini uygulamanın kendi LLM'i üretir.
Geliştirme ajanları yalnızca kodu yazar. Akış:

1. Kontrollü adaptörler özgün internet metnini, kaynak URL'sini, kimliğini ve zamanı toplar.
2. Model oyun arayışları, öneri talepleri, tartışmalar ve yorumlardan kanıtlı ihtiyaçları çıkarır.
3. Aynı model ihtiyaçlardan yeni mobil oyun konsepti hipotezleri üretir.
4. Kod şemayı, ihtiyaç/kanıt kimliklerini, özgün alıntıyı ve veri kökenini kontrol eder.

Hazır konsept, uydurma Türkçe alıntı ve sessiz model değiştirme yoktur. Geçerli
kanıt kimliği, iddianın anlamsal doğruluğunu tek başına kanıtlamaz; rapor inceleme
ister. Güncel veri modele girdi olarak verilir; model ağırlıkları eğitilmiş sayılmaz.

## Mevcut kaynak kapsamı

Kayıtlı App Store RSS adayları ile mobil Reddit topluluklarının JSON/RSS adayları
vardır. Topluluk istekleri ve tartışmaları yorum dışı veri sağlar. Bunlar tüm
internet veya tüm mobil pazar değildir. Canlı erişim ve yeniden kullanım hakları
bu sürümün testlerinde doğrulanmamıştır. Google Play adaptörü doğrulanana kadar
`source_unavailable` döner; Apple verisi Android/Reddit diye etiketlenmez.
Canlı kaynak başarısızlığı sentetik veriyle doldurulmaz.

## Yerel model ve çalıştırma

Kalite değerlendirme adayı `qwen3:8b`; kurulu olduğu varsayılmaz. Kullanılacak
etiketi açıkça yapılandırın. Ollama dışarıya açılmaz; servis otomatik başlatılmaz
ve ağırlık indirilmez. `auto` yalnız yerel Ollama'yı seçer. Harici sağlayıcılar
API anahtarı/model ve backend'de ayrıca ücretli sağlayıcı izni gerektirir.

```bash
OLLAMA_MODEL=qwen3:8b PYTHONPATH=GameScout-AI-AI-Service python3 -m gamescout_ai scout --provider ollama
python3 -m unittest discover -s GameScout-AI-AI-Service/tests -v
```

Model yoksa `model_unavailable`, kanıt/ihtiyaç yoksa `insufficient_data` görünür.
Geçersiz model çıktısı fikir üretmeden açık hata/partial durumuyla raporlanır.
`--no-network` yalnız sentetik test kanıtı kullanır; gerçek model araştırması yapmaz.
Eski `heuristic` seçeneği uyumluluk için vardır ve artık oyun fikri üretmez.

```bash
PYTHONPATH=GameScout-AI-AI-Service python3 -m gamescout_ai scout --provider heuristic --no-network
PYTHONPATH=GameScout-AI-AI-Service python3 -m gamescout_ai discover GameScout-AI-AI-Service/fixtures/discovery-demo.json --platform android
```

## Değerlendirme ve eğitim

Model planı: `docs/ai-model-plan.md`. On sentetik, insan incelemesi gerektiren
vaka `evaluation/player-needs-v1.json` içindedir. Eğitim yapılmamıştır.
Aşağıdaki komut varsayılan olarak modeli çağırmaz; `--live` yalnız yerel modele
sentetik vakaları gönderir, internet kaynağı toplamaz. Metrik diye sahte doğruluk
puanı üretmez; sonuçları incelemek gerekir.

```bash
python3 scripts/evaluate_scout_model.py
python3 scripts/evaluate_scout_model.py --live --model qwen2.5:3b --limit 2
```

Python çekirdeği standart kütüphane ile çalışır. Laravel iş verilerini ve kullanıcı
yetkisini sahiplenir; bu CLI onun import/auth/veritabanı katmanının yerine geçmez.
Kalıcı asenkron iş kuyruğu ve kapsamlı kaynak keşfi ayrı eksiklerdir.
