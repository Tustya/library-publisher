<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { fetchBook } from '@/api/catalog'
import { joinQueue, leaveQueue } from '@/api/queue'
import { createReservation } from '@/api/reservations'
import type { BookDetail } from '@/types/catalog'

type TabId = 'about' | 'impressions' | 'quotes' | 'readers'

const route = useRoute()
const router = useRouter()
const { isAuthenticated } = useAuth()
const book = ref<BookDetail | null>(null)
const loading = ref(true)
const error = ref('')
const reserveLoading = ref(false)
const reserveError = ref('')
const reserveSuccess = ref('')
const queueLoading = ref(false)
const queueError = ref('')
const queueSuccess = ref('')
const activeTab = ref<TabId>('about')

const id = computed(() => Number(route.params.id))
const canReserve = computed(
  () => (book.value?.available_count ?? 0) > 0 && !reserveLoading.value
)
const isUnavailable = computed(() => (book.value?.available_count ?? 0) === 0)
const showQueueBlock = computed(
  () => isUnavailable.value && !(book.value?.current_user_has_book ?? false)
)
const inQueue = computed(
  () => (book.value?.queue_position ?? null) != null
)
const queueTotal = computed(() => book.value?.queue_total ?? 0)
const queuePosition = computed(() => book.value?.queue_position ?? null)

const tabs: { id: TabId; label: string }[] = [
  { id: 'about', label: 'О книге' },
  { id: 'impressions', label: 'Впечатления' },
  { id: 'quotes', label: 'Цитаты' },
  { id: 'readers', label: 'Читали' },
]

const hasMeta = computed(
  () =>
    (book.value?.tags?.length ?? 0) > 0 ||
    !!book.value?.genre ||
    !!book.value?.language ||
    !!book.value?.age_rating
)

function formatReturnDate(isoDate: string | null | undefined): string {
  if (!isoDate) return '—'
  const d = new Date(isoDate + 'T12:00:00')
  if (Number.isNaN(d.getTime())) return '—'
  const day = d.getDate()
  const month = d.getMonth() + 1
  const year = d.getFullYear()
  return `${day.toString().padStart(2, '0')}.${month.toString().padStart(2, '0')}.${year}`
}

function isReturnDateOverdue(isoDate: string | null | undefined): boolean {
  if (!isoDate) return false
  const d = new Date(isoDate + 'T12:00:00')
  if (Number.isNaN(d.getTime())) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  d.setHours(0, 0, 0, 0)
  return d.getTime() < today.getTime()
}

async function loadBook(): Promise<void> {
  if (!id.value || Number.isNaN(id.value)) {
    error.value = 'Неверный идентификатор книги'
    loading.value = false
    return
  }
  try {
    book.value = await fetchBook(id.value)
  } catch {
    error.value = 'Книга не найдена'
    book.value = null
  } finally {
    loading.value = false
  }
}

async function reserve(): Promise<void> {
  if (!book.value || !canReserve.value) return
  if (!isAuthenticated.value) {
    await router.push({
      name: 'login',
      query: { redirect: route.fullPath },
    })
    return
  }
  reserveError.value = ''
  reserveSuccess.value = ''
  reserveLoading.value = true
  try {
    const result = await createReservation(book.value.id)
    reserveSuccess.value = `${result.message} Дата доставки: ${result.delivery_date}, возврат до: ${result.due_return_date}.`
    await loadBook()
  } catch (err: unknown) {
    const msg =
      err &&
      typeof err === 'object' &&
      'response' in err &&
      err.response &&
      typeof err.response === 'object' &&
      'data' in err.response &&
      err.response.data &&
      typeof err.response.data === 'object' &&
      'detail' in err.response.data
        ? String((err.response.data as { detail: unknown }).detail)
        : 'Не удалось оформить заказ.'
    reserveError.value = msg
  } finally {
    reserveLoading.value = false
  }
}

