import io, re, sys, pathlib
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset
G=pathlib.Path('tools/gfonts/ofl'); OUT=pathlib.Path('tools/fonts_out2'); OUT.mkdir(exist_ok=True)
html=open('/home/claude/italija.tingek/index.html',encoding='utf-8').read()
chars=set(html)|set(chr(c) for c in range(0x20,0x7f))|set(chr(c) for c in range(0xa0,0x180))|set('–—‘’“”„…•·°×−≈≤≥€→')
chars={c for c in chars if ord(c)>=0x20 and c not in '​️'}
print('chars',len(chars))
FEAT=['kern','ccmp','locl','mark','mkmk','tnum','lnum','pnum']
def make(src, limits, name, only=None):
    f=TTFont(G/src)
    f=instancer.instantiateVariableFont(f,limits)
    b=io.BytesIO(); f.save(b); b.seek(0); f=TTFont(b)
    o=subset.Options(); o.layout_features=FEAT; o.flavor='woff'; o.hinting=False; o.desubroutinize=True
    o.notdef_outline=True; o.name_IDs=[1,2,3,4,6]; o.drop_tables+=['DSIG']
    s=subset.Subsetter(o); s.populate(text=''.join(sorted(only or chars))); s.subset(f)
    f.flavor='woff'; p=OUT/name; f.save(p); print(name,p.stat().st_size,'B', 'fvar' in f and [(a.axisTag,a.minValue,a.maxValue) for a in f['fvar'].axes])
#make('atkinsonhyperlegiblenext/AtkinsonHyperlegibleNext[wght].ttf',{'wght':(400,800)},'atkinson-next.woff')
make('literata/Literata[opsz,wght].ttf',{'opsz':24,'wght':(500,700)},'literata.woff')
make('literata/Literata-Italic[opsz,wght].ttf',{'opsz':24,'wght':500},'literata-italic.woff',only=set(chr(c) for c in range(0x20,0x7f))|set('ąčęėįšųūžĄČĘĖĮŠŲŪŽ'))

FEAT[:]=['kern','ccmp','locl','mark','mkmk','tnum','pnum','case']
make('inter/Inter[opsz,wght].ttf',{'opsz':14,'wght':(400,800)},'inter.woff')
make('sourcesans3/SourceSans3[wght].ttf',{'wght':(400,800)},'source-sans.woff')
