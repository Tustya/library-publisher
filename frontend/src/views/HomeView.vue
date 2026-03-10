<script setup lang="ts">
import { useAuth } from '@/composables/useAuth'

const { isAuthenticated, user } = useAuth()
</script>

<template>
  <div class="home">
    <h1 class="home__title">
      Библиопарк "Мир"
    </h1>
    <p class="home__lead">
      Цифровой сервис библиотеки — каталог, бронирование, доставка книг.
    </p>
    <p
      v-if="isAuthenticated && user"
      class="home__user"
    >
      Вы вошли как {{ user.phone }}
    </p>
  </div>
</template>

<style scoped>
.home {
  max-width: 40rem;
  width: 100%;
}

@media (min-width: 1024px) {
  .home {
    max-width: 48rem;
  }
}

.home__title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem;
}

.home__lead {
  line-height: 1.6;
  margin: 0 0 1rem;
}

.home__user {
  font-size: 0.875rem;
  color: #555;
  margin: 0;
}
</style>
