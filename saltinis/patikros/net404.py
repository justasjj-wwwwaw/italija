import asyncio, sys
sys.path.insert(0,'/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad')
from t2 import setup
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':360,'height':740})
        await setup(ctx)
        pg=await ctx.new_page()
        bad=[]
        pg.on('response',lambda r: bad.append((r.status,r.url)) if r.status>=400 else None)
        pg.on('requestfailed',lambda r: bad.append(('FAIL',r.url)))
        await pg.goto('http://localhost:8765/index.html?t=2026-10-31T12:10',wait_until='load')
        await pg.evaluate("document.querySelectorAll('details.day').forEach(d=>d.open=true)")
        await pg.wait_for_timeout(2500)
        print(bad)
        await b.close()
asyncio.run(main())
