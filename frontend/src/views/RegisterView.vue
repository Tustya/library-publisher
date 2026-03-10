<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import PhoneInput from '@/components/PhoneInput.vue'
import { register as apiRegister } from '@/api/auth'

const router = useRouter()
const { login } = useAuth()

const phone = ref('')
const password = ref('')
const passwordConfirm = ref('')
const phoneComplete = ref(false)
const passwordVisible = ref(false)
const passwordConfirmVisible = ref(false)
const errorMessage = ref('')
const loading = ref(false)

const passwordsMatch = computed(() => password.value === passwordConfirm.value)
const canSubmit = computed(
  () =>
    phoneComplete.value &&
    password.value.length >= 8 &&
    passwordsMatch.value &&
    !loading.value
)

async function onSubmit(): Promise<void> {
  if (!canSubmit.value) return
  errorMessage.value = ''
  loading.value = true
  try {
    await apiRegister(phone.value, password.value)
    await login(phone.value, password.value)
    router.push({ name: 'catalog' })
  } catch (err: unknown) {
    const msg =
      err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data
            ?.detail
        : null
    errorMessage.value =
      typeof msg === 'string' ? msg : 'Ошибка регистрации. Попробуйте другой номер.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-page__brand" aria-hidden="true">
      <p class="auth-page__brand-text">
        Библиопарк «Мир»
      </p>
    </div>
    <div class="auth-page__main">
      <div class="auth-page__card">
        <h1 class="auth-page__title">
          Регистрация
        </h1>
        <form
          class="auth-page__form"
          @submit.prevent="onSubmit"
        >
          <div class="auth-page__field">
            <label for="reg-phone" class="auth-page__label">
              Телефон
            </label>
            <PhoneInput
              id="reg-phone"
              v-model="phone"
              @update:complete="phoneComplete = $event"
            />
          </div>
          <div class="auth-page__field">
            <label for="reg-password" class="auth-page__label">
              Пароль
            </label>
            <div class="auth-page__input-wrap">
              <input
                id="reg-password"
                v-model="password"
                :type="passwordVisible ? 'text' : 'password'"
                autocomplete="new-password"
                class="auth-page__input auth-page__input_password"
                placeholder="Не менее 8 символов"
                minlength="8"
                required
              >
              <button
                type="button"
                class="auth-page__toggle"
                :aria-label="passwordVisible ? 'Скрыть пароль' : 'Показать пароль'"
                :aria-pressed="passwordVisible"
                @click="passwordVisible = !passwordVisible"
              >
                <span v-if="passwordVisible" class="auth-page__toggle-icon" aria-hidden="true">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                </span>
                <span v-else class="auth-page__toggle-icon" aria-hidden="true">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                </span>
              </button>
            </div>
          </div>
          <div class="auth-page__field">
            <label for="reg-password-confirm" class="auth-page__label">
              Повторите пароль
            </label>
            <div class="auth-page__input-wrap">
              <input
                id="reg-password-confirm"
                v-model="passwordConfirm"
                :type="passwordConfirmVisible ? 'text' : 'password'"
                autocomplete="new-password"
                class="auth-page__input auth-page__input_password"
                placeholder="Повторите пароль"
                minlength="8"
                :aria-invalid="!!(passwordConfirm && !passwordsMatch)"
                :aria-describedby="passwordConfirm && !passwordsMatch ? 'reg-password-confirm-hint' : undefined"
              >
              <button
                type="button"
                class="auth-page__toggle"
                :aria-label="passwordConfirmVisible ? 'Скрыть пароль' : 'Показать пароль'"
                :aria-pressed="passwordConfirmVisible"
                @click="passwordConfirmVisible = !passwordConfirmVisible"
              >
                <span v-if="passwordConfirmVisible" class="auth-page__toggle-icon" aria-hidden="true">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                </span>
                <span v-else class="auth-page__toggle-icon" aria-hidden="true">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                </span>
              </button>
            </div>
            <span
              v-if="passwordConfirm && !passwordsMatch"
              id="reg-password-confirm-hint"
              class="auth-page__hint"
              role="alert"
            >
              Пароли не совпадают
            </span>
          </div>
          <p v-if="errorMessage" class="auth-page__error" role="alert">
            {{ errorMessage }}
          </p>
          <button
            type="submit"
            class="auth-page__submit"
            :disabled="!canSubmit"
            :aria-busy="loading"
          >
            Зарегистрироваться
          </button>
        </form>
        <p class="auth-page__footer">
          Уже есть аккаунт?
          <router-link to="/login" class="auth-page__link">
            Войти
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: grid;
  min-height: calc(100vh - 64px);
  grid-template-columns: 1fr;
  grid-template-rows: auto 1fr;
}

@media screen and (min-width: 768px) {
  .auth-page {
    grid-template-columns: minmax(0, 1fr) minmax(20rem, 28rem);
    grid-template-rows: 1fr;
  }
}

.auth-page__brand {
  position: relative;
  background: var(--color-background-warm) url('/images/libre.jpg') center / cover no-repeat;
  padding: var(--spacing-2xl) var(--spacing-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 10rem;
}

.auth-page__brand::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(21, 20, 17, 0.35);
  pointer-events: none;
}

@media screen and (min-width: 768px) {
  .auth-page__brand {
    min-height: 100%;
    padding: var(--spacing-4xl);
  }
}

.auth-page__brand-text {
  position: relative;
  z-index: 1;
  font-family: var(--font-family);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-snug);
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
  margin: 0;
}

