# MedGuard SA Security Implementation

This document outlines the comprehensive security implementation for MedGuard SA, including authentication, audit logging, and device validation features.

## Overview

The security implementation provides HIPAA-compliant authentication and audit logging with the following key features:

- **JWT Authentication** with device validation
- **Audit Trail System** for comprehensive logging
- **Device Fingerprinting** for enhanced security
- **Rate Limiting** and security monitoring
- **Environment Configuration** for different deployment stages

## API Endpoints

### Authentication Endpoints

#### 1. Login (`POST /api/auth/login/`)

Authenticates users with device validation and security checks.

**Request:**
```json
{
    "username": "user@example.com",
    "password": "secure_password"
}
```

**Headers:**
```
X-Device-Fingerprint: <device_fingerprint> (optional)
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "user@example.com",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "user_type": "patient",
        "preferred_language": "en"
    }
}
```

**Security Features:**
- Device fingerprint validation
- Rate limiting
- Audit logging
- IP address tracking
- Failed login attempt monitoring

#### 2. Token Refresh (`POST /api/auth/refresh/`)

Refreshes access tokens with security validation.

**Request:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Headers:**
```
X-Device-Fingerprint: <device_fingerprint> (optional)
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Security Features:**
- Device fingerprint validation
- Token blacklisting
- Audit logging
- Security event monitoring

#### 3. Logout (`POST /api/auth/logout/`)

Logs out users and blacklists refresh tokens.

**Request:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
    "message": "Successfully logged out"
}
```

**Security Features:**
- Token blacklisting
- Audit logging
- Session cleanup

### Security Logging Endpoints

#### 1. Security Event Logging (`POST /api/security/log/`)

Logs security events for monitoring and compliance.

**Request:**
```json
{
    "event_type": "data_access",
    "description": "User accessed patient medication records",
    "severity": "medium",
    "metadata": {
        "patient_id": 123,
        "medication_count": 5
    }
}
```

**Response:**
```json
{
    "message": "Security event logged successfully"
}
```

#### 2. Security Dashboard (`GET /api/security/dashboard/`)

Provides security metrics and incident overview.

**Query Parameters:**
- `days`: Number of days to analyze (default: 7)

**Response:**
```json
{
    "metrics": {
        "total_events": 1250,
        "failed_logins": 15,
        "access_denied": 8,
        "security_events": 23,
        "suspicious_ips": 3
    },
    "recent_incidents": [...],
    "suspicious_ips": [...],
    "date_range": {
        "start_date": "2024-01-01T00:00:00Z",
        "end_date": "2024-01-08T00:00:00Z",
        "days": 7
    }
}
```

#### 3. Audit Logs (`GET /api/security/audit-logs/`)

Retrieves audit logs with filtering and search capabilities.

**Query Parameters:**
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)
- `user_id`: Filter by user ID
- `action_type`: Filter by action type
- `severity`: Filter by severity level
- `ip_address`: Filter by IP address
- `search`: Search in description and object representation
- `ordering`: Sort order (e.g., `-timestamp`)

**Response:**
```json
{
    "count": 1250,
    "next": "http://localhost:8000/api/security/audit-logs/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": {
                "id": 1,
                "username": "user@example.com",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "user_type": "patient"
            },
            "action": "login",
            "action_display": "Login",
            "severity": "low",
            "severity_display": "Low",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0...",
            "description": "Successful login for user: user@example.com",
            "timestamp": "2024-01-08T10:30:00Z",
            "metadata": {
                "device_fingerprint": "abc123...",
                "ip_address": "192.168.1.100"
            }
        }
    ]
}
```

#### 4. Audit Log Summary (`GET /api/security/audit-logs/summary/`)

Provides summary statistics for audit logs.

**Query Parameters:**
- `days`: Number of days to analyze (default: 30)

