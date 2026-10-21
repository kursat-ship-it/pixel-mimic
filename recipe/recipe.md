# RECIPE v2: @hayret.piksel pixel-science reels

> **v2:** every video gets its **own music and edit**, designed for its topic. There is no fixed template any more.
> - **Constant (brand layer):** Çini Gecesi palette, hayret eye mark, diegetic tag rules, caption style, 30 fps, ≥3 layers, and the 4-note sonic logo motif (transposed per video).
> - **Variable (per spec):** music (tempo/meter/key/scale/makam/voices/drums/motif/sections) and structure (any segment list).
> - **Authoring guide (Turkish) + retention playbook:** §12. **Spec schema:** `recipe.json` → `spec_schema`. **Archetypes:** §12.4.
> - §0–§9 below are the **reference breakdown**, kept as one example (`bitloop init <dir> --archetype reference` / `scale_journey`).

---

# Reference example: "Pixel Science Loop" (cloned from Bit Wonder · "One Neuron of 86 Billion 🎧")

Reference: https://youtube.com/shorts/LXcZhstWlXM · @bitwonder · 48.0 s · 1080×1920 · 60 fps · music-only · uploaded 2026-10-17
Analysis: `ref/analysis/` (heavy files such as source.mp4/audio.wav/strips not committed) (report.json, fingerprint.json/png, STYLE.md, peaks.json, route.json, strips) ·
Contact sheet: `ref/contact_sheet.jpg` · per-beat keyframes `ref/keyframes/` (not committed; regenerate from the reference).
Machine-readable template: `recipe.json` (same field names as ReelMimic `plan.json`, with `{{slots}}`).
Style registry file (ReelMimic `_TEMPLATE.md` schema): `pixel-science-loop.md` → copy to `.claude/skills/video-clone/styles/` to register.

---

## 0. Route (ReelMimic step 2)
- **medium:** `2d-pixel` · **style:** `pixel-story` (closest installed) → proposed new style `pixel-science-loop` · **engine:** `pixel-art`
- Why: measured 6-px art grid + Bayer dithering + limited violet/amber palette. Not live-action, not AI footage.
- Engine gaps to close before rendering: vertical canvas (engine is hard-coded 1920×1080 / 480×270), top black-box captions
  instead of RPG `say()` box, smooth zoom by redrawing geometry (engine forbids bitmap scaling), no characters needed.
- Alternative: `motion-graphics` (HyperFrames) + pixelate/dither post filter — easier camera, weaker pixel authenticity.

## 1. The formula (topic-agnostic)
> **Follow ONE tiny thing through a chain of steps across scales → the chain closes and the camera explodes out to the
> whole system → reveal it is "one of N" → collapse the system into one everyday object with a number → push back
> into the first frame (seamless loop).**

Topic must provide: a small protagonist object (a neuron, a photon, a water drop, a bit, a seed…), 5 causal steps,
one "system" view, one big number, one everyday metaphor object + a number on it.

## 2. Locked timing (BPM-relative; reference 117.45 BPM, 1 beat = 0.511 s, total ≈ 94 beats = 48 s)
Write everything in beats; at another BPM just rescale. Hard cuts only where marked ✂ and only on a downbeat.

