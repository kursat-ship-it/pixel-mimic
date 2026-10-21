# @hayret.piksel: Marka Kılavuzu v1

> **Fikir:** Her video bir *hayret anı*na doğru akıyor. Merak (göz) açılıyor, "!" ile hayret geliyor, sonra döngü başa dönüyor.
> Bu tema "Çini Gecesi": İznik çinisinin kobaltı, türkuazı ve mercanı piksel gecesine taşınıyor.
> Referans videonun (Bit Wonder) **yapısını** koruyoruz. **Kimlik** bize ait.

Motor tarafında tek ayar yetiyor: spec dosyasında `"preset": "hayret"`. Bu ayar varsayılan olduğu için yazmasan da devrede.
- Kod: `../bitloop/bitloop/spec.py` (PRESETS), `palette.py`, `music.py`, `layers.py`, `props.py`, `pixfont.py`.
- Örnekler: `brand_board.png`, `sonic_identity.mp3`, `music_range_demo.mp3`. (`brand_teaser.mp4` repoda yok; `src/teaser.json` ile yeniden render edilir: `bitloop/bitloop.sh render brand/src/teaser.json -o brand/brand_teaser.mp4`.)

---

## 1. Palet: "Çini Gecesi" (17 renk)

| Rol | Ad | Hex |
|---|---|---|
| Zemin (en koyu → koyu) | Gece | `#060814` |
| | Derin Lacivert | `#0B1230` |
| | Mürekkep | `#141E4A` |
| Gövde / orta tonlar | Kobalt Koyu | `#1E2E73` |
| | Kobalt | `#2C47A6` |
| | Lapis | `#4169D1` |
| Açık tonlar | Gök | `#77A2EE` |
| | Sis | `#B8CDF2` |
| Işık / yazı | Krem | `#F4ECDC` |
| **Hayret** (enerji, sinyal, kilit sayı) | Derin Firuze | `#0B4F5C` |
| | Firuze | `#13A39B` |
| | **Türkuaz Işık** | `#41E8D2` |
| | Parıltı | `#D2FFF5` |
| **Isı** (gerilim, uyarı, "!", 2. vurgu) | Kiremit | `#7E1F35` |
| | **Çini Mercanı** | `#EC4A57` |
| | Mercan Işık | `#FF9A86` |
| Altyazı kutusu | Kutu | `#04060E` |

**Kurallar**
- Kare alanının yaklaşık %70'i kobalt gece tonlarında kalıyor. Türkuaz enerjiyi ve hayreti taşıyor; video boyunca alanı büyüyor (nokta → taşma → bütün nesne parlıyor).
- Mercan seyrek ve sıcak kullanılıyor: vuruş halkası, anten ışıkları, bokeh'in yaklaşık dörtte biri ve gözdeki "!".
- Altyazı kontrastı (kutu `#04060E` üzerinde, WCAG):
  - Krem: 17.2:1
  - Türkuaz Işık: 13.2:1
  - Mercan Işık: 9.8:1
  - Çini Mercanı: 5.5:1. Yalnızca büyük grafikte kullanılıyor, altyazı metninde kullanılmıyor.

**Neden bu palet?** Kanal adı "hayret" ve Türkçe. Türkiye'ye ait, tanınır ama klişe olmayan bir görsel kök arıyorduk: İznik çinisi. Kobalt gece bilim ve uzay duygusunu veriyor. Türkuaz, mor/amber kullanan referanstan ve rakip kanallardan net biçimde ayrışıyor. Mercan da sıcak kontrastı ve "!" anını sağlıyor.

## 2. Logo işareti: "hayret gözü"
- 15×10 piksellik bir badem göz:
  - Krem kontur.
  - Türkuaz iris.
  - Göz bebeği mercan **"!"**.
  - Üstte 3 kıvılcım (Parıltı).
