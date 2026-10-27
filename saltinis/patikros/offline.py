import asyncio
from playwright.async_api import async_playwright
URL='http://localhost:8765/index.html'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':800},service_workers='allow')
        pg=await ctx.new_page()
        errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.route('**/*wikipedia.org/**',lambda r:r.abort())
        await pg.route('https://upload.wikimedia.org/**',lambda r:r.abort())
        await pg.goto(URL,wait_until='load')
        await pg.evaluate("navigator.serviceWorker.ready.then(()=>1)")
        await pg.wait_for_timeout(1500)
        keys=await pg.evaluate("caches.keys()")
        print('caches',keys)
        cached=await pg.evaluate("caches.open(%s).then(c=>c.keys()).then(k=>k.map(r=>new URL(r.url).pathname))"%repr(keys[0]))
        print('cached:',cached)
        # SW controls?  reload once so the page is controlled
        await pg.reload(wait_until='load'); await pg.wait_for_timeout(500)
        print('controlled:',await pg.evaluate("!!navigator.serviceWorker.controller"))
        await ctx.set_offline(True)
        await pg.goto(URL+'?t=2026-10-31T12:10',wait_until='load'); await pg.wait_for_timeout(700)
        print('offline title:',await pg.title())
        print('offline livebar visible:',await pg.evaluate("!document.getElementById('livebar').hidden"))
        print('offline fonts:',await pg.evaluate("[...document.fonts].map(f=>f.family+':'+f.status).join(',')"))
        print('offline h1:',await pg.evaluate("document.querySelector('h1').innerText.replace(/\\n/g,' ')"))
        r=await pg.evaluate("fetch('fonts/inter.woff').then(r=>r.status+' '+r.headers.get('content-type'))")
        print('offline font fetch:',r)
        r=await pg.evaluate("fetch('manifest.webmanifest').then(r=>r.status)")
        print('offline manifest fetch:',r)
        await pg.goto('http://localhost:8765/',wait_until='load')
        print('offline root:',await pg.title())
        print('errors',errs)
        await b.close()
asyncio.run(main())
