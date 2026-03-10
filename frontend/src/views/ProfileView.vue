<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { fetchMe, updateProfile } from '@/api/auth'
import { fetchMyReservations, cancelReservation } from '@/api/reservations'
import PhoneInput from '@/components/PhoneInput.vue'
import { formatPhoneDisplay } from '@/utils/phoneMask'
import type { User, UserUpdate } from '@/types/auth'
import type { ReservationItem } from '@/types/reservation'

const router = useRouter()
const { user: authUser, setUser, logout } = useAuth()

function handleLogout(): void {
  logout()
  router.push('/')
}
const user = ref<User | null>(null)
const editing = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const phoneComplete = ref(true)
const reservations = ref<ReservationItem[]>([])
const reservationsLoading = ref(false)
const cancelingId = ref<number | null>(null)

const form = ref<UserUpdate>({
  first_name: null,
  last_name: null,
  patronymic: null,
  phone: null,
  delivery_address: null,
})

const displayPhone = computed(() =>
  user.value?.phone ? formatPhoneDisplay(user.value.phone) : ''
)

const fullName = computed(() => {
  const u = user.value
  if (!u) return ''
  const parts = [u.last_name, u.first_name, u.patronymic].filter(Boolean)
  return parts.length ? parts.join(' ') : 'Не указано'
})

const avatarInitials = computed(() => {
  const u = user.value
  if (!u) return '?'
  const last = (u.last_name || '').trim().slice(0, 1).toUpperCase()
  const first = (u.first_name || '').trim().slice(0, 1).toUpperCase()
  if (last && first) return `${last}${first}`
  if (first) return first
  if (u.phone) return u.phone.slice(-1)
  return '?'
})

const canSave = computed(
  () =>
    (form.value.phone == null || phoneComplete.value) &&
    !saving.value
)

const reservationsOnHand = computed(
  () => reservations.value.filter((r) => r.status === 'issued')
)
const reservationsCurrent = computed(
  () => reservations.value.filter((r) => r.status === 'created')
)
const reservationsHistory = computed(
  () => reservations.value.filter((r) => r.status === 'returned')
)

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

async function loadUser(): Promise<void> {
  try {
    const u = authUser.value ?? (await fetchMe())
    user.value = u
    setUser(u)
    form.value = {
      first_name: u.first_name ?? null,
      last_name: u.last_name ?? null,
      patronymic: u.patronymic ?? null,
      phone: u.phone,
      delivery_address: u.delivery_address ?? null,
    }
    phoneComplete.value = true
  } catch {
    user.value = null
  }
}

function startEdit(): void {
  if (user.value) {
    form.value = {
      first_name: user.value.first_name ?? null,
      last_name: user.value.last_name ?? null,
      patronymic: user.value.patronymic ?? null,
      phone: user.value.phone,
      delivery_address: user.value.delivery_address ?? null,
    }
    phoneComplete.value = true
    editing.value = true
    errorMessage.value = ''
  }
}

function cancelEdit(): void {
  editing.value = false
  errorMessage.value = ''
}

async function save(): Promise<void> {
  if (!canSave.value || !user.value) return
  errorMessage.value = ''
  saving.value = true
  try {
    const payload: UserUpdate = {
      first_name: form.value.first_name || null,
      last_name: form.value.last_name || null,
      patronymic: form.value.patronymic || null,
      delivery_address: form.value.delivery_address || null,
    }
    if (form.value.phone != null) payload.phone = form.value.phone
    const updated = await updateProfile(payload)
    user.value = updated
    setUser(updated)
    editing.value = false
  } catch (err: unknown) {
    const msg =
      err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data
            ?.detail
        : null
    errorMessage.value =
      typeof msg === 'string' ? msg : 'Не удалось сохранить профиль.'
  } finally {
    saving.value = false
  }
}

async function loadReservations(): Promise<void> {
  if (!authUser.value) return
  reservationsLoading.value = true
  try {
    const res = await fetchMyReservations()
    reservations.value = res.items
  } catch {
    reservations.value = []
  } finally {
    reservationsLoading.value = false
  }
}

