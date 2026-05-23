from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from apps.attendance.models import ClassSession, AttendanceRecord
from apps.courses.models import Course
from apps.accounts.models import StudentProfile, LecturerProfile
import uuid
import csv


@login_required
def dashboard(request):
    """Lecturer dashboard view with courses and students"""
    if hasattr(request.user, 'lecturer_profile'):
        lecturer = request.user.lecturer_profile
        courses = Course.objects.filter(lecturer=lecturer)
        course_codes = [c.code for c in courses]
        sessions = ClassSession.objects.filter(course_code__in=course_codes).order_by('-start_time')[:10]
        
        # Get enrolled students for each course
        course_students = {}
        for course in courses:
            students = StudentProfile.objects.filter(enrolled_courses=course).select_related('user')
            course_students[course.code] = students.count()
    else:
        courses = []
        sessions = []
        course_students = {}
    
    context = {
        'user': request.user,
        'courses': courses,
        'sessions': sessions,
        'course_students': course_students,
        'total_courses': courses.count(),
        'total_sessions': sessions.count(),
        'page_title': 'Lecturer Dashboard'
    }
    return render(request, 'lecturer/dashboard.html', context)


@login_required
def my_courses(request):
    """View all courses assigned to lecturer"""
    if hasattr(request.user, 'lecturer_profile'):
        lecturer = request.user.lecturer_profile
        courses = Course.objects.filter(lecturer=lecturer).select_related('programme')
        
        # Get student count for each course
        for course in courses:
            course.student_count = StudentProfile.objects.filter(enrolled_courses=course).count()
            course.sessions_count = ClassSession.objects.filter(course_code=course.code).count()
    else:
        courses = []
    
    context = {
        'courses': courses,
        'page_title': 'My Courses'
    }
    return render(request, 'lecturer/my_courses.html', context)


@login_required
def course_students(request, course_code):
    """View students enrolled in a specific course"""
    course = get_object_or_404(Course, code=course_code)
    
    # Check if this course belongs to the lecturer
    if hasattr(request.user, 'lecturer_profile'):
        if course.lecturer != request.user.lecturer_profile:
            messages.error(request, 'You are not authorized to view this course')
            return redirect('/lecturer/dashboard/')
    
    students = StudentProfile.objects.filter(enrolled_courses=course).select_related('user')
    
    # Get attendance records for these students in this course
    sessions = ClassSession.objects.filter(course_code=course.code)
    for student in students:
        attendance_count = AttendanceRecord.objects.filter(
            student=student,
            session__in=sessions
        ).count()
        student.attendance_count = attendance_count
        student.total_sessions = sessions.count()
        student.attendance_rate = round((attendance_count / sessions.count()) * 100, 1) if sessions.count() > 0 else 0
    
    context = {
        'course': course,
        'students': students,
        'total_students': students.count(),
        'total_sessions': sessions.count(),
        'page_title': f'Students - {course.code}'
    }
    return render(request, 'lecturer/course_students.html', context)


@login_required
def export_course_students_csv(request, course_code):
    """Export students list with attendance to CSV"""
    import csv
    from django.http import HttpResponse
    
    course = get_object_or_404(Course, code=course_code)
    students = StudentProfile.objects.filter(enrolled_courses=course).select_related('user')
    sessions = ClassSession.objects.filter(course_code=course.code)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{course_code}_students_attendance.csv"'
    
    writer = csv.writer(response)
    writer.writerow([f'Student List - {course.code}: {course.name}'])
    writer.writerow([])
    writer.writerow(['Student Name', 'Registration No', 'Email', 'Attendance Count', 'Total Sessions', 'Attendance Rate'])
    
    for student in students:
        attendance_count = AttendanceRecord.objects.filter(student=student, session__in=sessions).count()
        rate = round((attendance_count / sessions.count()) * 100, 1) if sessions.count() > 0 else 0
        writer.writerow([
            student.user.get_full_name(),
            student.reg_no,
            student.user.email,
            attendance_count,
            sessions.count(),
            f'{rate}%'
        ])
    
    return response


