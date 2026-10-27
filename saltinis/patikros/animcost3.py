import asyncio
from playwright.async_api import async_playwright
U='http://localhost:8765/index.html?t=2026-10-26T15:20'
JS={'base':'',
 'noclip':"document.querySelectorAll('.waves').forEach(function(g){g.removeAttribute('clip-path')})",
 'groups':"""(function(){var g=document.querySelector('#ovmap .waves');var gs=[0,1,2,3].map(function(i){var e=document.createElementNS('http://www.w3.org/2000/svg','g');e.setAttribute('class','wg w'+i);g.appendChild(e);return e;});
   [].slice.call(g.querySelectorAll('use.w')).forEach(function(u){var c=u.getAttribute('class').match(/w(\\d)/)[1];u.setAttribute('class','');gs[+c].appendChild(u);});
   var st=document.createElement('style');st.textContent='.wg{fill:none;stroke:#BFE3F2;stroke-linecap:round;animation:wv 7s ease-in-out infinite}.wg.w1{animation-duration:8.6s}.wg.w2{animation-duration:6.2s}.wg.w3{animation-duration:9.4s}';document.head.appendChild(st);})()""",
 'groups+noclip':None}
async def run(b, name, js):
    ctx=await b.new_context(viewport={'width':360,'height':760},device_scale_factor=3,is_mobile=True,has_touch=True,service_workers='block')
    pg=await ctx.new_page(); await pg.route('**/*wikipedia.org/**',lambda r:r.abort()); await pg.route('**/api.open-meteo.com/**',lambda r:r.abort())
    await pg.goto(U,wait_until='load')
    for j in js: 
        if j: await pg.evaluate(j)
    await pg.wait_for_timeout(1500)
    cdp=await ctx.new_cdp_session(pg); await cdp.send('Performance.enable'); await cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
    async def m():
        r=await cdp.send('Performance.getMetrics'); return {x['name']:x['value'] for x in r['metrics']}
    a=await m(); await pg.wait_for_timeout(3000); c=await m()
    dt=c['Timestamp']-a['Timestamp']
    print('%-14s busy %3.0f%%'%(name,100*(c['TaskDuration']-a['TaskDuration'])/dt))
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        await run(b,'base',[JS['base']]); await run(b,'noclip',[JS['noclip']]); await run(b,'groups',[JS['groups']]); await run(b,'groups+noclip',[JS['groups'],JS['noclip']])
        await b.close()
asyncio.run(main())
