# Gardos Ežeras 2026 | Kelionės Vadovas

Statinė kelionės svetainė adresu **italija.tingek.lt**. Be kūrimo žingsnio ir be išorinių priklausomybių: tiesiog failai, kuriuos aptarnauja GitHub Pages.

## Failai

- `index.html`: visas puslapis (CSS ir JS įdėti viduje, ikonos kaip SVG sprite)
- `fonts/`: savo serveryje laikomi šriftai (Hanken Grotesk, Bodoni Moda; apkarpyti iki lietuviškų ir lotyniškų ženklų, WOFF, licencija OFL, tekstai šalia)
- `sw.js`: „service worker“, kad puslapis atsidarytų ir be ryšio (kalnuose)
- `manifest.webmanifest`, `icons/`: programėlės ikonos ir pridėjimas į telefono pagrindinį ekraną
- `og.jpg`: paveikslėlis, rodomas pasidalijus nuoroda (Messenger, WhatsApp, Facebook ir kt.)
- `CNAME`: custom domenas `italija.tingek.lt`
- `.nojekyll`: GitHub Pages nenaudoja Jekyll

## Paleidimas per GitHub Pages

1. Repozitorijos **Settings → Pages**: Source `Deploy from a branch`, branch `main`, folder `/ (root)`.
2. **Custom domain**: `italija.tingek.lt` (jau nurodyta `CNAME` faile), įjunkite `Enforce HTTPS`.
3. DNS pas `tingek.lt` tiekėją: `CNAME` įrašas `italija` → `justasjj-wwwwaw.github.io`.

## Kaip veikia

- **Laikai ir trukmės.** Kiekvienas punktas turi siūlomą laiką (Italijos laiku), o tarp punktų rodoma kelionės trukmė (automobiliu, pėsčiomis ar keltuvu) ir atstumas.
- **Dienos suvestinė.** Kiekvienos dienos pradžioje: bendras važiavimo laikas ir atstumas, ėjimo laikas ir apytikslis žingsnių skaičius, saulėtekis, saulėlydis, sutemos ir (kelionės dieną) kiek liko iki sutemų.
- **Gyvas režimas.** Kelionės dienomis puslapis pagal Italijos laiką atidaro šiandienos dieną, praėjusius punktus suskleidžia, dabartinį paryškina („Dabar“), kitą pažymi („Toliau“). Apačioje rodoma gyva juosta: kas vyksta, kas toliau, kiek liko iki sutemų. Žemėlapyje pulsuoja dabartinis taškas.
- **Peržiūra be kelionės.** Pridėkite `?t=2026-10-31T12:10` prie adreso (laikas – Italijos), pvz. `https://italija.tingek.lt/?t=2026-10-31T12:10`. Nuorodos pateiktos puslapio apačioje.
- **Žemėlapiai.** Viršuje: pasirinkite dieną (1–5) ir pamatysite maršrutą su atvykimo laikais. Kiekviena diena turi savo detalų žemėlapį su laikais ir nuorodą „Maršrutas Google Maps“.
- **Nuotraukos.** Mažos nuotraukos prie gražiausių vietų įkeliamos naršyklėje iš Wikipedia / Wikimedia Commons (laisvos licencijos), **tik atidarytoms dienoms**, su 7 s riba ir 14 dienų talpykla naršyklėje. Jei nuotraukos gauti nepavyksta, vieta paprasčiausiai lieka be nuotraukos ir puslapis „nešokinėja“ (vieta nuotraukai rezervuota iš anksto). Kuri nuotrauka rodoma, nustato Wikipedijos straipsnio pagrindinė nuotrauka; sąrašas yra `PH` žodyne generavimo skripte.
- **Be ryšio.** Pirmą kartą atidarius su internetu, puslapis, šriftai ir ikonos išsaugomi. Vėliau, jei tinklo nėra ar jis lėtas (>5 s), rodoma išsaugota versija, o kai tik ryšys yra, imama naujausia. Nuotraukos ir žemėlapių nuorodos į Google Maps be ryšio neveikia.

## Optimizavimas ir suderinamumas

- **Greitis.** Joks išorinis šaltinis neblokuoja piešimo: šriftai savi (~90 KB, iš anksto užkraunami, `font-display: swap`), nėra bibliotekų, HTML po suspaudimo ~30 KB. Matuota su sulėtintu 4G tinklu (1,6 Mb/s, 150 ms) ir 4× lėtesniu procesoriumi telefono dydžio ekrane: pirmas turinys ~1 s, išdėstymo šuoliai (CLS) 0, pirmas įkėlimas ~250 KB.
- **Suderinamumas.** Skriptas parašytas ES5 sintakse (patikrinta `eslint`, `ecmaVersion: 5`), kur reikia, naudojamos patikros (`fetch`, `AbortController`, `serviceWorker`, `Intl`), o jų nebuvimas nieko nesugadina. Be JavaScript puslapis lieka naudojamas: žemėlapis matomas, o dienų programas galima atverti paspaudus (tai veikia pačioje naršyklėje), tik nėra gyvo režimo ir nuotraukų.
- **Naršyklių minimumas** (išvesta iš naudojamų CSS funkcijų `gap` flex ir `clamp()`, ne išbandyta): Chrome / Edge 84+, Firefox 75+, Safari / iOS 14.5+, Samsung Internet 14+. Senesnėse puslapis gali atrodyti su kitokiais tarpais ir šrifto dydžiais.
- **Prieinamumas.** Teksto kontrastas ≥ 4,5:1 (didelio ≥ 3:1), paspaudžiami elementai mobiliajame ne žemesni kaip 36 px, antraščių hierarchija h1 → h2 → h3 → h4, `aria-*` ir `alt` visur, kur reikia, `prefers-reduced-motion` gerbiamas.
- **Patikrinta realiai tik Chromium** (Playwright). Firefox ir Safari testavimo aplinkoje nebuvo, todėl jų atveju remtasi statine patikra (sintaksė, CSS funkcijų lentelė, struktūra), o ne bandymu su pačia naršykle.

## Duomenys ir prielaidos

- Kelionės trukmės: OSRM maršrutų skaičiavimas (be spūsčių), suapvalinta aukštyn; kalnų keliams pridėta atsarga.
- Ėjimas: įvertis pagal planuojamą ėjimo laiką (~100 žingsnių per minutę).
- Saulės laikai: astronominis skaičiavimas (NOAA algoritmas), sutemos – civilinės sutemos pabaiga. Tarp kalnų realus saulėlydis ankstesnis.
- Cascata Varone lapkritį dirba 10:00–17:00.

## Pastaba atnaujinant

Pakeitus `index.html`, pasikeičia ir `sw.js` versija (`CACHE`), kad lankytojai gautų naują turinį. Jei redaguojate `index.html` ranka, pakeiskite `garda-…` pavadinimą `sw.js` faile.
