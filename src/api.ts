// Set VITE_API_BASE_URL to use a separate backend; otherwise use Vite's same-origin /api proxy.
// Set VITE_API_BASE_URL=mock to use sample receipt data (auth and settings still need the backend).
import {Receipt,Summary,CategoryTotal,Answer,Filters} from './types'
import {Lang} from './i18n'
import {m} from './mock'

const BASE=(import.meta.env.VITE_API_BASE_URL as string|undefined)?.replace(/\/$/,'')
const MOCK=BASE==='mock'
const wait=()=>new Promise(r=>setTimeout(r,400))

async function call<T>(path:string,init:RequestInit|undefined,mock:()=>T):Promise<T>{
  if(MOCK){await wait();return mock()}
  const body=init?.body
  const res=await fetch((BASE||'')+path,{...init,credentials:'include',headers:body instanceof FormData?{}:{'Content-Type':'application/json'}})
  if(res.status===401&&path!=='/api/auth/status'&&path!=='/api/auth/login'){
    window.dispatchEvent(new Event('vyapar-mitra:unauthorized'))
  }
  const j=await res.json().catch(()=>null)
  if(!res.ok||!j?.success)throw new Error(j?.error?.message??j?.error??'Request failed')
  return j.data as T
}

const json=(method:string,body?:unknown):RequestInit=>({method,body:body===undefined?undefined:JSON.stringify(body)})
const request=<T>(path:string,init?:RequestInit)=>call<T>(path,init,()=>{throw new Error('Authentication and settings require the backend API.')})

export interface Account {
  fullName:string
  email:string
  businessName:string
  phone:string
  address:string
  gstin:string
  language:Lang
  currency:string
}
export interface AuthStatus {configured:boolean;authenticated:boolean;account:Account|null}
export const authStatus=()=>request<AuthStatus>('/api/auth/status')
export const signUp=(account:Account & {password:string;passwordConfirmation:string})=>
  request<{account:Account}>('/api/auth/setup',json('POST',account))
export const signIn=(email:string,password:string)=>
  request<{account:Account}>('/api/auth/login',json('POST',{email,password}))
export const signOut=()=>request<{signedOut:boolean}>('/api/auth/logout',json('POST'))
export const saveProfile=(account:Partial<Account>,currentPassword?:string)=>
  request<Account>('/api/auth/profile',json('PATCH',{...account,...(currentPassword?{currentPassword}:{})}))
export const changePassword=(currentPassword:string,newPassword:string,passwordConfirmation:string)=>
  request<{passwordChanged:boolean}>('/api/auth/password',json('POST',{currentPassword,newPassword,passwordConfirmation}))

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
export const deleteReceipt=(id:string)=>call<void>(`/api/receipts/${id}`,json('DELETE'),()=>m.deleteReceipt(id))
export const keepSeparate=(id:string)=>call<Receipt>(`/api/receipts/${id}/keep-separate`,json('POST'),()=>m.keep(id))
export const list=(f:Filters={})=>call<Receipt[]>('/api/receipts?'+new URLSearchParams(Object.entries(f).filter(([,v])=>v) as [string,string][]),undefined,()=>m.list(f))
export const summary=()=>call<Summary>('/api/dashboard/summary',undefined,()=>m.summary())
export const categories=()=>call<CategoryTotal[]>('/api/dashboard/categories',undefined,()=>m.categories())
export const ask=(question:string,lang:Lang)=>call<Answer>('/api/questions/ask',json('POST',{question,lang}),()=>m.ask(question,lang))

export async function exportPdf(){
  let blob:Blob
  if(!MOCK){
    const r=await fetch((BASE||'')+'/api/export/pdf',{credentials:'include'})
    if(r.status===401)window.dispatchEvent(new Event('vyapar-mitra:unauthorized'))
    if(!r.ok) throw new Error('PDF export failed')
    blob=await r.blob()
  } else {
    await wait()
    blob=new Blob([m.pdf()],{type:'application/pdf'})
  }
  const a=document.createElement('a')
  a.href=URL.createObjectURL(blob)
  a.download='vyapar-mitra-payment-summary.pdf'
  a.click()
  window.setTimeout(()=>URL.revokeObjectURL(a.href),1000)
}

export async function exportCsv(){
  if(MOCK)throw new Error('CSV export requires the backend API.')
  const response=await fetch((BASE||'')+'/api/export/csv',{credentials:'include'})
  if(response.status===401)window.dispatchEvent(new Event('vyapar-mitra:unauthorized'))
  if(!response.ok)throw new Error('CSV export failed')
  const blob=await response.blob()
  const url=URL.createObjectURL(blob)
  const link=document.createElement('a')
  link.href=url
  link.download='vyapar-mitra-ledger.csv'
  link.click()
  window.setTimeout(()=>URL.revokeObjectURL(url),1000)
}
