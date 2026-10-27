import asyncio, sys, json, gzip
sys.path.insert(0,'/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad')
from t2 import setup
sys.path.insert(0,'/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad/chk')
from wx import payload
from urllib.parse import urlparse, parse_qs
import asyncio as _a
from playwright.async_api import async_playwright
INIT='''
window.__m={cls:0,lcp:0,fcp:0,lt:[],shifts:[]};
new PerformanceObserver(l=>{l.getEntries().forEach(e=>{if(!e.hadRecentInput){__m.cls+=e.value;__m.shifts.push([Math.round(performance.now()),+e.value.toFixed(4)]);}})}).observe({type:'layout-shift',buffered:true});
new PerformanceObserver(l=>{l.getEntries().forEach(e=>{__m.lcp=e.startTime})}).observe({type:'largest-contentful-paint',buffered:true});
new PerformanceObserver(l=>{l.getEntries().forEach(e=>{if(e.name==='first-contentful-paint')__m.fcp=e.startTime})}).observe({type:'paint',buffered:true});
new PerformanceObserver(l=>{l.getEntries().forEach(e=>{__m.lt.push(e.duration)})}).observe({type:'longtask',buffered:true});
'''
async def run(label,query,cpu,net):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':780},device_scale_factor=2,is_mobile=True,has_touch=True,service_workers='block')
        await setup(ctx)   # mocks wikipedia + commons
        async def om(r):
            await _a.sleep(0.35)
            q=parse_qs(urlparse(r.request.url).query)
            await r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps(payload(q)))
        await ctx.route('**/api.open-meteo.com/**',om)
        # remove old google fonts abort-routing noise: none needed now
        pg=await ctx.new_page()
        await pg.add_init_script(INIT)
        cdp=await ctx.new_cdp_session(pg)
        await cdp.send('Network.enable')
        await cdp.send('Network.setCacheDisabled',{'cacheDisabled':True})
        if net: await cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':150,'downloadThroughput':1.6*1024*1024/8,'uploadThroughput':750*1024/8})
        if cpu>1: await cdp.send('Emulation.setCPUThrottlingRate',{'rate':cpu})
        reqs={}
        def onresp(e): reqs[e['requestId']]={'url':e['response']['url'],'type':e.get('type')}
        cdp.on('Network.responseReceived',onresp)
        sizes={}
        cdp.on('Network.loadingFinished',lambda e:sizes.__setitem__(e['requestId'],e['encodedDataLength']))
        await pg.goto('http://localhost:8765/index.html'+query,wait_until='load')
        await pg.wait_for_timeout(4500)
        m=await pg.evaluate('window.__m')
        # trigger scroll to bottom to check lazy bits
        tot=sum(sizes.values())
        by={}
        for rid,r in reqs.items():
            k=r['url'].split('localhost:8765')[-1] if 'localhost' in r['url'] else r['url'].split('/')[2]
            by[k]=by.get(k,0)+sizes.get(rid,0)
        print(f"== {label}: FCP {m['fcp']:.0f}ms LCP {m['lcp']:.0f}ms CLS {m['cls']:.4f} longtasks {len(m['lt'])} (max {max(m['lt'] or [0]):.0f}ms, total {sum(m['lt']):.0f}ms) requests {len(reqs)} bytes {tot/1024:.0f}KB")
        if m['shifts']: print('   shifts',m['shifts'][:6])
        if label.startswith('slow'): 
            for k,v in sorted(by.items(),key=lambda x:-x[1])[:12]: print(f'   {v/1024:7.1f} KB  {k}')
        photos=await pg.evaluate("document.querySelectorAll('.ph.ok').length+'/'+document.querySelectorAll('.ph').length")
        print('   photos ok/slots:',photos)
        await b.close()
async def main():
    await run('fast desktop-ish, static','?t=2026-09-01T10:00',1,False)
    await run('slow 4G + 4x CPU, static','?t=2026-09-01T10:00',4,True)
    await run('slow 4G + 4x CPU, live day3','?t=2026-10-31T12:10',4,True)
asyncio.run(main())
