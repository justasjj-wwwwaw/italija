import asyncio, io
from playwright.async_api import async_playwright
from PIL import Image, ImageChops
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await b.new_context(viewport={'width':360,'height':800},device_scale_factor=2,service_workers='block')
        pg=await ctx.new_page(); await pg.route('**/*wikipedia.org/**',lambda r:r.abort()); await pg.route('**/api.open-meteo.com/**',lambda r:r.abort())
        await pg.goto('http://localhost:8765/index.html?t=2026-10-26T15:20',wait_until='load'); await pg.add_style_tag(content='.nav{position:static!important}.boat,.sky{visibility:hidden}'); await pg.wait_for_timeout(800)
        el=await pg.query_selector('#ovmap')
        a=Image.open(io.BytesIO(await el.screenshot())).convert('RGB'); await pg.wait_for_timeout(1500); c=Image.open(io.BytesIO(await el.screenshot())).convert('RGB')
        d=ImageChops.difference(a,c); print('waves-only diff bbox',d.getbbox(),'changed px',sum(1 for v in d.convert('L').getdata() if v>8))
        await b.close()
asyncio.run(main())
