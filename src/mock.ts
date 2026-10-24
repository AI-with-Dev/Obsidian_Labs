// SAMPLE DATA — enable with VITE_API_BASE_URL=mock for receipt-screen previews.
import {Receipt,Summary,CategoryTotal,Answer,Filters} from './types'
import {Lang,dictFor} from './i18n'

const img=(v:string,t:number,type='income')=>'data:image/svg+xml;utf8,'+encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="400" height="560"><rect width="400" height="560" fill="#fffef8" stroke="#999"/><text x="30" y="60" font-size="24" font-family="sans-serif" font-weight="bold">${type==='income'?'PAYMENT RECEIPT':'EXPENSE VOUCHER'}</text><text x="30" y="100" font-size="20" font-family="sans-serif">${v}</text><text x="30" y="150" font-size="26" font-family="sans-serif" fill="${type==='income'?'#064e3b':'#b91c1c'}">${type==='income'?'+':'-'} INR ${t}</text></svg>`)

const mk=(id:string,vendor:string,date:string,category:string,total:number,status:Receipt['status'],items:Receipt['items'],type:Receipt['type']='income',x:Partial<Receipt>={}):Receipt=>({
  id,
  vendor,
  date,
  currency:'INR',
  items,
  total,
  category,
  status,
  type,
  fileName:id+'.png',
  fileUrl:img(vendor,total,type),
  flags:[],
  ...x
})

let db:Receipt[]=[
  mk('r1','Sharma Stationery Store (Counter Sale)','2026-10-03','retail_sales',12450,'confirmed',[{name:'Counter sales (retail bills)',amount:12450}],'income'),
  mk('r2','Gupta Book Depot (Wholesale Collection)','2026-10-06','wholesale_collection',1860,'confirmed',[{name:'Notebooks batch collection',amount:1200},{name:'Packing boxes',amount:660}],'income'),
  mk('r3','Modern Public School (Bulk Books)','2026-10-09','advance_payment',2400,'confirmed',[{name:'Advance for library books',amount:2400}],'income'),
  mk('r4','Rajasthan Coaching Academy','2026-10-12','credit_recovery',3120,'confirmed',[{name:'Udhar / Credit settlement',amount:3120}],'income'),
  mk('r5','Mahalaxmi Stationery (Cash Collection)','','retail_sales',940,'draft',[{name:'General retail cash',amount:940}],'income',{flags:['date']}),
  mk('r6','Gupta Book Depot (Repeat Entry)','2026-10-06','wholesale_collection',1860,'duplicate',[{name:'Notebooks batch collection',amount:1200},{name:'Packing boxes',amount:660}],'income',{duplicateOfId:'r2'}),
  mk('r7','City Cargo Tempo (Goods Delivery Fee)','2026-10-14','transport',850,'confirmed',[{name:'Delivery freight to godown',amount:850}],'expense'),
]

const conf=()=>db.filter(r=>r.status==='confirmed')
const confIncome=()=>conf().filter(r=>r.type!=='expense')
const confExpense=()=>conf().filter(r=>r.type==='expense')

const sum=(rs:Receipt[])=>rs.reduce((a,r)=>a+(r.total||0),0)
const group=(k:(r:Receipt)=>string)=>{
  const g:Record<string,Receipt[]>={}
  confIncome().forEach(r=>(g[k(r)]??=[]).push(r))
  return Object.entries(g).map(([key,rs])=>({key,amount:sum(rs)})).sort((a,b)=>b.amount-a.amount)
}
const find=(id:string)=>{const r=db.find(x=>x.id===id);if(!r)throw new Error('not found');return r}
const put=(id:string,p:Partial<Receipt>)=>{const r=Object.assign(find(id),p);return {...r}}

function generatePdfDoc(): string {
  const totInc = sum(confIncome())
  const totExp = sum(confExpense())
  const items = conf().slice(0, 30)

  let stream = 'BT /F1 16 Tf 50 780 Td (Vyapar Mitra - Official Payment & Collections Summary) Tj\n'
  stream += '/F2 10 Tf 0 -22 Td (Export Format: Official PDF | Generated: ' + new Date().toISOString().slice(0, 10) + ') Tj\n'
  stream += '/F1 12 Tf 0 -24 Td (TOTAL MONEY RECEIVED: (+) INR ' + totInc.toLocaleString('en-IN') + ') Tj\n'
  if (totExp > 0) {
    stream += '/F1 10 Tf 0 -18 Td (Total Outgoing Expenses: (-) INR ' + totExp.toLocaleString('en-IN') + ') Tj\n'
  }
  stream += '/F1 10 Tf 0 -28 Td (Date         Type      Customer / Payer                  Amount) Tj\n'
  stream += '/F2 9 Tf 0 -5 Td (--------------------------------------------------------------------------------) Tj\n'

  items.forEach(r => {
    const isInc = r.type !== 'expense'
    const sign = isInc ? '(+) ' : '(-) '
    const d = (r.date || '----').padEnd(12)
    const t = isInc ? 'Received ' : 'Expense  '
    const name = (r.vendor || 'Unknown Customer').slice(0, 32).padEnd(34)
    const amt = sign + 'INR ' + (r.total || 0).toLocaleString('en-IN')
    const line = `${d} ${t} ${name} ${amt}`
    stream += `0 -18 Td (${line.replace(/[()\\]/g, '')}) Tj\n`
  })

  stream += 'ET'

  const o1 = '1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n'
  const o2 = '2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n'
  const o3 = '3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>\nendobj\n'
  const o4 = '4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n'
  const o5 = '5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n'
  const o6 = `6 0 obj\n<< /Length ${stream.length} >>\nstream\n${stream}\nendstream\nendobj\n`

  const header = '%PDF-1.4\n'
  const p1 = header.length
  const p2 = p1 + o1.length
  const p3 = p2 + o2.length
  const p4 = p3 + o3.length
  const p5 = p4 + o4.length
  const p6 = p5 + o5.length
  const xrefPos = p6 + o6.length

  const pad = (n: number) => String(n).padStart(10, '0') + ' 00000 n \n'
  const xref = `xref\n0 7\n0000000000 65535 f \n${pad(p1)}${pad(p2)}${pad(p3)}${pad(p4)}${pad(p5)}${pad(p6)}`
  const trailer = `trailer\n<< /Size 7 /Root 1 0 R >>\nstartxref\n${xrefPos}\n%%EOF`

  return header + o1 + o2 + o3 + o4 + o5 + o6 + xref + trailer
}

export const m={
  upload:(f:File)=>{const r=mk('r'+(db.length+1),'','','other',0,'draft',[],'income',{fileName:f.name,fileUrl:URL.createObjectURL(f)});r.total=null;db=[r,...db];return {id:r.id}},
  extract:(id:string)=>put(id,{vendor:'Shri Krishna Books (Counter)',date:'',total:780,category:'retail_sales',type:'income',items:[{name:'Registers & Notebooks',amount:520},{name:'Gel pens box',amount:260}],flags:['date']}),
  get:(id:string)=>({...find(id)}),
  save:(r:Receipt)=>put(r.id,r),
  confirm:(id:string)=>put(id,{status:'confirmed'}),
  discard:(id:string)=>{db=db.filter(r=>r.id!==id)},
  deleteReceipt:(id:string)=>{db=db.filter(r=>r.id!==id)},
  keep:(id:string)=>put(id,{status:'draft',duplicateOfId:undefined}),
  list:(f:Filters)=>db.filter(r=>(f.status==='confirmed'?r.status==='confirmed':f.status==='pending'?r.status!=='confirmed':true)
    &&(!f.type||r.type===f.type)
    &&(!f.q||(r.vendor+r.items.map(i=>i.name).join(' ')).toLowerCase().includes(f.q.toLowerCase()))
    &&(!f.from||r.date>=f.from)&&(!f.to||r.date<=f.to)&&(!f.vendor||r.vendor===f.vendor)).sort((a,b)=>b.date.localeCompare(a.date)),
  summary:():Summary=>({
    totalReceived:sum(confIncome()),
    totalSpent:sum(confExpense()),
    totalBalance:sum(confIncome())-sum(confExpense()),
    confirmedCount:conf().length,
    reviewCount:db.length-conf().length,
    topVendors:group(r=>r.vendor).slice(0,4).map(g=>({vendor:g.key,amount:g.amount})),
    topCustomers:group(r=>r.vendor).slice(0,4).map(g=>({customer:g.key,amount:g.amount}))
  }),
  categories:():CategoryTotal[]=>group(r=>r.category).map(g=>({category:g.key,amount:g.amount})),
  csv:()=>['Vendor,Date,Category,Currency,Total',...conf().map(r=>`"${r.vendor}",${r.date},${r.category},${r.currency},${r.total}`)].join('\n'),
  pdf:()=>generatePdfDoc(),
  ask:(q:string,lang:Lang):Answer=>{
    const s=q.toLowerCase(),d=dictFor(lang),has=(...w:string[])=>w.some(x=>s.includes(x))
    const A=(k:string,v:Record<string,string|number>,receipts:Receipt[]):Answer=>({answer:d[k].replace(/\{(\w+)\}/g,(_,x)=>String(v[x])),supported:true,receipts})
    const f=(n:number)=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR'}).format(n)
    if(has('waiting','review','जांच','जाँच','सत्यापन')){const p=db.filter(r=>r.status!=='confirmed');return A('qa.ans.review',{n:p.length},p)}
    if(has('between','के बीच')){const rs=confIncome().filter(r=>r.date>='2026-10-01'&&r.date<='2026-10-15');return A('qa.ans.dates',{amount:f(sum(rs))},rs)}
    if(has('customer','shop','vendor','दुकान','ग्राहक')){const g=group(r=>r.vendor)[0];return A('qa.ans.vendor',{name:g.key,amount:f(g.amount)},conf().filter(r=>r.vendor===g.key))}
    if(has('total','कुल','received','आवक','कमाई'))return A('qa.ans.total',{amount:f(sum(confIncome())),n:confIncome().length},confIncome())
    return {answer:d['qa.unsupported'],supported:false,receipts:[]}
  }
}
