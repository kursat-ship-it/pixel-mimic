# QC raporu: canli-gozu (bağımsız QC)

Tarih: 2026-10-21, 01:36–02:00 (Europe/Istanbul, UTC+3). Hiçbir şey paylaşılmadı.

## Puanlar (1–10)
| Alan | v1 | v2 | Not |
|---|---|---|---|
| Görsel | 7.5 | 8.5 | Paletler güzel ve tutarlı. Mozaikte artık hiçbir çiçek metnin altında kalmıyor, yılan karosu canlı, kovan etiketi düz krem. |
| Retention | 7.5 | 8 | Sakin tempo korunuyor (ortalama görsel değişim 0.91 s). S3'teki "kaybolur" artık gösteriliyor. |
| Ses | 7 | 7.5 | Dinamik bir yay eklendi (LRA 1.8 → 2.3). Nagel artık droptan 2.8 LU sessiz (v1'de neredeyse aynıydı). Senkron 0 kare. |
| Bilgi doğruluğu | 8.5 | 9 | Mantis nüansı açıklamaya eklendi. Arı/kırmızı efsanesi yok. Bütün paletlerin "çeviri" olduğu söyleniyor. |
| Teslim | 8.5 | 9 | Upload 27.6 MB, SSIM .980. Master da artık bt709 etiketli. |
| Metadata | 8 | 8.5 | Thoen ölçüsü eklendi, #hayretpiksel eklendi. |

## Kullanıcı geri bildirimi uygulanmış mı?
- **Anlatıcı cümleleri:** Evet. 9 tam cümle bloğu var. Kelimeler vuruşta beliriyor (16'lık, callout 8'lik), Nagel diyalog kutusunda.
- **Okuma süresi:** Validator OK. Ölçtüğüm "tam görünür" süreler 2.9–4.5 s. S2, S3, S6 ve S8 formülün sınırında (0.6 + 0.35 s/kelime), yani yeterli ama cömert değil.
- **Yerleşimler:** v1'de 6 blok `top`'taydı. v2'de 5 top, 2 mid (S4, S7), 1 panel, 1 dialog ve 1 callout var. S8'deki blok iki karo sırasının arasındaki çizgiye ortalandı.
- **Sakin tempo:** Evet. 7 sakin geçiş + 2 hızlı geçiş (glitch = ters köşe, mosaic = drop). Önceki reel'de görsel değişim 0.28 s'de bir oluyordu, burada 0.91 s'de bir.

## Bilim ve palet kontrolü
- **Arı:** UV-fotoğraf konvansiyonunda yanlış renk. Boğa gözü görünüyor. Kırmızı top koyu ve az kontrastlı ama görünür, yani "arılar kırmızıyı göremez" efsanesi yok.
- **Köpek:** Machado döteranopi matrisi + 2×2 iri piksel (düşük keskinlik). Top çimle aynı zeytin rengine dönüyor.
- **Yılan:** Isı haritası + bulanıklık. Metinde "görür" değil "ısıyı algılar" deniyor.
- **Yarasa:** Sonar halkaları B tıklarıyla 0 kare senkron. "Sesle görür" bir metafor, kaynaklarda not edilmiş.
- **Mantis:** 12 bant (abartılı hali) → 5 düz sınıf (Thoen 2014). "kötü ayırt ediyor" bir sadeleştirme. Açıklama artık "birbirine yakın renkleri, 12–25 nm" diyor. Ekrandaki yazıya "yakın" kelimesi sığmadı: head boyutunda 4 satır oluyor ve okuma süresi validator'dan geçmiyor.
- **Okunabilirlik:** Metin kutusu marka renklerinde, her modda aynı. Bütün paletlerde okunuyor.

## v1 bulguları ve düzeltmeler
1. **Mozaik metni çiçekleri örtüyordu (yüksek).** "Altı göz…" kutusu insan ve arı karolarının çiçeğini kapatıyordu; boğa gözü görünmüyordu. Karo kırpması `[-44,-36,46,69]` yapıldı (çiçek karonun ortasına indi). Metin `xy [0.5, 0.335]` ile 1. ve 2. sıra arasına ortalandı. Altı çiçeğin hepsi görünüyor; kapak karesi de buna göre düzeldi.
2. **Yılan karosu donuktu (orta).** Engine'e (`VisionMosaic`) iki şey eklendi: ısı karosuna otomatik kazanç (termal kameraların AGC'si; temp yüzdelik 3–99.7 aralığına geriliyor) ve karoya özel blur (1.2). Kovan ve çiçek artık sıcak/soğuk olarak okunuyor.
3. **S9 kovan etiketi (orta).** Vinyet krem boyayı %78'e indiriyordu ve sağ yarı krem/Sis damalıydı. Engine'e (`render._matte_glow` + `Canvas.keep`) şunlar eklendi: okunur etiketlerin altındaki glow temizleniyor ve bu pikseller vinyetten muaf. Etiket artık düz krem. Okunur ölçüde: 6 px/dot.
4. **S3'te "kaybolur" gösterilmiyordu (orta).** Plan, insan/köpek karşılaştırmasını istiyordu. 5. vuruşta 1.25 vuruşluk "insan gözü" peek'i eklendi (mevcut özellik): kırmızı top bir anlığına ortaya çıkıyor, sonra yine kayboluyor.
5. **Düz miks (orta).** Bölüm seviyeleri −15…−12.5 LUFS arasındaydı; drop ile Nagel neredeyse eşitti.
   - Engine'e `sections[].level_db` eklendi (SFX öncesi, ±40 ms crossfade).
   - Değerler: köpek −1, yılan −1.5, yarasa −1, mantis12 −1.5, mantis_kaba −2.5, drop +1.5, Nagel −4, döngü −1.
   - Bas .065 → .056.
   - Sonuç: LRA 2.3. S7 −14.6 → S8 −13.7 → S9 −16.5 LUFS. Döngü dikişi pürüzsüz.
