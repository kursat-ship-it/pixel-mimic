# Kaynaklar: matematik-edm
Erişim tarihi: 2026-10-22. Bu parça **bilimsel iddia** değil, matematik + ses sentezi; "kaynak" = formüllerin ve sentez tekniklerinin tanımı.

## Web Audio API (brief'in referansı)
- W3C. *Web Audio API* (Working Draft). https://www.w3.org/TR/webaudio/
  - "Prosedürel ses": osilatörler + kazanç zarfları + filtrelerle gerçek zamanlı ses. Biz tarayıcı yerine repo'nun
    `bitloop/voices.py` (numpy) sentezleyicisini kullanıyoruz; fikir aynı (dalga biçimi → ses).

## Sentez teknikleri (formüllerin ses karşılığı)
- Puckette, M. (2007). *The Theory and Technique of Electronic Music*. World Scientific.
  - Sinüs osilatör, üstel zarf (`exp(−t/τ)`), kare dalga (`sign(sin)`), ring/FM modülasyonu, `tanh` yumuşak kırpma.
- `tanh(10·sin(...))`: yumuşak doyum (soft-clip) — 808/phonk distorsiyonunun matematiksel karşılığı; sert kırpma yerine
  harmonik üretir, tık/clip yapmaz. (DSP'de "waveshaping" olarak standart.)
- `sign(sin(2πft))`: kare dalga (acid/TB-303 karakteri); `mod(t, T)`: periyodik kapı (hardtekk/jersey ritmi).
- `2^mod(2t,1)`: oktav basamağı (trance arpej); `(100+50t)` frekans taraması + `(t/3)` genlik artışı (build-up).

## Dürüstlük notları (QC için)
- **Eğri birebir formülden** çizilir (her karede, sahne yerel zamanı). **Ses** aynı frekans/sönüm karakterini kullanır ama
  müzikal tempoda (120 BPM) çalar: 4–8 Hz'lik kapılar perde olarak duyulmaz, 39/65 Hz gerçek sub-bass'tır. Bu bilinçli bir
  "duyulabilir hâl" çevirisidir, formülden sapma değil.
- **44,1 kHz / 16-bit PCM**: motor 48 kHz sentezler; teslim WAV'ı 44,1 kHz/16-bit'e indirilir. MP4 sesi AAC'tir (PCM MP4'e
  standart değil) ve 44,1 kHz'e ayarlanır.
- Emoji (📢/🔥) piksel fontunda yok; kaldırıldı, görsel vurgu üstlendi.
- Renk paleti **konuya özel "neon"**: siyah `#0A0A0A` + neon pembe `#FF00FF` + marka `#04060E`/`#F4ECDC` (marka katmanı sabit).
