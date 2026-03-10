<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChipSelect from '@/components/ChipSelect.vue'
import {
  createTag,
  fetchAdminBook,
  createBook,
  updateBook,
  deleteBook,
  createCopy,
  updateCopy,
  deleteCopy,
} from '@/api/admin'
import {
  fetchAuthors,
  fetchAgeRatings,
  fetchGenres,
  fetchLanguages,
  fetchTags,
} from '@/api/catalog'
import type {
  BookCreate,
  BookCopyCreate,
  BookDetailWithCopies,
  BookUpdate,
  RefItem,
} from '@/types/admin'

const route = useRoute()
const router = useRouter()

const bookId = computed(() => {
  if (route.name === 'admin-book-new') return null
  const id = route.params.id
  return id ? Number(id) : null
})

const isNew = computed(() => route.name === 'admin-book-new')

const book = ref<BookDetailWithCopies | null>(null)
const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')

const form = ref<BookCreate & BookUpdate>({
  author_ids: [],
  title: '',
  description: null,
  cover_url: null,
  genre_id: null,
  age_rating_id: 0,
  language_id: 0,
  tag_ids: null,
})

const authors = ref<RefItem[]>([])
const genres = ref<RefItem[]>([])
const ageRatings = ref<RefItem[]>([])
const languages = ref<RefItem[]>([])
const tags = ref<RefItem[]>([])

const tagIdsModel = computed({
  get(): number[] {
    return form.value.tag_ids ?? []
  },
  set(ids: number[]) {
    form.value.tag_ids = ids.length ? ids : null
  },
})

const coverPreviewError = ref(false)
const coverPreviewAuthor = computed(() => {
  const ids = form.value.author_ids ?? []
  if (!ids.length) return 'Автор не выбран'
  const names = ids
    .map((id) => authors.value.find((a) => a.id === id)?.name)
    .filter(Boolean)
  return names.length ? names.join(', ') : 'Автор не выбран'
})

async function onCreateTag(name: string): Promise<void> {
  try {
    const newTag = await createTag(name)
    tags.value = [...tags.value, newTag]
    form.value.tag_ids = [...(form.value.tag_ids ?? []), newTag.id]
  } catch {
    errorMessage.value = 'Не удалось создать тег'
  }
}

const copyForm = ref<BookCopyCreate>({
  unique_number: '',
  status: 'Доступно',
  cover_url: null,
})
const addingCopy = ref(false)
const editingCopyId = ref<number | null>(null)
const editingCopyStatus = ref('')
const deletingCopyId = ref<number | null>(null)

async function loadBook(): Promise<void> {
  if (!bookId.value) return
  loading.value = true
  try {
    book.value = await fetchAdminBook(bookId.value)
    form.value = {
      author_ids: book.value.author_ids?.length ? [...book.value.author_ids] : [],
      title: book.value.title,
      description: book.value.description,
      cover_url: book.value.cover_url,
      genre_id: book.value.genre_id,
      age_rating_id: book.value.age_rating_id,
      language_id: book.value.language_id,
      tag_ids: book.value.tag_ids?.length ? [...book.value.tag_ids] : null,
    }
  } catch {
    book.value = null
    errorMessage.value = 'Не удалось загрузить книгу'
  } finally {
    loading.value = false
  }
}

async function saveBook(): Promise<void> {
  if (!form.value.author_ids?.length || !form.value.title?.trim()) {
    errorMessage.value = 'Выберите хотя бы одного автора и введите название'
    return
  }
  if (!form.value.age_rating_id || !form.value.language_id) {
    errorMessage.value = 'Выберите возраст и язык'
    return
  }
  saving.value = true
  errorMessage.value = ''
  try {
    if (isNew.value) {
      const created = await createBook({
        author_ids: form.value.author_ids,
        title: form.value.title.trim(),
        description: form.value.description,
        cover_url: form.value.cover_url || null,
        genre_id: form.value.genre_id ?? null,
        age_rating_id: form.value.age_rating_id,
        language_id: form.value.language_id,
        tag_ids: form.value.tag_ids?.length ? form.value.tag_ids : null,
      })
      router.replace({ name: 'admin-book-edit', params: { id: created.id } })
      book.value = created
    } else if (bookId.value) {
      book.value = await updateBook(bookId.value, {
        author_ids: form.value.author_ids,
        title: form.value.title.trim(),
        description: form.value.description,
        cover_url: form.value.cover_url || null,
        genre_id: form.value.genre_id ?? null,
        age_rating_id: form.value.age_rating_id,
        language_id: form.value.language_id,
        tag_ids: form.value.tag_ids,
      })
    }
  } catch (err: unknown) {
    const msg =
      err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : null
    errorMessage.value = typeof msg === 'string' ? msg : 'Не удалось сохранить'
  } finally {
    saving.value = false
  }
}

