"""
Django management command to create a test user for authentication testing.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a test user for authentication testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='testuser',
            help='Username for the test user'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='test@medguard-sa.com',
            help='Email for the test user'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='test123',
            help='Password for the test user'
        )
        parser.add_argument(
            '--user-type',
            type=str,
            choices=['patient', 'caregiver', 'healthcare_provider'],
            default='patient',
            help='User type for the test user'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
                        user_type = options['user_type'].lower()

        try:
            with transaction.atomic():
                # Check if user already exists
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'user_type': user_type,
                        'is_active': True,
                        'first_name': 'Test',
                        'last_name': 'User',
                        'preferred_language': 'en'
                    }
                )

                if created:
                    # Set password for new user
                    user.set_password(password)
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully created test user: {username}'
                        )
                    )
                else:
                    # Update password for existing user
                    user.set_password(password)
                    user.is_active = True
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully updated test user: {username}'
                        )
                    )

                self.stdout.write(f'Username: {username}')
                self.stdout.write(f'Email: {email}')
                self.stdout.write(f'Password: {password}')
                self.stdout.write(f'User Type: {user_type}')
                self.stdout.write(f'Is Active: {user.is_active}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create test user: {e}')
            ) 