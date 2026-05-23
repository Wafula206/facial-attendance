from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Count, Q, Avg
from apps.accounts.models import User, ClassSession, AttendanceRecord, StudentProfile, LecturerProfile
from apps.courses.models import Course
import json
import uuid
from datetime import datetime, timedelta
import csv
from io import StringIO

def is_lecturer(user):
    return user.is_authenticated and user.user_type == 'lecturer'

def is_student(user):
    return user.is_authenticated and user.user_type == 'student'

# ==================== LECTURER VIEWS ====================

@login_required
@user_passes_test(is_lecturer)
def lecturer_dashboard(request):
    """Lecturer main dashboard - DATA FROM DATABASE"""
    lecturer = request.user.lecturer_profile
    courses = lecturer.courses.all()
    
    # Get today's sessions from database
    today = timezone.now().date()
    today_sessions = ClassSession.objects.filter(
        lecturer=lecturer,
        start_time__date=today
    ).order_by('start_time')
    
    # Get upcoming sessions from database
    upcoming_sessions = ClassSession.objects.filter(
        lecturer=lecturer,
        start_time__gt=timezone.now(),
        status='scheduled'
    ).order_by('start_time')[:5]
    
    # Get recent attendance stats from database
    total_students = StudentProfile.objects.filter(
        enrolled_courses__in=courses
    ).distinct().count()
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lecturer Dashboard | Karatina University</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: "Segoe UI", Arial; background: #f0f2f5; }}
            .navbar {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 30px;
                display: flex;
                justify-content: space-between;
                flex-wrap: wrap;
            }}
            .nav-links a {{
                color: white;
                text-decoration: none;
                margin-left: 20px;
                padding: 8px 15px;
                border-radius: 5px;
            }}
            .nav-links a:hover {{ background: rgba(255,255,255,0.2); }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .stat-value {{ font-size: 2rem; font-weight: bold; color: #667eea; }}
            .section {{
                background: white;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 30px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .section h3 {{ margin-bottom: 20px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
            .session-card {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 15px;
                display: flex;
                justify-content: space-between;
                flex-wrap: wrap;
            }}
            .btn {{
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 5px;
            }}
            .btn-primary {{ background: #667eea; color: white; }}
            .btn-success {{ background: #4CAF50; color: white; }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{ background: #667eea; color: white; }}
        </style>
    </head>
    <body>
        <div class="navbar">
            <h2>🎓 Lecturer Dashboard - {request.user.get_full_name()}</h2>
            <div class="nav-links">
                <a href="/lecturer/dashboard/">Dashboard</a>
                <a href="/recognition/">Take Attendance</a>
                <a href="/admin/logout/">Logout</a>
            </div>
        </div>
        
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-value">{courses.count()}</div><div>My Courses</div></div>
                <div class="stat-card"><div class="stat-value">{total_students}</div><div>Total Students</div></div>
                <div class="stat-card"><div class="stat-value">{today_sessions.count()}</div><div>Today's Sessions</div></div>
            </div>
            
            <div class="section">
                <h3>📅 Today's Sessions</h3>
                {''.join([f'''
                <div class="session-card">
                    <div>
                        <strong>{session.course.code} - {session.title}</strong><br>
                        🕐 {session.start_time.strftime("%H:%M")} - {session.end_time.strftime("%H:%M")} | 📍 {session.venue}
                    </div>
                    <div>
                        <a href="/recognition/?session={session.id}" class="btn btn-success">Start Session</a>
                    </div>
                </div>
                ''' for session in today_sessions]) or "<p>No sessions today</p>"}
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

@login_required
@user_passes_test(is_lecturer)
def create_session(request):
    """Create a new class session"""
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        title = request.POST.get('title')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        venue = request.POST.get('venue')
        
        course = get_object_or_404(Course, id=course_id, lecturer=request.user.lecturer_profile)
        
        session = ClassSession.objects.create(
            course=course,
            lecturer=request.user.lecturer_profile,
            title=title,
            start_time=start_time,
            end_time=end_time,
            venue=venue,
            status='scheduled'
        )
        
        return JsonResponse({'success': True, 'session_id': str(session.id)})
    
    courses = request.user.lecturer_profile.courses.all()
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Create Session</title>
        <style>
            body {{ font-family: Arial; background: #f0f2f5; padding: 20px; }}
            .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
            input, select {{ width: 100%; padding: 10px; margin: 10px 0; }}
            button {{ background: #667eea; color: white; padding: 12px; border: none; border-radius: 5px; width: 100%; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Create Session</h2>
            <form id="sessionForm">
                <select name="course_id" required>
                    <option value="">Select Course</option>
                    {''.join([f'<option value="{c.id}">{c.code} - {c.name}</option>' for c in courses])}
                </select>
                <input type="text" name="title" placeholder="Session Title" required>
                <input type="datetime-local" name="start_time" required>
                <input type="datetime-local" name="end_time" required>
                <input type="text" name="venue" placeholder="Venue" required>
                <button type="submit">Create</button>
            </form>
        </div>
        <script>
            document.getElementById("sessionForm").onsubmit = async (e) => {{
                e.preventDefault();
                const formData = new FormData(e.target);
                const res = await fetch("/attendance/session/create/", {{ method: "POST", body: formData }});
                const data = await res.json();
                if (data.success) {{
                    alert("Session created!");
                    window.location.href = "/lecturer/dashboard/";
                }}
            }};
        </script>
    </body>
    </html>
    '''
    return HttpResponse(html)

@login_required
@user_passes_test(is_lecturer)
def session_attendance(request, session_id):
    """View attendance for a session"""
    session = get_object_or_404(ClassSession, id=session_id)
    records = session.attendances.select_related('student__user').all()
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Session Attendance</title>
        <style>
            body {{ font-family: Arial; padding: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            th {{ background: #667eea; color: white; }}
        </style>
    </head>
    <body>
        <h2>{session.title} Attendance</h2>
        <a href="/lecturer/dashboard/">Back</a>
        <table>
            <thead><tr><th>Student</th><th>Reg No</th><th>Status</th><th>Time</th></tr></thead>
            <tbody>
                {''.join([f'<tr><td>{r.student.user.get_full_name()}</td><td>{r.student.user.reg_no}</td><td>{r.status}</td><td>{r.marked_at.strftime("%H:%M:%S")}</td></tr>' for r in records]) or '<tr><td colspan="4">No records</td></tr>'}
            </tbody>
        </table>
    </body>
    </html>
    '''
    return HttpResponse(html)

# ==================== STUDENT VIEWS ====================

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    """Student dashboard"""
    student = request.user.student_profile
    
    total = AttendanceRecord.objects.filter(student=student).count()
    present = AttendanceRecord.objects.filter(student=student, status='present').count()
    percentage = (present / total * 100) if total > 0 else 0
    
    recent = AttendanceRecord.objects.filter(student=student).select_related('session__course')[:10]
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Student Dashboard</title>
        <style>
            body {{ font-family: Arial; background: #f0f2f5; padding: 20px; }}
            .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
            .stat-card {{ background: white; padding: 20px; border-radius: 10px; text-align: center; flex: 1; }}
            .stat-value {{ font-size: 2rem; font-weight: bold; color: #667eea; }}
            table {{ width: 100%; border-collapse: collapse; background: white; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #667eea; color: white; }}
        </style>
    </head>
    <body>
        <h2>Welcome, {request.user.get_full_name()}</h2>
        <div class="stats">
            <div class="stat-card"><div class="stat-value">{total}</div><div>Total Sessions</div></div>
            <div class="stat-card"><div class="stat-value">{present}</div><div>Present</div></div>
            <div class="stat-card"><div class="stat-value">{percentage:.1f}%</div><div>Attendance</div></div>
        </div>
        <h3>Recent Attendance</h3>
        <table>
            <thead><tr><th>Course</th><th>Session</th><th>Date</th><th>Status</th></tr></thead>
            <tbody>
                {''.join([f'<tr><td>{r.session.course.code}</td><td>{r.session.title}</td><td>{r.session.start_time.strftime("%Y-%m-%d")}</td><td>{r.status}</td></tr>' for r in recent]) or '<tr><td colspan="4">No records</td></tr>'}
            </tbody>
        </table>
        <br>
        <a href="/student/attendance/export/">Export CSV</a>
    </body>
    </html>
    '''
    return HttpResponse(html)

@login_required
@user_passes_test(is_student)
def student_attendance(request):
    """All attendance records"""
    student = request.user.student_profile
    records = AttendanceRecord.objects.filter(student=student).select_related('session__course')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Attendance</title>
        <style>
            body {{ font-family: Arial; padding: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            th {{ background: #667eea; color: white; }}
        </style>
    </head>
    <body>
        <h2>All Attendance Records</h2>
        <a href="/student/dashboard/">Back</a>
        <table>
            <thead><tr><th>Course</th><th>Session</th><th>Date</th><th>Status</th><th>Confidence</th></tr></thead>
            <tbody>
                {''.join([f'<tr><td>{r.session.course.code}</td><td>{r.session.title}</td><td>{r.session.start_time.strftime("%Y-%m-%d")}</td><td>{r.status}</td><td>{r.confidence:.0%}</td></tr>' for r in records]) or '<tr><td colspan="5">No records</td></tr>'}
            </tbody>
        </table>
    </body>
    </html>
    '''
    return HttpResponse(html)

@login_required
@user_passes_test(is_student)
def export_attendance(request):
    """Export attendance to CSV"""
    student = request.user.student_profile
    records = AttendanceRecord.objects.filter(student=student).select_related('session__course')
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Course', 'Session', 'Date', 'Status', 'Confidence', 'Time'])
    
    for r in records:
        writer.writerow([
            r.session.course.code,
            r.session.title,
            r.session.start_time.strftime('%Y-%m-%d'),
            r.status,
            f"{r.confidence:.0%}",
            r.marked_at.strftime('%H:%M:%S')
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename=attendance_{request.user.username}.csv'
    return response
