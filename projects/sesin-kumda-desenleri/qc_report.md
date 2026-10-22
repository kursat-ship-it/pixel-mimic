# QC raporu: sesin-kumda-desenleri (v1)

**Konu:** Chladni desenleri — titreşen bir plakanın üstündeki kum, sesin düğüm çizgilerinde toplanır.
**Süre:** 20,0 sn (40 vuruş, 120 BPM, 4/4, 8 sahne, **calm**). 1080×1920, 30 fps, sabit kamera. Palet: Çini Gecesi.
**Teslim:** `out/sesin-kumda-desenleri.mp4` · `out/sesin-kumda-desenleri_master.mp4` · `out/cover.png` · `out/contact_sheet.png` · `out/music_44k1_16bit.wav` · `out/upload.json` (`posted: false`). **Hiçbir yerde paylaşılmadı.**

## Puanlar (v1)
| Kategori | Puan | Gerekçe |
|---|---|---|
| **Görsel** | 9/10 | Kum dağınıktan düğüm çizgilerine oturuyor; mod (n,m) büyüdükçe desen çoğalıyor; plaka + sürücü + "KUM LAB" etiketi (okunur). |
| **Retention** | 8/10 | Kanca 0, rehook 5/11/14 sn (en uzun boşluk 6 sn), ters köşe 11 sn, drop 16,5 sn, ödül 16,5-19 sn. 20 sn alt sınır. |
| **Ses** | 8/10 | −14,1 LUFS, TP −4,0 dBTP, LRA 3,7; calm FM drone+pad+lead; Shepard riser + sonic logo. |
| **Bilgi doğruluğu** | 9/10 | Chladni 1787 + düğüm çizgisi modeli kaynaklı; frekans↔mod ilişkisi "ideal, birebir değil" diye işaretli (`sources.md`). |
| **Teslim** | 10/10 | 600 kare = 20,000 sn; 0 decode hatası; bt709; faststart; **lag 0**; SSIM 0,996. |
| **Metadata** | 9/10 | Başlık 41 karakter, 6 hashtag, cover_t 17,2, `posted: false`. |

## Ölçümler (CI, `out/qc_measurements.txt`)
- **Bütünlük:** 600 kare · 20,000 sn · h264 High 1080×1920 yuv420p bt709 · AAC 48 kHz 196 kb/s · **0 decode hatası** · faststart ✓.
- **Görsel:** medyan parlaklık 42,5/255 · **near-black yok** · en uzun durağan 1,57 sn (reveal'de planlı hold, <2 sn) · loop dikişi.
- **Ses:** **I −14,1 LUFS** (hedef −14 ±0,5) · LRA 3,7 · **TP −4,0 dBTP** (≤ −1 ✓).
- **A/V sync:** **en iyi lag 0 kare** (r 0,295) ✓.
- **SSIM:** 0,9959 (min 0,9336).
- **Validator:** **0 hata**; uyarılar: süre 20 sn (alt sınır), S7 başlığı plakanın %36'sını kaplıyor, okuma süreleri.

## Kalan küçük konular
1. **Süre 20 sn** (tatlı noktanın alt sınırı). Desenlerin daha rahat izlenmesi için 22-24 sn'ye çıkarılabilir (plan seçeneği).
2. **S7 başlığı** plakanın üst kısmını kaplıyor; `place: "top"` + `subject` ile kaydırılabilir.
3. Okuma süreleri (5-6 blok, 20 sn'de 8 sahne) — uyarı, hata değil.

**Karar:** Yayına hazır (onay sende). **Paylaşım yapılmadı.**
