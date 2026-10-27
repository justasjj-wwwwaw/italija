import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':360,'height':740},java_script_enabled=False)
        pg=await ctx.new_page()
        await pg.goto('http://localhost:8765/index.html',wait_until='load')
        await pg.wait_for_timeout(400)
        print('details open:',await pg.evaluate("[...document.querySelectorAll('details.day')].map(d=>d.open)") if False else 'n/a (js off)')
        h=await pg.content()
        import re
        print('details total:',len(re.findall(r'<details[^>]*class="day',h)),'open attr:',len(re.findall(r'<details[^>]*class="day[^>]*\sopen',h)))
        print('ph slots visible:',await pg.locator('.ph').first.is_visible())
        print('livebar hidden:',not await pg.locator('#livebar').is_visible())
        print('scrollW',await pg.evaluate("document.documentElement.scrollWidth") if False else '')
        await pg.screenshot(path='nojs.png',full_page=False)
        await b.close()
asyncio.run(main())
