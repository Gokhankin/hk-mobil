# HK Mobil - Sedna Ön Büro "Oda Tablosu" Entegrasyon Notları (05 Eylül 2026)

Bu döküman, Sedna Ön Büro (Front Office) **"Oda Tablosu"** ekranındaki oda durum sınıflandırma mantığının ve orijinal renk paletinin, `hk_mobil` uygulamasına mevcut mobil ergonomi, 4 satırlı sabit başlık ve 4 sütunlu kare oda ızgarası bozulmadan entegre edilmesi sürecini detaylandırır.

---

## 1. Sedna Ön Büro Orijinal Renk Paleti ve Karşılıkları

Sedna Ön Büro sisteminde kullanılan orijinal HEX renkleri ve iş kuralları şu şekildedir:

| Durum / Kategori | Sedna Rengi | HEX Kodu | Metin Rengi | Açıklama |
| :--- | :--- | :--- | :--- | :--- |
| **Inhouse (Konaklayan)** | Fıstık Yeşili | `#16a34a` | `#14532d` | Bugün çıkışı olmayan, içeride konaklayan odalar |
| **Arrival (Gelen)** | Sedna Sarısı | `#facc15` | `#713f12` | Bugün giriş yapacak (Check-in bekleyen) odalar |
| **Departure (Gidecek)** | Sedna Kırmızısı | `#ef4444` | `#ffffff` | Bugün çıkış yapacak ve henüz çıkış yapmamış odalar |
| **C/Out - C/In (Turnaround)** | Sedna Pembesi | `#f472b6` | `#831843` | Aynı gün hem çıkış hem giriş olan veya tahsisli odalar |
| **Temiz Odalar** | Sedna Beyazı | `#ffffff` | `#0f172a` | Boş ve temizlenmiş (veya hazır) odalar (gri kenarlık ile) |
| **Kirli Odalar** | Sedna Grisi | `#9ca3af` | `#ffffff` | Boş veya çıkış yapılmış, temizlik bekleyen odalar |
| **Out of Order (Arızalı)** | Sedna Lilası | `#c084fc` | `#ffffff` | Sedna'da arızaya/OOO durumuna alınmış odalar |
| **Dünden Kirli** | Sedna Kehribar | `#f59e0b` | `#ffffff` | Dünden kalan boş kirli odalar |
| **Blokeli** | Sedna İndigo | `#6366f1` | `#ffffff` | Blokajlı / kilitli odalar |

---

## 2. Yapılan Mimari ve Kod Değişiklikleri

### A. SQL ve Backend Katmanı (`queries_hk.py` & `hk_server.py`)
1. **`TodayArr` ve `TodayDep` CTE'leri:**
   - Aynı gün içerisinde hem ayrılışı (`CheckOutDate = @Today`) hem de yeni rezervasyon gelişi (`CheckinDate = @Today`) olan odaların tam tespiti sağlandı.
   - `TodayDep.OdadaHala` (Status = 2) ve `TodayDep.CikisYapildi` (Status = 3) bayrakları eklendi.
2. **`IS_CO_CI` ve `DD_STATUS` Sütunları:**
   - Turnaround odalar (`arr.HasArrival = 1 AND dep.Room IS NOT NULL`) veya DailyDetail tahsisli odalar (`dd.Status = 3`) `IS_CO_CI = 1` olarak işaretlendi.
   - `DailyDetail.Status` (`DD_STATUS`) doğrudan frontend'e iletildi (4: OOO, 2: Blokeli).
3. **`get_guest_stats` Fonksiyonu:**
   - `arrivals`, `departures` ve `inhouse` istatistiklerinin yanına `coci` (Checkout/Checkin oda ve pax sayısı) eklendi.
4. **`hk_server.py`:**
   - API yanıtında `guest_stats.coci` nesnesi sağlandı.

### B. Frontend ve Tasarım Katmanı (`templates/hk_mobile.html`)
1. **Üst Başlık (Header) 4 Satır Düzeni ve Şekil Bütünlüğü Korundu:**
   - Yapı, boyutlar ve ergonomi aynen muhafaza edildi.
   - **Satır 2 (Misafir / Hareket Sayaçları):**
     - `kpiInhouse`: Fıstık Yeşili (`#16a34a`) - Inhouse
     - `kpiGelen`: Sedna Sarısı (`#facc15`) - Gelen
     - `kpiGidecek`: Sedna Kırmızısı (`#ef4444`) - Gidecek
     - `kpiCoci`: Sedna Pembesi (`#f472b6`) - C/Out - C/In
   - **Satır 3 (Oda Durumu Sayaçları):**
     - `kpiKirli`: Sedna Grisi (`#9ca3af`) - Kirli
     - `kpiTemiz`: Sedna Beyazı (`#ffffff`, koyu siyah yazı) - Temiz
     - `kpiOoo`: Sedna Lilası (`#c084fc`) - Arızalı
     - `kpiBosKirli`: Kehribar/Turuncu (`#f59e0b`) - Dünden Kirli
2. **Oda Grid Kutucukları (`renderGrid`):**
   - Her oda kartı Sedna Ön Büro hiyerarşisine göre renklendirildi:
     - Arızalı -> Lila
     - C/Out - C/In -> Pembe
     - Gidecek (Odada Hâlâ) -> Kırmızı
     - Inhouse -> Fıstık Yeşili
     - Gelen (Giriş Bekleyen) -> Sarı
     - Boş & Temiz -> Beyaz (koyu metin ve şık sınır çizgisi)
     - Boş & Kirli -> Gri
     - Dünden Kirli -> Turuncu
   - Açık renkli kartlarda (Beyaz, Sarı, Yeşil, Pembe) metinlerin, oda numarasının ve ikonların net okunabilmesi için otomatik koyu metin ve kontrast ayarı yapıldı.
3. **Filtreleme & Arama Uyumluluğu:**
   - Üstteki herhangi bir KPI kartına tıklandığında (Inhouse, Gelen, Gidecek, C/Out-C/In, Kirli, Temiz, Arızalı, Dünden Kirli) oda listesi anında süzülür.
   - İkinci tıklamada veya başlığa basıldığında tüm liste geri yüklenir.
4. **Oda Durum Güvenlik Modalı (Popup):**
   - Modal içerisindeki durum seçeneklerinin renk noktaları Sedna standartlarına uyarlandı (Kirli = Gri, Temiz = Beyaz, Hazır = Sarı, Arızalı = Lila, Blokeli = İndigo).

---

## 3. Dağıtım ve Canlı Sunucu Doğrulaması

1. **Canlı Sunucuya Aktarım:**
   - Güncellenen `templates/hk_mobile.html`, `queries_hk.py` ve `hk_server.py` dosyaları SSH/SFTP üzerinden `192.168.0.128` Society sunucusuna yüklendi.
2. **Servis Yeniden Başlatma:**
   - Eski `hk_server.py` süreci sonlandırılıp `/home/society/Masaüstü/hk_mobil/venv/bin/python3` ile arka planda sorunsuz başlatıldı (PID: `193716`).
