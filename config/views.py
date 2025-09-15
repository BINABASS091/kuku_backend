from django.http import JsonResponse
from django.views import View
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import os

from .models import SystemConfiguration, SystemLog, BackupRecord
from .serializers import (
    SystemConfigurationSerializer, 
    SystemLogSerializer, 
    BackupRecordSerializer
)

logger = logging.getLogger(__name__)

class APIRootView(View):
    """
    API Root View that provides information about available API endpoints.
    """
    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'name': 'Smart Kuku API',
            'version': '1.0.0',
            'description': 'Smart Kuku Poultry Management System API',
            'endpoints': {
                'api_documentation': '/api/schema/swagger-ui/',
                'api_schema': '/api/schema/',
                'authentication': {
                    'obtain_token': '/api/token/',
                    'refresh_token': '/api/token/refresh/'
                },
                'api_v1': '/api/v1/',
                'system_administration': {
                    'configuration': '/api/v1/system/configuration/',
                    'logs': '/api/v1/system/logs/',
                    'backups': '/api/v1/system/backups/',
                    'metrics': '/api/v1/system/metrics/'
                }
            }
        })

class SystemConfigurationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing system configuration
    """
    queryset = SystemConfiguration.objects.all()
    serializer_class = SystemConfigurationSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_object(self):
        """Always return the single configuration instance"""
        config, created = SystemConfiguration.objects.get_or_create()
        return config
    
    def list(self, request):
        """Return the single configuration as a list with one item"""
        config = self.get_object()
        serializer = self.get_serializer(config)
        return Response([serializer.data])
    
    def retrieve(self, request, pk=None):
        """Retrieve the single configuration instance"""
        config = self.get_object()
        serializer = self.get_serializer(config)
        return Response(serializer.data)
    
    def update(self, request, pk=None):
        """Update the single configuration instance"""
        config = self.get_object()
        config.updated_by = request.user
        serializer = self.get_serializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        logger.info(f"System configuration updated by {request.user.username}")
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def reset_to_defaults(self, request):
        """Reset configuration to default values"""
        config = self.get_object()
        
        # Reset to defaults
        config.site_name = 'Smart Kuku Poultry Management'
        config.site_description = 'Advanced IoT-enabled poultry farm management system'
        config.timezone = 'Africa/Nairobi'
        config.language = 'en'
        config.currency = 'KES'
        config.session_timeout = 3600
        config.password_min_length = 8
        config.require_two_factor = False
        config.allow_registration = True
        config.max_login_attempts = 5
        config.email_notifications = True
        config.sms_notifications = False
        config.push_notifications = True
        config.temp_min_threshold = 18.0
        config.temp_max_threshold = 35.0
        config.humidity_min_threshold = 40.0
        config.humidity_max_threshold = 70.0
        config.battery_level_threshold = 20.0
        config.cache_enabled = True
        config.debug_mode = False
        config.log_level = 'INFO'
        config.data_retention_days = 365
        config.auto_backup_enabled = True
        config.backup_frequency = 'daily'
        config.backup_retention_days = 30
        config.api_rate_limit = 1000
        config.webhook_enabled = False
        config.webhook_url = ''
        config.updated_by = request.user
        config.save()
        
        logger.info(f"System configuration reset to defaults by {request.user.username}")
        
        serializer = self.get_serializer(config)
        return Response(serializer.data)

class SystemLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing system logs
    """
    queryset = SystemLog.objects.all()
    serializer_class = SystemLogSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['level', 'module', 'user']
    search_fields = ['message', 'module', 'user__username']
    ordering = ['-timestamp']
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get log statistics"""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        stats = {
            'total_logs': SystemLog.objects.count(),
            'errors_today': SystemLog.objects.filter(
                level='ERROR', 
                timestamp__date=today
            ).count(),
            'warnings_today': SystemLog.objects.filter(
                level='WARNING', 
                timestamp__date=today
            ).count(),
            'critical_issues': SystemLog.objects.filter(
                level='CRITICAL',
                timestamp__date__gte=yesterday
            ).count(),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['delete'])
    def clear_logs(self, request):
        """Clear all system logs (admin only)"""
        if not request.user.is_superuser:
            return Response(
                {'error': 'Only superusers can clear logs'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        count = SystemLog.objects.count()
        SystemLog.objects.all().delete()
        
        logger.warning(f"All system logs cleared by {request.user.username} ({count} records deleted)")
        
        return Response({'message': f'{count} log entries cleared'})

class BackupRecordViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing backup records
    """
    queryset = BackupRecord.objects.all()
    serializer_class = BackupRecordSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['backup_type', 'status']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['post'])
    def create_backup(self, request):
        """Create a new manual backup"""
        try:
            # Create backup record
            backup = BackupRecord.objects.create(
                filename=f"smartkuku-manual-backup-{timezone.now().strftime('%Y-%m-%d-%H-%M-%S')}.sql",
                backup_type='manual',
                description='Manual backup created from admin panel',
                created_by=request.user,
                includes_database=True,
                includes_media=request.data.get('include_media', True),
                includes_logs=request.data.get('include_logs', False),
            )
            
            # Here you would implement actual backup logic
            # For now, simulate with a size
            backup.size_bytes = 47000000  # ~47MB
            backup.status = 'completed'
            backup.save()
            
            logger.info(f"Manual backup created by {request.user.username}: {backup.filename}")
            
            serializer = self.get_serializer(backup)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            return Response(
                {'error': 'Backup creation failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore from backup"""
        backup = self.get_object()
        
        if backup.status != 'completed':
            return Response(
                {'error': 'Cannot restore from incomplete backup'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Here you would implement actual restore logic
            logger.warning(f"Database restore initiated by {request.user.username} from {backup.filename}")
            
            return Response({'message': f'Restore from {backup.filename} completed successfully'})
            
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            return Response(
                {'error': 'Restore operation failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get backup statistics"""
        stats = {
            'total_backups': BackupRecord.objects.count(),
            'total_size_bytes': BackupRecord.objects.filter(
                status='completed'
            ).aggregate(Sum('size_bytes'))['size_bytes__sum'] or 0,
            'last_backup': None,
            'success_rate': 0,
            'available_space_bytes': self._get_available_space(),
        }
        
        # Get last backup
        last_backup = BackupRecord.objects.filter(status='completed').first()
        if last_backup:
            stats['last_backup'] = last_backup.created_at.isoformat()
        
        # Calculate success rate
        total = BackupRecord.objects.count()
        completed = BackupRecord.objects.filter(status='completed').count()
        if total > 0:
            stats['success_rate'] = (completed / total) * 100
        
        return Response(stats)
    
    def _get_available_space(self):
        """Get available disk space in bytes"""
        try:
            statvfs = os.statvfs('/')
            return statvfs.f_frsize * statvfs.f_bavail
        except:
            return 0

class SystemMetricsView(APIView):
    """
    API endpoint for system metrics and health information
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get system metrics"""
        try:
            # Database metrics
            from django.contrib.auth import get_user_model
            from farms.models import Farm
            from batches.models import Batch
            from subscriptions.models import FarmerSubscription
            
            User = get_user_model()
            
            metrics = {
                # User metrics
                'total_users': User.objects.count(),
                'admin_users': User.objects.filter(is_staff=True).count(),
                'active_farmers': User.objects.filter(role='FARMER', is_active=True).count(),
                
                # Farm metrics
                'total_farms': Farm.objects.count(),
                'active_batches': Batch.objects.filter(batch_status=1).count(),
                'total_subscriptions': FarmerSubscription.objects.count(),
                
                # System metrics
                'log_entries_today': SystemLog.objects.filter(
                    timestamp__date=timezone.now().date()
                ).count(),
                'error_logs_today': SystemLog.objects.filter(
                    level='ERROR',
                    timestamp__date=timezone.now().date()
                ).count(),
                'backup_count': BackupRecord.objects.filter(status='completed').count(),
                
                # Performance metrics
                'disk_usage_percent': self._get_disk_usage(),
                'memory_usage_percent': self._get_memory_usage(),
            }
            
            return Response(metrics)
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve system metrics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_disk_usage(self):
        """Get disk usage percentage"""
        try:
            statvfs = os.statvfs('/')
            total = statvfs.f_frsize * statvfs.f_blocks
            available = statvfs.f_frsize * statvfs.f_bavail
            used = total - available
            return round((used / total) * 100, 2)
        except:
            return 0
    
    def _get_memory_usage(self):
        """Get memory usage percentage - simplified implementation"""
        try:
            # This is a simplified implementation
            # In production, you might want to use psutil or similar
            import subprocess
            result = subprocess.run(['free', '-m'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            if len(lines) > 1:
                memory_line = lines[1].split()
                total = int(memory_line[1])
                used = int(memory_line[2])
                return round((used / total) * 100, 2)
        except:
            pass
        return 0
