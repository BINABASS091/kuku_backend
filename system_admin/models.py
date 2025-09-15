from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class SystemConfiguration(models.Model):
    """System-wide configuration settings"""
    
    # General Settings
    site_name = models.CharField(max_length=100, default='Smart Kuku Poultry Management')
    site_description = models.TextField(default='Advanced IoT-enabled poultry farm management system')
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    language = models.CharField(max_length=10, default='en')
    date_format = models.CharField(max_length=20, default='DD/MM/YYYY')
    currency = models.CharField(max_length=10, default='KES')
    
    # Security Settings
    session_timeout = models.IntegerField(default=3600, help_text='Session timeout in seconds')
    password_min_length = models.IntegerField(default=8, validators=[MinValueValidator(6), MaxValueValidator(20)])
    require_two_factor = models.BooleanField(default=False)
    allow_registration = models.BooleanField(default=True)
    max_login_attempts = models.IntegerField(default=5, validators=[MinValueValidator(3), MaxValueValidator(10)])
    
    # Notification Settings
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    
    # Alert Thresholds
    temp_min_threshold = models.FloatField(default=18.0, help_text='Minimum temperature threshold (°C)')
    temp_max_threshold = models.FloatField(default=35.0, help_text='Maximum temperature threshold (°C)')
    humidity_min_threshold = models.FloatField(default=40.0, help_text='Minimum humidity threshold (%)')
    humidity_max_threshold = models.FloatField(default=70.0, help_text='Maximum humidity threshold (%)')
    battery_level_threshold = models.FloatField(default=20.0, help_text='Battery level alert threshold (%)')
    
    # Performance Settings
    cache_enabled = models.BooleanField(default=True)
    debug_mode = models.BooleanField(default=False)
    log_level = models.CharField(
        max_length=20, 
        choices=[
            ('DEBUG', 'Debug'),
            ('INFO', 'Info'),
            ('WARNING', 'Warning'),
            ('ERROR', 'Error'),
            ('CRITICAL', 'Critical'),
        ],
        default='INFO'
    )
    backup_frequency = models.CharField(
        max_length=20,
        choices=[
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='daily'
    )
    data_retention_days = models.IntegerField(default=365)
    
    # Integration Settings
    api_rate_limit = models.IntegerField(default=1000, help_text='API requests per hour')
    webhook_enabled = models.BooleanField(default=False)
    webhook_url = models.URLField(blank=True, null=True)
    sms_provider = models.CharField(max_length=50, default='twilio')
    email_provider = models.CharField(max_length=50, default='smtp')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'system_configuration_tb'
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configurations'
    
    def __str__(self):
        return f"System Configuration - {self.site_name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one configuration instance exists
        if not self.pk and SystemConfiguration.objects.exists():
            raise ValueError("Only one SystemConfiguration instance is allowed")
        super().save(*args, **kwargs)
    
    @classmethod
    def get_config(cls):
        """Get the single system configuration instance"""
        config, created = cls.objects.get_or_create(
            defaults={
                'site_name': 'Smart Kuku Poultry Management',
                'site_description': 'Advanced IoT-enabled poultry farm management system'
            }
        )
        return config


class SystemLog(models.Model):
    """System activity and error logs"""
    
    LOG_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    level = models.CharField(max_length=20, choices=LOG_LEVELS, db_index=True)
    message = models.TextField()
    module = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)
    stack_trace = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'system_logs_tb'
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['level', 'timestamp']),
            models.Index(fields=['module', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.level} - {self.module} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class BackupRecord(models.Model):
    """Database backup records and metadata"""
    
    BACKUP_TYPES = [
        ('automatic', 'Automatic'),
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled'),
    ]
    
    BACKUP_STATUS = [
        ('completed', 'Completed'),
        ('in_progress', 'In Progress'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=200)
    file_path = models.CharField(max_length=500)
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPES)
    status = models.CharField(max_length=20, choices=BACKUP_STATUS, default='in_progress')
    file_size = models.BigIntegerField(null=True, blank=True, help_text='File size in bytes')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    include_media = models.BooleanField(default=True)
    include_logs = models.BooleanField(default=False)
    compression_enabled = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'backup_records_tb'
        verbose_name = 'Backup Record'
        verbose_name_plural = 'Backup Records'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} - {self.status}"
    
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    @property
    def duration_seconds(self):
        """Return backup duration in seconds"""
        if self.completed_at and self.created_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None


class SystemMetrics(models.Model):
    """System performance and health metrics"""
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    cpu_usage_percent = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    memory_usage_percent = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    disk_usage_percent = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    database_connections = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    api_requests_per_minute = models.IntegerField(default=0)
    error_count_last_hour = models.IntegerField(default=0)
    response_time_avg_ms = models.FloatField(default=0.0)
    
    # Application-specific metrics
    total_farms = models.IntegerField(default=0)
    total_devices = models.IntegerField(default=0)
    active_sensors = models.IntegerField(default=0)
    total_users = models.IntegerField(default=0)
    active_subscriptions = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'system_metrics_tb'
        verbose_name = 'System Metrics'
        verbose_name_plural = 'System Metrics'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Metrics - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
