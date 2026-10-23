// MOCK BACKEND — delete/ignore once VITE_API_BASE_URL points to the real API. Totals here stand in for server-side math.
import {Receipt,Summary,CategoryTotal,Answer,Filters} from './types'
import {Lang,dictFor} from './i18n'
const img=(v:string,t:number)=>'data:image/svg+xml;utf8,'+encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="400" height="560"><rect width="400" height="560" fill="#fffef8" stroke="#999"/><text x="30" y="60" font-size="26" font-family="monospace">${v}</text><text x="30" y="120" font-size="20" font-family="monospace">TOTAL ${t}</text></svg>`)
const mk=(id:string,vendor:string,date:string,category:string,total:number,status:Receipt['status'],items:Receipt['items'],x:Partial<Receipt>={}):Receipt=>({id,vendor,date,currency:'INR',items,total,category,status,fileName:id+'.png',fileUrl:img(vendor,total),flags:[],...x})
let db:Receipt[]=[
 mk('r1','Sharma Wholesale Traders','2026-10-03','inventory',12450,'confirmed',[{name:'Stock (assorted)',amount:12450}]),
 mk('r2','Ganesh Packaging','2026-10-06','packaging',1860,'confirmed',[{name:'Bags',amount:1200},{name:'Tape',amount:660}]),
 mk('r3','City Transport','2026-10-09','transport',2400,'confirmed',[{name:'Goods delivery',amount:2400}]),
 mk('r4','Rajasthan Power','2026-10-12','utilities',3120,'confirmed',[{name:'Electricity bill',amount:3120}]),
 mk('r5','Mahalaxmi Hardware','','repairs',940,'draft',[{name:'Shutter lock',amount:940}],{flags:['date']}),
 mk('r6','Ganesh Packaging','2026-10-06','packaging',1860,'duplicate',[{name:'Bags',amount:1200},{name:'Tape',amount:660}],{duplicateOfId:'r2'}),
]
const conf=()=>db.filter(r=>r.status==='confirmed')
const sum=(rs:Receipt[])=>rs.reduce((a,r)=>a+(r.total||0),0)
const group=(k:(r:Receipt)=>string)=>{const g:Record<string,Receipt[]>={};conf().forEach(r=>(g[k(r)]??=[]).push(r));return Object.entries(g).map(([key,rs])=>({key,amount:sum(rs)})).sort((a,b)=>b.amount-a.amount)}
const find=(id:string)=>{const r=db.find(x=>x.id===id);if(!r)throw new Error('not found');return r}
const put=(id:string,p:Partial<Receipt>)=>{const r=Object.assign(find(id),p);return {...r}}
export const m={
 upload:(f:File)=>{const r=mk('r'+(db.length+1),'','','other',0,'draft',[],{fileName:f.name,fileUrl:URL.createObjectURL(f)});r.total=null;db=[r,...db];return {id:r.id}},
 extract:(id:string)=>put(id,{vendor:'Kisan General Store',date:'',total:780,category:'inventory',items:[{name:'Rice 10 kg',amount:520},{name:'Oil 1 L',amount:260}],flags:['date']}),
 get:(id:string)=>({...find(id)}),
 save:(r:Receipt)=>put(r.id,r),
 confirm:(id:string)=>put(id,{status:'confirmed'}),
 discard:(id:string)=>{db=db.filter(r=>r.id!==id)},
 keep:(id:string)=>put(id,{status:'draft',duplicateOfId:undefined}),
 list:(f:Filters)=>db.filter(r=>(f.status==='confirmed'?r.status==='confirmed':f.status==='pending'?r.status!=='confirmed':true)
   &&(!f.q||(r.vendor+r.items.map(i=>i.name).join(' ')).toLowerCase().includes(f.q.toLowerCase()))
   &&(!f.from||r.date>=f.from)&&(!f.to||r.date<=f.to)&&(!f.category||r.category===f.category)&&(!f.vendor||r.vendor===f.vendor)).sort((a,b)=>b.date.localeCompare(a.date)),
 summary:():Summary=>({totalSpent:sum(conf()),confirmedCount:conf().length,reviewCount:db.length-conf().length,topVendors:group(r=>r.vendor).slice(0,3).map(g=>({vendor:g.key,amount:g.amount}))}),
 categories:():CategoryTotal[]=>group(r=>r.category).map(g=>({category:g.key,amount:g.amount})),
 csv:()=>['Vendor,Date,Category,Currency,Total',...conf().map(r=>`"${r.vendor}",${r.date},${r.category},${r.currency},${r.total}`)].join('\n'),
 ask:(q:string,lang:Lang):Answer=>{
  const s=q.toLowerCase(),d=dictFor(lang),has=(...w:string[])=>w.some(x=>s.includes(x))
  const A=(k:string,v:Record<string,string|number>,receipts:Receipt[]):Answer=>({answer:d[k].replace(/\{(\w+)\}/g,(_,x)=>String(v[x])),supported:true,receipts})
  const f=(n:number)=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR'}).format(n)
  if(has('waiting','review','जांच','जाँच')){const p=db.filter(r=>r.status!=='confirmed');return A('qa.ans.review',{n:p.length},p)}
  if(has('between','के बीच')){const rs=conf().filter(r=>r.date>='2026-10-01'&&r.date<='2026-10-15');return A('qa.ans.dates',{amount:f(sum(rs))},rs)}
  if(has('shop','vendor','दुकान')){const g=group(r=>r.vendor)[0];return A('qa.ans.vendor',{name:g.key,amount:f(g.amount)},conf().filter(r=>r.vendor===g.key))}
  if(has('type','category','प्रकार')){const g=group(r=>r.category)[0];return A('qa.ans.category',{name:d['cat.'+g.key],amount:f(g.amount)},conf().filter(r=>r.category===g.key))}
  if(has('total','कुल'))return A('qa.ans.total',{amount:f(sum(conf())),n:conf().length},conf())
  return {answer:d['qa.unsupported'],supported:false,receipts:[]}}
}
