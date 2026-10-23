import {useCallback,useEffect,useState,ReactNode} from 'react'
import {useI18n,money,day} from './i18n'
import * as api from './api'
import {CATEGORIES,Receipt,Filters,Answer} from './types'

const btn='min-h-14 px-6 rounded-xl text-lg font-semibold focus-visible:outline-4 focus-visible:outline-amber-500 disabled:opacity-50 inline-flex items-center justify-center'
const primary=`${btn} bg-emerald-800 text-white hover:bg-emerald-900`
const ghost=`${btn} border-2 border-emerald-800 text-emerald-900 bg-white hover:bg-emerald-50`
const field='w-full min-h-14 px-4 rounded-xl border-2 border-stone-500 bg-white text-lg disabled:bg-stone-100'
const card='block rounded-2xl bg-white border border-stone-300 p-5'
const h1='text-3xl font-bold mb-2'
const h2='text-2xl font-bold mb-3'

function useHash(){
  const get=()=>location.hash.slice(1)||'/'
  const [h,s]=useState(get)
  useEffect(()=>{const f=()=>{s(get());scrollTo(0,0)};addEventListener('hashchange',f);return()=>removeEventListener('hashchange',f)},[])
  return h
}
function useLoad<T>(fn:()=>Promise<T>,deps:unknown[]){
  const [s,set]=useState<{d?:T;e?:boolean;l:boolean}>({l:true})
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run=useCallback(()=>{set(p=>({...p,e:false,l:true}));fn().then(d=>set({d,l:false}),()=>set({e:true,l:false}))},deps)
  useEffect(run,[run])
  return {...s,run}
}
function State({l,e,run,children}:{l:boolean;e?:boolean;run:()=>void;children:ReactNode}){
  const {t}=useI18n()
  if(l)return <p role="status" className="text-xl py-8">{t('common.loading')}</p>
  if(e)return <div role="alert" className={card}><p className="text-xl mb-4">{t('common.error')}</p><button className={primary} onClick={run}>{t('common.retry')}</button></div>
  return <>{children}</>
}
const icon={draft:'✎',confirmed:'✓',duplicate:'⚠'}
function Badge({s}:{s:Receipt['status']}){
  const {t}=useI18n()
  return <span className="inline-flex gap-1 rounded-full border-2 border-stone-700 bg-stone-50 px-3 text-base font-semibold"><span aria-hidden>{icon[s]}</span>{t('status.'+s)}</span>
}
function RList({rs}:{rs:Receipt[]}){
  const {t,lang}=useI18n()
  if(!rs.length)return <p className="text-lg">{t('lg.empty')}</p>
  return <ul className="space-y-3">{rs.map(r=><li key={r.id}>
    <a href={`#/receipt/${r.id}`} className={`${card} flex flex-wrap items-center justify-between gap-2 hover:border-emerald-800`}>
      <span><b className="block text-xl">{r.vendor||'—'}</b><span className="text-stone-700">{r.date?day(r.date,lang):'—'} · {t('cat.'+r.category)}</span></span>
      <span className="text-right"><b className="block text-xl">{r.total==null?'—':money(r.total,lang,r.currency)}</b>{r.status!=='confirmed'&&<Badge s={r.status}/>}</span>
    </a></li>)}</ul>
}
function Rows({rows}:{rows:{label:string;amount:number;href:string}[]}){
  const {lang}=useI18n()
  return <ul className="space-y-2">{rows.map(r=><li key={r.label}><a href={r.href} className={`${card} flex justify-between gap-3 text-lg hover:border-emerald-800`}><span>{r.label}</span><b>{money(r.amount,lang)}</b></a></li>)}</ul>
}

