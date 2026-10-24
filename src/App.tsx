import {useCallback,useEffect,useState,useRef,ReactNode} from 'react'
import {useI18n,money,day} from './i18n'
import * as api from './api'
import {Account} from './api'
import {AuthPage,SettingsPage} from './account'
import {VyaparMitraLogo} from './components/VyaparMitraLogo'
import {Receipt,Item,Filters,Answer} from './types'

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
function MenuIcon({className="w-5 h-5"}:{className?:string}){
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/></svg>
}
function ChevronDownIcon({className="w-4 h-4"}:{className?:string}){
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
}

// Design system tokens: high-contrast, large touch targets tailored for budget mobile screens in direct sunlight
const btn = 'min-h-[48px] px-5 sm:px-6 rounded-xl text-base font-bold focus-visible:outline-2 focus-visible:outline-emerald-600 disabled:opacity-50 inline-flex items-center justify-center gap-2 transition-all cursor-pointer select-none active:scale-[0.99]'
const primary = `${btn} bg-emerald-700 text-white hover:bg-emerald-800 shadow-sm`
const prominentBtn = `${btn} min-h-[54px] sm:min-h-[58px] bg-emerald-700 text-white hover:bg-emerald-800 shadow-md text-lg sm:text-xl font-black py-3.5`
const ghost = `${btn} border-2 border-stone-300 text-stone-800 bg-white hover:bg-stone-50 hover:border-emerald-700/60 shadow-2xs`
const field = 'w-full min-h-[48px] sm:min-h-[50px] px-3.5 sm:px-4 rounded-xl border-2 border-stone-300 bg-white text-base font-semibold text-stone-900 focus:outline-none focus:ring-2 focus:ring-emerald-700/30 focus:border-emerald-700 disabled:bg-stone-100 disabled:text-stone-500 transition-all placeholder:text-stone-400'
const card = 'block rounded-2xl bg-white border-2 border-stone-200/90 shadow-2xs hover:shadow-xs transition-all p-5 sm:p-6'
const h1 = 'text-2xl sm:text-3xl font-bold tracking-tight text-stone-900 mb-1'
const h2 = 'text-xl sm:text-2xl font-bold tracking-tight text-stone-900 mb-4'

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
      <span className="inline-flex items-center gap-1.5 rounded-xs border border-emerald-300/80 bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
        <CheckCircleIcon className="w-3.5 h-3.5" />
        {t('status.confirmed')}
      </span>
    )
  }
  if (s === 'duplicate') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-xs border border-rose-300/80 bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-800">
        <span aria-hidden className="font-bold">⚠</span>
        {t('status.duplicate')}
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-xs border border-amber-300/80 bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-800">
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
      {rs.map(r => {
        const isBorrowed = r.type === 'expense'
        return (
          <li key={r.id}>
            <div
              onClick={() => onSelect ? onSelect(r) : location.hash = `#/receipt/${r.id}`}
              role="button"
              tabIndex={0}
              className={`${card} flex flex-wrap items-center justify-between gap-3 hover:border-emerald-700/60 hover:shadow-md transition-all group cursor-pointer`}
            >
              <div className="flex items-center gap-3.5 min-w-[200px]">
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center transition-colors shrink-0 ${
                  isBorrowed ? 'bg-amber-50 text-amber-800 group-hover:bg-amber-100' : 'bg-emerald-50 text-emerald-800 group-hover:bg-emerald-100'
                }`}>
                  {isBorrowed ? <ClockIcon className="w-5 h-5" /> : <WalletIcon className="w-5 h-5" />}
                </div>
                <div>
                  <b className="block text-base sm:text-lg text-stone-900 group-hover:text-emerald-900 transition-colors">
                    {r.vendor || '—'}
                  </b>
                  <div className="flex items-center flex-wrap gap-2 text-sm text-stone-500 mt-0.5">
                    <span>{r.date ? day(r.date, lang) : '—'}</span>
                    <span className={`inline-flex items-center gap-1 rounded-xs border px-1.5 py-0.2 text-[11px] font-bold ${
                      isBorrowed ? 'border-amber-300 bg-amber-50 text-amber-900' : 'border-emerald-300 bg-emerald-50 text-emerald-800'
                    }`}>
                      {isBorrowed ? t('type.borrowed') : t('type.income')}
                    </span>
                  </div>
                </div>
              </div>
              <div className="text-right flex items-center gap-3 ml-auto">
                <div>
                  <b className={`block text-lg sm:text-xl font-black ${isBorrowed ? 'text-amber-800' : 'text-emerald-700'}`}>
                    {r.total == null ? '—' : (isBorrowed ? `उधार ${money(r.total, lang, r.currency)}` : `+ ${money(r.total, lang, r.currency)}`)}
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
        )
      })}
    </ul>
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
  onDeleted: () => void
}

function ReviewReceiptModal({ receiptId, file, onClose, onSuccess, onDeleted }: ReviewModalProps){
  const { t, lang } = useI18n()

  const [loading, setLoading] = useState(true)
  const [loadingMsg, setLoadingMsg] = useState(t('up.sending'))
  const [initError, setInitError] = useState<string | null>(null)

  const [receipt, setReceipt] = useState<Receipt | null>(null)
  const [transactionType, setTransactionType] = useState<'income' | 'expense'>('income')
  const [vendor, setVendor] = useState('')
  const [date, setDate] = useState('')
  const [currency, setCurrency] = useState('INR')
  const [items, setItems] = useState<Item[]>([])
  const [total, setTotal] = useState<string>('')

  const [showImage, setShowImage] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [dupResolving, setDupResolving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  // Populate form fields with essential everyday details
  const populate = (r: Receipt) => {
    setReceipt(r)
    setTransactionType(r.type === 'expense' ? 'expense' : 'income')
    setVendor(r.vendor || '')
    setDate(r.date || '')
    setCurrency(r.currency || 'INR')
    setItems(r.items && r.items.length ? r.items.map(it => ({
      name: it.name || '',
      amount: it.amount || 0,
    })) : [{ name: '', amount: 0 }])
    setTotal(r.total !== null && r.total !== undefined ? String(r.total) : '')
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
  // Item field update
  const updateItem = (index: number, patch: Partial<Item>) => {
    setItems(prev => {
      const copy = [...prev]
      copy[index] = { ...copy[index], ...patch }
      return copy
    })
  }

  const addItem = () => {
    setItems(prev => [...prev, { name: '', amount: 0 }])
  }

  const removeItem = (index: number) => {
    setItems(prev => prev.filter((_, i) => i !== index))
  }

  // Calculate items sum
  const itemsTotal = items.reduce((acc, it) => acc + (Number(it.amount) || 0), 0)

  // Auto-fill total from items sum if desired
  const applyCalculatedTotal = () => {
    if (itemsTotal > 0) {
      setTotal(String(Math.round(itemsTotal * 100) / 100))
    }
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

  const handleDeleteReceipt = async () => {
    if (!receipt || !receiptId || isDeleting) return
    if (!window.confirm(t('rv.deleteConfirm'))) return

    setIsDeleting(true)
    setSubmitError(null)
    try {
      await api.deleteReceipt(receipt.id)
      onDeleted()
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : t('common.error'))
      setIsDeleting(false)
    }
  }

  // Final Validation and Save & Confirm
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!receipt || isSubmitting) return

    setSubmitError(null)

    // Validation: simple essential merchant details
    const trimmedVendor = vendor.trim()
    const trimmedDate = date.trim()
    const numericTotal = total === '' ? null : Number(total)

    if (!trimmedVendor || !trimmedDate || numericTotal === null || isNaN(numericTotal) || numericTotal < 0) {
      setSubmitError(t('rv.validationError'))
      return
    }

    setIsSubmitting(true)

    try {
      // 1. Prepare finalized receipt payload using essential details
      const finalized: Receipt = {
        ...receipt,
        vendor: trimmedVendor,
        date: trimmedDate,
        currency: currency || 'INR',
        type: transactionType,
        category: receipt?.category || 'other',
        items: items
          .map(it => ({
            name: it.name.trim() || 'Item',
            amount: Number(it.amount) || 0,
          }))
          .filter(it => it.name.length > 0 || it.amount > 0),
        total: numericTotal,
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
                {receipt?.fileName || file?.name || 'Vyapar Mitra'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {receiptId && receipt && (
              <button
                type="button"
                className="min-h-[38px] px-3 rounded-xs border border-rose-300 bg-rose-50 text-rose-800 hover:bg-rose-100 text-sm font-semibold transition-colors cursor-pointer disabled:opacity-50"
                onClick={() => void handleDeleteReceipt()}
                disabled={isDeleting || isSubmitting}
              >
                {isDeleting ? t('rv.deleting') : t('rv.delete')}
              </button>
            )}
            <button
              type="button"
              className="w-9 h-9 rounded-xl border border-stone-200 text-stone-500 hover:text-stone-900 hover:bg-stone-100 flex items-center justify-center transition-colors cursor-pointer disabled:opacity-50"
              onClick={onClose}
              disabled={isSubmitting || isDeleting}
              aria-label={t('rv.close')}
            >
              <XIcon className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Content */}
        <div className="p-5 sm:p-6 overflow-y-auto flex-1 space-y-5">
          {submitError && (
            <div role="alert" className="rounded-xl border border-rose-300 bg-rose-50 p-3.5 text-rose-900 text-sm font-semibold flex items-center gap-2">
              <span>⚠</span>
              <span>{submitError}</span>
            </div>
          )}
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
                      {showImage ? t('rv.hidePreview') : t('rv.showPreview')}
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

              {/* Transaction Type: Money Received vs. Borrowed Items / Credit */}
              <div className="bg-white p-4 sm:p-5 rounded-2xl border-2 border-stone-200/90 shadow-2xs space-y-2.5">
                <span className="block text-xs sm:text-sm font-extrabold uppercase tracking-wider text-stone-800">
                  {t('rv.typeLabel')} <span className="text-emerald-700 font-black">*</span>
                </span>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setTransactionType('income')}
                    className={`min-h-[50px] px-3 py-2.5 rounded-xl font-bold text-xs sm:text-sm md:text-base flex items-center justify-center gap-2 transition-all cursor-pointer border-2 select-none active:scale-[0.99] ${
                      transactionType === 'income'
                        ? 'bg-emerald-700 border-emerald-800 text-white shadow-sm ring-2 ring-emerald-600/30'
                        : 'bg-stone-50 border-stone-200 text-stone-700 hover:bg-stone-100 hover:border-emerald-700/40'
                    }`}
                  >
                    <WalletIcon className="w-4 h-4 sm:w-5 sm:h-5 shrink-0" />
                    <span className="truncate">{t('rv.typeIncome')}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setTransactionType('expense')}
                    className={`min-h-[50px] px-3 py-2.5 rounded-xl font-bold text-xs sm:text-sm md:text-base flex items-center justify-center gap-2 transition-all cursor-pointer border-2 select-none active:scale-[0.99] ${
                      transactionType === 'expense'
                        ? 'bg-amber-700 border-amber-800 text-white shadow-sm ring-2 ring-amber-600/30'
                        : 'bg-stone-50 border-stone-200 text-stone-700 hover:bg-stone-100 hover:border-amber-700/40'
                    }`}
                  >
                    <ClockIcon className="w-4 h-4 sm:w-5 sm:h-5 shrink-0" />
                    <span className="truncate">{t('rv.typeExpense')}</span>
                  </button>
                </div>
              </div>

              {/* 1. Essential Ledger Entry: Party/Person Name, Date */}
              <div className="bg-white p-4 sm:p-5 rounded-2xl border-2 border-stone-200/90 shadow-2xs space-y-3.5">
                <div className="border-b border-stone-200 pb-2">
                  <h3 className="text-xs sm:text-sm font-black uppercase tracking-wider text-emerald-900 flex items-center gap-1.5">
                    <StoreIcon className="w-4 h-4 text-emerald-700" />
                    {t('rv.details')}
                  </h3>
                </div>

                <div>
                  <label className="block">
                    <span className="mb-1.5 flex items-center justify-between text-sm sm:text-base font-bold text-stone-900">
                      <span>{t('rv.vendor')} <span className="text-emerald-700 font-black">*</span></span>
                    </span>
                    <input
                      type="text"
                      className={field}
                      placeholder={lang === 'hi' ? 'उदा. रमेश, सुरेश भाई' : 'e.g. Ramesh, Suresh bhai'}
                      value={vendor}
                      onChange={e => setVendor(e.target.value)}
                      required
                    />
                  </label>
                </div>

                <div>
                  <label className="block">
                    <span className="mb-1.5 block text-sm sm:text-base font-bold text-stone-900">
                      {t('rv.date')} <span className="text-emerald-700 font-black">*</span>
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
              </div>

              {/* 2. Items & Goods Description */}
              <div className="bg-white p-4 sm:p-5 rounded-2xl border-2 border-stone-200/90 shadow-2xs space-y-3">
                <div className="flex items-center justify-between border-b border-stone-200 pb-2">
                  <h3 className="text-xs sm:text-sm font-black uppercase tracking-wider text-emerald-900 flex items-center gap-1.5">
                    <ReceiptIcon className="w-4 h-4 text-emerald-700" />
                    {t('rv.itemsSection')}
                  </h3>
                  <button
                    type="button"
                    className="text-xs sm:text-sm font-bold text-emerald-700 hover:text-emerald-800 cursor-pointer px-2.5 py-1 rounded-lg hover:bg-emerald-50 transition-colors"
                    onClick={addItem}
                  >
                    {t('rv.addItem')}
                  </button>
                </div>

                <div className="space-y-2.5">
                  {items.map((it, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <input
                        type="text"
                        className={`${field} flex-1 text-sm sm:text-base`}
                        placeholder={t('rv.item')}
                        value={it.name}
                        onChange={e => updateItem(idx, { name: e.target.value })}
                      />
                      <div className="w-28 sm:w-36 shrink-0 relative">
                        <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-sm font-bold text-stone-400">₹</span>
                        <input
                          type="number"
                          inputMode="decimal"
                          step="any"
                          min="0"
                          placeholder="0.00"
                          className={`${field} pl-6 text-sm sm:text-base font-bold text-stone-900`}
                          value={it.amount || ''}
                          onChange={e => updateItem(idx, { amount: Number(e.target.value) || 0 })}
                        />
                      </div>
                      {items.length > 1 && (
                        <button
                          type="button"
                          className="w-10 h-10 rounded-xl text-stone-400 hover:text-rose-700 hover:bg-rose-50 flex items-center justify-center shrink-0 transition-colors font-bold text-base cursor-pointer"
                          onClick={() => removeItem(idx)}
                          aria-label={t('rv.removeItem')}
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* 3. High-Contrast Prominent Total Card */}
              <div className="bg-emerald-50/85 rounded-2xl border-2 border-emerald-600/90 p-4 sm:p-5 shadow-xs space-y-2">
                <div className="flex items-center justify-between">
                  <label htmlFor="receipt-total-input" className="text-sm sm:text-base font-extrabold uppercase tracking-wide text-emerald-950 flex items-center gap-1.5">
                    <WalletIcon className="w-5 h-5 text-emerald-800" />
                    <span>{t('rv.total')} <span className="text-rose-600">*</span></span>
                  </label>
                  {itemsTotal > 0 && (
                    <button
                      type="button"
                      onClick={applyCalculatedTotal}
                      className="text-xs sm:text-sm font-bold text-emerald-800 hover:text-emerald-950 underline cursor-pointer"
                    >
                      {t('rv.autoFill')} (₹{itemsTotal.toLocaleString('en-IN')})
                    </button>
                  )}
                </div>

                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-2xl font-black text-emerald-700">₹</span>
                  <input
                    id="receipt-total-input"
                    type="number"
                    inputMode="decimal"
                    step="any"
                    min="0"
                    className="w-full min-h-[56px] sm:min-h-[60px] pl-9 pr-4 rounded-xl border-2 border-emerald-600 focus:border-emerald-700 focus:ring-2 focus:ring-emerald-700/30 text-2xl sm:text-3xl font-black text-emerald-950 bg-white shadow-inner"
                    placeholder="0.00"
                    value={total}
                    onChange={e => setTotal(e.target.value)}
                    required
                  />
                </div>
              </div>

            </form>
          )}
        </div>

        {/* Modal Footer / Large Touch-Friendly Save & Confirm Button */}
        {!loading && !initError && receipt?.status !== 'duplicate' && (
          <div className="p-4 sm:p-5 border-t border-stone-200/80 bg-white space-y-2.5">
            <button
              type="submit"
              form="review-receipt-form"
              className="w-full min-h-[54px] sm:min-h-[58px] bg-emerald-700 hover:bg-emerald-800 active:bg-emerald-900 text-white text-lg sm:text-xl font-black rounded-xl shadow-md flex items-center justify-center gap-2.5 cursor-pointer transition-all active:scale-[0.99] disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>{t('rv.addingReceipt')}</span>
                </>
              ) : (
                <>
                  <CheckCircleIcon className="w-6 h-6 text-emerald-200" />
                  <span>{t('rv.addReceipt')}</span>
                </>
              )}
            </button>
            <div className="text-center">
              <button
                type="button"
                className="text-xs sm:text-sm font-semibold text-stone-500 hover:text-stone-800 underline py-1.5 cursor-pointer"
                disabled={isSubmitting}
                onClick={onClose}
              >
                {t('rv.cancelFinishLater')}
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
    api.list({ status: 'pending' }),
    api.list({ status: 'confirmed' })
  ]), [refreshKey])
  const s = q.d?.[0], p = q.d?.[1], confirmed = q.d?.[2]

  return (
    <State {...q}>
      {s && p && (
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

          {/* Key Stat Cards: 2 Prominent Pillar Cards (Money Received & Borrowed Items) + Support Stats */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Pillar 1: Total Money Received (Green Card) */}
            <div className="rounded-2xl p-6 bg-gradient-to-br from-emerald-950 via-emerald-900 to-teal-950 text-white shadow-md shadow-emerald-950/20 border-2 border-emerald-700/60 flex flex-col justify-between relative overflow-hidden">
              <div className="relative z-10">
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="w-10 h-10 rounded-xl bg-emerald-800/90 border border-emerald-600/50 text-emerald-200 flex items-center justify-center">
                    <WalletIcon className="w-5 h-5" />
                  </span>
                  <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-md bg-emerald-800/90 text-emerald-200 border border-emerald-700/60">
                    {t('type.income')}
                  </span>
                </div>
                <p className="text-emerald-200 text-sm font-semibold">
                  {t('home.received')}
                </p>
                <p className="text-3xl sm:text-4xl font-black tracking-tight text-white mt-1.5">
                  {money(s.totalReceived ?? 0, lang, currency)}
                </p>
                <p className="text-xs text-emerald-300/80 mt-1">
                  {t('home.receivedSub')}
                </p>
              </div>
              <div className="relative z-10 pt-4 mt-3 border-t border-emerald-800/60 flex items-center text-xs text-emerald-200/90 font-medium">
                <span>{s.confirmedCount} {t('home.count').toLowerCase()}</span>
              </div>
            </div>

            {/* Pillar 2: Total Active Credit / Borrowed Items (Amber Card) */}
            <div className="rounded-2xl p-6 bg-gradient-to-br from-stone-900 via-amber-950 to-stone-950 text-white shadow-md shadow-amber-950/20 border-2 border-amber-600/70 flex flex-col justify-between relative overflow-hidden">
              <div className="relative z-10">
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="w-10 h-10 rounded-xl bg-amber-900/90 border border-amber-600/50 text-amber-200 flex items-center justify-center">
                    <ClockIcon className="w-5 h-5" />
                  </span>
                  <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-md bg-amber-900/90 text-amber-200 border border-amber-700/60">
                    {t('type.borrowed')}
                  </span>
                </div>
                <p className="text-amber-200 text-sm font-semibold">
                  {t('home.borrowed')}
                </p>
                <p className="text-3xl sm:text-4xl font-black tracking-tight text-amber-100 mt-1.5">
                  {money(s.totalBorrowed ?? s.totalSpent ?? 0, lang, currency)}
                </p>
                <p className="text-xs text-amber-300/80 mt-1">
                  {t('home.borrowedSub')}
                </p>
              </div>
              <div className="relative z-10 pt-4 mt-3 border-t border-amber-800/60 flex items-center text-xs text-amber-200/90 font-medium">
                <span>{t('type.expense')}</span>
              </div>
            </div>

            {/* Support Card 1: Confirmed Entries */}
            <a
              href="#/ledger"
              className={`${card} flex flex-col justify-between hover:border-emerald-600/60 hover:shadow-md transition-all group`}
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200/70 flex items-center justify-center">
                    <CheckCircleIcon className="w-5 h-5" />
                  </span>
                  <ArrowRightIcon className="w-4 h-4 text-stone-400 group-hover:text-emerald-700 transition-colors" />
                </div>
                <p className="text-stone-600 text-sm font-semibold">{t('home.count')}</p>
                <p className="text-3xl sm:text-4xl font-black text-stone-900 group-hover:text-emerald-800 transition-colors mt-1">
                  {s.confirmedCount}
                </p>
              </div>
              <span className="text-xs font-bold text-emerald-700 mt-4 block">
                {t('home.viewAll')} →
              </span>
            </a>

            {/* Support Card 2: Receipts / Notes Awaiting Review */}
            <div
              className={`${card} flex flex-col justify-between hover:border-amber-500/60 hover:shadow-md transition-all`}
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="w-10 h-10 rounded-xl bg-amber-50 text-amber-800 border border-amber-200/70 flex items-center justify-center">
                    <ReceiptIcon className="w-5 h-5" />
                  </span>
                  {s.reviewCount > 0 ? (
                    <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-amber-100 text-amber-900 border border-amber-300">
                      {t('home.pendingBadge')}
                    </span>
                  ) : (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800">
                      {t('home.allClear')}
                    </span>
                  )}
                </div>
                <p className="text-stone-600 text-sm font-semibold">{t('home.review')}</p>
                <p className="text-3xl sm:text-4xl font-black text-stone-900 mt-1">
                  {s.reviewCount}
                </p>
              </div>
              {s.reviewCount > 0 ? (
                <a href="#waiting-section" className="text-xs font-bold text-amber-800 mt-4 block underline">
                  {t('home.reviewNow')} ↓
                </a>
              ) : (
                <span className="text-xs text-stone-500 mt-4 block">{t('home.none')}</span>
              )}
            </div>
          </div>

          {/* Payments Waiting for Review Section */}
          <section id="waiting-section" className="scroll-mt-6">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className={h2}>{t('home.waiting')}</h2>
              </div>
              {p.length > 0 && (
                <span className="text-xs sm:text-sm font-bold bg-amber-100 text-amber-900 px-3 py-1 rounded-xs">
                  {p.length} {t('home.review').toLowerCase()}
                </span>
              )}
            </div>
            {p.length ? (
              <RList rs={p} onSelect={onSelectReceipt} />
            ) : (
              <div className={`${card} text-center py-8 text-stone-700 bg-emerald-50/30 border border-dashed border-emerald-200`}>
                <CheckCircleIcon className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
                <p className="text-base sm:text-lg font-bold text-emerald-900">{t('home.none')}</p>
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

          {/* Top Vendors / Suppliers */}
          {s.topVendors && s.topVendors.length > 0 && (
            <section>
              <div className="flex items-center justify-between mb-3">
                <h2 className={h2}>{t('home.vendors')}</h2>
                <a href="#/ledger" className="text-sm font-semibold text-emerald-800 hover:underline">
                  {t('home.viewAll')} →
                </a>
              </div>
              <TopVendorsList
                rows={s.topVendors.map(v => ({
                  label: v.vendor,
                  amount: v.amount,
                  href: `#/ledger?vendor=${encodeURIComponent(v.vendor)}`
                }))}
              />
            </section>
          )}
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
  const blank: Filters = { q: '', from: '', to: '', vendor: '' }
  const [fl, setFl] = useState<Filters>({ ...blank, vendor: p.get('vendor') || '' })
  const [ex, setEx] = useState<'idle' | 'busy' | 'ok' | 'err'>('idle')

  const vendors = useLoad(() => api.summary(), [refreshKey])
  const r = useLoad(() => api.list({ ...fl, status: 'confirmed' }), [JSON.stringify(fl), refreshKey])

  const up = (k: keyof Filters, v: string) => setFl(x => ({ ...x, [k]: v }))
  const doExport = async () => {
    if (ex === 'busy') return
    setEx('busy')
    try {
      await api.exportPdf()
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
          <span>{ex === 'busy' ? t('lg.exporting') : t('lg.exportPdf')}</span>
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
      <div className={`${card} grid gap-4 sm:grid-cols-2 lg:grid-cols-4`}>
        <div className="sm:col-span-2">
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

        <div className="sm:col-span-2">
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

        <div className="flex items-end sm:col-span-2 lg:col-span-2">
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

      {/* 1. User Input Box on the TOP */}
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
                <span>{t('qa.assistant')}</span>
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

      {/* 2. Question Suggestions on the BOTTOM */}
      <div className="space-y-2.5 pt-4 border-t border-stone-200/80">
        <span className="text-xs font-semibold uppercase tracking-wider text-stone-500">
          {lang === 'hi' ? 'सुझाव (पूछने के लिए छुएँ)' : 'Suggested Questions (Tap to ask)'}
        </span>
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
    </div>
  )
}

