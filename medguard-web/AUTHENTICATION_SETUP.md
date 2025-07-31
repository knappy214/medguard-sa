# MedGuard SA Authentication Setup

This document provides instructions for setting up and testing the authentication system between the Vue.js frontend and Django backend.

## Prerequisites

1. **Backend Setup**: Ensure the Django backend is running on `http://localhost:8000`
2. **Database**: PostgreSQL database should be configured and running
3. **Dependencies**: All Python and Node.js dependencies should be installed

## Backend Setup

### 1. Start the Django Backend

```bash
cd medguard_backend
python manage.py runserver
```

### 2. Create Test User

Run the management command to create a test user:

```bash
cd medguard_backend
python manage.py create_test_user --username testuser --email test@medguard-sa.com --password test123 --user-type PATIENT
```

### 3. Test Backend API

Run the authentication test script to verify the backend is working:

```bash
cd medguard_backend
python test_auth_api.py
```

This will test all authentication endpoints:
- `/api/test/` - Basic connectivity test
- `/api/users/auth/login/` - User login
- `/api/users/auth/validate/` - Token validation
- `/api/users/auth/refresh/` - Token refresh
- `/api/users/auth/logout/` - User logout

## Frontend Setup

### 1. Install Dependencies

```bash
cd medguard-web
npm install
```

### 2. Start the Development Server

```bash
cd medguard-web
npm run dev
```

The frontend will be available at `http://localhost:5173` with a proxy configured to forward API requests to the backend.

## Testing the Authentication Flow

### 1. Access the Application

1. Open your browser and navigate to `http://localhost:5173`
2. You should be redirected to the login page (`/login`)

### 2. Login with Test Credentials

Use the following credentials:
- **Email**: `testuser` (or `test@medguard-sa.com`)
- **Password**: `test123`

### 3. Verify Authentication

After successful login, you should:
1. Be redirected to the dashboard (`/dashboard`)
2. See your user information displayed
3. See your permissions listed
4. See security information including device ID and session timeout

### 4. Test Logout

1. Click the "Logout" button in the dashboard
2. You should be redirected back to the login page
3. Try accessing `/dashboard` directly - you should be redirected to login

## API Endpoints

The following authentication endpoints are available:

### Login
- **URL**: `POST /api/users/auth/login/`
- **Body**: `{ "username": "testuser", "password": "test123" }`
- **Response**: JWT tokens and user information

### Token Validation
- **URL**: `GET /api/users/auth/validate/`
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: Current user information

### Token Refresh
- **URL**: `POST /api/users/auth/refresh/`
- **Body**: `{ "refresh": "<refresh_token>" }`
- **Response**: New access token

### Logout
- **URL**: `POST /api/users/auth/logout/`
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: Success message

## Security Features

The authentication system includes several HIPAA-compliant security features:

1. **JWT Tokens**: Secure token-based authentication
2. **Token Blacklisting**: Secure logout with token revocation
3. **Device Fingerprinting**: Device-specific token validation
4. **IP Address Validation**: Token binding to client IP addresses
5. **Rate Limiting**: Protection against brute force attacks
6. **Audit Logging**: Comprehensive security event tracking
7. **Session Timeout**: Automatic logout after inactivity
8. **Encrypted Storage**: Secure token storage using Web Crypto API

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure the backend CORS settings include `http://localhost:5173`
2. **Database Connection**: Verify PostgreSQL is running and accessible
3. **Token Issues**: Check browser console for token-related errors
4. **Proxy Issues**: Verify the Vite proxy configuration is correct

### Debug Steps

1. Check browser developer tools for network requests
2. Verify backend logs for authentication attempts
3. Test API endpoints directly using curl or Postman
4. Check browser console for JavaScript errors

## Development Notes

- The frontend uses Vue 3 with Composition API
- Authentication state is managed using Vue's reactive system
- Tokens are stored securely using browser's Web Crypto API
- The system supports both English and Afrikaans localization
- All UI text is internationalized and accessible

## Next Steps

Once authentication is working, you can:

1. Add more user types (CAREGIVER, HEALTHCARE_PROVIDER)
2. Implement role-based access control
3. Add multi-factor authentication
4. Integrate with medication management features
5. Add user profile management
6. Implement password reset functionality 