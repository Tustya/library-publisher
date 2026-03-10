<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { fetchBooks, fetchGenres } from '@/api/catalog'
import BookCard from '@/components/BookCard.vue'
import type { RefItem } from '@/types/admin'
import type { BookListEntry } from '@/types/catalog'

const SEARCH_DEBOUNCE_MS = 350

const route = useRoute()
const books = ref<BookListEntry[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const pages = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const searchQuery = ref('')
const genreFilter = ref('')
const ageFilter = ref('')
const languageFilter = ref('')
const genres = ref<RefItem[]>([])
const sentinelRef = ref<HTMLElement | null>(null)
let searchDebounceId: ReturnType<typeof setTimeout> | null = null
let observer: IntersectionObserver | null = null

const ageOptions = [
  { value: '', label: 'Возраст' },
  { value: '0+', label: '0+' },
  { value: '6+', label: '6+' },
  { value: '12+', label: '12+' },
  { value: '16+', label: '16+' },
]

const languageOptions = [
  { value: '', label: 'Язык' },
  { value: 'русский', label: '🇷🇺 Русский' },
  { value: 'английский', label: '🇬🇧 Английский' },
]

async function loadBooks(append = false): Promise<void> {
  if (append) {
    loadingMore.value = true
  } else {
    loading.value = true
  }
  try {
    const res = await fetchBooks({
      page: page.value,
      size: size.value,
      search: searchQuery.value || undefined,
      genre: genreFilter.value || undefined,
      age_rating: ageFilter.value || undefined,
      language: languageFilter.value || undefined,
    })
    if (append && page.value > 1) {
      books.value = [...books.value, ...res.items]
    } else {
      books.value = res.items
    }
    total.value = res.total
    pages.value = res.pages
  } catch {
    if (!append) {
      books.value = []
    }
    total.value = append ? total.value : 0
    pages.value = append ? pages.value : 0
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore(): void {
  if (loading.value || loadingMore.value || page.value >= pages.value) return
  page.value += 1
  loadBooks(true)
}

function scheduleSearch(): void {
  if (searchDebounceId != null) clearTimeout(searchDebounceId)
  searchDebounceId = setTimeout(() => {
    searchDebounceId = null
    page.value = 1
    loadBooks(false)
  }, SEARCH_DEBOUNCE_MS)
}

function applyGenre(genreName: string): void {
  genreFilter.value = genreFilter.value === genreName ? '' : genreName
  page.value = 1
  loadBooks(false)
}

onMounted(async () => {
  try {
    genres.value = await fetchGenres()
  } catch {
    genres.value = []
  }
  observer = new IntersectionObserver(
    (entries) => {
      const entry = entries[0]
      if (!entry?.isIntersecting) return
      loadMore()
    },
    { rootMargin: '200px', threshold: 0 }
  )
})

watch(
  () => route.query,
  (q) => {
    if (q.search != null) searchQuery.value = String(q.search)
    if (q.genre != null) genreFilter.value = String(q.genre)
    if (q.age != null) ageFilter.value = String(q.age)
    if (q.lang != null) languageFilter.value = String(q.lang)
    page.value = 1
    loadBooks(false)
  },
  { immediate: true }
)

watch(sentinelRef, (el) => {
  if (observer == null) return
  observer.disconnect()
  if (el) observer.observe(el)
})

onUnmounted(() => {
  observer?.disconnect()
})
</script>

<template>
  <div class="catalog">
    <header class="catalog__header">
      <h1 class="catalog__title">
        Каталог книг
      </h1>
    </header>

    <div class="catalog__filters">
      <div class="catalog__search-wrap">
        <input
          v-model="searchQuery"
          type="search"
          class="catalog__search"
          placeholder="Поиск по названию или автору"
          aria-label="Поиск по названию или автору"
          autocomplete="off"
          @input="scheduleSearch"
        >
      </div>

      <div
        v-if="genres.length > 0"
        class="catalog__genres"
        role="group"
        aria-label="Фильтр по жанру"
      >
        <button
          v-for="genre in genres"
          :key="genre.id"
          type="button"
          class="catalog__tag"
          :class="{ 'catalog__tag--active': genreFilter === genre.name }"
          :aria-pressed="genreFilter === genre.name"
          @click="applyGenre(genre.name)"
        >
          {{ genre.name }}
        </button>
      </div>

      <div class="catalog__meta">
        <div class="catalog__select-wrap">
          <select
            v-model="ageFilter"
            class="catalog__select"
            :class="{ 'catalog__select--filled': ageFilter }"
            aria-label="Возраст"
            @change="page = 1; loadBooks(false)"
          >
            <option
              v-for="opt in ageOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </option>
          </select>
        </div>
        <div class="catalog__select-wrap">
          <select
            v-model="languageFilter"
            class="catalog__select"
            :class="{ 'catalog__select--filled': languageFilter }"
            aria-label="Язык"
            @change="page = 1; loadBooks(false)"
          >
            <option
              v-for="opt in languageOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <p
      v-if="loading"
      class="catalog__status"
    >
      Загрузка…
    </p>
    <template v-else>
      <div
        v-if="books.length"
        class="catalog__grid"
      >
        <BookCard
          v-for="book in books"
          :key="book.id"
          :book="book"
        />
      </div>
      <div
        v-if="books.length && page < pages"
        ref="sentinelRef"
        class="catalog__sentinel"
        aria-hidden="true"
      />
      <p
        v-if="loadingMore"
        class="catalog__status catalog__status--loading"
      >
        Загрузка…
      </p>
      <p
        v-else-if="!books.length"
        class="catalog__empty"
      >
        Книг не найдено. Измените параметры поиска или импортируйте каталог.
      </p>
    </template>
  </div>
</template>

<style scoped>
.catalog {
  width: 100%;
}

.catalog__header {
  margin-bottom: var(--spacing-xl);
}

.catalog__title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-snug);
  color: var(--color-text);
  margin: 0;
}

.catalog__filters {
  margin-bottom: var(--spacing-2xl);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

/* Поиск: одно поле, без кнопки, в стиле design-system */
.catalog__search-wrap {
  max-width: 100%;
}

.catalog__search {
  width: 100%;
  min-height: 44px;
  padding: var(--spacing-md) var(--spacing-lg);
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-normal);
  line-height: var(--line-height-normal);
  color: var(--color-text);
  background: var(--color-background-input);
  border: none;
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-input);
  transition: box-shadow 0.15s ease;
}