**Response:**
```json
{
    "total_actions": 1250,
    "actions_by_type": [
        {"action": "login", "count": 450},
        {"action": "data_access", "count": 300},
        {"action": "data_modification", "count": 200}
    ],
    "actions_by_severity": [
        {"severity": "low", "count": 1000},
        {"severity": "medium", "count": 200},
        {"severity": "high", "count": 50}
    ],
    "top_users": [
        {"user__username": "admin", "count": 100},
        {"user__username": "user@example.com", "count": 50}
    ],
    "recent_security_events": [...],
    "date_range": {
        "start_date": "2023-12-09T00:00:00Z",
        "end_date": "2024-01-08T00:00:00Z",
        "days": 30
    }
}
```

#### 5. Audit Log Export (`GET /api/security/audit-logs/export/`)

Exports audit logs to CSV format.

**Query Parameters:**
- Same as audit logs endpoint

**Response:**
- CSV file download

## Device Fingerprinting

### Overview

Device fingerprinting enhances security by creating unique identifiers for devices based on various request characteristics.

### Implementation

The device fingerprinting system:

1. **Generates fingerprints** from:
   - User agent string
   - IP address
   - Accept language headers
   - Accept encoding headers
   - Custom device fingerprint headers

2. **Validates fingerprints** during:
   - Login attempts
   - Token refresh operations
   - API requests

3. **Analyzes risk** based on:
   - Fingerprint mismatches
   - Suspicious IP addresses
   - Suspicious user agents

### Usage

#### Client-Side Implementation

```javascript
// Generate device fingerprint
function generateDeviceFingerprint() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Device fingerprint', 2, 2);
    
    const fingerprint = {
        userAgent: navigator.userAgent,
        language: navigator.language,
        platform: navigator.platform,
        screenResolution: `${screen.width}x${screen.height}`,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        canvas: canvas.toDataURL()
    };
    
    return btoa(JSON.stringify(fingerprint));
}

// Include in API requests
const headers = {
    'Content-Type': 'application/json',
    'X-Device-Fingerprint': generateDeviceFingerprint()
};
```

#### Server-Side Validation

```python
from security.device_fingerprinting import validate_device_fingerprint

# Validate device fingerprint
is_valid = validate_device_fingerprint(request, stored_fingerprint)
if not is_valid:
    # Log security event
    log_audit_event(
        user=request.user,
        action='device_fingerprint_mismatch',
        description='Device fingerprint validation failed',
        severity='high',
        request=request
    )
```

## Environment Configuration

### Environment Variables

The system uses environment variables for configuration:

```bash
# Environment
ENVIRONMENT=production  # development, staging, production

# API Configuration
API_BASE_URL=https://api.medguard-sa.com
API_VERSION=v1

# Security Settings
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=604800
JWT_ROTATE_REFRESH_TOKENS=True
JWT_BLACKLIST_AFTER_ROTATION=True
DEVICE_FINGERPRINTING_ENABLED=True
RATE_LIMIT_ENABLED=True
AUDIT_LOGGING_ENABLED=True

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=medguard_sa_prod
DB_USER=medguard_user
DB_PASSWORD=secure_password

# Redis
REDIS_URL=redis://localhost:6379/1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@medguard-sa.com
EMAIL_HOST_PASSWORD=secure_password

# CORS
FRONTEND_URL=https://medguard-sa.com
MOBILE_APP_URL=https://app.medguard-sa.com
```

### Environment-Specific Settings

#### Development
- Debug mode enabled
- Console email backend
- Local database and Redis
- Debug toolbar enabled

#### Staging
- Production-like settings
- Staging database and services
- Email notifications enabled
- Security headers enabled

#### Production
- Debug mode disabled
- Production database and services
- SSL/HTTPS required
- Enhanced security headers
- Comprehensive logging

## Security Features

### 1. JWT Authentication

- **Access Token Lifetime**: 1 hour (configurable)
- **Refresh Token Lifetime**: 7 days (configurable)
- **Token Rotation**: Enabled
- **Token Blacklisting**: Enabled
- **Device Validation**: Integrated

### 2. Rate Limiting

- **Anonymous Users**: 100 requests/minute
- **Authenticated Users**: 1000 requests/hour
- **Configurable**: Per environment

### 3. Audit Logging

- **Comprehensive Tracking**: All user actions
- **HIPAA Compliance**: 7-year retention
- **Encryption**: Optional
- **Export Capability**: CSV format
- **Real-time Monitoring**: Dashboard

