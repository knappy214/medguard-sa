"""
Django management command to rotate encryption keys for MedGuard SA.

This command rotates encryption keys according to HIPAA compliance
requirements and healthcare security best practices.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from security.patient_encryption import EncryptionKey
from security.audit import log_security_event

User = get_user_model()


class Command(BaseCommand):
    """
    Management command to rotate encryption keys.
    """
    
    help = 'Rotate encryption keys for HIPAA compliance'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--key-type',
            type=str,
            choices=['fernet', 'rsa', 'aes', 'all'],
            default='all',
            help='Type of keys to rotate'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force rotation even if keys are not due for rotation'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be rotated without actually rotating'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        self.key_type = options['key_type']
        self.force = options['force']
        self.dry_run = options['dry_run']
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No keys will actually be rotated')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Starting key rotation process...')
        )
        
        try:
            if self.key_type == 'all':
                key_types = ['fernet', 'rsa', 'aes']
            else:
                key_types = [self.key_type]
            
            total_rotated = 0
            
            for kt in key_types:
                rotated = self._rotate_keys_by_type(kt)
                total_rotated += rotated
            
            if self.dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'DRY RUN: Would rotate {total_rotated} keys'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully rotated {total_rotated} encryption keys!'
                    )
                )
            
        except Exception as e:
            raise CommandError(f'Failed to rotate keys: {e}')
    
    def _rotate_keys_by_type(self, key_type: str) -> int:
        """Rotate keys of specified type."""
        self.stdout.write(f'Checking {key_type.upper()} keys for rotation...')
        
        # Get keys that need rotation
        keys_to_rotate = self._get_keys_needing_rotation(key_type)
        
        if not keys_to_rotate:
            self.stdout.write(f'No {key_type} keys need rotation')
            return 0
        
        rotated_count = 0
        
        for key in keys_to_rotate:
            if self._should_rotate_key(key):
                if not self.dry_run:
                    self._rotate_single_key(key)
                
                self.stdout.write(
                    f'{"Would rotate" if self.dry_run else "Rotated"} '
                    f'{key_type} key: {key.key_id}'
                )
                rotated_count += 1
        
        return rotated_count
    
    def _get_keys_needing_rotation(self, key_type: str):
        """Get keys that need rotation."""
        # Keys older than 90 days (configurable)
        rotation_threshold = timezone.now() - timedelta(days=90)
        
        keys = EncryptionKey.objects.filter(
            key_type=key_type,
            is_active=True
        )
        
        if not self.force:
            keys = keys.filter(created_at__lt=rotation_threshold)
        
        return keys
    
    def _should_rotate_key(self, key) -> bool:
        """Check if a key should be rotated."""
        if self.force:
            return True
        
        # Check age
        age_threshold = timezone.now() - timedelta(days=90)
        if key.created_at < age_threshold:
            return True
        
        # Check if key is expired
        if key.expires_at and key.expires_at < timezone.now():
            return True
        
        return False
    
    def _rotate_single_key(self, old_key):
        """Rotate a single encryption key."""
        try:
            # Generate new key
            new_key_id = EncryptionKey.objects.generate_key(old_key.key_type)
            
            # Mark old key as inactive
            old_key.is_active = False
            old_key.save()
            
            # Log the rotation
            admin_user = self._get_admin_user()
            log_security_event(
                user=admin_user,
                event_type='key_rotation',
                details={
                    'old_key_id': old_key.key_id,
                    'new_key_id': new_key_id,
                    'key_type': old_key.key_type,
                    'rotation_reason': 'scheduled_rotation'
                }
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Failed to rotate key {old_key.key_id}: {e}'
                )
            )
            raise
    
    def _get_admin_user(self):
        """Get admin user for logging."""
        try:
            return User.objects.filter(is_superuser=True).first()
        except Exception:
            return None