| Beat | Slot | Ref time | Beats | Camera (pace) | Caption (on → off, rel. to beat start) | Visual rule |
|---|---|---|---|---|---|---|
| B1 | **HOOK** | 0.0–3.5 | 7 | slow push-in + slight orbit → crash-zoom into the bright point (last 0.6 s) | `{{hook_line}}` 3 lines, 0.0 → 2.7 s | protagonist already in action at frame 0; a data cue (trace/graph/counter) in amber at bottom |
| B2 | STEP 1 | 3.5–7.3 | 7–8 | ✂ match-cut on scale (bright point → macro) then slow pull-out | `{{step1}}` +2 beats → 1.9 s | macro texture; amber "flood" event on a note |
| B3 | STEP 2 | 7.3–12.0 | 9 | continuous pull-out, framing static | `{{step2}}` +2.5 beats → 2.6 s | rhythmic repeated motion synced to 8th notes (hops) |
| B4 | STEP 3 (+number) | 12.0–16.0 | 8 | tilt/roll into steep diagonal perspective, track along to next part | `{{step3}}` +1 beat → 2.3 s, number line amber | first amber number |
| B5 | STEP 4 | 16.0–20.0 | 8 | ✂ on beat, slow push on a close-up | `{{step4}}` +1 beat → 2.3 s | "the gap / the key part" close-up |
| B6 | STEP 5 + BUILD | 20.0–24.0 | 8 | slow pull-out, then **hold ~0.4 s** | `{{step5}}` +1 beat → 1.9 s, then **wordless 1.5 s** | contracting amber ring + growing glow = countdown |
| B7 | **HIT / SCALE BURST** (P1) | 24.0–30.5 | 12–13 | ✂ on downbeat → flare+shockwave → fast pull-out (~2 s) → slow drift | **none** (8–10 s wordless total incl. B6 tail) | chain closes; waves of sparks across many copies of the protagonist |
| B8 | BIG NUMBER | 30.5–35.2 | 9 | continuous morph: system becomes a recognisable silhouette | `{{big_number_line}}` +3.5 beats → 2.65 s, number amber | particles assemble into shape, gold waves sweep |
| B9 | **METAPHOR + BRAND** (P2) | 35.2–44.6 | 18 | pull-out reveal of the everyday object around it, then near-static hold | `{{metaphor_line}}` +2 beats → 3.5 s; brand `{{brand_handle}}` etched in-world ≈ +10 beats → end | the longest hold; system = filament/core of the object |
| B10 | **LOOP** | 44.6–48.0 | 7 | fastest move: push into the object → through the system → land exactly on frame 0 | `{{hook_line}}` returns ≈ 2.5 s into the beat | last frame == first frame |

Ratios to keep (±30 %): 3 hard cuts per 48 s; mean segment 4.8 s (≈9 beats); text-on-screen ≈ 40 % of runtime;
one wordless stretch of ≈ 20 % of runtime right after the climax; every segment has camera motion (no dead stills).

## 3. Locked look
- Canvas 1080×1920; art grid 180×320 ×6 (or 270×480 ×4 in the engine); nearest-neighbour only; 4×4 Bayer dither for glow, fog, fades.
- Palette (lock): bg `#11071A` `#221031` · violet `#663B9F` `#6E3FAC` · lilac `#B087DC` · off-white `#F4ECEB` · amber/energy `#E5AF4D` `#F8D070` · ember `#AB603A`.
  Everything cool violet; **amber only on the energy/signal and the key number**. Amber area grows across the film (dot → flood → whole object glows).
- Pseudo-3D shading on round forms (spheres, capsules, tubes): 3–4 ramp steps + 1 off-white specular dot + amber rim light.
- Ambient: drifting dust motes in every shot, soft dithered vignette, dithered bloom around every spark.
- Brightness: mean ≈ 0.19, low-key, glow-on-black.

## 4. Locked typography
- Font: 5×7 monospace pixel font, ALL CAPS — bitloop's built-in font (full-height İ Ş Ğ Ü Ö Ç). Press Start 2P has the glyphs but squashes accented capitals; DotGothic16 lacks İ Ş Ğ. Stroke 12 px, cap ≈ 80 px, line height 120 px.
- Box: solid `#05000C` rectangle hugging text (~24 px pad), top edge y = 186 px (≈ 10 %), centred; 1–3 lines, ≤ 12 chars/line, ≤ 6 words.
  **(Reference-clone look only. Since Oct 2026 @hayret.piksel uses full-sentence narration blocks (§12.6); the 12-char/6-word rule is retired.)**
- Text `#F0E8F0`; numeric/key-fact line `#F8D070`.
- In: 6 frames (0.1 s) dithered fade (text ghost first, then box). Out: 6 frames dithered fade. No typewriter, no bounce, no emoji.
- Language: write captions in the channel's language (Turkish) but keep them telegraphic: "BİR NÖRON / ATEŞLER / NE KADAR UZAĞA?".

## 5. Locked sound
- Music-only, no VO; title ends with 🎧. 110–125 BPM steady electronic/lo-fi pulse, bass-heavy, no drop silence > 0.5 s.
- Every spark/flash/hop placed on an audio onset (8th-note grid); the P1 hit on a downbeat after a small dip.
- Music must be user-provided or library-licensed (ReelMimic rule: never download commercial songs).

