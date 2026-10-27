import asyncio, json
from playwright.async_api import async_playwright
from t2 import setup, SP, URL

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, w, h, mob in (('m320', 320, 640, True), ('m360', 360, 740, True), ('d1280', 1280, 900, False)):
            ctx = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2 if mob else 1, is_mobile=mob, has_touch=mob)
            await setup(ctx)
            pg = await ctx.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(URL, wait_until='load')
            await pg.add_style_tag(content='html{scroll-behavior:auto!important}')
            await pg.wait_for_timeout(600)
            await pg.evaluate("document.getElementById('toggle-all').click()")
            await pg.wait_for_timeout(600)
            info = await pg.evaluate('''() => {
              const de = document.documentElement; const over=[]; const small=[];
              document.querySelectorAll('body *').forEach(el => {
                const r = el.getBoundingClientRect();
                if (r.width && r.right > innerWidth + 1 && !el.closest('.nav-in') && !el.closest('svg')) over.push(el.tagName + '.' + el.className + ' ' + Math.round(r.right));
              });
              document.querySelectorAll('a,button,summary').forEach(el => {
                const r = el.getBoundingClientRect();
                if (r.width && r.height < 36 && !el.closest('svg') && !el.classList.contains('cred') && !el.closest('footer') && !el.classList.contains('go')) small.push((el.className||el.tagName)+' h='+Math.round(r.height)+' '+(el.textContent||'').trim().slice(0,22));
              });
              return {scrollW: de.scrollWidth, innerW: innerWidth, over: over.slice(0,8), small: small.slice(0,10)};
            }''')
            info['errors'] = errs
            print(name, json.dumps(info, ensure_ascii=False))
            await pg.evaluate("window.scrollTo(0,0)")
            await pg.wait_for_timeout(200)
            await pg.screenshot(path=f'{SP}/f_{name}_top.png')
            if name == 'd1280':
                await pg.tap('.dbtn[data-day="4"]') if False else await pg.click('.dbtn[data-day="4"]')
                await pg.wait_for_timeout(300)
                await pg.screenshot(path=f'{SP}/f_{name}_sel4.png')
                await pg.evaluate("document.getElementById('d3').scrollIntoView()")
                await pg.wait_for_timeout(300)
                await pg.screenshot(path=f'{SP}/f_{name}_d3.png')
            if name == 'm320':
                await pg.evaluate("document.getElementById('d2').scrollIntoView()")
                await pg.wait_for_timeout(300)
                await pg.screenshot(path=f'{SP}/f_{name}_d2.png')
            await ctx.close()
        await b.close()
asyncio.run(main())
