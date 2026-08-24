# Housekeeping (HK) Mobil ve Dashboard Geliştirme Notları

Bu döküman, Sedna SQL veritabanı üzerinden çalışan Housekeeping (Oda Durumu) entegrasyonu ve sonradan geliştirilen özel mobil uygulamanın tüm aşamalarını kaydetmek amacıyla oluşturulmuştur.

## 1. Veritabanı Sorununun Çözümü ve Sütun Eşleştirme
- **Sorun:** HK raporları ilk başta Sedna veritabanı `Room` tablosunda hata veriyordu çünkü standart tahmin edilen (`RoomNumber`, `RoomType`, `Status`) sütun adları sistemle uyuşmuyordu.
- **Çözüm:** `test_room.py` isimli ufak bir betik yazılarak tablodaki gerçek sütunlar listelendi.
- Doğru eşleştirmeler şu şekilde yapıldı ve `queries.py` güncellendi:
  - Oda Numarası ➔ `Room`
  - Oda Tipi ➔ `RoomTypeCode`
  - Temizlik Durumu ➔ `HkStatus`

## 2. Etkileşimli (Tıklanabilir) Oda Durum Paneli
- Yalnızca salt-okunur (read-only) tablolardan vazgeçilerek **canlı** güncellenebilen bir yapıya geçildi.
- **Backend (`app.py` & `queries.py`):** `/api/hk/update` adı altında bir POST rotası oluşturuldu. Bu rota, kullanıcının butona bastığı an `UPDATE Room SET HkStatus = ? WHERE Room = ?` komutunu çalıştırarak Sedna DB'yi gerçek zamanlı günceller.
- **Hız ve Performans Optimizasyonu:** Kullanıcı butona bastığında tüm sayfanın veya veritabanı verisinin baştan yüklenmesi (Refresh sürtünmesi) engellendi. Kutucuklar yerel Javascript ile saniyesinde renk ve durum değiştiriyor, böylece sıfır gecikme (zero-lag) ile arka arkaya düzinelerce oda tıklanabiliyor.
- **Durum Döngüsü (Renk Mantığı):**
  - `KİRLİ` (Kırmızı 🟥) ➔ `TEMİZ` (Yeşil 🟩)
  - `TEMİZ` (Yeşil 🟩) ➔ `HAZIR` (Sarı 🟨)
  - `HAZIR` (Sarı 🟨) ➔ `BİLİNMİYOR` (Gri ⬜)
  - `BİLİNMİYOR` (Gri ⬜) ➔ *Tekrar Başa: `KİRLİ`*

## 3. Bağımsız HK Mobil Uygulaması (`hk_mobil` klasörü)
HK çalışanlarının otel operasyonundayken telefonlarından (Ngrok aracılığıyla) kolayca erişebilmesi için ana panelden bağımsız, özel bir mikro-site oluşturuldu.
- **`hk_server.py`:** Sadece HK işlemlerine odaklanan, `5002` portunda çalışan hafifletilmiş Flask sunucusu.
- **`templates/hk_mobile.html` Tasarım Özellikleri:**
  - Premium mobil uygulama hissiyatı (Ölçeklenemeyen yapı: `user-scalable=no`).
  - Ekranı kaydırsanız da yukarıda sabit kalan (Sticky) mavi bilgilendirme barı.
  - Tüm otel geneli **Canlı Sayaçlar** (Toplam Temiz, Toplam Kirli, Toplam Hazır).
  - Kusursuz Kare Grid Mimarisi: Geniş bilgisayar ekranlarında kutucuklar esnemez (sol-sağ uzamaz), sadece yan yana yığılır (Örn: 15 sütun). Mobilde ise dörderli sütunlar halinde mükemmel küçük kareler oluşturur (`aspect-ratio: 1/1`). 
- **`baslat_hk_mobil.bat`:** Operasyon sırasında tek tıkla hem Flask Canlı Sunucusunu hem de personelin telefonundan erişebilmesi için gerekli olan Ngrok HTTPS tünelini çalıştırır. Personeller Wifi şebekesine bağlı olmasalar bile, 4G üzerinden verilen adrese girip Sedna'yı canlı anlık yönetebilirler.

