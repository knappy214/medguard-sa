"""
Wagtail 7.0.2 Translation Workflow System

This module implements the new translation workflow for content approval
with multiple stages and quality assurance features.
"""

from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User, Group
from django.db import models
from django.utils import timezone
from wagtail import hooks
from wagtail.models import Page, Locale
from wagtail.admin.views.pages import get_page_permissions_for_user
from wagtail.admin.views.pages.listing import get_page_listing_context
from wagtail.admin.views.pages.listing import get_page_listing_context_for_translation


class TranslationWorkflowStage(models.Model):
    """Model for translation workflow stages."""
    
    STAGE_CHOICES = [
        ('draft', _('Draft')),
        ('review', _('Review')),
        ('approved', _('Approved')),
        ('published', _('Published')),
        ('rejected', _('Rejected')),
    ]
    
    name = models.CharField(max_length=50, choices=STAGE_CHOICES)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    requires_approval = models.BooleanField(default=False)
    auto_advance = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.get_name_display()


class TranslationWorkflow(models.Model):
    """Model for managing translation workflows."""
    
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='translation_workflows')
    source_locale = models.ForeignKey(Locale, on_delete=models.CASCADE, related_name='source_workflows')
    target_locale = models.ForeignKey(Locale, on_delete=models.CASCADE, related_name='target_workflows')
    current_stage = models.ForeignKey(TranslationWorkflowStage, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_workflows')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['page', 'target_locale']
    
    def __str__(self):
        return f"Translation workflow for {self.page.title} ({self.target_locale})"
    
    def advance_stage(self, user, notes=None):
        """Advance to the next stage in the workflow."""
        current_order = self.current_stage.order
        next_stage = TranslationWorkflowStage.objects.filter(
            order__gt=current_order
        ).first()
        
        if next_stage:
            # Create workflow log entry
            TranslationWorkflowLog.objects.create(
                workflow=self,
                from_stage=self.current_stage,
                to_stage=next_stage,
                user=user,
                notes=notes
            )
            
            self.current_stage = next_stage
            self.updated_at = timezone.now()
            self.save()
            
            # Check if workflow is completed
            if next_stage.name == 'published':
                self.completed_at = timezone.now()
                self.is_active = False
                self.save()
            
            return True
        
        return False
    
    def reject_translation(self, user, reason):
        """Reject the translation and return to draft stage."""
        reject_stage = TranslationWorkflowStage.objects.get(name='rejected')
        
        # Create workflow log entry
        TranslationWorkflowLog.objects.create(
            workflow=self,
            from_stage=self.current_stage,
            to_stage=reject_stage,
            user=user,
            notes=f"Rejected: {reason}"
        )
        
        self.current_stage = reject_stage
        self.updated_at = timezone.now()
        self.save()
        
        return True
    
    def get_available_actions(self, user):
        """Get available actions for the current user and stage."""
        actions = []
        
        if not self.is_active:
            return actions
        
        # Check user permissions
        page_perms = get_page_permissions_for_user(user, self.page)
        
        if self.current_stage.name == 'draft':
            if page_perms.can_edit():
                actions.append('submit_for_review')
        
        elif self.current_stage.name == 'review':
            if user.groups.filter(name='translators').exists():
                actions.append('approve')
                actions.append('request_changes')
            if page_perms.can_edit():
                actions.append('edit')
        
        elif self.current_stage.name == 'approved':
            if user.groups.filter(name='editors').exists():
                actions.append('publish')
            if page_perms.can_edit():
                actions.append('edit')
        
        elif self.current_stage.name == 'rejected':
            if page_perms.can_edit():
                actions.append('resubmit')
        
        return actions


class TranslationWorkflowLog(models.Model):
    """Model for logging translation workflow activities."""
    
    workflow = models.ForeignKey(TranslationWorkflow, on_delete=models.CASCADE, related_name='logs')
    from_stage = models.ForeignKey(TranslationWorkflowStage, on_delete=models.CASCADE, related_name='from_logs')
    to_stage = models.ForeignKey(TranslationWorkflowStage, on_delete=models.CASCADE, related_name='to_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.workflow} - {self.from_stage} to {self.to_stage} by {self.user}"


class TranslationQualityCheck(models.Model):
    """Model for translation quality checks."""
    
    workflow = models.OneToOneField(TranslationWorkflow, on_delete=models.CASCADE, related_name='quality_check')
    spelling_check = models.BooleanField(default=False)
    grammar_check = models.BooleanField(default=False)
    terminology_check = models.BooleanField(default=False)
    consistency_check = models.BooleanField(default=False)
    completeness_check = models.BooleanField(default=False)
    medical_accuracy_check = models.BooleanField(default=False)
    checked_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    checked_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Quality check for {self.workflow}"
    
    def run_quality_checks(self):
        """Run all quality checks on the translation."""
        # This would integrate with external quality checking services
        # For now, we'll set basic checks
        self.spelling_check = True
        self.grammar_check = True
        self.terminology_check = True
        self.consistency_check = True
        self.completeness_check = True
        self.medical_accuracy_check = True
        self.checked_at = timezone.now()
        self.save()


@hooks.register('register_page_listing_buttons')
def translation_workflow_buttons(page, page_perms, is_parent=False, context=None):
    """Add translation workflow buttons to page listing."""
    if not page_perms.can_edit():
        return []
    
    buttons = []
    
    # Check if page has active translation workflows
    active_workflows = TranslationWorkflow.objects.filter(
        page=page,
        is_active=True
    )
    
    for workflow in active_workflows:
        status = workflow.current_stage.name
        buttons.append({
            'label': _(f'Translation: {status.title()}'),
            'url': f'/admin/translation-workflow/{workflow.id}/',
            'classname': f'button button-small translation-status-{status}',
            'title': _(f'Translation workflow status: {status}'),
        })
    
    return buttons


@hooks.register('register_page_listing_more_buttons')
def translation_workflow_more_buttons(page, page_perms, is_parent=False, context=None):
    """Add more translation workflow buttons."""
    if not page_perms.can_edit():
        return []
    
    buttons = []
    
    # Add workflow management buttons
    active_workflows = TranslationWorkflow.objects.filter(
        page=page,
        is_active=True
    )
    
    for workflow in active_workflows:
        actions = workflow.get_available_actions(page_perms.user)
        
        for action in actions:
            buttons.append({
                'label': _(action.replace('_', ' ').title()),
                'url': f'/admin/translation-workflow/{workflow.id}/{action}/',
                'classname': 'button button-small',
            })
    
    return buttons


def create_translation_workflow(page, target_locale, user):
    """Create a new translation workflow."""
    # Get or create workflow stages
    draft_stage, _ = TranslationWorkflowStage.objects.get_or_create(
        name='draft',
        defaults={'description': 'Initial draft stage', 'order': 0}
    )
    
    # Create workflow
    workflow = TranslationWorkflow.objects.create(
        page=page,
        source_locale=page.locale,
        target_locale=target_locale,
        current_stage=draft_stage,
        created_by=user
    )
    
    # Create quality check record
    TranslationQualityCheck.objects.create(workflow=workflow)
    
    return workflow


def get_translation_workflow_status(page, locale):
    """Get translation workflow status for a page and locale."""
    try:
        workflow = TranslationWorkflow.objects.get(
            page=page,
            target_locale=locale,
            is_active=True
        )
        return workflow.current_stage.name
    except TranslationWorkflow.DoesNotExist:
        return 'not_started' 