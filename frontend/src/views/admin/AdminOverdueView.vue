<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchOverdue } from '@/api/admin'
import type { AdminOverdueItem } from '@/types/admin'

const overdue = ref<AdminOverdueItem[]>([])
const loading = ref(false)

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function formatPhone(raw: string | undefined): string {
  if (!raw) return '—'
  const digits = raw.replace(/\D/g, '')
  if (digits.length === 11 && (digits[0] === '7' || digits[0] === '8')) {
    return `+7 (${digits.slice(1, 4)}) ${digits.slice(4, 7)}-${digits.slice(7, 9)}-${digits.slice(9)}`
  }
  if (digits.length === 10 && digits[0] === '9') {
    return `+7 (${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 8)}-${digits.slice(8)}`
  }
  return raw
}

async function load(): Promise<void> {
  loading.value = true
  try {
    overdue.value = await fetchOverdue()
  } catch {
    overdue.value = []
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="admin-overdue">
    <p v-if="loading" class="admin-overdue__loading">
      Загрузка…
    </p>
    <p v-else-if="overdue.length === 0" class="admin-overdue__empty">
      Нет просроченных возвратов.
    </p>
    <div v-else class="admin-overdue__table-wrap">
      <table class="admin-overdue__table" role="grid">
        <thead>
          <tr>
            <th>Читатель</th>
            <th class="admin-overdue__th-contact">Контакты</th>
            <th>Книга</th>
            <th>Срок возврата</th>
            <th>Дней просрочки</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="o in overdue" :key="o.reservation_id">
            <td>
              {{ o.user_name || '—' }}
            </td>
            <td class="admin-overdue__cell-contact">{{ formatPhone(o.user_phone) }}</td>
            <td>
              <RouterLink :to="{ name: 'book', params: { id: o.book_id } }" class="admin-overdue__book-link">
                {{ o.book_author }}
              </RouterLink>.
              <RouterLink :to="{ name: 'book', params: { id: o.book_id } }" class="admin-overdue__book-link">
                {{ o.book_title }}
              </RouterLink>
            </td>
            <td>{{ formatDate(o.due_return_date) }}</td>
            <td>
              <strong class="admin-overdue__days">{{ o.days_overdue }}</strong>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.admin-overdue__loading,
.admin-overdue__empty {
  color: #555;
  margin: 0;
}

.admin-overdue__table-wrap {
  overflow-x: auto;
}

.admin-overdue__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9375rem;
}

.admin-overdue__table th,
.admin-overdue__table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.admin-overdue__table th {
  font-weight: 600;
  background: #f5f5f5;
}

.admin-overdue__th-contact,
.admin-overdue__cell-contact {
  min-width: 11em;
  white-space: nowrap;
}

.admin-overdue__table tbody tr:hover {
  background: #fafafa;
}

.admin-overdue__days {
  color: #c62828;
}

.admin-overdue__book-link {
  color: var(--color-primary, #1976d2);
  text-decoration: none;
}

.admin-overdue__book-link:hover {
  text-decoration: underline;
}
</style>
