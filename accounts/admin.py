from django.contrib import admin
from .models import (
    Employee,
    Attendance,
    LeaveRequest,
    Performance,
    Document,
    PayrollRecord,
    PolicyDocument,
    Project,
    Task,
    RecruitmentCandidate,
    OnboardingTask,
    TrainingCourse,
    TrainingEnrollment,
    Announcement,
    SupportTicket,
    ExpenseClaim,
    TimesheetEntry,
    Holiday,
    Asset,
    FeedbackSurvey,
    SurveyResponse,
    ChatMessage,
    AIRequest,
)


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


@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = ['employee', 'salary_month', 'gross_salary', 'deductions', 'net_salary', 'status']
    list_filter = ['status', 'salary_month']
    search_fields = ['employee__user__username', 'employee__employee_id']
    date_hierarchy = 'salary_month'


@admin.register(PolicyDocument)
class PolicyDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'effective_date', 'is_active']
    list_filter = ['document_type', 'is_active', 'effective_date']
    search_fields = ['title', 'description']
    date_hierarchy = 'effective_date'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'start_date', 'end_date']
    search_fields = ['name', 'manager__user__username']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'assigned_to', 'status', 'priority', 'due_date']
    list_filter = ['status', 'priority', 'due_date']
    search_fields = ['title', 'assigned_to__user__username', 'project__name']
    date_hierarchy = 'due_date'


@admin.register(RecruitmentCandidate)
class RecruitmentCandidateAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'position_applied', 'status', 'applied_on']
    list_filter = ['status', 'applied_on']
    search_fields = ['full_name', 'email', 'position_applied']
    date_hierarchy = 'applied_on'


@admin.register(OnboardingTask)
class OnboardingTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'employee', 'due_date', 'completed']
    list_filter = ['completed', 'due_date']
    search_fields = ['title', 'employee__user__username']
    date_hierarchy = 'due_date'


@admin.register(TrainingCourse)
class TrainingCourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'trainer', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'start_date', 'end_date']
    search_fields = ['title', 'trainer']


@admin.register(TrainingEnrollment)
class TrainingEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['course', 'employee', 'enrolled_on', 'status']
    list_filter = ['status', 'enrolled_on']
    search_fields = ['course__title', 'employee__user__username']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'audience', 'is_active', 'published_date']
    list_filter = ['is_active', 'audience', 'published_date']
    search_fields = ['title', 'content']
    date_hierarchy = 'published_date'


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['subject', 'employee', 'status', 'priority', 'assigned_to', 'updated_at']
    list_filter = ['status', 'priority', 'updated_at']
    search_fields = ['subject', 'employee__user__username']
    date_hierarchy = 'updated_at'


@admin.register(ExpenseClaim)
class ExpenseClaimAdmin(admin.ModelAdmin):
    list_display = ['employee', 'amount', 'status', 'submitted_on', 'approved_by']
    list_filter = ['status', 'submitted_on', 'approved_by']
    search_fields = ['employee__user__username', 'amount', 'reason']
    date_hierarchy = 'submitted_on'


@admin.register(TimesheetEntry)
class TimesheetEntryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'project', 'hours_worked']
    list_filter = ['date', 'project']
    search_fields = ['employee__user__username', 'project__name']
    date_hierarchy = 'date'


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ['name', 'date']
    list_filter = ['date']
    search_fields = ['name']
    date_hierarchy = 'date'


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['name', 'asset_tag', 'category', 'assigned_to', 'status']
    list_filter = ['status', 'category']
    search_fields = ['name', 'asset_tag']


@admin.register(FeedbackSurvey)
class FeedbackSurveyAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title']
    date_hierarchy = 'created_at'


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ['survey', 'employee', 'submitted_at']
    list_filter = ['submitted_at']
    search_fields = ['survey__title', 'employee__user__username']
    date_hierarchy = 'submitted_at'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'created_at', 'message']
    list_filter = ['created_at']
    search_fields = ['sender__username', 'message']
    date_hierarchy = 'created_at'


@admin.register(AIRequest)
class AIRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'resolved']
    list_filter = ['resolved', 'created_at']
    search_fields = ['user__username', 'query']
    date_hierarchy = 'created_at'


from django.utils import timezone