### 4. Device Fingerprinting

- **Multi-factor Identification**: User agent, IP, headers
- **Risk Analysis**: Suspicious pattern detection
- **Cache Storage**: Redis-based
- **Validation**: Real-time checking

### 5. Security Monitoring

- **Real-time Alerts**: High-severity events
- **Dashboard**: Security metrics
- **Incident Tracking**: Security events
- **IP Analysis**: Suspicious activity detection

## Database Schema

### AuditLog Model

```python
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL)
    action = models.CharField(max_length=50, choices=ActionType.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField(default=dict)
    previous_values = models.JSONField(default=dict)
    new_values = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    request_path = models.CharField(max_length=500)
    request_method = models.CharField(max_length=10)
    session_id = models.CharField(max_length=100)
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    retention_date = models.DateTimeField()
    is_anonymized = models.BooleanField(default=False)
```

### SecurityEvent Model

```python
class SecurityEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL)
    event_type = models.CharField(max_length=50, choices=EventType.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    description = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    request_path = models.CharField(max_length=500)
    request_method = models.CharField(max_length=10)
    metadata = models.JSONField(default=dict)
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField()
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL)
    resolved_at = models.DateTimeField()
    timestamp = models.DateTimeField(auto_now_add=True)
```

## Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run security tests specifically
python manage.py test security.tests

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Coverage

The security implementation includes comprehensive tests for:

- Authentication endpoints
- Device fingerprinting
- Audit logging
- Security event handling
- Rate limiting
- Token validation

## Deployment

### Prerequisites

1. **Database**: PostgreSQL with SSL support
2. **Cache**: Redis for session and token storage
3. **Email**: SMTP server for notifications
4. **SSL Certificate**: For HTTPS in production

### Deployment Steps

1. **Environment Setup**:
   ```bash
   export ENVIRONMENT=production
   export SECRET_KEY=your-secret-key
   export DB_PASSWORD=your-db-password
   ```

2. **Database Migration**:
   ```bash
   python manage.py migrate
   ```

3. **Static Files**:
   ```bash
   python manage.py collectstatic
   ```

4. **Create Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

5. **Start Services**:
   ```bash
   # Start Redis
   redis-server
   
   # Start Celery (if using)
   celery -A medguard_backend worker -l info
   
   # Start Django
   python manage.py runserver
   ```

## Monitoring and Maintenance

### Log Monitoring

Monitor the following log files:

- `/var/log/medguard-sa/django.log` - General application logs
- `/var/log/medguard-sa/security.log` - Security-specific logs

### Regular Maintenance

1. **Audit Log Cleanup**: Automatic cleanup after retention period
2. **Token Blacklist Cleanup**: Regular cleanup of expired tokens
3. **Security Event Review**: Regular review of security events
4. **Database Maintenance**: Regular backups and optimization

### Security Alerts

The system generates alerts for:

- Failed login attempts (multiple)
- Device fingerprint mismatches
- High-severity security events
- Suspicious IP addresses
- Rate limit violations

## Compliance

### HIPAA Compliance

The implementation includes:

- **Audit Trails**: Comprehensive logging of all access
- **Access Controls**: Role-based permissions
- **Data Encryption**: At rest and in transit
- **Session Management**: Secure session handling
- **Incident Response**: Security event monitoring

### POPIA Compliance

Additional features for South African POPIA:

- **Data Subject Rights**: Access and deletion capabilities
- **Data Minimization**: Minimal data collection
- **Purpose Limitation**: Clear data usage purposes
- **Security Safeguards**: Comprehensive security measures

## Support

For technical support or security concerns:

1. **Documentation**: Check this document and inline code comments
2. **Logs**: Review application and security logs
3. **Monitoring**: Use the security dashboard for insights
4. **Testing**: Run comprehensive test suites

## Changelog

### Version 1.0.0 (Current)
- Initial security implementation
- JWT authentication with device validation
- Comprehensive audit logging
- Security monitoring dashboard
- Environment-specific configuration
- HIPAA and POPIA compliance features 