# QC raporu: matematik-edm (v1)

**Konu:** 9 matematik fonksiyonu → 9 EDM ses karakteri → 1 drop (tüm katmanlar birleşir).
**Süre:** 20,0 sn (40 vuruş, 120 BPM, 4/4, 11 sahne, punchy tempo). 1080×1920, 30 fps, sabit kamera. Palet: neon (siyah + neon pembe).
**Teslim:** `out/matematik-edm.mp4` (upload, 11,6 MB) · `out/matematik-edm_master.mp4` (CRF 18, 21,8 MB) · `out/cover.png` · `out/contact_sheet.png` · `out/music_44k1_16bit.wav` · `out/upload.json` (`posted: false`). **Hiçbir yerde paylaşılmadı.**

## Puanlar (v1)
| Kategori | Puan | Gerekçe |
|---|---|---|
| **Görsel** | 9/10 | Neon XY osiloskop, formüller okunur, takip noktası net, parçacık patlamaları beat-sync, drop'ta 9 eğri üst üste. Küçük: S0-S10 metin konumu konu kırpabilir. |
| **Retention** | 8/10 | Kanca 0 sn, rehook ~1/3/5/7/9/11/13/15/17 sn (en uzun 2 sn), twist 9 sn (%45), drop 19 sn, ödül 19-20 sn. 20 sn tam alt sınır. |
| **Ses** | 7/10 | −15 LUFS (hedef −14 ±0,5), TP −5,8 dBFS ✅, LRA 1,0 (çok sıkışık), telefon kaybı ~6 LU (hafif bass-ağır). Her bölümün ses karakteri net. |
| **Bilgi doğruluğu** | 9/10 | Eğri = fonksiyon birebir; ses = fonksiyon karakterinin duyulabilir hâli (120 BPM tempoda). Bu `sources.md`'de açık. |
| **Teslim** | 9/10 | 600 kare = 20,000 sn; 0 decode hatası; bt709; faststart; SSIM 0,977 (min 0,916); 44,1 kHz / 16-bit WAV hazır. |
| **Metadata** | 9/10 | Başlık 49 karakter, 6 hashtag, cover_t 19,4, `posted: false`. |

## Ölçümler (CI, `out/qc_measurements.txt`)
- **Bütünlük:** 600 kare · 20,000 sn · h264 High 1080×1920 yuv420p bt709 · AAC 48 kHz 204 kb/s · **0 decode hatası** · faststart ✓ · 11,6 MB.
- **Görsel:** medyan parlaklık 36,6/255 · **near-black kare yok** · en uzun durağan 0 kare · bölüm hareketi 8,4 → 19,1 → 4,2 → 9,9 → 6,1 → 15,5 → 26,5 → 12,4 → 22,1 → 7,5 → **10,4** (drop zirvesi) · loop dikişi 2,18 vs medyan 11,45.
- **Ses:** **I −15,0 LUFS** (hedef −14 ±0,5) · LRA 1,0 · **TP −5,8 dBFS** (≤ −1 ✓) · telefon sim. −21,2 (kayıp ~6 LU) · bölüm LUFS S0 −17,5 → S10 −16,0.
- **A/V sync:** **en iyi lag 1 kare** (r 0,038) · kesmeler ±33 ms (tolere edilebilir).
- **SSIM (upload vs ara):** ortalama **0,9773** (min 0,9159).
- **Validator:** **0 hata**, uyarılar: süre 20 sn (alt sınır), S0 başlık 4 satır, okuma süreleri, subject coverage, re-hook gap, curiosity gap — hepsi 20 sn/yoğun metin doğası.

## Brief uygulaması
- ✅ 9 fonksiyon, 9 ses karakteri, 1 drop, 20 sn, 1080×1920, 30 fps.
- ✅ Sabit kamera, neon pembe + siyah, formüller okunur, takip noktası, parçacık, etiket (MAT-LAB @hayret.piksel).
- ✅ 44,1 kHz / 16-bit PCM WAV (`out/music_44k1_16bit.wav`).
- ✅ Formüller eksiksiz, fonksiyon karakteri duyulur.
- ⚠️ Emoji (📢/🔥) piksel fontunda yok → kaldırıldı (görsel vurgu üstlendi).
- ⚠️ Loudness −15 LUFS (hedef −14) - biraz sessiz; istenirse `level_db` ile kaldırılabilir.
- ⚠️ Telefon simülasyonda ~6 LU kayıp (bass ağırlığı) - istenirse bass bir oktav yukarı.

## Kalan küçük konular
1. **Cover (19,4 sn)** "HER SES = TEK BİR GRAFİK" yazısı kırpılmış olabilir (rate: 16th). İstersen `cover_t ≈ 19,6` ile tam başlıklı bir kapak.
2. **Metin konumu:** S0/S10 title place konu (osiloskop) üzerine yazıyor; `place: "top"` + `subject` ayarı ile düzeltilebilir.
3. **Loudness:** −15 LUFS yerine −14 istenirse master `limit_ceiling` veya `level_db` ayarı.
4. **Telefon kaybı ~6 LU:** bass biraz ağır; `b808` octave 2 veya `level_db` azaltma.

## Dosyalar
`projects/matematik-edm/{plan_tr.md, sources.md, build_spec.py, render_brief.md, palettes.py, spec.json, spec_proxy.json, retention_map.txt, qc_report.md, out/{cover.png, contact_sheet.png, key_stills.png, qc_measurements.txt, upload.json, music_44k1_16bit.wav}}`
Motor: `bitloop/bitloop/scenes_mathlab.py` (`formula_scope`), `palettes.py`, `tests/test_mathlab.py` (4 test).

**Karar:** Yayına hazır (onay sende). **Paylaşım yapılmadı.**