.auth-page__main {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl) var(--spacing-lg);
  background: var(--color-background);
}

@media screen and (min-width: 768px) {
  .auth-page__main {
    padding: var(--spacing-3xl);
    background: var(--color-background-alt);
  }
}

.auth-page__card {
  width: 100%;
  max-width: 28rem;
  background: var(--color-background);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-3xl);
}

.auth-page__title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-snug);
  color: var(--color-text);
  margin: 0 0 var(--spacing-2xl);
  text-align: center;
}

.auth-page__form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.auth-page__field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.auth-page__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
}

.auth-page__input-wrap {
  position: relative;
  display: flex;
  align-items: stretch;
}

.auth-page__input {
  width: 100%;
  height: 2.75rem;
  min-height: 44px;
  padding: 0 var(--spacing-lg);
  padding-right: 3rem;
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

.auth-page__input::placeholder {
  color: var(--color-text-light);
}

.auth-page__input:hover {
  border-color: var(--color-border-dark);
}

.auth-page__input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}

.auth-page__input:focus:not(:focus-visible) {
  box-shadow: none;
}

.auth-page__input[aria-invalid="true"] {
  border-color: var(--color-error);
}

.auth-page__input_password {
  padding-right: 3rem;
}

.auth-page__toggle {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 3rem;
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: none;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color 0.15s ease;
}

.auth-page__toggle:hover {
  color: var(--color-primary);
}

.auth-page__toggle:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.auth-page__toggle-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-page__hint {
  font-size: var(--font-size-sm);
  color: var(--color-error);
}

.auth-page__error {
  font-size: var(--font-size-sm);
  color: var(--color-error);
  background: var(--color-error-bg);
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-sm);
  margin: 0;
}

.auth-page__submit {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-normal);
  min-height: 44px;
  padding: 12px var(--spacing-xl);
  color: #fff;
  background: var(--color-primary);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.auth-page__submit:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.auth-page__submit:active:not(:disabled) {
  background: var(--color-primary-active);
}

.auth-page__submit:disabled {
  background: var(--color-background-subtle);
  color: var(--color-text-muted);
  cursor: not-allowed;
}

.auth-page__submit:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.auth-page__footer {
  margin: var(--spacing-2xl) 0 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.auth-page__link {
  color: var(--color-primary);
  font-weight: var(--font-weight-medium);
  margin-left: var(--spacing-xs);
}

.auth-page__link:hover {
  color: var(--color-primary-hover);
}
</style>
