from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard and Profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    
    # Leave Management
    path('leave/request/', views.leave_request, name='leave_request'),
    path('leave/history/', views.leave_history, name='leave_history'),
    path('leave/tracker/', views.leave_tracker, name='leave_tracker'),
    path('leave/<int:request_id>/approve/', views.approve_leave, name='approve_leave'),
    path('leave/<int:request_id>/reject/', views.reject_leave, name='reject_leave'),
    
    # Attendance
    path('attendance/', views.attendance_view, name='attendance'),
    
    # Performance
    path('performance/', views.performance_view, name='performance'),
    
    # Documents
    path('documents/', views.documents_view, name='documents'),
    path('documents/download/<int:doc_id>/', views.download_document, name='download_document'),
    path('payroll/', views.payroll_view, name='payroll'),
    path('policies/', views.policies_view, name='policies'),
    path('directory/', views.directory_view, name='directory'),
    path('projects/', views.projects_view, name='projects'),
    path('tasks/', views.tasks_view, name='tasks'),
    path('recruitment/', views.recruitment_view, name='recruitment'),
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('trainings/', views.trainings_view, name='trainings'),
    path('announcements/', views.announcements_view, name='announcements'),
    path('helpdesk/', views.helpdesk_view, name='helpdesk'),
    path('expenses/', views.expenses_view, name='expenses'),
    path('timesheets/', views.timesheets_view, name='timesheets'),
    path('holidays/', views.holidays_view, name='holidays'),
    path('assets/', views.assets_view, name='assets'),
    path('feedback/', views.feedback_view, name='feedback'),
    path('chat/', views.chat_view, name='chat'),
    path('ai-assistance/', views.ai_assistance_view, name='ai_assistance'),
    path('reports/', views.reports_view, name='reports'),
]