function Home(){
  const {t,lang}=useI18n()
  const q=useLoad(()=>Promise.all([api.summary(),api.categories(),api.list({status:'pending'})]),[])
  const s=q.d?.[0],c=q.d?.[1],p=q.d?.[2]
  return <State {...q}>{s&&c&&p&&<div className="space-y-8">
    <h1 className={h1}>{t('home.title')}</h1>
    {s.confirmedCount===0&&<div className={card}><p className="mb-4 text-xl">{t('home.empty')}</p><a href="#/upload" className={primary}>{t('home.add')}</a></div>}
    <div className="grid gap-4 sm:grid-cols-3">
      <div className={card}><p>{t('home.spent')}</p><p className="text-3xl font-bold">{money(s.totalSpent,lang)}</p></div>
      <a href="#/ledger" className={`${card} hover:border-emerald-800`}><p>{t('home.count')}</p><p className="text-3xl font-bold">{s.confirmedCount}</p></a>
      <div className={card}><p>{t('home.review')}</p><p className="text-3xl font-bold">{s.reviewCount}</p></div>
    </div>
    <section><h2 className={h2}>{t('home.waiting')}</h2>{p.length?<RList rs={p}/>:<p className="text-lg">{t('home.none')}</p>}</section>
    <section><h2 className={h2}>{t('home.cats')}</h2><Rows rows={c.map(x=>({label:t('cat.'+x.category),amount:x.amount,href:`#/ledger?category=${x.category}`}))}/></section>
    <section><h2 className={h2}>{t('home.vendors')}</h2><Rows rows={s.topVendors.map(v=>({label:v.vendor,amount:v.amount,href:`#/ledger?vendor=${encodeURIComponent(v.vendor)}`}))}/></section>
  </div>}</State>
}

const OK=['image/jpeg','image/png','application/pdf']
function Upload(){
  const {t}=useI18n()
  const [file,setFile]=useState<File|null>(null)
  const [st,setSt]=useState<'idle'|'up'|'read'|'done'|'err'>('idle')
  const [msg,setMsg]=useState(''),[id,setId]=useState('')
  const busy=st==='up'||st==='read'
  const pick=(f?:File)=>{setFile(null);setMsg('');setSt('idle');if(!f)return;if(!OK.includes(f.type)){setMsg(t('up.badType'));setSt('err');return}setFile(f)}
  const send=async()=>{
    if(!file||busy)return
    try{setSt('up');const r=await api.upload(file);setSt('read');await api.extract(r.id);setId(r.id);setSt('done')}
    catch{setMsg(t('up.fail'));setSt('err')}
  }
  return <div className="space-y-6 max-w-2xl">
    <h1 className={h1}>{t('up.title')}</h1>
    <p className="text-xl">{t('up.help')}</p>
    <label className={`${ghost} cursor-pointer w-full`}>{t('up.choose')}
      <input type="file" accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf" className="sr-only" disabled={busy} onChange={e=>pick(e.target.files?.[0])}/></label>
    {file&&<p className={card}><span className="block text-stone-700">{t('up.selected')}</span><b className="break-all">{file.name}</b></p>}
    <div role="status" aria-live="polite" className="text-xl">
      {st==='up'&&t('up.sending')}{st==='read'&&t('up.reading')}
      {st==='done'&&<span>✓ {t('up.done')}</span>}
    </div>
    {st==='err'&&<p role="alert" className="rounded-xl border-2 border-red-800 bg-red-50 p-4 text-lg">⚠ {msg}</p>}
    {busy&&<progress className="w-full h-3" aria-hidden/>}
    {st==='done'?<a href={`#/receipt/${id}`} className={`${primary} w-full`}>{t('up.next')} →</a>
     :<button className={`${primary} w-full`} disabled={!file||busy} onClick={send}>{st==='err'&&file?t('common.retry'):t('up.send')}</button>}
  </div>
}

function F({label,warn,children}:{label:string;warn?:boolean;children:ReactNode}){
  const {t}=useI18n()
  return <label className="block"><span className="mb-1 block text-lg font-semibold">{label}</span>{children}
    {warn&&<span className="mt-1 block font-semibold text-amber-900">⚠ {t('rv.unclear')}</span>}</label>
}
function Side({x,h}:{x:Receipt;h:string}){
  const {lang,t}=useI18n()
  return <div className={card}><h3 className="mb-2 text-xl font-bold">{h}</h3>
    <img src={x.fileUrl} alt="" className="mb-3 max-h-48 rounded-lg border"/>
    <p><b>{x.vendor||'—'}</b></p><p>{x.date?day(x.date,lang):'—'}</p><p>{x.total==null?'—':money(x.total,lang,x.currency)}</p><p>{t('cat.'+x.category)}</p></div>
}
function Dup({r,busy,onDiscard,onKeep}:{r:Receipt;busy:boolean;onDiscard:()=>void;onKeep:()=>void}){
  const {t}=useI18n()
  const o=useLoad(()=>api.get(r.duplicateOfId!),[r.duplicateOfId])
  return <section className="space-y-4">
    <h2 className={h2}>{t('dp.title')}</h2><p className="text-xl">{t('dp.help')}</p>
    <State {...o}><div className="grid gap-4 sm:grid-cols-2"><Side x={r} h={t('dp.new')}/>{o.d&&<Side x={o.d} h={t('dp.old')}/>}</div></State>
    <div className="flex flex-col gap-3 sm:flex-row">
      <button className={ghost} disabled={busy} onClick={onDiscard}>{t('dp.discard')}</button>
      <button className={primary} disabled={busy} onClick={onKeep}>{t('dp.keep')}</button></div>
  </section>
}

