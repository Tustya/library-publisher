/**
 * Нормализация и маска телефона: единый формат 79XXXXXXXXX.
 * Ввод: +7, 8, вставка из буфера — приводятся к одному виду.
 */
const DIGITS_ONLY = /\D/g
const RUS_CODE = '7'
const RUS_MOBILE_PREFIX = '9'

export function normalizePhone(raw: string): string {
  const digits = raw.replace(DIGITS_ONLY, '')
  if (!digits.length) return ''
  let normalized = digits
  if (normalized.startsWith('8') && normalized.length >= 10) {
    normalized = RUS_CODE + normalized.slice(1)
  } else if (normalized.startsWith('7') && normalized.length >= 10) {
    // уже 79XXXXXXXX или 79XXXXXXXXX — не дописывать 7
  } else if (normalized.length === 10 && normalized.startsWith(RUS_MOBILE_PREFIX)) {
    normalized = RUS_CODE + normalized
  } else if (normalized.length === 10) {
    normalized = RUS_CODE + normalized
  }
  return normalized.slice(0, 11)
}

/** Проверка: полный номер 79XXXXXXXXX (11 цифр). */
export function isCompletePhone(phone: string): boolean {
  const n = normalizePhone(phone)
  return n.length === 11 && n.startsWith('79')
}

/**
 * Форматирование для отображения: +7 (9XX) XXX-XX-XX.
 */
export function formatPhoneDisplay(normalized: string): string {
  const d = normalized.replace(DIGITS_ONLY, '').slice(0, 11)
  if (d.length === 0) return ''
  if (d.length === 1) return d === '7' ? '+7 (' : `+7 (${d}`
  if (d.length <= 4) return `+7 (${d.slice(1)}`
  if (d.length <= 7) return `+7 (${d.slice(1, 4)}) ${d.slice(4)}`
  return `+7 (${d.slice(1, 4)}) ${d.slice(4, 7)}-${d.slice(7, 9)}-${d.slice(9, 11)}`
}

/**
 * Из отображаемой строки или ввода получить 11 цифр 79XXXXXXXXX.
 */
export function toNormalized11(digitsOnly: string): string {
  const digits = digitsOnly.replace(DIGITS_ONLY, '')
  if (!digits.length) return ''
  if (digits.startsWith('8') && digits.length >= 10) {
    return (RUS_CODE + digits.slice(1)).slice(0, 11)
  }
  if (digits.startsWith('7') && digits.length >= 10) {
    return digits.slice(0, 11)
  }
  if (digits.length === 10 && digits.startsWith(RUS_MOBILE_PREFIX)) {
    return RUS_CODE + digits
  }
  if (digits.length >= 10) {
    return (RUS_CODE + digits).slice(0, 11)
  }
  if (digits.startsWith(RUS_MOBILE_PREFIX)) {
    return (RUS_CODE + digits).slice(0, 11)
  }
  return digits
}

/**
 * Количество цифр в display строго до позиции cursorPosition (для восстановления курсора).
 */
export function getDigitIndexAtPosition(display: string, cursorPosition: number): number {
  let count = 0
  const pos = Math.max(0, Math.min(cursorPosition, display.length))
  for (let i = 0; i < pos; i++) {
    if (/\d/.test(display[i])) count++
  }
  return count
}

/**
 * Позиция в display сразу после digitIndex-й цифры (0-based); если digitIndex >= числа цифр — конец строки.
 */
export function getPositionAfterDigit(display: string, digitIndex: number): number {
  let count = 0
  for (let i = 0; i < display.length; i++) {
    if (/\d/.test(display[i])) {
      if (count === digitIndex) return i + 1
      count++
    }
  }
  return display.length
}

/**
 * Удалить цифру в normalized по индексу (0-based). Для Backspace/Delete.
 */
export function removeDigitAt(normalized: string, digitIndex: number): string {
  if (digitIndex < 0 || digitIndex >= normalized.length) return normalized
  return normalized.slice(0, digitIndex) + normalized.slice(digitIndex + 1)
}
