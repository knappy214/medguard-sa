# 🔐 MedGuard SA Authentication System

A comprehensive, HIPAA-compliant authentication system built with Vue 3, TypeScript, and Django REST Framework.

## 🚀 Features

### ✅ **User Registration**
- **Multi-step registration form** with validation
- **Password strength indicator** with real-time feedback
- **User type selection** (Patient, Caregiver, Healthcare Provider)
- **Terms of Service and Privacy Policy** acceptance
- **Automatic login** after successful registration

### ✅ **Secure Login**
- **Email/username authentication** with Django backend
- **Password visibility toggle** for better UX
- **Remember me functionality** with secure token storage
- **Session timeout** with automatic logout
- **Activity monitoring** for security

### ✅ **Password Reset**
- **Two-step password reset process**
- **Email-based reset links** with secure tokens
- **Password strength validation** on reset
- **Automatic redirect** to login after reset

### ✅ **Profile Management**
- **User profile editing** with real-time updates
- **Language preference** settings (English/Afrikaans)
- **Secure profile data** handling
- **Form validation** and error handling

### ✅ **Multi-Factor Authentication (MFA)**
- **TOTP support** for 2FA (Time-based One-Time Password)
- **Recovery codes** for backup access
- **Device trust** management
- **SMS/Email verification** options

### ✅ **Role-Based Access Control**
- **Detailed permission system** with granular controls
- **User type restrictions** for different features
- **Admin panel access** for healthcare providers
- **Patient data protection** with role-based views

### ✅ **Security Features**
- **JWT token authentication** with automatic refresh
- **Encrypted token storage** using Web Crypto API
- **Device fingerprinting** for security tracking
- **Audit logging** for all authentication events
- **Rate limiting** to prevent brute force attacks
- **Session management** with automatic cleanup

## 🏗️ Architecture

### Frontend (Vue 3 + TypeScript)
```
src/
├── components/auth/
│   ├── LoginForm.vue          # Login interface
│   ├── RegisterForm.vue       # Registration form
│   ├── PasswordResetForm.vue  # Password reset
│   └── ProfileForm.vue        # Profile management
├── components/common/
│   └── Navigation.vue         # User navigation
├── composables/
│   └── useAuth.ts            # Authentication composable
├── services/
│   └── authService.ts        # Core auth service
└── router/
    └── index.ts              # Route protection
```

### Backend (Django REST Framework)
```
medguard_backend/
├── users/
│   ├── views.py              # Authentication views
│   ├── urls.py               # Auth endpoints
│   └── models.py             # User model
├── security/
│   ├── views.py              # Security logging
│   └── models.py             # Audit models
└── medguard_notifications/
    └── services.py           # Notification system
```

## 🔧 API Endpoints

### Authentication
- `POST /api/users/auth/login/` - User login
- `POST /api/users/auth/register/` - User registration
- `POST /api/users/auth/logout/` - User logout
- `POST /api/users/auth/refresh/` - Token refresh
- `GET /api/users/auth/validate/` - Token validation

### Password Management
- `POST /api/users/password-reset-request/` - Request password reset
- `POST /api/users/password-reset-confirm/<uidb64>/<token>/` - Confirm reset

### Profile Management
- `GET /api/users/profile/` - Get user profile
- `PUT /api/users/profile/` - Update user profile
- `POST /api/users/auth/change-password/` - Change password

### Security
- `POST /api/security/audit/` - Log security events
- `GET /api/security/dashboard/` - Security dashboard

## 🛡️ Security Implementation

### Token Management
```typescript
// Encrypted token storage using Web Crypto API
private async encryptData(data: string): Promise<string> {
  const encoder = new TextEncoder()
  const dataBuffer = encoder.encode(data)
  
  const key = await crypto.subtle.generateKey(
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  )
  
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const encryptedBuffer = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    dataBuffer
  )
  
  // Combine IV, key, and encrypted data
  return btoa(String.fromCharCode(...combined))
}
```

### Session Management
```typescript
// Automatic session timeout
private setupSessionTimeout(): void {
  const checkSession = () => {
    const timeSinceLastActivity = Date.now() - this.lastActivity.value
    
    if (timeSinceLastActivity > SECURITY_CONFIG.SESSION_TIMEOUT) {
      this.handleSessionTimeout()
    }
  }
  
  this.sessionTimer = window.setInterval(checkSession, 60000)
}
```

