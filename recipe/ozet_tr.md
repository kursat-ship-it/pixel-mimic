# Videonun formülü — "One Neuron of 86 Billion 🎧" (Bit Wonder)

- **Ne?** 48 saniyelik, dikey (1080×1920, 60 fps), seslendirmesiz, sadece müzikli bir bilim kısası. Görsel tarz: koyu mor zemin üzerinde parlayan, 3D gölgeli ama piksel ızgarasına (6 px) oturtulmuş **piksel art**. Gerçek çekim ya da yapay zekâ videosu değil.
- **Ana fikir:** Tek bir küçük şeyi (bir nöron sinyali) takip et, onu adım adım ölçekler arasında gezdir, sonunda "bu, 86 milyardan sadece biri" de ve hepsini tek bir gündelik nesneye (ampul, ~20 watt) bağla.
- **Kanca (0–3,5 sn):** İlk karede olay zaten oluyor; üstte "ONE NEURON FIRES — HOW FAR?" sorusu, altta turuncu bir sinyal çizgisi. 3,5. saniyede parlayan noktaya hızlı zoom ile ilk ölçek atlaması.
- **Gövde (3,5–24 sn):** 5 mekanizma adımı, her biri ~4 saniye (müzikte 8 vuruş = 2 ölçü). Her adımda 2–4 kelimelik tek bir altyazı kartı; birinde mutlaka sayı var (100+ M/S).
- **Kurgu:** Neredeyse tek plan; sahneler kamera itme/çekme ile birbirine dönüşüyor. Sadece 3 sert kesme var (3,5 / 16 / 24 sn) ve hepsi müziğin vuruşuna denk geliyor. Her kıvılcım ve parlama bir notaya oturuyor (117 BPM).
- **Doruk (20–30 sn):** Altyazı kaybolur, sessiz bir gerilim: sonraki nöronun etrafında daralan turuncu halka → kısa nefes tutma → vuruşta parlama + şok dalgası → kamera hızla geri çekilip binlerce nöronu gösterir. ~10 saniye hiç yazı yok.
- **Sonuç (30–44 sn):** Ağ bir beyin silüetine dönüşür, "ONE OF 86 BILLION NEURONS"; ardından beyin bir ampulün içinde görünür: "ALL OF IT RUNS ON ~20 WATTS". Kanal adı (@BITWONDER) ampulün camına kazınmış.
- **Bitiş / CTA:** Sözlü çağrı yok. Kamera ampulün içine dalıp ilk kareye geri döner, ilk altyazı tekrar belirir → kusursuz döngü (izlenme süresini artırır).
- **Yazı stili:** Üstte ortalı, siyah kutu içinde BÜYÜK HARF piksel font; beyaz metin, kilit sayı satırı amber/sarı. En fazla 3 satır, ~6 kelime; 0,1 sn'lik dither'lı belirme/kaybolma, daktilo efekti yok.
- **Renk:** Her şey koyu mor/lila; amber/turuncu sadece "enerji" ve önemli sayı için. Video boyunca amber alan büyür: tek nokta → taşma → tüm beyin altın gibi parlar.
- **Ses:** Seslendirme yok, başlıkta 🎧 ("sesi aç"). Bas ağırlıklı, sabit tempolu elektronik/lo-fi müzik (~117 BPM).
- **Senin konuna uyarlarken doldurulacaklar:** tek küçük kahraman nesne, açılış sorusu, 5 neden-sonuç adımı, "N taneden biri" sayısı, gündelik bir benzetme nesnesi + üzerindeki sayı, kanal adın ve lisanslı bir müzik. Başlık kalıbı: "Bir X, N Tanenin Biri 🎧" gibi, içinde sayı olsun.


## Kanal uyarlaması: @hayret.piksel (yeni varsayılan)
Yukarıdaki bilgiler **referans** videoyu anlatır. Bizim kanalda yapı aynı kalıyor: vuruş haritası, sahne rolleri, altyazı kuralları ve döngü. Kimlik ise bize ait:
- **30 fps** (referans 60 fps idi).
- **"Çini Gecesi" paleti:** kobalt gece zemin. **Türkuaz** hayret/enerji ve kilit sayının rengi, **mercan** sıcaklık ve gerilimin rengi, **krem** ışık ve yazının rengi.
- **Müzik (v1 örneği, artık seçeneklerden biri):** Re Hicaz chiptune, 112 BPM, maqsum ritmi. v2: her videoda konuya özel müzik.
- **Ses logosu:** 4 notalık La–Re–Mi♭–Fa♯. İfşa anında ve döngü dikişinde çalar.
- **Sahne katmanları:** her sahnede en az 3 hareketli katman var (ufuk ışığı, nebula/yıldız/çini/şehir arka planı, ön planda bokeh/toz).
- **Efektler:** vuruşta ekran sarsıntısı, düşüşte renk flaşı, tarama çizgisi parıltısı.
- **"@hayret.piksel" etiketi:** filigran olarak kullanılmıyor, hep dünyanın içinde duruyor. Metafor nesnesinin etiketinde okunur biçimde çıkıyor; başta bir de ince bir sahne öğesi var (uzay aracı gövdesi, neon tabela ya da terminal).

Ayrıntılar `../brand/BRAND.md` dosyasında.


## v2 (güncel): her videoya özel müzik ve kurgu
Sabit tek bir şablon yok artık. Her konu için müzik (tempo, ölçü, dizi/makam, sesler, davul, bölümler) ve kurgu (sahne listesi, geçişler, olaylar) baştan tasarlanıyor.
- **Sabit kalanlar:** marka katmanı ve 4 notalık ses logosu (her videonun anahtarına transpoze ediliyor).
- **Rehber ve izlenme oyun kitabı:** `recipe.md` §12.
- **Başlangıç iskeletleri:** 8 arketip.
- **Ön kontrol:** `validate` komutu render'dan önce RETENTION MAP basıyor.
