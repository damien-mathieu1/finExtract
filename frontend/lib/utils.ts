import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Amounts arrive in full currency units and may be USD or JPY, so no symbol here.
export function formatAmount(val: number) {
  const abs = Math.abs(val)
  if (abs < 1_000_000) return val.toLocaleString()
  const millions = (abs / 1_000_000).toLocaleString(undefined, { maximumFractionDigits: 0 })
  return `${val < 0 ? '-' : ''}${millions}M`
}