async function cancel(r: ReservationItem): Promise<void> {
  if (r.status !== 'created' || cancelingId.value !== null) return
  cancelingId.value = r.id
  try {
    await cancelReservation(r.id)
    await loadReservations()
  } finally {
    cancelingId.value = null
  }
}

onMounted(async () => {
  await loadUser()
  await loadReservations()
})
</script>

<template>
  <div class="profile">
    <template v-if="user">
      <div class="profile__grid">
        <!-- Колонка: профиль (данные или форма) -->
        <aside class="profile__aside">
          <!-- Режим просмотра -->
          <section
            v-if="!editing"
            class="profile__card profile__card--data"
          >
            <button
              type="button"
              class="profile__card-edit"
              aria-label="Редактировать профиль"
              @click="startEdit"
            >
              <svg class="profile__card-edit-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
            </button>
            <div class="profile__card-hero">
              <div class="profile__card-avatar" aria-hidden="true">
                {{ avatarInitials }}
              </div>
              <p class="profile__card-name">
                {{ fullName || 'Профиль' }}
              </p>
              <a :href="'tel:' + (user.phone || '')" class="profile__card-contact">
                {{ displayPhone }}
              </a>
              <p v-if="user.delivery_address" class="profile__card-address">
                {{ user.delivery_address }}
              </p>
            </div>
          </section>

          <!-- Режим редактирования -->
          <section
            v-else
            class="profile__card profile__card--edit"
          >
            <h2 class="profile__card-title">
              Редактирование
            </h2>
            <form
              class="profile__form"
              @submit.prevent="save"
            >
              <div class="profile__field">
                <label for="profile-phone" class="profile__label">Телефон</label>
                <PhoneInput
                  id="profile-phone"
                  :model-value="form.phone ?? ''"
                  @update:model-value="form.phone = $event"
                  @update:complete="phoneComplete = $event"
                />
              </div>
              <div class="profile__row">
                <div class="profile__field">
                  <label for="profile-lastname" class="profile__label">Фамилия</label>
                  <input
                    id="profile-lastname"
                    v-model="form.last_name"
                    type="text"
                    class="profile__input"
                    maxlength="100"
                    placeholder="Фамилия"
                  >
                </div>
                <div class="profile__field">
                  <label for="profile-firstname" class="profile__label">Имя</label>
                  <input
                    id="profile-firstname"
                    v-model="form.first_name"
                    type="text"
                    class="profile__input"
                    maxlength="100"
                    placeholder="Имя"
                  >
                </div>
              </div>
              <div class="profile__field">
                <label for="profile-patronymic" class="profile__label">Отчество</label>
                <input
                  id="profile-patronymic"
                  v-model="form.patronymic"
                  type="text"
                  class="profile__input"
                  maxlength="100"
                  placeholder="Отчество"
                >
              </div>
              <div class="profile__field">
                <label for="profile-address" class="profile__label">Адрес доставки</label>
                <textarea
                  id="profile-address"
                  v-model="form.delivery_address"
                  class="profile__input profile__input--textarea"
                  rows="3"
                  maxlength="500"
                  placeholder="Город, улица, дом, квартира"
                />
              </div>
              <p v-if="errorMessage" class="profile__error" role="alert">
                {{ errorMessage }}
              </p>
              <div class="profile__actions">
                <button
                  type="submit"
                  class="profile__btn profile__btn--primary"
                  :disabled="!canSave"
                >
                  Сохранить
                </button>
                <button
                  type="button"
                  class="profile__btn profile__btn--secondary"
                  @click="cancelEdit"
                >
                  Отмена
                </button>
              </div>
            </form>
          </section>
        </aside>

        <!-- Колонка: заказы -->
        <div class="profile__main">
          <!-- На руках -->
          <section class="profile__card profile__card--books">
            <h2 class="profile__card-title">
              На руках
            </h2>
            <p v-if="reservationsLoading" class="profile__empty">
              Загрузка…
            </p>
            <div v-else-if="reservationsOnHand.length === 0" class="profile__empty-block">
              <p class="profile__empty-block-text">
                Сейчас нет книг на руках.
              </p>
              <router-link to="/catalog" class="profile__empty-block-link">
                Перейти в каталог
              </router-link>
            </div>
            <ul v-else class="profile__bookings-list">
              <li
                v-for="r in reservationsOnHand"
                :key="r.id"
                :class="['profile__booking', r.is_overdue && 'profile__booking--overdue']"
              >
                <router-link
                  :to="{ name: 'book', params: { id: r.book_id } }"
                  class="profile__booking-link"
                  :aria-label="`Книга: ${r.book_title}`"
                >
                  <span class="profile__booking-cover">
                    <img
                      v-if="r.book_cover_url"
                      :src="r.book_cover_url"
                      :alt="`Обложка: ${r.book_title}`"
                      class="profile__booking-cover-img"
                      loading="lazy"
                    >
                    <span
                      v-else
                      class="profile__booking-cover-placeholder"
                    >
                      Нет обложки
                    </span>
                  </span>
                  <div class="profile__booking-body">
                    <span class="profile__booking-title">{{ r.book_title }}</span>
                    <span v-if="r.book_author" class="profile__booking-author">{{ r.book_author }}</span>
                    <div class="profile__booking-return">
                      <span class="profile__booking-return-label">Вернуть до:</span>
                      <strong class="profile__booking-return-date">{{ formatDate(r.due_return_date) }}</strong>
                      <span
                        v-if="r.is_overdue"
                        class="profile__booking-overdue-badge"
                        aria-label="Книга просрочена"
                      >
                        Просрочено
                      </span>
                    </div>
                  </div>
                </router-link>
              </li>
            </ul>
          </section>

          <!-- Текущие брони -->
          <section class="profile__card profile__card--books">
            <h2 class="profile__card-title">
              Текущие брони
            </h2>
            <p v-if="reservationsLoading" class="profile__empty">
              Загрузка…
            </p>
            <div v-else-if="reservationsCurrent.length === 0" class="profile__empty-block">
              <p class="profile__empty-block-text">
                Нет активных броней. Доставка по пятницам с 17:00 до 18:00.
              </p>
              <router-link to="/catalog" class="profile__empty-block-link">
                Заказать книгу
              </router-link>
            </div>
            <ul v-else class="profile__bookings-list">
              <li
                v-for="r in reservationsCurrent"
                :key="r.id"
                class="profile__booking"
              >
                <router-link
                  :to="{ name: 'book', params: { id: r.book_id } }"
                  class="profile__booking-link"
                  :aria-label="`Книга: ${r.book_title}`"
                >
                  <span class="profile__booking-cover">
                    <img
                      v-if="r.book_cover_url"
                      :src="r.book_cover_url"
                      :alt="`Обложка: ${r.book_title}`"
                      class="profile__booking-cover-img"
                      loading="lazy"
                    >
                    <span
                      v-else
                      class="profile__booking-cover-placeholder"
                    >
                      Нет обложки
                    </span>
                  </span>
                  <div class="profile__booking-body">
                    <span class="profile__booking-title">{{ r.book_title }}</span>
                    <span v-if="r.book_author" class="profile__booking-author">{{ r.book_author }}</span>
                  </div>
                </router-link>
                <div
                  class="profile__booking-actions"
                  @click.stop
                >
                  <button
                    type="button"
                    class="profile__btn profile__btn--secondary profile__btn--small"
                    :disabled="cancelingId === r.id"
                    aria-label="Отменить бронь"
                    @click="cancel(r)"
                  >
                    {{ cancelingId === r.id ? 'Отмена…' : 'Отменить' }}
                  </button>
                </div>
              </li>
            </ul>
          </section>

          <!-- История заказов -->
          <section class="profile__card profile__card--books profile__card--muted">
            <h2 class="profile__card-title">
              История заказов
            </h2>
            <p v-if="reservationsLoading" class="profile__empty">
              Загрузка…
            </p>
            <div v-else-if="reservationsHistory.length === 0" class="profile__empty-block">
              <p class="profile__empty-block-text">
                Пока нет завершённых заказов.
              </p>
            </div>
            <ul v-else class="profile__bookings-list">
              <li
                v-for="r in reservationsHistory"
                :key="r.id"
                class="profile__booking profile__booking--history"
              >
                <router-link
                  :to="{ name: 'book', params: { id: r.book_id } }"
                  class="profile__booking-link"
                  :aria-label="`Книга: ${r.book_title}`"
                >
                  <span class="profile__booking-cover">
                    <img
                      v-if="r.book_cover_url"
                      :src="r.book_cover_url"
                      :alt="`Обложка: ${r.book_title}`"
                      class="profile__booking-cover-img"
                      loading="lazy"
                    >
                    <span
                      v-else
                      class="profile__booking-cover-placeholder"
                    >
                      Нет обложки
                    </span>
                  </span>
                  <div class="profile__booking-body">
                    <span class="profile__booking-title">{{ r.book_title }}</span>
                    <span v-if="r.book_author" class="profile__booking-author">{{ r.book_author }}</span>
                  </div>
                </router-link>
              </li>
            </ul>
          </section>
        </div>

        <div class="profile__logout-wrap">
          <button
            type="button"
            class="profile__btn profile__btn--secondary profile__btn--logout"
            @click="handleLogout"
          >
            Выход
          </button>
        </div>
      </div>
    </template>

    <div v-else class="profile__loading-wrap">
      <p class="profile__loading">Загрузка…</p>
    </div>
  </div>
