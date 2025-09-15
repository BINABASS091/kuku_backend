from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import SystemConfiguration, SystemLog, BackupRecord

User = get_user_model()

class SystemConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for system configuration
    """
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    updated_by_full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemConfiguration
        fields = [
            'id', 'site_name', 'site_description', 'timezone', 'language', 'currency',
            'session_timeout', 'password_min_length', 'require_two_factor',
            'allow_registration', 'max_login_attempts', 'email_notifications',
            'sms_notifications', 'push_notifications', 'temp_min_threshold',
            'temp_max_threshold', 'humidity_min_threshold', 'humidity_max_threshold',
            'battery_level_threshold', 'cache_enabled', 'debug_mode', 'log_level',
            'data_retention_days', 'auto_backup_enabled', 'backup_frequency',
            'backup_retention_days', 'api_rate_limit', 'webhook_enabled',
            'webhook_url', 'created_at', 'updated_at', 'updated_by',
            'updated_by_username', 'updated_by_full_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'updated_by']
    
    def get_updated_by_full_name(self, obj):
        """Get the full name of the user who last updated the configuration"""
        if obj.updated_by:
            return f"{obj.updated_by.first_name} {obj.updated_by.last_name}".strip() or obj.updated_by.username
        return None
    
    def validate_password_min_length(self, value):
        """Validate password minimum length"""
        if value < 6:
            raise serializers.ValidationError("Password minimum length cannot be less than 6 characters")
        if value > 128:
            raise serializers.ValidationError("Password minimum length cannot exceed 128 characters")
        return value
    
    def validate_session_timeout(self, value):
        """Validate session timeout"""
        if value < 300:  # 5 minutes
            raise serializers.ValidationError("Session timeout cannot be less than 5 minutes (300 seconds)")
        if value > 86400:  # 24 hours
            raise serializers.ValidationError("Session timeout cannot exceed 24 hours (86400 seconds)")
        return value
    
    def validate_api_rate_limit(self, value):
        """Validate API rate limit"""
        if value < 10:
            raise serializers.ValidationError("API rate limit cannot be less than 10 requests per hour")
        if value > 100000:
            raise serializers.ValidationError("API rate limit cannot exceed 100,000 requests per hour")
        return value
    
    def validate_webhook_url(self, value):
        """Validate webhook URL format"""
        if value and not (value.startswith('http://') or value.startswith('https://')):
            raise serializers.ValidationError("Webhook URL must start with http:// or https://")
        return value
    
    def validate(self, attrs):
        """Validate temperature and humidity thresholds"""
        temp_min = attrs.get('temp_min_threshold', getattr(self.instance, 'temp_min_threshold', None))
        temp_max = attrs.get('temp_max_threshold', getattr(self.instance, 'temp_max_threshold', None))
        humidity_min = attrs.get('humidity_min_threshold', getattr(self.instance, 'humidity_min_threshold', None))
        humidity_max = attrs.get('humidity_max_threshold', getattr(self.instance, 'humidity_max_threshold', None))
        
        if temp_min is not None and temp_max is not None:
            if temp_min >= temp_max:
                raise serializers.ValidationError({
                    'temp_min_threshold': 'Minimum temperature must be less than maximum temperature'
                })
        
        if humidity_min is not None and humidity_max is not None:
            if humidity_min >= humidity_max:
                raise serializers.ValidationError({
                    'humidity_min_threshold': 'Minimum humidity must be less than maximum humidity'
                })
        
        return attrs

class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal user serializer for use in other serializers
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

class SystemLogSerializer(serializers.ModelSerializer):
    """
    Serializer for system logs
    """
    user_detail = UserMinimalSerializer(source='user', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    timestamp_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemLog
        fields = [
            'id', 'timestamp', 'timestamp_formatted', 'level', 'level_display',
            'module', 'message', 'details', 'ip_address', 'user_agent',
            'user', 'user_detail'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_timestamp_formatted(self, obj):
        """Format timestamp for display"""
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')

class BackupRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for backup records
    """
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    backup_type_display = serializers.CharField(source='get_backup_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    size_formatted = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = BackupRecord
        fields = [
            'id', 'filename', 'filepath', 'backup_type', 'backup_type_display',
            'status', 'status_display', 'size_bytes', 'size_formatted',
            'description', 'error_message', 'includes_database', 'includes_media',
            'includes_logs', 'created_at', 'created_at_formatted', 'completed_at',
            'created_by', 'created_by_detail', 'duration'
        ]
        read_only_fields = [
            'id', 'filepath', 'size_bytes', 'error_message', 'created_at', 'completed_at'
        ]
    
    def get_size_formatted(self, obj):
        """Format file size for human reading"""
        if not obj.size_bytes:
            return "0 B"
        
        size = obj.size_bytes
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def get_created_at_formatted(self, obj):
        """Format creation timestamp for display"""
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    
    def get_duration(self, obj):
        """Calculate backup duration in seconds"""
        if obj.completed_at and obj.created_at:
            delta = obj.completed_at - obj.created_at
            return delta.total_seconds()
        return None

class SystemMetricsSerializer(serializers.Serializer):
    """
    Serializer for system metrics (read-only)
    """
    total_users = serializers.IntegerField()
    admin_users = serializers.IntegerField()
    active_farmers = serializers.IntegerField()
    total_farms = serializers.IntegerField()
    active_batches = serializers.IntegerField()
    total_subscriptions = serializers.IntegerField()
    log_entries_today = serializers.IntegerField()
    error_logs_today = serializers.IntegerField()
    backup_count = serializers.IntegerField()
    disk_usage_percent = serializers.FloatField()
    memory_usage_percent = serializers.FloatField()

class LogStatsSerializer(serializers.Serializer):
    """
    Serializer for log statistics (read-only)
    """
    total_logs = serializers.IntegerField()
    errors_today = serializers.IntegerField()
    warnings_today = serializers.IntegerField()
    critical_issues = serializers.IntegerField()

class BackupStatsSerializer(serializers.Serializer):
    """
    Serializer for backup statistics (read-only)
    """
    total_backups = serializers.IntegerField()
    total_size_bytes = serializers.IntegerField()
    last_backup = serializers.DateTimeField(allow_null=True)
    success_rate = serializers.FloatField()
    available_space_bytes = serializers.IntegerField()
