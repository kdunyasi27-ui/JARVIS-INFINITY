# JARVIS INFINITY - Güvenlik Politikası

## 1. Gizli bilgiler

- Gerçek API anahtarları GitHub'a yüklenmez.
- .env dosyası paylaşılmaz.
- Gizli bilgiler ortam değişkenlerinde saklanır.

## 2. Kullanıcı güvenliği

- API istekleri doğrulanır.
- Yetkisiz erişim engellenir.
- Kullanıcı verileri izinsiz paylaşılmaz.

## 3. Otonom geliştirme güvenliği

JARVIS INFINITY geliştirme önerileri hazırlayabilir.

Ancak:

- Kod değişiklikleri önce ayrı ortamda test edilir.
- Başarısız testler ana sisteme uygulanmaz.
- Kritik değişiklikler kullanıcı onayı ister.
- Geri dönüş imkânı korunur.

## 4. Sistem güvenliği

- Güvenilmeyen kod doğrudan çalıştırılmaz.
- Dosya erişimi izinlerle sınırlandırılır.
- Ağ erişimi kontrol altında tutulur.
- İşlem kayıtları tutulur.

## 5. Acil durum

Bir güvenlik sorunu tespit edilirse:

1. Riskli işlem durdurulur.
2. İlgili kayıtlar korunur.
3. Yönetici bilgilendirilir.
4. Sorun giderilmeden işlem yeniden başlatılmaz.

## 6. Temel ilke

Güvenlik, hızdan ve otomatik geliştirmeden
önce gelir.
