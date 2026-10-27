import asyncio, json, sys, io
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw

SP = '/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad'
URL = 'http://localhost:8765/index.html'

def make_jpg():
    im = Image.new('RGB', (320, 240))
    d = ImageDraw.Draw(im)
    for y in range(240):
        d.line([(0, y), (320, y)], fill=(40 + y // 3, 120 + y // 4, 160 - y // 4))
    d.ellipse([100, 60, 220, 180], fill=(230, 190, 90))
    b = io.BytesIO(); im.save(b, 'JPEG'); return b.getvalue()
JPG = make_jpg()

async def setup(ctx):
    async def fonts(route): await route.abort()
    await ctx.route('**/fonts.googleapis.com/**', fonts)
    await ctx.route('**/fonts.gstatic.com/**', fonts)
    async def wiki(route):
        url = route.request.url
        if 'Lago' in url or 'Lake' in url:
            return await route.fulfill(status=404, body='{}')
        await route.fulfill(status=200, content_type='application/json', body=json.dumps({
            'type': 'standard', 'thumbnail': {'source': 'https://upload.wikimedia.org/mock/320px-x.jpg', 'width': 320, 'height': 240},
            'content_urls': {'desktop': {'page': 'https://en.wikipedia.org/wiki/Mock'}}}),
            headers={'access-control-allow-origin': '*'})
    await ctx.route('**/api/rest_v1/page/summary/**', wiki)
    async def img(route): await route.fulfill(status=200, content_type='image/jpeg', body=JPG, headers={'access-control-allow-origin': '*'})
    await ctx.route('https://upload.wikimedia.org/**', img)

async def main():
    which = sys.argv[1] if len(sys.argv) > 1 else 'static'
    async with async_playwright() as p:
        b = await p.chromium.launch()
        out = {}
        if which == 'static':
            ctx = await b.new_context(viewport={'width': 360, 'height': 740}, device_scale_factor=2, is_mobile=True, has_touch=True)
            await setup(ctx)
            pg = await ctx.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_FAILED' not in m.text else None)
            await pg.goto(URL, wait_until='load')
            await pg.add_style_tag(content='html{scroll-behavior:auto!important}')
            await pg.wait_for_timeout(800)
            await pg.screenshot(path=f'{SP}/v2_hero.png')
            # select day 3 on map
            await pg.tap('.dbtn[data-day="3"]')
            await pg.wait_for_timeout(300)
            await pg.evaluate("document.getElementById('ovmap').scrollIntoView({block:'start'})")
            await pg.evaluate("window.scrollBy(0,-60)")
            await pg.wait_for_timeout(300)
            await pg.screenshot(path=f'{SP}/v2_ov3.png')
            for n in (1, 2, 4, 5):
                await pg.tap(f'.dbtn[data-day="{n}"]')
                await pg.wait_for_timeout(200)
                el = await pg.query_selector('#ovmap')
                await el.screenshot(path=f'{SP}/v2_ov{n}.png')
            # open day 3, screenshot pieces
            await pg.evaluate("document.getElementById('d3').open=true")
            await pg.wait_for_timeout(500)
            await pg.evaluate("document.getElementById('d3').scrollIntoView()")
            await pg.wait_for_timeout(400)
            await pg.screenshot(path=f'{SP}/v2_d3_a.png')
            el = await pg.query_selector('#d3')
            await el.screenshot(path=f'{SP}/v2_d3_full.png')
            for n in (1, 2, 4, 5):
                await pg.evaluate(f"document.getElementById('d{n}').open=true")
            await pg.wait_for_timeout(500)
            for n in (1, 2, 4, 5):
                el = await pg.query_selector(f'#d{n}')
                await el.screenshot(path=f'{SP}/v2_d{n}_full.png')
            out['photos_ok'] = await pg.evaluate("document.querySelectorAll('.ph.ok').length")
            out['photos_total'] = await pg.evaluate("document.querySelectorAll('.ph').length")
            out['scrollW'] = await pg.evaluate("document.documentElement.scrollWidth")
            out['errors'] = errs
            await b.close()
            print(json.dumps(out, ensure_ascii=False, indent=1))
            return
        await b.close()

if __name__=='__main__':
    asyncio.run(main())
