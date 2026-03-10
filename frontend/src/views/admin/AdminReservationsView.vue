<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchAdminReservations, confirmReservationIssue, confirmReservationReturn } from '@/api/admin'
import type { AdminReservationItem } from '@/types/admin'

const router = useRouter()
const STATUS_OPTIONS = ['created', 'issued', 'returned', 'cancelled'] as const

const reservations = ref<AdminReservationItem[]>([])
const loading = ref(false)
const actionId = ref<number | null>(null)

const statusFilter = ref<string>('created')

const coverPreview = ref<{ url: string; alt: string } | null>(null)

function openCoverPreview(url: string, alt: string): void {
  coverPreview.value = { url, alt }
}

function closeCoverPreview(): void {
  coverPreview.value = null
}

function goToBook(bookId: number): void {
  router.push({ name: 'book', params: { id: String(bookId) } })
}

const previewOverlayRef = ref<HTMLElement | null>(null)
watch(coverPreview, (val) => {
  if (val) nextTick(() => previewOverlayRef.value?.focus())
})

const statusLabels: Record<string, string> = {
  created: 'Оформлена',
  issued: 'Выдана',
  returned: 'Возвращена',
  cancelled: 'Отменена',
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function statusLabel(s: string): string {
  return statusLabels[s] ?? s
}

const filteredReservations = computed(() =>
  reservations.value.filter((r) => r.status === statusFilter.value)
)

async function load(): Promise<void> {
  loading.value = true
  try {
    reservations.value = await fetchAdminReservations()
  } catch {
    reservations.value = []
  } finally {
    loading.value = false
  }
}

async function confirmIssue(r: AdminReservationItem): Promise<void> {
  if (r.status !== 'created' || actionId.value) return
  actionId.value = r.id
  try {
    await confirmReservationIssue(r.id)
    await load()
  } finally {
    actionId.value = null
  }
}

async function confirmReturn(r: AdminReservationItem): Promise<void> {
  if (r.status !== 'issued' || actionId.value) return
  actionId.value = r.id
  try {
    await confirmReservationReturn(r.id)
    await load()
  } finally {
    actionId.value = null
  }
}

onMounted(load)
</script>

<template>
  <div class="admin-reservations">
    <h2 class="admin-reservations__title">Брони и доставки</h2>
    <div class="admin-reservations__filter" role="group" aria-label="Фильтр по статусу брони">
      <span class="admin-reservations__filter-label">Статус:</span>
      <label
        v-for="status in STATUS_OPTIONS"
        :key="status"
        class="admin-reservations__filter-check"
      >
        <input
          v-model="statusFilter"
          type="radio"
          :value="status"
          class="admin-reservations__filter-input"
        >
        <span
          :class="[
            'admin-reservations__filter-badge',
            `admin-reservations__status--${status}`,
            { 'admin-reservations__filter-badge--active': statusFilter === status }
          ]"
        >
          {{ statusLabel(status) }}
        </span>
      </label>
    </div>
    <p v-if="loading" class="admin-reservations__loading">
      Загрузка…
    </p>
    <p v-else-if="reservations.length === 0" class="admin-reservations__empty">
      Нет броней
    </p>
    <p v-else-if="filteredReservations.length === 0" class="admin-reservations__empty">
      Нет броней с выбранным статусом
    </p>
    <ul v-else class="admin-reservations__list">
      <li
        v-for="r in filteredReservations"
        :key="r.id"
        :class="['admin-reservations__item', r.is_overdue && 'admin-reservations__item--overdue']"
      >
        <div class="admin-reservations__book-block">
          <div class="admin-reservations__cover-wrap">
            <button
              v-if="r.book_cover_url"
              type="button"
              class="admin-reservations__cover-btn"
              aria-label="Увеличить обложку"
              @click="openCoverPreview(r.book_cover_url!, r.book_title)"
            >
              <img
                :src="r.book_cover_url"
                :alt="r.book_title"
                class="admin-reservations__cover"
              >
            </button>
            <div v-else class="admin-reservations__cover admin-reservations__cover--placeholder">
              <span aria-hidden="true">Обложка</span>
            </div>
          </div>
          <span class="admin-reservations__author">{{ r.book_author }}</span>
          <button
            type="button"
            class="admin-reservations__book-link"
            @click="goToBook(r.book_id)"
          >
            {{ r.book_title }}
          </button>
        </div>
        <div class="admin-reservations__right">
          <span :class="['admin-reservations__status', `admin-reservations__status--${r.status}`]">
            {{ statusLabel(r.status) }}
          </span>
          <p class="admin-reservations__user-line">{{ r.user_name || r.user_phone }}</p>
          <p class="admin-reservations__contact">{{ r.user_phone }}</p>
          <p class="admin-reservations__address">{{ r.delivery_address }}</p>
          <p class="admin-reservations__delivery-date">
            <template v-if="r.status === 'issued'">
              Вернуть до: {{ formatDate(r.due_return_date) }}
            </template>
            <template v-else>
              Доставка: {{ formatDate(r.delivery_date) }}
            </template>
            <span v-if="r.is_overdue" class="admin-reservations__overdue">Просрочено</span>
          </p>
        </div>
        <div class="admin-reservations__actions">
          <button
            v-if="r.status === 'created'"
            type="button"
            class="admin-reservations__btn admin-reservations__btn--primary"
            :disabled="actionId !== null"
            @click="confirmIssue(r)"
          >
            {{ actionId === r.id ? '…' : 'Выдать' }}
          </button>
          <button
            v-if="r.status === 'issued'"
            type="button"
            class="admin-reservations__btn admin-reservations__btn--secondary"
            :disabled="actionId !== null"
            @click="confirmReturn(r)"
          >
            {{ actionId === r.id ? '…' : 'Вернули' }}
          </button>
        </div>
      </li>
    </ul>
    <Teleport to="body">
      <div
        v-if="coverPreview"
        ref="previewOverlayRef"
        tabindex="-1"
        class="admin-reservations__preview-overlay"
        role="dialog"
        aria-modal="true"
        aria-label="Предпросмотр обложки"
        @click.self="closeCoverPreview"
        @keydown.escape="closeCoverPreview"
      >
        <button
          type="button"
          class="admin-reservations__preview-close"
          aria-label="Закрыть"
          @click="closeCoverPreview"
        >
          ×
        </button>
        <img
          :src="coverPreview.url"
          :alt="coverPreview.alt"
          class="admin-reservations__preview-img"
          @click.stop
        >
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.admin-reservations__title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-heading);
  color: var(--color-text);
  margin: 0 0 var(--spacing-lg);
}