6. **S4 yerleşimi.** `auto` (top oldu) yerine `mid`: ısı haritasının boş ortası.
7. **Açıklama:** Mantis nüansı ("12–25 nm'lik farkı seçemiyor, biz birkaç nanometrelik farkı seçebiliyoruz") eklendi. sources.md'ye not düşüldü. #hayretpiksel eklendi.
8. **Master etiketi:** Master bt709 etiketsizdi, kayıpsız remux ile düzeltildi.
9. **Engine seçeneği:** `music.limit_ceiling` eklendi (varsayılan .6, davranış aynı). Denedim ama bu reel'de kullanmadım: AAC true-peak döngüsü tavanı daha da düşürdü.

## Kalan konular
- **Sıkışıklık:** LRA 2.3 hâlâ düşük. Asıl sınır, limiter'ın −4.4 dBFS tavanı (AAC güvenliği için); bu yüzden drop'u daha fazla yükseltmek mümkün olmadı. Chiptune için kabul edilebilir.
- **Telefon dengesi:** Telefon simülasyonu −18.9 LUFS (−4.6 LU). Kabul edilebilir; S3, S4 ve S7 alçak frekansa yaslı.
- **CRT anı:** 21.0–21.2 s'de ortalama parlaklık 11/255 (~%4) ve ~6 kare sürüyor. Siyah değil (floor .6 after-image), "ışık söner" anı olarak bilinçli. Dokunmadım.
- **S4 sakinliği:** 18–19 s arası neredeyse statik (fare koklaması + titreşim). Sakin tempo isteğine uyuyor ama en zayıf yer burası.
- **Süre 48.9 s:** Sürünen bölüm yok. En yavaşları S4 ve S9, ikisi de okuma süresi için gerekli. Planın kendi B seçeneği olarak yılan çıkarılırsa ~43 s olur; bu yapısal bir karar, sana bırakıyorum.
- **S6 mantis12:** Bilerek "aşırı" görünüyor. Dither şeritleri yoğun ama tasarım gereği.
- **"Altı göz":** Yılan çukuru ve yarasa sonarı göz değil, şiirsel bir ifade. S8 "çeviri" ve açıklama bunu dengeliyor.

## Doğrulama
- `validate` OK. Tek uyarı süreyle ilgili, bilinçli.
- Testler: 14 + 12 + 10 + 10 + 10 = 56/56 geçti (v1'de 55'ti; test_vision'a QC testi eklendi).
- Siyah kare yok (min lum 11.3/255, CRT). Dikiş farkı 2.3. Senkron xcorr 0 kare.

## Dosyalar
- out/canli-gozu.mp4: upload, 2-pass 4.4 Mbps, 27.6 MB, SSIM .980 (CRF-4'e göre), −14.3 LUFS, TP −2.5 dBFS
- out/canli-gozu_master.mp4: 53.7 MB, SSIM .996
- out/canli-gozu_v1.mp4: önceki upload, 27.6 MB
- out/cover.png: CRF-4 ara dosyadan alınan 37.5 s mozaik karesi. Not: `--package` meta.cover_t'yi dikkate almıyor, kapağı ilk kareden (kancadan) yazdı; elle değiştirdim. Engine'de ayrıca bakılması gereken bir konu.
- out/contact_sheet.png, out/upload.json
- CRF-4 ara dosya: /tmp/cg_crf4.mp4
- Yedekler: /workspace/qc3/bak/
- Değişen kod:
  - build_spec.py, sources.md
  - bitloop/bitloop/scenes_vision.py, render.py, raster.py, music.py
  - tests/test_vision.py

## Karar
Yayına hazır (onay sende). Paylaşım yapılmadı.