function ReceiptPage({id}:{id:string}){
  const {t}=useI18n()
  const q=useLoad(()=>api.get(id),[id])
  const [f,setF]=useState<Receipt|null>(null)
  const [note,setNote]=useState(''),[busy,setBusy]=useState(false),[err,setErr]=useState(false),[gone,setGone]=useState(false)
  useEffect(()=>{if(q.d)setF(q.d)},[q.d])
  const set=(p:Partial<Receipt>)=>setF(x=>x&&{...x,...p})
  const act=async(fn:()=>Promise<Receipt|void>,ok:string)=>{
    if(busy)return
    setBusy(true);setErr(false);setNote('')
    try{const r=await fn();if(r)setF(r);setNote(t(ok))}catch{setErr(true)}
    setBusy(false)
  }
  const ro=f?.status==='confirmed'
  return <State {...q}>{gone?<div className="space-y-4"><p className="text-xl">✓ {t('rv.gone')}</p><a className={primary} href="#/">{t('rv.goHome')}</a></div>
  :f&&<div className="space-y-6">
    <a href="#/" className="text-lg underline">{t('common.back')}</a>
    <div className="flex flex-wrap items-center gap-3"><h1 className="text-3xl font-bold">{ro?t('rv.titleDone'):t('rv.title')}</h1><Badge s={f.status}/></div>
    {f.status==='duplicate'?<Dup r={f} busy={busy}
      onDiscard={()=>act(async()=>{await api.discard(id);setGone(true)},'rv.gone')}
      onKeep={()=>act(()=>api.keepSeparate(id),'dp.kept')}/>:<>
    {!ro&&<p className="rounded-xl border-2 border-amber-600 bg-amber-50 p-4 text-lg">⚠ {t('rv.warn')}</p>}
    <div className="grid gap-6 lg:grid-cols-2 lg:items-start">
      <details open className={card}><summary className="min-h-12 cursor-pointer text-xl font-semibold">{t('rv.original')}</summary>
        {f.fileName.toLowerCase().endsWith('.pdf')?null:<img src={f.fileUrl} alt={t('rv.original')} className="my-3 w-full rounded-lg border"/>}
        <a href={f.fileUrl} target="_blank" rel="noreferrer" className="text-lg underline">{t('rv.open')}</a></details>
      <fieldset disabled={ro||busy} className={`${card} space-y-5`}>
        <F label={t('rv.vendor')} warn={!ro&&(f.flags.includes('vendor')||!f.vendor)}><input className={field} value={f.vendor} onChange={e=>set({vendor:e.target.value})}/></F>
        <F label={t('rv.date')} warn={!ro&&(f.flags.includes('date')||!f.date)}><input type="date" className={field} value={f.date} onChange={e=>set({date:e.target.value})}/></F>
        <F label={t('rv.currency')}><select className={field} value={f.currency} onChange={e=>set({currency:e.target.value})}>{['INR','USD','EUR'].map(c=><option key={c}>{c}</option>)}</select></F>
        <div><p className="mb-1 text-lg font-semibold">{t('rv.items')}</p><div className="space-y-3">
          {f.items.map((it,i)=><div key={i} className="flex gap-2">
            <input aria-label={t('rv.item')} placeholder={t('rv.item')} className={field} value={it.name} onChange={e=>set({items:f.items.map((x,j)=>j===i?{...x,name:e.target.value}:x)})}/>
            <input aria-label={t('rv.amount')} placeholder={t('rv.amount')} type="number" inputMode="decimal" min="0" className={`${field} max-w-32`} value={it.amount} onChange={e=>set({items:f.items.map((x,j)=>j===i?{...x,amount:Number(e.target.value)}:x)})}/>
            {!ro&&<button type="button" aria-label={t('rv.removeItem')} className={`${ghost} px-4`} onClick={()=>set({items:f.items.filter((_,j)=>j!==i)})}>✕</button>}</div>)}
          {!ro&&<button type="button" className={ghost} onClick={()=>set({items:[...f.items,{name:'',amount:0}]})}>{t('rv.addItem')}</button>}</div></div>
        <F label={t('rv.total')} warn={!ro&&(f.flags.includes('total')||f.total==null)}><input type="number" inputMode="decimal" min="0" className={field} value={f.total??''} onChange={e=>set({total:e.target.value===''?null:Number(e.target.value)})}/></F>
        <F label={t('rv.category')}><select className={field} value={f.category} onChange={e=>set({category:e.target.value})}>{CATEGORIES.map(c=><option key={c} value={c}>{t('cat.'+c)}</option>)}</select></F>
      </fieldset>
    </div>
    <div role="status" aria-live="polite">
      {busy&&<p className="text-xl">{t('rv.saving')}</p>}
      {note&&<p className="rounded-xl border-2 border-emerald-800 bg-emerald-50 p-4 text-lg">✓ {note}</p>}
      {err&&<p role="alert" className="rounded-xl border-2 border-red-800 bg-red-50 p-4 text-lg">⚠ {t('common.error')}</p>}</div>
    {ro?<a href="#/ledger" className={primary}>{t('rv.goLedger')}</a>:<div className="space-y-3">
      <p className="text-lg">{t('rv.confirmHelp')}</p>
      <div className="flex flex-col gap-3 sm:flex-row">
        <button className={ghost} disabled={busy} onClick={()=>act(()=>api.save(f),'rv.saved')}>{t('rv.save')}</button>
        <button className={primary} disabled={busy} onClick={()=>act(async()=>{await api.save(f);return api.confirm(id)},'rv.confirmed')}>{t('rv.confirm')}</button></div></div>}
    </>}
  </div>}</State>
}

