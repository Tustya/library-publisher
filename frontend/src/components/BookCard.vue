<script setup lang="ts">
import type { BookListEntry } from '@/types/catalog'

defineProps<{
  book: BookListEntry
}>()
</script>

<template>
  <article class="book-card">
    <router-link
      :to="{ name: 'book', params: { id: book.id } }"
      class="book-card__link"
      :aria-label="`Книга: ${book.title}`"
    >
      <span class="book-card__cover-wrap">
        <img
          v-if="book.cover_url"
          :src="book.cover_url"
          :alt="`Обложка: ${book.title}`"
          class="book-card__cover"
          loading="lazy"
        >
        <span
          v-else
          class="book-card__cover book-card__cover--placeholder"
        >
          Нет обложки
        </span>
        <span
          v-if="book.available_count === 0"
          class="book-card__badge"
          aria-hidden="true"
        >
          На руках
        </span>
      </span>
      <div class="book-card__body">
        <span class="book-card__author">{{ book.author }}</span>
        <span class="book-card__title">{{ book.title }}</span>
      </div>
    </router-link>
  </article>
</template>

<style scoped>
.book-card {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  background: var(--color-background);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  transition: box-shadow 0.2s ease;
}

.book-card:hover {
  box-shadow: var(--shadow-lg);
}

.book-card__link {
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

.book-card__link:hover {
  background: var(--color-background-alt);
}

.book-card__link:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.book-card__cover-wrap {
  position: relative;
  display: block;
  width: 100%;
  aspect-ratio: 2 / 3;
  overflow: hidden;
  background: var(--color-background-alt);
}

.book-card__badge {
  position: absolute;
  top: var(--spacing-sm);
  right: var(--spacing-sm);
  padding: var(--spacing-xs) var(--spacing-md);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  line-height: 1.2;
  color: var(--color-background);
  background: rgba(21, 20, 17, 0.75);
  border-radius: var(--radius-sm);
  backdrop-filter: blur(4px);
}

.book-card__cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.book-card__cover--placeholder {
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

.book-card__body {
  flex: 1;
  min-width: 0;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.book-card__title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: var(--line-height-snug);
}

.book-card__author {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-normal);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
