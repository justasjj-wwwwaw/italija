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

- Kelionės dienomis (spalio 29 – lapkričio 2 d.) automatiškai atsidaro „šiandienos“ diena, o meniu atsiranda nuoroda „Šiandien“.
- Spustelėjus dienos numerį žemėlapyje, atsidaro ta diena.
- Visos vietos turi nuorodą į Google Maps.
