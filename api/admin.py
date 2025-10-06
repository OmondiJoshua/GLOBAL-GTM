from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Report, ReportData

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = [
        'username', 'email', 'first_name', 'last_name', 
        'role', 'county', 'sublocation', 'employee_id', 'is_active'
    ]
    list_filter = ['role', 'county', 'sublocation', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'employee_id']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('role', 'county', 'sublocation', 'phone_number', 'employee_id')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': ('role', 'county', 'sublocation', 'phone_number', 'email')
        }),
    )

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'county', 'sublocation', 'status', 
        'assigned_to', 'created_by', 'created_at', 'total_entries'
    ]
    list_filter = ['status', 'county', 'sublocation', 'created_at']
    search_fields = ['title', 'description', 'county', 'sublocation']
    readonly_fields = ['total_entries', 'active_rate', 'completion_rate', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'status')
        }),
        ('Location & Assignment', {
            'fields': ('county', 'sublocation', 'assigned_to', 'created_by')
        }),
        ('Statistics', {
            'fields': ('total_entries', 'active_rate', 'completion_rate')
        }),
        ('Feedback', {
            'fields': ('manager_feedback',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ReportData)
class ReportDataAdmin(admin.ModelAdmin):
    list_display = [
        'entry_number', 'customer_name', 'customer_phone', 'location',
        'service_type', 'priority', 'status', 'is_active', 'created_at'
    ]
    list_filter = ['service_type', 'priority', 'status', 'is_active', 'created_at']
    search_fields = ['entry_number', 'customer_name', 'customer_phone', 'location']
    readonly_fields = ['entry_number', 'is_active', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('report', 'entry_number', 'customer_name', 'customer_phone', 'location')
        }),
        ('Service Details', {
            'fields': ('service_type', 'priority', 'status', 'is_active')
        }),
        ('Feedback', {
            'fields': ('agent_feedback', 'supervisor_feedback')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('report')