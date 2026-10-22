# Render brief: sesin-kumda-desenleri

Yeni sahne + test yazıldı; CI'da doğrulanacak.

## 1. Yeni sahne: `chladni` (yazıldı: `bitloop/scenes_chladni.py`)
- `SCENES`'e kayıtlı; `own_layers = 3`.
- Parametreler: `n,m` (plaka modu), `x/y/w/h` (plaka), `particles`, `settle_s` (kumun çizgiye oturma süresi), `jitter`,
  `label` ("mod n,m"), `label_y`, `driver`, `driver_y`.
- Düğüm çizgileri: `u=(2k+1)/(2n)`, `v=(2l+1)/(2m)` (ideal basit-mesnetli kare plaka). Kum her karede en yakın çizgiye
  `settle` oranında çekilir; pozisyon `t`'nin **saf fonksiyonu** (deterministik, paralel worker'da güvenli).
- `DEFAULT_STACK["chladni"] = (["horizon","nebula"], ["dust"])`.
- **Dikkat:** ilk karelerde kum dağınık (hook), 1 sn içinde çizgilere oturur. `label_y=-80` (üst), sürücü `y=78`
  (plaka altı), etiket plakası `y=88` (güvenli bölge üstü, `y<102,4`).

## 2. Test
- `bitloop/tests/test_chladni.py` (3 test): kayıt/validasyon, düğüm çizgisi doğruluğu (`_nodes`), kare deterministik +
  kumun zamanla oturması.

## 3. Doğrulama
- `cd bitloop && for t in tests/test_*.py; do python "$t" || exit 1; done` — yeni `test_chladni` + eski 87.
- `bitloop validate spec_proxy.json` → **0 hata** (`series_tree` proxy).
- `bitloop validate spec.json` → `chladni` kayıtlı olduğu için **0 hata** olmalı.
- `bitloop sheet`/`key_stills` ile kumun çizgilere oturduğunu, etiketin okunur olduğunu gözle; `bitloop music` dinle.

## 4. Bilinen incelikler
- **Frekans ↔ mod:** gerçek plaka modları ideal `cos·cos` değil; görsel idealize model (kalitatif doğru). Ses tarafında
  mod sırası yükseldikçe tiz yükseliyor; birebir f(n,m) eşlemesi değil — `sources.md`'de açık.
- Kum partikül sayısı 1600; performans için vektörel (`cv.points` tek çağrı).
- `label` metni "mod n,m" — fontta küçük harf + rakam + virgül var; `snap=True` ile keskin.
