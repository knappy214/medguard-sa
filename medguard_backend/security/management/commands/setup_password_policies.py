"""
Django management command to set up default password policies.

This command creates default password policies for different user types
in the MedGuard SA healthcare system.
"""

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from security.password_policies import PasswordPolicy


class Command(BaseCommand):
    help = 'Set up default password policies for MedGuard SA'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing policies',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up default password policies...')
        )

        policies = [
            {
                'policy_type': PasswordPolicy.PolicyType.PATIENT,
                'name': 'Patient Password Policy',
                'description': 'Standard password policy for patient accounts',
                'min_length': 8,
                'require_uppercase': True,
                'require_lowercase': True,
                'require_digits': True,
                'require_special_chars': False,
                'prevent_reuse_count': 3,
                'max_age_days': 180,
                'max_failed_attempts': 5,
                'lockout_duration_minutes': 30,
                'require_2fa': False,
                'require_2fa_for_admin': False,
                'hipaa_compliant': True,
            },
            {
                'policy_type': PasswordPolicy.PolicyType.CAREGIVER,
                'name': 'Caregiver Password Policy',
                'description': 'Enhanced password policy for caregiver accounts',
                'min_length': 10,
                'require_uppercase': True,
                'require_lowercase': True,
                'require_digits': True,
                'require_special_chars': True,
                'prevent_reuse_count': 5,
                'max_age_days': 120,
                'max_failed_attempts': 5,
                'lockout_duration_minutes': 30,
                'require_2fa': True,
                'require_2fa_for_admin': True,
                'hipaa_compliant': True,
            },
            {
                'policy_type': PasswordPolicy.PolicyType.HEALTHCARE_PROVIDER,
                'name': 'Healthcare Provider Password Policy',
                'description': 'Strict password policy for healthcare providers',
                'min_length': 12,
                'require_uppercase': True,
                'require_lowercase': True,
                'require_digits': True,
                'require_special_chars': True,
                'prevent_reuse_count': 8,
                'max_age_days': 90,
                'max_failed_attempts': 3,
                'lockout_duration_minutes': 60,
                'require_2fa': True,
                'require_2fa_for_admin': True,
                'hipaa_compliant': True,
            },
            {
                'policy_type': PasswordPolicy.PolicyType.ADMINISTRATOR,
                'name': 'Administrator Password Policy',
                'description': 'Administrative password policy for staff accounts',
                'min_length': 12,
                'require_uppercase': True,
                'require_lowercase': True,
                'require_digits': True,
                'require_special_chars': True,
                'prevent_reuse_count': 10,
                'max_age_days': 60,
                'max_failed_attempts': 3,
                'lockout_duration_minutes': 120,
                'require_2fa': True,
                'require_2fa_for_admin': True,
                'hipaa_compliant': True,
            },
            {
                'policy_type': PasswordPolicy.PolicyType.SYSTEM_ADMIN,
                'name': 'System Administrator Password Policy',
                'description': 'Maximum security policy for system administrators',
                'min_length': 16,
                'require_uppercase': True,
                'require_lowercase': True,
                'require_digits': True,
                'require_special_chars': True,
                'prevent_reuse_count': 15,
                'max_age_days': 30,
                'max_failed_attempts': 2,
                'lockout_duration_minutes': 240,
                'require_2fa': True,
                'require_2fa_for_admin': True,
                'hipaa_compliant': True,
            },
        ]

        created_count = 0
        updated_count = 0

        for policy_data in policies:
            policy_type = policy_data.pop('policy_type')
            
            if options['force']:
                # Delete existing policy if force option is used
                PasswordPolicy.objects.filter(policy_type=policy_type).delete()
                policy, created = PasswordPolicy.objects.get_or_create(
                    policy_type=policy_type,
                    defaults=policy_data
                )
            else:
                # Update existing policy or create new one
                policy, created = PasswordPolicy.objects.get_or_create(
                    policy_type=policy_type,
                    defaults=policy_data
                )
                
                if not created:
                    # Update existing policy
                    for key, value in policy_data.items():
                        setattr(policy, key, value)
                    policy.save()
                    updated_count += 1
                    self.stdout.write(
                        f'Updated policy: {policy.name}'
                    )
                else:
                    created_count += 1
                    self.stdout.write(
                        f'Created policy: {policy.name}'
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up password policies. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )

        # Display summary
        self.stdout.write('\nPassword Policy Summary:')
        self.stdout.write('=' * 50)
        
        for policy in PasswordPolicy.objects.all().order_by('policy_type'):
            self.stdout.write(f'\n{policy.name}:')
            self.stdout.write(f'  Type: {policy.get_policy_type_display()}')
            self.stdout.write(f'  Min Length: {policy.min_length}')
            self.stdout.write(f'  Require Special Chars: {policy.require_special_chars}')
            self.stdout.write(f'  Require 2FA: {policy.require_2fa}')
            self.stdout.write(f'  Max Age: {policy.max_age_days} days')
            self.stdout.write(f'  HIPAA Compliant: {policy.hipaa_compliant}') 