### Activity Monitoring
```typescript
// Track user activity for session management
private setupActivityMonitoring(): void {
  const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
  
  events.forEach(event => {
    document.addEventListener(event, () => {
      this.lastActivity.value = Date.now()
    }, true)
  })
}
```

## 🎨 User Interface

### Login Form
- Clean, modern design with healthcare branding
- Password visibility toggle
- Remember me checkbox
- Links to registration and password reset
- Real-time validation and error handling

### Registration Form
- Multi-section form with clear organization
- Password strength indicator
- User type selection
- Terms and privacy policy modals
- Comprehensive validation

### Navigation
- User avatar with initials
- Dropdown menu with profile and logout
- Role-based navigation items
- Responsive design for mobile

## 🔄 State Management

### Authentication Composable
```typescript
export function useAuth() {
  const user = computed(() => authService.currentUser.value)
  const isAuthenticated = computed(() => authService.authenticated.value)
  const isLoading = computed(() => authService.loading.value)
  
  const login = async (credentials: LoginCredentials) => {
    const user = await authService.login(credentials)
    router.push('/dashboard')
    return user
  }
  
  const logout = async (reason?: string) => {
    await authService.logout(reason)
    router.push('/login')
  }
  
  return { user, isAuthenticated, isLoading, login, logout }
}
```

## 🚦 Route Protection

### Navigation Guards
```typescript
router.beforeEach((to, from, next) => {
  const requiresAuth = to.meta.requiresAuth !== false
  
  if (requiresAuth && !authService.authenticated.value) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && authService.authenticated.value) {
    next('/dashboard')
  } else {
    next()
  }
})
```

## 📱 Mobile Responsiveness

All authentication components are fully responsive:
- **Mobile-first design** approach
- **Touch-friendly** interface elements
- **Adaptive layouts** for different screen sizes
- **Optimized navigation** for mobile devices

## 🔍 Testing

### Manual Testing Checklist
- [ ] User registration with all user types
- [ ] Login with valid/invalid credentials
- [ ] Password reset flow (request and confirm)
- [ ] Profile update functionality
- [ ] Session timeout behavior
- [ ] Logout functionality
- [ ] Navigation guards
- [ ] Mobile responsiveness

### Security Testing
- [ ] Token encryption/decryption
- [ ] Session timeout handling
- [ ] Rate limiting
- [ ] XSS protection
- [ ] CSRF protection
- [ ] Input validation

## 🚀 Getting Started

### Frontend Development
```bash
cd medguard-web
npm install
npm run dev
```

### Backend Development
```bash
cd medguard_backend
python manage.py runserver
```

### Environment Setup
Ensure your `.env` file includes:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=MedGuard SA
```

## 📚 Usage Examples

### Using the Auth Composable
```vue
<script setup>
import { useAuth } from '@/composables/useAuth'

const { user, isAuthenticated, login, logout } = useAuth()

const handleLogin = async () => {
  try {
    await login({ email: 'user@example.com', password: 'password' })
  } catch (error) {
    console.error('Login failed:', error)
  }
}
</script>
```

### Checking Permissions
```vue
<template>
  <div v-if="hasPermission('admin_access')">
    Admin Panel
  </div>
</template>

<script setup>
import { useAuth } from '@/composables/useAuth'
const { hasPermission } = useAuth()
</script>
```

## 🔧 Configuration

### Security Settings
```typescript
const SECURITY_CONFIG = {
  ACCESS_TOKEN_EXPIRY: 15 * 60 * 1000, // 15 minutes
  REFRESH_TOKEN_EXPIRY: 7 * 24 * 60 * 60 * 1000, // 7 days
  SESSION_TIMEOUT: 30 * 60 * 1000, // 30 minutes
  PBKDF2_ITERATIONS: 100000,
  SALT_LENGTH: 32
}
```

## 🎯 Future Enhancements

- [ ] **Biometric authentication** (fingerprint/face ID)
- [ ] **Single Sign-On (SSO)** integration
- [ ] **Advanced MFA** with hardware tokens
- [ ] **Audit dashboard** for security monitoring
- [ ] **User activity analytics**
- [ ] **Advanced role management** with custom permissions

## 📞 Support

For questions or issues with the authentication system:
1. Check the Django backend logs for API errors
2. Verify network connectivity between frontend and backend
3. Ensure all environment variables are properly set
4. Check browser console for JavaScript errors

---

**Built with ❤️ for MedGuard SA - Professional Healthcare Management System** 