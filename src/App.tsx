import {useCallback,useEffect,useState,useRef,ReactNode} from 'react'
import {useI18n,money,day} from './i18n'
import * as api from './api'
import {Account} from './api'
import {AuthPage,SettingsPage} from './account'
import {CATEGORIES,Receipt,Item,Filters,Answer} from './types'

// Reusable SVG Icons for clear, simple visual guidance
function StoreIcon({className="w-5 h-5"}:{className?:string}){
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m2 7 4.41-4.41A2 2 0 0 1 7.83 2h8.34a2 2 0 0 1 1.42.59L22 7"/><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><path d="M15 22v-4a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v4"/><path d="M2 7h20"/><circle cx="12" cy="12" r="1"/></svg>
}
function WalletIcon({className="w-5 h-5"}:{className?:string}){
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/></svg>
}
function CheckCircleIcon({className="w-5 h-5"}:{className?:string}){
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>
}
function ClockIcon({className="w-5 h-5"}:{className?:string}){
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
}
function PlusIcon({className="w-5 h-5"}:{className?:string}){
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
}
function ReceiptIcon({className="w-5 h-5"}:{className?:string}){
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M8 7h8"/><path d="M8 11h8"/><path d="M8 15h5"/></svg>
}
function ArrowRightIcon({className="w-4 h-4"}:{className?:string}){
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
}
function SparklesIcon({className="w-5 h-5"}:{className?:string}){
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
}
function DownloadIcon({className="w-5 h-5"}:{className?:string}){
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
}
function SearchIcon({className="w-5 h-5"}:{className?:string}){
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
}
function SettingsIcon({className="w-5 h-5"}:{className?:string}){
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="m19.4 15 .1.1a2 2 0 0 1-2.8 2.8l-.1-.1a2 2 0 0 0-3.4 1.4v.2a2 2 0 0 1-4 0v-.2A2 2 0 0 0 5.8 18l-.1.1a2 2 0 0 1-2.8-2.8l.1-.1a2 2 0 0 0-1.4-3.4h-.2a2 2 0 0 1 0-4h.2A2 2 0 0 0 3 4.2l-.1-.1a2 2 0 0 1 2.8-2.8l.1.1a2 2 0 0 0 3.4-1.4v-.2a2 2 0 0 1 4 0V0a2 2 0 0 0 3.4 1.4l.1-.1a2 2 0 0 1 2.8 2.8l-.1.1a2 2 0 0 0 1.4 3.4h.2a2 2 0 0 1 0 4h-.2a2 2 0 0 0-1.4 3.4Z" transform="translate(1 2) scale(.92)"/></svg>
}
function UploadCloudIcon({className="w-8 h-8"}:{className?:string}){
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m16 16-4-4-4 4"/></svg>
}
function XIcon({className="w-5 h-5"}:{className?:string}){
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
}

// Design system tokens matching the warm cream & emerald green reference
const btn = 'min-h-[48px] px-5 sm:px-6 rounded-2xl text-base sm:text-lg font-semibold focus-visible:outline-4 focus-visible:outline-emerald-500 disabled:opacity-50 inline-flex items-center justify-center gap-2 transition-all cursor-pointer select-none active:scale-[0.99]'
const primary = `${btn} bg-emerald-700 text-white hover:bg-emerald-800 shadow-sm shadow-emerald-900/10`
const prominentBtn = `${btn} bg-emerald-600 text-white hover:bg-emerald-700 shadow-md shadow-emerald-700/25 text-lg font-bold py-3.5`
const ghost = `${btn} border border-stone-300 text-stone-800 bg-white hover:bg-stone-50 hover:border-emerald-700/40 shadow-xs`
const field = 'w-full min-h-[48px] px-3.5 sm:px-4 rounded-xl border border-stone-300 bg-white text-base text-stone-900 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:border-emerald-600 disabled:bg-stone-100 disabled:text-stone-500 transition-all'
const card = 'block rounded-2xl sm:rounded-3xl bg-white border border-stone-200/90 shadow-xs hover:shadow-sm transition-all p-5 sm:p-6'
const h1 = 'text-2xl sm:text-3xl font-bold tracking-tight text-stone-900 mb-1'
const h2 = 'text-xl sm:text-2xl font-bold tracking-tight text-stone-900 mb-4'

// Subtle category pill colors for easy recognition
const catColors: Record<string, string> = {
  inventory: 'bg-emerald-50 text-emerald-800 border-emerald-200/70',
  packaging: 'bg-amber-50 text-amber-800 border-amber-200/70',
  transport: 'bg-blue-50 text-blue-800 border-blue-200/70',
  utilities: 'bg-teal-50 text-teal-800 border-teal-200/70',
  rent: 'bg-purple-50 text-purple-800 border-purple-200/70',
  repairs: 'bg-rose-50 text-rose-800 border-rose-200/70',
  other: 'bg-stone-100 text-stone-700 border-stone-200/70',
}

const OK = ['image/jpeg', 'image/png', 'application/pdf']

function useHash(){
  const get = () => location.hash.slice(1) || '/'
  const [h, s] = useState(get)
  useEffect(() => {
    const f = () => { s(get()); scrollTo(0, 0) }
    addEventListener('hashchange', f)
    return () => removeEventListener('hashchange', f)
  }, [])
  return h
}

function useLoad<T>(fn: () => Promise<T>, deps: unknown[]){
  const [s, set] = useState<{ d?: T; e?: boolean; l: boolean }>({ l: true })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(() => {
    set(p => ({ ...p, e: false, l: true }))
    fn().then(
      d => set({ d, l: false }),
      () => set({ e: true, l: false })
    )
  }, deps)
  useEffect(run, [run])
  return { ...s, run }
}

function State({ l, e, run, children }: { l: boolean; e?: boolean; run: () => void; children: ReactNode }){
  const { t } = useI18n()
  if (l) return (
    <div role="status" className="flex flex-col items-center justify-center py-16 gap-3 text-stone-500">
      <div className="w-10 h-10 border-3 border-emerald-700 border-t-transparent rounded-full animate-spin" />
      <p className="text-lg font-medium">{t('common.loading')}</p>
    </div>
  )
  if (e) return (
    <div role="alert" className={`${card} text-center py-8 border-red-200 bg-red-50/50 max-w-lg mx-auto`}>
      <p className="text-lg font-medium text-stone-800 mb-4">{t('common.error')}</p>
      <button className={primary} onClick={run}>{t('common.retry')}</button>
    </div>
  )
  return <>{children}</>
}

function Badge({ s }: { s: Receipt['status'] }){
  const { t } = useI18n()
  if (s === 'confirmed') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-300/80 bg-emerald-50 px-3 py-1 text-xs sm:text-sm font-semibold text-emerald-800">
        <CheckCircleIcon className="w-3.5 h-3.5" />
        {t('status.confirmed')}
      </span>
    )
  }
  if (s === 'duplicate') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-rose-300/80 bg-rose-50 px-3 py-1 text-xs sm:text-sm font-semibold text-rose-800">
        <span aria-hidden className="font-bold">⚠</span>
        {t('status.duplicate')}
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-300/80 bg-amber-50 px-3 py-1 text-xs sm:text-sm font-semibold text-amber-800">
      <ClockIcon className="w-3.5 h-3.5" />
      {t('status.draft')}
    </span>
  )
}

