# Geliştirme orkestrasyonu

Ekip sözleşmesi: [RULES.md](../orchestration/RULES.md). Planlayıcı, uygulayıcı ve
incelemeci her çağrıda güncel sözleşmeyi alır. Scheduler dosya/dizin kapsamı
çakışan görevleri eşzamanlı başlatmaz. SOLID ise Codex incelemesiyle değerlendirilir;
statik bir kural metni veya geçen testler tek başına bunu garanti etmez.

Codex başkan olarak görev planını, test/kabul koşullarını ve bağımsız incelemeyi
yönetir. Uygulama görevleri Antigravity çalışanlarına verilir. Bu araç GameScout ürününün araştırma
graph'ından ayrıdır; örnek görevler GameScout geliştirmesini başlatmaz.

## Kalıcı hafıza

- `Project.md`: ürün hedefi; `Agents.md`: geliştirme kuralları.
- `.orchestra/tasks.sqlite3`: görevler, durumlar, sonuçlar, test ve inceleme kayıtları.
- `.orchestra/workspaces/`: görevlerin ayrı çalışma kopyaları.
- `.orchestra/integrations/`: birleştirilmiş sonucun ayrı çalışma kopyaları.

Her çalışana proje belgeleri ve ilgili görev bağlamı verilir. Hafıza, kayıtlardan
bağlamın yeniden oluşturulmasıdır; sınırsız sohbet geçmişi değildir. Modelin gizli
akıl yürütmesi tutulmaz. `.orchestra` gizli ve Git dışında yereldir; silinirse
kayıtlar kaybolur. Otomatik yedekleme henüz yoktur. Obsidian gerekmez.

```bash
python3 scripts/orchestra.py status
python3 scripts/orchestra.py show parallel-demo-ui
```

## Kurulum ve iki ajanlı deneme

Repo kökünde Python standart kütüphanesi yeterlidir. CLI hesap girişleri gerekir.
Model çağrıları hesap kotası tüketir.

```bash
python3 scripts/orchestra_doctor.py --smoke
python3 scripts/orchestra.py init
python3 scripts/orchestra.py add orchestration/tasks/parallel-ui.json
python3 scripts/orchestra.py add orchestration/tasks/parallel-api.json
python3 scripts/orchestra.py run --workers 2 --max-fixes 1 --integrate parallel-demo --notify
```

Denemede iki ayrı Antigravity oturumu `demo/ui.txt` ve `demo/api.txt` üretir. Test ve bağımsız
Codex incelemeleri geçerse sonuç ayrı entegrasyon kopyasında birleştirilir. Ana
proje klasörüne otomatik kopyalama, commit, push veya deploy yapılmaz.
Aynı görev ID'si tekrar eklenmez; durumunu `status` ile kontrol edin.
`run --integrate` yeni çalıştırılan görevleri seçer; yeni görev yoksa tüm incelenmiş
kayıtları seçebilir. Eski kayıtları dışarıda tutmak için açık görev ID'leriyle
`integrate` komutunu kullanın.

## Paralel çalışma ve düzeltme

`--workers` aynı çalıştırmada 1–3 çalışan sınırı seçer. Bunlar şu an ayrı
Antigravity CLI oturumlarıdır. Antigravity içindeki yerel alt ajanların gerçekten
çağrıldığı doğrulanmış değildir; bu özellik varsa açık dosya sahipliği ve sınırlı
yetkiyle ayrıca kullanılabilir. Bağımsız görevler ayrı
kopyalarda çalışır; dosya kapsamları çakışan görevler birlikte başlatılmaz.
`--max-fixes` 0–2 düzeltme hakkı verir. Kontrol veya inceleme başarısızlığı,
görev sahibine geri bildirilir; sınır dolunca görev engelli olarak saklanır.
Sağlayıcı/izin veya dosya kapsamı hatası başarı sayılmaz.