.admin-reservations__filter {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-sm) var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.admin-reservations__filter-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
}

.admin-reservations__filter-check {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
  user-select: none;
}

.admin-reservations__filter-input {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

.admin-reservations__filter-input:focus + .admin-reservations__filter-badge {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.admin-reservations__filter-badge {
  display: inline-block;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  border: 1px dashed var(--color-border);
  background: transparent;
  color: var(--color-text-light);
  opacity: 0.65;
  transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease, opacity 0.15s ease;
}

.admin-reservations__filter-badge--active {
  border-style: solid;
  opacity: 1;
}

.admin-reservations__filter-badge--active.admin-reservations__status--created {
  background: rgba(70, 130, 235, 0.2);
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.admin-reservations__filter-badge--active.admin-reservations__status--issued {
  background: var(--color-success-bg);
  color: var(--color-success);
  border-color: var(--color-success);
}

.admin-reservations__filter-badge--active.admin-reservations__status--returned {
  background: var(--color-background-subtle);
  color: var(--color-text-muted);
  border-color: var(--color-border-dark);
}

.admin-reservations__filter-badge--active.admin-reservations__status--cancelled {
  background: var(--color-error-bg);
  color: var(--color-error);
  border-color: var(--color-error);
}

.admin-reservations__loading,
.admin-reservations__empty {
  color: var(--color-text-muted);
  margin: 0;
  font-size: var(--font-size-sm);
}

.admin-reservations__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.admin-reservations__item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-xl);
  padding: var(--spacing-xl);
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  flex-wrap: wrap;
}

@media screen and (max-width: 767px) {
  .admin-reservations__item {
    flex-direction: column;
    flex-wrap: nowrap;
    align-items: stretch;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
  }

  /* Верхняя строка: обложка слева, автор и название справа */
  .admin-reservations__book-block {
    width: 100%;
    max-width: 100%;
    flex-direction: row;
    align-items: flex-start;
    gap: var(--spacing-sm);
    flex-shrink: 0;
    min-width: 0;
  }

  .admin-reservations__cover-wrap {
    flex-shrink: 0;
  }

  .admin-reservations__author {
    flex: 1 1 auto;
    min-width: 0;
    max-width: none;
  }

  .admin-reservations__book-link {
    flex: 1 1 auto;
    min-width: 0;
    max-width: none;
  }

  /* Ниже: блок с пользователем и датой */
  .admin-reservations__right {
    flex: none;
    width: 100%;
    min-width: 0;
  }

  /* Ниже: кнопка */
  .admin-reservations__actions {
    width: 100%;
    flex: none;
  }

  .admin-reservations__btn {
    width: 100%;
  }
}

.admin-reservations__item--overdue {
  border-left: 4px solid var(--color-brand-gold);
  background: var(--color-brand-gold-bg);
}

.admin-reservations__book-block {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--spacing-xs);
  min-width: 0;
}

