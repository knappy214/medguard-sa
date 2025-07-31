# Generated manually to add UserProfile table

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_add_user_avatar'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('professional_title', models.CharField(blank=True, max_length=100, verbose_name='Professional Title')),
                ('license_number', models.CharField(blank=True, max_length=50, verbose_name='License Number')),
                ('specialization', models.CharField(blank=True, max_length=100, verbose_name='Specialization')),
                ('facility_name', models.CharField(blank=True, max_length=200, verbose_name='Facility Name')),
                ('facility_address', models.TextField(blank=True, verbose_name='Facility Address')),
                ('facility_phone', models.CharField(blank=True, max_length=20, verbose_name='Facility Phone')),
                ('notification_preferences', models.JSONField(blank=True, default=dict, verbose_name='Notification Preferences')),
                ('privacy_settings', models.JSONField(blank=True, default=dict, verbose_name='Privacy Settings')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='users.user')),
            ],
            options={
                'verbose_name': 'User Profile',
                'verbose_name_plural': 'User Profiles',
                'db_table': 'users_user_profile',
            },
        ),
    ] 