Görev JSON'unda `provider`, `allowed_paths`, `depends_on` ve `checks` tanımlanır.
Kontroller argv listeleridir. Bunlar yerel komut çalıştırma yetkisidir; modelin
önerdiği komutlar koordinatör tarafından incelenmeden kuyruğa alınmaz. `provider` bu düzende yalnızca `antigravity` olabilir; Codex
ürün kodu uygulama görevi almaz. İsteğe bağlı `subagents` alanı `frontend` ve
`backend` rollerini isteyebilir; bu istek yerel alt ajan çalıştığının bağımsız
kanıtı sayılmaz. Rol şablonları `orchestration/agents/` altından görev kopyasının
`.agents/agents/` dizinine aktarılır; örnek konum
`.orchestra/workspaces/GOREV-ID/.agents/agents/` şeklindedir. Şablon metadata
yapısı resmi belgeye göre hazırlanmıştır; gerçek alt ajan çağrısı canlı olarak
henüz doğrulanmamıştır.

## Birleştirme ve son kontrol

Önceden incelenmiş görevler ayrıca şöyle birleştirilebilir:

```bash
python3 scripts/orchestra.py integrate demo-birlesim parallel-demo-ui parallel-demo-api --notify
```

Birleştirme ayrı kopyada yapılır. İncelenen içerik sonradan değişmişse, kaynak
sürümleri uyumsuzsa veya dosya değişiklikleri çakışıyorsa işlem durur. Birleşmiş
sonuçta testler ve Codex'in son incelemesi tekrar yürütülür. Çakışmayı sessizce
son yazan kazanır yöntemiyle çözmez. Başarısız sonuç ana projeyi değiştirmez.

Önceki sürümde tamamlanan `orchestra-demo` kaydı yeni içerik doğrulama bilgilerini
taşımayabilir; bu eski kaydı yeni entegrasyon denemesine katmayın. Yeni örnek
görevleri kullanın.

## Planlama

```bash
python3 scripts/orchestra.py plan "Yalnızca GameScout Aşama 0 görevlerini öner"
```

Plan komutu Codex'i salt okunur çalıştırır ve öneriyi dosyaya kaydeder; görevleri
kendiliğinden kuyruğa almaz. Koordinatör önerilen kapsam, bağımlılık ve test
komutlarını inceleyip görev dosyalarını ekler. Her görev için başarı mesajı yerine
test sonucu ve bağımsız inceleme gerekir.

## Bildirim ve kesinti

`--notify` tamamlanınca terminal zili ve macOS'ta yerel masaüstü bildirimi dener.
İşletim sistemi izinleri nedeniyle masaüstü bildirimi görünmeyebilir. Bildirim
telefon mesajı veya bu sohbete otomatik dönüş değildir. Sürekli arka plan servisi
henüz yoktur; bilgisayar açık ve çalışan terminal oturumu devam ediyor olmalıdır.

Süreç kesilmişse önce eski çalışanın durduğundan emin olun. Ardından:

```bash
python3 scripts/orchestra.py recover GOREV-ID
```

Kayıt engelli yapılır; görev kendiliğinden yeniden çalıştırılmaz. Çalışma kopyası
ve hafıza korunur. Süre aşımında alt süreçler de durdurulmaya çalışılır.
Paralel çalışmada Ctrl+C, çalışan işlerin sonlanmasını bekleyebilir; anlık iptal
garantisi yoktur. Yeni bir çalıştırmadan önce eski sürecin kapandığını doğrulayın.

## İzolasyon sınırı

Çalışma kopyaları Git commit'inden başlar; ana klasörün commit edilmemiş
değişiklikleri otomatik taşınmaz. Ayrı clone, işletim sistemi güvenlik sandbox'ı
değildir. Sağlayıcının araç izinleri ayrıca geçerlidir. Dosya kapsamı diff ve
inceleme ile kontrol edilir; testlerin ürettiği ignored çıktılar da buna dahildir.
Gerekli çıktı dizinlerini görev kapsamında belirtin. SOLID kod inceleme ölçütüdür,
dosya izolasyon mekanizması değildir.

## Doğrulama

```bash
python3 -m unittest discover -s tests -v
```

İlk canlı tek görev denemesi kullanıcı terminalinde Antigravity → test → Codex
incelemesi ile geçti. Yeni paralel ve entegrasyon davranışlarının otomatik testleri
sahte sağlayıcılar ve geçici Git depolarıyla çalışır; gerçek sağlayıcıların model
kalitesini veya masaüstü bildirim görünürlüğünü kanıtlamaz. Yerel canlı deneme
ayrı olarak yukarıdaki komutlarla yürütülür.
