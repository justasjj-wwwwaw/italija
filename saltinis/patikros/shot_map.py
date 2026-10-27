import asyncio, sys
from playwright.async_api import async_playwright
SP='/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad'
async def main(out, w=360, t='2026-10-29T12:10', sel=None, sel_css='.mapbox'):
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await b.new_context(viewport={'width':w,'height':800},device_scale_factor=2,is_mobile=(w<500),has_touch=(w<500),service_workers='block')
        pg=await ctx.new_page(); await pg.route('**/*wikipedia.org/**',lambda r:r.abort()); await pg.route('**/api.open-meteo.com/**',lambda r:r.abort())
        url='http://localhost:8765/index.html'+(('?t='+t) if t else '')
        await pg.goto(url,wait_until='load'); await pg.add_style_tag(content='html{scroll-behavior:auto!important}.nav{position:static!important}'); await pg.wait_for_timeout(900)
        if sel:
            await pg.click(f'.dbtn[data-day="{sel}"]'); await pg.wait_for_timeout(500)
        el=await pg.query_selector(sel_css); await el.screenshot(path=out)
        await b.close()
a=sys.argv
asyncio.run(main(a[1], int(a[2]) if len(a)>2 else 360, a[3] if len(a)>3 and a[3]!='-' else None, a[4] if len(a)>4 and a[4]!='-' else None))
