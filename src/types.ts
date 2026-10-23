export type Status = 'draft' | 'confirmed' | 'duplicate'
export interface Item {
  name: string
  amount: number
  quantity?: number
  unitPrice?: number
}
export interface Receipt {
  id: string
  vendor: string
  date: string
  currency: string
  items: Item[]
  total: number | null
  category: string
  status: Status
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
  confirmedCount: number
  reviewCount: number
  topVendors: { vendor: string; amount: number }[]
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
}
// Add a key here + "cat.<key>" in both locale files to extend categories.
export const CATEGORIES = ['inventory', 'packaging', 'transport', 'utilities', 'rent', 'repairs', 'other']