async function joinQueueAction(): Promise<void> {
  if (!book.value) return
  if (!isAuthenticated.value) {
    await router.push({
      name: 'login',
      query: { redirect: route.fullPath },
    })
    return
  }
  queueError.value = ''
  queueSuccess.value = ''
  queueLoading.value = true
  try {
    const result = await joinQueue(book.value.id)
    queueSuccess.value = result.message
    await loadBook()
  } catch (err: unknown) {
    const msg =
      err &&
      typeof err === 'object' &&
      'response' in err &&
      err.response &&
      typeof err.response === 'object' &&
      'data' in err.response &&
      err.response.data &&
      typeof err.response.data === 'object' &&
      'detail' in err.response.data
        ? String((err.response.data as { detail: unknown }).detail)
        : 'Не удалось встать в очередь.'
    queueError.value = msg
  } finally {
    queueLoading.value = false
  }
}

async function leaveQueueAction(): Promise<void> {
  if (!book.value || !inQueue.value) return
  queueError.value = ''
  queueSuccess.value = ''
  queueLoading.value = true
  try {
    const result = await leaveQueue(book.value.id)
    queueSuccess.value = result.message
    await loadBook()
  } catch (err: unknown) {
    const msg =
      err &&
      typeof err === 'object' &&
      'response' in err &&
      err.response &&
      typeof err.response === 'object' &&
      'data' in err.response &&
      err.response.data &&
      typeof err.response.data === 'object' &&
      'detail' in err.response.data
        ? String((err.response.data as { detail: unknown }).detail)
        : 'Не удалось выйти из очереди.'
    queueError.value = msg
  } finally {
    queueLoading.value = false
  }
}

onMounted(loadBook)
</script>

