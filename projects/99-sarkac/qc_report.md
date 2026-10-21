# QC raporu: 99-sarkac (v1)

**Konu:** 9×11 = 99 sarkaç, Kuramoto çiftlenmesiyle kendiliğinden senkronize olur; 17:16 doğal frekanslı tek aykırı dışarıda kalır.
**Süre:** 15,0 sn (30 vuruş, 120 BPM, 4/4), 1080×1920, 30 fps, sabit kamera. `pacing: calm`, marka paleti "Çini Gecesi".
**Teslim:** `out/99-sarkac.mp4` (upload, 8,6 MB) · `out/99-sarkac_master.mp4` (CRF 18) · `out/cover.png` · `out/contact_sheet.png` · `out/upload.json` (`posted: false`). **Hiçbir yerde paylaşılmadı.**

## Puanlar (v1)
| Kategori | Puan | Gerekçe |
|---|---|---|
| **Görsel** | 9/10 | 99 sarkaç temiz; kaos→hizalı sütun geçişi net; türkuaz izler hipnotik; mercan halka vivid; R(t) formülü okunur. Küçük: S1/S5'te metin üst üste binmesi. |
| **Retention** | 8/10 | Kanca 0 sn, yeniden kancalar ~2 sn'de bir, ters köşe 9 sn (%60), drop+logo 12 sn, ödül 13-15 sn. 15 sn tatlı noktanın altında ve metin yoğun (bilerek). |
| **Ses** | 8/10 | −14,2 LUFS, TP −3,8 dBTP, LRA 4,4; tık'lar kaosta poliritmden tek ritme çözülüyor; aykırı yarım ses yukarıda. Telefon kaybı ~6 LU (hafif bass-ağır). Kulakla denetlenemedi (bu ortamda ses yok). |
| **Bilgi doğruluğu** | 9/10 | Kuramoto (1975) + düzen parametresi (Strogatz 2000) + metronom senkronu (Pantaleone 2002) kaynaklı; 17:16 açıkça **sanatsal seçim** olarak işaretli (`sources.md`). |
| **Teslim** | 9/10 | 450 kare = 15,000 sn; 0 decode hatası; bt709; faststart; SSIM 0,976. Loop dikişi 3,64 (medyan 1,85'in ~2 katı; donma→döngü doğası). |
| **Metadata** | 9/10 | Başlık 49 karakter, 6 hashtag, cover_t 13,0, `posted: false`. |

## Ölçümler (CI, `out/qc_measurements.txt`)
- **Bütünlük:** 450 kare · 15,000 sn · h264 High 1080×1920 yuv420p bt709 · AAC 48 kHz 196 kb/s · **0 decode hatası** · faststart ✓ · 8,6 MB.
- **Görsel:** medyan parlaklık 25,9/255 · **near-black kare yok** · en uzun durağan 3 kare (0,10 sn) · bölüm hareketi 1,99→1,81→2,39→2,72→**4,53** (S5'te zirve = ifşa/drop) · loop dikişi 3,64 vs medyan 1,85.
- **Ses:** **I −14,2 LUFS** (hedef −14 ±0,5) · LRA 4,4 · **TP −3,8 dBTP** (≤ −1) · telefon sim. −20,2 (kayıp ~6 LU) · bölüm LUFS S1 −14,7 → S5 −13,3 (yükseliyor).
- **A/V sync:** **en iyi lag 0 kare** (r 0,115) · kesmeler ±1 karede (S2 −100 ms, S3 0, S4 −100 ms, S5 +33 ms).
- **SSIM (upload vs ara):** ortalama **0,9762** (min 0,9243).
- **Validator:** **0 hata**, 9 uyarı (süre + 8 okuma süresi + "çok yoğun") — hepsi 15 sn'lik brief'in doğal sonucu, belgelendi.

## Kürşat'ın brief'i uygulandı mı?
- ✅ 9×11 = 99 sarkaç, kaos → senkron, tek aykırı (17:16), mercan halka 13 sn, R(t) formülü 14 sn, sonda donma, döngü.
- ✅ Sabit kamera, shake yok, gereksiz geçiş yok (yalnız 4 nokta geçiş: cut/dissolve/match/glitch/iris).
- ✅ Renkler markaya çevrildi: `#101018`→Gece `#060814`; beyaz kütleler→Krem; kırmızı halka→Çini Mercanı; izler→Türkuaz.
- ✅ 30 fps, 1080×1920, tam 15,0 sn MP4.
- ⚠️ `👀` emoji piksel fontunda yok → kaldırıldı (o vuruşu iris + mercan halka taşıyor).
- ⚠️ "17'ye karşı 16" = aykırının frekans oranı (grup 16 salınımda o, 17; ~yarım ses) olarak yorumlandı.

## Kalan küçük konular
1. **Cover (13,0 sn)** halkayı göstermiyor (halka tam 13,0'da başlıyor, sınır karesi). İstenirse `cover_t ≈ 13,4` ile halka öne çıkan bir kapak üretilebilir (tek render).
2. **Metin yoğunluğu:** 15 sn'de 9 blok; S1/S5'te kısa süreli üst üste binme. 20 sn'lik ferah sürüm seçenek olarak duruyor.
3. **Telefon kaybı ~6 LU** (hedef <~5): bass/pad biraz ağır; istenirse bass bir oktav yukarı ya da `level_db` ile kısılır.
4. **Loop dikişi 2× medyan:** "donma → döngü" tasarımının doğası; dissolve yumuşatıyor.

## Dosyalar
`projects/99-sarkac/{plan_tr.md, sources.md, build_spec.py, render_brief.md, spec.json, spec_proxy.json, retention_map.txt, qc_report.md, out/{cover.png, contact_sheet.png, key_stills.png, qc_measurements.txt, upload.json}}`
Motor: `bitloop/bitloop/scenes_sync.py` (`pendulum_grid`), pixfont Σ/φ/|, sfx `tick_hi`, `tests/test_sync.py` (6 test).

**Karar:** Yayına hazır (onay sende). **Paylaşım yapılmadı.**
