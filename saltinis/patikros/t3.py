import asyncio, json, sys
from playwright.async_api import async_playwright
from t2 import setup, SP, URL

CASES = [
  ('2026-10-29T14:30','d1_pre'), ('2026-10-30T09:20','d2_coffee_end'), ('2026-10-30T22:00','d2_night'),
  ('2026-10-31T12:10','d3_terr'), ('2026-10-31T13:55','d3_travel'), ('2026-11-01T11:00','d4_ridge'),
  ('2026-11-02T16:30','d5_drive'), ('2026-11-03T00:10','flight'), ('2026-11-03T02:00','after'),
  ('2026-10-28T10:00','before'),
]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for t, name in CASES:
            ctx = await b.new_context(viewport={'width': 360, 'height': 740}, device_scale_factor=2, is_mobile=True, has_touch=True)
            await setup(ctx)
            pg = await ctx.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(URL + '?t=' + t, wait_until='load')
            await pg.add_style_tag(content='html{scroll-behavior:auto!important}')
            await pg.wait_for_timeout(1200)
            info = await pg.evaluate('''() => {
              const bar=document.getElementById('livebar');
              const q=s=>document.querySelector(s);
              return {
                bar: bar.hidden ? null : [q('#lb-a').textContent, q('#lb-b').textContent, q('#lb-r').innerText.replace(/\\n/g,' | ')],
                open: [...document.querySelectorAll('details.day')].map(d=>d.id+':'+(d.open?1:0)).join(' '),
                cur: [...document.querySelectorAll('li.ev.is-cur')].map(e=>e.dataset.title),
                next: [...document.querySelectorAll('li.ev.is-next')].map(e=>e.dataset.title),
                past: document.querySelectorAll('li.ev.is-past').length,
                trav: [...document.querySelectorAll('.leg.on')].map(e=>e.textContent),
                today: q('#nav-today').hidden ? null : q('#nav-today').getAttribute('href'),
                cd: q('#countdown').textContent,
                sel: q('#ovmap').dataset.sel,
                sun: [...document.querySelectorAll('.dl-t')].map(e=>e.textContent).slice(0,5),
                scrollY: Math.round(scrollY), scrollW: document.documentElement.scrollWidth
              };
            }''')
            print(name, t, json.dumps(info, ensure_ascii=False), errs)
            await pg.screenshot(path=f'{SP}/live_{name}.png')
            await ctx.close()
        await b.close()
asyncio.run(main())
