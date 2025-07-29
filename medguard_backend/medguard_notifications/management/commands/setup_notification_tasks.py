"""
Django management command to set up notification system periodic tasks.

This command creates all the necessary periodic tasks for the notification system
including medication reminders, stock alerts, and cleanup tasks.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications.periodic_tasks import (
    create_all_periodic_tasks,
    list_all_tasks,
    reset_task_counters
)


class Command(BaseCommand):
    help = 'Set up periodic tasks for the notification system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset task counters before creating new tasks',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all existing periodic tasks',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of all tasks (will delete existing ones)',
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_tasks()
            return

        if options['reset']:
            self.stdout.write('Resetting task counters...')
            reset_task_counters()
            self.stdout.write(self.style.SUCCESS('Task counters reset successfully!'))

        if options['force']:
            self.stdout.write('Force recreation mode enabled...')
            # Delete existing tasks
            from django_celery_beat.models import PeriodicTask
            deleted_count = PeriodicTask.objects.filter(
                task__startswith='notifications.'
            ).delete()[0]
            self.stdout.write(f'Deleted {deleted_count} existing notification tasks')

        self.stdout.write('Creating periodic tasks for notification system...')
        
        try:
            create_all_periodic_tasks()
            self.stdout.write(
                self.style.SUCCESS('All periodic tasks created successfully!')
            )
            
            # List the created tasks
            self.list_tasks()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating periodic tasks: {str(e)}')
            )

    def list_tasks(self):
        """List all periodic tasks."""
        self.stdout.write('\nCurrent periodic tasks:')
        self.stdout.write('=' * 50)
        
        tasks = list_all_tasks()
        
        if not tasks:
            self.stdout.write('No periodic tasks found.')
            return
        
        for task in tasks:
            status = '✓' if task['enabled'] else '✗'
            self.stdout.write(
                f"{status} {task['name']} ({task['schedule_type']})"
            )
            self.stdout.write(f"    Schedule: {task['schedule']}")
            self.stdout.write(f"    Task: {task['task']}")
            if task['description']:
                self.stdout.write(f"    Description: {task['description']}")
            if task['last_run']:
                self.stdout.write(f"    Last run: {task['last_run']}")
            self.stdout.write(f"    Run count: {task['total_run_count']}")
            self.stdout.write('') 