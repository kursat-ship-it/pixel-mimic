# Render brief: 99-sarkac

Render'cı bu dosyayı okur, `build_spec.py`'nin TARGET spec'indeki (`pendulum_grid`) yeni sahneyi ve iki küçük motor
eklentisini yazar. Kurallar: yeni parametreler **eski davranışa varsayılan** (eski spec'ler bayt-aynı render eder),
her şey `t`'nin saf fonksiyonu, palet-dışı karışım yok, metin piksel-ızgara oturur, güvenli alanlara girilmez, test eklenir.

## 1. Yeni sahne: `pendulum_grid` (esas iş)
`bitloop/scenes_music.py`'ye (veya yeni bir modüle) `pendulum_grid` sahnesini ekle ve `SCENES`'e kaydet.
9 sütun × 11 satır = **99 sarkaç**, üstten asılı, aşağı sallanır. Sabit tepe-üstü görünüm, kamera 1:1.

### Parametreler (hepsi isteğe bağlı, varsayılan davranış = kare 0'da zaten senkron görüntü değil, kaotik; dikkatli ol)
| Param | Tip / varsayılan | Anlam |
|---|---|---|
| `rows`, `cols` | 11, 9 | grid boyutu |
| `phase` | "chaos" | `chaos` → `emerge` → `waves` → `converge` → `lock` (segment'ten gelir, sürekli değil ama global vuruş saatiyle aynı faz evrimi) |
| `outlier` | {"i": 16, "freq_ratio": 17/16} | aykırı sarkaç (indeks) ve doğal frekans oranı |
| `outlier_ring` | {"at": 26, "beats": 1} | kırmızı halka aykırıya kilitlenir + vuruşla nabız |
| `formula` | {"text": "R(t) = |Σ e^{iφ_j}| / 99", "at": 28, "dot": 2} | alt bölümde zarif formül |
| `freeze` | {"at": 29, "beats": 1} | son kompozisyon 1 vuruş donar (döngü dikişine hazırlık) |
| `trails`, `bloom`, `tick_beats` | True, 0.6, otomatik | izler + bloom + tık yoğunluğu |

### Fizik (Kuramoto, deterministic, seeded)
- Her sarkaç j: faz φ_j(t). Doğal frekans ω (grup = 1), aykırı ω* = 17/16.
- Çiftlenme: φ_j' = ω_j + (K/N) Σ_k sin(φ_k − φ_j). K, `phase`'e göre 0'dan kritik üstüne yükselir:
  chaos→K küçük (R≈0) · emerge→K artar · waves→R yükselir (üç dalga deseni görünür) · converge→R→1 · lock→R≈1 (aykırı hariç).
- **Global vuruş saati**: φ_j(t) yalnızca t'ye bağlı; segmentler arası kesintisiz (aynı dünya). `phase` yalnızca K profilini seçer.
- Döngü: tam sayı salınım sayısı film başına; `freeze`'den sonra `loop_transition` (dissolve) frame 0'a (kaos) sarar. Son kare == frame 0 hâli.

### Görsel (palet-dışı yok; marka renkleri)
- Zemin: Gece `#060814` → Derin Lacivert `#0B1230` (back layer `stars`/`nebula` zaten var).
- İpler: Sis `#B8CDF2` (ince, 1 px). Kütleler: Krem `#F4ECDC` + Parıltı `#D2FFF5` parlama noktası.
- İzler (trail): Türkuaz Işık `#41E8D2`, Bayer dither, `glow` buffer (kütlelerin altındaki okunur etiketleri glow'dan muaf tut — `Canvas.matte`).
- Kırmızı halka: Çini Mercanı `#EC4A57` + Mercan Işık `#FF9A86`; `flash`/`pulse` olayıyla vuruşa kilitli nabız.
- Formül: alt bölümde, okunur (dot≥5 ekran pikseli), `formula_bitmap` benzeri; **Σ ve φ glifi gerekli** (bkz. §3).
- `own_layers` sınıf niteliği = en az 2 (izler + glow/halka), böylece katman kuralı (≥3) back 2 + front 1 + own ≥ 3 sağlanır.

### Ses (SFX: sahnenin `sfx(dur)` metodu)
- `sfx(dur)` → `[(beat, "tick"), ...]`: her sarkacın tepe noktası bir "tick" üretir (99 gerçek akış değil, **işitilebilir indirgeme**):
  chaos'ta rastgele dağılmış (poliritm), lock'ta ızgaraya kilitli. Aykırının tepeleri → `"tick_hi"` (yarım ses yukarı, vuruş dışı).
- beat'ler segmente göre (negatif = sondan). `timeline_events` bunları SFX'e besler; `tick` zaten var, `tick_hi` §2'de eklenir.

## 2. Yeni SFX: `tick_hi`
`sfx.py`'ye `tick_hi` ekle = `tick` ile aynı 35 ms vurmalı tık, ancak `root + 61` (17:16 ≈ bir yarım ses yukarı) ve pan karşıda.
Eski davranışa dokunma (yeni kind). Test: `tick_hi` çıktısı `tick` ile aynı süre/zarfta ama daha yüksek perde.

## 3. Yeni glifler: `Σ` ve `φ` (pixfont)
`pixfont.py`'nin `_L` (küçük/orta metrikler) bölümüne **Σ** (toplam) ve **φ** (phi) ekle — 5×7, mevcut Yunanca (μ ν π ψ ∂ ħ ρ λ Λ) ile aynı stil.
Formül, `formula_bitmap`'in düz ayrıştırıcısına güvenmek yerine sahne tarafından elle dizilir: büyük Σ + "e" üst simgesi "iφ_j"
(alt simge j). Test: `pixfont.missing("Σφ")` boş döner; bir still/calm frame'de formül okunur (5 px/dot üstü).

## 4. Doğrulama zinciri (hepsi geçmeli)
- `cd bitloop && for t in tests/test_*.py; do python "$t" || exit 1; done` (eski 73 + yeni testler).
- `bitloop validate spec_proxy.json` → **0 hata** (warnings: süre + okuma süresi bilerek).
- `bitloop validate spec.json` → yalnızca beklenen `unknown scene 'pendulum_grid'` hataları (sahne yazılmadan önce).
- Sahne yazıldıktan sonra `bitloop validate spec.json` → 0 hata.
- `bitloop sheet` / `strip` (kanca + kırmızı halka + formül anları) gözle bak; `bitloop music` dinle.

## 5. Dikkat
- **Sabit kamera, shake yok** (brief). `fx.shake` artırma; drop'ta `pulse`/`flash` (ışık) yeter.
- **Palet-dışı karışım yok**; izler Bayer dither. Kütleler ve halka küçük nesneler → düz palet tonu.
- Metin (anlatım) sonradan, marka renginde, tam çözünürlükte eklenir; sahnenin formülü dünya-içi metindir (dot kontrolü).
