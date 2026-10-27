import asyncio, io
from playwright.async_api import async_playwright
from PIL import Image, ImageChops
SP='/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad'
U='http://localhost:8765/index.html'
async def page(b, **kw):
    ctx=await b.new_context(viewport=kw.pop('vp',{'width':360,'height':800}),device_scale_factor=2,service_workers='block',**kw)
    pg=await ctx.new_page(); await pg.route('**/*wikipedia.org/**',lambda r:r.abort()); await pg.route('**/api.open-meteo.com/**',lambda r:r.abort())
    pg._errs=[]; pg.on('pageerror',lambda e:pg._errs.append(str(e))); pg.on('console',lambda m: m.type=='error' and pg._errs.append(m.text))
    return pg
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        # 1. animation runs
        pg=await page(b)
        await pg.goto(U+'?t=2026-10-29T12:10',wait_until='load'); await pg.add_style_tag(content='.nav{position:static!important}'); await pg.wait_for_timeout(600)
        mb=await pg.query_selector('.mapbox')
        a=Image.open(io.BytesIO(await mb.screenshot())); await pg.wait_for_timeout(2000); c=Image.open(io.BytesIO(await mb.screenshot()))
        diff=ImageChops.difference(a.convert('RGB'),c.convert('RGB')).getbbox()
        n=await pg.evaluate("document.getAnimations?document.getAnimations().length:-1")
        print('anim running: diff bbox',diff,'animations',n)
        print('counts', await pg.evaluate("({waves:document.querySelectorAll('#ovmap .wg use').length,boats:document.querySelectorAll('#ovmap .boat').length,peaks:document.querySelectorAll('#ovmap .mts path').length,rfOn:[].filter.call(document.querySelectorAll('#ovmap .rf'),function(e){return getComputedStyle(e).display!=='none'}).length})"))
        # paused when off screen
        await pg.evaluate("window.scrollTo(0,3000)"); await pg.wait_for_timeout(400)
        print('paused offscreen:', await pg.evaluate("[document.getElementById('ovmap').classList.contains('paused'),document.getElementById('sky').classList.contains('paused')]"))
        await pg.evaluate("window.scrollTo(0,0)"); await pg.wait_for_timeout(400)
        print('resumed:', await pg.evaluate("[document.getElementById('ovmap').classList.contains('paused'),document.getElementById('sky').classList.contains('paused')]"))
        # day 3 opened map
        await pg.evaluate("document.getElementById('d3').open=true"); await pg.wait_for_timeout(300)
        el=await pg.query_selector('#d3 .dmbox'); await el.scroll_into_view_if_needed(); await el.screenshot(path=f'{SP}/dm3.png')
        await pg.evaluate("document.getElementById('d1').open=true"); await pg.wait_for_timeout(300)
        el=await pg.query_selector('#d1 .dmbox'); await el.scroll_into_view_if_needed(); await el.screenshot(path=f'{SP}/dm1.png')
        print('errors',pg._errs)
        # 2. reduced motion
        pg=await page(b, reduced_motion='reduce')
        await pg.goto(U+'?t=2026-10-29T12:10',wait_until='load'); await pg.wait_for_timeout(500)
        await pg.click('.dbtn[data-day="3"]'); await pg.wait_for_timeout(300)
        r=await pg.evaluate("""({anims:document.getAnimations().filter(function(a){return a.playState==='running'}).length,
          wave:getComputedStyle(document.querySelector('#ovmap .wg')).opacity,
          boat:getComputedStyle(document.querySelector('#ovmap .b1')).transform,
          rf:getComputedStyle(document.querySelector('#ovmap .dl.on .rf')).display})""")
        print('reduced motion:', r, pg._errs)
        # 3. no JS
        pg=await page(b, java_script_enabled=False)
        await pg.goto(U,wait_until='load'); await pg.wait_for_timeout(400)
        el=await pg.query_selector('#sky'); await el.screenshot(path=f'{SP}/sky_nojs.png')
        # 4. desktop
        pg=await page(b, vp={'width':1280,'height':900})
        await pg.goto(U+'?t=2026-10-26T15:20',wait_until='load'); await pg.wait_for_timeout(600)
        el=await pg.query_selector('.hero'); await el.screenshot(path=f'{SP}/hero1280.png')
        print('desktop errors',pg._errs)
        await b.close()
asyncio.run(main())
