<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import type { RefItem } from '@/types/admin'

const props = withDefaults(
  defineProps<{
    modelValue: number[]
    items: RefItem[]
    id?: string
    placeholder?: string
    disabled?: boolean
    creatable?: boolean
    searchAriaLabel?: string
    removeAriaLabelPrefix?: string
  }>(),
  {
    id: 'chip-select',
    placeholder: 'Найти…',
    disabled: false,
    creatable: false,
    searchAriaLabel: 'Поиск для добавления',
    removeAriaLabelPrefix: 'Удалить ',
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: number[]]
  create: [name: string]
}>()

const searchQuery = ref('')
const isDropdownOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)

const valueIds = computed(() => props.modelValue ?? [])

const selectedItems = computed(() => {
  return valueIds.value
    .map((id) => props.items.find((a) => a.id === id))
    .filter((a): a is RefItem => a != null)
})

const availableToAdd = computed(() => {
  const q = (searchQuery.value || '').trim().toLowerCase()
  const selectedIds = new Set(valueIds.value)
  let list = props.items.filter((a) => !selectedIds.has(a.id))
  if (q) {
    list = list.filter((a) => a.name.toLowerCase().includes(q))
  }
  return list
})

function addItem(id: number): void {
  if (valueIds.value.includes(id)) return
  emit('update:modelValue', [...valueIds.value, id])
  searchQuery.value = ''
  isDropdownOpen.value = false
  nextTick(() => inputRef.value?.focus())
}

function removeItem(id: number): void {
  emit(
    'update:modelValue',
    valueIds.value.filter((x) => x !== id)
  )
}

function onInputFocus(): void {
  if (props.disabled) return
  isDropdownOpen.value = true
}

function onInputBlur(): void {
  setTimeout(() => {
    isDropdownOpen.value = false
  }, 200)
}

function onInputKeydown(e: KeyboardEvent): void {
  if (e.key === 'Escape') {
    isDropdownOpen.value = false
    inputRef.value?.blur()
    return
  }
  if (e.key === 'Enter') {
    e.preventDefault()
    const q = searchQuery.value.trim()
    if (!q) return
    const exact = props.items.find(
      (i) => i.name.localeCompare(q, undefined, { sensitivity: 'accent' }) === 0
    )
    if (exact && !valueIds.value.includes(exact.id)) {
      addItem(exact.id)
      return
    }
    if (props.creatable) {
      emit('create', q)
      searchQuery.value = ''
      isDropdownOpen.value = false
    }
  }
}

function handleClickOutside(event: MouseEvent): void {
  const el = dropdownRef.value
  if (el && !el.contains(event.target as Node)) {
    isDropdownOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div ref="dropdownRef" class="chip-select">
    <div class="chip-select__chips">
      <span
        v-for="item in selectedItems"
        :key="item.id"
        class="chip-select__chip"
      >
        {{ item.name }}
        <button
          type="button"
          class="chip-select__chip-remove"
          :aria-label="removeAriaLabelPrefix + item.name"
          :disabled="disabled"
          @click.prevent="removeItem(item.id)"
        >
          ×
        </button>
      </span>
    </div>
    <input
      :id="id"
      ref="inputRef"
      v-model="searchQuery"
      type="text"
      class="chip-select__input"
      :placeholder="placeholder"
      :disabled="disabled"
      autocomplete="off"
      :aria-label="searchAriaLabel"
      @focus="onInputFocus"
      @blur="onInputBlur"
      @keydown="onInputKeydown"
    >
    <div
      v-show="isDropdownOpen && availableToAdd.length > 0"
      class="chip-select__dropdown"
      role="listbox"
    >
      <button
        v-for="item in availableToAdd"
        :key="item.id"
        type="button"
        class="chip-select__option"
        role="option"
        @mousedown.prevent="addItem(item.id)"
      >
        {{ item.name }}
      </button>
    </div>
    <div
      v-show="isDropdownOpen && searchQuery.trim() && availableToAdd.length === 0"
      class="chip-select__empty"
    >
      {{ creatable ? 'Нажмите Enter для создания' : 'Ничего не найдено' }}
    </div>
  </div>
</template>

<style scoped>
.chip-select {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-base);
  color: var(--color-text);
  background: var(--color-background-input);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  min-height: 44px;
}

.chip-select:focus-within {
  box-shadow: var(--shadow-focus);
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.chip-select__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.chip-select__chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  font-size: var(--font-size-sm);
  color: var(--color-text);
  background: var(--color-background-chip, #e8e8e8);
  border-radius: var(--radius-sm);
}

.chip-select__chip-remove {
  padding: 0 2px;
  font-size: 1.125rem;
  line-height: 1;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  border-radius: 2px;
}

.chip-select__chip-remove:hover:not(:disabled) {
  color: var(--color-error);
}

.chip-select__chip-remove:focus-visible {
  outline: var(--focus-outline);
  outline-offset: 2px;
}

.chip-select__chip-remove:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.chip-select__input {
  flex: 1;
  min-width: 120px;
  padding: 4px 0;
  font-size: inherit;
  color: inherit;
  background: transparent;
  border: none;
  outline: none;
}

.chip-select__input::placeholder {
  color: var(--color-text-muted);
}

.chip-select__dropdown {
  position: absolute;
  z-index: 10;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  max-height: 220px;
  overflow-y: auto;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-dropdown, 0 4px 12px rgba(0, 0, 0, 0.15));
}

.chip-select__option {
  display: block;
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-base);
  text-align: left;
  color: var(--color-text);
  background: none;
  border: none;
  cursor: pointer;
}

.chip-select__option:hover {
  background: var(--color-background-input);
}

.chip-select__option:focus-visible {
  outline: var(--focus-outline);
  outline-offset: -2px;
}

.chip-select__empty {
  position: absolute;
  z-index: 10;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  padding: var(--spacing-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}
</style>