## 4. Sedna Cloud Tarzı Müşteri KPI Kartları Entegrasyonu
- **Gereksinim:** HK Mobil uygulamasının üst kısmındaki oda durumu KPI pencerelerinin hemen üzerine Sedna Cloud projesinde olduğu gibi günlük **Gelen Müşteri**, **Gidecek Müşteri** ve **Inhouse Müşteri** istatistiklerinin eklenmesi.
- **Backend (`queries_hk.py` & `hk_server.py`):** 
  - `get_guest_stats(conn)` fonksiyonu yazıldı. Sedna SQL Server veritabanından `Reservation` ve `Room` tabloları sorgulanarak bugünün Gelen Müşteri (Giriş yapacak), Gidecek Müşteri (Çıkış yapacak) ve Inhouse Müşteri (Konaklayan) oda sayıları ve toplam Pax (yetişkin + çocuk) sayıları çekildi.
  - `/api/hk/data` API yanıtına `guest_stats` nesnesi eklendi.
- **Frontend (`templates/hk_mobile.html`):**
  - HK Mobil başlığında (Header) sticky üst alanın oda sayaçları üstüne 3'lü esnek kart yapısı (`.guest-summary-bar`) eklendi.
  - Mobil ekran uyumlu cam etkisi (glassmorphism) ve özel renk temaları uygulandı:
    - **Gelen Müşteri:** Yeşil tonlar (`#34d399`) + Uçak giriş ikonu (`fa-plane-arrival`).
    - **Gidecek Müşteri:** Kırmızı/Gül tonları (`#fb7185`) + Uçak çıkış ikonu (`fa-plane-departure`).
    - **Inhouse Müşteri:** Mavi tonlar (`#38bdf8`) + Yatak ikonu (`fa-bed`).
  - HK Mobil giriş ekranına yetkisiz erişimi engellemek için **1234** PIN şifre koruması eklendi. Oturum doğrulama `sessionStorage` seviyesine çekilerek her yeni tarayıcı girişinde ve üst menüden görevli değiştirildiğinde tekrar şifre girm zorunlu kılındı.
  - **Sedna Front Office `S/O` Kırmızı İbare Düzeltmesi:** HK Mobil'den oda temizlendiğinde Sedna tablosunda `HkStatus = 2` yazılarak ortaya çıkan kırmızı **S/O** (Second OK/Supervisor) ibaresi engellendi. Sedna ana renk/durum kontrolünün `DirtyClean` (1=Kirli, 0=Temiz) sütununda olduğu doğrulanıp `HkStatus` varsayılan 0 değerine çekildi. Veritabanındaki 118 nolu odanın `HkStatus` değeri sıfırlanarak kırmızı ibare kaldırıldı.

## 6. Güvenli Oda Durum Değiştirme ve Oda Arama Arayüzü (Ağustos 2026)
- **Ergonomik Oda Arama Çubuğu (Search Bar):**
  - HK Mobil uygulamasının üst kısmındaki oda sayaçları (KPI) üzerine cep telefonunda tam satır kaplayacak şekilde yüksekliği artırılmış, 1 satır büyük bir arama çubuğu ve yeşil **OK** butonu yerleştirildi.
  - Mobil cihazlarda arama kutusuna dokunulduğunda doğrudan sayısal numaralandırma klavyesinin açılması için `inputmode="numeric"` ve `pattern="[0-9]*"` özellikleri eklendi.
  - Kullanıcı oda numarasını (Örn: `104`) girip **OK** tuşuna bastığında veya 'Enter' tıkladığında ekranda o odayı özel olarak süzüp otomatik odaklanır (smooth scroll + sarı halka vurgulama animasyonu).
- **Çift Aşamalı Güvenlik Onay Modalı (Popup + OK Butonu):**
  - Yanlışlıkla ekrana dokunmaları ve odaya tıklar tıklamaz veritabanının anında değişmesini engellemek için doğrudan tıklama mantığı kaldırıldı.
  - Odaya dokunulduğunda ekranda **Güvenlik Penceresi (Modal Popup)** açılır.
  - Açılan modal pencerede oda no, oda tipi, oda notu ve renkli durum seçenekleri (KİRLİ 🟥, TEMİZ 🟩, HAZIR 🟨, ARIZALI ⬛, BLOKELİ 🟦) sunulur.
  - Kullanıcı yeni durumu seçip en alttaki yeşil **"ONAYLA (OK)"** butonuna basmadan Sedna SQL veritabanı kesinlikle güncellenmez.