function Ledger({query}:{query:string}){
  const {t,lang}=useI18n()
  const p=new URLSearchParams(query)
  const blank:Filters={q:'',from:'',to:'',category:'',vendor:''}
  const [fl,setFl]=useState<Filters>({...blank,category:p.get('category')||'',vendor:p.get('vendor')||''})
  const [ex,setEx]=useState<'idle'|'busy'|'ok'|'err'>('idle')
  const vendors=useLoad(()=>api.summary(),[])
  const r=useLoad(()=>api.list({...fl,status:'confirmed'}),[JSON.stringify(fl)])
  const up=(k:keyof Filters,v:string)=>setFl(x=>({...x,[k]:v}))
  const doExport=async()=>{if(ex==='busy')return;setEx('busy');try{await api.exportCsv();setEx('ok')}catch{setEx('err')}}
  const vlist=Array.from(new Set([...(vendors.d?.topVendors.map(v=>v.vendor)??[]),...(fl.vendor?[fl.vendor]:[])]))
  return <div className="space-y-6">
    <div><h1 className={h1}>{t('lg.title')}</h1><p className="text-xl">{t('lg.help')}</p></div>
    <div className={`${card} grid gap-4 sm:grid-cols-2`}>
      <F label={t('lg.search')}><input type="search" className={field} value={fl.q} onChange={e=>up('q',e.target.value)}/></F>
      <F label={t('lg.category')}><select className={field} value={fl.category} onChange={e=>up('category',e.target.value)}><option value="">{t('cat.all')}</option>{CATEGORIES.map(c=><option key={c} value={c}>{t('cat.'+c)}</option>)}</select></F>
      <F label={t('lg.from')}><input type="date" className={field} value={fl.from} onChange={e=>up('from',e.target.value)}/></F>
      <F label={t('lg.to')}><input type="date" className={field} value={fl.to} onChange={e=>up('to',e.target.value)}/></F>
      <F label={t('lg.vendor')}><select className={field} value={fl.vendor} onChange={e=>up('vendor',e.target.value)}><option value="">{t('lg.allVendors')}</option>{vlist.map(v=><option key={v}>{v}</option>)}</select></F>
      <div className="flex items-end"><button className={ghost} onClick={()=>setFl(blank)}>{t('lg.clear')}</button></div>
    </div>
    <State {...r}><RList rs={r.d??[]}/></State>
    <div className="space-y-3"><button className={primary} disabled={ex==='busy'} onClick={doExport}>{t('lg.export')}</button>
      <div role="status" aria-live="polite" className="text-lg">{ex==='busy'&&t('lg.exporting')}{ex==='ok'&&`✓ ${t('lg.exportOk')}`}{ex==='err'&&`⚠ ${t('lg.exportErr')}`}</div>
      {ex==='err'&&<button className={ghost} onClick={doExport}>{t('common.retry')}</button>}</div>
    <span className="sr-only">{lang}</span>
  </div>
}

