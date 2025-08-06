"""
Django management command for security monitoring.

This command runs security monitoring checks and can be scheduled
to run periodically for continuous security monitoring.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.core.cache import cache
import json

from security.monitoring import run_security_monitoring, run_compliance_monitoring


class Command(BaseCommand):
    """
    Management command for security monitoring.
    """
    
    help = 'Run security monitoring checks for MedGuard SA'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--type',
            type=str,
            choices=['security', 'compliance', 'all'],
            default='all',
            help='Type of monitoring to run'
        )
        
        parser.add_argument(
            '--output',
            type=str,
            choices=['console', 'json', 'file'],
            default='console',
            help='Output format for monitoring results'
        )
        
        parser.add_argument(
            '--output-file',
            type=str,
            help='File path for output (when using --output file)'
        )
        
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Run monitoring continuously (for daemon mode)'
        )
        
        parser.add_argument(
            '--interval',
            type=int,
            default=300,  # 5 minutes
            help='Interval in seconds for continuous monitoring'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        self.monitoring_type = options['type']
        self.output_format = options['output']
        self.output_file = options.get('output_file')
        self.continuous = options['continuous']
        self.interval = options['interval']
        
        if self.continuous:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Starting continuous monitoring (interval: {self.interval}s)...'
                )
            )
            self._run_continuous_monitoring()
        else:
            self.stdout.write(
                self.style.SUCCESS('Running security monitoring checks...')
            )
            self._run_single_monitoring()
    
    def _run_single_monitoring(self):
        """Run a single monitoring check."""
        try:
            results = {}
            
            if self.monitoring_type in ['security', 'all']:
                self.stdout.write('Running security monitoring...')
                results['security'] = run_security_monitoring()
            
            if self.monitoring_type in ['compliance', 'all']:
                self.stdout.write('Running compliance monitoring...')
                results['compliance'] = run_compliance_monitoring()
            
            # Output results
            self._output_results(results)
            
            # Summary
            self._display_summary(results)
            
        except Exception as e:
            raise CommandError(f'Monitoring failed: {e}')
    
    def _run_continuous_monitoring(self):
        """Run continuous monitoring."""
        import time
        
        try:
            while True:
                self.stdout.write(
                    f'\n{timezone.now().strftime("%Y-%m-%d %H:%M:%S")} - Running monitoring cycle...'
                )
                
                self._run_single_monitoring()
                
                self.stdout.write(f'Sleeping for {self.interval} seconds...')
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS('\nContinuous monitoring stopped.')
            )
        except Exception as e:
            raise CommandError(f'Continuous monitoring failed: {e}')
    
    def _output_results(self, results: dict):
        """Output monitoring results in specified format."""
        if self.output_format == 'console':
            self._output_console(results)
        elif self.output_format == 'json':
            self._output_json(results)
        elif self.output_format == 'file':
            self._output_file(results)
    
    def _output_console(self, results: dict):
        """Output results to console."""
        for monitoring_type, data in results.items():
            self.stdout.write(
                self.style.SUCCESS(f'\n=== {monitoring_type.upper()} MONITORING RESULTS ===')
            )
            
            if monitoring_type == 'security':
                self._display_security_results(data)
            elif monitoring_type == 'compliance':
                self._display_compliance_results(data)
    
    def _display_security_results(self, data: dict):
        """Display security monitoring results."""
        # Display alerts
        if data.get('alerts'):
            self.stdout.write(self.style.ERROR('\nSECURITY ALERTS:'))
            for alert in data['alerts']:
                severity_style = self._get_severity_style(alert['severity'])
                self.stdout.write(
                    severity_style(f"  [{alert['severity'].upper()}] {alert['message']}")
                )
        else:
            self.stdout.write(self.style.SUCCESS('  No security alerts'))
        
        # Display metrics
        self.stdout.write('\nSECURITY METRICS:')
        for metric_name, metric_data in data.get('metrics', {}).items():
            if isinstance(metric_data, dict):
                value = metric_data.get('total_failed_logins') or \
                       metric_data.get('total_violations') or \
                       metric_data.get('total_attempts') or \
                       metric_data.get('total_data_accesses') or \
                       metric_data.get('total_admin_actions') or \
                       metric_data.get('encryption_failures') or \
                       metric_data.get('compliance_score', 'N/A')
                
                self.stdout.write(f"  {metric_name}: {value}")
        
        # Display recommendations
        if data.get('recommendations'):
            self.stdout.write('\nRECOMMENDATIONS:')
            for rec in data['recommendations']:
                self.stdout.write(f"  - {rec}")
    
    def _display_compliance_results(self, data: dict):
        """Display compliance monitoring results."""
        score = data.get('overall_score', 0)
        score_style = self.style.SUCCESS if score >= 90 else self.style.WARNING if score >= 80 else self.style.ERROR
        
        self.stdout.write(
            score_style(f'  Overall Compliance Score: {score:.1f}%')
        )
        
        # Display violations
        if data.get('violations'):
            self.stdout.write(self.style.ERROR('\nCOMPLIANCE VIOLATIONS:'))
            for violation in data['violations']:
                self.stdout.write(
                    self.style.ERROR(f"  {violation['check']}: {violation['score']}%")
                )
        else:
            self.stdout.write(self.style.SUCCESS('  No compliance violations'))
        
        # Display recommendations
        if data.get('recommendations'):
            self.stdout.write('\nCOMPLIANCE RECOMMENDATIONS:')
            for rec in data['recommendations']:
                self.stdout.write(f"  - {rec}")
    
    def _output_json(self, results: dict):
        """Output results as JSON."""
        # Convert datetime objects to strings for JSON serialization
        json_results = self._serialize_for_json(results)
        print(json.dumps(json_results, indent=2, default=str))
    
    def _output_file(self, results: dict):
        """Output results to file."""
        if not self.output_file:
            raise CommandError('--output-file required when using --output file')
        
        json_results = self._serialize_for_json(results)
        
        with open(self.output_file, 'w') as f:
            json.dump(json_results, f, indent=2, default=str)
        
        self.stdout.write(
            self.style.SUCCESS(f'Results written to {self.output_file}')
        )
    
    def _serialize_for_json(self, data):
        """Serialize data for JSON output."""
        if isinstance(data, dict):
            return {k: self._serialize_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_for_json(item) for item in data]
        elif hasattr(data, 'isoformat'):  # datetime objects
            return data.isoformat()
        else:
            return data
    
    def _display_summary(self, results: dict):
        """Display monitoring summary."""
        self.stdout.write(self.style.SUCCESS('\n=== MONITORING SUMMARY ==='))
        
        total_alerts = 0
        critical_alerts = 0
        
        if 'security' in results:
            security_alerts = len(results['security'].get('alerts', []))
            total_alerts += security_alerts
            
            critical_alerts += len([
                alert for alert in results['security'].get('alerts', [])
                if alert.get('severity') == 'critical'
            ])
            
            self.stdout.write(f'Security Alerts: {security_alerts}')
        
        if 'compliance' in results:
            compliance_score = results['compliance'].get('overall_score', 0)
            violations = len(results['compliance'].get('violations', []))
            
            self.stdout.write(f'Compliance Score: {compliance_score:.1f}%')
            self.stdout.write(f'Compliance Violations: {violations}')
        
        # Overall status
        if critical_alerts > 0:
            status_style = self.style.ERROR
            status = 'CRITICAL'
        elif total_alerts > 0:
            status_style = self.style.WARNING
            status = 'WARNING'
        else:
            status_style = self.style.SUCCESS
            status = 'OK'
        
        self.stdout.write(
            status_style(f'\nOverall Status: {status}')
        )
    
    def _get_severity_style(self, severity: str):
        """Get style for severity level."""
        styles = {
            'low': self.style.SUCCESS,
            'medium': self.style.WARNING,
            'high': self.style.ERROR,
            'critical': self.style.ERROR,
        }
        return styles.get(severity, self.style.SUCCESS)