async function deleteBookConfirm(): Promise<void> {
  if (!bookId.value || !confirm('Удалить книгу? Экземпляры и связанные данные будут удалены.')) return
  try {
    await deleteBook(bookId.value)
    router.push({ name: 'admin-books' })
  } catch {
    errorMessage.value = 'Не удалось удалить книгу'
  }
}

function startAddCopy(): void {
  copyForm.value = { unique_number: '', status: 'Доступно', cover_url: null }
  addingCopy.value = true
}

function cancelAddCopy(): void {
  addingCopy.value = false
}

async function submitAddCopy(): Promise<void> {
  if (!copyForm.value.unique_number.trim() || !bookId.value) return
  try {
    const copy = await createCopy(bookId.value, {
      unique_number: copyForm.value.unique_number.trim(),
      status: copyForm.value.status,
      cover_url: copyForm.value.cover_url,
    })
    if (book.value) {
      book.value = { ...book.value, copies: [...book.value.copies, copy] }
    }
    addingCopy.value = false
    copyForm.value = { unique_number: '', status: 'Доступно', cover_url: null }
  } catch (err: unknown) {
    const msg =
      err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : null
    errorMessage.value = typeof msg === 'string' ? msg : 'Не удалось добавить экземпляр'
  }
}

function startEditCopy(id: number, status: string): void {
  editingCopyId.value = id
  editingCopyStatus.value = status
}

function cancelEditCopy(): void {
  editingCopyId.value = null
}

async function submitEditCopy(): Promise<void> {
  if (!editingCopyId.value) return
  try {
    const updated = await updateCopy(editingCopyId.value, {
      status: editingCopyStatus.value,
    })
    if (book.value) {
      book.value = {
        ...book.value,
        copies: book.value.copies.map((c) =>
          c.id === updated.id ? updated : c
        ),
      }
    }
    editingCopyId.value = null
  } catch {
    errorMessage.value = 'Не удалось обновить экземпляр'
  }
}

async function removeCopy(copyId: number): Promise<void> {
  if (!confirm('Удалить экземпляр?')) return
  deletingCopyId.value = copyId
  try {
    await deleteCopy(copyId)
    if (book.value) {
      book.value = {
        ...book.value,
        copies: book.value.copies.filter((c) => c.id !== copyId),
      }
    }
  } catch {
    errorMessage.value = 'Не удалось удалить экземпляр'
  } finally {
    deletingCopyId.value = null
  }
}

watch(() => form.value.cover_url, () => {
  coverPreviewError.value = false
})

watch(bookId, (id) => {
  if (id) loadBook()
  else {
    book.value = null
    form.value = {
      author_ids: [],
      title: '',
      description: null,
      cover_url: null,
      genre_id: null,
      age_rating_id: ageRatings.value[0]?.id ?? 0,
      language_id: languages.value[0]?.id ?? 0,
      tag_ids: null,
    }
    errorMessage.value = ''
  }
}, { immediate: true })

onMounted(async () => {
  try {
    const [a, g, ar, l, t] = await Promise.all([
      fetchAuthors(),
      fetchGenres(),
      fetchAgeRatings(),
      fetchLanguages(),
      fetchTags(),
    ])
    authors.value = a
    genres.value = g
    ageRatings.value = ar
    languages.value = l
    tags.value = t
    if (isNew.value && form.value.age_rating_id === 0 && ar[0])
      form.value.age_rating_id = ar[0].id
    if (isNew.value && form.value.language_id === 0 && l[0])
      form.value.language_id = l[0].id
  } catch {
    authors.value = []
    genres.value = []
    ageRatings.value = []
    languages.value = []
    tags.value = []
  }
})
</script>

