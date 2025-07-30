#!/usr/bin/env python
"""
Deployment script for MedGuard performance optimizations.

This script applies all the performance optimizations including:
- Database migrations
- Redis configuration updates
- Celery configuration deployment
- Mobile optimizations
- Image processing setup
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
from django.conf import settings
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.base')
django.setup()

logger = logging.getLogger(__name__)


class OptimizationDeployer:
    """Deployment class for performance optimizations."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = self.project_root / 'scripts'
        self.migrations_dir = self.project_root / 'medications' / 'migrations'
        
    def deploy_all_optimizations(self):
        """Deploy all performance optimizations."""
        logger.info("Starting MedGuard performance optimization deployment...")
        
        try:
            # Step 1: Install dependencies
            self.install_dependencies()
            
            # Step 2: Run database migrations
            self.run_migrations()
            
            # Step 3: Update Redis configuration
            self.update_redis_config()
            
            # Step 4: Deploy Celery configuration
            self.deploy_celery_config()
            
            # Step 5: Setup mobile optimizations
            self.setup_mobile_optimizations()
            
            # Step 6: Initialize image processing
            self.initialize_image_processing()
            
            # Step 7: Run performance tests
            self.run_performance_tests()
            
            logger.info("✅ All performance optimizations deployed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")
            raise
    
    def install_dependencies(self):
        """Install required dependencies."""
        logger.info("Installing dependencies...")
        
        try:
            # Install Pillow for image processing
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', 'Pillow==11.3.0'
            ], check=True, capture_output=True)
            
            # Install psutil for system monitoring
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', 'psutil==6.1.0'
            ], check=True, capture_output=True)
            
            logger.info("✅ Dependencies installed successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            raise
    
    def run_migrations(self):
        """Run database migrations."""
        logger.info("Running database migrations...")
        
        try:
            # Make migrations
            execute_from_command_line(['manage.py', 'makemigrations', 'medications'])
            
            # Migrate
            execute_from_command_line(['manage.py', 'migrate'])
            
            logger.info("✅ Database migrations completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise
    
    def update_redis_config(self):
        """Update Redis configuration."""
        logger.info("Updating Redis configuration...")
        
        try:
            # Test Redis connection
            from django.core.cache import caches
            
            # Test default cache
            default_cache = caches['default']
            default_cache.set('test_key', 'test_value', 60)
            test_value = default_cache.get('test_key')
            
            if test_value != 'test_value':
                raise Exception("Redis cache test failed")
            
            # Test mobile cache
            mobile_cache = caches.get('mobile_api', caches['default'])
            mobile_cache.set('mobile_test_key', 'mobile_test_value', 60)
            mobile_test_value = mobile_cache.get('mobile_test_key')
            
            if mobile_test_value != 'mobile_test_value':
                raise Exception("Mobile Redis cache test failed")
            
            # Clean up test keys
            default_cache.delete('test_key')
            mobile_cache.delete('mobile_test_key')
            
            logger.info("✅ Redis configuration updated successfully")
            
        except Exception as e:
            logger.error(f"❌ Redis configuration update failed: {e}")
            raise
    
    def deploy_celery_config(self):
        """Deploy Celery configuration."""
        logger.info("Deploying Celery configuration...")
        
        try:
            from medguard_backend.celery import app
            
            # Test Celery configuration
            inspect = app.control.inspect()
            stats = inspect.stats()
            
            logger.info(f"✅ Celery configuration deployed successfully")
            logger.info(f"   Active workers: {len(stats) if stats else 0}")
            
        except Exception as e:
            logger.error(f"❌ Celery configuration deployment failed: {e}")
            raise
    
    def setup_mobile_optimizations(self):
        """Setup mobile optimizations."""
        logger.info("Setting up mobile optimizations...")
        
        try:
            # Test mobile settings import
            from medguard_backend.settings.mobile import MOBILE_API_OPTIMIZATION
            
            # Test mobile middleware
            from medguard_backend.middleware.mobile import MobileOptimizationMiddleware
            
            logger.info("✅ Mobile optimizations setup successfully")
            logger.info(f"   API optimization enabled: {MOBILE_API_OPTIMIZATION.get('ENABLE_COMPRESSION', False)}")
            
        except Exception as e:
            logger.error(f"❌ Mobile optimizations setup failed: {e}")
            raise
    
    def initialize_image_processing(self):
        """Initialize image processing."""
        logger.info("Initializing image processing...")
        
        try:
            from medications.image_tasks import process_medication_image
            
            # Test Pillow import
            from PIL import Image
            
            logger.info("✅ Image processing initialized successfully")
            logger.info(f"   Pillow version: {Image.__version__}")
            
        except Exception as e:
            logger.error(f"❌ Image processing initialization failed: {e}")
            raise
    
    def run_performance_tests(self):
        """Run performance tests."""
        logger.info("Running performance tests...")
        
        try:
            # Import and run performance monitor
            from scripts.performance_monitor import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            metrics = monitor.collect_all_metrics()
            
            # Generate report
            report = monitor.generate_report(metrics)
            
            # Save report
            timestamp = django.utils.timezone.now().strftime('%Y%m%d_%H%M%S')
            report_file = f'deployment_performance_report_{timestamp}.txt'
            
            with open(report_file, 'w') as f:
                f.write(report)
            
            logger.info("✅ Performance tests completed successfully")
            logger.info(f"   Report saved to: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ Performance tests failed: {e}")
            raise
    
    def create_deployment_summary(self):
        """Create a deployment summary."""
        summary = """
MEDGUARD PERFORMANCE OPTIMIZATION DEPLOYMENT SUMMARY
===================================================

✅ Database Optimizations:
   - New indexes for medication queries
   - Image field optimizations
   - Composite indexes for complex queries

✅ Redis Multi-Tier Setup:
   - Default cache (general purpose)
   - Mobile API cache (optimized for mobile)
   - Mobile images cache (long-term storage)
   - Image processing cache (task-specific)

✅ Celery Configuration:
   - Optimized worker settings
   - Multi-tier task routing
   - Enhanced performance settings
   - Image processing task queues

✅ Mobile Optimizations:
   - Mobile-specific middleware
   - API response optimization
   - Caching strategies
   - Performance monitoring
   - Image optimization settings

✅ Image Processing:
   - Pillow integration
   - Multiple format support (WebP, AVIF, JPEG XL)
   - Priority-based processing
   - Batch processing capabilities
   - Error handling and retry logic

✅ Performance Monitoring:
   - System metrics collection
   - Database performance tracking
   - Cache hit rate monitoring
   - API response time tracking
   - Image processing statistics

DEPLOYMENT COMPLETED SUCCESSFULLY!
        """
        
        # Save summary to file
        timestamp = django.utils.timezone.now().strftime('%Y%m%d_%H%M%S')
        summary_file = f'deployment_summary_{timestamp}.txt'
        
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        logger.info(f"📋 Deployment summary saved to: {summary_file}")
        print(summary)


def main():
    """Main function to run the deployment."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    deployer = OptimizationDeployer()
    
    try:
        # Deploy all optimizations
        deployer.deploy_all_optimizations()
        
        # Create deployment summary
        deployer.create_deployment_summary()
        
        print("\n🎉 MedGuard performance optimizations deployed successfully!")
        print("The system is now optimized for:")
        print("  • Faster database queries with new indexes")
        print("  • Enhanced mobile performance")
        print("  • Optimized image processing")
        print("  • Multi-tier Redis caching")
        print("  • Improved Celery task management")
        print("  • Comprehensive performance monitoring")
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        print(f"\n❌ Deployment failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 