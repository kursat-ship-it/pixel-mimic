# Araştırmacı / planlayıcı rehberi: anlatım metni ve sakin tempo (Ekim 2026'dan itibaren)

Bu rehber `projects/<konu>/plan_tr.md` yazan araştırmacı için. Ayrıntılı kurallar recipe.md §12.3, §12.6 ve §12.7'de. Kullanıcı geri bildirimi şöyleydi: 12 harf / 6 kelimelik altyazılar anlamı bozuyordu, kurgu da çok hızlıydı. Bu yüzden bundan sonraki her plan şu kurallara uyuyor.

## 1. Metin = anlatıcı cümleleri
- Her sahnede 1–2 **anlatım bloğu** yaz. Her blok tam bir cümle ya da iki kısa cümle.
  - **body:** ≤ 5 satır × ~24 harf, yani ~120 harf.
  - **head** (kanca/başlık): ≤ 3 satır × ~15 harf.
- Telgraf dili yok. "1814: LAPLACE'IN ŞEYTANI" yerine: "*1814*'te Laplace, her atomun yerini bilen bir zihnin yarını dün kadar net göreceğini yazdı."
- Anahtar kelime ya da sayı `*türkuaz*`, karşıt vurgu `_mercan_`. Blok başına en fazla 1–2 vurgu.
- Normal yazım (büyük-küçük harf). BÜYÜK HARF sadece başlık kartında ya da kısa etikette (`"case": "upper"`).
- Kanal adı metinde hiç geçmez.

## 2. Okuma süresi bütçesi (planı yazarken hesapla)
- **Okuma:** blok tamamen açıldıktan sonra **0,6 sn + 0,35 sn × kelime** ekranda kalmalı. 12 kelime ≈ 4,8 sn, 20 kelime ≈ 7,6 sn.
- **Açılış:** harf harf 16'lık notada 120 BPM'de harf başına 0,125 sn (100 harf ≈ 12 sn, uzun). 32'likte ≈ 6 sn. `rate: "auto"` önce 16'lığı dener, sığmazsa 32'liğe geçer.
- **Kural:** sahne süresi ≥ açılış + okuma. Sığmıyorsa metni kısalt, ikiye böl ya da sahneyi uzat.
- **Kanca:** ilk blok ≤ ~12 kelime, `head` boyutu, `reveal: "word"` ya da hızlı type. ~3 sn içinde tamamen okunur olmalı. İlk harf ≤ 0,2 sn.

## 3. Yerleşim seçimi (planda her blok için yaz)
| Yerleşim | Ne zaman |
|---|---|
| `top` (varsayılan kutu) | genel anlatım |
| `dialog` + `speaker` | bir karakter/bilim insanı konuşuyor (LAPLACE, LIBET…) |
| `panel` | alt bant. Özne üstteyse |
| `title` | bölüm/başlık kartı ("İKİ KAMP"), büyük sayı |
| `callout` + `target` | sahnedeki bir nesneyi adlandır ("hazırlık potansiyeli") |
| `world` + `surface` | kitap sayfası, tabela, ekran, kara tahta |
| `auto` | emin değilsen motor özneyi kapatmayan yeri seçer |

- Alt %18 ve sağ sütun (%12,5) platform arayüzüne ait, oraya metin koyma.

## 4. Sakin tempo
- **Çekim:** yeni sahne/segment ~3–5 sn'de bir. 40 sn'lik video ≈ 8–11 sahne (eskiden 10 sahne + 20 olay).
- **Görsel değişim:** ortalama ~3 sn yeterli. Açılan metin değişim sayılır. 4–5 sn'lik durağan an, metin açılıyorsa sorun değil.
- **Geçişler:** varsayılan `dissolve`, `match`, `slide`, `push`, `iris`, `tiles`, `crt`, `silhouette`.
  - Hızlı geçişler (`crash`, `whip`, `spin`, `glitch`, `flash`, `mosaic`, `portal`, `split`) ~10 sn'de en fazla 1. Bunları hikâyenin döndüğü yere sakla: kanca, ters köşe, ifşa, düşüş.
- **Kamera:** küçük ve yavaş, örneğin zoom `[1, 1.15]` 4 sn'de. Büyük dalış yalnızca kancada ya da ifşada. `punch` sahne başına en fazla 1.
- **Shake/flash:** varsayılan yumuşak, planda artırma.
- Retention hedefleri hâlâ geçerli: kanca ≤ 1,5 sn, yeniden kanca 5–8 sn, ters köşe %30–80, ödül son %45. Yeniden kancayı artık çoğunlukla **cümlenin kendisi** taşıyor: soru, sayı, "ama…".

## 5. plan_tr.md tablo biçimi
| Zaman (sn) | Sahne | Anlatım (yerleşim · açılış) | Geçiş | Müzik |
|---|---|---|---|---|
| 0,0–4,0 | S1 kanca: … | **top · head · word:** "Geleceğin *yazılıysa*, seçen kim?" | cut | … |
| 4,0–9,0 | S2 … | **dialog LAPLACE · type 16th:** "Her atomun yerini bilen bir zihin için yarın, dün kadar *nettir*." (11 kelime → 4,5 sn okuma) | dissolve | … |

- Her satırda kelime sayısını ve okuma süresini yaz. Planı `bitloop validate` ile kontrol et.
- "on screen … < … reading time", "fast transitions", "segments average" uyarıları kalmasın.
