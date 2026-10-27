import asyncio, json, sys, datetime, math
sys.path.insert(0,'/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad')
from t2 import setup
from playwright.async_api import async_playwright
from urllib.parse import urlparse, parse_qs
SP='/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad'
URL='http://localhost:8765/index.html'

def payload(q, mode1=False):
    lat=float(q['latitude'][0]); el=float(q.get('elevation',[0])[0] or 0)
    d0=datetime.date(2026,10,22) if mode1 else datetime.date(2026,10,29)
    n=24 if mode1 else 5
    days=[(d0+datetime.timedelta(i)).isoformat() for i in range(n)]
    base=15-(el/1000*6.5)-(lat-45.5)*3
    codes=[1,2,61,3,95,0,45,63,2,80]
    daily={'time':days,'weather_code':[codes[i%10] for i in range(n)],
      'temperature_2m_max':[round(base+math.sin(i)*1.5,1) for i in range(n)],
      'temperature_2m_min':[round(base-6+math.sin(i)*1.5,1) for i in range(n)],
      'precipitation_sum':[round(abs(math.sin(i))*7,1) for i in range(n)],
      'precipitation_probability_max':[(i*17)%100 for i in range(n)],
      'wind_speed_10m_max':[round(12+i*3+el/100,1) for i in range(n)],
      'wind_gusts_10m_max':[round(30+i*6+el/50,1) for i in range(n)]}
    ht=[f'{d}T{h:02d}:00' for d in days for h in range(24)]
    hourly={'time':ht,'temperature_2m':[round(base-6+ (h if h<15 else 30-h)*0.7,1) for d in days for h in range(24)],
      'precipitation_probability':[ (h*4)%100 if h%5 else None for d in days for h in range(24)],
      'weather_code':[codes[(h+i)%10] for i,d in enumerate(days) for h in range(24)]}
    return {'latitude':lat,'longitude':10.8,'timezone':'Europe/Rome','daily':daily,'hourly':hourly}

async def scenario(name, handler, viewport=(360,740), shot=None, reload=False, ls=True):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':viewport[0],'height':viewport[1]},device_scale_factor=2 if viewport[0]<500 else 1,service_workers='block')
        await setup(ctx)
        calls=[]
        async def route(r):
            calls.append(r.request.url); await handler(r, len(calls))
        await ctx.route('**/api.open-meteo.com/**', route)
        pg=await ctx.new_page(); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(URL+'?t=2026-09-01T10:00',wait_until='load'); await pg.wait_for_timeout(1200)
        if reload:
            n0=len(calls)
            await pg.reload(wait_until='load'); await pg.wait_for_timeout(1000)
            print('  calls after reload (cache test): +',len(calls)-n0)
        info=await pg.evaluate("""()=>[...document.querySelectorAll('.st-wx')].map(t=>({n:t.dataset.n,loc:t.querySelector('.wx-loc').textContent,main:t.querySelector('.wx-main').textContent.replace(/\\s+/g,' '),meta:t.querySelector('.wx-meta').textContent.replace(/\\s+/g,' '),hrs:[...t.querySelectorAll('.wx-h')].map(h=>h.textContent.replace(/\\s+/g,' ')).join(' | '),alt:(t.querySelector('.wx-alt')||{}).textContent||'',adv:t.querySelector('.wx-adv').textContent,src:t.querySelector('.wx-src').textContent}))""")
        print('==',name,'| requests:',len(calls),'| errors:',errs)
        for i in info: print('  D'+i['n'],i['loc'],'|',i['main'],'|',i['meta'],'|',i['hrs'],'|',i['alt'],'|',i['adv'],'|',i['src'])
        if shot:
            for n in shot:
                await pg.evaluate(f"document.querySelectorAll('details.day').forEach(d=>d.open=(d.id==='d{n}'))")
                await pg.add_style_tag(content='html{scroll-behavior:auto!important}')
                el=await pg.query_selector(f'#d{n} .dstats')
                await el.scroll_into_view_if_needed()
                await el.screenshot(path=f'{SP}/wx_{name}_d{n}_{viewport[0]}.png')
        await b.close()
    return calls

async def ok(route,n):
    q=parse_qs(urlparse(route.request.url).query)
    await route.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps(payload(q,'past_days' in q)))
async def first400(route,n):
    q=parse_qs(urlparse(route.request.url).query)
    if 'start_date' in q:
        return await route.fulfill(status=400,content_type='application/json',headers={'access-control-allow-origin':'*'},body='{"error":true,"reason":"out of range"}')
    await ok(route,n)
async def fail(route,n): await route.abort()

async def main():
    c=await scenario('ok',ok,shot=[1,4,5],reload=True)
    print('  sample url:',c[0][:260])
    await scenario('fallback400',first400)
    await scenario('fail',fail)
    await scenario('ok',ok,viewport=(1280,900),shot=[4])
if __name__=='__main__': asyncio.run(main())