## 6. Slots to fill per topic (see recipe.json)
`{{topic}}` · `{{protagonist}}` (the ONE tiny thing) · `{{hook_line}}` (subject + "how far / how fast / how small?" question, ≤ 6 words) ·
`{{step1..5}}` (cause → effect chain, 2–4 words each; one has a number) · `{{system_view}}` · `{{big_number_line}}` ("ONE OF / N / THINGS") ·
`{{metaphor_object}}` + `{{metaphor_line}}` (number + everyday unit) · `{{brand_handle}}` · `{{title}}` ("One X of N 🎧" pattern: ≤ 6 words + a number + 🎧) ·
`{{description}}` (2 sentences, facts incl. numbers + 3–4 hashtags) · `{{music}}`.

## 7. Hook rules (first 1–3 s)
1. Frame 0 already shows the protagonist mid-action (no logo, no intro), the caption/narration box is on from frame 0 (first letter ≤ 0.2 s).
2. Caption = subject + open question, fully readable by ~3 s. 3. A tiny data cue (trace/counter) moves on the beat. 4. By ~4 s one clear visual turn delivers the first scale jump (calm pacing: a match/dissolve or a single crash, not a chain of them).

## 8. Ending / CTA
No verbal CTA. Retention comes from the seamless loop (last frame = first frame, first caption reappears) + brand in-world on the hero object. Title/description carry the facts.

## 9. QA checklist (ReelMimic human-eye list adapted)
- Pixel discipline (no AA, no non-integer bitmap scaling, no smooth gradients) · captions readable on phone · only 3 hard cuts, all on beats ·
  every spark on a note · P1 has a 0.4 s held breath before the hit · B7 has no text · last frame vs first frame diff ≈ 0 ·
  side-by-side `clip_strip.py --vs` of our P1/P2 vs reference P1 (20.6–26.5 s) / P2 (30–44.6 s).

---

## 10. Engine: `bitloop` v2 (`bitloop/`)
- Commands: `init <dir> --archetype <name>`, `validate` (rules + **retention map**), `sheet`, `strip`, `music`, `render --package`.
- Listings: `bitloop list archetypes|styles|scales|drums|transitions|props|scenes`.
- The reference itself is `templates/reference_scale_journey.json` (`preset: reference`: violet/amber, 117.45 BPM D minor, four-on-floor, 94 beats = 48.0 s).
- `scale_journey` is the same structure re-designed for the channel: Hicaz maqsum at 128 BPM, 10 different transitions, a twist and punch-ins, about 44 s.

## 11. Channel layer: @hayret.piksel
See `../brand/BRAND.md`. The reference's 60 fps / violet-amber / D minor are replaced by:
- 30 fps.
- The Çini Gecesi palette (turquoise = wonder/key number, coral = heat).
- A diegetic tag only.
- The sonic logo, transposed into each video's own key.

Music is **not** fixed to Hicaz; it is designed per topic (§12).

---

## 12. Konuya özel müzik + kurgu tasarım rehberi (TR)

Her video için bir **spec** yazıyoruz. Marka katmanı sabit kalıyor, gerisini konu belirliyor. Akış şöyle:

1) Konuyu sorgula → 2) duyguyu ve "hayret anını" bul → 3) arketip seç (ya da hiçbirini seçme) → 4) müziği ve kurguyu aynı vuruş saatinde tasarla → 5) `validate` ile retention haritasına bak → 6) `sheet`/`strip` ile gözle kontrol et → 7) render al.

### 12.1 Konuya sorulacak sorular
| Soru | Neyi belirler? |
|---|---|
| Hayret anı ne? (tek cümle + tek sayı) | ödül sahnesi (reveal/payoff), sayının düşüşe denk gelmesi, metafor nesnesi |
| Konu **küçükten büyüğe** mi, **süreç** mi, **karşılaştırma** mı, **mit** mi, **hikâye** mi? | arketip (§12.4) |
| Duygu ne: merak, gerilim, ferahlık, komiklik, huşu, hüzün? | dizi/makam, tempo, ölçü, ses rengi (aşağıdaki tablo) |
| Ritim fiziksel mi (kalp, dalga, makine, yürüyüş, dönme)? | ölçü ve tempo (ör. kalp ≈ 70 BPM, makine 7/8, dönme 3/4) |
| Kültürel bağ var mı (Türkiye, tarih, mutfak, doğa)? | makam ve aksak ritim seçimi |
| Kaç "seviye" var (ölçek basamağı, adım, madde)? | bölüm sayısı ve sıklık (her 4–8 vuruşta yeni seviye) |
| Görsel olarak hangi tek nesne her şeyi özetliyor? | metafor nesnesi (kavanoz/kutu/pil/telefon/küre/PNG), okunur etiket |