.admin-reservations__cover-wrap {
  line-height: 0;
}

.admin-reservations__cover-btn {
  display: block;
  padding: 0;
  margin: 0;
  border: none;
  background: none;
  cursor: pointer;
  line-height: 0;
  border-radius: var(--radius-sm);
}

.admin-reservations__cover-btn:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.admin-reservations__cover {
  display: block;
  width: 56px;
  height: 84px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  background: var(--color-background-alt);
}

.admin-reservations__book-link {
  display: block;
  width: 100%;
  text-align: left;
  padding: 0;
  margin: 0;
  border: none;
  background: none;
  font: inherit;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
  cursor: pointer;
  text-decoration: none;
  max-width: 140px;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-clamp: 2;
}

.admin-reservations__book-link:hover {
  text-decoration: underline;
}

.admin-reservations__book-link:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.admin-reservations__cover--placeholder {
  width: 56px;
  height: 84px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xs);
  color: var(--color-text-light);
  border: 1px solid var(--color-border);
}

.admin-reservations__author {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  display: block;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admin-reservations__book {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-snug);
  color: var(--color-text);
  max-width: 140px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-clamp: 2;
}

.admin-reservations__right {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.admin-reservations__user-line,
.admin-reservations__contact,
.admin-reservations__address,
.admin-reservations__delivery-date {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin: 0;
  line-height: var(--line-height-relaxed);
}

.admin-reservations__user-line {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
}

.admin-reservations__overdue {
  margin-left: var(--spacing-sm);
  color: var(--color-brand-gold);
  font-weight: var(--font-weight-semibold);
}

.admin-reservations__status {
  align-self: flex-start;
  flex-shrink: 0;
  display: inline-block;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  line-height: 1.2;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}

.admin-reservations__status--created {
  background: rgba(70, 130, 235, 0.12);
  color: var(--color-primary);
}

.admin-reservations__status--issued {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.admin-reservations__status--returned {
  background: var(--color-background-subtle);
  color: var(--color-text-muted);
}

.admin-reservations__status--cancelled {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.admin-reservations__actions {
  flex-shrink: 0;
}

.admin-reservations__btn {
  padding: 10px var(--spacing-xl);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  min-height: 44px;
  transition: background-color 0.15s ease;
}

.admin-reservations__btn--primary {
  background: var(--color-primary);
  color: var(--color-background);
}

.admin-reservations__btn--primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.admin-reservations__btn--primary:active:not(:disabled) {
  background: var(--color-primary-active);
}

.admin-reservations__btn--secondary {
  background: var(--color-background-alt);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.admin-reservations__btn--secondary:hover:not(:disabled) {
  background: var(--color-background-subtle);
  border-color: var(--color-border-dark);
}

.admin-reservations__btn:disabled {
  background: var(--color-background-subtle);
  color: var(--color-text-light);
  cursor: not-allowed;
}

.admin-reservations__btn:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

/* Предпросмотр обложки (Teleport в body — глобальные стили без scoped для overlay) */
.admin-reservations__preview-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  background: rgba(21, 20, 17, 0.85);
  cursor: zoom-out;
}

.admin-reservations__preview-overlay:focus {
  outline: none;
}

.admin-reservations__preview-close {
  position: absolute;
  top: var(--spacing-lg);
  right: var(--spacing-lg);
  width: 44px;
  height: 44px;
  padding: 0;
  border: none;
  border-radius: var(--radius-circle);
  background: var(--color-background);
  color: var(--color-text);
  font-size: var(--font-size-2xl);
  line-height: 1;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.admin-reservations__preview-close:hover {
  background: var(--color-background-alt);
}

.admin-reservations__preview-close:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.admin-reservations__preview-img {
  max-width: 90vw;
  max-height: 85vh;
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-lg);
  cursor: default;
}
</style>
