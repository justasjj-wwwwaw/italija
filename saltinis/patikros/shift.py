import asyncio, json, sys
sys.path.insert(0,'/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad'); sys.path.insert(0,'/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad/chk')
from t2 import setup
from wx import payload
from playwright.async_api import async_playwright
from urllib.parse import urlparse, parse_qs
INIT='''window.__s=[];new PerformanceObserver(l=>{l.getEntries().forEach(e=>{if(e.hadRecentInput)return;window.__s.push({t:Math.round(e.startTime),v:+e.value.toFixed(4),src:e.sources.map(s=>{var n=s.node;return (n?(n.nodeName+'.'+(n.className&&n.className.baseVal!==undefined?n.className.baseVal:n.className)+'#'+n.id):'?')+' '+JSON.stringify(s.previousRect.y|0)+'->'+JSON.stringify(s.currentRect.y|0)})})})}).observe({type:'layout-shift',buffered:true});
window.__sc=[];addEventListener('scroll',()=>window.__sc.push([Math.round(performance.now()),Math.round(scrollY)]));'''
async def main(q):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':780},is_mobile=True,has_touch=True,service_workers='block')
        await setup(ctx)
        async def om(r):
            await asyncio.sleep(1.2)
            qq=parse_qs(urlparse(r.request.url).query)
            await r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps(payload(qq)))
        await ctx.route('**/api.open-meteo.com/**',om)
        pg=await ctx.new_page(); await pg.add_init_script(INIT)
        cdp=await ctx.new_cdp_session(pg)
        await cdp.send('Network.enable'); await cdp.send('Network.setCacheDisabled',{'cacheDisabled':True})
        await cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':150,'downloadThroughput':1.6*1024*1024/8,'uploadThroughput':750*1024/8})
        await cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
        await pg.goto('http://localhost:8765/index.html'+q,wait_until='load'); await pg.wait_for_timeout(4500)
        print(q); print(json.dumps(await pg.evaluate('window.__s'),indent=0)[:1500]); print('scroll events',await pg.evaluate('window.__sc.slice(0,14)'))
        await b.close()
asyncio.run(main(sys.argv[1]))
