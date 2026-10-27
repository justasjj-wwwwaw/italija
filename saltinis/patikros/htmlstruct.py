import re, sys, collections
from html.parser import HTMLParser
h=open('/home/claude/italija.tingek/index.html',encoding='utf-8').read()
class P(HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True); s.ids=collections.Counter(); s.refs=[]; s.heads=[]; s.imgs=[]; s.blank=[]; s.uses=[]; s.stack=[]; s.errs=[]; s.btn=[]
        s.VOID={'meta','link','img','br','hr','input','source','path','circle','rect','ellipse','line','use','polyline','polygon','stop','wbr'}
    def handle_starttag(s,t,a):
        a=dict(a)
        if 'id' in a: s.ids[a['id']]+=1
        for k in ('aria-labelledby','aria-describedby','aria-controls'):
            if k in a: s.refs+= [(k,x) for x in a[k].split()]
        if re.fullmatch(r'h[1-6]',t): s.heads.append(int(t[1]))
        if t=='img': s.imgs.append(a)
        if t=='a' and a.get('target')=='_blank': s.blank.append(a)
        if t=='use': s.uses.append(a.get('href') or a.get('xlink:href'))
        if t=='a' and 'href' in a and a['href'].startswith('#') and a['href']!='#': s.refs.append(('href',a['href'][1:]))
        if t=='button' and 'type' not in a: s.btn.append(a)
        if t not in s.VOID: s.stack.append(t)
    def handle_startendtag(s,t,a): 
        a=dict(a)
        if 'id' in a: s.ids[a['id']]+=1
        if t=='use': s.uses.append(a.get('href') or a.get('xlink:href'))
    def handle_endtag(s,t):
        if t in s.VOID: return
        if not s.stack or s.stack[-1]!=t:
            s.errs.append(f'mismatch </{t}> stack top={s.stack[-3:]} line={s.getpos()[0]}')
            if t in s.stack:
                while s.stack and s.stack.pop()!=t: pass
        else: s.stack.pop()
p=P(); p.feed(h)
print('dup ids:',[k for k,v in p.ids.items() if v>1])
missing=[(k,x) for k,x in p.refs if x not in p.ids]
print('dangling refs:',missing[:10], len(missing))
print('use targets missing:',[u for u in p.uses if u and u.startswith('#') and u[1:] not in p.ids][:10])
# heading order
bad=[(a,b) for a,b in zip(p.heads,p.heads[1:]) if b-a>1]
print('heading jumps:',bad, 'h1 count',p.heads.count(1), 'seq start',p.heads[:8])
print('img w/o alt:',[i for i in p.imgs if 'alt' not in i][:3],'| imgs',len(p.imgs),'| w/o width/height:',sum(1 for i in p.imgs if 'width' not in i or 'height' not in i))
print('target=_blank w/o noopener:',[a.get('href') for a in p.blank if 'noopener' not in (a.get('rel') or '')][:5],len(p.blank))
print('buttons w/o type:',len(p.btn))
print('unclosed:',p.stack,'errors:',p.errs[:6])
print('lang:',re.search(r'<html[^>]*>',h).group(0))
print('doctype ok:',h.lstrip().lower().startswith('<!doctype html>'))
print('external hosts:',sorted(set(re.findall(r'https?://([a-z0-9.-]+)',re.sub(r'<svg.*?</svg>','',h,flags=re.S)))) )
