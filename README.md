# Gardos Ežeras 2026 | Kelionės Vadovas

Statinė kelionės svetainė (vienas `index.html`, be priklausomybių) adresu **italija.tingek.lt**.

## Failai

- `index.html`: visas puslapis (CSS ir JS įdėti viduje, šriftai iš Google Fonts)
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
- **Nuotraukos.** Mažos nuotraukos prie gražiausių vietų įkeliamos naršyklėje iš Wikipedia / Wikimedia Commons (laisvos licencijos). Jei nuotraukos nepavyksta gauti, vieta paprasčiausiai lieka be nuotraukos. Kuri nuotrauka rodoma, nustato Wikipedijos straipsnio pagrindinė nuotrauka; sąrašas yra `PH` žodyne generavimo skripte.

## Duomenys ir prielaidos

- Kelionės trukmės: OSRM maršrutų skaičiavimas (be spūsčių), suapvalinta aukštyn; kalnų keliams pridėta atsarga.
- Ėjimas: įvertis pagal planuojamą ėjimo laiką (~100 žingsnių per minutę).
- Saulės laikai: astronominis skaičiavimas (NOAA algoritmas), sutemos – civilinės sutemos pabaiga. Tarp kalnų realus saulėlydis ankstesnis.
- Cascata Varone lapkritį dirba 10:00–17:00.