.catalog__search::placeholder {
  color: var(--color-text-light);
}

.catalog__search:hover {
  box-shadow: 0 0 0 1px rgba(21, 20, 17, 0.08), 0 1px 2px rgba(21, 20, 17, 0.04);
}

.catalog__search:focus {
  outline: none;
  box-shadow: 0 0 0 2px var(--color-primary);
}

/* Теги жанров: компактные чипы с малым радиусом (4px), чтобы в ряд влезало больше */
.catalog__genres {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.catalog__tag {
  min-height: 32px;
  padding: var(--spacing-xs) var(--spacing-md);
  font-family: var(--font-family);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  line-height: 1.35;
  color: var(--color-text-secondary);
  background: var(--color-background-alt);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: color 0.15s ease, background 0.15s ease, border-color 0.15s ease;
}

.catalog__tag:hover {
  color: var(--color-text);
  background: var(--color-background-subtle);
  border-color: var(--color-border-dark);
}

.catalog__tag--active {
  color: var(--color-background);
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.catalog__tag--active:hover {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

/* Возраст и язык — выпадающие списки */
.catalog__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-lg);
}

.catalog__select-wrap {
  position: relative;
}

.catalog__select {
  min-width: 6.5rem;
  min-height: 36px;
  padding: var(--spacing-xs) var(--spacing-lg) var(--spacing-xs) var(--spacing-md);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-normal);
  line-height: var(--line-height-normal);
  color: var(--color-text-muted);
  background: var(--color-background-input);
  border: none;
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-input);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 12 12'%3E%3Cpath fill='%23999999' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right var(--spacing-md) center;
  padding-right: 1.75rem;
  transition: box-shadow 0.15s ease, color 0.15s ease;
}

.catalog__select--filled {
  color: var(--color-text);
}

.catalog__select:hover {
  box-shadow: 0 0 0 1px rgba(21, 20, 17, 0.08), 0 1px 2px rgba(21, 20, 17, 0.04);
}

.catalog__select:focus {
  outline: none;
  box-shadow: 0 0 0 2px var(--color-primary);
}

.catalog__status {
  margin: 0 0 var(--spacing-lg);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.catalog__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-2xl);
}

@media (min-width: 768px) {
  .catalog__grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  }
}

@media (min-width: 1024px) {
  .catalog__grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}

.catalog__empty {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--color-text-muted);
}

.catalog__sentinel {
  height: 1px;
  width: 100%;
  pointer-events: none;
  visibility: hidden;
}

.catalog__status--loading {
  margin-top: var(--spacing-lg);
}
</style>
