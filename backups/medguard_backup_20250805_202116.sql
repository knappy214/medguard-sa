-- Schema-only backup created by MedGuard SA Migration Script
-- Created at: 2025-08-05 20:21:18.261584
-- This is a minimal backup containing only table schemas

# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuditLogs(models.Model):
    id = models.BigAutoField(primary_key=True)
    action = models.CharField(max_length=50)
    severity = models.CharField(max_length=20)
    object_id = models.IntegerField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField()
    previous_values = models.JSONField()
    new_values = models.JSONField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField()
    request_path = models.CharField(max_length=500)
    request_method = models.CharField(max_length=10)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    metadata = models.JSONField()
    timestamp = models.DateTimeField()
    retention_date = models.DateTimeField(blank=True, null=True)
    is_anonymized = models.BooleanField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'audit_logs'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class DjangoSite(models.Model):
    domain = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'django_site'


class HomeHomepage(models.Model):
    page_ptr = models.OneToOneField('WagtailcorePage', models.DO_NOTHING, primary_key=True)
    hero_title = models.CharField(max_length=200)
    hero_subtitle = models.CharField(max_length=500)
    hero_content = models.TextField()
    main_content = models.TextField()
    cta_title = models.CharField(max_length=200)
    cta_content = models.TextField()
    meta_description = models.CharField(max_length=160)

    class Meta:
        managed = False
        db_table = 'home_homepage'


