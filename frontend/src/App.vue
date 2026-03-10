<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const route = useRoute()
const router = useRouter()
const { user, isAuthenticated, isAdmin } = useAuth()
const menuOpen = ref(false)

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

function isActive(path: string): boolean {
  return route.path.startsWith(path)
}

const BURGER_BREAKPOINT = 768

function closeMenu(): void {
  menuOpen.value = false
}

function toggleMenu(): void {
  menuOpen.value = !menuOpen.value
}

function handleResize(): void {
  if (window.innerWidth >= BURGER_BREAKPOINT) {
    menuOpen.value = false
  }
}

function handleClickOutside(event: MouseEvent): void {
  const target = event.target as HTMLElement
  if (menuOpen.value && !target.closest('.app__header')) {
    closeMenu()
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="app">
    <a
      href="#main"
      class="skip-link"
    >Перейти к основному содержимому</a>
    <header class="app__header">
      <div class="app__header-inner">
        <div class="app__header-left">
          <h1 class="app__title">
            <router-link to="/catalog" class="app__title-link">Библиопарк "Мир"</router-link>
          </h1>
          <nav
            class="app__nav"
            :class="{ 'app__nav--open': menuOpen }"
            aria-label="Основная навигация"
          >
            <template v-if="isAuthenticated">
              <router-link
                to="/catalog"
                class="app__nav-link"
                :class="{ 'app__nav-link--active': isActive('/catalog') }"
                @click="closeMenu"
              >
                Каталог
              </router-link>
              <router-link
                v-if="isAdmin"
                to="/admin"
                class="app__nav-link"
                :class="{ 'app__nav-link--active': isActive('/admin') }"
                @click="closeMenu"
              >
                Админка
              </router-link>
            </template>
            <template v-else>
              <router-link
                to="/catalog"
                class="app__nav-link"
                :class="{ 'app__nav-link--active': isActive('/catalog') }"
                @click="closeMenu"
              >
                Каталог
              </router-link>
            </template>
            <template v-if="!isAuthenticated">
              <router-link
                to="/login"
                class="app__nav-link app__nav-auth"
                :class="{ 'app__nav-link--active': isActive('/login') }"
                @click="closeMenu"
              >
                Вход
              </router-link>
            </template>
            <template v-else>
              <router-link
                to="/profile"
                class="app__nav-link app__nav-link--avatar app__nav-auth"
                :class="{ 'app__nav-link--active': isActive('/profile') }"
                aria-label="Профиль"
                @click="closeMenu"
              >
                <span class="app__nav-avatar" aria-hidden="true">{{ avatarInitials }}</span>
                <span class="app__nav-link-text">Профиль</span>
              </router-link>
            </template>
          </nav>
        </div>
        <div class="app__header-right">
          <template v-if="!isAuthenticated">
            <router-link
              to="/login"
              class="app__login-btn app__header-auth"
              :class="{ 'app__login-btn--active': isActive('/login') }"
              aria-label="Вход"
              @click="closeMenu"
            >
              <svg
                class="app__login-icon"
                width="22"
                height="22"
                viewBox="0 0 18 18"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <path
                  d="M11.25 2.25H14.25C14.6478 2.25 15.0294 2.40804 15.3107 2.68934C15.592 2.97064 15.75 3.35218 15.75 3.75V14.25C15.75 14.6478 15.592 15.0294 15.3107 15.3107C15.0294 15.592 14.6478 15.75 14.25 15.75H11.25"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  d="M7.5 12.75L11.25 9L7.5 5.25"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  d="M11.25 9H2.25"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </router-link>
          </template>
          <template v-else>
            <router-link
              to="/profile"
              class="app__nav-link app__nav-link--avatar app__header-auth"
              :class="{ 'app__nav-link--active': isActive('/profile') }"
              aria-label="Профиль"
              @click="closeMenu"
            >
              <span class="app__nav-avatar" aria-hidden="true">{{ avatarInitials }}</span>
            </router-link>
          </template>
          <button
            type="button"
            class="app__burger"
            :class="{ 'app__burger--open': menuOpen }"
            :aria-expanded="menuOpen"
            :aria-label="menuOpen ? 'Закрыть меню' : 'Открыть меню навигации'"
            @click="toggleMenu"
          >
            <span class="app__burger-bar" />
            <span class="app__burger-bar" />
            <span class="app__burger-bar" />
          </button>
        </div>
      </div>
    </header>
    <Transition name="app__nav-backdrop">
      <div
        v-if="menuOpen"
        class="app__nav-backdrop"
        aria-hidden="true"
        @click="closeMenu"
      />
    </Transition>
    <main
      id="main"
      class="app__main"
      role="main"
    >
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 0.5rem 0.5rem;
}

.app__header {
  display: flex;
  align-items: center;
  width: calc(100% + 1rem);
  margin-left: -0.5rem;
  margin-right: -0.5rem;
  margin-bottom: 1rem;
  min-height: 64px;
  box-shadow: var(--shadow-divider-bottom);
}

.app__header-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  width: 100%;
  padding: 0 16px 0 24px;
}

.app__header-left {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-xl);
  flex: 1;
  min-width: 0;
}

.app__header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

