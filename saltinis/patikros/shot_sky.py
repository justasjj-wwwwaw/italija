import asyncio
from playwright.async_api import async_playwright
from PIL import Image
SP='/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad'
CASES=[('2026-10-26T06:20',None),('2026-10-26T07:10',None),('2026-10-26T17:30',None),('2026-10-26T21:30',None),('2026-10-26T12:00','4'),('2026-11-02T08:00',None)]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await b.new_context(viewport={'width':360,'height':800},device_scale_factor=2,is_mobile=True,has_touch=True,service_workers='block')
        pg=await ctx.new_page(); await pg.route('**/*wikipedia.org/**',lambda r:r.abort()); await pg.route('**/api.open-meteo.com/**',lambda r:r.abort())
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        files=[]
        for i,(t,sel) in enumerate(CASES):
            await pg.goto('http://localhost:8765/index.html?t='+t,wait_until='load'); await pg.add_style_tag(content='.nav{position:static!important}'); await pg.wait_for_timeout(500)
            if sel: await pg.click(f'.dbtn[data-day="{sel}"]'); await pg.wait_for_timeout(300)
            el=await pg.query_selector('#sky'); f=f'{SP}/sky_{i}.png'; await el.screenshot(path=f); files.append(f)
            print(t,sel,await pg.evaluate("document.getElementById('sky').className+' | '+document.getElementById('sky-sr').textContent"))
        print('errors',errs)
        ims=[Image.open(f) for f in files]; W=ims[0].width; H=sum(i.height for i in ims)+8*len(ims)
        out=Image.new('RGB',(W,H),'white'); y=0
        for im in ims: out.paste(im,(0,y)); y+=im.height+8
        out.save(f'{SP}/sky_all.png')
        await b.close()
asyncio.run(main())
