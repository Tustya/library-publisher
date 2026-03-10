import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import ProfileView from '@/views/ProfileView.vue'
import CatalogView from '@/views/CatalogView.vue'
import BookView from '@/views/BookView.vue'
import AdminLayout from '@/views/admin/AdminLayout.vue'
import AdminBooksView from '@/views/admin/AdminBooksView.vue'
import AdminBookEditView from '@/views/admin/AdminBookEditView.vue'
import AdminReservationsView from '@/views/admin/AdminReservationsView.vue'
import AdminOverdueView from '@/views/admin/AdminOverdueView.vue'
import AdminReadersView from '@/views/admin/AdminReadersView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: { name: 'catalog' } },
    { path: '/catalog', name: 'catalog', component: CatalogView },
    { path: '/catalog/:id', name: 'book', component: BookView },
    { path: '/login', name: 'login', component: LoginView, meta: { guest: true } },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { guest: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true },
    },
    {
      path: '/admin',
      component: AdminLayout,
      meta: { requiresAuth: true, requiresAdmin: true },
      children: [
        { path: '', redirect: { name: 'admin-books' } },
        { path: 'books', name: 'admin-books', component: AdminBooksView },
        { path: 'books/new', name: 'admin-book-new', component: AdminBookEditView },
        { path: 'books/:id', name: 'admin-book-edit', component: AdminBookEditView },
        { path: 'reservations', name: 'admin-reservations', component: AdminReservationsView },
        { path: 'overdue', name: 'admin-overdue', component: AdminOverdueView },
        { path: 'readers', name: 'admin-readers', component: AdminReadersView },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const { init, isAuthenticated, isAdmin } = useAuth()
  await init()
  if (to.meta.guest && isAuthenticated.value) {
    return { name: 'catalog' }
  }
  if (to.meta.requiresAuth && !isAuthenticated.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && !isAdmin.value) {
    return { name: 'catalog' }
  }
  return true
})

export default router
