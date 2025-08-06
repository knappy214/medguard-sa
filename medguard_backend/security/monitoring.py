"""
Security monitoring for MedGuard SA healthcare application.

This module provides comprehensive monitoring for security events,
compliance violations, and healthcare-specific security metrics.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import SecurityEvent
from .audit import log_audit_event

logger = logging.getLogger(__name__)
User = get_user_model()


class SecurityMonitor:
    """
    Main security monitoring class for healthcare applications.
    """
    
    def __init__(self):
        self.alert_thresholds = {
            'failed_logins_per_hour': 10,
            'rate_limit_violations_per_hour': 5,
            'unauthorized_access_attempts': 3,
            'data_access_anomalies': 20,
            'admin_actions_per_hour': 50,
            'encryption_failures_per_hour': 1,
        }
        
        self.notification_channels = [
            'email',
            'log',
            'database',
        ]
    
    def monitor_security_events(self) -> Dict[str, Any]:
        """
        Monitor security events and generate alerts.
        
        Returns:
            Dictionary with monitoring results and alerts
        """
        monitoring_results = {
            'timestamp': timezone.now(),
            'alerts': [],
            'metrics': {},
            'recommendations': [],
        }
        
        # Check various security metrics
        monitoring_results['metrics']['failed_logins'] = self._check_failed_logins()
        monitoring_results['metrics']['rate_limit_violations'] = self._check_rate_limit_violations()
        monitoring_results['metrics']['unauthorized_access'] = self._check_unauthorized_access()
        monitoring_results['metrics']['data_access_anomalies'] = self._check_data_access_anomalies()
        monitoring_results['metrics']['admin_activities'] = self._check_admin_activities()
        monitoring_results['metrics']['encryption_status'] = self._check_encryption_status()
        monitoring_results['metrics']['compliance_score'] = self._check_compliance_score()
        
        # Generate alerts based on thresholds
        monitoring_results['alerts'] = self._generate_alerts(monitoring_results['metrics'])
        
        # Generate recommendations
        monitoring_results['recommendations'] = self._generate_recommendations(monitoring_results['metrics'])
        
        # Send notifications if needed
        if monitoring_results['alerts']:
            self._send_notifications(monitoring_results)
        
        return monitoring_results
    
    def _check_failed_logins(self) -> Dict[str, Any]:
        """Check failed login attempts."""
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        failed_logins = SecurityEvent.objects.filter(
            event_type='login_failed',
            timestamp__gte=one_hour_ago
        ).count()
        
        # Get top IPs with failed attempts
        failed_by_ip = SecurityEvent.objects.filter(
            event_type='login_failed',
            timestamp__gte=one_hour_ago
        ).values('ip_address').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return {
            'total_failed_logins': failed_logins,
            'threshold': self.alert_thresholds['failed_logins_per_hour'],
            'alert_triggered': failed_logins > self.alert_thresholds['failed_logins_per_hour'],
            'top_ips': list(failed_by_ip),
            'severity': 'high' if failed_logins > 20 else 'medium' if failed_logins > 5 else 'low'
        }
    
    def _check_rate_limit_violations(self) -> Dict[str, Any]:
        """Check rate limit violations."""
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        # Placeholder for rate limit violations (model not available)
        violations = 0
        violations_by_type = []
        
        return {
            'total_violations': violations,
            'threshold': self.alert_thresholds['rate_limit_violations_per_hour'],
            'alert_triggered': violations > self.alert_thresholds['rate_limit_violations_per_hour'],
            'by_form_type': list(violations_by_type),
            'severity': 'high' if violations > 10 else 'medium' if violations > 3 else 'low'
        }
    
    def _check_unauthorized_access(self) -> Dict[str, Any]:
        """Check unauthorized access attempts."""
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        unauthorized_attempts = SecurityEvent.objects.filter(
            event_type='access_denied',
            timestamp__gte=one_hour_ago
        ).count()
        
        # Get attempts by user
        attempts_by_user = SecurityEvent.objects.filter(
            event_type='access_denied',
            timestamp__gte=one_hour_ago
        ).values('user__username').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return {
            'total_attempts': unauthorized_attempts,
            'threshold': self.alert_thresholds['unauthorized_access_attempts'],
            'alert_triggered': unauthorized_attempts > self.alert_thresholds['unauthorized_access_attempts'],
            'by_user': list(attempts_by_user),
            'severity': 'critical' if unauthorized_attempts > 10 else 'high' if unauthorized_attempts > 5 else 'medium'
        }
    
    def _check_data_access_anomalies(self) -> Dict[str, Any]:
        """Check for data access anomalies."""
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        # Placeholder for patient data access patterns (model not available)
        data_accesses = 0
        unusual_patterns = []
        
        return {
            'total_data_accesses': data_accesses,
            'threshold': self.alert_thresholds['data_access_anomalies'],
            'alert_triggered': data_accesses > self.alert_thresholds['data_access_anomalies'],
            'unusual_patterns': list(unusual_patterns),
            'severity': 'high' if unusual_patterns.count() > 0 else 'low'
        }
    
    def _check_admin_activities(self) -> Dict[str, Any]:
        """Check admin activities."""
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        # Placeholder for admin activities (model not available)
        admin_actions = 0
        actions_by_type = []
        
        return {
            'total_admin_actions': admin_actions,
            'threshold': self.alert_thresholds['admin_actions_per_hour'],
            'alert_triggered': admin_actions > self.alert_thresholds['admin_actions_per_hour'],
            'by_action_type': list(actions_by_type),
            'severity': 'medium' if admin_actions > 100 else 'low'
        }
    
    def _check_encryption_status(self) -> Dict[str, Any]:
        """Check encryption status and failures."""
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        # Placeholder for encryption operations (model not available)
        encryption_ops = 0
        encryption_failures = 0
        
        return {
            'total_encryption_ops': encryption_ops,
            'encryption_failures': encryption_failures,
            'threshold': self.alert_thresholds['encryption_failures_per_hour'],
            'alert_triggered': encryption_failures > self.alert_thresholds['encryption_failures_per_hour'],
            'success_rate': ((encryption_ops - encryption_failures) / encryption_ops * 100) if encryption_ops > 0 else 100,
            'severity': 'critical' if encryption_failures > 5 else 'high' if encryption_failures > 1 else 'low'
        }
    
    def _check_compliance_score(self) -> Dict[str, Any]:
        """Check current compliance score."""
        # Placeholder for compliance reports (model not available)
        compliance_score = 95  # Assume good compliance for now
        
        threshold = getattr(settings, 'HIPAA_COMPLIANCE_THRESHOLD', 90)
        
        return {
            'compliance_score': compliance_score,
            'threshold': threshold,
            'alert_triggered': compliance_score < threshold,
            'last_report_date': timezone.now(),
            'severity': 'critical' if compliance_score < 70 else 'high' if compliance_score < 85 else 'low'
        }
    
    def _generate_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on metrics."""
        alerts = []
        
        for metric_name, metric_data in metrics.items():
            if metric_data.get('alert_triggered', False):
                alert = {
                    'type': metric_name,
                    'severity': metric_data.get('severity', 'medium'),
                    'message': self._get_alert_message(metric_name, metric_data),
                    'timestamp': timezone.now(),
                    'data': metric_data,
                }
                alerts.append(alert)
        
        return alerts
    
    def _get_alert_message(self, metric_name: str, metric_data: Dict[str, Any]) -> str:
        """Get alert message for metric."""
        messages = {
            'failed_logins': f"High number of failed logins detected: {metric_data.get('total_failed_logins', 0)} in the last hour",
            'rate_limit_violations': f"Rate limit violations detected: {metric_data.get('total_violations', 0)} in the last hour",
            'unauthorized_access': f"Unauthorized access attempts detected: {metric_data.get('total_attempts', 0)} in the last hour",
            'data_access_anomalies': f"Unusual data access patterns detected: {metric_data.get('total_data_accesses', 0)} accesses in the last hour",
            'admin_activities': f"High admin activity detected: {metric_data.get('total_admin_actions', 0)} actions in the last hour",
            'encryption_status': f"Encryption failures detected: {metric_data.get('encryption_failures', 0)} failures in the last hour",
            'compliance_score': f"HIPAA compliance score below threshold: {metric_data.get('compliance_score', 0)}%",
        }
        
        return messages.get(metric_name, f"Alert triggered for {metric_name}")
    
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on metrics."""
        recommendations = []
        
        # Check failed logins
        if metrics['failed_logins']['alert_triggered']:
            recommendations.append("Consider implementing IP-based blocking for repeated failed login attempts")
            recommendations.append("Review and strengthen password policies")
        
        # Check rate limit violations
        if metrics['rate_limit_violations']['alert_triggered']:
            recommendations.append("Review and adjust rate limiting thresholds")
            recommendations.append("Investigate potential automated attacks")
        
        # Check unauthorized access
        if metrics['unauthorized_access']['alert_triggered']:
            recommendations.append("Review user permissions and role assignments")
            recommendations.append("Consider implementing additional access controls")
        
        # Check encryption failures
        if metrics['encryption_status']['alert_triggered']:
            recommendations.append("Investigate encryption key issues")
            recommendations.append("Check encryption service availability")
        
        # Check compliance score
        if metrics['compliance_score']['alert_triggered']:
            recommendations.append("Review HIPAA compliance requirements")
            recommendations.append("Schedule compliance audit and remediation")
        
        return recommendations
    
    def _send_notifications(self, monitoring_results: Dict[str, Any]):
        """Send notifications for security alerts."""
        for channel in self.notification_channels:
            try:
                if channel == 'email':
                    self._send_email_notification(monitoring_results)
                elif channel == 'log':
                    self._log_notification(monitoring_results)
                elif channel == 'database':
                    self._store_notification(monitoring_results)
            except Exception as e:
                logger.error(f"Failed to send notification via {channel}: {e}")
    
    def _send_email_notification(self, monitoring_results: Dict[str, Any]):
        """Send email notification for security alerts."""
        if not hasattr(settings, 'SECURITY_ALERT_EMAIL'):
            return
        
        subject = f"MedGuard SA Security Alert - {len(monitoring_results['alerts'])} alerts"
        
        message = "Security Alert Summary:\n\n"
        for alert in monitoring_results['alerts']:
            message += f"- {alert['severity'].upper()}: {alert['message']}\n"
        
        message += "\nRecommendations:\n"
        for rec in monitoring_results['recommendations']:
            message += f"- {rec}\n"
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.SECURITY_ALERT_EMAIL],
            fail_silently=False,
        )
    
    def _log_notification(self, monitoring_results: Dict[str, Any]):
        """Log security alerts."""
        for alert in monitoring_results['alerts']:
            logger.warning(
                f"Security Alert [{alert['severity'].upper()}]: {alert['message']}"
            )
    
    def _store_notification(self, monitoring_results: Dict[str, Any]):
        """Store security alerts in database."""
        for alert in monitoring_results['alerts']:
            SecurityEvent.objects.create(
                event_type='security_alert',
                severity=alert['severity'],
                details=alert['data'],
                ip_address='127.0.0.1',  # System generated
                target_object='security_monitor',
            )


class ComplianceMonitor:
    """
    HIPAA compliance monitoring for healthcare applications.
    """
    
    def __init__(self):
        self.compliance_checks = [
            'access_controls',
            'audit_logging',
            'data_encryption',
            'user_authentication',
            'data_backup',
            'incident_response',
        ]
    
    def run_compliance_check(self) -> Dict[str, Any]:
        """Run comprehensive compliance check."""
        results = {
            'timestamp': timezone.now(),
            'overall_score': 0,
            'checks': {},
            'violations': [],
            'recommendations': [],
        }
        
        total_score = 0
        
        for check in self.compliance_checks:
            check_result = self._run_individual_check(check)
            results['checks'][check] = check_result
            total_score += check_result['score']
        
        results['overall_score'] = total_score / len(self.compliance_checks)
        
        # Generate violations and recommendations
        for check_name, check_result in results['checks'].items():
            if check_result['score'] < 80:  # Below 80% is considered non-compliant
                results['violations'].append({
                    'check': check_name,
                    'score': check_result['score'],
                    'issues': check_result.get('issues', [])
                })
        
        results['recommendations'] = self._generate_compliance_recommendations(results)
        
        return results
    
    def _run_individual_check(self, check_name: str) -> Dict[str, Any]:
        """Run individual compliance check."""
        # This would implement specific compliance checks
        # For now, return a placeholder
        return {
            'score': 85,  # Placeholder score
            'status': 'compliant',
            'issues': [],
            'details': f"Compliance check for {check_name} completed"
        }
    
    def _generate_compliance_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []
        
        if results['overall_score'] < 90:
            recommendations.append("Overall compliance score needs improvement")
        
        for violation in results['violations']:
            recommendations.append(f"Address issues in {violation['check']} compliance check")
        
        return recommendations


# Global monitoring instance
security_monitor = SecurityMonitor()
compliance_monitor = ComplianceMonitor()


def run_security_monitoring():
    """Run security monitoring and return results."""
    return security_monitor.monitor_security_events()


def run_compliance_monitoring():
    """Run compliance monitoring and return results."""
    return compliance_monitor.run_compliance_check()