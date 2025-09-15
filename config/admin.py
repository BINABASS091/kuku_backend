from django.contrib import admin
from .models import SystemConfiguration, SystemLog, BackupRecord

@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'timezone', 'language', 'currency', 'updated_at', 'updated_by']
    fieldsets = (
        ('General Settings', {
            'fields': ('site_name', 'site_description', 'timezone', 'language', 'currency')
        }),
        ('Security Settings', {
            'fields': ('session_timeout', 'password_min_length', 'require_two_factor', 
                      'allow_registration', 'max_login_attempts')
        }),
        ('Notification Settings', {
            'fields': ('email_notifications', 'sms_notifications', 'push_notifications')
        }),
        ('Alert Thresholds', {
            'fields': ('temp_min_threshold', 'temp_max_threshold', 'humidity_min_threshold',
                      'humidity_max_threshold', 'battery_level_threshold')
        }),
        ('Performance Settings', {
            'fields': ('cache_enabled', 'debug_mode', 'log_level', 'data_retention_days')
        }),
        ('Backup Settings', {
            'fields': ('auto_backup_enabled', 'backup_frequency', 'backup_retention_days')
        }),
        ('Integration Settings', {
            'fields': ('api_rate_limit', 'webhook_enabled', 'webhook_url')
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'level', 'module', 'message_truncated', 'user', 'ip_address']
    list_filter = ['level', 'module', 'timestamp']
    search_fields = ['message', 'module', 'user__username']
    readonly_fields = ['timestamp', 'level', 'module', 'message', 'user', 'ip_address', 'details']
    date_hierarchy = 'timestamp'
    
    def message_truncated(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_truncated.short_description = 'Message'
    
    def has_add_permission(self, request):
        return False  # Logs are created programmatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs should not be modified

@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    list_display = ['filename', 'created_at', 'size_formatted', 'backup_type', 'status', 'created_by']
    list_filter = ['backup_type', 'status', 'created_at']
    search_fields = ['filename', 'description']
    readonly_fields = ['created_at', 'size_formatted']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Backup Information', {
            'fields': ('filename', 'description', 'file_path', 'created_at', 'created_by')
        }),
        ('Backup Details', {
            'fields': ('backup_type', 'status', 'size_bytes', 'size_formatted')
        }),
        ('Content Included', {
            'fields': ('includes_database', 'includes_media', 'includes_logs')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ['collapse']
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
