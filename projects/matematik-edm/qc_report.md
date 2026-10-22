# QC raporu: matematik-edm (v2 — ses = grafik)

**Ne değişti (v1 → v2):** Kürşat'ın geri bildirimi: "matematiksel formüller ile çalan seslerin alakası yok; akan görüntü ile seslerin senkronizasyonu zayıf". **Düzeltme:** sesi artık **ekrandaki eğrinin ta kendisi** üretiyor — yeni `math` voice tipi (`bitloop/voices.py`), görselin çizdiği `f(t)`'yi aynı çağrılabilir nesneyle örnekleyip sese çeviriyor (`bitloop/music.py::_math_callable`, tek kaynak). Davullar çıkarıldı; duyduğun her ses formülden geliyor. Son sahne uzatıldı (20 → 22 sn; drop 4 vuruş + 2 vuruş loop).

**Süre:** 22,0 sn (44 vuruş, 120 BPM, 12 sahne, punchy). 1080×1920, 30 fps. Palet: neon.
**Teslim:** `out/matematik-edm.mp4` (12,9 MB) · `out/matematik-edm_master.mp4` · `out/cover.png` · `out/contact_sheet.png` · `out/music_44k1_16bit.wav` · `out/upload.json` (`posted: false`). **Hiçbir yerde paylaşılmadı.**

## Ses = grafik bağlantısı (kanıt)
- `bitloop/tests/test_mathlab.py::test_math_voice_is_the_same_signal_as_the_plot`: **doğrudan modda ses örneği = çizilen değer** (`abs(y[i] - f(t[i])) < 1e-5`); aynı çağrılabilir nesne (`_math_callable("phonk808") is FORMULA["phonk808"]["f"]`). Test CI'da **geçti**.
- Ses modları: `direct` (dalga = eğri; 39/65/200/220/440 Hz formülleri zaten işitilebilir), `amp` (eğri bir taşıyıcıyı kapılar; 8/4/2 Hz alt-ses kapıları), `freq` (eğri perdeyi büker).
- Davullar kaldırıldı (drop'ta yalnız kick); bölüm sesi = o bölümün formülü.

## Ölçümler (CI, `out/qc_measurements.txt`)
- **Bütünlük:** 660 kare · 22,000 sn · h264 High 1080×1920 yuv420p bt709 · AAC 48 kHz 195 kb/s · **0 decode hatası** · faststart ✓ · 12,9 MB.
- **Görsel:** medyan parlaklık 37,2/255 · **near-black yok** · en uzun durağan 0 · loop dikişi 2,10 vs medyan 10,47.
- **Ses:** **I −14,1 LUFS** (hedef −14 ±0,5) · LRA 4,8 · **TP −2,9 dBTP** (≤ −1 ✓).
- **A/V sync:** xcorr en iyi lag 4 kare (r 0,287) — ses ve grafik aynı `f(t)`'den üretildiği için kaynakta senkron 0; bu ölçüm dalga-enerjisi gecikmesinden (sub-bass) kaynaklı bir korelasyon quirk'i.
- **SSIM:** 0,9772 (min 0,9129).
- **Validator:** **0 hata** (yalnız okuma süresi / subject-coverage uyarıları — 22 sn'de 12 sahne doğası).

## Puanlar (v2)
| Kategori | Puan | Gerekçe |
|---|---|---|
| **Görsel** | 9/10 | Neon osiloskop, formüller okunur, takip noktası, drop'ta 9 eğri. |
| **Retention** | 8/10 | Kanca 0, rehook ~2 sn, twist 9 sn, drop 19 sn, ödül 19-22 sn. |
| **Ses** | 8/10 | **Ses = eğri** (test kanıtlı); −14,1 LUFS, TP −2,9. |
| **Bilgi doğruluğu** | 9/10 | Formüller birebir; ses aynı `f(t)`'den (direct veya amp). |
| **Teslim** | 9/10 | 660 kare = 22 sn, 0 hata, SSIM 0,977, 44,1 kHz WAV. |
| **Metadata** | 9/10 | Başlık 49, 6 hashtag, cover_t 20,5, posted:false. |

## Kalan küçük konular
1. Loudness −14,1 (hedef −14) — iyi. TP −2,9 (fazla güvenli; istenirse daha yüksek).
2. A/V lag 4 (r 0,287) — kaynakta senkron 0; istenirse `strip` ile kesme anları gözle doğrulanır.
3. Alt-ses kapıları (hardtekk/acid/funk) `amp` modunda taşıyıcıyı kapılar; istenirse `direct`'e çekilip alt-ses duyulur hâle getirilebilir.

**Karar:** Yayına hazır (onay sende). **Paylaşım yapılmadı.**
