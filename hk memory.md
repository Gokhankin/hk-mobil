# HK Mobil Memory & Sistem Dokümantasyonu

## 📌 Proje Genel Bakışı
**HK Mobil**, Cook's Club Adaköy için geliştirilmiş, Kat Hizmetleri (Housekeeping) personelinin telefon veya masaüstü bilgisayarlar üzerinden anlık oda durumlarını (KİRLİ, TEMİZ, ARIZALI/OOO, BLOKELİ, SABAH/AKŞAM Vardiyası) takip ettiği ve değiştirdiği mobil öncelikli web portalıdır.

---

## 🛠️ Mimari ve Sistem Yapılandırması

* **Sunucu (Ubuntu):** `192.168.0.128`
* **Proje Dizini:** `/home/society/Masaüstü/hk_mobil/`
* **Backend:** Flask (`hk_server.py`)
* **Python Sanal Ortamı (venv):** `/home/society/Masaüstü/short/sedna_rapor/venv/`
* **Çalıştırma Portu:** `5002`
* **Veritabanı Entegrasyonu:** Sedna SQL Server (`192.168.0.41:1433`, Database: `SednaAdakoy`)
* **Canlı Ngrok Tüneli:** `https://scouring-outpour-handball.ngrok-free.dev`

---

## 💡 Veritabanı ve Mantık Kuralları

1. **Fiziksel Satılabilir Odalar (111 Oda Filtresi):**
   * Veritabanı sorgularında (`queries_hk.py`) `ForeCast=1` filtresi uygulanır. Sanal / PM odalar (1000, 2000, 2001 vb.) ve teknik odalar hariç tutularak tam olarak oteldeki 111 satılabilir fiziksel oda raporlanır.
2. **Anlık Canlı Yazma (Write-Back):**
   * Kullanıcı arayüzde oda durumunu (ör. KİRLİ ➔ TEMİZ) güncellediğinde, SQL üzerindeki `Room` ve `DailyDetail` tabloları anında güncellenir ve `conn.commit()` ile Sedna sistemine anlık işlenir.
3. **Vardiya Mantığı:**
   * **SABAH Vardiyası:** Genel oda temizlik ve hijyen durumunu (`KİRLİ / TEMİZ / ARIZALI / BLOKELİ`) yönetir.
   * **AKŞAM Vardiyası:** Her gün sıfırlanan Turndown (Akşam Yatak Açma Servisi) takibidir. Odalar güne `BEKLİYOR` (Gri) başlar, servis yapıldıkça `AKŞAM TAMAM` (Mor) durumuna çekilir.

---

## 🎨 Arayüz (UI/UX) ve Mobil Optimizasyonlar

1. **Kusursuz Mobil Düzen (No Overflow):**
   * `max-width: 100vw`, `overflow-x: hidden !important` ve `touch-action: pan-y` kullanılarak mobil cihazlarda sağa/sola çekince oluşan sayfa kaymaları ve arkadaki beyaz boşluklar tamamen engellenmiştir.
   * Mobil cihazlarda odalar tam oturan **4'lü Izgara (Grid)** yapısında gösterilir.
2. **Açık / Koyu Mod (Dark & Light Mode):**
   * Sağ üst kontrol çubuğuna **Ay / Güneş ikonu** eklenmiştir.
   * Koyu modda göze hoş gelen `Slate Dark (#0f172a / #1e293b)` renk paleti kullanılır.
   * Seçilen mod `localStorage` hafızasına kaydedilir, sayfa yenilendiğinde otomatik hatırlanır.
3. **Not Balonları (Tooltip Position & Z-Index):**
   * Masaüstü görünümde oda kartının üzerine gelindiğinde oda ve durum notları gösterilir.
   * Üst sıradaki odaların notlarının mavi sayaç çubuğunun altında kalmaması için not pencereleri kartın altına doğru (`top: 105%`) açılacak şekilde ve maksimum katman önceliğiyle (`z-index: 10000`) konumlandırılmıştır.
4. **Society Portal Entegrasyonu:**
   * Adaköy Society Portal ana orkestratör ekranına (`https://garage-specimen-shucking.ngrok-free.dev`) **HK Mobil Housekeeping** servisi, canlı Ngrok butonu ve ikonlarıyla entegre edilmiştir.

---

## 🚀 Çalıştırma ve Servis Komutları (Ubuntu)

```bash
# Servisi ve Ngrok tünelini arka planda başlatma
cd "/home/society/Masaüstü/hk_mobil"
nohup /home/society/Masaüstü/short/sedna_rapor/venv/bin/python3 hk_server.py > hk.log 2>&1 &
nohup ngrok http --url=scouring-outpour-handball.ngrok-free.dev 5002 > ngrok_hk.log 2>&1 &
```

---
*Son Güncelleme Tarihi: 3 Ağustos 2026*
