from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()

class SystemConfiguration(models.Model):
    """
    System-wide configuration settings
    """
    TIMEZONE_CHOICES = [
        ('Africa/Nairobi', 'Africa/Nairobi (EAT)'),
        ('UTC', 'UTC'),
        ('Africa/Lagos', 'Africa/Lagos (WAT)'),
        ('Africa/Cairo', 'Africa/Cairo (EET)'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('sw', 'Swahili'),
        ('fr', 'French'),
    ]
    
    CURRENCY_CHOICES = [
        ('KES', 'KES (Kenyan Shilling)'),
        ('USD', 'USD (US Dollar)'),
        ('NGN', 'NGN (Nigerian Naira)'),
        ('EGP', 'EGP (Egyptian Pound)'),
    ]
    
    LOG_LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'), 
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    BACKUP_FREQUENCY_CHOICES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    # General Settings
    site_name = models.CharField(max_length=100, default='Smart Kuku Poultry Management')
    site_description = models.TextField(default='Advanced IoT-enabled poultry farm management system')
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default='Africa/Nairobi')
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='KES')
    
    # Security Settings
    session_timeout = models.IntegerField(default=3600, validators=[MinValueValidator(300)])  # seconds
    password_min_length = models.IntegerField(default=8, validators=[MinValueValidator(6)])
    require_two_factor = models.BooleanField(default=False)
    allow_registration = models.BooleanField(default=True)
    max_login_attempts = models.IntegerField(default=5, validators=[MinValueValidator(1)])
    
    # Notification Settings
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    
    # Alert Thresholds
    temp_min_threshold = models.FloatField(default=18.0)
    temp_max_threshold = models.FloatField(default=35.0)
    humidity_min_threshold = models.FloatField(default=40.0)
    humidity_max_threshold = models.FloatField(default=70.0)
    battery_level_threshold = models.FloatField(default=20.0)
    
    # Performance Settings
    cache_enabled = models.BooleanField(default=True)
    debug_mode = models.BooleanField(default=False)
    log_level = models.CharField(max_length=20, choices=LOG_LEVEL_CHOICES, default='INFO')
    data_retention_days = models.IntegerField(default=365, validators=[MinValueValidator(30)])
    
    # Backup Settings
    auto_backup_enabled = models.BooleanField(default=True)
    backup_frequency = models.CharField(max_length=20, choices=BACKUP_FREQUENCY_CHOICES, default='daily')
    backup_retention_days = models.IntegerField(default=30, validators=[MinValueValidator(7)])
    
    # Integration Settings
    api_rate_limit = models.IntegerField(default=1000, validators=[MinValueValidator(100)])
    webhook_enabled = models.BooleanField(default=False)
    webhook_url = models.URLField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configurations'
        
    def __str__(self):
        return f"System Configuration - {self.site_name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one configuration record exists
        if not self.pk and SystemConfiguration.objects.exists():
            self.pk = SystemConfiguration.objects.first().pk
        super().save(*args, **kwargs)

class SystemLog(models.Model):
    """
    System logging model aligned with Django logging
    """
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    module = models.CharField(max_length=100)
    message = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['level']),
            models.Index(fields=['module']),
        ]
    
    def __str__(self):
        return f"{self.level} - {self.module} - {self.timestamp}"

class BackupRecord(models.Model):
    """
    Track backup files and operations
    """
    TYPE_CHOICES = [
        ('automatic', 'Automatic'),
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled'),
    ]
    
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    size_bytes = models.BigIntegerField(default=0)
    backup_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    description = models.TextField(blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Backup content flags
    includes_database = models.BooleanField(default=True)
    includes_media = models.BooleanField(default=True)
    includes_logs = models.BooleanField(default=False)
    
    # Metadata
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Backup Record'
        verbose_name_plural = 'Backup Records'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['backup_type']),
        ]
    
    def __str__(self):
        return f"{self.filename} - {self.status}"
    
    @property
    def size_formatted(self):
        """Return human-readable file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.size_bytes < 1024.0:
                return f"{self.size_bytes:.1f} {unit}"
            self.size_bytes /= 1024.0
        return f"{self.size_bytes:.1f} TB"
