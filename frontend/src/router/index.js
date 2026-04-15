import { createRouter, createWebHistory } from 'vue-router'

import UserLayout from '../layouts/UserLayout.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import { useUserStore } from '../stores/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: UserLayout,
      children: [
        { path: '', name: 'home', component: () => import('../views/user/Home.vue') },
        { path: 'login', name: 'login', component: () => import('../views/user/Login.vue'), meta: { guestOnly: true } },
        { path: 'register', name: 'register', component: () => import('../views/user/Register.vue'), meta: { guestOnly: true } },
        { path: 'search', name: 'search', component: () => import('../views/user/SearchResults.vue') },
        { path: 'products/:id', name: 'product-detail', component: () => import('../views/user/ProductDetail.vue') },
        { path: 'messages', name: 'messages', component: () => import('../views/user/Messages.vue'), meta: { requiresAuth: true } },
        { path: 'publish', name: 'publish', component: () => import('../views/user/PublishProduct.vue'), meta: { requiresAuth: true } },
        { path: 'my-products', name: 'my-products', component: () => import('../views/user/MyProducts.vue'), meta: { requiresAuth: true } },
        { path: 'sellers/:sellerId', name: 'seller-profile', component: () => import('../views/user/SellerProfile.vue') },
        { path: 'orders', name: 'orders', component: () => import('../views/user/MyOrders.vue'), meta: { requiresAuth: true } },
        { path: 'favorites', name: 'favorites', component: () => import('../views/user/Favorites.vue'), meta: { requiresAuth: true } },
        { path: 'history', name: 'history', component: () => import('../views/user/History.vue'), meta: { requiresAuth: true } },
        { path: 'profile', name: 'profile', component: () => import('../views/user/Profile.vue'), meta: { requiresAuth: true } }
      ]
    },
    {
      path: '/admin',
      component: AdminLayout,
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/admin/audits' },
        { path: 'dashboard', name: 'admin-dashboard', component: () => import('../views/admin/Dashboard.vue') },
        { path: 'products', name: 'admin-products', component: () => import('../views/admin/ProductAudit.vue') },
        { path: 'products/:productId', name: 'admin-product-detail', component: () => import('../views/admin/ProductDetailAdmin.vue') },
        { path: 'audits', name: 'admin-audits', component: () => import('../views/admin/AuditQueue.vue') },
        { path: 'operations', name: 'admin-operations', component: () => import('../views/admin/OperationLogs.vue') },
        { path: 'recommendations', name: 'admin-recommendations', component: () => import('../views/admin/RecommendationWorkbench.vue') },
        { path: 'notifications', name: 'admin-notifications', component: () => import('../views/admin/AdminNotifications.vue') },
        { path: 'platform', name: 'admin-platform', component: () => import('../views/admin/PlatformOps.vue') },
        { path: 'reports', name: 'admin-reports', component: () => import('../views/admin/ReportManage.vue') },
        { path: 'appeals', name: 'admin-appeals', component: () => import('../views/admin/AppealManage.vue') },
        { path: 'access', name: 'admin-access', component: () => import('../views/admin/AccessManage.vue') }
      ]
    }
  ],
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach(async (to) => {
  const userStore = useUserStore()
  if (!userStore.initialized) {
    await userStore.bootstrap()
  }

  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.guestOnly && userStore.isAuthenticated) {
    return { name: 'home' }
  }

  if (to.path.startsWith('/admin') && !userStore.isAdmin) {
    return { name: 'home' }
  }

  return true
})

export default router