</template>

<style scoped>
/* ——— Контейнер ——— */
.profile {
  width: 100%;
  max-width: var(--container-wide);
  margin: 0 auto;
}

/* ——— Сетка: сайдбар + основной контент ——— */
.profile__grid {
  display: grid;
  gap: var(--spacing-3xl);
}

@media (min-width: 1024px) {
  .profile__grid {
    grid-template-columns: minmax(0, 22rem) 1fr;
    gap: var(--spacing-4xl);
    align-items: start;
  }
}

.profile__aside {
  min-width: 0;
}

.profile__logout-wrap {
  margin-top: var(--spacing-2xl);
  grid-column: 1 / -1;
}

.profile__btn--logout {
  width: auto;
  padding: 0;
  min-height: auto;
  background: transparent;
  box-shadow: none;
  color: var(--color-text-muted);
  font-weight: var(--font-weight-normal);
  text-decoration: none;
}

.profile__btn--logout:hover {
  color: var(--color-primary);
  background: transparent;
  box-shadow: none;
}

.profile__btn--logout:active {
  background: transparent;
  box-shadow: none;
}

.profile__main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3xl);
}

/* ——— Карточки: радиус 8px по ui-kit, тени без линий ——— */
.profile__card {
  background: var(--color-background);
  border-radius: var(--radius-lg);
  padding: var(--spacing-2xl);
  box-shadow: var(--shadow-card);
}

