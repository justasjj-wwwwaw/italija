import asyncio
from playwright.async_api import async_playwright
U='http://localhost:8765/index.html?t=2026-10-26T15:20'
async def run(b, rm):
    ctx=await b.new_context(viewport={'width':360,'height':760},device_scale_factor=3,is_mobile=True,has_touch=True,service_workers='block',reduced_motion=rm)
    pg=await ctx.new_page(); await pg.route('**/*wikipedia.org/**',lambda r:r.abort()); await pg.route('**/api.open-meteo.com/**',lambda r:r.abort())
    await pg.goto(U,wait_until='load'); await pg.wait_for_timeout(1500)
    cdp=await ctx.new_cdp_session(pg); await cdp.send('Performance.enable'); await cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
    async def m():
        r=await cdp.send('Performance.getMetrics'); return {x['name']:x['value'] for x in r['metrics']}
    a=await m(); await pg.wait_for_timeout(4000); c=await m()
    dt=c['Timestamp']-a['Timestamp']
    print(rm,'main-thread busy %.0f%%'%(100*(c['TaskDuration']-a['TaskDuration'])/dt),'layout+style %.0f ms'%(1000*((c['LayoutDuration']-a['LayoutDuration'])+(c['RecalcStyleDuration']-a['RecalcStyleDuration']))))
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        await run(b,'reduce'); await run(b,'no-preference')
        await b.close()
asyncio.run(main())