- Anlamı: göz merakı, "!" hayret anını, kıvılcımlar keşfi temsil ediyor.
- Kullanım biçimleri:
  - Tam renk: neon tabela, etiket.
  - Tek renk: damga, kazıma, terminal.
  - Açık zemin üstünde koyu konturlu.
  - Yıldız arka planında soluk bir **takımyıldız** olarak.
- Yazı biçimi: `@hayret.piksel`, hep küçük harf ve tam bu şekilde. Dar yüzeylerde iki satır: `@hayret` / `.piksel`.

## 3. Metin: anlatım blokları (Ekim 2026'dan beri) ve altyazı
- **Ana metin = anlatım bloğu** (`narration`, recipe §12.6): tam cümleler, normal yazım (büyük-küçük harf), 5×7 piksel font, Türkçe harfler tam (â î û dahil).
  - Boyutlar: **body** 6 px/nokta (≈ 24 harf/satır, ≤ 5 satır) ve **head** 9 px (≈ 15 harf, ≤ 3 satır); büyük başlık kartı 12 px. **Ölçülmüş alt sınır 5 px/nokta**: 5,4" telefonda 35 cm'den büyük harf ≥ 22′. Bunun altında metin yok.
  - Yerleşim: üst kutu, RPG diyalog kutusu, alt panel, başlık kartı, nesneyi işaret eden etiket, dünyanın içinde (tabela/ekran/kitap/tahta). Otomatik yerleşim alt %18'e ve sağ sütuna (%12,5) girmez, özneyi kapatmaz.
  - Açılış müziğe kilitli: harf harf (16'lık/32'lik), kelime kelime (vuruş/8'lik) ya da satır satır; yumuşak chiptune "blip" (mikste ~−28 dB), imleç, dither ya da silme ile çıkış.
  - Okuma süresi: tam açıldıktan sonra ≥ 0,6 sn + 0,35 sn/kelime ekranda kalır.
- **Kısa altyazı** (`caption`, eski üst kutu) hâlâ var: üstte ortalı, y=186 px, 12 px nokta, BÜYÜK HARF (Türkçe i→İ, ı→I), en fazla 3 satır. 12 harf / 6 kelime sınırı **kalktı**; uzun satırlar küçülür ama 5 px/noktanın altına inmez (inecekse validator hata verir → anlatım bloğu kullan).
- Geçiş: dither'lı belirme ve kaybolma.
- Renkler: metin Krem, **anahtar kelime / kilit sayı Türkuaz** (`*...*`), ikinci vurgu Mercan Işık (`_..._`), kutu Gece. Hepsi Gece üstünde ≥ 7:1 kontrast.
- Metnin ekranda kalma oranına üst sınır yok (eski %25–60 kuralı kalktı); okunurluk kuralları geçerli.
- **Kanal adı altyazıda ve anlatım metninde hiç geçmiyor.**

## 4. Ses kimliği: sabit logo, her videoda yeni müzik
**Her video kendi konusuna göre tamamen farklı bir müzik ve kurguyla geliyor.** Tempo, ölçü, dizi/makam, akorlar, sesler, davul, melodi ve bölüm yapısı her seferinde baştan tasarlanıyor. Rehber: `../recipe/recipe.md` §12.

**Sabit kalan tek şey: ses logosu motifi.**
| Öğe | Kural |
|---|---|
| Motif | 4 nota, dizinin **5 → 1 → 2 → 3**'ü (Hicaz'da 2→3 artık ikili olduğu için "hayret" rengi daha da belirginleşiyor) |
| Ritim | **kısa-kısa-kısa-UZUN** (½ ½ ½ vuruş + 1¾ vuruş). Uzun nota ifşa vuruşuna ve döngü dikişine (yeni turun 1. vuruşu) oturuyor, kısa notalar ona doğru giden ön vuruşlar |
| Transpozisyon | o anki bölümün **anahtarına ve dizisine** göre yeniden yazılıyor (lidyen, frigyen, pentatonik, uşşak…). Tempo haritasını izlediği için ritardando'da da yerinde kalıyor |
| Tını | o videonun **lead sesi** (2A03 pulse, Game Boy, SID PWM, FM…). Altında bir oktav aşağıdan üçgen dalga var |
| Armoni | uzun notanın altında o anki akorun kökü (bas) ve akor darbesi, ardından parıltı arpeji |
| Yer | `music.logo.at`: varsayılanı `["reveal","loop"]`, istenirse vuruş listesi verilebiliyor |