@media (max-width: 767px) {
  .app__header-auth {
    display: none;
  }

  .app__header-right .app__nav-link--avatar,
  .app__header-right .app__nav-link--avatar .app__nav-avatar {
    display: none;
  }

  .app__nav {
    display: flex;
    position: fixed;
    top: 0;
    right: 0;
    width: 80vw;
    height: 100vh;
    flex-direction: column;
    align-items: stretch;
    gap: 0;
    padding: var(--spacing-xl);
    padding-top: calc(64px + var(--spacing-lg));
    background: var(--color-background);
    box-shadow: -4px 0 24px rgba(0, 0, 0, 0.12);
    z-index: 101;
    transform: translateX(100%);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    pointer-events: none;
    border-top: none;
    order: unset;
  }

  .app__nav--open {
    transform: translateX(0);
    pointer-events: auto;
    width: 80vw;
  }

  .app__nav-link {
    justify-content: flex-start;
    min-height: 48px;
  }
}

.app__nav-backdrop {
  display: none;
}

.app__nav-backdrop-enter-active,
.app__nav-backdrop-leave-active {
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.app__nav-backdrop-enter-from,
.app__nav-backdrop-leave-to {
  opacity: 0;
}

.app__nav-backdrop-enter-to,
.app__nav-backdrop-leave-from {
  opacity: 1;
}

@media (max-width: 767px) {
  .app__nav-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 100;
    background: rgba(0, 0, 0, 0.4);
    cursor: pointer;
  }
}

.app__login-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  color: var(--color-text);
  text-decoration: none;
  border-radius: var(--radius-md);
  transition: color 0.2s, background-color 0.2s;
  flex-shrink: 0;
}

.app__login-btn:hover {
  color: var(--color-primary);
  background-color: var(--color-background-alt);
}

.app__login-btn--active {
  color: var(--color-primary);
  background-color: var(--color-background-subtle);
}

.app__login-btn--active:hover {
  background-color: rgba(70, 130, 235, 0.08);
}

.app__login-btn:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.app__login-icon {
  flex-shrink: 0;
}

.app__title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-heading);
  margin: 0;
}

.app__title-link {
  color: var(--color-text);
  text-decoration: none;
}

.app__title-link:hover {
  color: var(--color-primary);
}

.app__title-link:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
  border-radius: var(--radius-sm);
}

.app__burger {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  width: 44px;
  height: 44px;
  padding: 10px;
  border: none;
  background: transparent;
  cursor: pointer;
}

.app__burger-bar {
  display: block;
  width: 100%;
  height: 2px;
  background: var(--color-primary);
  border-radius: 1px;
  transition: transform 0.2s, opacity 0.2s;
}

.app__burger--open .app__burger-bar:nth-child(1) {
  transform: translateY(7px) rotate(45deg);
}

.app__burger--open .app__burger-bar:nth-child(2) {
  opacity: 0;
}

.app__burger--open .app__burger-bar:nth-child(3) {
  transform: translateY(-7px) rotate(-45deg);
}

.app__nav {
  display: none;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  align-items: center;
}

.app__nav--open {
  display: flex;
  flex-direction: column;
  order: 10;
  padding: var(--spacing-lg) 0;
  border-top: 1px solid var(--color-border);
}

.app__nav-link {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
  text-decoration: none;
  padding: var(--spacing-sm) var(--spacing-md);
  min-height: 44px;
  min-width: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  transition: background-color 0.2s, color 0.2s;
}

.app__nav-link:hover {
  background-color: var(--color-background-alt);
  color: var(--color-primary);
}

.app__nav-link--active {
  color: var(--color-text);
  font-weight: var(--font-weight-semibold);
  background-color: var(--color-background-subtle);
}

.app__nav-link--active:hover {
  background-color: var(--color-background-alt);
  color: var(--color-text);
}

.app__nav-link--avatar {
  padding: 0;
}

.app__nav-link--avatar .app__nav-link-text {
  display: none;
}

.app__nav--open .app__nav-link--avatar .app__nav-avatar {
  display: none;
}

.app__nav--open .app__nav-link--avatar .app__nav-link-text {
  display: inline;
}

.app__nav--open .app__nav-link--avatar {
  padding: var(--spacing-sm) var(--spacing-md);
}

.app__nav-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-circle);
  background: var(--color-primary);
  color: var(--color-background);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.app__nav-link--avatar:hover .app__nav-avatar {
  background: var(--color-primary-hover);
}

.app__nav-link:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.app__main {
  width: 100%;
  max-width: var(--container-narrow);
  line-height: 1.6;
}

@media (min-width: 768px) {
  .app__burger {
    display: none;
  }

  .app__nav .app__nav-auth {
    display: none;
  }

  .app__nav {
    display: flex;
    flex-direction: row;
    width: auto;
    padding: 0;
    border-top: none;
    gap: var(--spacing-xs);
  }

  .app__nav--open {
    flex-direction: row;
  }

  .app__header-left {
    gap: var(--spacing-2xl);
  }

  .app {
    padding: 0 var(--spacing-xl) var(--spacing-xl);
  }

  .app__header {
    width: calc(100% + 3rem);
    margin-left: -1.5rem;
    margin-right: -1.5rem;
    margin-bottom: var(--spacing-xl);
  }

  .app__header-inner {
    padding: 0 16px 0 24px;
  }

  .app__title {
    font-size: var(--font-size-2xl);
  }
}

@media (min-width: 1024px) {
  .app {
    padding: 0 2rem 2rem;
  }

  .app__header {
    display: flex;
    align-items: center;
    width: calc(100% + 4rem);
    margin-left: -2rem;
    margin-right: -2rem;
    min-height: 64px;
  }

  .app__header-inner {
    width: 100%;
    padding: 0 16px 0 24px;
  }

  .app__main {
    max-width: var(--container-wide);
  }
}
</style>
