# QC raporu: gelecek-secim (bağımsız QC)

Tarih: 2026-10-20 (Europe/Istanbul, UTC+3). Hiçbir şey paylaşılmadı.

## Puanlar (1–10)
| Alan | v1 | v2 | Not |
|---|---|---|---|
| Görsel | 7 | 8 | S3 kadrajı, S10 iri piksel, zar dither'ı ve Libet W düzeltildi. S8'in alt üçte biri daha sakin. |
| Retention | 8 | 8 | Kanca güçlü. 19 hook/re-hook var. En uzun statik an 1.75 s (28.75 s'de). S3'teki hareket bilerek azaltıldı (pan kaldırıldı). |
| Ses | 7 | 8 | "Kehanet bozulur" anı artık kulakla da duyuluyor (E5 fısıltı ve ardından gelen C5 kaçış + glitch çatlağı). −14.1 LUFS, TP −2.1 dBFS, LRA 3.0, telefon simülasyonu −17.9 LUFS. Senkron xcorr 0 kare. |
| Bilgi doğruluğu | 7.5 | 9 | Scriven iddiası yumuşatıldı. Açıklamada %59 "ankete yanıt veren, kabul/eğilim" olarak yazıldı. Libet 2012 notu eklendi. |
| Teslim | 8 | 9 | Upload: 22.8 MB, SSIM .974 (v1 .945). Master + upload bt709 etiketli (v1 master etiketsizdi). |
| Metadata | 7 | 8.5 | Açıklama nüanslı, sonda CTA 👇 var. |

## v1 bulguları ve düzeltmeler
1. **S3 pan (yüksek).** Kahraman ilk ~0.7 s kadraj dışındaydı, plaka ~11.8 s'de sağ kenardan taşıyordu ve kahraman alt UI bölgesindeydi (0.84–0.98 H). Düzeltme: `camera zoom [1.0,1.06], pan [[0,18],[-2,22]], inOutSine`. Kahraman artık ilk kareden görünüyor, plaka hep kadrajda.
2. **S10 iri kafa (orta).** inOutCubic, 4.6× zoomda ~0.5 s oyalanıyordu. Ease `outCubic` yapıldı: iri faz ~0.1 s'ye indi, sona sıfır hızla geliniyor ve seam korunuyor (seam farkı 4.96, medyan 3.96).
3. **Zarlarda mavimsi dither (orta).** Krem→Sis karışımı palet dışı kalıyordu. Düzeltme: her yüz düz palet tonunda (Krem / Sis / Gök). Değişiklik `scenes_story.draw_die` içinde.
4. **Libet "W" (orta).** r=7'lik disk W'yi kesiyordu. Disk r=8.8 oldu, r=10 mercan halka eklendi, rozet biraz içeri alındı. Değişiklik `scenes_story.py` içinde.
5. **E6 fısıltı ve C5 kaçış (yüksek, ses).** Stem FFT'de fısıltının tahmini E6, kaçışın C5'inden ~31 dB düşüktü, yani duyulmuyordu. Düzeltme: yalnızca S6'da `fisilti_k` sesi (pulse .25, oct 5, vol .05, kısa zarf, kehanet serisi, lookahead 1). Artık lead'in ~12 dB altında ve aynı registerda: önce E duyuluyor, sonra C. Beat-3 punch'ın `sfx`'i `glitch` oldu: 1.5–8 kHz bandında +10 dB, telefonda duyulur bir çatlak. Proxy spec de bu sesi hariç tutuyor.
6. **S6 altyazısı (bilgi).** "TERSİNİ YAPARSIN!" yerine "*TERSİNİ* YAPABİLİRSİN" kondu. Scriven'in kaçınan argümanı tartışmalı ve kaynak "yapabilir" diyor. Anlam aynı, kesinlik iddiası yok. İstenirse geri alınabilir.
7. **S8 alt üçte bir (düşük).** Horizon `k .55` yapıldı ve ağaç 18 birim yukarı alındı (pan son [0,18]).
8. **Açıklama.** Scriven "gösterdi" yerine "savundu (tartışmalı)" yazıldı. "PhilPapers 2020 anketine yanıt veren filozofların %59'u … kabul ediyor ya da ona yakın duruyor" eklendi. Libet 1983 → 2012 "gürültü" cümlesi ve 👇 eklendi.
9. **bt709 etiketi.** Etiketler `h264_metadata` bsf ile yeniden muxlandı (kayıpsız kopya).

Plaka ve terminal etiketleri (1-dot) okunaklı ("@hayret.piksel", "> W = -200 ms"). Diegetik ve ince olsun diye bilerek değiştirilmedi.

## Kalan konular
- S3: kahramanın alt yarısı hâlâ ~0.80–0.92 H'de, yani alt-sol platform yazısının altında kalıyor. Altyazı kutusu saat kasasının üst kenarına biniyor (kadran açık). Daha fazla kaldırmak saati altyazının altına sokar.
- S3 hareketi v1'in ~yarısı. Tam kare kaydırma kalktı, domino, sarkaç ve ışınlar hareket ediyor.
- S8: alt bölgede yürüyen figürler kalabalık (UI bölgesi).
- 26.75 s'deki drop öncesi "nefes" yalnızca ~4 dB düşüyor (mosaic sfx dolduruyor). Drop yine de iniyor.
- "SEÇEN YİNE SENSİN" ve "BİLMEK, SEÇMEYİ SİLMEZ" uyumcu bir duruş. Ekranda iki kamp da veriliyor, kabul edilebilir.
- Cover değişmedi (aynı kare, etkilenmiyor).

## Doğrulama
`validate` OK (0 hata/uyarı). Testler 14/14 + 12/12 geçti. Siyah kare yok (min lum 21.8). Senkron xcorr 0 kare.

## Dosyalar
- out/gelecek-secim.mp4: upload, 2-pass 4.4 Mbps, 22.8 MB, SSIM .974 (CRF-4'e göre)
- out/gelecek-secim_master.mp4: 46.3 MB, SSIM .994
- out/gelecek-secim_v1.mp4: önceki upload
- out/contact_sheet.png (yenilendi), out/upload.json (açıklama güncellendi), out/cover.png
- Yedekler: /workspace/qc2/bak/
- Değişen kod: build_spec.py, bitloop/bitloop/scenes_story.py (draw_die, Libet W)

## Karar
Yayına hazır (onay sende). Paylaşım yapılmadı.
