import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Suaviza series reemplazando valores 0 por la media de los dos valores previos mostrados
// Mantiene el tipo de cada elemento y no muta el array original
export function smoothZerosWithPrevAvg<T extends { value: number }>(series: T[]): T[] {
  const result: T[] = []
  const history: number[] = []
  for (const item of series) {
    const raw = typeof item.value === 'number' && isFinite(item.value) ? item.value : 0
    let nextValue = raw
    if (raw === 0) {
      const last = history.length >= 1 ? history[history.length - 1] : undefined
      const prev = history.length >= 2 ? history[history.length - 2] : undefined
      if (last !== undefined && prev !== undefined) {
        nextValue = (last + prev) / 2
      } else if (last !== undefined) {
        nextValue = last
      }
    }
    // Clamp opcional por seguridad
    if (nextValue < 0) nextValue = 0
    if (nextValue > 100) nextValue = 100
    history.push(nextValue)
    result.push({ ...item, value: nextValue })
  }
  return result
}
