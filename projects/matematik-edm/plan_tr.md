# matematik-edm: "Her ses = tek bir grafik"

**Süre:** 20,0 sn (40 vuruş, 120 BPM, 4/4, 11 sahne, **punchy** tempo — EDM enerjisi). Sabit kamera, sahne içi titreşim.
**Fikir:** Her bölüm bir matematik fonksiyonu; fonksiyon hem **canlı çizilen eğriyi** hem **o bölümün ses karakterini** belirler. Dokuz ayrı fonksiyon/katman (hardtekk kick → phonk 808 → acid → funk → phonk melodi → jersey club → trance arp → psytrance → build) tek bir elektronik parçaya birleşir; drop'ta hepsi aynı anda patlar.
**Hayret anı:** "Matematik = müzik". Aynı anda hem duyduğun hem gördüğün şey, ekrandaki formülün ta kendisi.

## Başlık önerileri
1. **Her Ses = Tek Bir Grafik: Matematikle EDM 🎧** ← önerim
2. 9 Fonksiyon, 1 Parça: Matematiğin Sesi 🔊
3. Formülü Duyabilir misin? Matematik + EDM 🎧

## Renk ve marka notu (bilinçli sapma)
Brief **siyah + neon pembe** istiyor; bu, kanalın "Çini Gecesi" paletinden bilinçli bir ayrılık. Kural gereği **konuya özel palet** kullanıyorum (`palette: "neon"`, `projects/matematik-edm/palettes.py`): zemin `#0A0A0A`, neon pembe `#FF00FF`, beyaz-pembe vurgular; marka katmanı (anlatım kutusu/metni `#04060E`/`#F4ECDC`, logo, etiket, sonic logo) sabit kalıyor. Elektrik camgöbeği `#00FFFF` yalnız çok seyrek ikinci vurgu.

