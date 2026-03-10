<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { path: '/admin/books', name: 'admin-books', label: 'Книги' },
  { path: '/admin/reservations', name: 'admin-reservations', label: 'Брони' },
  { path: '/admin/overdue', name: 'admin-overdue', label: 'Просрочки' },
  { path: '/admin/readers', name: 'admin-readers', label: 'Читатели' },
]

function isActive(item: (typeof navItems)[0]): boolean {
  return (
    route.path.startsWith(item.path) ||
    route.name === item.name ||
    (item.path === '/admin/books' && route.name === 'admin-book-edit')
  )
}
</script>

<template>
  <div class="admin">
    <nav class="admin__nav" aria-label="Административное меню">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="admin__nav-link"
        :class="{ 'admin__nav-link--active': isActive(item) }"
      >
        {{ item.label }}
      </router-link>
    </nav>
    <div class="admin__content">
      <router-view />
    </div>
  </div>
</template>

<style scoped>
.admin {
  width: 100%;
}

.admin__nav {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-2xl);
  padding-bottom: var(--spacing-lg);
  box-shadow: var(--shadow-divider-bottom);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.admin__nav-link {
  padding: var(--spacing-sm) var(--spacing-lg);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-primary);
  text-decoration: none;
  border-radius: var(--radius-md);
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.admin__nav-link:hover {
  background: var(--color-background-alt);
}

.admin__nav-link--active {
  background: var(--color-primary);
  color: var(--color-background);
}

.admin__nav-link--active:hover {
  background: var(--color-primary-hover);
  color: var(--color-background);
}

.admin__content {
  width: 100%;
}
</style>
