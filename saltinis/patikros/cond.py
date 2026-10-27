import asyncio, json, sys
sys.path.insert(0,'/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad'); sys.path.insert(0,'/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad/chk')
from t2 import setup
from wx import payload
from playwright.async_api import async_playwright
from urllib.parse import urlparse, parse_qs
def mk(q):
    j=payload(q)
    codes=[]
    for d in range(5):
        for h in range(24):
            c=1
            if d==0 and (h<10 or h>20): c=45          # rūkas tik naktį/rytą, daily code = 45
            if d==1 and 10<=h<=14: c=61               # 5 val. lietaus
            if d==2 and h==15: c=95                   # perkūnija
            if d==3 and h in (9,10): c=63             # tik 2 val. lietaus
            if d==4: c=3
            codes.append(c)
    j['hourly']['weather_code']=codes
    j['daily']['weather_code']=[45,63,95,63,3]
    return j
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await b.new_context(viewport={'width':390,'height':780},service_workers='block')
        await setup(ctx)
        async def om(r):
            q=parse_qs(urlparse(r.request.url).query)
            await r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps(mk(q)))
        await ctx.route('**/api.open-meteo.com/**',om)
        pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://localhost:8765/index.html?t=2026-09-01T10:00',wait_until='load'); await pg.wait_for_timeout(1200)
        print(await pg.evaluate("[...document.querySelectorAll('.st-wx')].map(t=>t.dataset.n+': '+t.querySelector('.wx-cond').textContent+' | '+t.querySelector('.wx-src').textContent).join('\\n')"))
        print('errors',errs)
        await b.close()
asyncio.run(main())