export default function App(){
  const { t, lang, setLang, setCurrency } = useI18n()
  const [authLoading,setAuthLoading]=useState(true)
  const [authError,setAuthError]=useState('')
  const [account,setAccount]=useState<Account|null>(null)
  const loadAuth=useCallback(async()=>{
    setAuthLoading(true)
    setAuthError('')
    try{
      const state=await api.authStatus()
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
      setAuthError('')
    }
    window.addEventListener('vyapar-mitra:unauthorized',expired)
    return ()=>{
      window.removeEventListener('vyapar-mitra:unauthorized',expired)
    }
  },[])
  const h = useHash()
  const [path, query = ''] = h.split('?')
  const rm = path.match(/^\/receipt\/(.+)$/)

  // Modal & Notification State
  const [activeModal, setActiveModal] = useState<{ id?: string; file?: File } | null>(null)
  const [toastMessage, setToastMessage] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  // Header state & click-outside detection
  const [menuOpen, setMenuOpen] = useState(false)
  const headerRef = useRef<HTMLElement>(null)

  // Close mobile dropdown menu on click outside or Escape key
  useEffect(() => {
    if (!menuOpen) return
    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      if (headerRef.current && !headerRef.current.contains(event.target as Node)) {
        setMenuOpen(false)
      }
    }
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('touchstart', handleClickOutside)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('touchstart', handleClickOutside)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [menuOpen])

  // Automatically close mobile menu when expanding to tablet/desktop (>= 640px)
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 640) {
        setMenuOpen(false)
      }
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

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

  const handleModalDeleted = () => {
    setActiveModal(null)
    setRefreshKey(prev => prev + 1)
    if (location.hash.startsWith('#/receipt/')) {
      location.hash = '#/'
    }
  }

  const handleAuthenticated = (nextAccount:Account) => {
    setAccount(nextAccount)
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
    return <AuthPage error={authError} onRetry={()=>void loadAuth()} onAuthenticated={handleAuthenticated}/>
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
          <div className="bg-emerald-800 text-white px-5 py-3.5 rounded-xs shadow-xl flex items-center justify-between gap-3 border border-emerald-700">
            <div className="flex items-center gap-2.5">
              <CheckCircleIcon className="w-5 h-5 text-emerald-300 shrink-0" />
              <p className="text-sm font-semibold">{toastMessage}</p>
            </div>
            <button
              onClick={() => setToastMessage(null)}
              className="text-emerald-200 hover:text-white p-1 cursor-pointer"
              aria-label={t('common.dismiss')}
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
          onDeleted={handleModalDeleted}
        />
      )}

      {/* Top Header Bar - Clean, Left-Aligned Logo & Responsive Navigation */}
      <header
        ref={headerRef}
        className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-stone-200/90 shadow-[0_1px_4px_rgba(0,0,0,0.03)] transition-all"
      >
        <div className="w-full flex items-center justify-between px-3 sm:px-6 lg:px-8 py-2.5 sm:py-3">
          {/* Brand Logo strictly pinned to the far left corner */}
          <a
            href="#/"
            onClick={() => setMenuOpen(false)}
            className="flex items-center gap-2.5 sm:gap-3 group select-none transition-transform active:scale-[0.99] shrink-0"
            aria-label="Vyapar Mitra Home"
          >
            {/* Sleek Geometric Logo Icon */}
            <div className="relative shrink-0 flex items-center justify-center">
              <VyaparMitraLogo className="w-9 h-9 sm:w-10 sm:h-10 drop-shadow-sm group-hover:scale-105 group-hover:drop-shadow transition-all duration-200" />
              <span
                className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-white ring-1 ring-emerald-600/20"
                title="Synced & Active"
              />
            </div>

            {/* Refined Brand Typography & SaaS Accent */}
            <div className="leading-tight flex flex-col justify-center">
              <div className="flex items-center gap-1 sm:gap-1.5">
                <span className="text-lg sm:text-[21px] font-black tracking-tight text-stone-900 group-hover:text-emerald-950 transition-colors">
                  {lang === 'hi' ? 'व्यापार' : 'Vyapar'}
                </span>
                <span className="text-lg sm:text-[21px] font-black tracking-tight bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 bg-clip-text text-transparent">
                  {lang === 'hi' ? 'मित्र' : 'Mitra'}
                </span>
                <span className="hidden xl:inline-flex items-center px-1.5 py-0.5 rounded-xs text-[10px] font-extrabold uppercase tracking-wide bg-emerald-50 text-emerald-800 border border-emerald-200/80 shadow-2xs">
                  {lang === 'hi' ? 'डिजिटल बहीखाता' : 'Smart Ledger'}
                </span>
              </div>
              <span className="text-[10px] sm:text-[11px] font-semibold text-stone-500 tracking-normal hidden md:block">
                {lang === 'hi' ? 'दुकानदार का भरोसेमंद साथी' : 'Digital Retail Ledger & Business Companion'}
              </span>
            </div>
          </a>

          {/* Laptop & Desktop Layout (640px and wider): Clean horizontal navigation tabs */}
          <nav aria-label={t('nav.label')} className="hidden sm:flex items-center gap-1 md:gap-1.5 lg:gap-2">
            {nav.map(item => {
              const active = path === item.p
              const Icon = item.icon
              return (
                <a
                  key={item.p}
                  href={'#' + item.p}
                  aria-current={active ? 'page' : undefined}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs md:text-sm font-semibold transition-all duration-150 select-none ${
                    active
                      ? 'bg-emerald-50 text-emerald-900 border border-emerald-300 shadow-2xs'
                      : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4 h-4 shrink-0 transition-colors ${active ? 'text-emerald-700' : 'text-stone-400'}`} />
                  <span className="whitespace-nowrap">{t(item.k)}</span>
                </a>
              )
            })}
          </nav>

          {/* Mobile Layout (< 640px / sm): Hamburger toggle button on the right */}
          <div className="flex sm:hidden items-center gap-2">
            <button
              type="button"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-expanded={menuOpen}
              aria-label={t('nav.label')}
              className={`flex items-center justify-center p-2 rounded-xl border font-semibold shadow-2xs cursor-pointer transition-all active:scale-95 ${
                menuOpen
                  ? 'bg-emerald-50 text-emerald-900 border-emerald-300 ring-2 ring-emerald-500/20'
                  : 'bg-white hover:bg-stone-50 border-stone-300 text-stone-800 hover:border-emerald-600/40'
              }`}
            >
              {menuOpen ? (
                <XIcon className="w-5 h-5 text-emerald-800" />
              ) : (
                <MenuIcon className="w-5 h-5 text-stone-700" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Menu (screens smaller than 640px) */}
        {menuOpen && (
          <div
            className="sm:hidden border-t border-stone-200/90 bg-white/98 backdrop-blur-md shadow-lg animate-in slide-in-from-top-2 duration-150"
            role="dialog"
            aria-label={t('nav.label')}
          >
            <div className="px-4 py-3">
              <nav aria-label={t('nav.label')} className="flex flex-col space-y-1">
                {nav.map(item => {
                  const active = path === item.p
                  const Icon = item.icon
                  return (
                    <a
                      key={item.p}
                      href={'#' + item.p}
                      aria-current={active ? 'page' : undefined}
                      onClick={() => setMenuOpen(false)}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-colors active:scale-[0.99] ${
                        active
                          ? 'bg-emerald-50 text-emerald-900 border border-emerald-300 shadow-2xs'
                          : 'text-stone-700 hover:text-stone-900 hover:bg-stone-50 border border-transparent'
                      }`}
                    >
                      <Icon className={`w-5 h-5 shrink-0 ${active ? 'text-emerald-700' : 'text-stone-400'}`} />
                      <span className="flex-1">{t(item.k)}</span>
                      {active && (
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                      )}
                    </a>
                  )
                })}
              </nav>
            </div>
          </div>
        )}
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
          <SettingsPage account={account} onAccountUpdated={updated=>{setAccount(updated);setCurrency(updated.currency);setLang(updated.language)}} onSignOut={handleSignOut}/>
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