<template>
  <div class="admin-book-edit">
    <header class="admin-book-edit__header">
      <div class="admin-book-edit__header-main">
        <router-link :to="{ name: 'admin-books' }" class="admin-book-edit__back">
          К списку книг
        </router-link>
        <h1 class="admin-book-edit__title">
          {{ isNew ? 'Новая книга' : (book?.title ?? '') }}
        </h1>
      </div>
      <div v-if="!isNew && book" class="admin-book-edit__header-actions">
        <button
          type="button"
          class="admin-book-edit__btn admin-book-edit__btn--outline-danger"
          aria-label="Удалить книгу"
          @click="deleteBookConfirm"
        >
          Удалить книгу
        </button>
      </div>
    </header>

    <template v-if="loading">
      <div class="admin-book-edit__loading">
        <span class="admin-book-edit__loading-text">Загрузка…</span>
      </div>
    </template>
    <template v-else>
      <div class="admin-book-edit__card">
        <div class="admin-book-edit__layout">
          <aside class="admin-book-edit__preview">
            <p class="admin-book-edit__cover-preview-label">Предпросмотр карточки</p>
            <div class="admin-book-edit__cover-card">
              <span class="admin-book-edit__cover-card-img-wrap">
                <img
                  v-if="form.cover_url && !coverPreviewError"
                  :src="form.cover_url"
                  alt=""
                  class="admin-book-edit__cover-card-img"
                  @error="coverPreviewError = true"
                >
                <span
                  v-else-if="!form.cover_url"
                  class="admin-book-edit__cover-card-placeholder"
                >
                  Нет обложки
                </span>
                <span
                  v-else
                  class="admin-book-edit__cover-card-placeholder"
                >
                  Ошибка загрузки
                </span>
              </span>
              <div class="admin-book-edit__cover-card-body">
                <span class="admin-book-edit__cover-card-author">
                  {{ coverPreviewAuthor }}
                </span>
                <span class="admin-book-edit__cover-card-title">
                  {{ form.title || 'Название книги' }}
                </span>
              </div>
            </div>
          </aside>
          <div class="admin-book-edit__form-wrap">
            <form class="admin-book-edit__form" @submit.prevent="saveBook">
              <div class="admin-book-edit__field">
                <label for="book-author" class="admin-book-edit__label">Авторы</label>
                <ChipSelect
                  id="book-author"
                  v-model="form.author_ids"
                  :items="authors"
                  placeholder="Найти автора…"
                  search-aria-label="Поиск автора для добавления"
                  remove-aria-label-prefix="Удалить автора "
                />
              </div>
              <div class="admin-book-edit__field">
                <label for="book-title" class="admin-book-edit__label">Название</label>
                <input
                  id="book-title"
                  v-model="form.title"
                  type="text"
                  class="admin-book-edit__input"
                  required
                  placeholder="Введите название книги"
                >
              </div>
              <div class="admin-book-edit__field">
                <label for="book-description" class="admin-book-edit__label">Описание</label>
                <textarea
                  id="book-description"
                  v-model="form.description"
                  class="admin-book-edit__input admin-book-edit__input--textarea"
                  rows="4"
                  placeholder="Краткое описание или аннотация"
                />
              </div>
              <div class="admin-book-edit__field">
                <label for="book-cover" class="admin-book-edit__label">Ссылка на обложку</label>
                <input
                  id="book-cover"
                  v-model="form.cover_url"
                  type="url"
                  class="admin-book-edit__input"
                  placeholder="https://..."
                >
              </div>
              <div class="admin-book-edit__row">
            <div class="admin-book-edit__field">
              <label for="book-genre" class="admin-book-edit__label">Жанр</label>
              <select
                id="book-genre"
                v-model="form.genre_id"
                class="admin-book-edit__select"
                :class="{ 'admin-book-edit__select--filled': form.genre_id }"
                aria-label="Жанр"
              >
                <option :value="null">
                  Выберите жанр
                </option>
                <option
                  v-for="g in genres"
                  :key="g.id"
                  :value="g.id"
                >
                  {{ g.name }}
                </option>
              </select>
            </div>
            <div class="admin-book-edit__field">
              <label for="book-age" class="admin-book-edit__label">Возраст</label>
              <select
                id="book-age"
                v-model="form.age_rating_id"
                class="admin-book-edit__select"
                aria-label="Возраст"
              >
                <option
                  v-for="ar in ageRatings"
                  :key="ar.id"
                  :value="ar.id"
                >
                  {{ ar.name }}
                </option>
              </select>
            </div>
            <div class="admin-book-edit__field">
              <label for="book-language" class="admin-book-edit__label">Язык</label>
              <select
                id="book-language"
                v-model="form.language_id"
                class="admin-book-edit__select"
                aria-label="Язык"
              >
                <option
                  v-for="lang in languages"
                  :key="lang.id"
                  :value="lang.id"
                >
                  {{ lang.name }}
                </option>
              </select>
            </div>
          </div>
          <div class="admin-book-edit__field">
            <label for="book-tags" class="admin-book-edit__label">Теги</label>
            <ChipSelect
              id="book-tags"
              v-model="tagIdsModel"
              :items="tags"
              placeholder="Найти тег…"
              creatable
              search-aria-label="Поиск тега для добавления"
              remove-aria-label-prefix="Удалить тег "
              @create="onCreateTag"
            />
          </div>
          <div v-if="errorMessage" class="admin-book-edit__error" role="alert">
            {{ errorMessage }}
          </div>
          <div class="admin-book-edit__form-actions">
            <button
              type="submit"
              class="admin-book-edit__btn admin-book-edit__btn--primary"
              :disabled="saving"
            >
              {{ isNew ? 'Создать книгу' : 'Сохранить' }}
            </button>
          </div>
            </form>
          </div>
        </div>
      </div>

      <section v-if="book && !isNew" class="admin-book-edit__card admin-book-edit__copies">
        <h2 class="admin-book-edit__copies-title">Экземпляры</h2>
        <p class="admin-book-edit__copies-desc">
          Номер экземпляра и статус. Добавляйте экземпляры после создания книги.
        </p>
        <ul class="admin-book-edit__copies-list">
          <li v-for="c in book.copies" :key="c.id" class="admin-book-edit__copy">
            <template v-if="editingCopyId === c.id">
              <input
                v-model="editingCopyStatus"
                type="text"
                class="admin-book-edit__copy-input"
                placeholder="Статус"
              >
              <div class="admin-book-edit__copy-actions">
                <button
                  type="button"
                  class="admin-book-edit__btn admin-book-edit__btn--primary admin-book-edit__btn--sm"
                  @click="submitEditCopy"
                >
                  Сохранить
                </button>
                <button
                  type="button"
                  class="admin-book-edit__btn admin-book-edit__btn--outline admin-book-edit__btn--sm"
                  @click="cancelEditCopy"
                >
                  Отмена
                </button>
              </div>
            </template>
            <template v-else>
              <span class="admin-book-edit__copy-number">{{ c.unique_number }}</span>
              <span class="admin-book-edit__copy-status">{{ c.status }}</span>
              <div class="admin-book-edit__copy-actions">
                <button
                  type="button"
                  class="admin-book-edit__btn admin-book-edit__btn--outline admin-book-edit__btn--sm"
                  @click="startEditCopy(c.id, c.status)"
                >
                  Изменить
                </button>
                <button
                  type="button"
                  class="admin-book-edit__btn admin-book-edit__btn--outline-danger admin-book-edit__btn--sm"
                  :disabled="deletingCopyId === c.id"
                  @click="removeCopy(c.id)"
                >
                  {{ deletingCopyId === c.id ? '…' : 'Удалить' }}
                </button>
              </div>
            </template>
          </li>
        </ul>
        <div v-if="addingCopy" class="admin-book-edit__copy-add">
          <input
            v-model="copyForm.unique_number"
            type="text"
            class="admin-book-edit__input"
            placeholder="Номер экземпляра"
          >
          <input
            v-model="copyForm.status"
            type="text"
            class="admin-book-edit__input"
            placeholder="Статус"
          >
          <div class="admin-book-edit__copy-actions">
            <button
              type="button"
              class="admin-book-edit__btn admin-book-edit__btn--primary admin-book-edit__btn--sm"
              @click="submitAddCopy"
            >
              Добавить
            </button>
            <button
              type="button"
              class="admin-book-edit__btn admin-book-edit__btn--outline admin-book-edit__btn--sm"
              @click="cancelAddCopy"
            >
              Отмена
            </button>
          </div>
        </div>
        <button
          v-else
          type="button"
          class="admin-book-edit__add-copy"
          @click="startAddCopy"
        >
          Добавить экземпляр
        </button>
      </section>
    </template>
  </div>