- **Hicaz/maqsum artık yalnızca bir seçenek** (`style: "hicaz_maqsum"`). Örnek dosya `sonic_identity.mp3` bu stilde.
- Müzik yelpazesi `music_range_demo.mp3` dosyasında: 7/8 aksak frigyen 140 (SID) · 3/4 lidyen vals 90→70 rit. (FM) · half-time minör 75 (Game Boy).
- **Efekt paleti:** her olay ve geçiş kendi SFX'ini getiriyor. `music.sfx` ile değiştirilebiliyor ya da susturulabiliyor.
  - Olay ve vurgu sesleri: hit, boom, riser, whoosh, swipe, shimmer, zap, tick, pop, thud.
  - Geçiş sesleri: glitch, bitcrush, tiles, portal, crt_off/on, spin, flash, crash, split.
- **Mastering:** −14 LUFS (iki geçişli), gerçek tepe ≤ −1 dBTP.

## 5. Görsel gramer: "zengin, çok katmanlı sahneler"
Her sahnede **en az 3 hareketli katman** var. Motor bunu varsayılan olarak sağlıyor (`DEFAULT_STACK`); istersen sahne bazında `layers` ile değiştirebilirsin.
1. **Arka plan (paralaks 0,1–0,5):**
   - `horizon`: türkuaz/mercan ufuk ışığı.
   - `nebula`.
   - `stars`: 3 derinlik, göz kırpan yıldızlar, logo takımyıldızı.
   - `tiles`: İznik 8 köşeli yıldız örgüsü.
   - `grid`: perspektif zemin.
   - `skyline`: yanıp sönen pencereler, mercan anten ışıkları.
   - `rays`: ışık hüzmeleri.
2. **Orta plan:** konu, yani sahnenin kendisi (nöron, kavanoz, ağ…) ve parıltısı.
3. **Ön plan (paralaks 1,2–1,6):** `bokeh` (dörtte biri mercan), `debris`, `dust`.
4. **Ortam detayları:**
   - Yanıp sönen ışıklar, süzülen parçacıklar.
   - Tarama çizgisi parıltısı (döngüyle hizalı periyot).
   - Hafif vinyet.
