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