## Akış (her sahne ≈ 2 sn = 4 vuruş; formül sahne boyunca alt bölümde okunur)
| Zaman (sn) | Sahne | Fonksiyon | Görsel | Ses (bölüm) | Etiket |
|---|---|---|---|---|---|
| 0,0–1,0 | **GİRİŞ** | — | Koordinat düzlemi neon pembe çizgiyle açılır; ilk basla canlanır. | Tek acid blip + ilk kick; düşük enerji. | **MATEMATİKLE ELEKTRONİK MÜZİK** (title) |
| 1,0–3,0 | **hardtekk** | `y = mod(8t,1) > 0.9 ? 1 : -1` | Keskin dikey darbeler; her darbede sarsıntı + pembe parçacık. | Sert mekanik kick (four_on_floor, punchy). | HARDTEKK KICK |
| 3,0–5,0 | **phonk 808** | `y = sin(2π·39t)·exp(−3t)·tanh(10·sin(2π·0.5t))` | Eğri aşağı kıvrılır; takip noktası düşük salınım. | Derin distorsiyonlu 808 bass (triangle/fm, oktav 2). | PHONK 808 |
| 5,0–7,0 | **acid** | `y = sign(sin(2π·4t))·exp(−0.5·mod(t,0.25))` | Kare dalga, keskin sıçramalar. | Rezonanslı acid bass (pulse %25, arp updown). | ACID BASSLINE |
| 7,0–9,0 | **funk** | `y = sin(2π·2t) + 0.5·sin(2π·6t+π/4)` | Üst üste binen senkoplu dalgalar. | Funk groove (breakbeat/shuffle + tok bas). | FUNK RİTMİ |
| 9,0–11,0 | **phonk melodi** | `y = sin(2π·(220+50·sin(2π·0.3t))·t)` | Melodik yükseliş/düşüş; nokta Y'de gezer. | Karanlık modüleli FM lead (oktav 5). | PHONK MELODİSİ |
| 11,0–13,0 | **jersey club** | `y = mod(12t,1) < 0.3 ? sin(2π·200t) : 0` | Hızlı üçlü darbeler, her vuruşta parlama. | Hızlı enerjik jersey ritmi (16'lık hat + rim). | JERSEY CLUB |
| 13,0–15,0 | **trance** | `y = sin(2π·440·2^mod(2t,1)·t)·exp(−2·mod(t,0.5))` | Noktalar basamak basamak tırmanır; her nota iz bırakır. | Yükselen trance arpej (arp up, 16'lık). | TRANCE ARPEGGIO |
| 15,0–17,0 | **psytrance** | `y = sin(2π·65t)·(0.5+0.5·sign(sin(2π·8t)))` | Kesintili bass hareketi; sert ritmik titreşim. | Sürücü psytrance bassline (16'lık pulse). | PSYTRANCE BASS |
| 17,0–19,0 | **build** | `y = sin(2π·(100+50t)·t)·(t/3)` | Genlik+frekans büyür; ızgara sıklaşır, parlama artar. | Riser + snare roll; enerji tırmanır. | HAZIR MISIN? |
| 19,0–20,0 | **DROP** | tüm katmanlar | Bütün grafikler aynı anda; parçacık patlaması; güçlü son vurgu. | **Drop:** kick + 808 + acid + funk + phonk + jersey + trance + psy birlikte. | **HER SES = TEK BİR GRAFİK** (title) |

## Matematik → ses dürüstlüğü
- **Eğri tam olarak fonksiyondan** çizilir (her karede, sahne yerel zamanıyla; zaman değişkeni her sahne için sıfırdan).
- **Ses**, formülün frekans/sönüm karakterini kullanır ama **müzikal tempoda** (120 BPM) çalar. Nedeni: 4–8 Hz'lik bir "gate" (hardtekk/jersey) tek başına perde olarak duyulmaz; 39 Hz (808) ve 65 Hz (psy) ise gerçek sub-bass'tır. Formül: doğru grafik; ses: aynı karakterin duyulabilir hâli. Bu `sources.md`'de açıkça yazılı.
- **Tık/sıçrama koruması:** bölüm geçişlerinde `level_db` ±40 ms crossfade; ani parametre atlaması yok.

## Etiket (@hayret.piksel)
- **DROP, okunur:** dijital laboratuvar plakası ("MAT-LAB") + `@hayret.piksel`, 19 sn'de belirir. (Brief "süs yok" dediği için tek etiket.)

## Açıklama metni (öneri)
Dokuz matematik fonksiyonu, dokuz ayrı elektronik ses karakteri... ve finalde hepsi tek bir parçada birleşiyor. Gördüğün eğri, duyduğun sesin ta kendisi: 39 Hz'lik 808'den 440 Hz'lik trance arpejine. Sence hangisi en sert? 👇
`#matematik #elektronikmüzik #edm #pixelart #chiptune #hayretpiksel`

## Teknik uyarlamalar (brief → repo)
1. **Web Audio API** → repo'nun kendi numpy sentezleyicisi (`bitloop/voices.py`). Aynı fikir (prosedürel ses), farklı motor; tarayıcı yok.
2. **44,1 kHz / 16-bit PCM** → motor 48 kHz'de sentezler; teslimde **44,1 kHz 16-bit PCM WAV** olarak yeniden örneklenir (`out/music_44k1_16bit.wav`). MP4'te ses AAC'tir (PCM MP4'e standart değil); 44,1 kHz'e indirilir.
3. **"📢/🔥" emoji** → piksel fontunda yok; kaldırıldı (intro ve drop'ta görsel vurgu üstleniyor).
4. **Süre 20 sn** → 15–90 sınırı içinde; 20–45 tatlı noktasının tam alt sınırında (uyarı yok).
5. **Kalabalık tempo** → `pacing: "punchy"` (11 sahne/20 sn). Kanalın "sakin tempo" varsayılanından bilinçli sapma; konu EDM olduğu için gerekçeli. Sen onaylarsan `calm`'a çekilebilir ama kurgu yavaşlar.

## Açık seçimler (senin kararın)
1. **Tempo:** `punchy` (önerim, EDM) mi, `calm` (kanal varsayılanı, daha yavaş) mı?
2. **Renk:** neon pembe `#FF00FF` (brief) mi, yoksa marka Çini Gecesi'ne mi çekilsin? (Brief'e uydum; marka katmanı sabit.)
3. **Başlık:** 1 (önerim), 2 ya da 3.
