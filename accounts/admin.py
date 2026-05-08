from django.contrib import admin
from .models import Employee, Attendance, LeaveRequest, Performance, Document


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'user', 'department', 'position', 'is_active']
    list_filter = ['department', 'position', 'is_active', 'date_joined']
    search_fields = ['user__username', 'user__email', 'employee_id', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'employee_id')
        }),
        ('Employment Details', {
            'fields': ('department', 'position', 'manager', 'salary', 'date_joined')
        }),
        ('Personal Information', {
            'fields': ('phone_number', 'gender', 'date_of_birth', 'profile_photo')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'zip_code'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'status', 'check_in_time', 'check_out_time']
    list_filter = ['status', 'date', 'employee__department']
    search_fields = ['employee__user__username', 'employee__employee_id']
    date_hierarchy = 'date'
    readonly_fields = ['created_at']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'status', 'days_requested']
    list_filter = ['leave_type', 'status', 'start_date']
    search_fields = ['employee__user__username', 'employee__employee_id']
    readonly_fields = ['created_at', 'updated_at', 'approval_date']
    actions = ['approve_leaves', 'reject_leaves']
    
    def approve_leaves(self, request, queryset):
        updated = queryset.update(status='A', approved_by=request.user, approval_date=timezone.now())
        self.message_user(request, f'{updated} leave request(s) approved.')
    approve_leaves.short_description = "Approve selected leave requests"
    
    def reject_leaves(self, request, queryset):
        updated = queryset.update(status='R')
        self.message_user(request, f'{updated} leave request(s) rejected.')
    reject_leaves.short_description = "Reject selected leave requests"


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'review_date', 'rating', 'reviewer']
    list_filter = ['rating', 'review_date', 'employee__department']
    search_fields = ['employee__user__username', 'employee__employee_id']
    readonly_fields = ['created_at']
    date_hierarchy = 'review_date'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'document_type', 'title', 'uploaded_date']
    list_filter = ['document_type', 'uploaded_date', 'employee__department']
    search_fields = ['employee__user__username', 'title']
    readonly_fields = ['uploaded_date']
    date_hierarchy = 'uploaded_date'


from django.utils import timezone