function Ask(){
  const {t,lang}=useI18n()
  const [q,setQ]=useState(''),[a,setA]=useState<Answer|null>(null),[l,setL]=useState(false),[e,setE]=useState(false)
  const go=async(text:string)=>{
    if(!text.trim()||l)return
    setQ(text);setL(true);setE(false)
    try{setA(await api.ask(text,lang))}catch{setE(true)}
    setL(false)
  }
  return <div className="max-w-2xl space-y-6">
    <div><h1 className={h1}>{t('qa.title')}</h1><p className="text-xl">{t('qa.help')}</p></div>
    <div className="flex flex-col gap-3">{[1,2,3,4,5].map(n=><button key={n} className={`${ghost} justify-start text-left`} disabled={l} onClick={()=>go(t('qa.ex'+n))}>{t('qa.ex'+n)}</button>)}</div>
    <div className="flex flex-col gap-3 sm:flex-row"><input className={field} aria-label={t('qa.placeholder')} placeholder={t('qa.placeholder')} value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>e.key==='Enter'&&go(q)}/>
      <button className={primary} disabled={l||!q.trim()} onClick={()=>go(q)}>{t('qa.send')}</button></div>
    <div role="status" aria-live="polite">
      {l&&<p className="text-xl">{t('qa.thinking')}</p>}
      {e&&<div role="alert" className={card}><p className="mb-3 text-lg">{t('common.error')}</p><button className={primary} onClick={()=>go(q)}>{t('common.retry')}</button></div>}
      {a&&!l&&!e&&<div className="space-y-4"><p className={`${card} text-xl font-semibold`}>{a.answer}</p>
        {a.supported&&a.receipts.length>0&&<><h2 className="text-xl font-bold">{t('qa.sources')}</h2><RList rs={a.receipts}/></>}</div>}
    </div>
  </div>
}

export default function App(){
  const {t,lang,setLang}=useI18n()
  const h=useHash()
  const [path,query='']=h.split('?')
  const rm=path.match(/^\/receipt\/(.+)$/)
  const nav=[['/','nav.home'],['/upload','nav.upload'],['/ledger','nav.ledger'],['/ask','nav.ask']]
  return <>
    <header className="border-b-4 border-emerald-800 bg-white">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <a href="#/" className="text-2xl font-bold text-emerald-900">{t('app.name')}</a>
        <button className={ghost} aria-label={t('lang.label')} onClick={()=>setLang(lang==='en'?'hi':'en')}>{t('lang.other')}</button>
      </div>
      <nav aria-label={t('nav.label')} className="mx-auto grid max-w-5xl grid-cols-2 gap-2 px-4 pb-3 sm:grid-cols-4">
        {nav.map(([p,k])=><a key={p} href={'#'+p} aria-current={path===p?'page':undefined} className={`${path===p?primary:ghost} text-center`}>{t(k)}</a>)}
      </nav>
    </header>
    <main className="mx-auto max-w-5xl px-4 py-8">
      {rm?<ReceiptPage key={rm[1]} id={rm[1]}/>:path==='/upload'?<Upload/>:path==='/ledger'?<Ledger key={h} query={query}/>:path==='/ask'?<Ask/>:<Home/>}
    </main>
  </>
}