<template>
  <div class="book-page">
    <template v-if="loading">
      <p class="book-page__loading">
        Загрузка…
      </p>
    </template>
    <template v-else-if="error">
      <p class="book-page__error">
        {{ error }}
      </p>
      <router-link
        to="/catalog"
        class="book-page__back"
      >
        К списку книг
      </router-link>
    </template>
    <template v-else-if="book">
      <router-link
        to="/catalog"
        class="book-page__back"
        aria-label="Вернуться к списку книг"
      >
        К списку книг
      </router-link>
      <div class="book-page__layout">
        <div class="book-page__cover-wrap">
          <img
            v-if="book.cover_url"
            :src="book.cover_url"
            :alt="`Обложка: ${book.title}`"
            class="book-page__cover"
          >
          <div
            v-else
            class="book-page__cover book-page__cover--placeholder"
          >
            Нет обложки
          </div>
        </div>
        <div class="book-page__main">
          <p
            v-if="isUnavailable"
            class="book-page__status book-page__status--unavailable"
          >
            {{ isReturnDateOverdue(book.earliest_return_date) ? 'На руках. Вернется скоро, кто-то зачитался' : `На руках. Вернётся ${formatReturnDate(book.earliest_return_date)}` }}
          </p>
          <h1 class="book-page__title">
            {{ book.title }}
          </h1>
          <p class="book-page__author">
            {{ book.author }}
          </p>
          <div class="book-page__actions">
            <template v-if="canReserve">
              <button
                type="button"
                class="book-page__btn book-page__btn--primary"
                aria-label="Забронировать книгу"
                @click="reserve"
              >
                {{ reserveLoading ? 'Оформление…' : 'Забронировать' }}
              </button>
            </template>
            <template v-else-if="showQueueBlock">
              <p
                v-if="queueTotal > 0 && !inQueue"
                class="book-page__queue-info"
              >
                В очереди: {{ queueTotal }} человек
              </p>
              <p
                v-if="inQueue"
                class="book-page__queue-info"
              >
                Вы в очереди: место {{ queuePosition }} из {{ queueTotal }}
              </p>
              <button
                v-if="inQueue"
                type="button"
                class="book-page__btn book-page__btn--secondary"
                :disabled="queueLoading"
                aria-label="Выйти из очереди"
                @click="leaveQueueAction"
              >
                {{ queueLoading ? '…' : 'Выйти из очереди' }}
              </button>
              <button
                v-else
                type="button"
                class="book-page__btn book-page__btn--primary"
                :disabled="queueLoading"
                aria-label="Встать в очередь на книгу"
                @click="joinQueueAction"
              >
                {{ queueLoading ? '…' : 'Встать в очередь' }}
              </button>
            </template>
          </div>
          <p
            v-if="reserveSuccess"
            class="book-page__success"
            role="status"
          >
            {{ reserveSuccess }}
          </p>
          <p
            v-if="queueSuccess"
            class="book-page__success"
            role="status"
          >
            {{ queueSuccess }}
          </p>
          <p
            v-if="reserveError"
            class="book-page__reserve-error"
            role="alert"
          >
            {{ reserveError }}
          </p>
          <p
            v-if="queueError"
            class="book-page__reserve-error"
            role="alert"
          >
            {{ queueError }}
          </p>

          <nav
            class="book-page__tabs"
            role="tablist"
            aria-label="Разделы страницы книги"
          >
            <button
              v-for="tab in tabs"
              :key="tab.id"
              type="button"
              role="tab"
              :aria-selected="activeTab === tab.id"
              :aria-controls="`panel-${tab.id}`"
              :id="`tab-${tab.id}`"
              class="book-page__tab"
              :class="{ 'book-page__tab--active': activeTab === tab.id }"
              @click="activeTab = tab.id"
            >
              {{ tab.label }}
            </button>
          </nav>
          <div
            v-for="tab in tabs"
            :key="tab.id"
            :id="`panel-${tab.id}`"
            role="tabpanel"
            :aria-labelledby="`tab-${tab.id}`"
            :hidden="activeTab !== tab.id"
            class="book-page__panel"
          >
            <template v-if="tab.id === 'about'">
              <p
                v-if="book.description"
                class="book-page__description"
              >
                {{ book.description }}
              </p>
              <p
                v-else
                class="book-page__description book-page__description--empty"
              >
                Описание пока не добавлено.
              </p>
            </template>
            <template v-else>
              <p class="book-page__placeholder">
                Раздел «{{ tab.label }}» скоро появится.
              </p>
            </template>
          </div>

          <footer class="book-page__meta">
            <dl v-if="hasMeta" class="book-page__meta-list">
              <template v-if="book.tags?.length">
                <dt class="book-page__meta-term">Теги</dt>
                <dd class="book-page__meta-value">
                  {{ book.tags.join(', ') }}
                </dd>
              </template>
              <template v-if="book.genre">
                <dt class="book-page__meta-term">Жанр</dt>
                <dd class="book-page__meta-value">
                  {{ book.genre }}
                </dd>
              </template>
              <dt class="book-page__meta-term">Язык</dt>
              <dd class="book-page__meta-value">
                {{ book.language }}
              </dd>
              <dt class="book-page__meta-term">Возраст</dt>
              <dd class="book-page__meta-value">
                {{ book.age_rating }}
              </dd>
            </dl>
          </footer>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.book-page {
  width: 100%;
  padding: 0 var(--spacing-lg);
}

.book-page__loading,
.book-page__error {
  margin: 0 0 var(--spacing-lg);
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
}

.book-page__error {
  color: var(--color-error);
}

.book-page__success {
  font-size: var(--font-size-sm);
  color: var(--color-success);
  margin: 0 0 var(--spacing-md);
  line-height: var(--line-height-body);
}

.book-page__reserve-error {
  font-size: var(--font-size-sm);
  color: var(--color-error);
  margin: 0 0 var(--spacing-md);
  line-height: var(--line-height-body);
}

.book-page__back {
  display: inline-block;
  margin-bottom: var(--spacing-xl);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-primary);
  text-decoration: none;
  line-height: var(--line-height-normal);
}

.book-page__back:hover {
  text-decoration: underline;
  color: var(--color-primary-hover);
}

.book-page__back:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.book-page__layout {
  display: grid;
  gap: var(--spacing-2xl);
  grid-template-columns: 1fr;
}

@media (max-width: 767px) {
  .book-page__cover-wrap {
    justify-self: center;
  }
}

