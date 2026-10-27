// compare JS NOAA (from the page) with python values for the trip days
const fs=require('fs');const src=fs.readFileSync(process.argv[2],'utf8');
const pick=(name)=>{const i=src.indexOf('function '+name+'(');let d=0,j=src.indexOf('{',i);for(let k=j;k<src.length;k++){if(src[k]=='{')d++;if(src[k]=='}'){d--;if(!d)return src.slice(i,k+1);}}};
eval(pick('lastSun')+pick('romeOff')+pick('sunUT'));
const cases=JSON.parse(process.argv[3]);let bad=0;
for(const c of cases){const [y,m,d]=c.iso.split('-').map(Number);const doy=Math.round((Date.UTC(y,m-1,d)-Date.UTC(y,0,0))/864e5),tz=romeOff(y,m-1,d);
 const mm=h=>Math.round(((h+tz)%24)*60);const r=mm(sunUT(doy,c.lat,c.lon,90.833,true)),s=mm(sunUT(doy,c.lat,c.lon,90.833,false)),k=mm(sunUT(doy,c.lat,c.lon,96,false));
 const ok=Math.abs(r-c.rise)<=1&&Math.abs(s-c.set)<=1&&Math.abs(k-c.dusk)<=1;if(!ok)bad++;console.log(c.iso,'tz',tz,'js',r,s,k,'py',c.rise,c.set,c.dusk,ok?'OK':'DIFF');}
for(const [y,m,d] of [[2026,9,24],[2026,9,25],[2026,9,26],[2026,2,28],[2026,2,29],[2027,2,28]])console.log('offset',y,m+1,d,romeOff(y,m,d));
process.exit(bad?1:0);