@login_required
def lecturer_sessions(request):
    """View all sessions for lecturer"""
    if hasattr(request.user, 'lecturer_profile'):
        lecturer = request.user.lecturer_profile
        courses = Course.objects.filter(lecturer=lecturer)
        course_codes = [c.code for c in courses]
        sessions = ClassSession.objects.filter(course_code__in=course_codes).order_by('-start_time')
    else:
        sessions = []
    
    context = {
        'sessions': sessions,
        'page_title': 'My Sessions'
    }
    return render(request, 'lecturer/sessions.html', context)


@login_required
def create_session_form(request):
    """Form to create a new session"""
    if hasattr(request.user, 'lecturer_profile'):
        lecturer = request.user.lecturer_profile
        courses = Course.objects.filter(lecturer=lecturer)
    else:
        courses = []
    
    context = {'courses': courses, 'page_title': 'Create Session'}
    return render(request, 'lecturer/create_session.html', context)


@login_required
def create_session_submit(request):
    """Submit new session"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            course_code = data.get('course_code')
            topic = data.get('topic', '')
            venue = data.get('venue', '')
            start_time_str = data.get('start_time')
            duration = int(data.get('duration', 2))
            
            course = get_object_or_404(Course, code=course_code)
            from datetime import datetime
            start_datetime = datetime.fromisoformat(start_time_str)
            end_datetime = start_datetime + timezone.timedelta(hours=duration)
            
            session = ClassSession.objects.create(
                id=uuid.uuid4(),
                course_code=course.code,
                course_name=course.name,
                topic=topic,
                start_time=start_datetime,
                end_time=end_datetime,
                venue=venue,
                status='scheduled'
            )
            return JsonResponse({'success': True, 'session_id': str(session.id)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@login_required
def session_attendance(request, session_id):
    """View attendance for a specific session"""
    session = get_object_or_404(ClassSession, id=session_id)
    records = AttendanceRecord.objects.filter(session=session).select_related('student__user')
    context = {
        'session': session,
        'records': records,
        'page_title': f'Attendance - {session.course_code}'
    }
    return render(request, 'lecturer/session_attendance.html', context)


@login_required
def start_session(request, session_id):
    """Start a session"""
    session = get_object_or_404(ClassSession, id=session_id)
    session.status = 'ongoing'
    session.save()
    return JsonResponse({'success': True, 'message': 'Session started'})


@login_required
def end_session(request, session_id):
    """End a session"""
    session = get_object_or_404(ClassSession, id=session_id)
    session.status = 'completed'
    session.save()
    return JsonResponse({'success': True, 'message': 'Session ended'})


@login_required
def delete_session(request, session_id):
    """Delete a session"""
    session = get_object_or_404(ClassSession, id=session_id)
    session.delete()
    return JsonResponse({'success': True, 'message': 'Session deleted'})


@login_required
def set_mode_original(request):
    """Set recognition mode to original"""
    request.session['recognition_mode'] = 'original'
    return JsonResponse({'success': True, 'mode': 'original'})


@login_required
def set_mode_cnn(request):
    """Set recognition mode to CNN"""
    request.session['recognition_mode'] = 'cnn'
    return JsonResponse({'success': True, 'mode': 'cnn'})


@login_required
def get_recognition_preference(request):
    """Get current recognition mode"""
    mode = request.session.get('recognition_mode', 'original')
    return JsonResponse({'mode': mode})


# ==================== REPORTS ====================

@login_required
def attendance_report(request):
    """Generate attendance report for lecturer's courses"""
    if hasattr(request.user, 'lecturer_profile'):
        lecturer = request.user.lecturer_profile
        courses = Course.objects.filter(lecturer=lecturer)
        course_codes = [c.code for c in courses]
        sessions = ClassSession.objects.filter(course_code__in=course_codes)
        
        total_sessions = sessions.count()
        
        students_with_attendance = StudentProfile.objects.filter(
            attendancerecord__session__in=sessions
        ).distinct()
        total_students = students_with_attendance.count()
        
        course_stats = []
        for course in courses:
            course_sessions = sessions.filter(course_code=course.code)
            session_count = course_sessions.count()
            attendance_records = AttendanceRecord.objects.filter(session__in=course_sessions)
            total_attendance = attendance_records.count()
            
            unique_students = StudentProfile.objects.filter(
                attendancerecord__session__in=course_sessions
            ).distinct().count()
            
            course_stats.append({
                'course': course,
                'sessions': session_count,
                'attendance_count': total_attendance,
                'enrolled_students': unique_students,
                'attendance_rate': round((total_attendance / (session_count * max(unique_students, 1))) * 100, 1) if session_count > 0 else 0
            })
        
        context = {
            'courses': courses,
            'course_stats': course_stats,
            'total_sessions': total_sessions,
            'total_students': total_students,
            'page_title': 'Attendance Report'
        }
        return render(request, 'lecturer/attendance_report.html', context)
    
    return redirect('/lecturer/dashboard/')


