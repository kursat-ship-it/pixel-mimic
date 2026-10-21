# Render brief: matematik-edm

Render'cı bu dosyayı okur. Bu turda **motor işi** zaten büyük ölçüde yazıldı; aşağıdakiler eksik/doğrulanacak.

## 1. Yeni sahne: `formula_scope` (yazıldı: `bitloop/scenes_mathlab.py`)
- `SCENES`'e kayıtlı (`scenes_mathlab` → `scenes.py` import); `own_layers = 3`.
- 9 formül `FORMULA` sözlüğünde; eğri her karede **sahne-yerel t** ile birebir hesaplanır.
- Parametreler: `formula` (hardtekk|phonk808|acid|funk|phonkmel|jersey|trance|psy|build|all), `formula_text`, `window`, `gain`, `x/y/w/h`, `particles`, `formula_y`, `formula_dot`.
- `formula="all"`: dokuz eğriyi aynı anda çizer (drop).
- Siyah takip noktası (mercan halesi) en yeni örnekte; her vuruşta radyal parçacık.
- `DEFAULT_STACK["formula_scope"] = (["grid","nebula"], ["dust"])` eklendi.
- **Eksik/iyileştirilecek:** giriş sahnesinde (S0) düzlemin neon çizgiyle "açılması" (fade-in) — şu an normal çiziyor; istenirse `lt<0.15` için alfa rampası.

## 2. Palet (yazıldı: `projects/matematik-edm/palettes.py`)
- `neon`: siyah `#0A0A0A` → neon pembe `#FF00FF`; marka caption `#04060E`/`#F4ECDC` sabit; camgöbeği `#00FFFF` seyrek aksan.
- `spec.palette` = dict (engine `Palette` dict destekliyor).

## 3. 44,1 kHz / 16-bit PCM (teslim ayrıntısı)
- Motor 48 kHz sentezler (global `SR`). **Global SR'yi değiştirme** (eski reylerin sesi bozulur).
- CI'da ek adım: `bitloop music spec.json -o /tmp/music.wav` → `ffmpeg -i /tmp/music.wav -ar 44100 -sample_fmt s16 out/music_44k1_16bit.wav`. MP4'ün AAC sesi de 44,1 kHz'e indirilir.
- (İsteğe bağlı, daha temiz: `music.audio_sr` (varsayılan 48000) parametresi ekleyip `render`'ın `-ar`'ını ondan beslemek. Eski davranış korunur; test eklenir.)

## 4. Doğrulama
- `cd bitloop && for t in tests/test_*.py; do python "$t" || exit 1; done` — yeni `test_mathlab.py` (6 test) + eski 79.
- `bitloop validate spec_proxy.json` → **0 hata** (noise_scope proxy).
- `bitloop validate spec.json` → sahne kayıtlı olduğu için **0 hata** olmalı.
- `bitloop sheet` / `strip` ile formüllerin alt bölümde okunur olduğunu gözle; `bitloop music` dinle.

## 5. Dikkat
- Formül metni 1 dot ≈ 6 ekran px; satır başına ≤ ~24 karakter (2 satıra bölündü). Taşarsa `formula_dot` düşür veya satır böl.
- Alt güvenli alan: `formula_y = 92` (y<102,4) — plaka `y=88`. İkisi de güvenli bölgenin üstünde.
- Emoji yok; ses-görsel senkronu global vuruş saatinde.
- Bölüm geçişlerinde ani tık olmasın: `level_db` crossfade (zaten motor yapıyor).