</template>

<style scoped>
/* Контейнер: на всю ширину, без цветного фона */
.admin-book-edit {
  width: 100%;
  padding: var(--spacing-2xl) var(--spacing-lg);
}

@media (min-width: 768px) {
  .admin-book-edit {
    padding: var(--spacing-3xl) var(--spacing-2xl);
  }
}

/* Шапка: навигация + заголовок, один акцент — ссылка */
.admin-book-edit__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-2xl);
}

.admin-book-edit__header-main {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.admin-book-edit__back {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-primary);
  text-decoration: none;
  line-height: var(--line-height-normal);
}

.admin-book-edit__back:hover {
  text-decoration: underline;
  color: var(--color-primary-hover);
}

.admin-book-edit__back:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.admin-book-edit__title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-snug);
  color: var(--color-text);
  margin: 0;
}

@media (max-width: 767px) {
  .admin-book-edit__title {
    font-size: var(--font-size-xl);
  }
}

.admin-book-edit__header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

/* Кнопки по ui-kit: primary 44px, padding 10–12 / 20–24, radius 7px */
.admin-book-edit__btn {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  line-height: 1.25;
  padding: 10px var(--spacing-xl);
  min-height: 44px;
  border-radius: var(--radius-md);
  cursor: pointer;
  border: none;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.admin-book-edit__btn:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.admin-book-edit__btn--primary {
  background: var(--color-primary);
  color: var(--color-background);
}

.admin-book-edit__btn--primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.admin-book-edit__btn--primary:active:not(:disabled) {
  background: var(--color-primary-active);
}

.admin-book-edit__btn--primary:disabled {
  background: var(--color-background-subtle);
  color: var(--color-text-muted);
  cursor: not-allowed;
}

.admin-book-edit__btn--outline {
  background: transparent;
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.admin-book-edit__btn--outline:hover {
  background: var(--color-background-alt);
  border-color: var(--color-border-dark);
}

.admin-book-edit__btn--outline-danger {
  background: transparent;
  color: var(--color-error);
  border: 1px solid var(--color-error);
}

.admin-book-edit__btn--outline-danger:hover {
  background: var(--color-error-bg);
}

.admin-book-edit__btn--sm {
  padding: var(--spacing-sm) var(--spacing-md);
  min-height: 36px;
  font-size: var(--font-size-sm);
}

/* Карточка: белый фон, border e5e7eb, radius 8px, тень sm (ui-kit) */
.admin-book-edit__card {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--spacing-2xl);
}

.admin-book-edit__card:last-child {
  margin-bottom: 0;
}

/* Раскладка: слева предпросмотр, справа форма */
.admin-book-edit__layout {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2xl);
}

