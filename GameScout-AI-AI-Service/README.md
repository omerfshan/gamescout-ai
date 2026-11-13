# GameScout AI — Discovery & Otonom Pazar Fırsatı Araştırmacısı (Scout)

Python standart kütüphanesi üzerine SOLID ve katmanlı mimari (`domain/`, `application/`, `infrastructure/`) ile inşa edilmiş GameScout AI servisi iki temel yetenek sunar:

1. **`scout` (Otonom AI Pazar Fırsatı Araştırmacısı)**:
   - Apple App Store, Google Play ve Reddit (`r/AndroidGaming`, `r/iosgaming`, `r/gamedev`) üzerindeki oyuncu yorumlarını, puanlarını ve oyun isteklerini tarar.
   - Oyuncuların hangi türleri arzuladığını (`top_genre_insights`) ve mevcut oyunlarda nelerden şikayet ettiğini analiz ederek somut **"Şu Oyun Yapılabilir!"** konsept önerileri (`actionable_game_proposals`) üretir.
   - **Esnek AI / LLM Mimarisi**:
     - Yerel **Ollama** (`OLLAMA_BASE_URL=http://127.0.0.1:11434`, `OLLAMA_MODEL`)
     - Harici **OpenAI / Gemini API** (`AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL`)
     - Yerel model veya API anahtarı olmadığında kesintisiz çalışan **GameScout Hibrit AI Analiz Motoru** (`heuristic`).

2. **`discover` (Deterministik Sentetik Discovery Çekirdeği)**:
   - Yerel JSON veri kaynağını (`schema_version=1.0.0`, `data_origin=synthetic_demo`) katı şema doğrulamasıyla tekilleştirir ve filtreler.

## Kullanım (Repo Kökünden)

```bash
# Otonom AI Pazar ve Oyun Fırsatı Taraması (Otomatik Ollama / API / Hibrit Motor)
PYTHONPATH=GameScout-AI-AI-Service python3 -m gamescout_ai scout --provider auto

# Çevrimdışı / Hızlı Hibrit AI Analiz Motoru ile Tarama
PYTHONPATH=GameScout-AI-AI-Service python3 -m gamescout_ai scout --provider heuristic --no-network

# Sentetik Discovery Filtreleme
PYTHONPATH=GameScout-AI-AI-Service python3 -m gamescout_ai discover GameScout-AI-AI-Service/fixtures/discovery-demo.json --platform android --max-games 10

# Birim Testleri
python3 -m unittest discover -s GameScout-AI-AI-Service/tests -v
```
