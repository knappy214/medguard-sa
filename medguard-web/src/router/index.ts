import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import authService from '@/services/authService'

// Import components
import LoginForm from '@/components/auth/LoginForm.vue'
import RegisterForm from '@/components/auth/RegisterForm.vue'
import PasswordResetForm from '@/components/auth/PasswordResetForm.vue'
import ProfileForm from '@/components/auth/ProfileForm.vue'
import Dashboard from '@/components/common/Dashboard.vue'
import MedicationDashboard from '@/components/medication/MedicationDashboard.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginForm,
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterForm,
    meta: { requiresAuth: false }
  },
  {
    path: '/password-reset',
    name: 'PasswordReset',
    component: PasswordResetForm,
    meta: { requiresAuth: false }
  },
  {
    path: '/password-reset/:uidb64/:token',
    name: 'PasswordResetConfirm',
    component: PasswordResetForm,
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: ProfileForm,
    meta: { requiresAuth: true }
  },
  {
    path: '/medications',
    name: 'Medications',
    component: MedicationDashboard,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard for authentication
router.beforeEach((to, from, next) => {
  const requiresAuth = to.meta.requiresAuth !== false
  
  if (requiresAuth && !authService.authenticated.value) {
    // Redirect to login if authentication is required but user is not authenticated
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && authService.authenticated.value) {
    // Redirect to dashboard if user is already authenticated and trying to access auth pages
    next('/dashboard')
  } else {
    next()
  }
})

export default router 