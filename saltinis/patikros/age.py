import asyncio, json, sys, time
sys.path.insert(0,'/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad'); sys.path.insert(0,'/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad/chk')
from t2 import setup
from wx import payload
from playwright.async_api import async_playwright
from urllib.parse import urlparse, parse_qs
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await b.new_context(service_workers='block')
        await setup(ctx)
        async def om(r):
            q=parse_qs(urlparse(r.request.url).query)
            await r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps(payload(q)))
        await ctx.route('**/api.open-meteo.com/**',om)
        pg=await ctx.new_page()
        await pg.goto('http://localhost:8765/index.html?t=2026-09-01T10:00',wait_until='load'); await pg.wait_for_timeout(1000)
        for mins in (16,200,3000):
            await pg.evaluate("(m)=>{var c=JSON.parse(localStorage.getItem('garda-wx-1'));c.t=Date.now()-m*60000;localStorage.setItem('garda-wx-1',JSON.stringify(c));}",mins)
            await pg.route('**/api.open-meteo.com/**',lambda r:r.abort())   # tinklas nepasiekiamas: rodomas išsaugotas
            await pg.reload(wait_until='load'); await pg.wait_for_timeout(900)
            print(mins,'min ->',await pg.evaluate("document.querySelector('.st-wx .wx-src').textContent"))
            await pg.unroute('**/api.open-meteo.com/**')
        await b.close()
asyncio.run(main())
