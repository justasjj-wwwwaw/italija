import asyncio, json, sys
sys.path.insert(0,'/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad'); sys.path.insert(0,'/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad/chk')
from t2 import setup
from wx import payload
from playwright.async_api import async_playwright
from urllib.parse import urlparse, parse_qs
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':780},is_mobile=True,has_touch=True,service_workers='block')
        await setup(ctx)
        async def om(r):
            await asyncio.sleep(5.0)
            q=parse_qs(urlparse(r.request.url).query)
            await r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps(payload(q)))
        await ctx.route('**/api.open-meteo.com/**',om)
        pg=await ctx.new_page()
        await pg.goto('http://localhost:8765/index.html?t=2026-10-31T12:10',wait_until='load')
        await pg.wait_for_timeout(3800)
        before=await pg.evaluate("(()=>{var e=document.querySelector('.ev.is-cur');var r=e.getBoundingClientRect();return [Math.round(r.top),Math.round(scrollY),document.querySelector('.st-wx[data-n=\"3\"] .wx-hrs').hidden]})()")
        await pg.wait_for_timeout(3500)
        after=await pg.evaluate("(()=>{var e=document.querySelector('.ev.is-cur');var r=e.getBoundingClientRect();return [Math.round(r.top),Math.round(scrollY),document.querySelector('.st-wx[data-n=\"3\"] .wx-hrs').hidden]})()")
        print('before [curTop, scrollY, hoursHidden]:',before,'after:',after)
        await b.close()
asyncio.run(main())