### 12.2 Duygu → müzik seçimi (başlangıç noktaları, kesin kural değil)
| Duygu / konu | Dizi | Tempo | Ölçü | Davul | Ses rengi | `style` |
|---|---|---|---|---|---|---|
| Huşu, uzay, ölçek | lydian, whole_tone | 80–100 (ivmelenerek) | 4/4 | half_time → four_on_floor | fm, sid pad | `whole_tone_space` |
| Merak, keşif | dorian, pentatonic_major | 110–128 | 4/4 | breakbeat | gameboy | `pentatonic_bounce` |
| Gerilim, tehlike, gizem | phrygian, locrian, harmonic_minor | 130–150 | 7/8, 4/4 | aksak_7_8, trap | sid | `aksak_phrygian`, `trap_harmonic` |
| Masal, zarif, tarih | lydian, nihavend | 84–96 | 3/4, 6/8 | waltz, six_eight | fm | `lydian_waltz`, `nihavend_six_eight` |
| Türkiye / yerel bağ | hicaz, uşşak, rast, kürdi, hüzzam (`tuning: approx`) | 100–132 | 4/4 maqsum, 9/8 aksak | maqsum, aksak_9_8 | 2a03 | `hicaz_maqsum`, `rast_aksak` |
| Hüzün → umut (önce/sonra) | minor → major (bölüm `scale` değişimi) | 72–90 | 4/4 | half_time → four_on_floor | gameboy | `halftime_minor` |
| Mizah, ters köşe | blues, mixolydian | 100–120 | 4/4 swing | shuffle | 2a03 | `blues_shuffle` |
| Enerji, rekor, imkânsız sayı | major, mixolydian | 100 → 124 (accel) | 4/4 | four_on_floor, dnb | sid | `synthwave_major` |

**Müzik kuralları:**
- Düşüş (drop) hayret anına denk gelmeli. Hemen öncesinde `riser` ve ≤ 0,5 vuruş `stop` (nefes tutma) olmalı.
- Enerji videonun ikinci yarısında zirve yapmalı (eskalasyon).
- Ritardando (`bpm_to`) kapanışta, accelerando büyüme anlatılarında işe yarar.
- Ses logosu kendiliğinden ifşa vuruşuna ve döngü dikişine yerleşiyor. Videonun dizisine/makamına transpoze ediliyor, lead sesinin tınısıyla çalınıyor. Bunun için ek bir şey yapman gerekmiyor.
- Melodiyi kontura göre seç: "question" kontur soru cümlesine, "rise" büyümeye, "fall" çözülmeye, "arch" hikâyeye uyar. Ya da notaları açıkça yaz.
- Aynı stili art arda iki videoda kullanma. Her videoda en az tempo, dizi veya ölçüden biri değişmeli.

### 12.3 Retention (izlenme süresi) oyun kitabı
1. **Kanca (0,5–1,5 sn):**
   - İlk karede hareket ve bir özne olmalı (`void` olmaz).
   - Görsel bir kalıp kırıcı kullan: beklenmedik ölçek, tek bir crash-zoom ya da güçlü bir match. **Güçlü ama okunur:** kanca metni ~3 sn içinde tamamen görünür olmalı.
   - Merak boşluğu açan bir soru ya da cesur bir iddia ekle.
   - **Logo intro'su yok.** Etiket ilk 2 saniyede görünmüyor.