.profile__card--data {
  background: var(--color-background-alt);
  padding: var(--spacing-xl);
  position: sticky;
  top: var(--spacing-xl);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  box-shadow: var(--shadow-card);
}

.profile__card-edit {
  position: absolute;
  top: var(--spacing-md);
  right: var(--spacing-md);
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: none;
  border-radius: var(--radius-circle);
  background: var(--color-background);
  color: var(--color-text-secondary);
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
}

.profile__card-edit:hover {
  color: var(--color-primary);
  background: var(--color-background);
  box-shadow: var(--shadow-md);
}

.profile__card-edit:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.profile__card-edit-icon {
  flex-shrink: 0;
}

.profile__card-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  width: 100%;
}

.profile__card-avatar {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-circle);
  background: var(--color-primary);
  color: var(--color-background);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: -0.02em;
  flex-shrink: 0;
}

.profile__card-name {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-snug);
  color: var(--color-text);
}

.profile__card-contact {
  font-size: var(--font-size-base);
  color: var(--color-primary);
  text-decoration: none;
  transition: color 0.2s ease;
}

.profile__card-contact:hover {
  color: var(--color-primary-hover);
}

.profile__card-address {
  margin: 0;
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
  color: var(--color-text-muted);
  max-width: 100%;
}

.profile__card--edit {
  position: sticky;
  top: var(--spacing-xl);
  min-width: 0;
}

.profile__card--books {
  min-width: 0;
}

.profile__card-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-heading);
  color: var(--color-text);
  margin: 0 0 var(--spacing-lg);
  letter-spacing: -0.01em;
}