@media (min-width: 768px) {
  .admin-book-edit__layout {
    flex-direction: row;
    align-items: flex-start;
    gap: var(--spacing-3xl);
  }
}

.admin-book-edit__preview {
  flex-shrink: 0;
}

@media (min-width: 768px) {
  .admin-book-edit__preview {
    position: sticky;
    top: var(--spacing-lg);
  }
}

.admin-book-edit__form-wrap {
  flex: 1;
  min-width: 0;
}

/* Форма: отступы между группами xl, база 8px */
.admin-book-edit__form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.admin-book-edit__field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.admin-book-edit__row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: var(--spacing-lg);
}

@media (max-width: 767px) {
  .admin-book-edit__row {
    grid-template-columns: 1fr;
  }
}

/* Метки: 14px, font-weight 500 (ui-kit) */
.admin-book-edit__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
}

/* Поля: фон f8f8f8, бордер e5e7eb, фокус outline 2px primary, radius 4px, 44px */
.admin-book-edit__input {
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-base);
  font-family: var(--font-family);
  color: var(--color-text);
  background: var(--color-background-input);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  min-height: 44px;
  transition: box-shadow 0.15s ease;
}

.admin-book-edit__input::placeholder {
  color: var(--color-text-light);
}

.admin-book-edit__input:hover {
  box-shadow: var(--shadow-input);
}

