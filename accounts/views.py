from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from django.utils import timezone
from .forms import (
    RegisterForm, LoginForm, EmployeeProfileForm, UserProfileForm, 
    LeaveRequestForm, AttendanceForm, DocumentUploadForm
)
from .models import Employee, LeaveRequest, Attendance, Performance, Document


def register(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
    else:
        form = RegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


def _get_current_employee(request):
    try:
        return Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return None


def _can_manage_leave(user, leave_request):
    if user.is_superuser:
        return True
    manager = leave_request.employee.manager
    return manager is not None and manager.user == user


@login_required(login_url='login')
def dashboard(request):
    """Main dashboard view for logged-in users."""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        employee = None
    
    # Get recent attendance records
    recent_attendance = Attendance.objects.filter(employee=employee).order_by('-date')[:10] if employee else []
    
    # Get pending leave requests
    pending_leaves = LeaveRequest.objects.filter(
        employee=employee, 
        status='P'
    ).order_by('-created_at') if employee else []
    
    # Get recent performance reviews
    recent_reviews = Performance.objects.filter(employee=employee).order_by('-review_date')[:3] if employee else []
    
    # Calculate statistics
    stats = {}
    if employee:
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        # Present days this month
        present_days = Attendance.objects.filter(
            employee=employee,
            date__gte=month_start,
            status='P'
        ).count()
        
        # Absent days this month
        absent_days = Attendance.objects.filter(
            employee=employee,
            date__gte=month_start,
            status='A'
        ).count()
        
        # Leave days this month
        leave_days = Attendance.objects.filter(
            employee=employee,
            date__gte=month_start,
            status='L'
        ).count()
        
        # Approved leaves count
        approved_leaves = LeaveRequest.objects.filter(
            employee=employee,
            status='A'
        ).count()
        
        stats = {
            'present': present_days,
            'absent': absent_days,
            'on_leave': leave_days,
            'approved_leaves': approved_leaves,
        }
    
    context = {
        'employee': employee,
        'has_subordinates': employee.subordinates.exists() if employee else False,
        'recent_attendance': recent_attendance,
        'pending_leaves': pending_leaves,
        'recent_reviews': recent_reviews,
        'stats': stats,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required(login_url='login')
def profile(request):
    """Employee profile view."""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=request.user)
        employee_form = EmployeeProfileForm(request.POST, request.FILES, instance=employee)
        
        if user_form.is_valid() and employee_form.is_valid():
            user_form.save()
            employee_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        user_form = UserProfileForm(instance=request.user)
        employee_form = EmployeeProfileForm(instance=employee)
    
    context = {
        'employee': employee,
        'user_form': user_form,
        'employee_form': employee_form,
    }
    return render(request, 'accounts/profile.html', context)


@login_required(login_url='login')
def leave_request(request):
    """Leave request view."""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = employee
            leave.save()
            messages.success(request, 'Leave request submitted successfully!')
            return redirect('leave_history')
    else:
        form = LeaveRequestForm()
    
    context = {'form': form}
    return render(request, 'accounts/leave_request.html', context)


@login_required(login_url='login')
def leave_tracker(request):
    """Manager leave tracker view."""
    employee = _get_current_employee(request)
    if employee is None and not request.user.is_superuser:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')

    if request.user.is_superuser:
        pending_requests = LeaveRequest.objects.filter(status='P').order_by('-created_at')
    else:
        pending_requests = LeaveRequest.objects.filter(
            employee__manager=employee,
            status='P'
        ).order_by('-created_at')

    tracker_summary = {
        'total_pending': pending_requests.count(),
        'subordinate_requests': LeaveRequest.objects.filter(employee__manager=employee).count() if employee else 0,
    }

    context = {
        'pending_requests': pending_requests,
        'tracker_summary': tracker_summary,
    }
    return render(request, 'accounts/leave_tracker.html', context)


@login_required(login_url='login')
@require_http_methods(['POST'])
def approve_leave(request, request_id):
    leave_request = get_object_or_404(LeaveRequest, id=request_id)
    if not _can_manage_leave(request.user, leave_request):
        raise PermissionDenied

    leave_request.status = 'A'
    leave_request.approved_by = request.user
    leave_request.approval_date = timezone.now()
    leave_request.save()
    messages.success(request, f'Leave request for {leave_request.employee.user.username} has been approved.')
    return redirect('leave_tracker')


@login_required(login_url='login')
@require_http_methods(['POST'])
def reject_leave(request, request_id):
    leave_request = get_object_or_404(LeaveRequest, id=request_id)
    if not _can_manage_leave(request.user, leave_request):
        raise PermissionDenied

    leave_request.status = 'R'
    leave_request.approved_by = request.user
    leave_request.approval_date = timezone.now()
    leave_request.save()
    messages.success(request, f'Leave request for {leave_request.employee.user.username} has been rejected.')
    return redirect('leave_tracker')


@login_required(login_url='login')
def leave_history(request):
    """Leave request history view."""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')
    
    leaves = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        leaves = leaves.filter(status=status)
    
    context = {
        'leaves': leaves,
        'current_status': status,
    }
    return render(request, 'accounts/leave_history.html', context)


@login_required(login_url='login')
def attendance_view(request):
    """Attendance view."""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')
    
    # Get attendance records for current month
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    if today.month == 12:
        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    attendance_records = Attendance.objects.filter(
        employee=employee,
        date__gte=month_start,
        date__lte=month_end
    ).order_by('-date')
    
    # Calculate statistics
    present = attendance_records.filter(status='P').count()
    absent = attendance_records.filter(status='A').count()
    on_leave = attendance_records.filter(status='L').count()
    wfh = attendance_records.filter(status='WFH').count()
    
    context = {
        'attendance_records': attendance_records,
        'month': today.strftime('%B %Y'),
        'stats': {
            'present': present,
            'absent': absent,
            'on_leave': on_leave,
            'wfh': wfh,
            'total': attendance_records.count(),
        }
    }
    return render(request, 'accounts/attendance.html', context)


@login_required(login_url='login')
def performance_view(request):
    """Performance review view."""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')
    
    reviews = Performance.objects.filter(employee=employee).order_by('-review_date')
    
    # Calculate average rating
    average_rating = 0
    if reviews.exists():
        average_rating = sum([r.rating for r in reviews]) / reviews.count()
    
    context = {
        'reviews': reviews,
        'average_rating': round(average_rating, 2),
        'total_reviews': reviews.count(),
    }
    return render(request, 'accounts/performance.html', context)


@login_required(login_url='login')
def documents_view(request):
    """Documents view."""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.employee = employee
            document.uploaded_by = request.user
            document.save()
            messages.success(request, 'Document uploaded successfully!')
            return redirect('documents')
    else:
        form = DocumentUploadForm()
    
    documents = Document.objects.filter(employee=employee).order_by('-uploaded_date')
    
    context = {
        'documents': documents,
        'form': form,
    }
    return render(request, 'accounts/documents.html', context)


@login_required(login_url='login')
def download_document(request, doc_id):
    """Download document view."""
    try:
        employee = Employee.objects.get(user=request.user)
        document = Document.objects.get(id=doc_id, employee=employee)
        
        file_handle = document.file.open('rb')
        response = JsonResponse({
            'file_name': document.file.name,
            'file_url': document.file.url,
        })
        return response
    except (Employee.DoesNotExist, Document.DoesNotExist):
        messages.error(request, 'Document not found.')
        return redirect('documents')