## 7. Kullanıcı ve Güvenlik Şifresi Güncellemesi (Ağustos 2026)
- **Giriş Kullanıcı Adı:** Varsayılan görevli kullanıcısı **`HK`** olarak belirlendi. Sedna DB'de ilk kurulumdan kalan `MAID1` test kaydı hem backend (`queries_hk.py`) hem de frontend (`templates/hk_mobile.html`) seviyesinde filtrelenerek listeden tamamen temizlendi.
- **Giriş Şifresi:** PIN şifresi **`123`** olarak güncellendi.
- **Canlı Sunucu Güncellemesi:** Değişiklikler canlı Society sunucusuna (`192.168.0.128`) aktarıldı ve `/home/society/Masaüstü/hk_mobil/venv/bin/python3` ile servis yeniden başlatıldı.

## 8. Tıklanabilir Müşteri KPI Filtreleme ve Sıfırlama Özellikleri (Ağustos 2026)
- **Etkileşimli Müşteri KPI Kartları:**
  - **Gelen Müşteri**, **Gidecek Müşteri** ve **Inhouse Müşteri** kartlarına tıklama özelliği eklendi.
  - Kartlara tıklandığında alt oda grid alanı otomatik süzülerek ilgili gruba giren odaları anında listeler.
- **SQL ve KPI Veri Senkronizasyonu Hata Düzeltmesi:**
  - Üst sayaç sayısıyla tıklayınca çıkan oda sayısındaki uyumsuzluğu gidermek için `queries_hk.py` içerisindeki `BUGUN_GELEN`, `BUGUN_GIDECEK` ve `DOLU_BOS` SQL alt sorguları, üstteki `get_guest_stats` sorgusuyla birebir eşleştirildi (`Status` & `StatusCode` filtrelenmesi, No-Show temizliği vb.).
- **Filtre Sıfırlama & Varsayılana Dönüş:**
  - **Sol Üst Logo / Başlık:** `CC HK` başlığına basıldığında tüm aktif süzgeçler ve arama kelimeleri temizlenerek varsayılan tüm oda listesine dönülür.
  - **Aynı Karta Tekrar Basma:** Seçili süzgeç kartına ikinci kez basıldığında filtre otomatik olarak kaldırılır.

## 9. Temel Operasyonel Tasarım ve Veri Tutarlılığı Prensibi (Ağustos 2026)
- **Tek Gerçek Kaynak (Single Source of Truth):** Projelerde yeni iş mantığı uydurmak veya varsayımda bulunmak kesinlikle yasaktır. Gerçeğin tek kaynağı Sedna veritabanı (SQL Server) ve Sedna Front Office iş kurallarıdır.
- **Sedna Görselleştirme Misyonu:** Uygulamalarımızın tek ve asli görevi; Sedna ve SQL sorgularının ürettiği durum ve verileri, en doğru formatta ve en göz alıcı/kullanıcı dostu mobil KPI arayüzleri ile sahada operasyon yapan kullanıcıya anlık yansıtmaktır.
- **Canlı Veri Senkronizasyonu & Filtre Mantığı:**
  - Örneğin Sedna'da bir oda çıkış yaptığında (`Status 2 -> 3`), Gidecek Müşteri KPI kartı (10'dan 9'a) ve tıklanınca süzülen oda listesi anında %100 eşzamanlı olarak 9 odaya düşer.
  - Sayfa yenilendiğinde veya otomatik güncellendiğinde kullanıcı tarafından seçilmiş olan aktif filtre state'i (`applyCurrentFilter()`) korunur.

## 10. Acente Bilgisi, C/O Çıkış Durumu ve Uzatma Saati Entegrasyonu (Ağustos 2026)
- **Acente Bilgisi (C/N ve Genel Odalar):**
  - `queries_hk.py` içerisindeki `Reservation` sorgusuna `LEFT JOIN Agency a ON res.AgencyId = a.RecId` eklenerek `ACENTE` adı çekildi.
  - C/N (Giriş yapacak) odalarda ve oda kartlarında acente bilgisi (Örn: `🏢 NEILSON`, `🏢 EXPEDIA`, `🏢 BOOKING`) etiketi ile görselleştirildi.
  - Oda durum değiştirme güvenlik pop-up modalında müşteri detay kartına **Acente** bilgisi eklendi.
