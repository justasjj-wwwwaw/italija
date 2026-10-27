# Šaltinis

Svetainė generuojama vienu skriptu, rankomis `index.html` neredaguojama.

- `build.py` – visas turinys (dienos, punktai, laikai, žemėlapiai, nakvynės, orai, stiliai, JavaScript). Paleidus `python3 saltinis/build.py` iš naujo sukuriami `index.html`, `sw.js` (nauja talpyklos versija), `manifest.webmanifest`, `CNAME`, `.nojekyll` repozitorijos šaknyje. Reikia tik Python 3.
- `patikros/` – patikros skriptai (Playwright + Chromium, Pillow): struktūra, kontrastas, perpildymas, darbas be ryšio, greitaveika, animacijų apkrova, žemėlapio užrašų persidengimas. Juose nurodyti kelių adresai yra iš kūrimo aplinkos, prieš naudojant juos reikia pakeisti; daugumai reikia vietinio serverio `python3 -m http.server 8765` repozitorijos šaknyje.
- `irankiai/gen_fonts2.py` – šriftų (Inter, Literata) apkarpymas iki lietuviškų ir lotyniškų ženklų.
