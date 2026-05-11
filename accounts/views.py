from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from functools import wraps
from django.utils import timezone
from django.db.models import Q, Avg, Sum
from .forms import (
    RegisterForm, LoginForm, EmployeeProfileForm, EmployeeCreateForm, UserProfileForm, 
    LeaveRequestForm, AttendanceForm, DocumentUploadForm,
    PolicyDocumentForm, ProjectForm, TaskForm, RecruitmentCandidateForm, OnboardingTaskForm,
    TrainingCourseForm, TrainingEnrollmentForm, AnnouncementForm, SupportTicketForm,
    ExpenseClaimForm, TimesheetEntryForm, HolidayForm, AssetForm, FeedbackResponseForm,
    ChatMessageForm, AIRequestForm,
)
from .models import (
    Employee, LeaveRequest, Attendance, Performance, Document,
    PayrollRecord, PolicyDocument, Project, Task, RecruitmentCandidate, OnboardingTask,
    TrainingCourse, TrainingEnrollment, Announcement, SupportTicket,
    ExpenseClaim, TimesheetEntry, Holiday, Asset, FeedbackSurvey, SurveyResponse,
    ChatMessage, AIRequest, AuditLog, ERPIntegrationSetting, ERPIntegrationLog,
)


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
                _log_audit_action(user, 'login', request=request)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """User logout view."""
    user = request.user if request.user.is_authenticated else None
    logout(request)
    _log_audit_action(user, 'logout', request=request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


def _get_current_employee(request):
    try:
        return Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return None


def _is_hr(user):
    return user.is_superuser or getattr(user, 'role', '') == 'HR'


def _is_manager(user):
    return user.is_superuser or getattr(user, 'role', '') == 'MANAGER'


def _is_ceo(user):
    return user.is_superuser or getattr(user, 'role', '') == 'CEO'


def _can_manage_leave(user, leave_request):
    if user.is_superuser or _is_hr(user):
        return True
    if _is_manager(user):
        manager = leave_request.employee.manager
        return manager is not None and manager.user == user
    return False


def _has_role(user, roles):
    if user.is_superuser:
        return True
    return getattr(user, 'role', '') in roles


def role_required(accepted_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if not _has_role(request.user, accepted_roles):
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def _get_client_ip(request):
    return request.META.get('REMOTE_ADDR', '')


def _log_audit_action(user, action, details='', request=None):
    if user is None:
        return
    AuditLog.objects.create(
        user=user,
        action=action,
        ip_address=_get_client_ip(request) if request is not None else '',
        details=details,
    )


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
        employee = None

    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=request.user)
        if employee:
            employee_form = EmployeeProfileForm(request.POST, request.FILES, instance=employee)
        else:
            employee_form = EmployeeCreateForm(request.POST, request.FILES)

        if user_form.is_valid() and employee_form.is_valid():
            user_form.save()
            employee_profile = employee_form.save(commit=False)
            if not employee:
                employee_profile.user = request.user
            employee_profile.save()
            messages.success(request, 'Profile saved successfully!')
            return redirect('profile')
    else:
        user_form = UserProfileForm(instance=request.user)
        employee_form = EmployeeProfileForm(instance=employee) if employee else EmployeeCreateForm()

    context = {
        'employee': employee,
        'user_form': user_form,
        'employee_form': employee_form,
        'is_new_profile': employee is None,
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
    employee = _get_current_employee(request)
    if employee is None and not (request.user.is_superuser or _is_hr(request.user)):
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')

    if request.user.is_superuser or _is_hr(request.user):
        leaves = LeaveRequest.objects.all().order_by('-created_at')
        show_employee_column = True
    elif _is_manager(request.user):
        leaves = LeaveRequest.objects.filter(
            Q(employee=employee) | Q(employee__manager=employee)
        ).order_by('-created_at')
        show_employee_column = True
    else:
        leaves = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')
        show_employee_column = False

    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        leaves = leaves.filter(status=status)

    manageable_leave_ids = [leave.id for leave in leaves if _can_manage_leave(request.user, leave)]

    context = {
        'leaves': leaves,
        'current_status': status,
        'show_employee_column': show_employee_column,
        'manageable_leave_ids': manageable_leave_ids,
    }
    return render(request, 'accounts/leave_history.html', context)


@login_required(login_url='login')
def attendance_view(request):
    """Attendance view."""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        employee = None
        messages.error(request, 'Employee profile not found. Contact HR to complete your employee record.')

    # Get attendance records for current month
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    if today.month == 12:
        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    attendance_records = Attendance.objects.none()
    if employee is not None:
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
        'employee': employee,
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
        return JsonResponse({
            'file_name': document.file.name,
            'file_url': document.file.url,
        })
    except (Employee.DoesNotExist, Document.DoesNotExist):
        messages.error(request, 'Document not found.')
        return redirect('documents')


@login_required(login_url='login')
def payroll_view(request):
    employee = _get_current_employee(request)
    if employee is None:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')

    if _is_hr(request.user):
        payroll_records = PayrollRecord.objects.order_by('-salary_month')
    elif _is_manager(request.user):
        payroll_records = PayrollRecord.objects.filter(
            Q(employee=employee) | Q(employee__manager=employee)
        ).order_by('-salary_month')
    else:
        payroll_records = PayrollRecord.objects.filter(employee=employee).order_by('-salary_month')

    context = {
        'payroll_records': payroll_records,
    }
    return render(request, 'accounts/payroll.html', context)


@login_required(login_url='login')
def policies_view(request):
    query = request.GET.get('q', '')
    policies = PolicyDocument.objects.filter(is_active=True)

    if query:
        policies = policies.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(document_type__icontains=query)
        )

    can_upload = _is_hr(request.user)

    if request.method == 'POST':
        if not can_upload:
            raise PermissionDenied
        form = PolicyDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            policy = form.save(commit=False)
            policy.uploaded_by = request.user
            policy.save()
            messages.success(request, 'Policy document uploaded successfully.')
            return redirect('policies')
    else:
        form = PolicyDocumentForm()

    context = {
        'policies': policies,
        'form': form,
        'query': query,
        'can_upload': can_upload,
    }
    return render(request, 'accounts/policies.html', context)


@login_required(login_url='login')
def directory_view(request):
    query = request.GET.get('search', '')
    department = request.GET.get('department', '')
    position = request.GET.get('position', '')

    employees = Employee.objects.select_related('user').all()

    if query:
        employees = employees.filter(
            Q(user__username__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(department__icontains=query) |
            Q(position__icontains=query)
        )

    if department:
        employees = employees.filter(department=department)

    if position:
        employees = employees.filter(position=position)

    context = {
        'employees': employees,
        'search_query': query,
        'selected_department': department,
        'selected_position': position,
        'departments': Employee.DEPARTMENT_CHOICES,
        'positions': Employee.POSITION_CHOICES,
    }
    return render(request, 'accounts/directory.html', context)


@login_required(login_url='login')
def projects_view(request):
    employee = _get_current_employee(request)

    if request.method == 'POST':
        if not (_is_hr(request.user) or _is_manager(request.user) or request.user.is_superuser):
            raise PermissionDenied
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project created successfully.')
            return redirect('projects')
    else:
        form = ProjectForm()

    if _is_hr(request.user) or request.user.is_superuser:
        projects = Project.objects.select_related('manager').all()
    elif _is_manager(request.user) and employee is not None:
        projects = Project.objects.select_related('manager').filter(
            Q(manager=employee) | Q(tasks__assigned_to=employee)
        ).distinct()
    else:
        projects = Project.objects.select_related('manager').filter(tasks__assigned_to=employee).distinct() if employee is not None else Project.objects.none()

    context = {
        'projects': projects,
        'form': form,
    }
    return render(request, 'accounts/projects.html', context)


@login_required(login_url='login')
def tasks_view(request):
    employee = _get_current_employee(request)
    if employee is None:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')

    if request.method == 'POST':
        if not (_is_hr(request.user) or _is_manager(request.user) or request.user.is_superuser):
            raise PermissionDenied
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task created successfully.')
            return redirect('tasks')
    else:
        form = TaskForm()

    if request.user.is_superuser or _is_hr(request.user):
        tasks = Task.objects.select_related('project', 'assigned_to').all()
    elif _is_manager(request.user):
        tasks = Task.objects.select_related('project', 'assigned_to').filter(
            Q(assigned_to=employee) | Q(project__manager=employee)
        )
    else:
        tasks = Task.objects.select_related('project', 'assigned_to').filter(assigned_to=employee)

    context = {
        'tasks': tasks,
        'form': form,
    }
    return render(request, 'accounts/tasks.html', context)


@login_required(login_url='login')
def recruitment_view(request):
    can_view_candidates = _is_hr(request.user) or _is_ceo(request.user) or request.user.is_superuser

    if request.method == 'POST':
        form = RecruitmentCandidateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Candidate application submitted successfully.')
            return redirect('recruitment')
    else:
        form = RecruitmentCandidateForm()

    candidates = RecruitmentCandidate.objects.order_by('-applied_on') if can_view_candidates else RecruitmentCandidate.objects.none()
    context = {
        'candidates': candidates,
        'form': form,
        'can_view_candidates': can_view_candidates,
    }
    return render(request, 'accounts/recruitment.html', context)


@login_required(login_url='login')
def onboarding_view(request):
    employee = _get_current_employee(request)
    if employee is None:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = OnboardingTaskForm(request.POST)
        if form.is_valid():
            onboarding_task = form.save(commit=False)
            onboarding_task.employee = employee
            if onboarding_task.completed and onboarding_task.completed_at is None:
                onboarding_task.completed_at = timezone.now()
            onboarding_task.save()
            messages.success(request, 'Onboarding task saved successfully.')
            return redirect('onboarding')
    else:
        form = OnboardingTaskForm()

    onboarding_tasks = OnboardingTask.objects.filter(employee=employee)
    context = {
        'onboarding_tasks': onboarding_tasks,
        'form': form,
    }
    return render(request, 'accounts/onboarding.html', context)


@login_required(login_url='login')
def trainings_view(request):
    employee = _get_current_employee(request)
    if employee is None:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')

    course_form = TrainingCourseForm()
    enrollment_form = TrainingEnrollmentForm()

    if request.method == 'POST':
        if 'create_course' in request.POST:
            if not (_is_hr(request.user) or _is_manager(request.user) or request.user.is_superuser):
                raise PermissionDenied
            course_form = TrainingCourseForm(request.POST)
            if course_form.is_valid():
                course_form.save()
                messages.success(request, 'Training course created successfully.')
                return redirect('trainings')
        elif 'enroll_course' in request.POST:
            enrollment_form = TrainingEnrollmentForm(request.POST)
            if enrollment_form.is_valid():
                enrollment = enrollment_form.save(commit=False)
                enrollment.employee = employee
                enrollment.save()
                messages.success(request, 'Enrolled successfully.')
                return redirect('trainings')

    courses = TrainingCourse.objects.all().order_by('-start_date')
    enrollments = TrainingEnrollment.objects.filter(employee=employee)

    context = {
        'courses': courses,
        'form': course_form,
        'enrollment_form': enrollment_form,
        'enrollments': enrollments,
    }
    return render(request, 'accounts/trainings.html', context)


@login_required(login_url='login')
def announcements_view(request):
    announcements = Announcement.objects.filter(is_active=True)
    if request.method == 'POST':
        if not _is_hr(request.user):
            raise PermissionDenied
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.published_by = request.user
            announcement.save()
            messages.success(request, 'Announcement posted successfully.')
            return redirect('announcements')
    else:
        form = AnnouncementForm()

    context = {
        'announcements': announcements,
        'form': form,
        'can_post': _is_hr(request.user),
    }
    return render(request, 'accounts/announcements.html', context)


@login_required(login_url='login')
def helpdesk_view(request):
    employee = _get_current_employee(request)
    if employee is None:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.employee = employee
            ticket.save()
            messages.success(request, 'Support ticket submitted successfully.')
            return redirect('helpdesk')
    else:
        form = SupportTicketForm()

    if _is_hr(request.user) or _is_manager(request.user) or request.user.is_superuser:
        tickets = SupportTicket.objects.all().order_by('-created_at')
    else:
        tickets = SupportTicket.objects.filter(employee=employee).order_by('-created_at')

    context = {
        'tickets': tickets,
        'form': form,
    }
    return render(request, 'accounts/helpdesk.html', context)


@login_required(login_url='login')
def expenses_view(request):
    employee = _get_current_employee(request)
    if employee is None:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ExpenseClaimForm(request.POST, request.FILES)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.employee = employee
            claim.save()
            messages.success(request, 'Expense claim submitted successfully.')
            return redirect('expenses')
    else:
        form = ExpenseClaimForm()

    if _is_hr(request.user) or _is_manager(request.user) or request.user.is_superuser:
        claims = ExpenseClaim.objects.all().order_by('-submitted_on')
    else:
        claims = ExpenseClaim.objects.filter(employee=employee).order_by('-submitted_on')

    context = {
        'claims': claims,
        'form': form,
    }
    return render(request, 'accounts/expenses.html', context)


@login_required(login_url='login')
def timesheets_view(request):
    employee = _get_current_employee(request)
    if employee is None:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = TimesheetEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.employee = employee
            entry.save()
            messages.success(request, 'Timesheet entry added successfully.')
            return redirect('timesheets')
    else:
        form = TimesheetEntryForm()

    if _is_hr(request.user) or _is_manager(request.user) or request.user.is_superuser:
        entries = TimesheetEntry.objects.all().order_by('-date')
    else:
        entries = TimesheetEntry.objects.filter(employee=employee).order_by('-date')

    context = {
        'entries': entries,
        'form': form,
    }
    return render(request, 'accounts/timesheets.html', context)


@login_required(login_url='login')
def holidays_view(request):
    if request.method == 'POST':
        if not _is_hr(request.user):
            raise PermissionDenied
        form = HolidayForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Holiday added successfully.')
            return redirect('holidays')
    else:
        form = HolidayForm()

    holidays = Holiday.objects.all().order_by('date')
    context = {
        'holidays': holidays,
        'form': form,
        'can_add': _is_hr(request.user),
    }
    return render(request, 'accounts/holidays.html', context)


@login_required(login_url='login')
def assets_view(request):
    if request.method == 'POST':
        if not _is_hr(request.user):
            raise PermissionDenied
        form = AssetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asset recorded successfully.')
            return redirect('assets')
    else:
        form = AssetForm()

    if _is_hr(request.user) or request.user.is_superuser:
        assets = Asset.objects.all().order_by('-created_at')
    else:
        employee = _get_current_employee(request)
        assets = Asset.objects.filter(assigned_to=employee).order_by('-created_at') if employee else Asset.objects.none()

    context = {
        'assets': assets,
        'form': form,
        'can_add': _is_hr(request.user),
    }
    return render(request, 'accounts/assets.html', context)


@login_required(login_url='login')
def feedback_view(request):
    employee = _get_current_employee(request)
    if employee is None:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')

    surveys = FeedbackSurvey.objects.filter(is_active=True).order_by('-created_at')
    responses = SurveyResponse.objects.filter(employee=employee)
    responded_surveys = list(responses.values_list('survey_id', flat=True))

    if request.method == 'POST':
        survey_id = request.POST.get('survey_id')
        response_form = FeedbackResponseForm(request.POST)
        if response_form.is_valid() and survey_id:
            response = response_form.save(commit=False)
            response.employee = employee
            response.survey = FeedbackSurvey.objects.get(id=survey_id)
            response.save()
            messages.success(request, 'Feedback submitted successfully.')
            return redirect('feedback')
    else:
        response_form = FeedbackResponseForm()

    context = {
        'surveys': surveys,
        'responses': responses,
        'response_form': response_form,
        'responded_surveys': responded_surveys,
    }
    return render(request, 'accounts/feedback.html', context)


@login_required(login_url='login')
def chat_view(request):
    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            chat_message = form.save(commit=False)
            chat_message.sender = request.user
            chat_message.save()
            return redirect('chat')
    else:
        form = ChatMessageForm()

    chat_messages = ChatMessage.objects.select_related('sender').order_by('-created_at')[:50]
    context = {
        'chat_messages': reversed(chat_messages),
        'form': form,
    }
    return render(request, 'accounts/chat.html', context)


@login_required(login_url='login')
def ai_assistance_view(request):
    if request.method == 'POST':
        form = AIRequestForm(request.POST)
        if form.is_valid():
            ai_request = form.save(commit=False)
            ai_request.user = request.user
            ai_request.response = 'Thank you for your request. An HR representative will review it shortly.'
            ai_request.resolved = False
            ai_request.save()
            messages.success(request, 'Your AI assistance request has been submitted.')
            return redirect('ai_assistance')
    else:
        form = AIRequestForm()

    requests = AIRequest.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'requests': requests,
        'form': form,
    }
    return render(request, 'accounts/ai_assistance.html', context)


@login_required(login_url='login')
def reports_view(request):
    employees = Employee.objects.count()
    active_holidays = Holiday.objects.filter(date__gte=timezone.now().date()).count()
    total_expenses = ExpenseClaim.objects.filter(status='APPROVED').aggregate(Sum('amount'))['amount__sum'] or 0
    pending_tickets = SupportTicket.objects.filter(status='OPEN').count()
    avg_rating = Performance.objects.aggregate(Avg('rating'))['rating__avg'] or 0
    context = {
        'employees': employees,
        'active_holidays': active_holidays,
        'total_expenses': total_expenses,
        'pending_tickets': pending_tickets,
        'average_rating': round(avg_rating, 2),
    }
    return render(request, 'accounts/reports.html', context)


@login_required(login_url='login')
@role_required(['HR', 'CEO'])
def hr_actions_view(request):
    """Central HR actions dashboard."""
    open_leave_requests = LeaveRequest.objects.filter(status='P').count()
    active_payroll = PayrollRecord.objects.count()
    active_policies = PolicyDocument.objects.filter(is_active=True).count()
    open_candidates = RecruitmentCandidate.objects.exclude(status='REJECTED').count()
    audit_entries = AuditLog.objects.count()
    context = {
        'open_leave_requests': open_leave_requests,
        'active_payroll': active_payroll,
        'active_policies': active_policies,
        'open_candidates': open_candidates,
        'audit_entries': audit_entries,
    }
    return render(request, 'accounts/hr_actions.html', context)


@login_required(login_url='login')
@role_required(['HR', 'CEO'])
def erp_integration_view(request):
    settings_qs = ERPIntegrationSetting.objects.filter(active=True)
    integration_settings = settings_qs.first()
    logs = ERPIntegrationLog.objects.order_by('-created_at')[:20]

    if request.method == 'POST':
        if not integration_settings:
            messages.error(request, 'No active ERP integration setting is configured.')
        else:
            # Placeholder integration step; replace with actual ERP/HRMS API calls.
            ERPIntegrationLog.objects.create(
                action='ERP_SYNC',
                status='SUCCESS',
                message=f'Synchronized with ERP endpoint {integration_settings.api_endpoint}',
            )
            messages.success(request, 'ERP sync completed. Check logs for details.')

    context = {
        'integration_settings': integration_settings,
        'logs': logs,
    }
    return render(request, 'accounts/erp_integration.html', context)


@login_required(login_url='login')
@role_required(['HR', 'CEO'])
def audit_logs_view(request):
    logs = AuditLog.objects.select_related('user').order_by('-created_at')[:50]
    context = {
        'audit_logs': logs,
    }
    return render(request, 'accounts/audit_logs.html', context)
