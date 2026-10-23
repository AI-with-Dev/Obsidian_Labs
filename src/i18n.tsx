import {createContext,useContext,useState,ReactNode} from 'react'
import en from './locales/en.json'
import hi from './locales/hi.json'
export type Lang='en'|'hi'
const dict:Record<Lang,Record<string,string>>={en,hi}
export const dictFor=(l:Lang)=>dict[l]
type V=Record<string,string|number>
interface C{lang:Lang;setLang:(l:Lang)=>void;currency:string;setCurrency:(c:string)=>void;t:(k:string,v?:V)=>string}
const Ctx=createContext<C>(null as unknown as C)
export function I18n({children}:{children:ReactNode}){
  const storedLang=localStorage.getItem('lang')
  const [lang,set]=useState<Lang>(storedLang==='hi'?'hi':'en')
  const [currency,setCurrency]=useState(()=>localStorage.getItem('currency')||'INR')
  const setLang=(l:Lang)=>{localStorage.setItem('lang',l);set(l)}
  const updateCurrency=(c:string)=>{localStorage.setItem('currency',c);setCurrency(c)}
  document.documentElement.lang=lang
  document.title = lang === 'hi' ? 'व्यापार मित्र (Vyapar Mitra)' : 'Vyapar Mitra'
  const t=(k:string,v:V={})=>(dict[lang][k]??k).replace(/\{(\w+)\}/g,(_,x)=>String(v[x]??''))
  return <Ctx.Provider value={{lang,setLang,currency,setCurrency:updateCurrency,t}}>{children}</Ctx.Provider>
}
export const useI18n=()=>useContext(Ctx)
const loc=(l:Lang)=>l==='hi'?'hi-IN':'en-IN'
export const money=(n:number,l:Lang,c='INR')=>new Intl.NumberFormat(loc(l),{style:'currency',currency:c,maximumFractionDigits:2}).format(n)
export const day=(d:string,l:Lang)=>new Date(d).toLocaleDateString(loc(l),{day:'numeric',month:'short',year:'numeric'})