function RList({ rs, onSelect }: { rs: Receipt[]; onSelect?: (r: Receipt) => void }){
  const { t, lang } = useI18n()
  if (!rs.length) return (
    <div className={`${card} text-center py-8 text-stone-500`}>
      <ReceiptIcon className="w-10 h-10 mx-auto text-stone-300 mb-2" />
      <p className="text-base sm:text-lg">{t('lg.empty')}</p>
    </div>
  )
  return (
    <ul className="space-y-3">
      {rs.map(r => (
        <li key={r.id}>
          <div
            onClick={() => onSelect ? onSelect(r) : location.hash = `#/receipt/${r.id}`}
            role="button"
            tabIndex={0}
            className={`${card} flex flex-wrap items-center justify-between gap-3 hover:border-emerald-700/60 hover:shadow-md transition-all group cursor-pointer`}
          >
            <div className="flex items-center gap-3.5 min-w-[200px]">
              <div className="w-11 h-11 rounded-2xl bg-stone-100 group-hover:bg-emerald-50 text-stone-600 group-hover:text-emerald-700 flex items-center justify-center transition-colors shrink-0">
                <ReceiptIcon className="w-5 h-5" />
              </div>
              <div>
                <b className="block text-base sm:text-lg text-stone-900 group-hover:text-emerald-900 transition-colors">
                  {r.vendor || '—'}
                </b>
                <div className="flex items-center flex-wrap gap-2 text-sm text-stone-500 mt-0.5">
                  <span>{r.date ? day(r.date, lang) : '—'}</span>
                  <span>•</span>
                  <span className={`px-2 py-0.5 rounded-md text-xs font-medium border ${catColors[r.category] || catColors.other}`}>
                    {t('cat.' + r.category)}
                  </span>
                </div>
              </div>
            </div>
            <div className="text-right flex items-center gap-3 ml-auto">
              <div>
                <b className="block text-lg sm:text-xl font-bold text-stone-900">
                  {r.total == null ? '—' : money(r.total, lang, r.currency)}
                </b>
                <div className="mt-0.5">
                  <Badge s={r.status} />
                </div>
              </div>
              <div className="text-stone-400 group-hover:text-emerald-700 transition-colors hidden sm:block">
                <ArrowRightIcon className="w-5 h-5" />
              </div>
            </div>
          </div>
        </li>
      ))}
    </ul>
  )
}

function CategoryBreakdown({ rows, total }: { rows: { label: string; amount: number; href: string }[]; total: number }){
  const { lang,currency } = useI18n()
  if (!rows.length) return null
  return (
    <div className="space-y-2.5">
      {rows.map(r => {
        const pct = total > 0 ? Math.round((r.amount / total) * 100) : 0
        return (
          <a
            key={r.label}
            href={r.href}
            className={`${card} p-4 sm:p-5 hover:border-emerald-700/50 hover:shadow-sm transition-all group block`}
          >
            <div className="flex justify-between items-center gap-2 mb-2 text-base">
              <span className="font-semibold text-stone-800 group-hover:text-emerald-800 transition-colors">{r.label}</span>
              <span className="font-bold text-stone-900">{money(r.amount, lang,currency)}</span>
            </div>
            <div className="w-full bg-stone-100 rounded-full h-2 overflow-hidden">
              <div
                className="bg-emerald-600 group-hover:bg-emerald-700 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(pct, 100)}%` }}
              />
            </div>
            <span className="text-xs text-stone-500 mt-1 block">{pct}% of total</span>
          </a>
        )
      })}
    </div>
  )
}

function TopVendorsList({ rows }: { rows: { label: string; amount: number; href: string }[] }){
  const { lang,currency } = useI18n()
  if (!rows.length) return null
  return (
    <ul className="space-y-2.5">
      {rows.map((r, idx) => (
        <li key={r.label}>
          <a
            href={r.href}
            className={`${card} p-4 sm:p-5 flex items-center justify-between gap-3 text-base hover:border-emerald-700/50 hover:shadow-sm transition-all group`}
          >
            <div className="flex items-center gap-3">
              <span className="w-7 h-7 rounded-xl bg-stone-100 group-hover:bg-emerald-50 text-stone-700 group-hover:text-emerald-800 font-bold text-xs flex items-center justify-center transition-colors">
                #{idx + 1}
              </span>
              <span className="font-semibold text-stone-800 group-hover:text-emerald-800 transition-colors">{r.label}</span>
            </div>
            <b className="font-bold text-stone-900">{money(r.amount, lang,currency)}</b>
          </a>
        </li>
      ))}
    </ul>
  )
}

// -------------------------------------------------------------
// REVIEW RECEIPT MODAL (Compact, Cream & Emerald, Structured)
// -------------------------------------------------------------
interface ReviewModalProps {
  receiptId?: string | null
  file?: File | null
  onClose: () => void
  onSuccess: (receipt: Receipt) => void
}

