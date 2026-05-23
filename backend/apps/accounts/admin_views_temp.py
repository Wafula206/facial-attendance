from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from .models import User, Programme, Semester, StudentProfile, LecturerProfile
from apps.courses.models import Course
from apps.attendance.models import ClassSession, AttendanceRecord
import uuid
import csv


def is_admin(user):
    return user.is_superuser or user.user_type == 'admin'


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    context = {
        'total_students': StudentProfile.objects.count(),
        'total_lecturers': LecturerProfile.objects.count(),
        'total_courses': Course.objects.count(),
        'total_programmes': Programme.objects.count(),
        'total_sessions': ClassSession.objects.count(),
        'active_semester': Semester.objects.filter(is_active=True).first(),
        'recent_sessions': ClassSession.objects.order_by('-start_time')[:5],
        'recent_students': StudentProfile.objects.order_by('-created_at')[:5],
        'recent_lecturers': LecturerProfile.objects.order_by('-created_at')[:5],
        'page_title': 'Admin Dashboard'
    }
    return render(request, 'accounts/admin_dashboard.html', context)


# ==================== USER MANAGEMENT ====================

@login_required
@user_passes_test(is_admin)
def manage_users(request):
    users = User.objects.all().select_related('student_profile', 'lecturer_profile')
    return render(request, 'accounts/manage_users.html', {'users': users})


@login_required
@user_passes_test(is_admin)
def create_user(request):
    programmes = Programme.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        reg_no = request.POST.get('reg_no')
        user_type = request.POST.get('user_type')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('/admin-dashboard/users/create/')
        
        user = User.objects.create_user(
            username=username, password=password, email=email,
            first_name=first_name, last_name=last_name, reg_no=reg_no, user_type=user_type
        )
        
        if user_type == 'student':
            programme_id = request.POST.get('programme')
            programme = Programme.objects.get(id=programme_id) if programme_id else None
            StudentProfile.objects.create(
                user=user, reg_no=reg_no, programme=programme,
                current_year=int(request.POST.get('current_year', 1)),
                current_semester=int(request.POST.get('current_semester', 1))
            )
            messages.success(request, f'Student {username} created')
        elif user_type == 'lecturer':
            LecturerProfile.objects.create(
                user=user, staff_id=reg_no,
                department=request.POST.get('department', ''),
                qualification=request.POST.get('qualification', '')
            )
            messages.success(request, f'Lecturer {username} created')
        return redirect('/admin-dashboard/users/')
    
    return render(request, 'accounts/create_user.html', {'programmes': programmes})


@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    programmes = Programme.objects.all()
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.user_type = request.POST.get('user_type')
        user.save()
        
        if hasattr(user, 'student_profile'):
            student = user.student_profile
            student.current_year = int(request.POST.get('current_year', 1))
            student.current_semester = int(request.POST.get('current_semester', 1))
            programme_id = request.POST.get('programme')
            if programme_id:
                student.programme = Programme.objects.get(id=programme_id)
            student.save()
        
        if hasattr(user, 'lecturer_profile'):
            lecturer = user.lecturer_profile
            lecturer.department = request.POST.get('department', '')
            lecturer.qualification = request.POST.get('qualification', '')
            lecturer.save()
        
        messages.success(request, f'User {user.username} updated')
        return redirect('/admin-dashboard/users/')
    
    return render(request, 'accounts/edit_user.html', {'edit_user': user, 'programmes': programmes})


@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted')
        return redirect('/admin-dashboard/users/')
    return render(request, 'accounts/delete_user.html', {'user': user})


