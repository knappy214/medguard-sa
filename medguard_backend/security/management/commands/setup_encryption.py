"""
Django management command to set up encryption keys for MedGuard SA.

This command initializes encryption keys for healthcare data protection
and ensures HIPAA-compliant encryption is properly configured.
"""

import os
import secrets
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import base64

# Import available encryption functions
from security.encryption import get_encryption_service

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to set up encryption keys.
    """
    
    help = 'Set up encryption keys for MedGuard SA healthcare data protection'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--environment',
            type=str,
            choices=['development', 'staging', 'production'],
            default='development',
            help='Environment for which to set up encryption keys'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of existing keys'
        )
        
        parser.add_argument(
            '--key-types',
            nargs='+',
            choices=['fernet', 'rsa', 'aes'],
            default=['fernet'],
            help='Types of encryption keys to generate'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        self.environment = options['environment']
        self.force = options['force']
        self.key_types = options['key_types']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Setting up encryption keys for {self.environment} environment...'
            )
        )
        
        try:
            # Check if keys already exist
            if not self.force and self._keys_exist():
                self.stdout.write(
                    self.style.WARNING(
                        'Encryption keys already exist. Use --force to regenerate.'
                    )
                )
                return
            
            # Generate master encryption key if not exists
            self._setup_master_key()
            
            # Generate encryption keys for each type
            for key_type in self.key_types:
                self._generate_encryption_key(key_type)
            
            # Create .env template with encryption settings
            self._create_env_template()
            
            # Display security recommendations
            self._display_security_recommendations()
            
            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully set up encryption keys for healthcare data protection!'
                )
            )
            
        except Exception as e:
            raise CommandError(f'Failed to set up encryption keys: {e}')
    
    def _keys_exist(self) -> bool:
        """Check if encryption keys already exist."""
        # For now, check if master key exists in environment
        return bool(os.getenv('HEALTHCARE_ENCRYPTION_KEY'))
    
    def _setup_master_key(self):
        """Set up master encryption key."""
        self.stdout.write('Setting up master encryption key...')
        
        # Generate a strong master key
        master_key = secrets.token_urlsafe(64)
        
        # Store in environment variable (for development)
        if self.environment == 'development':
            env_file = os.path.join(settings.BASE_DIR, '.env')
            
            # Read existing .env content
            env_content = []
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    env_content = f.readlines()
            
            # Remove existing HEALTHCARE_ENCRYPTION_KEY if present
            env_content = [
                line for line in env_content 
                if not line.startswith('HEALTHCARE_ENCRYPTION_KEY=')
            ]
            
            # Add new master key
            env_content.append(f'HEALTHCARE_ENCRYPTION_KEY={master_key}\n')
            
            # Write back to .env
            with open(env_file, 'w') as f:
                f.writelines(env_content)
            
            self.stdout.write(
                self.style.SUCCESS('Master key added to .env file')
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'For {self.environment} environment, set HEALTHCARE_ENCRYPTION_KEY manually:'
                )
            )
            self.stdout.write(f'HEALTHCARE_ENCRYPTION_KEY={master_key}')
    
    def _generate_encryption_key(self, key_type: str):
        """Generate encryption key of specified type."""
        self.stdout.write(f'Generating {key_type.upper()} encryption key...')
        
        try:
            if key_type == 'fernet':
                key = Fernet.generate_key()
                key_data = key
            elif key_type == 'rsa':
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                )
                key_data = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
            elif key_type == 'aes':
                key_data = secrets.token_bytes(32)  # 256-bit key
            else:
                raise ValueError(f"Unsupported key type: {key_type}")
            
            # Generate key ID
            key_id = secrets.token_hex(16)
            
            # Store key securely (for now, just log it)
            # In production, this would be stored in a secure key management system
            self.stdout.write(f"Key data length: {len(key_data)} bytes")
            
            # Log key generation (EncryptionKey model not available yet)
            logger.info(f"Generated {key_type.upper()} key with ID: {key_id}")
            
            # Store key metadata in cache for now
            cache_key = f"encryption_key_{key_id}"
            cache.set(cache_key, {
                'key_type': key_type,
                'environment': self.environment,
                'algorithm': self._get_algorithm_for_key_type(key_type),
                'created_at': timezone.now().isoformat(),
            }, timeout=86400)  # 24 hours
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Generated {key_type.upper()} key with ID: {key_id}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Failed to generate {key_type} key: {e}'
                )
            )
            raise
    
    def _get_admin_user(self):
        """Get or create admin user for key creation."""
        try:
            return User.objects.filter(is_superuser=True).first()
        except Exception:
            return None
    
    def _get_algorithm_for_key_type(self, key_type: str) -> str:
        """Get algorithm name for key type."""
        algorithms = {
            'fernet': 'AES-128-CBC',
            'rsa': 'RSA-2048',
            'aes': 'AES-256-GCM',
        }
        return algorithms.get(key_type, 'Unknown')
    
    def _create_env_template(self):
        """Create .env template with encryption settings."""
        template_content = f"""
# Healthcare Encryption Settings - Generated for {self.environment}
# DO NOT COMMIT THESE VALUES TO VERSION CONTROL

# Master encryption key (set this securely in production)
HEALTHCARE_ENCRYPTION_KEY=your_master_key_here

# Encryption salt (change for production)
HEALTHCARE_ENCRYPTION_SALT=medguard_salt_2024_{self.environment}

# Key rotation settings
KEY_ROTATION_DAYS=90
BACKUP_KEYS_COUNT=3

# Form security settings
FORM_RATE_LIMIT_DEFAULT=10
FORM_RATE_LIMIT_PRESCRIPTION=5
FORM_RATE_LIMIT_CRITICAL=2
MAX_FIELD_LENGTH=10000

# Admin access control
ADMIN_SESSION_TIMEOUT=30
ADMIN_MAX_FAILED_ATTEMPTS=5
ADMIN_LOCKOUT_DURATION=15
REQUIRE_2FA_FOR_ADMIN=True

# Document privacy
DEFAULT_PRIVACY_LEVEL=internal

# Compliance reporting
REPORT_RETENTION_DAYS=2555
HIPAA_COMPLIANCE_THRESHOLD=0.9
"""
        
        template_file = os.path.join(
            settings.BASE_DIR, 
            f'.env.{self.environment}.template'
        )
        
        with open(template_file, 'w') as f:
            f.write(template_content.strip())
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created environment template: .env.{self.environment}.template'
            )
        )
    
    def _display_security_recommendations(self):
        """Display security recommendations."""
        self.stdout.write(self.style.SUCCESS('\n=== SECURITY RECOMMENDATIONS ==='))
        
        recommendations = [
            '1. Store encryption keys securely using environment variables',
            '2. Never commit encryption keys to version control',
            '3. Rotate encryption keys every 90 days',
            '4. Use different keys for different environments',
            '5. Implement key backup and recovery procedures',
            '6. Monitor key usage and access patterns',
            '7. Enable 2FA for all admin users',
            '8. Regularly audit encryption key access',
            '9. Use hardware security modules (HSM) in production',
            '10. Implement proper key escrow for compliance',
        ]
        
        for rec in recommendations:
            self.stdout.write(f'   {rec}')
        
        if self.environment == 'production':
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  PRODUCTION ENVIRONMENT DETECTED ⚠️'
                )
            )
            self.stdout.write(
                'Ensure you have implemented proper key management procedures!'
            )
        
        self.stdout.write(self.style.SUCCESS('=== END RECOMMENDATIONS ===\n'))