function ReviewReceiptModal({ receiptId, file, onClose, onSuccess }: ReviewModalProps){
  const { t, lang } = useI18n()

  const [loading, setLoading] = useState(true)
  const [loadingMsg, setLoadingMsg] = useState(t('up.sending'))
  const [initError, setInitError] = useState<string | null>(null)

  const [receipt, setReceipt] = useState<Receipt | null>(null)
  const [vendor, setVendor] = useState('')
  const [invoiceNo, setInvoiceNo] = useState('')
  const [date, setDate] = useState('')
  const [category, setCategory] = useState('inventory')
  const [paymentMethod, setPaymentMethod] = useState('Cash')
  const [currency, setCurrency] = useState('INR')
  const [items, setItems] = useState<Item[]>([])
  const [tax, setTax] = useState<string>('')
  const [discount, setDiscount] = useState<string>('')
  const [total, setTotal] = useState<string>('')
  const [notes, setNotes] = useState('')

  const [showImage, setShowImage] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [dupResolving, setDupResolving] = useState(false)

  // Populate form fields from extracted/loaded receipt
  const populate = (r: Receipt) => {
    setReceipt(r)
    setVendor(r.vendor || '')
    setInvoiceNo(r.invoiceNumber || '')
    setDate(r.date || '')
    setCategory(r.category || 'inventory')
    setPaymentMethod(r.paymentMethod || 'Cash')
    setCurrency(r.currency || 'INR')
    setItems(r.items && r.items.length ? r.items.map(it => ({
      name: it.name || '',
      amount: it.amount || 0,
      quantity: it.quantity || 1,
      unitPrice: it.unitPrice || it.amount || 0,
    })) : [{ name: '', amount: 0, quantity: 1, unitPrice: 0 }])
    setTax(r.tax !== undefined && r.tax !== null ? String(r.tax) : '')
    setDiscount(r.discount !== undefined && r.discount !== null ? String(r.discount) : '')
    setTotal(r.total !== null && r.total !== undefined ? String(r.total) : '')
    setNotes(r.notes || '')
  }

  // Initial fetch / OCR process
  useEffect(() => {
    let active = true

    async function initialize() {
      setLoading(true)
      setInitError(null)

      try {
        if (file) {
          setLoadingMsg(t('up.sending'))
          const uploadRes = await api.upload(file)
          if (!active) return

          setLoadingMsg(t('up.reading'))
          const extracted = await api.extract(uploadRes.id)
          if (!active) return

          populate(extracted)
        } else if (receiptId) {
          setLoadingMsg(t('common.loading'))
          const data = await api.get(receiptId)
          if (!active) return
          populate(data)
        } else {
          setInitError('No receipt provided.')
        }
      } catch (err: unknown) {
        if (!active) return
        const msg = err instanceof Error ? err.message : t('up.fail')
        setInitError(msg)
      } finally {
        if (active) setLoading(false)
      }
    }

    initialize()
    return () => { active = false }
  }, [file, receiptId])

  // Subtotal calculation
  const subtotal = items.reduce((acc, it) => acc + (Number(it.amount) || 0), 0)

  // Item field update with auto-calculation of line amount if qty/price edited
  const updateItem = (index: number, patch: Partial<Item>) => {
    setItems(prev => {
      const copy = [...prev]
      const current = { ...copy[index], ...patch }
      if (patch.quantity !== undefined || patch.unitPrice !== undefined) {
        const q = Number(current.quantity) || 1
        const p = Number(current.unitPrice) || 0
        if (p > 0) {
          current.amount = Math.round(q * p * 100) / 100
        }
      }
      copy[index] = current
      return copy
    })
  }

  const addItem = () => {
    setItems(prev => [...prev, { name: '', amount: 0, quantity: 1, unitPrice: 0 }])
  }

  const removeItem = (index: number) => {
    setItems(prev => prev.filter((_, i) => i !== index))
  }

  // Recalculate suggested total when items, tax, or discount change
  const applyCalculatedTotal = () => {
    const tVal = Number(tax) || 0
    const dVal = Number(discount) || 0
    const calc = Math.max(0, subtotal + tVal - dVal)
    setTotal(String(Math.round(calc * 100) / 100))
  }

  // Handle duplicate decision: Keep as separate
  const handleKeepSeparate = async () => {
    if (!receipt) return
    setDupResolving(true)
    try {
      const updated = await api.keepSeparate(receipt.id)
      populate(updated)
    } catch {
      setSubmitError(t('common.error'))
    } finally {
      setDupResolving(false)
    }
  }

  // Handle duplicate decision: Discard
  const handleDiscardDuplicate = async () => {
    if (!receipt) return
    setDupResolving(true)
    try {
      await api.discard(receipt.id)
      onClose()
    } catch {
      setSubmitError(t('common.error'))
    } finally {
      setDupResolving(false)
    }
  }

  // Final Validation and Save & Confirm
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!receipt || isSubmitting) return

    setSubmitError(null)

    // Validation
    const trimmedVendor = vendor.trim()
    const trimmedDate = date.trim()
    const numericTotal = total === '' ? null : Number(total)

    if (!trimmedVendor || !trimmedDate || numericTotal === null || isNaN(numericTotal) || numericTotal < 0) {
      setSubmitError(t('rv.validationError'))
      return
    }

    setIsSubmitting(true)

    try {
      // 1. Prepare finalized receipt payload using user's edited values
      const finalized: Receipt = {
        ...receipt,
        vendor: trimmedVendor,
        date: trimmedDate,
        currency: currency || 'INR',
        category: category || 'inventory',
        items: items
          .map(it => ({
            name: it.name.trim() || 'Item',
            amount: Number(it.amount) || 0,
            quantity: Number(it.quantity) || 1,
            unitPrice: Number(it.unitPrice) || Number(it.amount) || 0,
          }))
          .filter(it => it.name.length > 0 || it.amount > 0),
        total: numericTotal,
        invoiceNumber: invoiceNo.trim() || undefined,
        subtotal,
        tax: tax !== '' ? Number(tax) : undefined,
        discount: discount !== '' ? Number(discount) : undefined,
        paymentMethod: paymentMethod || undefined,
        notes: notes.trim() || undefined,
        status: 'confirmed',
        flags: [],
      }

      // 2. Persist edits to database via PATCH
      await api.save(finalized)

      // 3. Confirm receipt via POST confirm
      const confirmed = await api.confirm(receipt.id)

      // 4. Success callback triggers dashboard refresh and closes modal
      onSuccess(confirmed || finalized)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : t('common.error')
      setSubmitError(msg)
      setIsSubmitting(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-stone-900/60 backdrop-blur-xs overflow-y-auto animate-in fade-in duration-150"
      onClick={e => { if (e.target === e.currentTarget && !isSubmitting) onClose() }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-review-title"
    >
      <div
        className="bg-[#FAF7F2] rounded-3xl shadow-2xl border border-stone-200/90 w-full max-w-[600px] max-h-[92vh] flex flex-col overflow-hidden relative"
        onClick={e => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-4 sm:px-6 sm:py-5 border-b border-stone-200/80 bg-white">
          <div className="flex items-center gap-2.5">
            <span className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center">
              <ReceiptIcon className="w-5 h-5" />
            </span>
            <div>
              <h2 id="modal-review-title" className="text-xl sm:text-2xl font-bold text-stone-900 leading-tight">
                {t('rv.title')}
              </h2>
              <p className="text-xs text-stone-500">
                {receipt?.fileName || file?.name || 'ShopLedger'}
              </p>
            </div>
          </div>
          <button
            type="button"
            className="w-9 h-9 rounded-xl border border-stone-200 text-stone-500 hover:text-stone-900 hover:bg-stone-100 flex items-center justify-center transition-colors cursor-pointer"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label={t('rv.close')}
          >
            <XIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-5 sm:p-6 overflow-y-auto flex-1 space-y-5">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-stone-600">
              <div className="w-10 h-10 border-3 border-emerald-700 border-t-transparent rounded-full animate-spin" />
              <p className="text-lg font-semibold text-stone-800">{loadingMsg}</p>
              <p className="text-xs text-stone-500">Extracting vendor, date, items, and total amount...</p>
            </div>
          ) : initError ? (
            <div className="text-center py-8 space-y-4">
              <div className="rounded-2xl border border-rose-300 bg-rose-50 p-4 text-rose-900 font-medium">
                ⚠ {initError}
              </div>
              <button className={ghost} onClick={onClose}>{t('rv.close')}</button>
            </div>
          ) : receipt?.status === 'duplicate' ? (
            /* Duplicate Detection Warning & Resolution */
            <div className="space-y-4">
              <div className="rounded-2xl border border-rose-300 bg-rose-50/80 p-4 text-rose-950">
                <h3 className="text-lg font-bold flex items-center gap-2">
                  <span>⚠</span> {t('dp.title')}
                </h3>
                <p className="text-sm mt-1">{t('dp.help')}</p>
              </div>

              {receipt.fileUrl && (
                <div className="rounded-2xl border border-stone-200 bg-white p-3 text-center">
                  <img src={receipt.fileUrl} alt="Receipt preview" className="max-h-48 mx-auto object-contain rounded-lg" />
                </div>
              )}

              <div className="grid grid-cols-2 gap-3 pt-2">
                <button
                  type="button"
                  className={`${ghost} text-rose-800 border-rose-300 hover:bg-rose-50`}
                  disabled={dupResolving}
                  onClick={handleDiscardDuplicate}
                >
                  {t('dp.discard')}
                </button>
                <button
                  type="button"
                  className={primary}
                  disabled={dupResolving}
                  onClick={handleKeepSeparate}
                >
                  {t('dp.keep')}
                </button>
              </div>
            </div>
          ) : (
            <form id="review-receipt-form" onSubmit={handleSubmit} className="space-y-6">
              {/* Receipt File Preview Pill / Expand */}
              {receipt?.fileUrl && (
                <div className="rounded-2xl border border-stone-200 bg-white p-3.5 flex flex-col gap-2">
                  <div className="flex items-center justify-between text-xs text-stone-600">
                    <span className="font-semibold flex items-center gap-1.5">
                      <ReceiptIcon className="w-4 h-4 text-emerald-700" />
                      {t('rv.preview')} ({receipt.fileName})
                    </span>
                    <button
                      type="button"
                      className="text-emerald-700 font-bold hover:underline cursor-pointer"
                      onClick={() => setShowImage(!showImage)}
                    >
                      {showImage ? 'Hide preview ▲' : 'Show preview ▼'}
                    </button>
                  </div>
                  {showImage && (
                    <div className="pt-2 border-t border-stone-100 text-center">
                      <img
                        src={receipt.fileUrl}
                        alt="Receipt preview"
                        className="max-h-56 mx-auto object-contain rounded-xl border border-stone-200 bg-stone-50"
                      />
                      <a
                        href={receipt.fileUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-block mt-2 text-xs font-semibold text-emerald-800 underline"
                      >
                        {t('rv.open')} ↗
                      </a>
                    </div>
                  )}
                </div>
              )}

              {/* Informative Warning Notice */}
              <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-3 text-xs sm:text-sm text-amber-900 flex items-start gap-2">
                <span className="text-base shrink-0">ℹ</span>
                <span>{t('rv.warn')}</span>
              </div>

              {/* 1. RECEIPT DETAILS SECTION */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-stone-500 border-b border-stone-200 pb-1">
                  1. {t('rv.details')}
                </h3>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="sm:col-span-2">
                    <label className="block">
                      <span className="mb-1 block text-sm font-semibold text-stone-800">
                        {t('rv.vendor')} <span className="text-rose-600">*</span>
                      </span>
                      <input
                        type="text"
                        className={field}
                        placeholder="e.g. Sharma Traders"
                        value={vendor}
                        onChange={e => setVendor(e.target.value)}
                        required
                      />
                    </label>
                  </div>

                  <div>
                    <label className="block">
                      <span className="mb-1 block text-sm font-semibold text-stone-800">
                        {t('rv.invoiceNo')}
                      </span>
                      <input
                        type="text"
                        className={field}
                        placeholder="e.g. INV-1049"
                        value={invoiceNo}
                        onChange={e => setInvoiceNo(e.target.value)}
                      />
                    </label>
                  </div>

                  <div>
                    <label className="block">
                      <span className="mb-1 block text-sm font-semibold text-stone-800">
                        {t('rv.date')} <span className="text-rose-600">*</span>
                      </span>
                      <input
                        type="date"
                        className={field}
                        value={date}
                        onChange={e => setDate(e.target.value)}
                        required
                      />
                    </label>
                  </div>

                  <div>
                    <label className="block">
                      <span className="mb-1 block text-sm font-semibold text-stone-800">
                        {t('rv.category')}
                      </span>
                      <select
                        className={field}
                        value={category}
                        onChange={e => setCategory(e.target.value)}
                      >
                        {CATEGORIES.map(c => (
                          <option key={c} value={c}>
                            {t('cat.' + c)}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>

                  <div>
                    <label className="block">
                      <span className="mb-1 block text-sm font-semibold text-stone-800">
                        {t('rv.paymentMethod')}
                      </span>
                      <select
                        className={field}
                        value={paymentMethod}
                        onChange={e => setPaymentMethod(e.target.value)}
                      >
                        <option value="Cash">{t('rv.cash')}</option>
                        <option value="UPI">{t('rv.upi')}</option>
                        <option value="Card">{t('rv.card')}</option>
                        <option value="Credit">{t('rv.credit')}</option>
                      </select>
                    </label>
                  </div>
                </div>
              </div>

              {/* 2. ITEMS SECTION */}
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-stone-200 pb-1">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-stone-500">
                    2. {t('rv.itemsSection')}
                  </h3>
                  <button
                    type="button"
                    className="text-xs font-bold text-emerald-700 hover:text-emerald-800 cursor-pointer"
                    onClick={addItem}
                  >
                    {t('rv.addItem')}
                  </button>
                </div>

                <div className="space-y-2.5">
                  {items.map((it, idx) => (
                    <div key={idx} className="bg-white p-3 rounded-xl border border-stone-200/90 shadow-2xs space-y-2">
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          className={`${field} flex-1`}
                          placeholder={t('rv.item')}
                          value={it.name}
                          onChange={e => updateItem(idx, { name: e.target.value })}
                        />
                        <button
                          type="button"
                          className="w-9 h-9 rounded-xl text-stone-400 hover:text-rose-700 hover:bg-rose-50 flex items-center justify-center shrink-0 transition-colors"
                          onClick={() => removeItem(idx)}
                          aria-label={t('rv.removeItem')}
                        >
                          ✕
                        </button>
                      </div>

                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div>
                          <label className="block text-stone-500 mb-0.5">{t('rv.qty')}</label>
                          <input
                            type="number"
                            inputMode="decimal"
                            step="any"
                            min="0"
                            className={`${field} min-h-[38px] text-sm px-2`}
                            value={it.quantity ?? 1}
                            onChange={e => updateItem(idx, { quantity: Number(e.target.value) })}
                          />
                        </div>
                        <div>
                          <label className="block text-stone-500 mb-0.5">{t('rv.price')} (₹)</label>
                          <input
                            type="number"
                            inputMode="decimal"
                            step="any"
                            min="0"
                            className={`${field} min-h-[38px] text-sm px-2`}
                            value={it.unitPrice ?? it.amount ?? 0}
                            onChange={e => updateItem(idx, { unitPrice: Number(e.target.value) })}
                          />
                        </div>
                        <div>
                          <label className="block text-stone-500 mb-0.5">{t('rv.amount')} (₹)</label>
                          <input
                            type="number"
                            inputMode="decimal"
                            step="any"
                            min="0"
                            className={`${field} min-h-[38px] text-sm px-2 font-bold text-stone-900`}
                            value={it.amount}
                            onChange={e => updateItem(idx, { amount: Number(e.target.value) })}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 3. AMOUNT SUMMARY SECTION */}
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-stone-200 pb-1">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-stone-500">
                    3. {t('rv.summary')}
                  </h3>
                  <button
                    type="button"
                    className="text-xs text-stone-500 hover:text-stone-800 underline"
                    onClick={applyCalculatedTotal}
                  >
                    Auto-fill total from items
                  </button>
                </div>

                <div className="bg-white p-4 rounded-2xl border border-stone-200/90 space-y-3">
                  <div className="flex justify-between items-center text-sm text-stone-600">
                    <span>{t('rv.subtotal')}:</span>
                    <span className="font-semibold text-stone-800">{money(subtotal, lang, currency)}</span>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-stone-600 mb-1">{t('rv.tax')} (₹)</label>
                      <input
                        type="number"
                        inputMode="decimal"
                        step="any"
                        min="0"
                        placeholder="0.00"
                        className={`${field} min-h-[42px] text-sm`}
                        value={tax}
                        onChange={e => setTax(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-stone-600 mb-1">{t('rv.discount')} (₹)</label>
                      <input
                        type="number"
                        inputMode="decimal"
                        step="any"
                        min="0"
                        placeholder="0.00"
                        className={`${field} min-h-[42px] text-sm`}
                        value={discount}
                        onChange={e => setDiscount(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="pt-2 border-t border-stone-100">
                    <label className="block">
                      <span className="mb-1 flex items-center justify-between text-base font-bold text-stone-900">
                        <span>{t('rv.total')} (₹) <span className="text-rose-600">*</span></span>
                        <span className="text-xs font-normal text-stone-500">Required</span>
                      </span>
                      <input
                        type="number"
                        inputMode="decimal"
                        step="any"
                        min="0"
                        className={`${field} text-xl font-extrabold text-emerald-950 border-emerald-600/50 focus:border-emerald-700 bg-emerald-50/20`}
                        placeholder="0.00"
                        value={total}
                        onChange={e => setTotal(e.target.value)}
                        required
                      />
                    </label>
                  </div>

                  <div>
                    <label className="block">
                      <span className="mb-1 block text-xs font-medium text-stone-600">{t('rv.notes')}</span>
                      <input
                        type="text"
                        className={`${field} min-h-[42px] text-sm`}
                        placeholder="Optional remarks (e.g. Paid by cashier)"
                        value={notes}
                        onChange={e => setNotes(e.target.value)}
                      />
                    </label>
                  </div>
                </div>
              </div>

              {/* Inline Error Notice */}
              {submitError && (
                <div role="alert" className="rounded-xl border border-rose-300 bg-rose-50 p-3.5 text-rose-900 text-sm font-semibold flex items-center gap-2">
                  <span>⚠</span>
                  <span>{submitError}</span>
                </div>
              )}
            </form>
          )}
        </div>

        {/* Modal Footer / Prominent Add Receipt Button */}
        {!loading && !initError && receipt?.status !== 'duplicate' && (
          <div className="p-4 sm:p-5 border-t border-stone-200/80 bg-white space-y-2">
            <button
              type="submit"
              form="review-receipt-form"
              className={`${prominentBtn} w-full`}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>{t('rv.addingReceipt')}</span>
                </>
              ) : (
                <>
                  <CheckCircleIcon className="w-5 h-5" />
                  <span>{t('rv.addReceipt')}</span>
                </>
              )}
            </button>
            <div className="text-center">
              <button
                type="button"
                className="text-xs text-stone-500 hover:text-stone-800 underline py-1"
                disabled={isSubmitting}
                onClick={onClose}
              >
                Cancel and finish later
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function Home({ onAddReceipt, onSelectReceipt, refreshKey }: { onAddReceipt: () => void; onSelectReceipt: (r: Receipt) => void; refreshKey: number }){
  const { t, lang,currency } = useI18n()
  const q = useLoad(() => Promise.all([
    api.summary(),
    api.categories(),
    api.list({ status: 'pending' }),
    api.list({ status: 'confirmed' })
  ]), [refreshKey])
  const s = q.d?.[0], c = q.d?.[1], p = q.d?.[2], confirmed = q.d?.[3]

  return (
    <State {...q}>
      {s && c && p && (
        <div className="space-y-8">
          {/* Welcoming Dashboard Greeting & Prominent Action Button */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-emerald-800 font-semibold text-sm mb-1">
                <StoreIcon className="w-4 h-4" />
                <span>{t('home.greeting')}</span>
              </div>
              <h1 className={h1}>{t('home.title')}</h1>
              <p className="text-stone-600 text-sm sm:text-base">
                {day(new Date().toISOString(), lang)}
              </p>
            </div>
            <div>
              <button onClick={onAddReceipt} className={prominentBtn}>
                <PlusIcon className="w-5 h-5" />
                <span>{t('home.add')}</span>
              </button>
            </div>
          </div>

          {/* Empty state prompt if 0 confirmed receipts */}
          {s.confirmedCount === 0 && (
            <div className={`${card} border-emerald-200 bg-emerald-50/40 p-6 sm:p-8 text-center max-w-xl mx-auto`}>
              <ReceiptIcon className="w-12 h-12 mx-auto text-emerald-700 mb-3" />
              <p className="mb-4 text-lg font-medium text-stone-800">{t('home.empty')}</p>
              <button onClick={onAddReceipt} className={primary}>
                <PlusIcon className="w-5 h-5" />
                {t('home.add')}
              </button>
            </div>
          )}

          {/* Key Stat Cards: 1 Prominent Dark-Green Card + 2 Smaller Cards */}
          <div className="grid gap-4 sm:grid-cols-3">
            {/* Prominent Dark-Green Card Showing Total Spending */}
            <div className="sm:col-span-1 rounded-2xl sm:rounded-3xl p-6 bg-gradient-to-br from-emerald-950 via-emerald-900 to-teal-950 text-white shadow-lg shadow-emerald-950/20 border border-emerald-800/40 flex flex-col justify-between relative overflow-hidden">
              <div className="relative z-10">
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="w-10 h-10 rounded-2xl bg-emerald-800/80 border border-emerald-600/40 text-emerald-200 flex items-center justify-center">
                    <WalletIcon className="w-5 h-5" />
                  </span>
                  <span className="text-xs font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-emerald-800/90 text-emerald-200 border border-emerald-700/50">
                    {t('home.verifiedBadge')}
                  </span>
                </div>
                <p className="text-emerald-200/90 text-sm font-medium">
                  {t('home.spent')}
                </p>
                <p className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mt-1.5">
                  {money(s.totalSpent ?? s.totalReceived ?? 0, lang,currency)}
                </p>
              </div>
              <div className="relative z-10 pt-4 mt-2 border-t border-emerald-800/50 flex items-center justify-between text-xs text-emerald-200/80">
                <span>{s.confirmedCount} {t('home.count').toLowerCase()}</span>
                <a href="#/ledger" className="underline hover:text-white transition-colors">
                  {t('home.allConfirmed')} →
                </a>
              </div>
            </div>

            {/* Smaller Card 1: Confirmed Receipts */}
            <a
              href="#/ledger"
              className={`${card} flex flex-col justify-between hover:border-emerald-600/60 hover:shadow-md transition-all group`}
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-800 border border-emerald-200/70 flex items-center justify-center">
                    <CheckCircleIcon className="w-5 h-5" />
                  </span>
                  <ArrowRightIcon className="w-4 h-4 text-stone-400 group-hover:text-emerald-700 transition-colors" />
                </div>
                <p className="text-stone-600 text-sm font-semibold">{t('home.count')}</p>
                <p className="text-3xl sm:text-4xl font-extrabold text-stone-900 group-hover:text-emerald-800 transition-colors mt-1">
                  {s.confirmedCount}
                </p>
              </div>
              <span className="text-xs font-medium text-emerald-700 mt-4 block">
                {t('home.viewAll')} →
              </span>
            </a>

            {/* Smaller Card 2: Receipts Awaiting Review */}
            <div
              className={`${card} flex flex-col justify-between hover:border-amber-500/60 hover:shadow-md transition-all`}
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="w-10 h-10 rounded-2xl bg-amber-50 text-amber-800 border border-amber-200/70 flex items-center justify-center">
                    <ClockIcon className="w-5 h-5" />
                  </span>
                  {s.reviewCount > 0 ? (
                    <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300">
                      {t('home.pendingBadge')}
                    </span>
                  ) : (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                      {t('home.allClear')}
                    </span>
                  )}
                </div>
                <p className="text-stone-600 text-sm font-semibold">{t('home.review')}</p>
                <p className="text-3xl sm:text-4xl font-extrabold text-stone-900 mt-1">
                  {s.reviewCount}
                </p>
              </div>
              {s.reviewCount > 0 ? (
                <a href="#waiting-section" className="text-xs font-medium text-amber-800 mt-4 block underline">
                  {t('home.reviewNow')} ↓
                </a>
              ) : (
                <span className="text-xs text-stone-500 mt-4 block">{t('home.none')}</span>
              )}
            </div>
          </div>

          {/* Receipts Waiting for Review Section (if any) */}
          <section id="waiting-section" className="scroll-mt-6">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className={h2}>{t('home.waiting')}</h2>
              </div>
              {p.length > 0 && (
                <span className="text-xs sm:text-sm font-bold bg-amber-100 text-amber-900 px-3 py-1 rounded-full">
                  {p.length} {t('home.review').toLowerCase()}
                </span>
              )}
            </div>
            {p.length ? (
              <RList rs={p} onSelect={onSelectReceipt} />
            ) : (
              <div className={`${card} text-center py-6 text-stone-600 bg-stone-50/70`}>
                <CheckCircleIcon className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
                <p className="text-base sm:text-lg font-medium">{t('home.none')}</p>
              </div>
            )}
          </section>

          {/* Clean, Readable Recent-Activity Section */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className={h2}>{t('home.recent')}</h2>
              </div>
              <a href="#/ledger" className="text-sm font-semibold text-emerald-800 hover:underline">
                {t('home.viewAll')} →
              </a>
            </div>
            {confirmed && confirmed.length > 0 ? (
              <RList rs={confirmed.slice(0, 5)} onSelect={onSelectReceipt} />
            ) : (
              <div className={`${card} text-center py-6 text-stone-500`}>
                <p className="text-base">{t('home.empty')}</p>
              </div>
            )}
          </section>

          {/* Spending Analytics: Categories & Top Vendors */}
          <div className="grid gap-6 md:grid-cols-2">
            <section>
              <h2 className={h2}>{t('home.cats')}</h2>
              <CategoryBreakdown
                rows={c.map(x => ({
                  label: t('cat.' + x.category),
                  amount: x.amount,
                  href: `#/ledger?category=${x.category}`
                }))}
                total={s.totalSpent ?? s.totalReceived ?? 0}
              />
            </section>
            <section>
              <h2 className={h2}>{t('home.vendors')}</h2>
              <TopVendorsList
                rows={s.topVendors.map(v => ({
                  label: v.vendor,
                  amount: v.amount,
                  href: `#/ledger?vendor=${encodeURIComponent(v.vendor)}`
                }))}
              />
            </section>
          </div>
        </div>
      )}
    </State>
  )
}

function Upload({ onFileSelect }: { onFileSelect: (f: File) => void }){
  const { t } = useI18n()
  const [dragActive, setDragActive] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = (f?: File) => {
    if (!f) return
    if (!OK.includes(f.type)) {
      alert(t('up.badType'))
      return
    }
    onFileSelect(f)
  }

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div>
        <h1 className={h1}>{t('up.title')}</h1>
        <p className="text-stone-600 text-base sm:text-lg">{t('up.help')}</p>
      </div>

      <div
        className={`${card} border-2 border-dashed ${dragActive ? 'border-emerald-600 bg-emerald-50/50' : 'border-stone-300'} hover:border-emerald-600/70 p-8 sm:p-12 text-center transition-all cursor-pointer`}
        onDragOver={e => { e.preventDefault(); setDragActive(true) }}
        onDragLeave={() => setDragActive(false)}
        onDrop={e => {
          e.preventDefault()
          setDragActive(false)
          handleFile(e.dataTransfer.files?.[0])
        }}
        onClick={() => inputRef.current?.click()}
      >
        <UploadCloudIcon className="w-14 h-14 mx-auto text-emerald-700 mb-4" />
        <h3 className="text-xl font-bold text-stone-900 mb-2">
          {t('up.choose')}
        </h3>
        <p className="text-stone-600 text-sm mb-4">
          Click or drop bill photos, scanned copies, or PDF invoices
        </p>
        <button
          type="button"
          className={prominentBtn}
          onClick={e => { e.stopPropagation(); inputRef.current?.click() }}
        >
          <PlusIcon className="w-5 h-5" />
          <span>{t('up.choose')}</span>
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
          className="sr-only"
          onChange={e => handleFile(e.target.files?.[0])}
        />
        <p className="text-xs text-stone-400 mt-4">JPG, PNG, PDF up to 10MB</p>
      </div>
    </div>
  )
}

function Ledger({ query, onSelectReceipt, refreshKey }: { query: string; onSelectReceipt: (r: Receipt) => void; refreshKey: number }){
  const { t, lang } = useI18n()
  const p = new URLSearchParams(query)
  const blank: Filters = { q: '', from: '', to: '', category: '', vendor: '' }
  const [fl, setFl] = useState<Filters>({ ...blank, category: p.get('category') || '', vendor: p.get('vendor') || '' })
  const [ex, setEx] = useState<'idle' | 'busy' | 'ok' | 'err'>('idle')

  const vendors = useLoad(() => api.summary(), [refreshKey])
  const r = useLoad(() => api.list({ ...fl, status: 'confirmed' }), [JSON.stringify(fl), refreshKey])

  const up = (k: keyof Filters, v: string) => setFl(x => ({ ...x, [k]: v }))
  const doExport = async () => {
    if (ex === 'busy') return
    setEx('busy')
    try {
      await api.exportCsv()
      setEx('ok')
    } catch {
      setEx('err')
    }
  }

  const vlist = Array.from(new Set([...(vendors.d?.topVendors.map(v => v.vendor) ?? []), ...(fl.vendor ? [fl.vendor] : [])]))

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className={h1}>{t('lg.title')}</h1>
          <p className="text-stone-600 text-sm sm:text-base">{t('lg.help')}</p>
        </div>
        <button className={primary} disabled={ex === 'busy'} onClick={doExport}>
          <DownloadIcon className="w-5 h-5" />
          <span>{t('lg.export')}</span>
        </button>
      </div>

      <div role="status" aria-live="polite">
        {ex === 'busy' && <p className="text-sm text-stone-600 animate-pulse">{t('lg.exporting')}</p>}
        {ex === 'ok' && <p className="text-sm font-semibold text-emerald-800">✓ {t('lg.exportOk')}</p>}
        {ex === 'err' && (
          <div className="flex items-center gap-3">
            <p className="text-sm font-semibold text-rose-800">⚠ {t('lg.exportErr')}</p>
            <button className={`${ghost} text-xs py-1 px-3`} onClick={doExport}>{t('common.retry')}</button>
          </div>
        )}
      </div>

      {/* Filter controls */}
      <div className={`${card} grid gap-4 sm:grid-cols-2 lg:grid-cols-3`}>
        <div className="sm:col-span-2 lg:col-span-1">
          <label className="block">
            <span className="mb-1.5 block text-sm font-semibold text-stone-800">{t('lg.search')}</span>
            <div className="relative">
              <input
                type="search"
                className={`${field} !pl-11 pr-4 placeholder:text-stone-400`}
                placeholder={t('lg.searchPlaceholder')}
                value={fl.q}
                onChange={e => up('q', e.target.value)}
              />
              <span className="absolute left-3.5 top-3.5 text-stone-400 pointer-events-none">
                <SearchIcon className="w-5 h-5" />
              </span>
            </div>
          </label>
        </div>

        <div>
          <label className="block">
            <span className="mb-1.5 block text-sm font-semibold text-stone-800">{t('lg.category')}</span>
            <select className={field} value={fl.category} onChange={e => up('category', e.target.value)}>
              <option value="">{t('cat.all')}</option>
              {CATEGORIES.map(c => <option key={c} value={c}>{t('cat.' + c)}</option>)}
            </select>
          </label>
        </div>

        <div>
          <label className="block">
            <span className="mb-1.5 block text-sm font-semibold text-stone-800">{t('lg.vendor')}</span>
            <select className={field} value={fl.vendor} onChange={e => up('vendor', e.target.value)}>
              <option value="">{t('lg.allVendors')}</option>
              {vlist.map(v => <option key={v}>{v}</option>)}
            </select>
          </label>
        </div>

        <div>
          <label className="block">
            <span className="mb-1.5 block text-sm font-semibold text-stone-800">{t('lg.from')}</span>
            <input type="date" className={field} value={fl.from} onChange={e => up('from', e.target.value)} />
          </label>
        </div>

        <div>
          <label className="block">
            <span className="mb-1.5 block text-sm font-semibold text-stone-800">{t('lg.to')}</span>
            <input type="date" className={field} value={fl.to} onChange={e => up('to', e.target.value)} />
          </label>
        </div>

        <div className="flex items-end">
          <button className={`${ghost} w-full`} onClick={() => setFl(blank)}>
            {t('lg.clear')}
          </button>
        </div>
      </div>

      {/* Filtered Receipts List */}
      <State {...r}>
        <RList rs={r.d ?? []} onSelect={onSelectReceipt} />
      </State>
      <span className="sr-only">{lang}</span>
    </div>
  )
}

function Ask({ onSelectReceipt }: { onSelectReceipt: (r: Receipt) => void }){
  const { t, lang } = useI18n()
  const [q, setQ] = useState(''), [a, setA] = useState<Answer | null>(null), [l, setL] = useState(false), [e, setE] = useState(false)

  const go = async (text: string) => {
    if (!text.trim() || l) return
    setQ(text); setL(true); setE(false)
    try {
      setA(await api.ask(text, lang))
    } catch {
      setE(true)
    }
    setL(false)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className={h1}>{t('qa.title')}</h1>
        <p className="text-stone-600 text-sm sm:text-base">{t('qa.help')}</p>
      </div>

      {/* Example suggestion chips */}
      <div className="space-y-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-stone-500">Tap to ask</span>
        <div className="flex flex-col gap-2">
          {[1, 2, 3, 4, 5].map(n => (
            <button
              key={n}
              className={`${ghost} text-left text-stone-700 hover:text-emerald-900 hover:border-emerald-700/60 justify-start py-3 px-4 text-sm sm:text-base`}
              disabled={l}
              onClick={() => go(t('qa.ex' + n))}
            >
              <SparklesIcon className="w-4 h-4 text-emerald-700 shrink-0" />
              <span>{t('qa.ex' + n)}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Query input */}
      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          className={field}
          aria-label={t('qa.placeholder')}
          placeholder={t('qa.placeholder')}
          value={q}
          onChange={e => setQ(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && go(q)}
        />
        <button className={prominentBtn} disabled={l || !q.trim()} onClick={() => go(q)}>
          <SparklesIcon className="w-5 h-5" />
          <span>{t('qa.send')}</span>
        </button>
      </div>

      {/* Answer result */}
      <div role="status" aria-live="polite">
        {l && (
          <div className={`${card} flex items-center gap-3 py-6`}>
            <div className="w-6 h-6 border-2 border-emerald-700 border-t-transparent rounded-full animate-spin" />
            <p className="text-base sm:text-lg font-medium text-stone-800">{t('qa.thinking')}</p>
          </div>
        )}
        {e && (
          <div role="alert" className={`${card} border-rose-200 bg-rose-50/50 p-6`}>
            <p className="mb-3 text-base text-rose-900 font-semibold">{t('common.error')}</p>
            <button className={primary} onClick={() => go(q)}>{t('common.retry')}</button>
          </div>
        )}
        {a && !l && !e && (
          <div className="space-y-6 pt-2">
            <div className={`${card} border-emerald-200 bg-emerald-50/40 p-6`}>
              <div className="flex items-center gap-2 text-emerald-800 font-semibold text-xs uppercase tracking-wider mb-2">
                <SparklesIcon className="w-4 h-4" />
                <span>ShopLedger Assistant</span>
              </div>
              <p className="text-lg sm:text-xl font-bold text-stone-900">{a.answer}</p>
            </div>
            {a.supported && a.receipts.length > 0 && (
              <div className="space-y-3">
                <h2 className="text-lg font-bold text-stone-900">{t('qa.sources')}</h2>
                <RList rs={a.receipts} onSelect={onSelectReceipt} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default function App(){
  const { t, lang, setLang, setCurrency } = useI18n()
  const [authLoading,setAuthLoading]=useState(true)
  const [authConfigured,setAuthConfigured]=useState(false)
  const [authError,setAuthError]=useState('')
  const [account,setAccount]=useState<Account|null>(null)
  const loadAuth=useCallback(async()=>{
    setAuthLoading(true)
    setAuthError('')
    try{
      const state=await api.authStatus()
      setAuthConfigured(state.configured)
      setAccount(state.account)
      if(state.account){
        setLang(state.account.language)
        setCurrency(state.account.currency)
      }
    }catch(error){
      setAuthError(error instanceof Error?error.message:t('auth.error'))
    }finally{
      setAuthLoading(false)
    }
  },[setLang,setCurrency,t])
  useEffect(()=>{void loadAuth()},[loadAuth])
  useEffect(()=>{
    const expired=()=>{
      setAccount(null)
      setAuthConfigured(true)
      setAuthError('')
    }
    window.addEventListener('shopledger:unauthorized',expired)
    return ()=>window.removeEventListener('shopledger:unauthorized',expired)
  },[])
  const h = useHash()
  const [path, query = ''] = h.split('?')
  const rm = path.match(/^\/receipt\/(.+)$/)

  // Modal & Notification State
  const [activeModal, setActiveModal] = useState<{ id?: string; file?: File } | null>(null)
  const [toastMessage, setToastMessage] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  // Direct route detection for #/receipt/:id
  useEffect(() => {
    if (rm && rm[1]) {
      setActiveModal({ id: rm[1] })
    }
  }, [rm?.[1]])

  // Hidden file input for header/dashboard action triggers
  const hiddenFileInputRef = useRef<HTMLInputElement>(null)

  const handleFilePicked = (f?: File) => {
    if (!f) return
    if (!OK.includes(f.type)) {
      alert(t('up.badType'))
      return
    }
    setActiveModal({ file: f })
  }

  // Handle successful confirmation
  const handleModalSuccess = (confirmedReceipt: Receipt) => {
    setActiveModal(null)
    setRefreshKey(prev => prev + 1)
    setToastMessage(`${t('rv.successToast')} (${confirmedReceipt.vendor || 'Receipt'})`)
    setTimeout(() => setToastMessage(null), 5000)
    // If on receipt page hash, return to home
    if (location.hash.startsWith('#/receipt/')) {
      location.hash = '#/'
    }
  }

  const handleModalClose = () => {
    setActiveModal(null)
    if (location.hash.startsWith('#/receipt/')) {
      location.hash = '#/'
    }
  }

  const handleAuthenticated = (nextAccount:Account) => {
    setAccount(nextAccount)
    setAuthConfigured(true)
    setAuthError('')
    setLang(nextAccount.language)
    setCurrency(nextAccount.currency)
  }

  const handleSignOut = async () => {
    try{
      await api.signOut()
      setAccount(null)
      location.hash='#/'
    }catch(error){
      setToastMessage(error instanceof Error?error.message:t('auth.error'))
      setTimeout(()=>setToastMessage(null),5000)
    }
  }

  const changeLanguage = async () => {
    if(!account)return
    const language=lang==='en'?'hi':'en'
    try{
      const updated=await api.saveProfile({...account,language})
      setAccount(updated)
      setLang(updated.language)
    }catch(error){
      setToastMessage(error instanceof Error?error.message:t('settings.saveError'))
      setTimeout(()=>setToastMessage(null),5000)
    }
  }

  const nav = [
    { p: '/', k: 'nav.home', icon: StoreIcon },
    { p: '/upload', k: 'nav.upload', icon: PlusIcon },
    { p: '/ledger', k: 'nav.ledger', icon: ReceiptIcon },
    { p: '/ask', k: 'nav.ask', icon: SparklesIcon },
    { p: '/settings', k: 'nav.settings', icon: SettingsIcon }
  ]

  if(authLoading){
    return <main className="flex min-h-screen items-center justify-center bg-[#FAF7F2] text-lg font-semibold text-stone-600">{t('common.loading')}</main>
  }

  if(!account){
    return <AuthPage configured={authConfigured} error={authError} onRetry={()=>void loadAuth()} onAuthenticated={handleAuthenticated}/>
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#FAF7F2] text-[#1C1917]">
      {/* Hidden file input for quick "+ Add Receipt" triggers */}
      <input
        ref={hiddenFileInputRef}
        type="file"
        accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
        className="sr-only"
        onChange={e => {
          handleFilePicked(e.target.files?.[0])
          e.target.value = ''
        }}
      />

      {/* Success Notification Banner / Toast */}
      {toastMessage && (
        <div className="fixed top-4 right-4 z-60 max-w-md animate-in slide-in-from-top duration-200">
          <div className="bg-emerald-800 text-white px-5 py-3.5 rounded-2xl shadow-xl flex items-center justify-between gap-3 border border-emerald-700">
            <div className="flex items-center gap-2.5">
              <CheckCircleIcon className="w-5 h-5 text-emerald-300 shrink-0" />
              <p className="text-sm font-semibold">{toastMessage}</p>
            </div>
            <button
              onClick={() => setToastMessage(null)}
              className="text-emerald-200 hover:text-white p-1"
              aria-label="Dismiss"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Review Receipt Modal Popup */}
      {activeModal && (
        <ReviewReceiptModal
          receiptId={activeModal.id}
          file={activeModal.file}
          onClose={handleModalClose}
          onSuccess={handleModalSuccess}
        />
      )}

      {/* Top Header */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-stone-200/90 shadow-2xs">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3 sm:py-4">
          <a href="#/" className="flex items-center gap-2.5 text-emerald-900 group">
            <span className="w-10 h-10 rounded-2xl bg-emerald-700 text-white flex items-center justify-center shadow-xs group-hover:bg-emerald-800 transition-colors">
              <StoreIcon className="w-5 h-5" />
            </span>
            <div className="leading-tight">
              <span className="text-xl sm:text-2xl font-extrabold tracking-tight block text-emerald-950">
                {t('app.name')}
              </span>
              <span className="text-[11px] font-medium text-stone-500 uppercase tracking-wider hidden sm:block">
                Digital Shopkeeper Ledger
              </span>
            </div>
          </a>

          {/* Header Action + Language Switcher */}
          <div className="flex items-center gap-2 sm:gap-3">
            <button
              type="button"
              onClick={() => hiddenFileInputRef.current?.click()}
              className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold shadow-xs transition-colors cursor-pointer"
            >
              <PlusIcon className="w-4 h-4" />
              <span>{t('home.add')}</span>
            </button>

            <button
              className="min-h-[42px] px-3.5 sm:px-4 rounded-xl border border-stone-200 bg-stone-50 hover:bg-stone-100 text-stone-800 text-sm font-semibold flex items-center gap-2 cursor-pointer transition-colors shadow-2xs"
              aria-label={t('lang.label')}
              onClick={() => void changeLanguage()}
            >
              <span className="text-base">{lang === 'en' ? '🇮🇳' : '🇬🇧'}</span>
              <span>{t('lang.other')}</span>
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav aria-label={t('nav.label')} className="mx-auto max-w-5xl px-4 pb-2.5">
          <div className="grid grid-cols-5 gap-1 sm:gap-2 bg-stone-100/80 p-1 rounded-2xl border border-stone-200/70">
            {nav.map(item => {
              const active = path === item.p
              const Icon = item.icon
              return (
                <a
                  key={item.p}
                  href={'#' + item.p}
                  aria-current={active ? 'page' : undefined}
                  className={`flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 py-2 px-2 rounded-xl text-xs sm:text-base font-semibold transition-all ${
                    active
                      ? 'bg-white text-emerald-900 shadow-xs border border-stone-200/80'
                      : 'text-stone-600 hover:text-stone-900 hover:bg-white/50'
                  }`}
                >
                  <Icon className={`w-4 h-4 sm:w-5 sm:h-5 ${active ? 'text-emerald-700' : 'text-stone-500'}`} />
                  <span className="truncate">{t(item.k)}</span>
                </a>
              )
            })}
          </div>
        </nav>
      </header>

      {/* Main Content View */}
      <main className="mx-auto max-w-5xl w-full px-4 py-6 sm:py-8 flex-1">
        {path === '/upload' ? (
          <Upload onFileSelect={f => setActiveModal({ file: f })} />
        ) : path === '/ledger' ? (
          <Ledger
            key={h}
            query={query}
            onSelectReceipt={r => setActiveModal({ id: r.id })}
            refreshKey={refreshKey}
          />
        ) : path === '/ask' ? (
          <Ask onSelectReceipt={r => setActiveModal({ id: r.id })} />
        ) : path === '/settings' ? (
          <SettingsPage account={account} onAccountUpdated={updated=>{setAccount(updated);setCurrency(updated.currency)}} onSignOut={handleSignOut}/>
        ) : (
          <Home
            onAddReceipt={() => hiddenFileInputRef.current?.click()}
            onSelectReceipt={r => setActiveModal({ id: r.id })}
            refreshKey={refreshKey}
          />
        )}
      </main>

      {/* Subtle Footer */}
      <footer className="border-t border-stone-200/80 bg-white/60 py-6 text-center text-xs text-stone-500">
        <div className="mx-auto max-w-5xl px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>© {new Date().getFullYear()} {t('app.name')} — Built for Indian retail shop owners</span>
          <span className="text-stone-400">Offline-ready • Fast • Secure</span>
        </div>
      </footer>
    </div>
  )
}