.profile__card-actions {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-lg);
  box-shadow: var(--shadow-divider-top);
}

/* ——— Данные профиля: компактная сетка label / value ——— */
.profile__dl {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.profile__dl-item {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--spacing-sm) var(--spacing-lg);
  align-items: baseline;
  padding: var(--spacing-md) 0;
  box-shadow: var(--shadow-divider-bottom);
}

.profile__dl-item:last-of-type {
  box-shadow: none;
  padding-bottom: 0;
}

.profile__dt {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-muted);
  line-height: var(--line-height-normal);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  order: 1;
}

.profile__dd {
  margin: 0;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-normal);
  color: var(--color-text);
  line-height: var(--line-height-body);
  text-align: right;
  order: 2;
}

@media (min-width: 380px) {
  .profile__dl-item {
    grid-template-columns: 7rem 1fr;
    align-items: baseline;
  }

  .profile__dd {
    text-align: left;
  }
}

/* ——— Кнопки ——— */
.profile__btn {
  padding: 12px var(--spacing-xl);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  font-family: var(--font-family);
  border-radius: var(--radius-md);
  cursor: pointer;
  min-height: 44px;
  transition: background-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease, transform 0.15s ease;
  box-sizing: border-box;
}

.profile__btn:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.profile__btn--primary {
  border: none;
  background: var(--color-primary);
  color: var(--color-background);
}

.profile__btn--primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
  transform: translateY(-1px);
}

.profile__btn--primary:active:not(:disabled) {
  background: var(--color-primary-active);
  transform: translateY(0);
}

.profile__btn--primary:disabled {
  background: var(--color-background-subtle);
  color: var(--color-text-muted);
  cursor: not-allowed;
  opacity: 1;
  transform: none;
}

.profile__btn--secondary {
  background: var(--color-background);
  border: none;
  color: var(--color-text);
  box-shadow: var(--shadow-sm);
}

.profile__btn--secondary:hover:not(:disabled) {
  color: var(--color-primary);
  background: rgba(70, 130, 235, 0.06);
  box-shadow: var(--shadow-md);
}

.profile__btn--secondary:active:not(:disabled) {
  background: rgba(70, 130, 235, 0.1);
  box-shadow: var(--shadow-sm);
}

/* ——— Форма ——— */
.profile__form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
  min-width: 0;
}

.profile__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
  min-width: 0;
}

.profile__row .profile__field {
  min-width: 0;
}

@media (max-width: 380px) {
  .profile__row {
    grid-template-columns: 1fr;
  }
}

.profile__field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.profile__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
  line-height: var(--line-height-normal);
}

.profile__input {
  width: 100%;
  min-width: 0;
  padding: 12px var(--spacing-lg);
  font-size: var(--font-size-base);
  font-family: var(--font-family);
  line-height: var(--line-height-body);
  color: var(--color-text);
  background: var(--color-background-input);
  border: none;
  border-radius: var(--radius-sm);
  box-sizing: border-box;
  box-shadow: var(--shadow-input);
  transition: box-shadow 0.2s ease;
}

.profile__input::placeholder {
  color: var(--color-text-light);
}

.profile__input:focus {
  outline: none;
  box-shadow: 0 0 0 2px var(--color-primary), 0 1px 2px rgba(21, 20, 17, 0.04);
}

.profile__input:focus-visible {
  outline: var(--focus-outline);
  outline-offset: 2px;
}

.profile__input--textarea {
  resize: vertical;
  min-height: 88px;
  line-height: var(--line-height-body);
}

.profile__error {
  font-size: var(--font-size-sm);
  color: var(--color-error);
  background: var(--color-error-bg);
  padding: var(--spacing-md);
  border-radius: var(--radius-sm);
  margin: 0;
  line-height: var(--line-height-normal);
}

.profile__actions {
  display: flex;
  gap: var(--spacing-lg);
  flex-wrap: wrap;
}

/* ——— Пустые состояния: блок с CTA ——— */
.profile__empty {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--color-text-muted);
  line-height: var(--line-height-body);
}

.profile__empty-block {
  padding: var(--spacing-2xl);
  background: var(--color-background-alt);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  text-align: center;
}

