# GameScout uygulama modeli: seçim ve değerlendirme

Kontrol tarihi: 14 Kasım 2026. Bu belge model ağırlığı indirme, model çalıştırma
veya eğitim yapıldığı iddiası değildir.

## Modelin görevi

Uygulamanın kendi modeli iki aşamada çalışır:

1. Kaynak kimliği ve özgün metni korunmuş internet kayıtlarından oyuncunun
   istediği deneyimi, kısıtlarını, beğenilerini, şikâyetlerini ve karşı örnekleri
   çıkarır. Girdi yalnızca yorum olmak zorunda değildir: oyun arayışı, öneri
   talebi ve topluluk tartışması da bir sinyaldir.
2. Doğrulanmış ihtiyaçları kullanarak yeni mobil oyun konsepti hipotezleri üretir.
   Her öneri ihtiyaç ve kanıt kimliklerine, temel döngüye, farkına, risklere ve
   denenebilir prototip planına bağlanır. Tek bir görüş pazarın tamamına genellenmez.

Geliştirme ajanları bu akışın kodunu yazar. Ürün çalışırken oyuncu ihtiyacını ve
konsepti onlar üretmez; model üretir. Kaynak toplama ve doğrulama uygulama kodunun
işidir. Model keyfi tarayıcı, dosya, shell veya SQL yetkisi edinmez.

## Yerelde doğrulanan durum

Depodaki model deposunda `qwen2.5:3b` manifesti bulundu:

- Konum: `.orchestra/tools/ollama/models/manifests/registry.ollama.ai/library/qwen2.5/3b`
- Manifest SHA-256: `cd232a7a8d590449a99eb8fe29b614ef9bf3624d2d17faa496e1135ba4188be0`
- Yerel yapılandırma: GGUF, 3.1B, `Q4_K_M`; katman toplamı yaklaşık 1.93 GB.
- Bu kontrol yalnızca dosya metadata'sını okudu; sunucunun çalıştığını veya modelin
  başarıyla yüklenebildiğini kanıtlamaz.

RAM sorgusu çalışma ortamında izin hatası verdi. Bu nedenle bu bilgisayarda
belirli modelin sığacağına, hızlı çalışacağına veya uygun gecikme sağlayacağına
dair doğrulanmış sonuç yoktur.

## Seçim

İlk kalite adayı **yerel Ollama üzerinde `qwen3:8b`** olsun. Ollama'nın resmi
kaydında bu tag `Q4_K_M` ve yaklaşık 5.2 GB indirme boyutuyla listeleniyor.
Bu indirme boyutu toplam RAM/VRAM gereksinimi değildir; bağlam ve çalışma
alanları ayrıca bellek tüketir. Model henüz yerelde bulunmuş veya denenmiş değildir.

Qwen'in kendi belgeleri Türkçeyi desteklenen diller arasında sayıyor. Bu,
GameScout'un Türkçe ihtiyaç çıkarımı ve kanıt doğruluğunda başarılı olacağını
tek başına kanıtlamaz; aşağıdaki alan değerlendirmesi zorunludur.

`qwen2.5:3b` düşük kaynaklı deneme adayı olarak kalabilir. Fakat daha küçük olduğu
için otomatik kalite onayı verilmez. İki model aynı değerlendirme kümesinde
karşılaştırılmadan biri diğerinden GameScout görevinde daha iyi ilan edilmez.
`qwen3:8b` önerisi değerlendirme adayıdır, ölçülmüş üstünlük sonucu değildir.

Uygulama bir modelden diğerine sessizce düşmez. Yapılandırılan model yoksa
`model_unavailable` gösterilir; hazır fikir şablonlarıyla başarılı rapor üretilmez.
OpenAI/Gemini yalnızca açık sunucu yapılandırması ve maliyet izniyle alternatif
olabilir. Kullanıcının istemciden sağlayıcı seçmesi ücretli çağrı açmaya yetmez.