.admin-book-edit__input:focus {
  outline: none;
  box-shadow: var(--shadow-focus);
  border-color: var(--color-primary);
}

.admin-book-edit__input--textarea {
  resize: vertical;
  min-height: 6rem;
  padding-top: var(--spacing-md);
}

.admin-book-edit__cover-preview-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin: 0 0 var(--spacing-sm);
}

.admin-book-edit__cover-card {
  width: 160px;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.admin-book-edit__cover-card-img-wrap {
  display: block;
  width: 100%;
  aspect-ratio: 2 / 3;
  overflow: hidden;
  background: var(--color-background-alt);
  position: relative;
}

.admin-book-edit__cover-card-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.admin-book-edit__cover-card-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-align: center;
  padding: var(--spacing-sm);
}

.admin-book-edit__cover-card-body {
  padding: var(--spacing-sm) var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.admin-book-edit__cover-card-author {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.admin-book-edit__cover-card-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  line-height: var(--line-height-snug);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.admin-book-edit__select {
  padding: var(--spacing-sm) var(--spacing-md);
  padding-right: 2.25rem;
  font-size: var(--font-size-base);
  font-family: var(--font-family);
  color: var(--color-text-muted);
  background: var(--color-background-input);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  min-height: 44px;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666666' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right var(--spacing-md) center;
  transition: box-shadow 0.15s ease, border-color 0.15s ease;
}

.admin-book-edit__select--filled,
.admin-book-edit__select:focus {
  color: var(--color-text);
}

.admin-book-edit__select:hover {
  box-shadow: var(--shadow-input);
}

.admin-book-edit__select:focus {
  outline: none;
  box-shadow: var(--shadow-focus);
  border-color: var(--color-primary);
}

/* Ошибка: красный, фон error-bg (ui-kit) */
.admin-book-edit__error {
  font-size: var(--font-size-sm);
  color: var(--color-error);
  background: var(--color-error-bg);
  padding: var(--spacing-md);
  border-radius: var(--radius-sm);
  margin: 0;
}

.admin-book-edit__form-actions {
  padding-top: var(--spacing-sm);
}

/* Загрузка */
.admin-book-edit__loading {
  padding: var(--spacing-3xl);
  text-align: center;
}

.admin-book-edit__loading-text {
  font-size: var(--font-size-base);
  color: var(--color-text-muted);
}

/* Секция экземпляров: тот же карточный стиль */
.admin-book-edit__copies-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-snug);
  color: var(--color-text);
  margin: 0 0 var(--spacing-sm);
}

.admin-book-edit__copies-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-xl);
  line-height: var(--line-height-normal);
}

.admin-book-edit__copies-list {
  list-style: none;
  margin: 0 0 var(--spacing-lg);
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.admin-book-edit__copy {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-background-alt);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  flex-wrap: wrap;
}

.admin-book-edit__copy-number {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-base);
  min-width: 8rem;
  color: var(--color-text);
}

.admin-book-edit__copy-status {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  flex: 1;
}

.admin-book-edit__copy-input {
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-base);
  font-family: var(--font-family);
  color: var(--color-text);
  background: var(--color-background-input);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  min-height: 44px;
  min-width: 12rem;
}

.admin-book-edit__copy-input:focus {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.admin-book-edit__copy-actions {
  display: flex;
  gap: var(--spacing-sm);
  margin-left: auto;
}

.admin-book-edit__copy-add {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--color-background-alt);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-lg);
  flex-wrap: wrap;
}

.admin-book-edit__add-copy {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  padding: 10px var(--spacing-xl);
  min-height: 44px;
  background: transparent;
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.admin-book-edit__add-copy:hover {
  background: var(--color-background-alt);
  border-color: var(--color-border-dark);
}

.admin-book-edit__add-copy:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}
</style>