2. **Açık döngü:** sonucu baştan vaat et ("…ama asıl şaşırtıcı olan sonda"), teslimatı geç yap (son %45).
3. **Yeniden kanca, her 5–8 saniyede bir:** yeni soru, yeni sayı, yeni ölçek, ifşa ya da müzikte düşüş. `rehook` rolü veya olayı da kullanılabilir.
4. **Görsel değişim, ortalama ~3 saniyede bir (sakin tempo, Ekim 2026'dan beri varsayılan):**
   - Kesme, geçiş, sakin kamera hareketi, yeni öğe **ya da açılan anlatım metni**. Harf harf / kelime kelime açılan metin görsel değişim sayılıyor.
   - Yeni çekim (segment) ~3–5 saniyede bir; geçişler artık ~2 sn'de bir değil.
   - **4,5 saniyeden uzun durağan an yok** (metin açılıyorsa 4–5 sn sorun değil). Düşüşten önceki ≤ 1,5 sn'lik nefes serbest.
   - Eski "punchy" tempo (1,5–2,5 sn, durağan ≤ 3 sn) sadece `"pacing": "punchy"` ile; ilk iki video buna sabitlendi.
5. **Artan bahis:** sayılar büyüsün, ölçek açılsın, enerji yükselsin.
6. **Kalıp kırma:** en az 3 farklı geçiş türü kullan, aynı geçiş 3 kez art arda gelmesin. Arada sessizlik, ritim değişimi (ölçü/tempo) ya da renk flaşı olabilir.
7. **Videonun ortasında ters köşe** (%30–80): "ama…", "aslında…", "ters!" (`twist` rolü).
8. **Tatmin edici ödül:** sayı düşüşe otururken ses logosu çalar ve okunur etiket görünür (nesne etiketi). Tek kare bile ekran görüntüsü alınacak kadar güzel olmalı.
9. **Kusursuz döngü:** son kare ilk kareye akıyor (`loop_transition`), kanca altyazısı geri geliyor. İzleyici farkında olmadan yeniden izliyor.
10. **Metin dili: anlatıcı cümleleri (§12.6).** 12 harf / 6 kelime sınırı kalktı; netlik kısalıktan önemli.
    - Tam cümle yaz: anlatım bloğu ≤ 5 satır × ~20–26 harf (body boyutu), başlık/kanca ≤ 3 satır × ~15 harf (head).
    - Normal yazım (büyük-küçük harf) varsayılan; `"case": "upper"` sadece başlık kartlarında.
    - Merak boşluğu bırak, cevabı ilk blokta verme. Anahtar kelime türkuaz (`*…*`), ikinci vurgu mercan (`_…_`).
    - **Okuma süresi:** blok tamamen açıldıktan sonra ekranda ≥ 0,6 sn + kelime başına 0,35 sn kalmalı (validator uyarır). Uzun metin = uzun segment ya da iki blok.
    - Metin kapsama oranı sınırı (eski %25–60) kalktı; metin videonun çoğunda ekranda olabilir.
    - Kanal adı metinde hiç geçmiyor (yalnızca dünyanın içinde etiket).
11. **Uzunluk:**
    - Hızlı liste ya da mit/gerçek: 20–30 sn.
    - Süreç ya da önce/sonra: 25–40 sn.
    - Ölçek yolculuğu ya da hikâye: 30–45 sn.
    - 45 saniyenin üstüne ancak gerçekten taşıyan bir hikâye varsa çık. Kesin sınır 15–90 sn.
12. **Başlık / açıklama / etiket (Türk izleyici):**
    - **Başlık:** ≤ 60 karakter, merak + sayı ("1 nöron sinyali ne kadar hızlı? ⚡"). Clickbait yalanı yok, sayı gerçek olmalı. 🎧 emojisi "sesi aç" sinyali veriyor.
    - **Açıklama:** 2 cümle (bilgi + sayı) ve gerekirse kaynak.
    - **Etiketler:** 3–6 tane (konu, #bilim, #ilginçbilgiler, #pixelart, #hayretpiksel).
    - **Kapak karesi** (`cover_t`): kancanın en güçlü karesi. Özne ve soru görünsün, en fazla 3 kelime.

`validate` bu kuralları denetliyor ve bir **RETENTION MAP** basıyor:
- Zaman çizelgesi şeridi: `!` kanca/yeniden kanca, `|` geçiş, `▲` düşüş, `♪` ses logosu, `@` okunur etiket, `↻` döngü.
- Olay tablosu.
- En uzun durağan an ve en uzun yeniden kanca boşluğu.

Render'dan önce yapıyı buradan gözden geçir.

### 12.4 Yapı arketipleri (isteğe bağlı başlangıç noktaları)
| Arketip | Ne zaman | Yapı | Müzik önerisi |
|---|---|---|---|
| `scale_journey` | tek bir küçük şeyin ölçekler boyunca yolculuğu (referans) | kanca → 4 adım → ters köşe → build → hit → sayı → metafor → döngü | Hicaz maqsum 128 |
| `countdown_top_n` | "en şaşırtıcı 5 …" | kanca → 5…2 (her madde 2 ölçü, farklı geçiş) → build+stop → 1 numara ifşa | pentatonik breakbeat 128 |
| `before_after_reveal` | dönüşüm, eski/yeni | önce (minör, half-time) → **split screen** → ters köşe → düşüş + **majöre geçiş** | A minör → A majör, 84 |
| `process_timeline` | "nasıl çalışır?" | numaralı aşamalar, **match cut** ve push zinciri | 7/8 aksak frigyen 140 |
| `myth_vs_fact` | yaygın yanlış | mit (glitch) → **CRT kapanma + sessizlik** → gerçek düşüşte | trap harmonik minör 130 → majör |
| `cosmic_zoom_out` | küçükten evrene | her **portal** bir 10'un kuvveti | whole-tone 84 → 112 accelerando → lidyen |
| `impossible_number` | akıl almaz sayı | sayılar her 4 sn'de büyür → build → sayı düşüşte | synthwave 100 → 124 accel, düşüşte +2 transpoze |
| `story_vignette` | mini hikâye, karakter | bir gün… → sorun → deneme → ters köşe → çözüm | 3/4 lidyen vals → harmonik minör → lidyen, rit. |

`bitloop init <dir> --archetype <ad>` iskeleti yazıyor (Ekim 2026'dan beri sakin tempo: altyazı yerine `{{kanca: …}}` / `{{anlatım: …}}` anlatım slotları, segment başına en fazla 1 `punch`, hızlı geçişler sadece ifşa/sayı/düşüşte, zoom aralığı yarıya indirildi). Müziği konuya göre **değiştir**; arketipler yalnızca başlangıç noktası. Hiçbirine uymayan bir yapı için `blank` ile başla.

### 12.5 Geçiş sözlüğü (vuruşa bağlı, SFX'i kendiliğinden geliyor)
| Geçiş | Ne zaman kullanılır? |
|---|---|
| `cut` | düz kesme |
| `crash` | odağa dalış |
| `dissolve` | dither erime |
| `whip` | hızlı yön değişimi |
| `slide` / `push` | sıra, liste |
| `mosaic` | sayı patlaması |
| `iris` | hayret gözü, ifşa |
| `tiles` | çini silme, kültürel geçiş |
| `glitch` | mit, hata, şüphe |
| `match` | şekil eşleşmesi, süreç |
| `silhouette` | ortak siluet üzerinden dönüşüm |
| `flash` | düşüş |
| `spin` | dönme, döngü |
| `split` | karşılaştırma |
| `portal` | nesnenin içinden geçiş, ölçek atlama |
| `crt` | kapanma, sessizlik, "aslında…" (koyu sahnede `floor: .6` ver: siyah kare kalmaz) |

Geçişin anahtar anı vuruşa oturuyor: `center` hizalamada değişim tam vuruşta oluyor.

**Sakin tempoda** (varsayılan) `beats` verilmemiş geçişlerin süresi ×1,6 uzuyor (ör. whip 0,5 → 0,75 vuruş, dissolve 1,5 → 2,5). Hızlı geçişler (`crash`, `whip`, `spin`, `glitch`, `flash`, `mosaic`, `portal`, `split`) için bütçe ~10 sn'de 1; onları hikâyenin döndüğü yere (ifşa, sayı, düşüş) sakla, geri kalanında `dissolve`, `match`, `slide`, `push`, `iris`, `tiles`, `crt`, `silhouette` kullan.

### 12.6 Anlatım metni (narration) — tam cümleler, müziğe kilitli açılış
Segmentin `narration` listesi. Her blok bir cümle ya da kısa paragraf; zamanlama vuruş cinsinden, harfler/kelimeler müzik ızgarasında açılıyor ve isteğe bağlı "blip" sesleri aynı vuruşlarda çalıyor.

```json
"narration": [
  {"text": "Bir kitap *geleceğini* biliyor olsaydı, _sen_ yine de seçer miydin?", "at": 0, "place": "top", "reveal": "type", "rate": "16th"},
  {"text": "Laplace: her atomun yerini bilen bir zihin, yarını dün gibi görür.", "at": 8, "until": 20, "place": "dialog", "speaker": "LAPLACE"},
  {"text": "Bu kitap = sen", "at": 4, "place": "callout", "target": [0, -20], "reveal": "word"},
  {"text": "YARIN = DÜN", "at": 2, "place": "world", "reveal": "line", "surface": {"x": 0, "y": -40, "w": 90, "fill": true}}
]
```

| Alan | Değerler (varsayılan kalın) |
|---|---|
| `text` | tam cümle; `*türkuaz*`, `_mercan_`, `\n` = zorunlu satır sonu |
| `at` | başlangıç vuruşu (segmente göre) veya `[başla, bitir]`; `until` verilmezse **otomatik**: açılış + okuma süresi (+`hold`), segment sonunda kesilir |
| `place` | **`auto`** (üst / alt panel / orta arasından özneyi ve diğer metni en az kapatanı seçer) · `top` (eski üst kutu) · `dialog` (RPG kutusu, `speaker` sekmesi, ▼ işareti) · `panel` (alt bant) · `title` (büyük başlık kartı, mercan alt çizgi) · `mid` · `callout` (nesneyi işaret eden etiket, `target` [x,y] sahne koordinatı ya da `"focus"`, `side`) · `world` (tabela, ekran, kitap sayfası, kara tahta: `surface` {x, y, w, dot, rot, fill, ink:"dark"}) |
| `size` | **`body`** 6 px/nokta ≈ 24 harf/satır, ≤ 5 satır · `head` 9 px ≈ 15 harf, ≤ 3 satır · `title` 12 px ≈ 11 harf · sayı = px/nokta (≥ 5) |
| `reveal` | **`type`** (harf harf) · `word` · `line` · `fade` · `none` |
| `rate` | **`auto`** (type: 16th, sığmazsa 32nd · word: beat → 8th · line: half → beat) · `32nd` `16th` `8th` `beat` `half` ya da vuruş sayısı. Virgülden sonra +1, noktadan sonra +2 adım nefes (`pauses`) |
| `blip` | **true** (type: her 2 harfte bir, ünlülerde biraz tiz; word/line: her birimde) · false · `{"every": 3, "vol": .6}`. Mikste ~−28 dB; tümden kapatmak: `music.sfx: {"blip": null, "blip_hi": null}` |
| `cursor` | type'ta **açık**: yazarken sabit, bitince 8'lik notalarda yanıp söner |
| `exit` | **`dither`** · `wipe` (soldan sağa) · `cut`; `exit_beats` **0,5** |
| `case` | **`as_is`** · `upper` (Türkçe i/İ doğru) |
| `xy` | `[fx, fy]` ekran oranı ile elle konum |

Spec düzeyinde: `narration_defaults` (tüm bloklara varsayılan), `readability` (`{"per_word": .35, "base": .6}` ayarlanabilir), segment düzeyinde `subject` (`[x0,y0,x1,y1]` sahne koordinatı, sayı = odak çevresi yarıçapı, `"none"`) — otomatik yerleşimin kaçındığı kutu.

**Okunurluk (ölçülmüş):** 5,4" (124 mm yükseklik) telefonda 35 cm'den büyük harf yüksekliği ≥ 22 yay dakikası (ISO 9241-303) → **en az 5 px/nokta** (`narration.MIN_DOT`; 4 px = 17,8′ yetersiz). Ayrıca 720p'ye küçültme + bulanıklık + JPEG-40 sonrası glif tanıma 3 px'ten itibaren %100. Body 6 px (26,7′), head 9 px, title 12 px. Dünyadaki metin için ekrandaki nokta = `surface.dot` × kamera zoom × 6; validator 5'in altını uyarır. Eski altyazılar da artık 5 px'in altına küçülmüyor.

**Güvenli alanlar:** alt %18 (platform yazısı/düğmeler), sağ %12,5 (beğeni/yorum sütunu), sol ve üst %5. Otomatik yerleşim bunların dışına çıkmaz; aynı anda görünen bloklar üst üste binmez, alt alta dizilir.

**Türkçe satır kırma:** kelime ortasından bölmez; sayı grupları ve sayı + birim (`300 000 km`, `%40`, `3 sn`) birlikte kalır; satır sonunda 1–2 harfli kelime (ve, de, bu) bırakmamaya çalışır; satıra sığmayan tek kelimeyi hece kuralına göre tireler (ki-tap-lık, türk-çe, sa-at). Ortalanmış bloklar (üst, başlık) eşit uzunluklu satırlara dengelenir.

**Döngü:** ilk segment `at: 0` ile başlayan blok, videonun sonunda kare 0'daki hâliyle (boş kutu) geri gelir; dikiş kusursuz kalır.

### 12.7 Sakin tempo (`"pacing": "calm"`, varsayılan)
| | calm (varsayılan) | punchy (eski) |
|---|---|---|
| sarsıntı / flaş (`fx.shake` / `fx.flash`) | 1,0 / 0,22 | 2,5 / 0,55 |
| `punch` / `flash` / `pulse` olay şiddeti | 0,05 / 0,35 / 0,12 | 0,12 / 0,6 / 0,3 |
| crash süresi / dalış zoom'u | 2 vuruş / ×3,5 | 1,2 / ×7 |
| arka plan katmanları, parçacıklar | %60 hız | %100 |
| `beats` verilmemiş geçişler | ×1,6 uzun | ×1 |
| validator: ortalama görsel değişim | 1–3,5 sn | ≤ 2,5 sn |
| validator: en uzun durağan an | 4,5 sn (açılan metin değişim sayılır) | 3 sn |
| validator: ortalama segment | ≥ 2,5 sn (hedef 3–5) | — |
| validator: hızlı geçiş bütçesi | ~1 / 10 sn | — |
| validator: kamera hızı (kanca hariç) | zoom ≤ 0,35 ln/sn, pan ≤ 30 px/sn, dönüş ≤ 6°/sn, orbit ≤ 4° | — |

Kamera önerisi: `ease` varsayılan `inOutSine`; zoom aralıkları küçük (ör. `[1, 1.15]` 4 sn'de), büyük dalışlar yalnızca kancada ya da ifşada. Kanca güçlü kalsın: ilk karede hareket + özne, ilk harf ≤ 0,2 sn, hızlı geçiş bütçesinin biri kancaya harcanabilir.

### 12.9 Görme modları (`visions`, `vision`, `palette`) — "aynı dünya, başka göz"
- Sahneyi bir kez G-buffer olarak çiz (albedo + UV / ısı / derinlik / nesne kimliği), sonra her segmentte farklı bir gözün haritasından geçir: `vision: "ari"`. Harita listesi ve formüller: `bitloop/README.md` → Vision system.
- Her göz kendi kilitli paletine dither'lanır. Metin kutusu her zaman marka renginde kalır (anlatım sonradan, tam çözünürlükte eklenir). Her görme paletinde `#04060E` ve `#F4ECDC` bulunsun.
- Aynı sahne art arda geliyorsa dünya kesintisiz akar (küresel vuruş saati): geçiş = göz değiştirme. Göz açılışı için `iris`, karanlığa geçiş için `crt`, "çöküş" için `collapse`, kancada merak için `peek` (≤ 0,75 vuruş).
- Sonar halkaları müzikteki `B` (yarasa cıvıltısı) vuruşlarına kilitli: halka her vuruşta 1 kare içinde başlar.
- Dürüstlük: "görür" yerine gerektiğinde "algılar"; yalancı renk (false colour) bir çeviri olduğunu açıklamada söyle.

### 12.8 Araştırmacı / planlayıcı için
Plan yazarken `recipe/RESEARCHER_GUIDE.md`'yi kullan. Rehberde şunlar var: anlatım cümleleri, okuma süresi bütçesi, yerleşim seçimi, sakin tempo ve plan tablosu biçimi.

### 12.10 Kozmos paketi (`cosmic_zoom`, `chalk_unify`, `galaxy_chess`, `chaos_twin`)
- **Ölçek zinciri:** `cosmic_zoom` ile kamera 1.0'da kalır, zoom'u sahne yapar. Her basamak ×10'dur; 1/8'in altına düşen basamak dither ile kaybolur. Döngü için son segmentte `rewind_to_frame0` kullan.
- **Tahta tektir:** art arda gelen `chalk_unify` segmentleri aynı tahtayı paylaşır (yazılan kalır). Okunur imza `tag: "legible"` ile yazılır (glow/vignette'ten muaf, validator sayar).
- **Kural = nota:** `galaxy_chess` `ca_series` ile müzikteki seriyi okur. Her hücre, notası çaldığı karede yanar.
- **Kaos ikizleri:** `chaos_twin.diverge_at`, ayrılmanın vuruşudur (±1 kare). Müzikteki ikiz melodilerin ayrıldığı vuruş ayrı ayarlanır; ikisini aynı yapmak istiyorsan `diverge_at`'i seriyle eşle.
- **Üs yazımı:** "10¹²⁰" artık doğrudan yazılabilir (pixfont üst simgeleri). Formüller `G_{μν}` sözdizimiyle yazılır.

