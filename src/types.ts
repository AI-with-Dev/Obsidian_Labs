export type Status = 'draft' | 'confirmed' | 'duplicate'
export type TransactionType = 'income' | 'expense'

export interface Item {
  name: string
  amount: number
  quantity?: number
  unitPrice?: number
}

export interface Receipt {
  id: string
  vendor: string // Customer / Payer name (or vendor for historical expenses)
  date: string
  currency: string
  items: Item[]
  total: number | null
  category: string
  status: Status
  type?: TransactionType // 'income' (green, money received) | 'expense' (red, outgoing)
  fileUrl: string
  fileName: string
  flags: string[]
  duplicateOfId?: string
  invoiceNumber?: string
  subtotal?: number
  tax?: number
  discount?: number
  paymentMethod?: string
  notes?: string
}

export interface Summary {
  totalSpent: number
  totalReceived?: number
  confirmedCount: number
  reviewCount: number
  topVendors: { vendor: string; amount: number }[]
  topCustomers?: { customer: string; amount: number }[]
}

export interface CategoryTotal {
  category: string
  amount: number
}

export interface Answer {
  answer: string
  supported: boolean
  receipts: Receipt[]
}

export interface Filters {
  q?: string
  from?: string
  to?: string
  category?: string
  vendor?: string
  status?: 'confirmed' | 'pending'
  type?: 'income' | 'expense'
}

export const CATEGORIES = [
  'retail_sales',
  'wholesale_collection',
  'advance_payment',
  'credit_recovery',
  'service_fee',
  'inventory',
  'packaging',
  'transport',
  'utilities',
  'rent',
  'repairs',
  'other',
]