class Icd10Codes(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(unique=True, max_length=20)
    description = models.TextField()
    category = models.CharField(max_length=20)
    is_active = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'icd10_codes'


class ImageProcessingJobs(models.Model):
    id = models.BigAutoField(primary_key=True)
    job_id = models.CharField(unique=True, max_length=100)
    job_type = models.CharField(max_length=20)
    job_status = models.CharField(max_length=20)
    job_priority = models.CharField(max_length=10)
    job_parameters = models.JSONField()
    job_result = models.JSONField()
    job_errors = models.JSONField()
    job_warnings = models.JSONField()
    job_progress = models.FloatField()
    job_started_at = models.DateTimeField(blank=True, null=True)
    job_completed_at = models.DateTimeField(blank=True, null=True)
    job_duration_seconds = models.IntegerField(blank=True, null=True)
    worker_node = models.CharField(max_length=100)
    retry_count = models.IntegerField()
    max_retries = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    prescription_image = models.ForeignKey('PrescriptionImages', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'image_processing_jobs'


class InteractionAlerts(models.Model):
    id = models.BigAutoField(primary_key=True)
    alert_type = models.CharField(max_length=20)
    alert_priority = models.CharField(max_length=20)
    alert_status = models.CharField(max_length=20)
    alert_title = models.CharField(max_length=200)
    alert_message = models.TextField()
    alert_data = models.JSONField()
    alert_date = models.DateTimeField()
    acknowledged_by = models.CharField(max_length=200)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.CharField(max_length=200)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolution_notes = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    patient = models.ForeignKey('PrescriptionPatients', models.DO_NOTHING, blank=True, null=True)
    interaction = models.ForeignKey('MedicationInteractions', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'interaction_alerts'


class InteractionChecks(models.Model):
    id = models.BigAutoField(primary_key=True)
    check_type = models.CharField(max_length=20)
    check_status = models.CharField(max_length=20)
    check_date = models.DateTimeField()
    checked_by = models.CharField(max_length=200)
    medications_checked = models.JSONField()
    interactions_found = models.IntegerField()
    critical_interactions = models.IntegerField()
    major_interactions = models.IntegerField()
    moderate_interactions = models.IntegerField()
    minor_interactions = models.IntegerField()
    check_notes = models.TextField()
    check_duration_seconds = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    patient = models.ForeignKey('PrescriptionPatients', models.DO_NOTHING, blank=True, null=True)
    prescription = models.ForeignKey('Prescriptions', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'interaction_checks'


class MedguardNotificationTemplates(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    variables = models.JSONField()
    is_active = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'medguard_notification_templates'


class MedguardNotifications(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    notification_type = models.CharField(max_length=20)
    priority = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    target_user_types = models.JSONField()
    scheduled_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField()
    show_on_dashboard = models.BooleanField()
    require_acknowledgment = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'medguard_notifications'


class MedguardNotificationsNotificationdetailpage(models.Model):
    page_ptr = models.OneToOneField('WagtailcorePage', models.DO_NOTHING, primary_key=True)
    additional_info = models.TextField()
    notification = models.OneToOneField(MedguardNotifications, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'medguard_notifications_notificationdetailpage'


class MedguardNotificationsNotificationindexpage(models.Model):
    page_ptr = models.OneToOneField('WagtailcorePage', models.DO_NOTHING, primary_key=True)
    intro = models.TextField()

    class Meta:
        managed = False
        db_table = 'medguard_notifications_notificationindexpage'


class MedguardNotificationsTargetUsers(models.Model):
    id = models.BigAutoField(primary_key=True)
    notification = models.ForeignKey(MedguardNotifications, models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'medguard_notifications_target_users'
        unique_together = (('notification', 'user'),)


class MedguardUserNotificationPreferences(models.Model):
    id = models.BigAutoField(primary_key=True)
    email_notifications_enabled = models.BooleanField()
    email_time_preference = models.CharField(max_length=20)
    email_custom_time = models.TimeField(blank=True, null=True)
    sms_notifications_enabled = models.BooleanField()
    sms_phone_number = models.CharField(max_length=20)
    sms_time_preference = models.CharField(max_length=20)
    push_notifications_enabled = models.BooleanField()
    push_device_token = models.CharField(max_length=255)
    in_app_notifications_enabled = models.BooleanField()
    medication_reminders_enabled = models.BooleanField()
    stock_alerts_enabled = models.BooleanField()
    system_notifications_enabled = models.BooleanField()
    quiet_hours_enabled = models.BooleanField()
    quiet_hours_start = models.TimeField(blank=True, null=True)
    quiet_hours_end = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    user = models.OneToOneField('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'medguard_user_notification_preferences'


class MedguardUserNotifications(models.Model):
    id = models.BigAutoField(primary_key=True)
    status = models.CharField(max_length=20)
    sent_at = models.DateTimeField()
    read_at = models.DateTimeField(blank=True, null=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    dismissed_at = models.DateTimeField(blank=True, null=True)
    notification = models.ForeignKey(MedguardNotifications, models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'medguard_user_notifications'
        unique_together = (('user', 'notification'),)


class MedicationInteractions(models.Model):
    id = models.BigAutoField(primary_key=True)
    interaction_type = models.CharField(max_length=20)
    severity_level = models.CharField(max_length=20)
    interaction_description = models.TextField()
    mechanism = models.TextField()
    clinical_effects = models.TextField()
    management = models.TextField()
    evidence_level = models.CharField(max_length=20)
    references = models.JSONField()
    is_active = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    medication1 = models.ForeignKey('Medications', models.DO_NOTHING)
    medication2 = models.ForeignKey('Medications', models.DO_NOTHING, related_name='medicationinteractions_medication2_set')

    class Meta:
        managed = False
        db_table = 'medication_interactions'


class MedicationLogs(models.Model):
    id = models.BigAutoField(primary_key=True)
    scheduled_time = models.DateTimeField()
    actual_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20)
    dosage_taken = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    notes = models.TextField()
    side_effects = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    medication = models.ForeignKey('Medications', models.DO_NOTHING)
    patient = models.ForeignKey('Users', models.DO_NOTHING)
    schedule = models.ForeignKey('MedicationSchedules', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'medication_logs'


class MedicationSchedules(models.Model):
    id = models.BigAutoField(primary_key=True)
    timing = models.CharField(max_length=20)
    custom_time = models.TimeField(blank=True, null=True)
    dosage_amount = models.DecimalField(max_digits=8, decimal_places=2)
    frequency = models.CharField(max_length=50)
    monday = models.BooleanField()
    tuesday = models.BooleanField()
    wednesday = models.BooleanField()
    thursday = models.BooleanField()
    friday = models.BooleanField()
    saturday = models.BooleanField()
    sunday = models.BooleanField()
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20)
    instructions = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    medication = models.ForeignKey('Medications', models.DO_NOTHING)
    patient = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'medication_schedules'


class Medications(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200)
    brand_name = models.CharField(max_length=200)
    medication_type = models.CharField(max_length=20)
    prescription_type = models.CharField(max_length=20)
    strength = models.CharField(max_length=50)
    dosage_unit = models.CharField(max_length=20)
    pill_count = models.IntegerField()
    low_stock_threshold = models.IntegerField()
    description = models.TextField()
    active_ingredients = models.TextField()
    manufacturer = models.CharField(max_length=200)
    side_effects = models.TextField()
    contraindications = models.TextField()
    storage_instructions = models.TextField()
    expiration_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    image_alt_text = models.CharField(max_length=200)
    image_metadata = models.JSONField()
    image_optimization_level = models.CharField(max_length=10)
    image_processing_attempts = models.IntegerField()
    image_processing_error = models.TextField()
    image_processing_last_attempt = models.DateTimeField(blank=True, null=True)
    image_processing_priority = models.CharField(max_length=10)
    image_processing_status = models.CharField(max_length=20)
    medication_image = models.CharField(max_length=100, blank=True, null=True)
    medication_image_avif = models.CharField(max_length=100, blank=True, null=True)
    medication_image_jpeg_xl = models.CharField(max_length=100, blank=True, null=True)
    medication_image_original = models.CharField(max_length=100, blank=True, null=True)
    medication_image_thumbnail = models.CharField(max_length=100, blank=True, null=True)
    medication_image_webp = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'medications'


class MedicationsMedicationdetailpage(models.Model):
    page_ptr = models.OneToOneField('WagtailcorePage', models.DO_NOTHING, primary_key=True)
    additional_info = models.TextField()
    medication = models.OneToOneField(Medications, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'medications_medicationdetailpage'


class MedicationsMedicationindexpage(models.Model):
    page_ptr = models.OneToOneField('WagtailcorePage', models.DO_NOTHING, primary_key=True)
    intro = models.TextField()

    class Meta:
        managed = False
        db_table = 'medications_medicationindexpage'


class NotificationTemplates(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    variables = models.JSONField()
    is_active = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'notification_templates'


class Notifications(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    notification_type = models.CharField(max_length=20)
    priority = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    target_user_types = models.JSONField()
    scheduled_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField()
    show_on_dashboard = models.BooleanField()
    require_acknowledgment = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'notifications'


class NotificationsNotificationdetailpage(models.Model):
    page_ptr = models.OneToOneField('WagtailcorePage', models.DO_NOTHING, primary_key=True)
    additional_info = models.TextField()
    notification = models.OneToOneField(Notifications, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'notifications_notificationdetailpage'


class NotificationsNotificationindexpage(models.Model):
    page_ptr = models.OneToOneField('WagtailcorePage', models.DO_NOTHING, primary_key=True)
    intro = models.TextField()

    class Meta:
        managed = False
        db_table = 'notifications_notificationindexpage'


class NotificationsTargetUsers(models.Model):
    id = models.BigAutoField(primary_key=True)
    notification = models.ForeignKey(Notifications, models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'notifications_target_users'
        unique_together = (('notification', 'user'),)


class NytNotification(models.Model):
    message = models.TextField()
    url = models.CharField(max_length=2000, blank=True, null=True)
    is_viewed = models.BooleanField()
    is_emailed = models.BooleanField()
    created = models.DateTimeField()
    occurrences = models.IntegerField()
    subscription = models.ForeignKey('NytSubscription', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    modified = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'nyt_notification'


class NytNotificationtype(models.Model):
    key = models.CharField(primary_key=True, max_length=128)
    label = models.CharField(max_length=128, blank=True, null=True)
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'nyt_notificationtype'


class NytSettings(models.Model):
    user = models.ForeignKey('Users', models.DO_NOTHING)
    interval = models.SmallIntegerField()
    is_default = models.BooleanField()
    created = models.DateTimeField()
    modified = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'nyt_settings'


class NytSubscription(models.Model):
    settings = models.ForeignKey(NytSettings, models.DO_NOTHING)
    notification_type = models.ForeignKey(NytNotificationtype, models.DO_NOTHING)
    object_id = models.CharField(max_length=64, blank=True, null=True)
    send_emails = models.BooleanField()
    latest = models.ForeignKey(NytNotification, models.DO_NOTHING, blank=True, null=True)
    created = models.DateTimeField()
    last_sent = models.DateTimeField(blank=True, null=True)
    modified = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'nyt_subscription'


class OcrProcessingResults(models.Model):
    id = models.BigAutoField(primary_key=True)
    processing_status = models.CharField(max_length=20)
    processing_priority = models.CharField(max_length=10)
    processing_started_at = models.DateTimeField(blank=True, null=True)
    processing_completed_at = models.DateTimeField(blank=True, null=True)
    processing_duration_seconds = models.IntegerField(blank=True, null=True)
    ocr_engine_used = models.CharField(max_length=100)
    ocr_engine_version = models.CharField(max_length=50)
    confidence_score = models.FloatField(blank=True, null=True)
    extracted_text = models.TextField()
    processed_text = models.TextField()
    text_blocks = models.JSONField()
    detected_language = models.CharField(max_length=10)
    language_confidence = models.FloatField(blank=True, null=True)
    image_quality_score = models.FloatField(blank=True, null=True)
    image_metadata = models.JSONField()
    processing_errors = models.JSONField()
    processing_warnings = models.JSONField()
    processing_notes = models.TextField()
    retry_count = models.IntegerField()
    max_retries = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    prescription_image = models.ForeignKey('PrescriptionImages', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'ocr_processing_results'


class PatientMedicationInteractions(models.Model):
    id = models.BigAutoField(primary_key=True)
    interaction_date = models.DateTimeField()
    interaction_status = models.CharField(max_length=20)
    reviewed_by = models.CharField(max_length=200)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    review_notes = models.TextField()
    action_taken = models.CharField(max_length=20)
    action_notes = models.TextField()
    risk_assessment = models.CharField(max_length=20)
    patient_specific_factors = models.JSONField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    interaction = models.ForeignKey(MedicationInteractions, models.DO_NOTHING)
    patient = models.ForeignKey('PrescriptionPatients', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'patient_medication_interactions'


class PharmacyIntegrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    pharmacy_name = models.CharField(max_length=200)
    integration_type = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    api_endpoint = models.CharField(max_length=200)
    api_key = models.CharField(max_length=255)
    webhook_url = models.CharField(max_length=200)
    auto_order_enabled = models.BooleanField()
    order_threshold = models.IntegerField()
    order_quantity_multiplier = models.FloatField()
    order_lead_time_days = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    last_sync = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pharmacy_integrations'


class PostOfficeAttachment(models.Model):
    file = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    mimetype = models.CharField(max_length=255)
    headers = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'post_office_attachment'


class PostOfficeAttachmentEmails(models.Model):
    id = models.BigAutoField(primary_key=True)
    attachment = models.ForeignKey(PostOfficeAttachment, models.DO_NOTHING)
    email = models.ForeignKey('PostOfficeEmail', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'post_office_attachment_emails'
        unique_together = (('attachment', 'email'),)


class PostOfficeEmail(models.Model):
    from_email = models.CharField(max_length=254)
    to = models.TextField()
    cc = models.TextField()
    bcc = models.TextField()
    subject = models.CharField(max_length=989)
    message = models.TextField()
    html_message = models.TextField()
    status = models.SmallIntegerField(blank=True, null=True)
    priority = models.SmallIntegerField(blank=True, null=True)
    created = models.DateTimeField()
    last_updated = models.DateTimeField()
    scheduled_time = models.DateTimeField(blank=True, null=True)
    headers = models.JSONField(blank=True, null=True)
    context = models.TextField(blank=True, null=True)
    template = models.ForeignKey('PostOfficeEmailtemplate', models.DO_NOTHING, blank=True, null=True)
    backend_alias = models.CharField(max_length=64)
    number_of_retries = models.IntegerField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    message_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'post_office_email'


class PostOfficeEmailtemplate(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    subject = models.CharField(max_length=255)
    content = models.TextField()
    html_content = models.TextField()
    created = models.DateTimeField()
    last_updated = models.DateTimeField()
    default_template = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    language = models.CharField(max_length=12)

    class Meta:
        managed = False
        db_table = 'post_office_emailtemplate'
        unique_together = (('name', 'language', 'default_template'),)


class PostOfficeLog(models.Model):
    date = models.DateTimeField()
    status = models.SmallIntegerField()
    exception_type = models.CharField(max_length=255)
    message = models.TextField()
    email = models.ForeignKey(PostOfficeEmail, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'post_office_log'


class PrescriptionAudits(models.Model):
    id = models.BigAutoField(primary_key=True)
    audit_type = models.CharField(max_length=20)
    action_performed = models.CharField(max_length=200)
    performed_by = models.CharField(max_length=200)
    performed_at = models.DateTimeField()
    previous_value = models.JSONField(blank=True, null=True)
    new_value = models.JSONField(blank=True, null=True)
    reason = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField()
    created_at = models.DateTimeField()
    prescription = models.ForeignKey('Prescriptions', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'prescription_audits'


class PrescriptionDispensings(models.Model):
    id = models.BigAutoField(primary_key=True)
    dispensing_status = models.CharField(max_length=20)
    dispenser_name = models.CharField(max_length=200)
    dispenser_role = models.CharField(max_length=100)
    dispensing_date = models.DateTimeField()
    total_medications = models.IntegerField()
    dispensed_medications = models.IntegerField()
    dispensing_notes = models.TextField()
    quality_check_passed = models.BooleanField()
    quality_check_by = models.CharField(max_length=200)
    quality_check_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    prescription = models.ForeignKey('Prescriptions', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'prescription_dispensings'


class PrescriptionDoctors(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    practice_number = models.CharField(max_length=50)
    specialty = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)
    email = models.CharField(max_length=254)
    practice_name = models.CharField(max_length=200)
    practice_address = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'prescription_doctors'


class PrescriptionImages(models.Model):
    id = models.BigAutoField(primary_key=True)
    image_file = models.CharField(max_length=100)
    image_type = models.CharField(max_length=20)
    image_format = models.CharField(max_length=10)
    image_size_bytes = models.IntegerField(blank=True, null=True)
    image_width = models.IntegerField(blank=True, null=True)
    image_height = models.IntegerField(blank=True, null=True)
    image_resolution_dpi = models.IntegerField(blank=True, null=True)
    image_quality_score = models.FloatField(blank=True, null=True)
    image_metadata = models.JSONField()
    upload_source = models.CharField(max_length=20)
    upload_device_info = models.JSONField()
    upload_location = models.CharField(max_length=200)
    upload_ip_address = models.GenericIPAddressField(blank=True, null=True)
    upload_user_agent = models.TextField()
    is_processed = models.BooleanField()
    processing_priority = models.CharField(max_length=10)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'prescription_images'


class PrescriptionMedications(models.Model):
    id = models.BigAutoField(primary_key=True)
    medication_number = models.IntegerField()
    medication_name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200)
    brand_name = models.CharField(max_length=200)
    strength = models.CharField(max_length=50)
    dosage_unit = models.CharField(max_length=20)
    quantity = models.IntegerField()
    quantity_unit = models.CharField(max_length=20)
    instructions = models.TextField()
    timing = models.CharField(max_length=20)
    custom_time = models.TimeField(blank=True, null=True)
    duration_days = models.IntegerField(blank=True, null=True)
    repeats = models.IntegerField()
    as_needed = models.BooleanField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20)
    dispensed_quantity = models.IntegerField()
    dispensed_at = models.DateTimeField(blank=True, null=True)
    dispensed_by = models.CharField(max_length=200)
    notes = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    medication = models.ForeignKey(Medications, models.DO_NOTHING, blank=True, null=True)
    prescription = models.ForeignKey('Prescriptions', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'prescription_medications'
        unique_together = (('prescription', 'medication_number'),)


class PrescriptionPatients(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    id_number = models.CharField(max_length=20)
    date_of_birth = models.DateField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10)
    contact_number = models.CharField(max_length=20)
    email = models.CharField(max_length=254)
    address = models.TextField()
    medical_aid_number = models.CharField(max_length=50)
    medical_aid_scheme = models.CharField(max_length=100)
    allergies = models.TextField()
    chronic_conditions = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'prescription_patients'


class PrescriptionRenewals(models.Model):
    id = models.BigAutoField(primary_key=True)
    prescription_number = models.CharField(max_length=100)
    prescribed_by = models.CharField(max_length=200)
    prescribed_date = models.DateField()
    expiry_date = models.DateField()
    status = models.CharField(max_length=20)
    priority = models.CharField(max_length=20)
    reminder_days_before = models.IntegerField()
    last_reminder_sent = models.DateTimeField(blank=True, null=True)
    renewed_date = models.DateField(blank=True, null=True)
    new_expiry_date = models.DateField(blank=True, null=True)
    notes = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    medication = models.ForeignKey(Medications, models.DO_NOTHING)
    patient = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'prescription_renewals'


class PrescriptionReviews(models.Model):
    id = models.BigAutoField(primary_key=True)
    review_type = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    reviewer_name = models.CharField(max_length=200)
    reviewer_role = models.CharField(max_length=100)
    review_date = models.DateTimeField()
    review_notes = models.TextField()
    approval_conditions = models.TextField()
    rejection_reason = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    prescription = models.ForeignKey('Prescriptions', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'prescription_reviews'


class PrescriptionValidations(models.Model):
    id = models.BigAutoField(primary_key=True)
    validation_type = models.CharField(max_length=20)
    validation_status = models.CharField(max_length=20)
    validation_date = models.DateTimeField()
    validated_by = models.CharField(max_length=200)
    validation_notes = models.TextField()
    warnings = models.JSONField()
    errors = models.JSONField()
    recommendations = models.JSONField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    prescription = models.ForeignKey('Prescriptions', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'prescription_validations'


class PrescriptionWorkflowStates(models.Model):
    id = models.BigAutoField(primary_key=True)
    state = models.CharField(max_length=20)
    previous_state = models.CharField(max_length=20)
    state_changed_at = models.DateTimeField()
    state_changed_by = models.CharField(max_length=200)
    notes = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    prescription = models.ForeignKey('Prescriptions', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'prescription_workflow_states'


class Prescriptions(models.Model):
    id = models.BigAutoField(primary_key=True)
    prescription_number = models.CharField(unique=True, max_length=100)
    prescription_date = models.DateField()
    expiry_date = models.DateField()
    status = models.CharField(max_length=20)
    priority = models.CharField(max_length=20)
    prescription_type = models.CharField(max_length=20)
    total_medications = models.IntegerField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    notes = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    doctor = models.ForeignKey(PrescriptionDoctors, models.DO_NOTHING, blank=True, null=True)
    patient = models.ForeignKey(PrescriptionPatients, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'prescriptions'


class PushNotificationsApnsdevice(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField()
    date_created = models.DateTimeField(blank=True, null=True)
    device_id = models.UUIDField(blank=True, null=True)
    registration_id = models.CharField(max_length=200)
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    application_id = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'push_notifications_apnsdevice'


class PushNotificationsGcmdevice(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField()
    date_created = models.DateTimeField(blank=True, null=True)
    device_id = models.BigIntegerField(blank=True, null=True)
    registration_id = models.TextField()
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    cloud_message_type = models.CharField(max_length=3)
    application_id = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'push_notifications_gcmdevice'


class PushNotificationsWebpushdevice(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField()
    date_created = models.DateTimeField(blank=True, null=True)
    application_id = models.CharField(max_length=64, blank=True, null=True)
    registration_id = models.TextField()
    p256dh = models.CharField(max_length=88)
    auth = models.CharField(max_length=24)
    browser = models.CharField(max_length=10)
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'push_notifications_webpushdevice'


class PushNotificationsWnsdevice(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField()
    date_created = models.DateTimeField(blank=True, null=True)
    device_id = models.UUIDField(blank=True, null=True)
    registration_id = models.TextField()
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    application_id = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'push_notifications_wnsdevice'


class SecurityAnonymizedDatasets(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    dataset_type = models.CharField(max_length=20)
    anonymization_method = models.CharField(max_length=30)
    status = models.CharField(max_length=20)
    original_record_count = models.IntegerField()
    anonymized_record_count = models.IntegerField()
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    deleted_at = models.DateTimeField(blank=True, null=True)
    hipaa_compliant = models.BooleanField()
    popia_compliant = models.BooleanField()
    metadata = models.JSONField()
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField(blank=True, null=True)
    created_by = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'security_anonymized_datasets'


class SecurityAnonymizedDatasetsAuthorizedUsers(models.Model):
    id = models.BigAutoField(primary_key=True)
    anonymizeddataset = models.ForeignKey(SecurityAnonymizedDatasets, models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'security_anonymized_datasets_authorized_users'
        unique_together = (('anonymizeddataset', 'user'),)


class SecurityDatasetAccessLogs(models.Model):
    id = models.BigAutoField(primary_key=True)
    access_type = models.CharField(max_length=20)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField()
    timestamp = models.DateTimeField()
    metadata = models.JSONField()
    dataset = models.ForeignKey(SecurityAnonymizedDatasets, models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'security_dataset_access_logs'


class SecurityEvents(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=20)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField()
    request_path = models.CharField(max_length=500)
    request_method = models.CharField(max_length=10)
    metadata = models.JSONField()
    is_resolved = models.BooleanField()
    resolution_notes = models.TextField()
    resolved_at = models.DateTimeField(blank=True, null=True)
    timestamp = models.DateTimeField()
    resolved_by = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('Users', models.DO_NOTHING, related_name='securityevents_user_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'security_events'


class StockAlertRules(models.Model):
    id = models.BigAutoField(primary_key=True)
    rule_name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=20)
    rule_conditions = models.JSONField()
    threshold_value = models.FloatField()
    threshold_unit = models.CharField(max_length=20)
    alert_priority = models.CharField(max_length=20)
    notification_channels = models.JSONField()
    is_active = models.BooleanField()
    rule_description = models.TextField()
    created_by = models.CharField(max_length=200)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    medication = models.ForeignKey(Medications, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stock_alert_rules'


class StockAlerts(models.Model):
    id = models.BigAutoField(primary_key=True)
    alert_type = models.CharField(max_length=20)
    priority = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    message = models.TextField()
    current_stock = models.IntegerField()
    threshold_level = models.IntegerField()
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolution_notes = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    acknowledged_by = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    created_by = models.ForeignKey('Users', models.DO_NOTHING, related_name='stockalerts_created_by_set')
    medication = models.ForeignKey(Medications, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'stock_alerts'


class StockAnalytics(models.Model):
    id = models.BigAutoField(primary_key=True)
    daily_usage_rate = models.FloatField()
    weekly_usage_rate = models.FloatField()
    monthly_usage_rate = models.FloatField()
    days_until_stockout = models.IntegerField(blank=True, null=True)
    predicted_stockout_date = models.DateField(blank=True, null=True)
    recommended_order_quantity = models.IntegerField()
    recommended_order_date = models.DateField(blank=True, null=True)
    seasonal_factor = models.FloatField()
    usage_volatility = models.FloatField()
    stockout_confidence = models.FloatField()
    last_calculated = models.DateTimeField()
    calculation_window_days = models.IntegerField()
    medication = models.OneToOneField(Medications, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'stock_analytics'


class StockForecasts(models.Model):
    id = models.BigAutoField(primary_key=True)
    forecast_date = models.DateField()
    forecast_period_days = models.IntegerField()
    forecast_type = models.CharField(max_length=20)
    predicted_demand = models.IntegerField()
    predicted_stock_level = models.IntegerField()
    predicted_stockout_date = models.DateField(blank=True, null=True)
    recommended_order_quantity = models.IntegerField()
    recommended_order_date = models.DateField(blank=True, null=True)
    confidence_level = models.FloatField()
    forecast_accuracy = models.FloatField(blank=True, null=True)
    seasonal_factors = models.JSONField()
    forecast_algorithm = models.CharField(max_length=100)
    forecast_parameters = models.JSONField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    medication = models.ForeignKey(Medications, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'stock_forecasts'


class StockPerformance(models.Model):
    id = models.BigAutoField(primary_key=True)
    performance_date = models.DateField()
    performance_metric = models.CharField(max_length=20)
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=20)
    target_value = models.FloatField(blank=True, null=True)
    performance_status = models.CharField(max_length=20)
    performance_trend = models.CharField(max_length=20)
    performance_notes = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    medication = models.ForeignKey(Medications, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stock_performance'


class StockReports(models.Model):
    id = models.BigAutoField(primary_key=True)
    report_type = models.CharField(max_length=20)
    report_period_start = models.DateField()
    report_period_end = models.DateField()
    report_date = models.DateTimeField()
    report_status = models.CharField(max_length=20)
    total_medications = models.IntegerField()
    low_stock_medications = models.IntegerField()
    out_of_stock_medications = models.IntegerField()
    expiring_medications = models.IntegerField()
    expired_medications = models.IntegerField()
    total_stock_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    report_data = models.JSONField()
    report_summary = models.TextField()
    generated_by = models.CharField(max_length=200)
    report_notes = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'stock_reports'


class StockTransactions(models.Model):
    id = models.BigAutoField(primary_key=True)
    transaction_type = models.CharField(max_length=30)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    stock_before = models.IntegerField()
    stock_after = models.IntegerField()
    reference_number = models.CharField(max_length=100)
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField(blank=True, null=True)
    notes = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    medication = models.ForeignKey(Medications, models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'stock_transactions'


class StockTrends(models.Model):
    id = models.BigAutoField(primary_key=True)
    trend_date = models.DateField()
    trend_type = models.CharField(max_length=20)
    opening_stock = models.IntegerField()
    closing_stock = models.IntegerField()
    stock_in = models.IntegerField()
    stock_out = models.IntegerField()
    stock_adjustments = models.IntegerField()
    stock_loss = models.IntegerField()
    usage_rate = models.FloatField()
    turnover_rate = models.FloatField()
    days_of_stock_remaining = models.IntegerField(blank=True, null=True)
    stock_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    trend_metadata = models.JSONField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    medication = models.ForeignKey(Medications, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'stock_trends'


class StockVisualizations(models.Model):
    id = models.BigAutoField(primary_key=True)
    chart_type = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    description = models.TextField()
    chart_data = models.JSONField()
    chart_options = models.JSONField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField()
    auto_refresh = models.BooleanField()
    refresh_interval_hours = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    last_generated = models.DateTimeField(blank=True, null=True)
    medication = models.ForeignKey(Medications, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'stock_visualizations'


class TaggitTag(models.Model):
    name = models.CharField(unique=True, max_length=100)
    slug = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'taggit_tag'


class TaggitTaggeditem(models.Model):
    object_id = models.IntegerField()
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING)
    tag = models.ForeignKey(TaggitTag, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'taggit_taggeditem'
        unique_together = (('content_type', 'object_id', 'tag'),)


class TextExtractionResults(models.Model):
    id = models.BigAutoField(primary_key=True)
    extraction_type = models.CharField(max_length=20)
    extraction_status = models.CharField(max_length=20)
    extracted_data = models.JSONField()
    confidence_scores = models.JSONField()
    validation_results = models.JSONField()
    extraction_errors = models.JSONField()
    extraction_warnings = models.JSONField()
    extraction_notes = models.TextField()
    extraction_duration_seconds = models.IntegerField(blank=True, null=True)
    extraction_algorithm = models.CharField(max_length=100)
    extraction_algorithm_version = models.CharField(max_length=50)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    ocr_result = models.ForeignKey(OcrProcessingResults, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'text_extraction_results'


class UserNotifications(models.Model):
    id = models.BigAutoField(primary_key=True)
    status = models.CharField(max_length=20)
    sent_at = models.DateTimeField()
    read_at = models.DateTimeField(blank=True, null=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    dismissed_at = models.DateTimeField(blank=True, null=True)
    notification = models.ForeignKey(Notifications, models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'user_notifications'
        unique_together = (('user', 'notification'),)


class Users(models.Model):
    id = models.BigAutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    user_type = models.CharField(max_length=20)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=17)
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=17)
    emergency_contact_relationship = models.CharField(max_length=50)
    preferred_language = models.CharField(max_length=10)
    timezone = models.CharField(max_length=50)
    email_notifications = models.BooleanField()
    sms_notifications = models.BooleanField()
    mfa_enabled = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    blood_type = models.CharField(max_length=15, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    medical_conditions = models.TextField(blank=True, null=True)
    current_medications = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'


class UsersGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(Users, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'users_groups'
        unique_together = (('user', 'group'),)


class UsersUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    password = models.CharField(max_length=128)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    email = models.CharField(unique=True, max_length=254)
    user_type = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=10)
    blood_type = models.CharField(max_length=15)
    allergies = models.TextField()
    medical_conditions = models.TextField()
    current_medications = models.TextField()
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=20)
    emergency_contact_relationship = models.CharField(max_length=20)
    preferred_language = models.CharField(max_length=2)
    timezone = models.CharField(max_length=50)
    email_notifications = models.BooleanField()
    sms_notifications = models.BooleanField()
    mfa_enabled = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    last_login = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users_user'


class UsersUserAvatar(models.Model):
    id = models.BigAutoField(primary_key=True)
    image = models.CharField(max_length=100)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    user = models.OneToOneField(Users, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'users_user_avatar'


class UsersUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(Users, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'users_user_permissions'
        unique_together = (('user', 'permission'),)


class UsersUserProfile(models.Model):
    id = models.BigAutoField(primary_key=True)
    professional_title = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    specialization = models.CharField(max_length=100)
    facility_name = models.CharField(max_length=200)
    facility_address = models.TextField()
    facility_phone = models.CharField(max_length=20)
    notification_preferences = models.JSONField()
    privacy_settings = models.JSONField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    user = models.OneToOneField(Users, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'users_user_profile'


class WagtailadminAdmin(models.Model):

    class Meta:
        managed = False
        db_table = 'wagtailadmin_admin'


class WagtailadminEditingsession(models.Model):
    object_id = models.CharField(max_length=255)
    last_seen_at = models.DateTimeField()
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING)
    user = models.ForeignKey(Users, models.DO_NOTHING)
    is_editing = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'wagtailadmin_editingsession'


class WagtailcoreCollection(models.Model):
    path = models.CharField(unique=True, max_length=255, db_collation='C')
    depth = models.IntegerField()
    numchild = models.IntegerField()
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'wagtailcore_collection'


class WagtailcoreCollectionviewrestriction(models.Model):
    restriction_type = models.CharField(max_length=20)
    password = models.CharField(max_length=255)
    collection = models.ForeignKey(WagtailcoreCollection, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'wagtailcore_collectionviewrestriction'


class WagtailcoreCollectionviewrestrictionGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    collectionviewrestriction = models.ForeignKey(WagtailcoreCollectionviewrestriction, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'wagtailcore_collectionviewrestriction_groups'
        unique_together = (('collectionviewrestriction', 'group'),)


class WagtailcoreComment(models.Model):
    text = models.TextField()
    contentpath = models.TextField()
    position = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    resolved_at = models.DateTimeField(blank=True, null=True)
    page = models.ForeignKey('WagtailcorePage', models.DO_NOTHING)
    resolved_by = models.ForeignKey(Users, models.DO_NOTHING, blank=True, null=True)
    revision_created = models.ForeignKey('WagtailcoreRevision', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(Users, models.DO_NOTHING, related_name='wagtailcorecomment_user_set')

    class Meta:
        managed = False
        db_table = 'wagtailcore_comment'


class WagtailcoreCommentreply(models.Model):
    text = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    comment = models.ForeignKey(WagtailcoreComment, models.DO_NOTHING)
    user = models.ForeignKey(Users, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'wagtailcore_commentreply'


class WagtailcoreGroupapprovaltask(models.Model):
    task_ptr = models.OneToOneField('WagtailcoreTask', models.DO_NOTHING, primary_key=True)

    class Meta:
        managed = False
        db_table = 'wagtailcore_groupapprovaltask'


class WagtailcoreGroupapprovaltaskGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    groupapprovaltask = models.ForeignKey(WagtailcoreGroupapprovaltask, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'wagtailcore_groupapprovaltask_groups'
        unique_together = (('groupapprovaltask', 'group'),)


class WagtailcoreGroupcollectionpermission(models.Model):
    collection = models.ForeignKey(WagtailcoreCollection, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'wagtailcore_groupcollectionpermission'
        unique_together = (('group', 'collection', 'permission'),)


class WagtailcoreGrouppagepermission(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    page = models.ForeignKey('WagtailcorePage', models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'wagtailcore_grouppagepermission'
        unique_together = (('group', 'page', 'permission'),)


class WagtailcoreLocale(models.Model):
    language_code = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'wagtailcore_locale'


class WagtailcoreModellogentry(models.Model):
    label = models.TextField()
    action = models.CharField(max_length=255)
    data = models.JSONField()
    timestamp = models.DateTimeField()
    content_changed = models.BooleanField()
    deleted = models.BooleanField()
    object_id = models.CharField(max_length=255)
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING, blank=True, null=True)
    user_id = models.BigIntegerField(blank=True, null=True)
    uuid = models.UUIDField(blank=True, null=True)
    revision_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'wagtailcore_modellogentry'


class WagtailcorePage(models.Model):
    path = models.CharField(unique=True, max_length=255, db_collation='C')
    depth = models.IntegerField()
    numchild = models.IntegerField()
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    live = models.BooleanField()
    has_unpublished_changes = models.BooleanField()
    url_path = models.TextField()
    seo_title = models.CharField(max_length=255)
    show_in_menus = models.BooleanField()
    search_description = models.TextField()
    go_live_at = models.DateTimeField(blank=True, null=True)
    expire_at = models.DateTimeField(blank=True, null=True)
    expired = models.BooleanField()
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING)
    owner = models.ForeignKey(Users, models.DO_NOTHING, blank=True, null=True)
    locked = models.BooleanField()
    latest_revision_created_at = models.DateTimeField(blank=True, null=True)
    first_published_at = models.DateTimeField(blank=True, null=True)
    live_revision = models.ForeignKey('WagtailcoreRevision', models.DO_NOTHING, blank=True, null=True)
    last_published_at = models.DateTimeField(blank=True, null=True)
    draft_title = models.CharField(max_length=255)
    locked_at = models.DateTimeField(blank=True, null=True)
    locked_by = models.ForeignKey(Users, models.DO_NOTHING, related_name='wagtailcorepage_locked_by_set', blank=True, null=True)
    translation_key = models.UUIDField()
    locale = models.ForeignKey(WagtailcoreLocale, models.DO_NOTHING)
    alias_of = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    latest_revision = models.ForeignKey('WagtailcoreRevision', models.DO_NOTHING, related_name='wagtailcorepage_latest_revision_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'wagtailcore_page'
        unique_together = (('translation_key', 'locale'),)


class WagtailcorePagelogentry(models.Model):
    label = models.TextField()
    action = models.CharField(max_length=255)
    data = models.JSONField()
    timestamp = models.DateTimeField()
    content_changed = models.BooleanField()
    deleted = models.BooleanField()
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING, blank=True, null=True)
    page_id = models.IntegerField()
    revision_id = models.IntegerField(blank=True, null=True)
    user_id = models.BigIntegerField(blank=True, null=True)
    uuid = models.UUIDField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'wagtailcore_pagelogentry'


class WagtailcorePagesubscription(models.Model):
    comment_notifications = models.BooleanField()
    page = models.ForeignKey(WagtailcorePage, models.DO_NOTHING)
    user = models.ForeignKey(Users, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'wagtailcore_pagesubscription'
        unique_together = (('page', 'user'),)


class WagtailcorePageviewrestriction(models.Model):
    password = models.CharField(max_length=255)
    page = models.ForeignKey(WagtailcorePage, models.DO_NOTHING)
    restriction_type = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'wagtailcore_pageviewrestriction'


class WagtailcorePageviewrestrictionGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    pageviewrestriction = models.ForeignKey(WagtailcorePageviewrestriction, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'wagtailcore_pageviewrestriction_groups'
        unique_together = (('pageviewrestriction', 'group'),)


class WagtailcoreReferenceindex(models.Model):
    object_id = models.CharField(max_length=255)
    to_object_id = models.CharField(max_length=255)
    model_path = models.TextField()
    content_path = models.TextField()
    content_path_hash = models.UUIDField()
    base_content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING)
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING, related_name='wagtailcorereferenceindex_content_type_set')
    to_content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING, related_name='wagtailcorereferenceindex_to_content_type_set')

    class Meta:
        managed = False
        db_table = 'wagtailcore_referenceindex'
        unique_together = (('base_content_type', 'object_id', 'to_content_type', 'to_object_id', 'content_path_hash'),)


class WagtailcoreRevision(models.Model):
    created_at = models.DateTimeField()
    content = models.JSONField()
    approved_go_live_at = models.DateTimeField(blank=True, null=True)
    object_id = models.CharField(max_length=255)
    user = models.ForeignKey(Users, models.DO_NOTHING, blank=True, null=True)
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING)
    base_content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING, related_name='wagtailcorerevision_base_content_type_set')
    object_str = models.TextField()

    class Meta:
        managed = False
        db_table = 'wagtailcore_revision'


class WagtailcoreSite(models.Model):
    hostname = models.CharField(max_length=255)
    port = models.IntegerField()
    is_default_site = models.BooleanField()
    root_page = models.ForeignKey(WagtailcorePage, models.DO_NOTHING)
    site_name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'wagtailcore_site'
        unique_together = (('hostname', 'port'),)


class WagtailcoreTask(models.Model):
    name = models.CharField(max_length=255)
    active = models.BooleanField()
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'wagtailcore_task'


class WagtailcoreTaskstate(models.Model):
    status = models.CharField(max_length=50)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(blank=True, null=True)
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING)
    revision = models.ForeignKey(WagtailcoreRevision, models.DO_NOTHING)
    task = models.ForeignKey(WagtailcoreTask, models.DO_NOTHING)
    workflow_state = models.ForeignKey('WagtailcoreWorkflowstate', models.DO_NOTHING)
    finished_by = models.ForeignKey(Users, models.DO_NOTHING, blank=True, null=True)
    comment = models.TextField()

    class Meta:
        managed = False
        db_table = 'wagtailcore_taskstate'


class WagtailcoreUploadedfile(models.Model):
    file = models.CharField(max_length=200)
    for_content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING, blank=True, null=True)
    uploaded_by_user = models.ForeignKey(Users, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'wagtailcore_uploadedfile'


class WagtailcoreWorkflow(models.Model):
    name = models.CharField(max_length=255)
    active = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'wagtailcore_workflow'


class WagtailcoreWorkflowcontenttype(models.Model):
    content_type = models.OneToOneField(DjangoContentType, models.DO_NOTHING, primary_key=True)
    workflow = models.ForeignKey(WagtailcoreWorkflow, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'wagtailcore_workflowcontenttype'


class WagtailcoreWorkflowpage(models.Model):
    page = models.OneToOneField(WagtailcorePage, models.DO_NOTHING, primary_key=True)
    workflow = models.ForeignKey(WagtailcoreWorkflow, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'wagtailcore_workflowpage'


class WagtailcoreWorkflowstate(models.Model):
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField()
    current_task_state = models.OneToOneField(WagtailcoreTaskstate, models.DO_NOTHING, blank=True, null=True)
    object_id = models.CharField(max_length=255)
    requested_by = models.ForeignKey(Users, models.DO_NOTHING, blank=True, null=True)
    workflow = models.ForeignKey(WagtailcoreWorkflow, models.DO_NOTHING)
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING)
    base_content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING, related_name='wagtailcoreworkflowstate_base_content_type_set')

    class Meta:
        managed = False
        db_table = 'wagtailcore_workflowstate'
        unique_together = (('base_content_type', 'object_id'),)


class WagtailcoreWorkflowtask(models.Model):
    sort_order = models.IntegerField(blank=True, null=True)
    task = models.ForeignKey(WagtailcoreTask, models.DO_NOTHING)
    workflow = models.ForeignKey(WagtailcoreWorkflow, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'wagtailcore_workflowtask'
        unique_together = (('workflow', 'task'),)


class WagtaildocsDocument(models.Model):
    title = models.CharField(max_length=255)
    file = models.CharField(max_length=100)
    created_at = models.DateTimeField()
    uploaded_by_user = models.ForeignKey(Users, models.DO_NOTHING, blank=True, null=True)
    collection = models.ForeignKey(WagtailcoreCollection, models.DO_NOTHING)
    file_size = models.BigIntegerField(blank=True, null=True)
    file_hash = models.CharField(max_length=40)

    class Meta:
        managed = False
        db_table = 'wagtaildocs_document'


class WagtailembedsEmbed(models.Model):
    url = models.TextField()
    max_width = models.SmallIntegerField(blank=True, null=True)
    type = models.CharField(max_length=10)
    html = models.TextField()
    title = models.TextField()
    author_name = models.TextField()
    provider_name = models.TextField()
    thumbnail_url = models.TextField()
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    last_updated = models.DateTimeField()
    hash = models.CharField(unique=True, max_length=32)
    cache_until = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'wagtailembeds_embed'


class WagtailformsFormsubmission(models.Model):
    form_data = models.JSONField()
    submit_time = models.DateTimeField()
    page = models.ForeignKey(WagtailcorePage, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'wagtailforms_formsubmission'


class WagtailimagesImage(models.Model):
    title = models.CharField(max_length=255)
    file = models.CharField(max_length=100)
    width = models.IntegerField()
    height = models.IntegerField()
    created_at = models.DateTimeField()
    focal_point_x = models.IntegerField(blank=True, null=True)
    focal_point_y = models.IntegerField(blank=True, null=True)
    focal_point_width = models.IntegerField(blank=True, null=True)
    focal_point_height = models.IntegerField(blank=True, null=True)
    uploaded_by_user = models.ForeignKey(Users, models.DO_NOTHING, blank=True, null=True)
    file_size = models.IntegerField(blank=True, null=True)
    collection = models.ForeignKey(WagtailcoreCollection, models.DO_NOTHING)
    file_hash = models.CharField(max_length=40)
    description = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'wagtailimages_image'


class WagtailimagesRendition(models.Model):
    file = models.CharField(max_length=100)
    width = models.IntegerField()
    height = models.IntegerField()
    focal_point_key = models.CharField(max_length=16)
    filter_spec = models.CharField(max_length=255)
    image = models.ForeignKey(WagtailimagesImage, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'wagtailimages_rendition'
        unique_together = (('image', 'filter_spec', 'focal_point_key'),)


class WagtailredirectsRedirect(models.Model):
    old_path = models.CharField(max_length=255)
    is_permanent = models.BooleanField()
    redirect_link = models.CharField(max_length=255)
    redirect_page = models.ForeignKey(WagtailcorePage, models.DO_NOTHING, blank=True, null=True)
    site = models.ForeignKey(WagtailcoreSite, models.DO_NOTHING, blank=True, null=True)
    automatically_created = models.BooleanField()
    created_at = models.DateTimeField(blank=True, null=True)
    redirect_page_route_path = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'wagtailredirects_redirect'
        unique_together = (('old_path', 'site'),)


class WagtailsearchIndexentry(models.Model):
    object_id = models.CharField(max_length=50)
    title_norm = models.FloatField()
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING)
    autocomplete = models.TextField()  # This field type is a guess.
    title = models.TextField()  # This field type is a guess.
    body = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'wagtailsearch_indexentry'
        unique_together = (('content_type', 'object_id'),)


class WagtailusersUserprofile(models.Model):
    submitted_notifications = models.BooleanField()
    approved_notifications = models.BooleanField()
    rejected_notifications = models.BooleanField()
    user = models.OneToOneField(Users, models.DO_NOTHING)
    preferred_language = models.CharField(max_length=10)
    current_time_zone = models.CharField(max_length=40)
    avatar = models.CharField(max_length=100)
    updated_comments_notifications = models.BooleanField()
    dismissibles = models.JSONField()
    theme = models.CharField(max_length=40)
    density = models.CharField(max_length=40)
    contrast = models.CharField(max_length=40)

    class Meta:
        managed = False
        db_table = 'wagtailusers_userprofile'