.profile__empty-block-text {
  margin: 0 0 var(--spacing-md);
  font-size: var(--font-size-base);
  color: var(--color-text-muted);
  line-height: var(--line-height-body);
}

.profile__empty-block-link {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-primary);
  text-decoration: none;
  transition: color 0.2s ease;
}

.profile__empty-block-link:hover {
  color: var(--color-primary-hover);
  text-decoration: underline;
}

.profile__empty-block-link:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
  border-radius: var(--radius-sm);
}

/* ——— Загрузка ——— */
.profile__loading-wrap {
  padding: var(--spacing-5xl) var(--spacing-lg);
  text-align: center;
}

.profile__loading {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--color-text-muted);
}

/* ——— Список заказов / книг: горизонтальная карусель в одну строку ——— */
.profile__bookings-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: nowrap;
  gap: 1rem;
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.profile__bookings-list::-webkit-scrollbar {
  display: none;
}

/* Карточка книги: фиксированная ширина в карусели, snap для плавной прокрутки */
.profile__booking {
  flex: 0 0 auto;
  width: 160px;
  display: flex;
  flex-direction: column;
  min-height: 100%;
  background: var(--color-background);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  transition: box-shadow 0.2s ease;
}

@media (min-width: 768px) {
  .profile__booking {
    width: 180px;
  }
}

@media (min-width: 1024px) {
  .profile__booking {
    width: 200px;
  }
}

.profile__booking:hover {
  box-shadow: var(--shadow-lg);
}

.profile__booking--overdue {
  background: var(--color-brand-gold-bg);
  box-shadow: var(--shadow-card), 0 2px 12px rgba(248, 180, 43, 0.12);
}

.profile__booking--overdue:hover {
  box-shadow: var(--shadow-lg), 0 2px 12px rgba(248, 180, 43, 0.14);
}

/* Ссылка на всю карточку */
.profile__booking-link {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  text-decoration: none;
  color: inherit;
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-radius: var(--radius-lg);
}

.profile__booking-link:hover {
  background: var(--color-background-alt);
}

.profile__booking-link:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

/* Обложка: соотношение 2:3 по ui-kit */
.profile__booking-cover {
  display: block;
  width: 100%;
  aspect-ratio: 2 / 3;
  overflow: hidden;
  background: var(--color-background-alt);
}

.profile__booking-cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.profile__booking-cover-placeholder {
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

/* Под обложкой: иерархия текста по дизайн-системе */
.profile__booking-body {
  flex: 1;
  min-width: 0;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.profile__booking-body .profile__booking-return {
  margin-top: auto;
}

.profile__booking-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: var(--line-height-snug);
}

.profile__booking-author {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-normal);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.profile__booking-return {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
  color: var(--color-text);
}

.profile__booking-return-label {
  color: var(--color-text-muted);
  font-weight: var(--font-weight-normal);
}

.profile__booking-return-date {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
}

/* Золотой бейдж «Просрочено» — важно сейчас (ui-kit) */
.profile__booking-overdue-badge {
  display: inline-block;
  padding: var(--spacing-xs) var(--spacing-md);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  background: var(--color-brand-gold);
  color: var(--color-brand-dark);
  border-radius: var(--radius-sm);
  line-height: var(--line-height-normal);
}

.profile__booking-actions {
  flex-shrink: 0;
  padding: var(--spacing-md);
  display: flex;
  align-items: center;
  box-shadow: var(--shadow-divider-top);
  background: var(--color-background);
}

.profile__booking-actions .profile__btn {
  width: 100%;
  justify-content: center;
}

.profile__booking--history {
  background: var(--color-background-alt);
}

.profile__card--muted .profile__booking {
  background: var(--color-background-alt);
}

.profile__btn--small {
  padding: var(--spacing-sm) var(--spacing-lg);
  font-size: var(--font-size-sm);
  min-height: 36px;
}

/* ——— Адаптив ——— */
@media (max-width: 1023px) {
  .profile__card--edit {
    position: static;
  }
}

@media (max-width: 767px) {
  .profile__card {
    padding: var(--spacing-xl);
  }

  .profile__actions {
    flex-direction: column;
  }

  .profile__actions .profile__btn {
    width: 100%;
  }
}

</style>
