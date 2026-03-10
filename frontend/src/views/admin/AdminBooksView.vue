<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchBooks } from '@/api/catalog'
import type { BookListEntry } from '@/types/catalog'

const SEARCH_DEBOUNCE_MS = 350

const router = useRouter()
const books = ref<BookListEntry[]>([])
const total = ref(0)
const page = ref(1)
const pages = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const searchQuery = ref('')
const sentinelRef = ref<HTMLElement | null>(null)
let searchDebounceId: ReturnType<typeof setTimeout> | null = null
let observer: IntersectionObserver | null = null

async function loadBooks(append = false): Promise<void> {
  if (append) {
    loadingMore.value = true
  } else {
    loading.value = true
  }
  try {
    const res = await fetchBooks({
      page: page.value,
      size: 20,
      search: searchQuery.value || undefined,
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

function goToBook(id: number): void {
  router.push({ name: 'admin-book-edit', params: { id } })
}

function goToNew(): void {
  router.push({ name: 'admin-book-new' })
}

onMounted(() => {
  loadBooks(false)
  observer = new IntersectionObserver(
    (entries) => {
      const entry = entries[0]
      if (!entry?.isIntersecting) return
      loadMore()
    },
    { rootMargin: '200px', threshold: 0 }
  )
})

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
  <div class="admin-books">
    <div class="admin-books__header">
      <h2 class="admin-books__title">
        Управление книгами
      </h2>
      <button
        type="button"
        class="admin-books__add-btn"
        aria-label="Добавить новую книгу"
        @click="goToNew"
      >
        Добавить книгу
      </button>
    </div>
    <div class="admin-books__search-wrap">
      <input
        v-model="searchQuery"
        type="search"
        class="admin-books__search"
        placeholder="Поиск по названию или автору"
        aria-label="Поиск книг по названию или автору"
        autocomplete="off"
        @input="scheduleSearch"
      >
    </div>
    <p v-if="loading" class="admin-books__loading">
      Загрузка…
    </p>
    <template v-else>
      <ul
        v-if="books.length"
        class="admin-books__grid"
      >
        <li
          v-for="b in books"
          :key="b.id"
          class="admin-books__card"
        >
          <button
            type="button"
            class="admin-books__card-link"
            :aria-label="`Редактировать: ${b.title}`"
            @click="goToBook(b.id)"
          >
            <span class="admin-books__cover-wrap">
              <img
                v-if="b.cover_url"
                :src="b.cover_url"
                :alt="b.title"
                class="admin-books__cover"
                loading="lazy"
              >
              <span v-else class="admin-books__cover admin-books__cover--placeholder">
                Нет обложки
              </span>
            </span>
            <div class="admin-books__card-body">
              <span class="admin-books__card-author">{{ b.author }}</span>
              <span class="admin-books__card-title">{{ b.title }}</span>
              <span class="admin-books__card-meta">
                {{ b.total_count }} экз., доступно {{ b.available_count }}
              </span>
            </div>
          </button>
        </li>
      </ul>
      <div
        v-if="books.length && page < pages"
        ref="sentinelRef"
        class="admin-books__sentinel"
        aria-hidden="true"
      />
      <p
        v-if="loadingMore"
        class="admin-books__loading admin-books__loading--more"
      >
        Загрузка…
      </p>
      <p
        v-else-if="!books.length"
        class="admin-books__empty"
      >
        Книги не найдены.
      </p>
    </template>
  </div>
</template>

<style scoped>
.admin-books__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  flex-wrap: wrap;
  gap: var(--spacing-lg);
}

.admin-books__title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-heading);
  color: var(--color-text);
  margin: 0;
}

.admin-books__add-btn {
  padding: 10px var(--spacing-xl);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  background: var(--color-primary);
  color: var(--color-background);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  min-height: 44px;
  transition: background-color 0.15s ease;
}

.admin-books__add-btn:hover {
  background: var(--color-primary-hover);
}

.admin-books__add-btn:active {
  background: var(--color-primary-active);
}

.admin-books__add-btn:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.admin-books__search-wrap {
  max-width: 100%;
  margin-bottom: var(--spacing-2xl);
}

.admin-books__search {
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

.admin-books__search::placeholder {
  color: var(--color-text-light);
}

.admin-books__search:hover {
  box-shadow: 0 0 0 1px rgba(21, 20, 17, 0.08), 0 1px 2px rgba(21, 20, 17, 0.04);
}

.admin-books__search:focus {
  outline: none;
  box-shadow: 0 0 0 2px var(--color-primary);
}

.admin-books__loading,
.admin-books__empty {
  color: var(--color-text-muted);
  margin: 0;
  font-size: var(--font-size-sm);
}

.admin-books__grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.admin-books__sentinel {
  height: 1px;
  width: 100%;
  pointer-events: none;
  visibility: hidden;
}

@media (min-width: 768px) {
  .admin-books__grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  }
}

@media (min-width: 1024px) {
  .admin-books__grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}

.admin-books__card {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.admin-books__card-link {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  text-align: left;
  padding: 0;
  margin: 0;
  border: none;
  background: none;
  font: inherit;
  color: inherit;
  cursor: pointer;
  border-radius: var(--radius-lg);
  background: var(--color-background);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  transition: box-shadow 0.2s ease, background-color 0.2s ease;
}

.admin-books__card-link:hover {
  box-shadow: var(--shadow-lg);
  background: var(--color-background-alt);
}

.admin-books__card-link:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.admin-books__cover-wrap {
  display: block;
  width: 100%;
  aspect-ratio: 2 / 3;
  overflow: hidden;
  background: var(--color-background-alt);
}

.admin-books__cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.admin-books__cover--placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-background-subtle);
  font-size: var(--font-size-xs);
  color: var(--color-text-light);
  text-align: center;
  padding: var(--spacing-sm);
  line-height: var(--line-height-snug);
}

.admin-books__card-body {
  flex: 1;
  min-width: 0;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.admin-books__card-author {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-normal);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.admin-books__card-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: var(--line-height-snug);
}

.admin-books__card-meta {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.admin-books__loading--more {
  margin-top: var(--spacing-lg);
}
</style>
