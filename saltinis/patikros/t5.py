import asyncio, json
from playwright.async_api import async_playwright
from t2 import setup, URL
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': 360, 'height': 740}, timezone_id='Europe/Vilnius')
        await setup(ctx)
        await ctx.add_init_script("""
          (function(){var R=Date;var fixed=R.UTC(2026,9,31,11,0,0);
          function F(){var a=arguments;return a.length?new (Function.prototype.bind.apply(R,[null].concat([].slice.call(a))))():new R(fixed)}
          F.prototype=R.prototype;F.now=function(){return fixed};F.UTC=R.UTC;F.parse=R.parse;window.Date=F;})();
        """)
        pg = await ctx.new_page()
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL, wait_until='load'); await pg.wait_for_timeout(800)
        print(await pg.evaluate("[document.getElementById('lb-a').textContent, document.getElementById('lb-b').textContent, document.getElementById('lb-r').innerText, document.getElementById('countdown').textContent]"), errs)
        await b.close()
asyncio.run(main())