@login_required
@user_passes_test(is_admin)
def promote_student(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    if student.current_year < 4:
        student.current_year += 1
        student.save()
        messages.success(request, f'{student.user.username} promoted to Year {student.current_year}')
    else:
        messages.warning(request, f'{student.user.username} is already in final year')
    return redirect('/admin-dashboard/users/')


# ==================== PROGRAMME MANAGEMENT ====================

@login_required
@user_passes_test(is_admin)
def manage_programmes(request):
    programmes = Programme.objects.all()
    return render(request, 'accounts/manage_programmes.html', {'programmes': programmes})


@login_required
@user_passes_test(is_admin)
def create_programme(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        name = request.POST.get('name')
        duration = request.POST.get('duration_years')
        Programme.objects.create(code=code, name=name, duration_years=duration)
        messages.success(request, f'Programme {code} created')
        return redirect('/admin-dashboard/programmes/')
    return render(request, 'accounts/create_programme.html')


@login_required
@user_passes_test(is_admin)
def edit_programme(request, programme_id):
    programme = get_object_or_404(Programme, id=programme_id)
    if request.method == 'POST':
        programme.code = request.POST.get('code')
        programme.name = request.POST.get('name')
        programme.duration_years = request.POST.get('duration_years')
        programme.save()
        messages.success(request, f'Programme {programme.code} updated')
        return redirect('/admin-dashboard/programmes/')
    return render(request, 'accounts/edit_programme.html', {'programme': programme})


@login_required
@user_passes_test(is_admin)
def delete_programme(request, programme_id):
    programme = get_object_or_404(Programme, id=programme_id)
    if request.method == 'POST':
        programme.delete()
        messages.success(request, 'Programme deleted')
        return redirect('/admin-dashboard/programmes/')
    return render(request, 'accounts/delete_programme.html', {'programme': programme})


# ==================== COURSE MANAGEMENT ====================

@login_required
@user_passes_test(is_admin)
def manage_courses(request):
    courses = Course.objects.select_related('programme', 'lecturer').all()
    return render(request, 'accounts/manage_courses.html', {'courses': courses})


@login_required
@user_passes_test(is_admin)
def create_course(request):
    programmes = Programme.objects.all()
    lecturers = LecturerProfile.objects.select_related('user').all()
    if request.method == 'POST':
        code = request.POST.get('code')
        name = request.POST.get('name')
        credits = request.POST.get('credits')
        programme_id = request.POST.get('programme')
        year = request.POST.get('year')
        semester = request.POST.get('semester')
        lecturer_id = request.POST.get('lecturer')
        programme = Programme.objects.get(id=programme_id) if programme_id else None
        lecturer = LecturerProfile.objects.get(id=lecturer_id) if lecturer_id else None
        Course.objects.create(
            code=code, name=name, credits=credits, programme=programme,
            year=year, semester=semester, lecturer=lecturer
        )
        messages.success(request, f'Course {code} created')
        return redirect('/admin-dashboard/courses/')
    return render(request, 'accounts/create_course.html', {'programmes': programmes, 'lecturers': lecturers})


@login_required
@user_passes_test(is_admin)
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    programmes = Programme.objects.all()
    lecturers = LecturerProfile.objects.select_related('user').all()
    if request.method == 'POST':
        course.code = request.POST.get('code')
        course.name = request.POST.get('name')
        course.credits = request.POST.get('credits')
        course.year = request.POST.get('year')
        course.semester = request.POST.get('semester')
        lecturer_id = request.POST.get('lecturer')
        if lecturer_id:
            course.lecturer = LecturerProfile.objects.get(id=lecturer_id)
        course.save()
        messages.success(request, f'Course {course.code} updated')
        return redirect('/admin-dashboard/courses/')
    return render(request, 'accounts/edit_course.html', {'course': course, 'programmes': programmes, 'lecturers': lecturers})


# ==================== SEMESTER MANAGEMENT ====================

@login_required
@user_passes_test(is_admin)
def manage_semesters(request):
    semesters = Semester.objects.all().order_by('-start_date')
    return render(request, 'accounts/manage_semesters.html', {'semesters': semesters})


@login_required
@user_passes_test(is_admin)
def create_semester(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_active = request.POST.get('is_active') == 'on'
        if is_active:
            Semester.objects.filter(is_active=True).update(is_active=False)
        Semester.objects.create(name=name, start_date=start_date, end_date=end_date, is_active=is_active)
        messages.success(request, f'Semester {name} created')
        return redirect('/admin-dashboard/semesters/')
    return render(request, 'accounts/create_semester.html')


@login_required
@user_passes_test(is_admin)
def activate_semester(request, semester_id):
    Semester.objects.filter(is_active=True).update(is_active=False)
    semester = get_object_or_404(Semester, id=semester_id)
    semester.is_active = True
    semester.save()
    messages.success(request, f'{semester.name} is now active')
    return redirect('/admin-dashboard/semesters/')


# ==================== SESSION MANAGEMENT ====================

@login_required
@user_passes_test(is_admin)
def manage_sessions(request):
    sessions = ClassSession.objects.all().order_by('-start_time')
    return render(request, 'accounts/manage_sessions.html', {'sessions': sessions})


@login_required
@user_passes_test(is_admin)
def create_session(request):
    courses = Course.objects.select_related('programme').all()
    if request.method == 'POST':
        course_id = request.POST.get('course')
        venue = request.POST.get('venue')
        start_date = request.POST.get('start_date')
        start_time = request.POST.get('start_time')
        duration = int(request.POST.get('duration', 2))
        course = get_object_or_404(Course, id=course_id)
        from datetime import datetime
        start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + timezone.timedelta(hours=duration)
        ClassSession.objects.create(
            id=uuid.uuid4(),
            course_code=course.code,
            course_name=course.name,
            start_time=start_datetime,
            end_time=end_datetime,
            venue=venue,
            status='scheduled'
        )
        messages.success(request, f'Session created for {course.code}')
        return redirect('/admin-dashboard/sessions/')
    return render(request, 'accounts/create_session.html', {'courses': courses})


@login_required
@user_passes_test(is_admin)
def start_session(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)
    session.status = 'ongoing'
    session.save()
    messages.success(request, f'Session for {session.course_code} started')
    return redirect('/admin-dashboard/sessions/')


@login_required
@user_passes_test(is_admin)
def end_session(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)
    session.status = 'completed'
    session.save()
    messages.success(request, f'Session for {session.course_code} ended')
    return redirect('/admin-dashboard/sessions/')


@login_required
@user_passes_test(is_admin)
def view_session_attendance(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)
    records = AttendanceRecord.objects.filter(session=session).select_related('student__user')
    return render(request, 'accounts/session_attendance.html', {'session': session, 'records': records})


@login_required
@user_passes_test(is_admin)
def edit_session(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)
    if request.method == 'POST':
        session.course_code = request.POST.get('course_code')
        session.course_name = request.POST.get('course_name')
        session.venue = request.POST.get('venue')
        session.status = request.POST.get('status')
        session.save()
        messages.success(request, 'Session updated successfully')
        return redirect('/admin-dashboard/sessions/')
    return render(request, 'accounts/edit_session.html', {'session': session})


@login_required
@user_passes_test(is_admin)
def delete_session(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)
    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Session deleted successfully')
        return redirect('/admin-dashboard/sessions/')
    return render(request, 'accounts/delete_session.html', {'session': session})


@login_required
@user_passes_test(is_admin)
def mark_attendance_manual(request, session_id, student_id):
    session = get_object_or_404(ClassSession, id=session_id)
    student = get_object_or_404(StudentProfile, id=student_id)
    
    record = AttendanceRecord.objects.filter(student=student, session=session).first()
    
    if record and record.check_in_time:
        messages.warning(request, f'{student.user.get_full_name()} already checked in')
    else:
        if not record:
            AttendanceRecord.objects.create(
                student=student, session=session, status='present',
                recognition_method='manual', confidence=1.0, check_in_time=timezone.now()
            )
        else:
            record.check_in_time = timezone.now()
            record.status = 'present'
            record.recognition_method = 'manual'
            record.confidence = 1.0
            record.save()
        messages.success(request, f'Attendance marked for {student.user.get_full_name()}')
    
    return redirect(f'/admin-dashboard/sessions/{session_id}/attendance/')


@login_required
@user_passes_test(is_admin)
def export_attendance_csv(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)
    records = AttendanceRecord.objects.filter(session=session).select_related('student__user')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{session.course_code}_{session.start_time.strftime("%Y%m%d")}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Reg No', 'Status', 'Check In Time', 'Check Out Time', 'Duration', 'Method'])
    for record in records:
        writer.writerow([
            record.student.user.get_full_name(),
            record.student.reg_no,
            record.status,
            record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else '-',
            record.check_out_time.strftime('%H:%M:%S') if record.check_out_time else '-',
            record.duration_minutes or '-',
            record.recognition_method
        ])
    return response
