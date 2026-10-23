// API service layer. Antigravity: set VITE_API_BASE_URL; every call below then hits the real endpoint.
// Backend must reply with {"success":true,"data":...,"error":null}. When BASE is empty, ./mock is used instead.
import {Receipt,Summary,CategoryTotal,Answer,Filters} from './types'
import {Lang} from './i18n'
import {m} from './mock'

const BASE=(import.meta.env.VITE_API_BASE_URL as string|undefined)?.replace(/\/$/,'')
const wait=()=>new Promise(r=>setTimeout(r,400))

async function call<T>(path:string,init:RequestInit|undefined,mock:()=>T):Promise<T>{
  if(!BASE){await wait();return mock()}
  const body=init?.body
  const res=await fetch(BASE+path,{...init,headers:body instanceof FormData?{}:{'Content-Type':'application/json'}})
  const j=await res.json().catch(()=>null)
  if(!res.ok||!j?.success)throw new Error(j?.error?.message??j?.error??'Request failed')
  return j.data as T
}

const json=(method:string,body?:unknown):RequestInit=>({method,body:body===undefined?undefined:JSON.stringify(body)})

export const upload=(file:File)=>{const fd=new FormData();fd.append('file',file);return call<{id:string}>('/api/receipts/upload',{method:'POST',body:fd},()=>m.upload(file))}
export const extract=(id:string)=>call<Receipt>(`/api/receipts/${id}/extract`,json('POST'),()=>m.extract(id))
export const get=(id:string)=>call<Receipt>(`/api/receipts/${id}`,undefined,()=>m.get(id))
export const save=(r:Receipt)=>call<Receipt>(`/api/receipts/${r.id}`,json('PATCH',{
  vendor:r.vendor,
  date:r.date,
  currency:r.currency,
  items:r.items,
  total:r.total,
  category:r.category,
  invoiceNumber:r.invoiceNumber,
  subtotal:r.subtotal,
  tax:r.tax,
  discount:r.discount,
  paymentMethod:r.paymentMethod,
  notes:r.notes,
}),()=>m.save(r))
export const confirm=(id:string)=>call<Receipt>(`/api/receipts/${id}/confirm`,json('POST'),()=>m.confirm(id))
export const discard=(id:string)=>call<void>(`/api/receipts/${id}/discard-duplicate`,json('POST'),()=>m.discard(id))
export const keepSeparate=(id:string)=>call<Receipt>(`/api/receipts/${id}/keep-separate`,json('POST'),()=>m.keep(id))
export const list=(f:Filters={})=>call<Receipt[]>('/api/receipts?'+new URLSearchParams(Object.entries(f).filter(([,v])=>v) as [string,string][]),undefined,()=>m.list(f))
export const summary=()=>call<Summary>('/api/dashboard/summary',undefined,()=>m.summary())
export const categories=()=>call<CategoryTotal[]>('/api/dashboard/categories',undefined,()=>m.categories())
export const ask=(question:string,lang:Lang)=>call<Answer>('/api/questions/ask',json('POST',{question,lang}),()=>m.ask(question,lang))

export async function exportCsv(){
  let blob:Blob
  if(BASE){const r=await fetch(BASE+'/api/export/csv');if(!r.ok)throw new Error('export failed');blob=await r.blob()}
  else{await wait();blob=new Blob([m.csv ? m.csv() : ''],{type:'text/csv'})}
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='shopledger-expenses.csv';a.click()
}

export async function exportPdf(){
  let blob:Blob
  if(BASE){
    const r=await fetch(BASE+'/api/export/pdf')
    if(!r.ok) throw new Error('PDF export failed')
    blob=await r.blob()
  } else {
    await wait()
    blob=new Blob([m.pdf()],{type:'application/pdf'})
  }
  const a=document.createElement('a')
  a.href=URL.createObjectURL(blob)
  a.download='shopledger-payment-summary.pdf'
  a.click()
}
