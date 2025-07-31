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
import ErrorPage from '@/components/common/ErrorPage.vue'

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
  },
  // Catch-all route for 404 errors
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: ErrorPage,
    meta: { requiresAuth: false }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard for authentication
router.beforeEach(async (to, from, next) => {
  // Skip auth check for login and register pages
  if (to.meta.requiresAuth === false) {
    next()
    return
  }

  // Check if user is authenticated
  if (authService.authenticated.value) {
    next()
  } else {
    // Try to restore session
    try {
      await authService.restoreSession()
      if (authService.authenticated.value) {
        next()
      } else {
        next('/login')
      }
    } catch (error) {
      console.error('Failed to restore session:', error)
      next('/login')
    }
  }
})

export default router 