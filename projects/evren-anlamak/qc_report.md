# QC raporu: evren-anlamak (bağımsız QC, 2026-10-21)

**Karar: YAYINA HAZIR (v2).** Hiçbir şey paylaşılmadı (upload.json `posted: false`).

## Bütünlük (render bir kez kesilip yeniden yapılmıştı)
| dosya | kare | video / ses süresi | decode hatası | not |
|---|---|---|---|---|
| v1 upload (out/evren-anlamak_v1.mp4) | 1440 | 48,000 / 48,000 sn | 0 | eksiksiz, kesik değil; bt709 |
| v1 master | 1440 | 48,000 / 48,000 sn | 0 | eksiksiz |
| **v2 upload** out/evren-anlamak.mp4 (27,834,280 B, 4,43 Mbps) | 1440 | 48,000 / 48,000 sn | 0 | bt709, faststart, AAC 48 kHz |
| **v2 master** out/evren-anlamak_master.mp4 (43,300,573 B) | 1440 | 48,000 / 48,000 sn | 0 | bt709 |
Upload ile master arasındaki SSIM 0,987.

## Puanlar (1–10)
| | v1 | v2 | neden |
|---|---|---|---|
| Görsel | 7,5 | 8,5 | tahta formülleri ve etiketler telefonda okunuyor, S7 ve kapak sakinleşti, S8'deki çocuk UI bandından çıktı, S10'da poz atlaması yok |
| Retention | 7,5 | 8 | zil ayrışması ile topların ayrışması aynı anda; 12 hook/re-hook, en uzun re-hook boşluğu 5,4 sn; durağan an en fazla 1,4 sn |
| Ses | 8 | 8,5 | −14,2 LUFS, LRA 4,3, TP −1,7 dBFS; telefon simülasyonunda (300 Hz HP) −15,7 LUFS; ikiz zil artık ayrı tınıda |
| Bilgi / kaynak | 8,5 | 9 | S4 cümlesi konuşmacıyla uyumlu; %95'in bağlamı ve Planck nüansı eklendi; Einstein'a yıl eklendi |
| Teslim | 9 | 9,5 | eksiksiz, bt709; kapak cover_t'den alındı |
| Metadata | 8 | 9 | açıklamada Planck 2018 ve "ne olduklarını bilmiyoruz", Einstein (1936) |