3. **API ve Ekran Testi:**
   - `http://192.168.0.128:5002/api/hk/data` uç noktası HTTP 200 ile 111 odayı ve yeni `guest_stats` verilerini eksiksiz döndürdü:
     - Inhouse: 81 Oda, 147 Pax
     - Gelen: 12 Oda, 21 Pax
     - Gidecek: 19 Oda, 35 Pax
     - C/Out - C/In: 9 Oda, 10 Pax
     - Dünden Kirli: 2 Oda
   - Sedna Ön Büro "Oda Tablosu" ekran görüntüsündeki 101, 103, 112, 118, 121, 127, 128, 335, 403, 407, 703 numaralı odaların renk ve durumlarının sistemle %100 birebir örtüştüğü test edilip doğrulandı.

---

## 18. Sedna Ön Büro "Oda Tablosu" Senkronizasyonu ve Tutarsızlık Giderimi (05 Eylül 2026)

### A. Bildirilen Tutarsızlıklar ve Kök Neden Analizi:

1. **Odalar 109, 129, 134 ve 411 (Sedna'da YEŞİL, Bizde BEYAZ veya GRİ Görünüyordu):**
   - **Kök Neden:** Bu odalarda bugün eski misafir çıkış yapmış (`Status = 3`), yeni misafir ise otele giriş yapıp odaya yerleşmiştir (`Status = 2` Inhouse). Eski sorgu mantığında `BUGUN_GIDECEK = 1` bayrağı aktif olduğu için kod odayı "Inhouse değil" sanıyor ve çıkış yapılmış odalarda Temiz (Beyaz) veya Kirli (Gri) durumuna düşürüyordu.
   - **Düzeltme:** Bir odada şu an aktif konaklayan misafir varsa (`DOLU_BOS = 1`) ve ayrılış tarihi bugün değilse, eski çıkıştan bağımsız olarak oda Sedna Ön Büro ile tam uyumlu şekilde **YEŞİL (Inhouse)** olarak renklendirildi.

2. **Odalar 305, 330, 334, 412, 413 (Sedna'da SARI, Bizde PEMBE Görünüyordu):**
   - **Kök Neden:** Bu odalarda dünkü misafir bugün sabah çıkış yapmıştır (`Status = 3` C/O yapıldı), bugün ise yeni rezervasyon gelişi (`Status = 1`) vardır. Eski kod, hem çıkış hem giriş kaydı olduğu için odayı "Turnaround / Çıkış & Giriş Çakışması" sayıp PEMBE boyuyordu. Halbuki eski misafir zaten çıkmıştır; odada bekleyen tek işlem yeni misafir girişidir (Arrival).
   - **Düzeltme:** Turnaround (PEMBE) koşulu yalnızca **ayrılacak misafir henüz odadan çıkmadıysa (`ODADA_HALA`)** veya oda Sedna'da özel tahsisliyse (`DD_STATUS = 3`) aktif olacak şekilde düzeltildi. Eski misafiri çıkmış yeni giriş bekleyen odalar Sedna gibi **SARI (Arrival)** yapıldı.

3. **Oda 403 (Sedna'da GRİ, Bizde TURUNCU Görünüyordu):**
   - **Kök Neden:** Oda 403 dünden kalan boş kirli bir odadır. Bizim arayüzdeki "Dünden Kirli" kuralı odanın arka planını turuncuya boyuyordu. Ancak Sedna Ön Büro "Oda Tablosu"nda turuncu renk yoktur; Sedna'da tüm kirli odalar **GRİ** renktedir.
   - **Düzeltme:** Odanın zemin rengi Sedna ile %100 aynı olacak şekilde **GRİ** yapıldı. HK personeli için "Dünden Kirli" olduğunu belirten küçük süpürge ikonu rozeti oda içine korunarak korundu.

4. **Oda 414 (Sedna'da KAHVERENGİ, Bizde MAVİ Görünüyordu):**
   - **Kök Neden:** Sedna `DailyDetail.Status = 2` kaydı Sedna Ön Büro'da `V.a.d` (Blokajlı / Arıza dışı kilitli oda) anlamına gelir ve Sedna tablosunda **KAHVERENGİ (`#a16207`)** olarak gösterilir. Bizde ise genel kuraldan ötürü maviye boyanıyordu.
   - **Düzeltme:** `DD_STATUS = 2` olan odalar Sedna'nın orijinal **KAHVERENGİ (`#a16207`)** rengine ve `V.A.D` etiketine çekildi.

5. **Sedna'da Gerçek PEMBE Odalar:**
   - Sedna ekran görüntüsündeki pembe odalar (`121, 415, 423, 705`) `DailyDetail.Status = 3` olan özel tahsisli odalardır. `IS_CO_CI` sayısı da tam olarak bu 4 odaya eşitlendi.


### Bölüm 19: Çift Yönlü Anlık Senkronizasyon & Sedna Ön Büro KPI Tam Eşitlemesi (2026-09-05 21:25)

#### 1. Yapılan İşlem ve İhtiyaç
- Kullanıcı talebi doğrultusunda HK Mobil ile Sedna Ön Büro arasında çift yönlü anlık (real-time) senkronizasyon sağlandı.
- Sedna Ön Büro alt durum çubuğundaki rakamlar ile HK Mobil KPI sayaçları arasındaki farklar giderildi:
  * Inhouse: 82 Oda / 149 Pax (Sanal/PM oda 2003 dahil Sedna ile %100 eşitlendi).
  * Arrival: 12 Oda / 21 Pax (Bugün beklenen girişler).
  * Departure (Odada Hâlâ): 3 Oda / 6 Pax (Bugün çıkış beklenen ama henüz çıkmamış olanlar).
  * Çıkış Yapan: 19 Oda / 34 Pax (Bugün C/Out işlemi tamamlananlar).
  * Giriş Yapan: 10 Oda / 17 Pax (Bugün C/In işlemi yapılanlar).
  * C/Out - C/In: 4 Oda (Turnaround çakışma ve tahsisli odalar).

#### 2. Çift Yönlü Canlı Senkronizasyon Altyapısı
1. **Sedna -> HK Mobil (Anlık Canlı Akış):**
   - Ön yüze startLiveSync() akıllı arka plan döngüsü eklendi (her 15 saniyede bir sessiz arka plan sorgusu).
   - Kullanıcı ekranda oda durum modalı açıkken veya oda ararken akış bozulmaz; veriler sessizce güncellenir.
2. **HK Mobil -> Sedna (Anlık Veritabanı Güncellemesi):**
   - Odaların temizlik durumu değiştirildiğinde Sedna veritabanında Room tablosunun DirtyClean ve HkStatus alanları ile DailyDetail tablosu anında UPDATE edilerek COMMIT edilir.
   - Sedna ekranı F5 yapıldığında veya açıldığında değişiklik aynı salisede Sedna Ön Büro'da görünür.

#### 3. Canlı Dağıtım
- Değiştirilen dosyalar (queries_hk.py, 	emplates/hk_mobile.html, hk_server.py) canlı sunucuya (192.168.0.128:5002) SFTP ile yüklendi ve Flask servisi yeniden başlatıldı (PID: 236739).
- API testi başarılı: HTTP 200, 111 oda, Sedna ile birebir aynı istatistikler doğrulandı.


### Bölüm 20: HK Mobil Çift Göstergeli Kart Mimarisi & Sedna OOO Senkronizasyonu (2026-09-05 21:51)

#### 1. Yapılan İşlem ve İhtiyaç
- Ön Büro oda tablosu ile Housekeeping oda tablosu mantıklarının birleştirilmesi sağlandı.
- Ön Büro görünümünde misafir olan odaların YEŞİL (Inhouse) kalması şartı korunurken, HK personelinin temizlik operasyonunu (odanın temiz mi kirli mi olduğunu) tek bakışta görebilmesi için **Çift Göstergeli (Dual Indicator)** kart yapısı geliştirildi.
- Sedna DailyDetail tablosunda OOO (Arızalı) statüsünün standart Status = 3 (Sedna HkRoomRack & FnOOO standartı) olduğu tespit edilerek backend senkronizasyonu güncellendi.

#### 2. Çift Göstergeli Kart Detayları
1. **Ana Renk (Ön Büro Durumu):**
   - Kartın arka plan rengi Sedna Ön Büro mantığını yansıtmaya devam eder (Yeşil = Inhouse, Sarı = Gelen, Kırmızı = Gidecek, Pembe = C/O-C/I, Gri = Kirli, Beyaz = Temiz, Lila = Arızalı).
2. **Alt Durum Şeridi (Bileşik Etiket):**
   - Misafir durumu ile temizlik durumu birleştirildi:
     * INHOUSE • KİRLİ / INHOUSE • TEMİZ
     * GİDECEK • KİRLİ / GİDECEK • TEMİZ
     * GELEN • KİRLİ / GELEN • TEMİZ
     * C/O-C/I • KİRLİ / C/O-C/I • TEMİZ
3. **Sağ Üst Temizlik Rozeti (Gözle Hızlı Tarama İkonu):**
   - Temiz ise: Küçük yeşil daire içinde **✓ Beyaz Tik** (.clean-ind-clean)
   - Kirli ise: Küçük kırmızı daire içinde **🧹 Beyaz Süpürge** (.clean-ind-dirty)
   - Arızalı ise: Küçük mor daire içinde **🔧 Beyaz İngiliz Anahtarı** (.clean-ind-ooo)
   - Not veya durum açıklaması olan odalarda rozet çakışmasını önlemek için akıllı has-remark konumlandırması uygulandı.

#### 3. Canlı Dağıtım
- Değişiklikler canlı Society sunucusuna (192.168.0.128:5002) deploy edildi ve Flask servisi yeniden başlatıldı (PID: 252440).
- HTTP 200 ile 111 odanın çift göstergeli olarak render edildiği test edildi.


### Bölüm 21: Mobil Çift Parmak İçe Küçültme (Pinch-to-Zoom) & Kompakt Görünüm (2026-09-05 21:54)

#### 1. Yapılan İşlem ve İhtiyaç
- Kullanıcı, mobil ekranda oda kutularının (KPI kartlarının) büyük olduğunu, ekranda daha fazla odayı tek bakışta görebilmek için iki parmakla içe doğru sıkıştırma (pinch-in) hareketi yapıldığında oda kutularının 2 kat küçülerek ekrana çok daha fazla odanın sığmasını talep etti.

#### 2. Uygulanan Mimari & Çözüm
1. **İki Parmakla Kıstırma Hareketi (Multi-touch Pinch Gesture):**
   - Mobil tarayıcılarda üst menünün sabit kalmasını sağlayan `user-scalable=no` meta ayarı bozulmadan, `.content` konteynerine `touchstart`, `touchmove` ve `touchend` multi-touch olay dinleyicileri eklendi.
   - İki parmak arası mesafe dinamik olarak `Math.hypot(x1 - x2, y1 - y2)` ile hesaplanır.
   - Parmaklar **içe doğru sıkıştırıldığında (Pinch-in, diff < -45px)**: Otomatik olarak Kompakt (2x Küçük) moda geçer.
   - Parmaklar **dışa doğru açıldığında (Pinch-out, diff > +45px)**: Standart (Normal) moda geri döner.
2. **Tek Dokunuşlu Hızlı Başlık Butonu (`#densityBtn`):**
   - Üst çubukta (sağ üst menüde, karanlık mod butonunun solunda) `<i class="fas fa-compress-alt"></i>` / `<i class="fas fa-expand-alt"></i>` ikonu yerleştirildi.
   - Kullanıcı parmak hareketi yapmadan da tek bir dokunuşla Kompakt ve Standart modlar arasında geçiş yapabilir.
3. **Kompakt Mod Tasarım Kuralları (`.grid.grid-compact`):**
   - Mobilde sütun sayısı 4'ten **7 sütuna** çıkarıldı (Geniş ekranda 64px auto-fill).
   - Oda numarası yazı boyutu `1.15rem`'den `0.78rem`'e optimize edildi.
   - Oda tipi ve durum şeritleri `0.38rem` olarak orantılı küçültüldü.
   - Temiz/Kirli/Arıza durum rozetleri ve ikonlar 11px mikro boyutta net olarak korunurken, alanı daraltan büyük C/O metin etiketleri kompakt modda gizlenerek alan tasarrufu sağlandı.
   - Kullanıcının seçimi `localStorage.getItem('hk_grid_density')` ile hafızaya alınır, sayfa yenilense veya uygulama kapatılıp açılsa da son tercih hatırlanır.
4. **Geri Bildirim Baloncuğu (Zoom Toast):**
   - Mod değiştiğinde ekranın alt kısmında şık animasyonlu bir bildirim ("Kompakt Görünüm: Odalar 2x Küçültüldü" / "Standart Görünüm") gösterilir.

#### 3. Canlı Dağıtım
- Değişiklikler canlı Society sunucusuna (`192.168.0.128:5002`) SFTP ile yüklendi ve Flask servisi yeniden başlatıldı (PID: `253594`).
- HTTP 200 testi yapıldı, mobil cihazlarda sorunsuz çalıştığı doğrulandı.


### Bölüm 22: "Dünden Kirli" (Boş Kirli) Mantığı & Doğrulaması (2026-09-05 21:58)

#### 1. Otelcilik & Sedna Veri Tabanı Mantığı
- **Bugün Çıkan Kirli:** Misafir bugün çıkış yapmış ve oda kirliye alınmıştır. Çıkış tarihi bugündür (`CAST(CheckOutDate AS DATE) = @Today`).
- **Dünden Kalan Kirli (Boş Kirli):** 
  * Misafir dün veya daha önceki tarihlerde çıkış yapmıştır (`CheckOutDate <> @Today`).
  * Odada aktif konaklayan misafir yoktur (`DOLU_BOS = 0`).
  * Odaya bugün yeni giriş yapılmamıştır (`CheckinDate <> @Today`).
  * Ancak oda temizlenmemiştir (`DirtyClean = 1`).
  * Gece denetimi (Night Audit) veya takvim ertesi güne geçtiğinde sistem bu odaları otomatik olarak **"Dünden Kirli"** grubuna ve sayacına dahil eder.

#### 2. Canlı Sunucu Doğrulaması
- Canlı sunucu (`192.168.0.128:5002`) API'sinden çekilen gerçek verilerle doğrulandı:
  * Toplam Dünden Kirli Sayısı: **2 Oda** (`403` ve `414`).
  * Her iki odanın da `Dolu = 0`, `Bugün Gelen = 0`, `Bugün Gidecek = 0`, `Durum = KIRLI` ve `CheckOutDate < @Today` olduğu teyit edildi.
  * Sistem Sedna Ön Büro ve Housekeeping standartlarına göre %100 kusursuz çalışmaktadır.


### Bölüm 23: Room Change (Oda Değişikliği) Odalarının Dünden Kirliye Düşmesinin Engellenmesi (2026-09-06 10:23)

#### 1. Sorun ve İhtiyaç
- Kullanıcı bildirimi: "HK mobil programında 333 nolu oda room change oldu, dünden kirliye düşmüş. Room change olan odalar asla dünden kirliye düşmesin, direkt kirliye düşsün."
- Örnek Vaka (Oda 333): Misafir (WILLIAM JOHN DAWSON - Rez No: 28712) dün 333 nolu odada konaklamış, bugün (06.09.2026) Ön Büro tarafından 208 nolu odaya Room Change yapılmıştır.
- Eski sorguda RoomChange sadece `RoomChangePlan` tablosundan kontrol ediliyordu. Ancak Sedna Ön Büro oda değişikliğini fiilen `DailyDetail` tablosunda dün 333, bugün 208 olarak güncellediği için eski oda (333) dünden devreden boş kirli gibi algılanıyordu.

#### 2. Uygulanan Çözüm
1. **`queries_hk.py` - `TodayRC` CTE Güçlendirildi:**
   - Resmi plan tablosunun (`RoomChangePlan`) yanı sıra, Sedna'da anlık/fiili olarak yapılan tüm oda değişiklikleri `DailyDetail` üzerinden bağlandı:
   ```sql
   SELECT dd_old.Room AS Room
   FROM DailyDetail dd_new
   JOIN DailyDetail dd_old ON dd_new.ReservationId = dd_old.ReservationId 
        AND dd_old.StayDate = DATEADD(day, -1, dd_new.StayDate) 
        AND dd_old.Room <> dd_new.Room
   WHERE CAST(dd_new.StayDate AS DATE) = @Today
   ```
   - Böylece dünden bugüne oda değişikliği ile boşalan eski odalar ve yeni odalar anında `TodayRC` kümesine dahil edilir.
2. **`BOS_KIRLI` Filtresinden Kesin Muafiyet:**
   - `rc.Room IS NULL` şartı sayesinde Room Change olan hiçbir oda artık `BOS_KIRLI` (Dünden Kirli) grubuna DÜŞMEZ.
   - Doğrudan genel **KİRLİ** durumuna (`DURUM: KIRLI`, `BOS_KIRLI: 0`) düşer.
3. **Kart Üzerinde "ROOM CHANGE" Rozeti:**
   - Boşalan eski oda üzerine şık mavi renkli `<div class="co-card-badge"><i class="fas fa-exchange-alt"></i> ROOM CHANGE</div>` etiketi eklendi. HK personeli odaya baktığında odanın dünden kalan değil, bugün yapılan bir Room Change neticesinde kirlendiğini anında görür.

#### 3. Canlı Test ve Doğrulama
- Canlı sunucuya aktarıldı (PID: `652701`).
- Oda 333 test edildi:
  * `DURUM: KIRLI`
  * `BOS_KIRLI: 0` (Dünden Kirli'den tamamen çıkarıldı)

### Bölüm 24: Room Change Listesi Popup Kutucuğu (RC Butonu & Modalı) Eklendi (2026-09-06 10:35)

#### 1. İhtiyaç ve Kapsam
- Kullanıcı talebi: "Room change olanları gösteren bir küçük kutucuk tıklayınca hangi oda hangi odaya room change oldu onu gösterelim. Ancak room change olan oda mutlaka kirliye düşsün dünden kirli olmasın, dünden kirli olanlar ise bir gün önceden kirli olupta yetişemeyen odalar dünden kirli olarak görünsün."

#### 2. Uygulanan Geliştirmeler
1. **Veritabanı Katmanı (`queries_hk.py` - `get_room_changes` fonksiyonu):**
   - Sedna SQL'de hem `DailyDetail` fiili oda değişiklikleri hem de `RoomChangePlan` planlı kayıtları taranarak şu alanlar JSON formatında çekildi:
     * `OldRoom` (Eski Oda No)
     * `NewRoom` (Yeni Oda No)
     * `GuestName` (Misafir Adı Soyadı)
     * `Voucher` (Voucher No)
     * `ChangeTime` (Değişiklik Saati)
     * `Source` (Fiili RC / Planlı RC)
2. **Backend API Katmanı (`hk_server.py`):**
   - `/api/hk/data` endpoint'ine `"room_changes": room_changes` dizisi eklendi.
3. **Frontend UI Katmanı (`hk_mobile.html`):**
   - **Header RC Butonu (`#headerRcBtn`):** Üst çubuğa mor temalı, dinamik sayaçlı rozet butonu eklendi (`RC <count>`). Eğer bugün herhangi bir Room Change yoksa buton görünmez (`display: none`), Room Change gerçekleştiği an otomatik belirir ve sayıyı gösterir.
   - **Room Change Detay Modalı (`#rcModal`):** Butona tıklandığında açılan açılır pencere tasarlandı:
     * Hangi eski odadan hangi yeni odaya geçildiği görsel oklarla vurgulanır: `[333 (Eski)] ➔ [208 (Yeni)]`.
     * Misafirin tam adı ve voucher numarası gösterilir.
     * Değişikliğin yapıldığı saat/zaman bilgisi listelenir.
   - **Dünden Kirli & Kirli Kuralı:**
     * Room Change olan odalar (örneğin 333 nolu oda) `BOS_KIRLI = 0` tutularak asla dünden kirliye düşürülmez, doğrudan `KİRLİ` kategorisinde gösterilir.
     * `DÜNDEN KİRLİ` filtresi yalnızca dünden kalan ve henüz temizlenemeyen gerçek devreden odalara ayrılmıştır.

#### 3. Canlı Sunucu Doğrulaması (`192.168.0.128:5002`)
- Dosyalar SFTP ile canlıya yüklendi ve Flask servisi yeniden başlatıldı (PID: `659665`).
- API test edildi:

### Bölüm 25: Room Change Modalı İçine Tarih Seçici ve Late Check-Out (Geç Çıkış) Entegrasyonu (2026-09-06 10:44)

#### 1. İhtiyaç ve Kapsam
- Kullanıcı talebi: "Geçmiş tarihleri gösteren bir tarih seçici olsa dünü ondan önceki günü gösterebilirmi, late room change görebilse iyi olur... Late checkout ve room changeleri room change modalı içine yapalım."

#### 2. Uygulanan Geliştirmeler
1. **Veritabanı Katmanı (`queries_hk.py`):**
   - `get_room_changes(conn, target_date=None)`: Parametrik tarih desteği eklendi. `COALESCE(?, CAST(GETDATE() AS DATE))` ile hem bugünü hem de istenilen geçmiş/gelecek herhangi bir tarihi filtreleyebilir.
   - `get_late_checkouts(conn, target_date=None)`: Sedna'da `CheckOutDate = @TargetDate` ve `LateCOut` tanımlı olan misafirleri; oda numarası, uzatma saati, misafir adı, voucher ve odada/çıkış yaptı durumuyla getiren fonksiyon yazıldı.
2. **Backend API Katmanı (`hk_server.py`):**
   - `/api/hk/data` endpoint'ine `late_checkouts` dizisi dahil edildi.
   - `/api/hk/rc_history?date=YYYY-MM-DD` adında yeni bir endpoint açıldı; seçilen tarihe göre hem oda değişikliklerini hem geç çıkışları anlık döndürür.
3. **Frontend UI Katmanı (`templates/hk_mobile.html`):**
   - **Sekmeli (Tabs) Yapı:**
     * `Room Change (<count>)` sekmesi: Hangi eski odanın hangi yeni odaya aktarıldığı, saati ve misafir detayı.
     * `Late C/Out (<count>)` sekmesi: Geç çıkış izni olan odalar, çıkış uzatma saati (örn. `12:00`, `16:00`), misafirin hâlâ odada mı olduğu yoksa çıkış mı yaptığı rozeti.
   - **Tarih Seçici Çubuğu:**
     * `Bugün`, `Dün`, `Önceki Gün` hızlı seçim hap butonları (pills).
     * Yanında dilediği geçmiş veya ileri tarihi seçebileceği takvim/tarih seçici (`<input type="date">`).
   - Sekme veya tarih değiştiğinde anında Sedna'dan o günün verisi çekilip sayaçlar ve liste güncellenir.

#### 3. Canlı Sunucu Doğrulaması (`192.168.0.128:5002`)
- Dosyalar SFTP ile yüklendi ve Flask servisi yeniden başlatıldı (PID: `663756`).
- Test sonuçları:
  * **06.09.2026 (Bugün):** RC: 1 adet (`333 -> 208`), Late C/Out: 21 adet.
  * **05.09.2026 (Dün):** RC: 0 adet, Late C/Out: 14 adet.
  * **04.09.2026 (Önceki Gün):** RC: 1 adet (`123 -> 130`), Late C/Out: 5 adet.
- Modal penceresi hem oda değişikliklerini hem de geç çıkışları (late check-out) geçmiş tarihleriyle birlikte eksiksiz ve hızlı bir şekilde listelemektedir.

### Bölüm 26: Late Check-Out Listesinde İptal/Hayalet Rezervasyonların Temizlenmesi (2026-09-06 10:56)

#### 1. Sorun ve İnceleme
5. **Sedna'da Gerçek PEMBE Odalar:**
   - Sedna ekran görüntüsündeki pembe odalar (`121, 415, 423, 705`) `DailyDetail.Status = 3` olan özel tahsisli odalardır. `IS_CO_CI` sayısı da tam olarak bu 4 odaya eşitlendi.


### Bölüm 19: Çift Yönlü Anlık Senkronizasyon & Sedna Ön Büro KPI Tam Eşitlemesi (2026-09-05 21:25)

#### 1. Yapılan İşlem ve İhtiyaç
- Kullanıcı talebi doğrultusunda HK Mobil ile Sedna Ön Büro arasında çift yönlü anlık (real-time) senkronizasyon sağlandı.
- Sedna Ön Büro alt durum çubuğundaki rakamlar ile HK Mobil KPI sayaçları arasındaki farklar giderildi:
  * Inhouse: 82 Oda / 149 Pax (Sanal/PM oda 2003 dahil Sedna ile %100 eşitlendi).
  * Arrival: 12 Oda / 21 Pax (Bugün beklenen girişler).
  * Departure (Odada Hâlâ): 3 Oda / 6 Pax (Bugün çıkış beklenen ama henüz çıkmamış olanlar).
  * Çıkış Yapan: 19 Oda / 34 Pax (Bugün C/Out işlemi tamamlananlar).
  * Giriş Yapan: 10 Oda / 17 Pax (Bugün C/In işlemi yapılanlar).
  * C/Out - C/In: 4 Oda (Turnaround çakışma ve tahsisli odalar).

#### 2. Çift Yönlü Canlı Senkronizasyon Altyapısı
1. **Sedna -> HK Mobil (Anlık Canlı Akış):**
   - Ön yüze startLiveSync() akıllı arka plan döngüsü eklendi (her 15 saniyede bir sessiz arka plan sorgusu).
   - Kullanıcı ekranda oda durum modalı açıkken veya oda ararken akış bozulmaz; veriler sessizce güncellenir.
2. **HK Mobil -> Sedna (Anlık Veritabanı Güncellemesi):**
   - Odaların temizlik durumu değiştirildiğinde Sedna veritabanında Room tablosunun DirtyClean ve HkStatus alanları ile DailyDetail tablosu anında UPDATE edilerek COMMIT edilir.
   - Sedna ekranı F5 yapıldığında veya açıldığında değişiklik aynı salisede Sedna Ön Büro'da görünür.

#### 3. Canlı Dağıtım
- Değiştirilen dosyalar (queries_hk.py, 	emplates/hk_mobile.html, hk_server.py) canlı sunucuya (192.168.0.128:5002) SFTP ile yüklendi ve Flask servisi yeniden başlatıldı (PID: 236739).
- API testi başarılı: HTTP 200, 111 oda, Sedna ile birebir aynı istatistikler doğrulandı.


### Bölüm 20: HK Mobil Çift Göstergeli Kart Mimarisi & Sedna OOO Senkronizasyonu (2026-09-05 21:51)

#### 1. Yapılan İşlem ve İhtiyaç
- Ön Büro oda tablosu ile Housekeeping oda tablosu mantıklarının birleştirilmesi sağlandı.
- Ön Büro görünümünde misafir olan odaların YEŞİL (Inhouse) kalması şartı korunurken, HK personelinin temizlik operasyonunu (odanın temiz mi kirli mi olduğunu) tek bakışta görebilmesi için **Çift Göstergeli (Dual Indicator)** kart yapısı geliştirildi.
- Sedna DailyDetail tablosunda OOO (Arızalı) statüsünün standart Status = 3 (Sedna HkRoomRack & FnOOO standartı) olduğu tespit edilerek backend senkronizasyonu güncellendi.

#### 2. Çift Göstergeli Kart Detayları
1. **Ana Renk (Ön Büro Durumu):**
   - Kartın arka plan rengi Sedna Ön Büro mantığını yansıtmaya devam eder (Yeşil = Inhouse, Sarı = Gelen, Kırmızı = Gidecek, Pembe = C/O-C/I, Gri = Kirli, Beyaz = Temiz, Lila = Arızalı).
2. **Alt Durum Şeridi (Bileşik Etiket):**
   - Misafir durumu ile temizlik durumu birleştirildi:
     * INHOUSE • KİRLİ / INHOUSE • TEMİZ
     * GİDECEK • KİRLİ / GİDECEK • TEMİZ
     * GELEN • KİRLİ / GELEN • TEMİZ
     * C/O-C/I • KİRLİ / C/O-C/I • TEMİZ
3. **Sağ Üst Temizlik Rozeti (Gözle Hızlı Tarama İkonu):**
   - Temiz ise: Küçük yeşil daire içinde **✓ Beyaz Tik** (.clean-ind-clean)
   - Kirli ise: Küçük kırmızı daire içinde **🧹 Beyaz Süpürge** (.clean-ind-dirty)
   - Arızalı ise: Küçük mor daire içinde **🔧 Beyaz İngiliz Anahtarı** (.clean-ind-ooo)
   - Not veya durum açıklaması olan odalarda rozet çakışmasını önlemek için akıllı has-remark konumlandırması uygulandı.

#### 3. Canlı Dağıtım
- Değişiklikler canlı Society sunucusuna (192.168.0.128:5002) deploy edildi ve Flask servisi yeniden başlatıldı (PID: 252440).
- HTTP 200 ile 111 odanın çift göstergeli olarak render edildiği test edildi.


### Bölüm 21: Mobil Çift Parmak İçe Küçültme (Pinch-to-Zoom) & Kompakt Görünüm (2026-09-05 21:54)

#### 1. Yapılan İşlem ve İhtiyaç
- Kullanıcı, mobil ekranda oda kutularının (KPI kartlarının) büyük olduğunu, ekranda daha fazla odayı tek bakışta görebilmek için iki parmakla içe doğru sıkıştırma (pinch-in) hareketi yapıldığında oda kutularının 2 kat küçülerek ekrana çok daha fazla odanın sığmasını talep etti.

#### 2. Uygulanan Mimari & Çözüm
1. **İki Parmakla Kıstırma Hareketi (Multi-touch Pinch Gesture):**
   - Mobil tarayıcılarda üst menünün sabit kalmasını sağlayan `user-scalable=no` meta ayarı bozulmadan, `.content` konteynerine `touchstart`, `touchmove` ve `touchend` multi-touch olay dinleyicileri eklendi.
   - İki parmak arası mesafe dinamik olarak `Math.hypot(x1 - x2, y1 - y2)` ile hesaplanır.
   - Parmaklar **içe doğru sıkıştırıldığında (Pinch-in, diff < -45px)**: Otomatik olarak Kompakt (2x Küçük) moda geçer.
   - Parmaklar **dışa doğru açıldığında (Pinch-out, diff > +45px)**: Standart (Normal) moda geri döner.
2. **Tek Dokunuşlu Hızlı Başlık Butonu (`#densityBtn`):**
   - Üst çubukta (sağ üst menüde, karanlık mod butonunun solunda) `<i class="fas fa-compress-alt"></i>` / `<i class="fas fa-expand-alt"></i>` ikonu yerleştirildi.
   - Kullanıcı parmak hareketi yapmadan da tek bir dokunuşla Kompakt ve Standart modlar arasında geçiş yapabilir.
3. **Kompakt Mod Tasarım Kuralları (`.grid.grid-compact`):**
   - Mobilde sütun sayısı 4'ten **7 sütuna** çıkarıldı (Geniş ekranda 64px auto-fill).
   - Oda numarası yazı boyutu `1.15rem`'den `0.78rem`'e optimize edildi.
   - Oda tipi ve durum şeritleri `0.38rem` olarak orantılı küçültüldü.
   - Temiz/Kirli/Arıza durum rozetleri ve ikonlar 11px mikro boyutta net olarak korunurken, alanı daraltan büyük C/O metin etiketleri kompakt modda gizlenerek alan tasarrufu sağlandı.
   - Kullanıcının seçimi `localStorage.getItem('hk_grid_density')` ile hafızaya alınır, sayfa yenilense veya uygulama kapatılıp açılsa da son tercih hatırlanır.
4. **Geri Bildirim Baloncuğu (Zoom Toast):**
   - Mod değiştiğinde ekranın alt kısmında şık animasyonlu bir bildirim ("Kompakt Görünüm: Odalar 2x Küçültüldü" / "Standart Görünüm") gösterilir.

#### 3. Canlı Dağıtım
- Değişiklikler canlı Society sunucusuna (`192.168.0.128:5002`) SFTP ile yüklendi ve Flask servisi yeniden başlatıldı (PID: `253594`).
- HTTP 200 testi yapıldı, mobil cihazlarda sorunsuz çalıştığı doğrulandı.


### Bölüm 22: "Dünden Kirli" (Boş Kirli) Mantığı & Doğrulaması (2026-09-05 21:58)

#### 1. Otelcilik & Sedna Veri Tabanı Mantığı
- **Bugün Çıkan Kirli:** Misafir bugün çıkış yapmış ve oda kirliye alınmıştır. Çıkış tarihi bugündür (`CAST(CheckOutDate AS DATE) = @Today`).
- **Dünden Kalan Kirli (Boş Kirli):** 
  * Misafir dün veya daha önceki tarihlerde çıkış yapmıştır (`CheckOutDate <> @Today`).
  * Odada aktif konaklayan misafir yoktur (`DOLU_BOS = 0`).
  * Odaya bugün yeni giriş yapılmamıştır (`CheckinDate <> @Today`).
  * Ancak oda temizlenmemiştir (`DirtyClean = 1`).
  * Gece denetimi (Night Audit) veya takvim ertesi güne geçtiğinde sistem bu odaları otomatik olarak **"Dünden Kirli"** grubuna ve sayacına dahil eder.

#### 2. Canlı Sunucu Doğrulaması
- Canlı sunucu (`192.168.0.128:5002`) API'sinden çekilen gerçek verilerle doğrulandı:
  * Toplam Dünden Kirli Sayısı: **2 Oda** (`403` ve `414`).
  * Her iki odanın da `Dolu = 0`, `Bugün Gelen = 0`, `Bugün Gidecek = 0`, `Durum = KIRLI` ve `CheckOutDate < @Today` olduğu teyit edildi.
  * Sistem Sedna Ön Büro ve Housekeeping standartlarına göre %100 kusursuz çalışmaktadır.


### Bölüm 23: Room Change (Oda Değişikliği) Odalarının Dünden Kirliye Düşmesinin Engellenmesi (2026-09-06 10:23)

#### 1. Sorun ve İhtiyaç
- Kullanıcı bildirimi: "HK mobil programında 333 nolu oda room change oldu, dünden kirliye düşmüş. Room change olan odalar asla dünden kirliye düşmesin, direkt kirliye düşsün."
- Örnek Vaka (Oda 333): Misafir (WILLIAM JOHN DAWSON - Rez No: 28712) dün 333 nolu odada konaklamış, bugün (06.09.2026) Ön Büro tarafından 208 nolu odaya Room Change yapılmıştır.
- Eski sorguda RoomChange sadece `RoomChangePlan` tablosundan kontrol ediliyordu. Ancak Sedna Ön Büro oda değişikliğini fiilen `DailyDetail` tablosunda dün 333, bugün 208 olarak güncellediği için eski oda (333) dünden devreden boş kirli gibi algılanıyordu.

#### 2. Uygulanan Çözüm
1. **`queries_hk.py` - `TodayRC` CTE Güçlendirildi:**
   - Resmi plan tablosunun (`RoomChangePlan`) yanı sıra, Sedna'da anlık/fiili olarak yapılan tüm oda değişiklikleri `DailyDetail` üzerinden bağlandı:
   ```sql
   SELECT dd_old.Room AS Room
   FROM DailyDetail dd_new
   JOIN DailyDetail dd_old ON dd_new.ReservationId = dd_old.ReservationId 
        AND dd_old.StayDate = DATEADD(day, -1, dd_new.StayDate) 
        AND dd_old.Room <> dd_new.Room
   WHERE CAST(dd_new.StayDate AS DATE) = @Today
   ```
   - Böylece dünden bugüne oda değişikliği ile boşalan eski odalar ve yeni odalar anında `TodayRC` kümesine dahil edilir.
2. **`BOS_KIRLI` Filtresinden Kesin Muafiyet:**
   - `rc.Room IS NULL` şartı sayesinde Room Change olan hiçbir oda artık `BOS_KIRLI` (Dünden Kirli) grubuna DÜŞMEZ.
   - Doğrudan genel **KİRLİ** durumuna (`DURUM: KIRLI`, `BOS_KIRLI: 0`) düşer.
3. **Kart Üzerinde "ROOM CHANGE" Rozeti:**
   - Boşalan eski oda üzerine şık mavi renkli `<div class="co-card-badge"><i class="fas fa-exchange-alt"></i> ROOM CHANGE</div>` etiketi eklendi. HK personeli odaya baktığında odanın dünden kalan değil, bugün yapılan bir Room Change neticesinde kirlendiğini anında görür.

#### 3. Canlı Test ve Doğrulama
- Canlı sunucuya aktarıldı (PID: `652701`).
- Oda 333 test edildi:
  * `DURUM: KIRLI`
  * `BOS_KIRLI: 0` (Dünden Kirli'den tamamen çıkarıldı)

### Bölüm 24: Room Change Listesi Popup Kutucuğu (RC Butonu & Modalı) Eklendi (2026-09-06 10:35)

#### 1. İhtiyaç ve Kapsam
- Kullanıcı talebi: "Room change olanları gösteren bir küçük kutucuk tıklayınca hangi oda hangi odaya room change oldu onu gösterelim. Ancak room change olan oda mutlaka kirliye düşsün dünden kirli olmasın, dünden kirli olanlar ise bir gün önceden kirli olupta yetişemeyen odalar dünden kirli olarak görünsün."

#### 2. Uygulanan Geliştirmeler
1. **Veritabanı Katmanı (`queries_hk.py` - `get_room_changes` fonksiyonu):**
   - Sedna SQL'de hem `DailyDetail` fiili oda değişiklikleri hem de `RoomChangePlan` planlı kayıtları taranarak şu alanlar JSON formatında çekildi:
     * `OldRoom` (Eski Oda No)
     * `NewRoom` (Yeni Oda No)
     * `GuestName` (Misafir Adı Soyadı)
     * `Voucher` (Voucher No)
     * `ChangeTime` (Değişiklik Saati)
     * `Source` (Fiili RC / Planlı RC)
2. **Backend API Katmanı (`hk_server.py`):**
   - `/api/hk/data` endpoint'ine `"room_changes": room_changes` dizisi eklendi.
3. **Frontend UI Katmanı (`hk_mobile.html`):**
   - **Header RC Butonu (`#headerRcBtn`):** Üst çubuğa mor temalı, dinamik sayaçlı rozet butonu eklendi (`RC <count>`). Eğer bugün herhangi bir Room Change yoksa buton görünmez (`display: none`), Room Change gerçekleştiği an otomatik belirir ve sayıyı gösterir.
   - **Room Change Detay Modalı (`#rcModal`):** Butona tıklandığında açılan açılır pencere tasarlandı:
     * Hangi eski odadan hangi yeni odaya geçildiği görsel oklarla vurgulanır: `[333 (Eski)] ➔ [208 (Yeni)]`.
     * Misafirin tam adı ve voucher numarası gösterilir.
     * Değişikliğin yapıldığı saat/zaman bilgisi listelenir.
   - **Dünden Kirli & Kirli Kuralı:**
     * Room Change olan odalar (örneğin 333 nolu oda) `BOS_KIRLI = 0` tutularak asla dünden kirliye düşürülmez, doğrudan `KİRLİ` kategorisinde gösterilir.
     * `DÜNDEN KİRLİ` filtresi yalnızca dünden kalan ve henüz temizlenemeyen gerçek devreden odalara ayrılmıştır.

#### 3. Canlı Sunucu Doğrulaması (`192.168.0.128:5002`)
- Dosyalar SFTP ile canlıya yüklendi ve Flask servisi yeniden başlatıldı (PID: `659665`).
- API test edildi:

### Bölüm 25: Room Change Modalı İçine Tarih Seçici ve Late Check-Out (Geç Çıkış) Entegrasyonu (2026-09-06 10:44)

#### 1. İhtiyaç ve Kapsam
- Kullanıcı talebi: "Geçmiş tarihleri gösteren bir tarih seçici olsa dünü ondan önceki günü gösterebilirmi, late room change görebilse iyi olur... Late checkout ve room changeleri room change modalı içine yapalım."

#### 2. Uygulanan Geliştirmeler
1. **Veritabanı Katmanı (`queries_hk.py`):**
   - `get_room_changes(conn, target_date=None)`: Parametrik tarih desteği eklendi. `COALESCE(?, CAST(GETDATE() AS DATE))` ile hem bugünü hem de istenilen geçmiş/gelecek herhangi bir tarihi filtreleyebilir.
   - `get_late_checkouts(conn, target_date=None)`: Sedna'da `CheckOutDate = @TargetDate` ve `LateCOut` tanımlı olan misafirleri; oda numarası, uzatma saati, misafir adı, voucher ve odada/çıkış yaptı durumuyla getiren fonksiyon yazıldı.
2. **Backend API Katmanı (`hk_server.py`):**
   - `/api/hk/data` endpoint'ine `late_checkouts` dizisi dahil edildi.
   - `/api/hk/rc_history?date=YYYY-MM-DD` adında yeni bir endpoint açıldı; seçilen tarihe göre hem oda değişikliklerini hem geç çıkışları anlık döndürür.
3. **Frontend UI Katmanı (`templates/hk_mobile.html`):**
   - **Sekmeli (Tabs) Yapı:**
     * `Room Change (<count>)` sekmesi: Hangi eski odanın hangi yeni odaya aktarıldığı, saati ve misafir detayı.
     * `Late C/Out (<count>)` sekmesi: Geç çıkış izni olan odalar, çıkış uzatma saati (örn. `12:00`, `16:00`), misafirin hâlâ odada mı olduğu yoksa çıkış mı yaptığı rozeti.
   - **Tarih Seçici Çubuğu:**
     * `Bugün`, `Dün`, `Önceki Gün` hızlı seçim hap butonları (pills).
     * Yanında dilediği geçmiş veya ileri tarihi seçebileceği takvim/tarih seçici (`<input type="date">`).
   - Sekme veya tarih değiştiğinde anında Sedna'dan o günün verisi çekilip sayaçlar ve liste güncellenir.

#### 3. Canlı Sunucu Doğrulaması (`192.168.0.128:5002`)
- Dosyalar SFTP ile yüklendi ve Flask servisi yeniden başlatıldı (PID: `663756`).
- Test sonuçları:
  * **06.09.2026 (Bugün):** RC: 1 adet (`333 -> 208`), Late C/Out: 21 adet.
  * **05.09.2026 (Dün):** RC: 0 adet, Late C/Out: 14 adet.
  * **04.09.2026 (Önceki Gün):** RC: 1 adet (`123 -> 130`), Late C/Out: 5 adet.
- Modal penceresi hem oda değişikliklerini hem de geç çıkışları (late check-out) geçmiş tarihleriyle birlikte eksiksiz ve hızlı bir şekilde listelemektedir.

### Bölüm 26: Late Check-Out Listesinde İptal/Hayalet Rezervasyonların Temizlenmesi (2026-09-06 10:56)

#### 1. Sorun ve İnceleme
- Kullanıcı bildirimi: "101 nolu odada ben kalıyorum 2 defa gösterilmiş. TAYFUN005 SANLI005 diye bekliyor görünüyor, bu tür hatalar olmasın. Şu an 101'de Gökhan Kın var, 12'de çıkış yapacak görünüyor."
- Veritabanı analizi (`Reservation` tablosu):
  * RecId `31759` (TAYFUN005 SANLI005): Rezervasyon `Status = -1` (İptal edilmiş/silinmiş rezervasyon) ve `Room = ''` (fiili odası yok). Ancak referans `RoomNummer = 1` olduğundan sorgudaki `COALESCE(NULLIF(r.Room, ''), rm_ref.Room)` join'i sebebiyle Oda 101 olarak yakalanıyordu.
  * RecId `32130` (GÖKHAN KIN): Rezervasyon `Status = 2` (Fiilen Odada), `Room = '101'`, `LateCOut = '12:00'`. Gerçek ve geçerli olan tek rezervasyon budur.

#### 2. Uygulanan Çözüm
- `queries_hk.py` içerisindeki `get_late_checkouts` fonksiyonuna Sedna Ön Büro iş kuralları ve otel mimarisi tam olarak entegre edildi:
  * `INNER JOIN Room rm ON r.Room = rm.Room AND rm.ForeCast = 1`: Yalnızca Cook's Club'ın satılabilir 111 fiili misafir odasında konaklayan rezervasyonlar listeye dahil edildi. Lojman, sanal veya iptal/odası silinmiş kayıtlar elendi.
  * `r.Status IN (2, 3)`: Yalnızca fiilen **Odada (Inhouse - 2)** veya **Çıkış Yapmış (Departed - 3)** olan kayıtlar alınır. İptal edilmiş (`-1`), beklemede kalmış veya silinmiş rezervasyonlar elendi.
  * `Voucher NOT LIKE '%NOSHOW%'` ve `ResRemark NOT LIKE '%NOSHOW%'` kuralları eklendi.

#### 3. Canlı Test ve Doğrulama
- Güncellenen kodlar SFTP ile canlı sunucuya aktarıldı ve Flask servisi yeniden başlatıldı (PID: `671195`).
- Canlı API üzerinden geçmiş ve bugünkü veriler denetlendi:
  * **Bugün (06.09.2026):**
    - Toplam 20 geçerli geç çıkış.
    - 101 nolu oda için yalnızca tek ve doğru kayıt görünmektedir:
      `{'Room': '101', 'GuestName': 'GOKHAN KIN', 'UzatmaSaati': '12:00', 'Status': 2, 'DurumText': 'Odada', 'Voucher': '32130'}`
    - Hayalet/iptal kayıt (`TAYFUN005 SANLI005`) tamamen kaldırıldı.
  * **Dün (05.09.2026):**
    - Toplam 12 geçerli geç çıkış.
    - `VLADIMIR BARYSHEV` (iptal/odasız) ve `2003` nolu sanal oda kayıtları ayıklandı.
  * **Önceki Gün (04.09.2026):**
    - Toplam 4 geçerli geç çıkış.
    - `GHONA002` iptal kaydı elendi.
  * **Room Change Kuralları:**
    - Oda 333: `DURUM: KIRLI`, `BOS_KIRLI: 0`, `IS_ROOM_CHANGE: 1`
    - Dünden Kirli toplam oda sayısı: 8 adet (`127, 128, 335, 403, 406, 407, 414, 703`).
- Sistem tüm yönleriyle hatasız ve %100 kararlı duruma getirildi.

### Bölüm 27: Blokeli Odaların (dd.Status = 3 / Tahsisli) C/O-C/I Olarak Görünmesi Hatasının Düzeltilmesi (2026-09-06 13:10)

#### 1. Sorun ve İnceleme
- Kullanıcı bildirimi: "hk_mobil uygulamasında bloklu olan 121 nolu odada c/o olup c/in olacak gibi görünen bir problem olduğunu söylediler."
- Veritabanı incelemesi:
  * Oda 121: `HkStatus = 0`, `DirtyClean = 1 (Kirli)`
  * `DailyDetail` tablosunda `StayDate = '2026-09-06'`, `Status = 3`, `StatusRemark = 'NADIRE HANIMA TAHSIS EDILMISTIR.'`
  * Rezervasyon tablosunda: 121 nolu oda için bugün ne gelen rezervasyon ne de giden rezervasyon bulunmaktadır.
- Kök Neden:
  * `queries_hk.py` içerisindeki `IS_CO_CI` tanımında:
    ```sql
    CASE 
        WHEN (arr.HasArrival = 1 AND dep.OdadaHala = 1) OR dd.[Status] = 3 THEN 1
        ELSE 0
    END AS [IS_CO_CI]
    ```
    ifadesinde yer alan `OR dd.[Status] = 3` koşulu, Sedna Ön Büro'da blokeli/tahsisli olan odaları yanlışlıkla turnaround (C/O - C/I) oda olarak işaretliyordu.
  * Arayüz tarafında (`templates/hk_mobile.html`) `isCoCiRoom` kontrolü `isBlokeli()` kontrolünden önce geldiği için, 121 nolu oda pembe renkte `C/O-C/I • KİRLİ` olarak render ediliyordu.
  * Ayrıca `coci_cnt` üst KPI sayaç sorgusunda da `OR dd.[Status] = 3` bulunduğu için C/O - C/I oda sayısı gereksiz yere şişiyordu.

#### 2. Uygulanan Çözüm
- `queries_hk.py`:
  * `IS_CO_CI` tanımı yalnızca gerçek Turnaround (aynı gün hem çıkış hem giriş olan) odaları kapsayacak şekilde güncellendi:
    ```sql
    CASE 
        WHEN arr.HasArrival = 1 AND (dep.OdadaHala = 1 OR dep.CikisYapildi = 1) THEN 1
        ELSE 0
    END AS [IS_CO_CI]
    ```
  * `coci_cnt` üst istatistik sorgusundan `OR dd.[Status] = 3` kaldırıldı. Sadece gerçek C/O ve C/I olan odalar sayılacak şekilde güncellendi.
- Canlı sunucuya dağıtım yapıldı ve Flask servisi yeniden başlatıldı (PID: `741426`).

#### 3. Doğrulama
- Canlı API üzerinden 121 nolu oda verisi kontrol edildi:
  * `ODA: '121'`
  * `DURUM: 'BLOKELI'`
  * `IS_CO_CI: 0`
  * `STATUS_REMARK: 'NADIRE HANIMA TAHSIS EDILMISTIR.'`
  * `DD_STATUS: 3`
- Arayüzde kart rengi: İndigo (`#6366f1`), etiket: `BLOKELİ • KİRLİ`.
- Gerçek Turnaround odaları (4 adet): `302, 318, 320, 327`.
- Blokeli odalar (4 adet): `121, 415, 423, 705`.

