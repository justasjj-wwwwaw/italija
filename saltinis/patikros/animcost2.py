import asyncio, sys
from playwright.async_api import async_playwright
U='http://localhost:8765/index.html?t=2026-10-26T15:20'
VAR={'all':'','no-waves':'.w{animation:none!important}','no-boats':'.boat,.bob{animation:none!important}',
     'no-sky':'.sky *{animation:none!important}','only-sky':'#ovmap *{animation:none!important}','none':'*{animation:none!important}'}
async def run(b, name, css):
    ctx=await b.new_context(viewport={'width':360,'height':760},device_scale_factor=3,is_mobile=True,has_touch=True,service_workers='block')
    pg=await ctx.new_page(); await pg.route('**/*wikipedia.org/**',lambda r:r.abort()); await pg.route('**/api.open-meteo.com/**',lambda r:r.abort())
    await pg.goto(U,wait_until='load'); 
    if css: await pg.add_style_tag(content=css)
    await pg.wait_for_timeout(1500)
    cdp=await ctx.new_cdp_session(pg); await cdp.send('Performance.enable'); await cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
    async def m():
        r=await cdp.send('Performance.getMetrics'); return {x['name']:x['value'] for x in r['metrics']}
    a=await m(); await pg.wait_for_timeout(3000); c=await m()
    dt=c['Timestamp']-a['Timestamp']
    print('%-9s busy %3.0f%%'%(name,100*(c['TaskDuration']-a['TaskDuration'])/dt))
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for k,v in VAR.items(): await run(b,k,v)
        await b.close()
asyncio.run(main())