- **C/O Odası Çıkış Durumu (Çıkış Yapıldı mı / Odada Hâlâ mı?):**
  - Bugün ayrılacak (C/O) odaların Sedna `Reservation.Status` değeri kontrol edildi:
    - `Status = 3` ➔ **🟢 ÇIKIŞ YAPILDI (C/O Yapıldı)**
    - `Status = 2` ➔ **🔴 HENÜZ ÇIKIŞ YAPMADI (Odada Hâlâ)**
  - Hem oda kartlarında canlı rozet etiketi olarak, hem de detay modalında büyük bilgilendirme kartı olarak gösterilmesi sağlandı.
- **Geç Çıkış / Uzatma Saati (Late Check-Out / Extension):**
  - `Reservation.LateCOut` sütunu sorguya dahil edilerek standart checkout (12:00) haricinde tanımlanan özel uzatma saatleri (Örn: `16:00`) tespit edildi.
  - Uzatması olan odaların kartlarına saat ikonlu **⏰ 16:00** rozeti eklendi.
  - Güvenlik modalında sarı/altın vurgulu **"GEÇ ÇIKIŞ / UZATMA SAATI: 16:00"** uyarı kutusu yerleştirildi.

## 11. Mobil Header 4-Satır Yapısı & Masaüstü Eşit Oda Kutuları Düzenlemesi (Ağustos 2026)
- **Eşit KPI Kart Boyutları (Mobilde 4 Satır Düzeni):**
  - Hem `.summary-item` (Oda durumları) hem de `.guest-summary-item` (Müşteri sayıları) kartlarına sabit `height: 44px`, eşit `border-radius: 10px`, aynı font ölçeklendirmeleri uygulandı.
  - Mobil header alanı ekran yüksekliğini kaplamayacak şekilde tam 4 düzenli satıra oturtuldu:
    - **Satır 1:** Header başlığı, Maid seçimi, Tema butonu, Çıkış ve Yenile butonları.
    - **Satır 2:** Müşteri KPI Kartları (Gelen, Gidecek, Inhouse).
    - **Satır 3:** Oda Durum KPI Kartları (Kirli, Temiz, Arızalı, Blokeli).
    - **Satır 4:** Oda arama girdisi (`Oda No...`), OK butonu ve Sabah/Akşam vardiya tabları (sıkıştırılmış tek satır).
- **Masaüstü Eşit Oda Kutucukları:**
  - Masaüstü ve geniş ekranlarda (`min-width: 520px`) `.grid` yapısına `grid-template-columns: repeat(auto-fill, 108px)` ve `.room-card` elemanına `width: 108px !important; height: 108px !important; aspect-ratio: 1 / 1 !important; overflow: hidden !important;` kuralları uygulandı.
  - Farklı içerik uzunluğuna sahip oda kartlarının masaüstünde biri büyük biri küçük görünmesi engellendi; tüm kartlar milimetrik eşit kareler olarak sabitlendi.
- **Mobilde Sağa/Sola Kayma (Horizontal Scroll) ve Taşma Koruması:**
  - `.grid` için `grid-template-columns: repeat(4, minmax(0, 1fr))` kuralı tanımlanarak hücrelerin içerik genişliği nedeniyle 4 sütundan dışarı genişlemesi kesin olarak engellendi.
  - `html`, `body`, `.content`, `.header`, `.grid` ve `.room-card` elemanlarına `overflow-x: hidden !important;`, `max-width: 100%;` ve `min-width: 0;` uygulanarak mobilde sağa/sola kayma (scroll) riski sıfırlandı.