@login_required
def session_report(request, session_id):
    """Detailed report for a specific session"""
    session = get_object_or_404(ClassSession, id=session_id)
    records = AttendanceRecord.objects.filter(session=session).select_related('student__user')
    
    present_count = records.count()
    
    all_sessions = ClassSession.objects.filter(course_code=session.course_code)
    students_who_attended = StudentProfile.objects.filter(
        attendancerecord__session__in=all_sessions
    ).distinct()
    total_students = students_who_attended.count()
    absent_count = total_students - present_count
    
    context = {
        'session': session,
        'records': records,
        'present_count': present_count,
        'absent_count': absent_count,
        'total_students': total_students,
        'attendance_rate': round((present_count / max(total_students, 1)) * 100, 1),
        'page_title': f'Report - {session.course_code}'
    }
    return render(request, 'lecturer/session_report.html', context)


@login_required
def export_report_csv(request, session_id):
    """Export session attendance to CSV"""
    session = get_object_or_404(ClassSession, id=session_id)
    records = AttendanceRecord.objects.filter(session=session).select_related('student__user')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_report_{session.course_code}_{session.start_time.strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Registration No', 'Status', 'Check In Time', 'Check Out Time', 'Duration (mins)', 'Recognition Method'])
    
    for record in records:
        writer.writerow([
            record.student.user.get_full_name(),
            record.student.reg_no,
            record.status.upper(),
            record.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if record.check_in_time else '-',
            record.check_out_time.strftime('%Y-%m-%d %H:%M:%S') if record.check_out_time else '-',
            record.duration_minutes or '-',
            record.recognition_method
        ])
    
    return response


@login_required
def overall_report_csv(request):
    """Export overall attendance report for all lecturer's courses"""
    if hasattr(request.user, 'lecturer_profile'):
        lecturer = request.user.lecturer_profile
        courses = Course.objects.filter(lecturer=lecturer)
        course_codes = [c.code for c in courses]
        sessions = ClassSession.objects.filter(course_code__in=course_codes)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="overall_attendance_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Course', 'Session Date', 'Topic', 'Total Students', 'Present', 'Attendance Rate'])
        
        for session in sessions:
            records = AttendanceRecord.objects.filter(session=session)
            present = records.count()
            
            all_course_sessions = ClassSession.objects.filter(course_code=session.course_code)
            enrolled = StudentProfile.objects.filter(
                attendancerecord__session__in=all_course_sessions
            ).distinct().count()
            
            rate = round((present / max(enrolled, 1)) * 100, 1)
            
            writer.writerow([
                session.course_code,
                session.start_time.strftime('%Y-%m-%d'),
                session.topic or '-',
                enrolled,
                present,
                f'{rate}%'
            ])
        
        return response
    
    return HttpResponse('Unauthorized', status=401)
