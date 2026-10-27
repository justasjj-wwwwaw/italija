import asyncio, sys, json
sys.path.insert(0,'/tmp/claude-0/-home-claude/c5f0fa83-c641-5b32-922d-d11e43d45947/scratchpad/chk')
from wx import payload
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright
JS=r'''()=>{
function parse(c){var m=c.match(/rgba?\(([^)]+)\)/);if(!m)return null;var p=m[1].split(/[ ,\/]+/).map(parseFloat);return {r:p[0],g:p[1],b:p[2],a:p.length>3&&!isNaN(p[3])?p[3]:1};}
function over(f,b){var a=f.a;return {r:f.r*a+b.r*(1-a),g:f.g*a+b.g*(1-a),b:f.b*a+b.b*(1-a),a:1};}
function lum(c){function ch(v){v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4);}return .2126*ch(c.r)+.7152*ch(c.g)+.0722*ch(c.b);}
function bgOf(el){var stack=[];for(var e=el;e&&e.nodeType===1;e=e.parentElement){var cs=getComputedStyle(e);var c=parse(cs.backgroundColor);if(c&&c.a>0)stack.push(c);if(c&&c.a===1)break;if(cs.backgroundImage!=='none'&&cs.backgroundImage.indexOf('gradient')<0&&false)break;}
 var base={r:255,g:255,b:255,a:1};for(var i=stack.length-1;i>=0;i--)base=over(stack[i],base);return base;}
var out=[],seen={};
var w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
while(w.nextNode()){var n=w.currentNode;if(!n.nodeValue.trim())continue;var el=n.parentElement;if(!el||el.closest('svg,script,style,[hidden]'))continue;
 var cs=getComputedStyle(el);if(cs.visibility==='hidden'||cs.display==='none')continue;var r=el.getBoundingClientRect();if(r.width===0||r.height===0)continue;
 var fg=parse(cs.color);var bg=bgOf(el);fg=over({r:fg.r,g:fg.g,b:fg.b,a:fg.a*parseFloat(cs.opacity||1)},bg);
 var L1=lum(fg),L2=lum(bg);var ratio=(Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
 var fs=parseFloat(cs.fontSize),bold=parseInt(cs.fontWeight)>=700;var large=fs>=24||(fs>=18.66&&bold);var need=large?3:4.5;
 if(ratio<need){var key=el.tagName+'.'+el.className+'|'+Math.round(ratio*100);if(seen[key])continue;seen[key]=1;out.push({t:n.nodeValue.trim().slice(0,40),cls:el.tagName+'.'+(el.className&&el.className.baseVal!==undefined?el.className.baseVal:el.className),ratio:+ratio.toFixed(2),need:need,fs:fs,fg:cs.color,bg:'rgb('+Math.round(bg.r)+','+Math.round(bg.g)+','+Math.round(bg.b)+')'});}}
return out;}'''
MOCK=True
async def run(url,vw,vh,label,extra=None):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':vw,'height':vh})
        pg=await ctx.new_page()
        await pg.route('**/*wikipedia.org/**',lambda r:r.abort())
        async def om(r):
            if MOCK:
                q=parse_qs(urlparse(r.request.url).query)
                return await r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps(payload(q)))
            await r.abort()
        await pg.route('**/api.open-meteo.com/**',om)
        await pg.goto(url,wait_until='load'); await pg.wait_for_timeout(1500)
        await pg.evaluate("document.querySelectorAll('details.day,details.stay-more').forEach(d=>d.open=true)")
        await pg.add_style_tag(content='*{transition:none!important;animation:none!important}')
        await pg.wait_for_timeout(300)
        res=await pg.evaluate(JS)
        print(label,'issues:',len(res))
        for x in res[:25]: print('  ',x)
        await b.close()
async def main():
    base='http://localhost:8765/index.html'
    await run(base+'?t=2026-09-01T10:00',1280,900,'static 1280')
    await run(base+'?t=2026-09-01T10:00',360,740,'static 360')
    await run(base+'?t=2026-10-31T12:10',360,740,'live 3d 12:10 @360')
    global MOCK
    MOCK=False
    await run(base+'?t=2026-09-01T10:00',360,740,'snapshot-only @360')
asyncio.run(main())