## 12. Veri Yükleme Yavaşlığı Optimizasyonu - 30 Kat Hız Artışı (Ağustos 2026)
- **Neden Yavaştı? (3-4 Saniye Bekleme Analizi):**
  - `queries_hk.py` içerisindeki `get_hk_status` fonksiyonu, 111 fiziki oda için her seferinde `OUTER APPLY` alt sorgusunda `Reservation` ve `Agency` tablolarında 111 defa ayrı ayrı tarih dönüştürme (`CAST(CheckinDate AS DATE)`), `NOT LIKE '%NOSHOW%'` ve `Agency` tablosuna `LEFT JOIN` atarak veritabanı taraması yapıyordu.
- **Uygulanan CTE & Row-Number Optimizasyonu:**
  - Sorgu yapısı `Common Table Expression (CTE)` mimarisine taşındı. `@Today` değişkeni en başta 1 kez tanımlandı.
  - Bugün aktif reservations tek bir turlamada `ROW_NUMBER() OVER (PARTITION BY MatchRoom ORDER BY ...)` ile index tabanlı filtrelendi.
- **Sonuç:**
  - SQL veritabanı oda durum sorgu süresi **3.018 saniyeden 0.106 saniyeye (106 milisaniye)** düşürüldü (**30 kat hızlanma**).
  - Mobil uygulamanın `/api/hk/data` uç noktasından veri alma ve oda kutucuklarını ekrana basma süresi 4 saniyeden **1 saniyenin altına** indirildi.

## 13. Proje Yedekleme ve C/In & C/Out Tarihleri Entegrasyonu (Ağustos 2026)
- **Proje Yedeği:**
  - İşlem öncesinde tüm `hk_mobil` projesi `eski projeler/hk_mobil_backup_20260822` klasörüne eksiksiz yedeklendi.
- **SQL Sorgu Güncellemesi (`queries_hk.py`):**
  - `get_hk_status` CTE sorgusuna `CONVERT(VARCHAR(10), res.CheckinDate, 104) AS [CHECKIN_TARIHI]` ve `CONVERT(VARCHAR(10), res.CheckOutDate, 104) AS [CHECKOUT_TARIHI]` sütunları eklendi.
- **Frontend & Detay Popup Görselleştirmesi (`hk_mobile.html`):**
  - Güvenli oda durum değiştirme modalına (`#modalGuestDetailCard`) yeşil takvim ikonlu `guest-dates-row` eklendi (`📅 C/In: DD.MM.YYYY ➔ C/Out: DD.MM.YYYY`).
  - Misafiri olan veya rezervasyonu bulunan tüm odalarda C/In ve C/Out tarihleri mobil ekranda net şekilde gösterildi.

## 15. Dünden Kirli Mantığı ve Oda Durum Eşitleme Düzeltmesi (Ağustos 2026)
- **Sorun:** 
  - Bugün çıkış yapıp temizlenen (OK alınan), ardından bugün yeni giriş olan veya öğleden sonra tekrar kirlenen (RC / Re-Clean) odalar (Örn: Oda 114 ve 424), sistem tarafından hatalı şekilde "DÜNDEN KİRLİ" (Sarı / Kehribar kart) olarak gösteriliyordu.
  - Ayrıca oda HK Mobil uygulamasında `HAZIR (OK)` olarak işaretlendiğinde, SQL sorgusundaki `CASE` sıralaması nedeniyle `DURUM` etiketi `'OK'` yerine `'TEMIZ'` olarak dönüyor, bu da arayüzde `HAZIR` yerine `TEMİZ` olarak görünüyordu.
