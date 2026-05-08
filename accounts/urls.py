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
]