@media (min-width: 768px) {
  .book-page__layout {
    grid-template-columns: auto 1fr;
    gap: var(--spacing-3xl);
    align-items: start;
  }
}

@media (min-width: 1024px) {
  .book-page__cover-wrap {
    width: 256px;
    height: 363px;
    flex-shrink: 0;
  }
}

.book-page__cover-wrap {
  aspect-ratio: 2 / 3;
  max-width: 200px;
  background: var(--color-background-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

@media (min-width: 768px) {
  .book-page__cover-wrap {
    max-width: 220px;
  }
}

.book-page__cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.book-page__cover--placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm);
  color: var(--color-text-light);
}

.book-page__main {
  min-width: 0;
}

.book-page__status {
  margin: 0 0 var(--spacing-sm);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-normal);
}

.book-page__status--unavailable {
  color: var(--color-text-muted);
}

.book-page__title {
  margin: 0 0 var(--spacing-sm);
  font-size: 2rem; /* 32px по ТЗ */
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-snug);
  color: var(--color-text);
}

@media (min-width: 768px) {
  .book-page__title {
    margin-top: var(--spacing-md); /* отступ над названием */
  }
}

.book-page__author {
  margin: 0 0 var(--spacing-xl);
  font-size: var(--font-size-sm); /* 14px по ТЗ */
  color: var(--color-text-secondary);
  line-height: var(--line-height-normal);
}

.book-page__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.book-page__queue-info {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-normal);
  width: 100%;
}

.book-page__btn {
  padding: 12px 24px;
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-md);
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  cursor: pointer;
  border: none;
  transition: background-color 0.15s ease;
}

.book-page__btn:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.book-page__btn--primary {
  background: var(--color-primary);
  color: var(--color-background);
}

.book-page__btn--primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.book-page__btn--primary:active:not(:disabled) {
  background: var(--color-primary-active);
}

.book-page__btn--primary:disabled {
  background: var(--color-background-subtle);
  color: var(--color-text-muted);
  cursor: not-allowed;
}

.book-page__btn--secondary {
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}

.book-page__btn--secondary:hover:not(:disabled) {
  background: var(--color-background-subtle);
  color: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

.book-page__btn--secondary:disabled {
  border-color: var(--color-border);
  color: var(--color-text-muted);
  cursor: not-allowed;
}

/* Табы */
.book-page__tabs {
  display: flex;
  gap: 0;
  margin: var(--spacing-2xl) 0 0;
  padding: 0;
  list-style: none;
  border-bottom: 1px solid var(--color-border);
}

.book-page__tab {
  padding: var(--spacing-md) var(--spacing-lg);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  cursor: pointer;
  transition: color 0.15s ease, border-color 0.15s ease;
}

.book-page__tab:hover {
  color: var(--color-text);
}

.book-page__tab--active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.book-page__tab:focus-visible {
  outline: var(--focus-outline);
  outline-offset: 2px;
}

.book-page__panel {
  margin-top: 0;
  padding: var(--spacing-xl) 0;
}

.book-page__panel[hidden] {
  display: none;
}

.book-page__description {
  margin: 0 0 var(--spacing-xl);
  font-size: var(--font-size-base);
  line-height: var(--line-height-relaxed);
  color: var(--color-text);
  white-space: pre-wrap;
}

.book-page__description--empty {
  color: var(--color-text-muted);
}

.book-page__placeholder {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

/* Мета внизу */
.book-page__meta {
  margin-top: var(--spacing-3xl);
  padding-top: var(--spacing-xl);
  border-top: 1px solid var(--color-border);
}

.book-page__meta-list {
  margin: 0;
  display: grid;
  gap: var(--spacing-sm) var(--spacing-xl);
  grid-template-columns: auto 1fr;
  font-size: var(--font-size-sm);
}

.book-page__meta-term {
  margin: 0;
  color: var(--color-text-muted);
  font-weight: var(--font-weight-normal);
}

.book-page__meta-value {
  margin: 0;
  color: var(--color-text-secondary);
}
</style>
