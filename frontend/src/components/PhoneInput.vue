<script setup lang="ts">
/**
 * Поле телефона с маской +7 (9XX) XXX-XX-XX.
 * v-model — нормализованное значение 79XXXXXXXXX.
 * Курсор привязан к цифрам; Backspace/Delete удаляют по одной цифре.
 */
import { ref, watch, computed, nextTick } from 'vue'
import {
  normalizePhone,
  formatPhoneDisplay,
  toNormalized11,
  isCompletePhone,
  getDigitIndexAtPosition,
  getPositionAfterDigit,
  removeDigitAt,
} from '@/utils/phoneMask'

const props = withDefaults(
  defineProps<{
    modelValue: string
    placeholder?: string
    disabled?: boolean
    id?: string
    error?: string
  }>(),
  {
    placeholder: '+7 (999) 123-45-67',
    disabled: false,
    id: undefined,
    error: '',
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'update:complete': [value: boolean]
}>()

const displayValue = ref('')

function displayToNormalized(display: string): string {
  return toNormalized11(display)
}

function syncFromModel(): void {
  const n = normalizePhone(props.modelValue)
  displayValue.value = formatPhoneDisplay(n)
}

syncFromModel()
watch(
  () => props.modelValue,
  () => syncFromModel()
)

function onInput(event: Event): void {
  const input = event.target as HTMLInputElement
  const cursorBefore = input.selectionStart ?? 0
  const newRaw = input.value
  const normalized = displayToNormalized(newRaw)
  const limited = normalized.slice(0, 11)
  const digitsBeforeCursor = getDigitIndexAtPosition(newRaw, cursorBefore)
  displayValue.value = formatPhoneDisplay(limited)
  emit('update:modelValue', limited)
  emit('update:complete', isCompletePhone(limited))

  nextTick(() => {
    const newCursor = getPositionAfterDigit(displayValue.value, Math.min(digitsBeforeCursor, limited.length))
    input.setSelectionRange(newCursor, newCursor)
  })
}

function onKeydown(event: KeyboardEvent): void {
  const input = event.target as HTMLInputElement
  const cursor = input.selectionStart ?? 0
  const selectionLen = (input.selectionEnd ?? cursor) - cursor
  const normalized = displayToNormalized(displayValue.value)
  if (normalized.length === 0) return

  if (event.key === 'Backspace' && selectionLen === 0) {
    const digitIndex = getDigitIndexAtPosition(displayValue.value, cursor)
    if (digitIndex <= 1) return
    event.preventDefault()
    const nextNormalized = removeDigitAt(normalized, digitIndex - 1)
    displayValue.value = formatPhoneDisplay(nextNormalized)
    emit('update:modelValue', nextNormalized)
    emit('update:complete', isCompletePhone(nextNormalized))
    nextTick(() => {
      const newCursor = getPositionAfterDigit(displayValue.value, digitIndex - 1)
      input.setSelectionRange(newCursor, newCursor)
    })
    return
  }

  if (event.key === 'Delete' && selectionLen === 0) {
    const digitIndex = getDigitIndexAtPosition(displayValue.value, cursor)
    if (digitIndex >= normalized.length) return
    event.preventDefault()
    const nextNormalized = removeDigitAt(normalized, digitIndex)
    displayValue.value = formatPhoneDisplay(nextNormalized)
    emit('update:modelValue', nextNormalized)
    emit('update:complete', isCompletePhone(nextNormalized))
    nextTick(() => {
      const newCursor = getPositionAfterDigit(displayValue.value, digitIndex)
      input.setSelectionRange(newCursor, newCursor)
    })
  }
}

function onPaste(event: ClipboardEvent): void {
  event.preventDefault()
  const input = event.target as HTMLInputElement
  const pasted = (event.clipboardData?.getData('text') ?? '').trim()
  const normalized = normalizePhone(pasted)
  const limited = normalized.slice(0, 11)
  displayValue.value = formatPhoneDisplay(limited)
  emit('update:modelValue', limited)
  emit('update:complete', isCompletePhone(limited))
  nextTick(() => {
    input.setSelectionRange(displayValue.value.length, displayValue.value.length)
  })
}

const inputId = computed(() => props.id ?? `phone-${Math.random().toString(36).slice(2)}`)
const hasError = computed(() => !!props.error)
</script>

<template>
  <div class="phone-input">
    <input
      :id="inputId"
      type="tel"
      autocomplete="tel"
      :value="displayValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :aria-invalid="hasError"
      :aria-describedby="error ? `${inputId}-error` : undefined"
      class="phone-input__field"
      inputmode="numeric"
      @input="onInput"
      @keydown="onKeydown"
      @paste="onPaste"
    >
    <span
      v-if="error"
      :id="`${inputId}-error`"
      class="phone-input__error"
      role="alert"
    >
      {{ error }}
    </span>
  </div>
</template>

<style scoped>
.phone-input {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.phone-input__field {
  width: 100%;
  height: 2.75rem;
  min-height: 44px;
  padding: 0 var(--spacing-lg);
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--color-text);
  background: var(--color-background-input);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  box-sizing: border-box;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.phone-input__field::placeholder {
  color: var(--color-text-light);
}

.phone-input__field:hover {
  border-color: var(--color-border-dark);
}

.phone-input__field:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}

.phone-input__field:focus:not(:focus-visible) {
  box-shadow: none;
}

.phone-input__field[aria-invalid="true"] {
  border-color: var(--color-error);
}

.phone-input__field:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.phone-input__error {
  font-size: var(--font-size-sm);
  color: var(--color-error);
}
</style>
