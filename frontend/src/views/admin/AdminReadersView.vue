<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchReaders } from '@/api/admin'
import type { AdminReaderItem } from '@/types/admin'

const readers = ref<AdminReaderItem[]>([])
const loading = ref(false)

function fullName(r: AdminReaderItem): string {
  const parts = [r.last_name, r.first_name, r.patronymic].filter(Boolean)
  return parts.length ? parts.join(' ') : '—'
}

function formatPhone(phone: string): string {
  if (phone.length === 11 && phone.startsWith('79')) {
    return `+7 ${phone.slice(1, 4)} ${phone.slice(4, 7)}-${phone.slice(7, 9)}-${phone.slice(9)}`
  }
  return phone
}

async function load(): Promise<void> {
  loading.value = true
  try {
    readers.value = await fetchReaders()
  } catch {
    readers.value = []
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="admin-readers">
    <p v-if="loading" class="admin-readers__loading">
      Загрузка…
    </p>
    <p v-else-if="readers.length === 0" class="admin-readers__empty">
      Нет зарегистрированных читателей.
    </p>
    <div v-else class="admin-readers__table-wrap">
      <table class="admin-readers__table" role="grid">
        <thead>
          <tr>
            <th>ID</th>
            <th>Телефон</th>
            <th>ФИО</th>
            <th>Адрес</th>
            <th>Роль</th>
            <th>Статус</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in readers" :key="r.id">
            <td>{{ r.id }}</td>
            <td>{{ formatPhone(r.phone) }}</td>
            <td>{{ fullName(r) }}</td>
            <td>{{ r.delivery_address || '—' }}</td>
            <td>
              <span :class="['admin-readers__role', r.role === 'admin' && 'admin-readers__role--admin']">
                {{ r.role === 'admin' ? 'Администратор' : 'Читатель' }}
              </span>
            </td>
            <td>{{ r.is_active ? 'Активен' : 'Неактивен' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.admin-readers__loading,
.admin-readers__empty {
  color: #555;
  margin: 0;
}

.admin-readers__table-wrap {
  overflow-x: auto;
}

.admin-readers__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9375rem;
}

.admin-readers__table th,
.admin-readers__table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.admin-readers__table th {
  font-weight: 600;
  background: #f5f5f5;
}

.admin-readers__table tbody tr:hover {
  background: #fafafa;
}

.admin-readers__role {
  font-size: 0.8125rem;
}

.admin-readers__role--admin {
  color: #0a7ea4;
  font-weight: 500;
}
</style>