## Çıktı sözleşmesi

Ollama'nın yerel API'si `format` alanına JSON Schema kabul ediyor. İhtiyaç ve
konsept aşamaları ayrı, sınırlı JSON yanıtları üretmeli. Şema doğrulaması yanında
şunlar kodla kontrol edilir:

- Kanıt kimlikleri gerçekten girdi havuzunda var mı?
- Modelin verdiği alıntı özgün metinle eşleşiyor mu?
- Konseptin dayandığı ihtiyaçlar gerçekten çıkarılan ihtiyaçlar mı?
- Canlı ve sentetik veri açıkça ayrılmış mı?
- Model iddiaya sayı, talep derecesi veya pazar genellemesi uydurmuş mu?

Bir kimliğin geçerli olması anlamsal destek demek değildir. Son değerlendirmede
örneklem bazlı insan incelemesi de gerekir. Gizli düşünce/chain-of-thought
istenmez veya saklanmaz; yalnızca kısa gerekçe, final JSON ve kaynak desteği tutulur.

## Eğitimden önce yapılacak değerlendirme

İlk sürümde temel modele ince ayar yapılmaz. Güncel internet kayıtlarını modele
kanıt olarak getirmek eğitim değildir. Başlangıç için sınırlı kanıt seçimi ve
getirme yeterlidir; vektör veritabanı veya embedding zorunlu değildir.

En azından şu etiketli vakalar değerlendirilir:

| Vaka | Beklenen davranış |
|---|---|
| “No ads, excellent controls” | Reklam/kontrol şikâyeti icat edilmez |
| “Offline strategy game wanted” | İstek ve kısıtlar metne bağlı çıkarılır |
| Tek olumlu görüş | “Çok yüksek pazar talebi” ilan edilmez |
| Aynı gönderinin kopyaları | Bağımsız çoklu talep gibi sayılmaz |
| Birbiriyle çelişen istekler | Karşı kanıt ve hedef kitle farkı gösterilir |
| Genel PC oyun sohbeti | Mobil kapsamına kanıtsız taşınmaz |
| Kaynağı belirsiz alıntı | Canlı kanıt olarak kabul edilmez |
| Prompt injection içeren gönderi | Talimat olarak uygulanmaz |
| Yetersiz/verisiz kaynak havuzu | Öneri sayısı zorlanmaz, çekimserlik gösterilir |
| Türkçe/İngilizce aynı ihtiyaç | Anlam korunur; özgün metin ayrıca saklanır |

Sürüm başına kaynak sadakati, yanlış ihtiyaç, desteksiz iddia, çekimserlik,
JSON uyumu ve yerel gecikme/bellek ölçülür. Donanım, model digest'i, prompt ve
graph sürümü kayda girer. Küçük sentetik testler gerçek pazar kalitesinin kanıtı
sayılmaz; izinli gerçek örneklerle ayrı değerlendirme gerekir.

Ancak etiketli ve kullanım hakkı bilinen veri yeterliyse, hatalar prompt/getirme/
doğrulama düzeltmeleriyle çözülemiyorsa LoRA gibi ince ayar değerlendirilebilir.
Eğitim/test ayrımı, kaynak sızıntısı ve kopya kayıtlar kontrol edilir; eğitimden
önce/sonra aynı tutulan test kümesiyle ölçüm yapılır. Eğitim örnekleri hazırlamak
veya prompt değiştirmek “model eğitildi” diye raporlanmaz.

## Resmi kaynaklar

- [Ollama — qwen3:8b](https://ollama.com/library/qwen3:8b)
- [Ollama — qwen3:8b-q4_K_M](https://ollama.com/library/qwen3:8b-q4_K_M)
- [Ollama — Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs)
- [Qwen — Qwen3-8B model kartı](https://huggingface.co/Qwen/Qwen3-8B)
- [Qwen — Qwen3 ve desteklenen diller](https://qwenlm.github.io/blog/qwen3/)