5. **Vuruş dili:** her `hit` anında ekran sarsıntısı (2,5 piksel, 0,7 sn'de sönüyor) ve türkuaz renk flaşı (0,35 sn).
6. **Kamera:** geometri yeniden çizilerek zoom yapılıyor, pikseller hep kare kalıyor. `punch` olayı vuruşta kısa bir yakınlaşma yapıyor.
7. **Geçiş kütüphanesi** (vuruşa bağlı, SFX'i kendiliğinden geliyor): cut, crash, dissolve, whip, slide, push, mosaic, **iris (hayret gözü biçiminde)**, **tiles (çini yıldızı)**, glitch, match, silhouette, flash, spin, split, portal, crt.
   - Videoda en az 3 farklı tür kullanılıyor, aynısı 3 kez art arda gelmiyor.
   - Döngü dikişi de bir geçiş (`loop_transition`).
8. **Tutma ritmi:** her 1,5–2,5 sn'de bir görsel değişim, 3 sn'den uzun durağan an yok (düşüş öncesi ≤ 1,5 sn'lik nefes hariç). Her 5–8 sn'de bir yeniden kanca, ortada ters köşe, sonda ödül. `validate` → RETENTION MAP.

## 6. Dünya içi etiket (tag) kuralları
**Ana kural:** `@hayret.piksel` hiçbir zaman filigran ya da altyazı olarak görünmüyor. Hep sahnedeki bir **nesnenin üstünde** duruyor.

| Yer | Prop / nesne | Ne zaman | Okunurluk |
|---|---|---|---|
| **Metafor nesnesinin etiketi** (kavanoz, kutu, pil) | `object` + `brand: "auto"` | ifşada, ses logosuyla aynı anda | **telefonda net okunur**. Her videoda en az 1 kez |
| Ampul camında kazıma, telefonda açılış metni, küre arması | `object` (bulb / phone / globe) | ifşa | okunur |
| Uzay aracı gövde yazısı | `ship` | yıldızlı sahnelerde, erken bir adımda | ince (fark edene) |
| Neon tabela | `neon_sign` | şehir silueti olan sahnelerde | ince → orta |
| Terminal açılış metni (`> @hayret.piksel`, `> merak.exe`) | `terminal` | grid ve teknoloji sahnelerinde | ince |
| Laboratuvar plakası "MK-II" | `plate` | makine ve kap sahnelerinde | ince |
| Görev arması | `patch` | uzay ve ekipman sahnelerinde | ince |
| Kara tahta | `chalkboard` | anlatım ve okul havasında | orta |
| Reklam panosu | `billboard` | boş mekânda; metafor nesne değilse otomatik yedek | okunur |
| "HAYRET!" damgası | `stamp` | sayı ya da ifşa vuruşunda pop yapıyor | orta |
| Logo takımyıldızı | `stars` katmanı | her yıldızlı arka planda | çok ince |

- **Otomatik yerleşim** (`brand.auto: true`):
  1. Metafor nesnesine okunur etiket konuyor. Metafor bir nesne değilse reklam panosu ekleniyor.
  2. İlk adım/sistem sahnesine arka plana göre tek bir ince prop seçiliyor: yıldızlar → uzay aracı, şehir → neon, grid → terminal.
- Bir videoda **en fazla 3** etiket görünmeli: 1 okunur, 1–2 ince. Hepsi sahnenin mantığına uymalı; ışığı, paralaksı ve dokusu sahneyle aynı olmalı.
- Okunurluk eşiği: telefonda handle en az 2 nokta (≈12 px) yüksekliğinde görünmeli, kontrast en az 7:1 olmalı (krem zemin üstünde koyu yazı ya da koyu zemin üstünde türkuaz/krem).

## 7. Hızlı kontrol listesi (her videoda)
- [ ] 30 fps, 1080×1920, −14 LUFS
- [ ] Her sahnede en az 3 hareketli katman. Sakin tempo: vuruşta hafif sarsıntı/flaş (shake ≤ 2, flash ≤ 0,4), yeni çekim ~3–5 sn'de bir, hızlı geçiş ~10 sn'de en fazla 1
- [ ] Türkuaz yalnızca enerji ve kilit sayı için kullanıldı. Mercan seyrek
- [ ] Müzik bu konu için tasarlandı (önceki videodan farklı tempo/ölçü/dizi). Ses logosu ifşada ve döngüde, videonun anahtarında çalıyor
- [ ] RETENTION MAP: kanca ≤ 1,5 sn (kanca metni ~3 sn'de okunmuş), yeniden kanca ≤ 8 sn, ortalama görsel değişim ~3 sn, durağan an ≤ 4,5 sn (açılan metin değişim sayılır), ters köşe ve ödül yerinde, ≥ 3 geçiş türü
- [ ] Etiket ifşada okunur biçimde görünüyor. Filigran yok, handle altyazıda geçmiyor
- [ ] Metin tam cümle ve okunur: ≥ 5 px/nokta, okuma süresi uyarısı yok, güvenli alanlarda, özneyi kapatmıyor. Türkçe harfler tam boy, satır kırma doğru
