# Türkiye Akademisyen Veri Seti (OpenAlex Tabanlı) 🇹🇷

Bu depo, **OpenAlex API** veritabanı kullanılarak Türkiye'deki üniversitelere bağlı olarak akademik faaliyet yürüten araştırmacıların verilerini toplamak, filtrelemek ve analiz etmek amacıyla geliştirilmiş açık kaynaklı bir veri seti ve toplama betiğini içerir.

## 📊 Veri Seti İçeriği
Veri seti, en az 5 ve üzeri yayına sahip olan Türkiye'deki akademisyenlerin temel bibliyometrik ve kurumsal bilgilerini barındırmaktadır. 

Oluşturulan dosyalarda yer alan sütunlar ve açıklamaları:
* **OpenAlex_ID:** Akademisyenin OpenAlex üzerindeki benzersiz kimlik numarası.
* **Ad_Soyad:** Akademisyenin adı ve soyadı.
* **Profil_URL:** OpenAlex üzerindeki detaylı profil bağlantısı.
* **ORCID:** Akademisyenin ORCID araştırmacı numarası.
* **Universite_Adi:** Bağlı olduğu son kurum / üniversite(ler).
* **Kurum_Turu:** Kurumun türü (Eğitim, devlet, tesis vb.).
* **Arastirma_Alanlari:** Başlıca çalışma ve uzmanlık alanları (Topics).
* **Makale_Sayisi:** Toplam yayın/makale sayısı (`works_count`).
* **Atif_Sayisi:** Toplam atıf sayısı (`cited_by_count`).
* **H_Index:** Akademik etki ölçütü H-indeksi.
* **Alternatif_Isimler:** Yayınlarda geçen alternatif isim varyasyonları.
* **Makale_Adlari:** (İsteğe bağlı modülle çekilen) En çok atıf alan makale başlıkları.

## 🗂️ Dosya Yapısı
Depo içerisinde şu dosyalar yer almaktadır:
* `openalex_tr_akademisyen.csv`: Tüm akademisyen verilerini içeren UTF-8 (Türkçe karakter uyumlu) CSV formatındaki ana veri seti.
* `openalex_tr_akademisyen.xlsx`: Veri setinin Excel formatındaki sürümü.
* `openalex_turkiye_akademisyen.py`: Verileri OpenAlex API üzerinden imleç (cursor) tabanlı ve güvenli hata yönetimiyle çeken Python betiği.

## 🚀 Veri Toplama Betiğinin Kullanımı

Eğer bu veri setini kendi bilgisayarınızda yeniden üretmek veya güncellemek isterseniz:

1. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install requests pandas openpyxl


   OpenAlex platformundan (ücretsiz) bir API anahtarı edinin ve ortam değişkeni olarak tanımlayın:

PowerShell: $env:OPENALEX_API_KEY="sizin_api_anahtariniz"

Linux/Mac: export OPENALEX_API_KEY="sizin_api_anahtariniz"

Betiği çalıştırın:

Bash
python openalex_turkiye_akademisyen.py --min-works 5
⚙️ Özellikler
Cursor Tabanlı Sayfalama: Büyük veri setlerinde kopma yaşamadan sayfa sayfa ilerleme.

Otomatik Kayıt ve Kaldığı Yerden Devam: Her 500 kayıtta bir diske yazma (append) ve openalex_state.json yardımıyla kesintilerde kaldığı yerden devam etme.

Hata Yönetimi: Ağ veya sunucu (HTTP 504, 429 vb.) kesintilerinde üstel bekleme (exponential backoff) mekanizması ile çökmeden devam etme.

📄 Lisans
Bu depo ve içerdiği veri seti CC0 1.0 Universal (Kamu Malı) lisansı ile lisanslanmıştır. Dilediğiniz gibi araştırma, geliştirme ve analizlerinizde özgürce kullanabilirsiniz.

Veri Kaynağı: OpenAlex API