## Düzeltmeler
1. **İkiz toplar ve ziller hizalandı.** Toplar 3. vuruşta ayrılıyordu, zil melodileri 6. vuruşta. KAOS_B tohumu 0,4001 → 0,403 yapıldı. Seriler artık 6. notada (rate 2 → S5'in 3. vuruşu = 21,6 sn) ayrılıyor; 6–17 arasındaki 12 notanın 12'si farklı. Ekranda tohum değeri geçmiyor; plan_tr.md güncellendi.
2. **saat / saat_b maskelemesi giderildi.** İkiz zilde FM oranı 3,5 → 2,0, index 2,2 → 1,6 oldu (daha yuvarlak, farklı bir zil). Pan ±0,5 → ±0,6. Birlikte çaldıkları kısım "iki zil aynı yolda" gibi, ayrılınca iki ayrı ses olarak duyuluyor.
3. **Tebeşir okunurluğu.** Engine'e `formula_dot`, `label_font` ve `note_font` parametreleri eklendi; varsayılanlar eskisi gibi. S2'de formüller 2 kat büyük ve ortalı. Alt simgeler artık nokta başına 12 çıktı pikseli; eskiden 3×5 mikro fontla 6 px idi. GÖRELİLİK / KUANTUM etiketleri Türkçe glifli 5×7 fontla yazılıyor; eskiden "GÜRELILIK" gibi bozuk okunuyordu.
4. **Küçük köşe notu.** Mikro "evrenin %95'i: ?" kaldırıldı. Yerine tebeşirle 5×7 "%95 = ?" yazılıyor ve callout bu notu gösteriyor: "Evrenin %95'i: bilinmiyor" (side below, 5,25. vuruşta, 16th). Eski callout bağlamsızdı ve notun üstünü örtüyordu.
5. **S4 dialog.** HAWKING, 2002 etiketinin altında üçüncü şahıs garip duruyordu. Yeni metin: "2002'de fikrimi değiştirdim: belki son teori _yok_." S3 gibi birinci şahıs bir özet; okuma süresi 3,05 sn < 4,5 sn ekranda kalma.
6. **S8'deki çocuk UI bandından çıktı.** `sky_view` y −150 → −100; ayaklar ~0,82 H'de, eskiden 0,88–0,97 H aralığındaydı. Einstein dialog'u xy [0,5; 0,585] konumunda. Yeni `const_y` parametresiyle denklem yıldız kümeleri yukarı alındı (−112 / −76 / −40), böylece dialog hiçbirini örtmüyor.
7. **S7 tahtaların tahtası ve kapak.** Yeni `far_ca` (CA ışığı 0,55 → 0,22) ve `far_dots` (taş noktaları 0,9 → 0,4) parametreleriyle komşu tahtalar sakin, ana tahta öne çıkıyor. Rule 30 piramidi hâlâ görünüyor ama gri blok kalabalığı yok. Kapak CRF-4 ara dosyadan 32,4 sn'de alındı (`--package` 0. kareyi yazıyordu).
8. **S10 iris içinde poz atlaması.** Yeni `rewind_turn` [1,2; 1,9] ile döngü segmenti S9'un yakın planıyla başlıyor (front pozu, kol aşağıda, kamera 1,12). Iris yalnızca paleti değiştiriyor; çocuk sonra q pozundan up pozuna dönüp teleskopa bakıyor. Kare 0'a iniş bozulmadı: dikiş farkı 1,03/255, eşiği aşan piksel sayısı v1 ile aynı (~50).
9. **Metadata.** Açıklamaya Planck 2018 nüansı ("varlıklarını ölçüyoruz ama ne olduklarını bilmiyoruz") ve Einstein (1936) eklendi. upload.json'a v2 notu yazıldı. retention_map.txt'nin sonuna v2 validate çıktısı eklendi.

## Doğrulama
- validate: OK. Tek uyarı süre (48 sn > 45). 12 hook/re-hook, en uzun re-hook boşluğu 5,4 sn, en uzun durağan an 3,45 sn (validator).
- Testler: cosmos 17 (yeni `test_qc_phone_legibility_options_and_pose_continuity` dahil), engine 14, fractal 12, narration 10, story 10, vision 10. Toplam 73/73 geçti.
- Ses bölümleri (LUFS): S1 −14,9 · S2 −16,8 · S3 −13,9 · S4 −14,6 · S5 −13,4 · S6 −12,9 · S7 −13,0 · S8 −19,5 (Einstein, bilinçli olarak sessiz) · S9 −14,5 · S10 −11,9. Telefonda S2 −3,7 LU ile en çok kaybeden bölüm; diğerleri 0,1–2,4 LU kaybediyor.
- Görüntü: medyan parlaklık 37/255 (kozmik ve karanlık ama kasıtlı); en karanlık an 13/255 (3,6 sn, S1 uzay geçişi). En uzun kıpırtısız an 43 kare (1,4 sn, S9); 2 sn'yi aşan ölü an yok.
- Bilgiler, sources.md'ye karşı kontrol edildi:
  - Hawking 1980: yüzyıl sonuna kadar ~yarı yarıya (Hawking'in kendi 1998 aktarımı: "50-50 chance"). Hawking 2002 "Gödel and the End of Physics": fikrini değiştirdi.
  - Gödel yalnızca "GÖDEL 1931" tahta notu olarak geçiyor; iddia cümlesi yok.
  - Planck 2018: 68,5 + 26,5 ≈ %95.
  - Shannon 1950: 10¹²⁰ oyun, ~10⁸⁰ atom; metinde "oyun sayısı" deniyor.
  - Feynman I-2: özet, tırnak yok.
  - Einstein 1936: birebir çeviri.

## Kalan sorunlar (küçük)
- S9 paneli çocuğun kazağının alt kısmını örtüyor. Yüz ve göz parıltısı açık; validator kapsama uyarısı vermiyor.
- Süre 48 sn, 45 sn'lik ideal aralığın biraz üstünde. Sakin tempo tercihi nedeniyle kısaltılmadı.
- S2'deki birleşme kayması sırasında (~0,4 sn) iki formül üst üste biniyor. Geçici bir an ve ardından tebeşir tozu bulutu geliyor.
- S7 kapağı v1'e göre sakin ama hâlâ yoğun bir doku taşıyor (komşu tahtaların taş noktaları).
- Contact sheet şimdi bitloop sheet çıktısı (10 sütun, 1620×1530); v1 farklı bir düzende ve 1756×1160 idi.

## Dosyalar
- out/evren-anlamak.mp4 (v2 upload, 27,8 MB) · out/evren-anlamak_master.mp4 (43,3 MB) · out/evren-anlamak_v1.mp4 (önceki upload, 27,8 MB)
- out/cover.png (32,4 sn, 1080×1920) · out/contact_sheet.png · out/upload.json
- Engine: scenes_chalk.py (formula_dot / label_font / note_font), scenes_cosmos.py (const_y, rewind_turn, far_ca / far_dots), tests/test_cosmos.py (+1 test)
- Yedekler: /workspace/qc4/bak/ (v1 build_spec.py, spec.json, plan, upload.json, cover, sheet, bitloop kopyası)
