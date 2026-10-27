import asyncio
from playwright.async_api import async_playwright
JS="""(function(){
 var ov=document.getElementById('ovmap');
 var mts=[].slice.call(ov.querySelectorAll('.mts path, .hillsS path')).map(function(e){return e.getBoundingClientRect();});
 var tx=[].slice.call(ov.querySelectorAll('text, .pin .dot, .lp .dot')).filter(function(e){var r=e.getBoundingClientRect();return r.width>0&&getComputedStyle(e).display!=='none'&&e.getClientRects().length;});
 var out=[];
 tx.forEach(function(t){var a=t.getBoundingClientRect();mts.forEach(function(m){var w=Math.min(a.right,m.right)-Math.max(a.left,m.left),h=Math.min(a.bottom,m.bottom)-Math.max(a.top,m.top);if(w>2&&h>2)out.push((t.textContent||t.getAttribute('class')).slice(0,24)+' '+Math.round(w)+'x'+Math.round(h));});});
 return out;})()"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':360,'height':800})
        await pg.route('**/*wikipedia.org/**',lambda r:r.abort()); await pg.route('**/api.open-meteo.com/**',lambda r:r.abort())
        await pg.goto('http://localhost:8765/index.html?t=2026-09-01T10:00',wait_until='load'); await pg.wait_for_timeout(400)
        for d in range(6):
            await pg.click(f'.dbtn[data-day="{d}"]'); await pg.wait_for_timeout(150)
            r=await pg.evaluate(JS); print('day',d,'overlaps',len(set(r)),sorted(set(r))[:8])
        await b.close()
asyncio.run(main())