- **Çözüm ve Güncellemeler:**
  1. **SQL `BOS_KIRLI` Mantığı Sertleştirildi (`queries_hk.py`):**
     - Bir odanın "DÜNDEN KİRLİ" kabul edilebilmesi için; odanın Kirli olması, **ve** bugün Girişi (`BUGUN_GELEN = 0`), Çıkışı (`BUGUN_GIDECEK = 0`) veya Inhouse konaklaması (`DOLU_BOS = 0`) **olmaması** kuralı bağlandı.
     - Bugün hareketi (C/In, C/Out, Inhouse) bulunan tüm odalar tekrar kirlendiğinde (RC olduğunda) "Dünden Kirli" bayrağı sıfırlanıp normal **KİRLİ** (Kırmızı kart `#f43f5e`) olarak görüntülenmesi sağlandı.
  2. **SQL `DURUM` Öncelik Mantığı Düzenlendi (`queries_hk.py`):**
     - SQL sorgusundaki `CASE` bloğunda `rm.HkStatus = 3` (`'OK'`) koşulu `rm.DirtyClean = 0` (`'TEMIZ'`) koşulunun üstüne alındı.
     - Böylece HK Mobile uygulamasından `HAZIR (OK)` tıklanan odalar tam ve doğru şekilde `HAZIR` (Sarı/Gold `#f59e0b` kart) durumına geçti.
  3. **Frontend Savunma Kontrolü (`hk_mobile.html`):**
     - Frontend `renderGrid` fonksiyonunda `isBosKirli` mantığı; bugün gelişi, gidişi veya inhouse konaklayanı olan odaları "Dünden Kirli" kartından muaf tutacak şekilde korumaya alındı.
  4. **Canlı Sunucu Deployment:**
     - Değişiklikler canlı Society sunucusuna (`192.168.0.128:5002`) aktarılarak Flask servisi yeniden başlatıldı. 
     - `/api/hk/data` uç noktasından yapılan canlı testlerde `BOS_KIRLI` oda sayısı tam olarak 7 fiziki boş kirli odaya sabitlendi.

## 16. Gün İçi İşlem Gören Odaların (C/O ve Bugün Kirlenen) "Dünden Kirli" Çıkma Sorununun Kesin Çözümü (24 Ağustos 2026)
- **Dünden Kirli Tanımı & İş Mantığı:**
  - Konaklayan (Inhouse) misafirlerin 2. veya 3. gün kalan odaları kesinlikle "Dünden Kirli" **DEĞİLDİR**, "In-House / Dolu" oda temizliğidir.
  - Gerçek "Dünden Kirli" oda: İçinde **hiç misafir bulunmayan (BOŞ)** ve dün temizlenmeyip bugüne sarkan boş kirli odadır.
- **Kök Neden Analizi:**
  1. **Oda 103 (C/O Yapılan Oda):** Ön büro Sedna'da çıkış yaparken rezervasyonun `Room` alanını `2003` olarak güncelliyordu. Eski SQL sorgusu odayı "boş ve hareketsiz" sanıp C/O kaydını kaçırıyor ve odayı "Dünden Kirli" yapıyordu. `ActiveRes` CTE'sinde `Remark` alanındaki oda numarası eşleşmesi ve `MorningSnapshot` C/O verileri bağlanarak Oda 103'ün bugünkü C/O hareketi (`BUGUN_GIDECEK = 1`, `CO_YAPILDI` rozeti) %100 yakalandı.
  2. **Oda 309 (Bugün Kirliye Düşürülen Oda):** Sabah HK snapshot'ında (`HkHistory`) **TEMİZ** olan oda gün içinde kirlendiğinde (HK personeli kirliye düşürdüğünde), eski SQL sorgusu odanın **sabah temiz olduğunu** kontrol etmediği için odayı "Dünden Kirli" yapıyordu. `MorningSnapshot` CTE'si eklenerek, bir odanın "Dünden Kirli" sayılması için **sabah 09:10 snapshot'ında da (`DirtyClean = 1`) kirli olma şartı** eklendi. Sabah temiz olup gün içinde kirlenen tüm odalar normal **KİRLİ (Kırmızı)** durumuna çekildi.
- **Uygulanan SQL CTE Optimizasyonu (`queries_hk.py`):**
  - **`MorningSnapshot` CTE Entegrasyonu:** Sabah 09:10'da Sedna `HkHistory` tablosuna yazılan ilk durum snapshot'ı sorguya dahil edildi.
  - **Müşteri KPI Senkronizasyonu:** `get_guest_stats` fonksiyonu grid sorgusuyla %100 birebir senkronize edilerek üst KPI kartlarındaki Gidecek Oda sayısı (10) ile tıklanınca süzülen oda listesi tam eşitlendi.
- **Canlı Sunucu Doğrulaması:**
  - Değişiklikler canlı Society sunucusuna (`192.168.0.128:5002`) deploy edildi.
  - Canlı API testinde: Oda 103 `DURUM: KIRLI`, `CO_DURUM: CO_YAPILDI`, `BOS_KIRLI: 0`; Oda 309 `DURUM: KIRLI`, `BOS_KIRLI: 0` olarak 100% doğrulandı.
