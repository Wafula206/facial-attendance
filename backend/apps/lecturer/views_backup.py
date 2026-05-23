from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from apps.accounts.models import ClassSession, LecturerProfile, AttendanceRecord, StudentProfile
from apps.courses.models import Course
from datetime import datetime

def get_navbar(request, active):
    """Generate navbar HTML"""
    user = request.user
    role = 'admin' if user.is_superuser else user.user_type
    
    navbar = f'''
    <div class="navbar">
        <div class="navbar-brand">
            <span>🎓</span>
            <span>Face Recognition Attendance System</span>
        </div>
        <div class="navbar-links">
    '''
    
    if role == 'admin':
        navbar += '''
            <a href="/admin-dashboard/"> Dashboard</a>
            <a href="/admin-dashboard/programmes/"> Programmes</a>
            <a href="/admin-dashboard/semesters/"> Semesters</a>
            <a href="/admin-dashboard/users/"> Users</a>
            <a href="/admin-dashboard/courses/"> Courses</a>
            <a href="/admin-dashboard/sessions/"> Sessions</a>
            <a href="/recognition/"> Take Attendance</a>
            <a href="/admin/"> Admin Panel</a>
        '''
    elif role == 'lecturer':
        navbar += '''
            <a href="/lecturer/dashboard/"> Dashboard</a>
            <a href="/lecturer/sessions/"> My Sessions</a>
            <a href="/lecturer/session/create/"> Create Session</a>
            <a href="/recognition/"> Take Attendance</a>
        '''
    elif role == 'student':
        navbar += '''
            <a href="/student/dashboard/"> Dashboard</a>
            <a href="/student/profile/"> My Profile</a>
            <a href="/student/attendance/"> Attendance</a>
        '''
    
    navbar += f'''
            <a href="/logout/" class="btn-danger" style="color:white; background:#f56565;"> Logout</a>
        </div>
        <div class="user-info">
            <div class="user-avatar">{user.get_full_name()[0] if user.get_full_name() else user.username[0]}</div>
            <span>{user.get_full_name() or user.username}</span>
        </div>
    </div>
    '''
    return navbar

def render_sessions(sessions, session_type):
    """Helper to render sessions from database"""
    if not sessions:
        if session_type == 'ongoing':
            return '<p>No ongoing sessions. Create a new session below.</p>'
        elif session_type == 'today':
            return '<p>No sessions scheduled for today.</p>'
        else:
            return '<p>No upcoming sessions scheduled.</p>'
    
    items = []
    for s in sessions:
        status_badge = ''
        if s.status == 'ongoing':
            status_badge = '<span class="badge" style="background:#48bb78; color:white; padding:4px 12px; border-radius:20px;">ONGOING</span>'
        elif s.status == 'scheduled':
            status_badge = '<span class="badge" style="background:#ed8936; color:white; padding:4px 12px; border-radius:20px;">SCHEDULED</span>'
        else:
            status_badge = '<span class="badge" style="background:#a0aec0; color:white; padding:4px 12px; border-radius:20px;">COMPLETED</span>'
        
        attendance_count = AttendanceRecord.objects.filter(session=s).count()
        
        items.append(f'''
        <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <strong>{s.course_code} - {s.title}</strong><br>
                📅 {s.start_time.strftime('%Y-%m-%d %H:%M')} - {s.end_time.strftime('%H:%M')}<br>
                📍 {s.venue}<br>
                {status_badge}
                <span style="margin-left: 10px;">✅ Attendance: {attendance_count}</span>
            </div>
            <div>
                <a href="/recognition/?session={s.id}" class="btn btn-success btn-sm" style="padding:8px 15px; background:#48bb78; color:white; text-decoration:none; border-radius:5px;">Take Attendance</a>
                <a href="/lecturer/session/{s.id}/attendance/" class="btn btn-primary btn-sm" style="padding:8px 15px; background:#667eea; color:white; text-decoration:none; border-radius:5px;">View Records</a>
                <a href="/lecturer/session/{s.id}/end/" class="btn btn-danger btn-sm" style="padding:8px 15px; background:#f56565; color:white; text-decoration:none; border-radius:5px;">End Session</a>
            </div>
        </div>
        ''')
    
    return ''.join(items)

def render_courses(courses):
    """Helper to render courses from database with View Students button"""
    if not courses:
        return '<p>No courses assigned to you. Contact administrator.</p>'
    
    items = []
    for c in courses:
        session_count = ClassSession.objects.filter(course_code=c.code).count()
        student_count = StudentProfile.objects.filter(enrolled_courses__code=c.code).count()
        
        items.append(f'''
        <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <strong>{c.code} - {c.name}</strong><br>
                📍 Department: {c.department} | Credits: {c.credits}<br>
                📊 Sessions: {session_count} | Students: {student_count}
            </div>
            <div>
                <a href="/lecturer/session/create/?course={c.code}" class="btn btn-primary btn-sm">+ Create Session</a>
                <a href="/lecturer/course/{c.code}/students/" class="btn btn-info btn-sm">👥 View Students</a>
            </div>
        </div>
        ''')
    
    return ''.join(items)

@login_required
@login_required
def dashboard(request):
    """Lecturer dashboard"""
    
    if request.user.is_superuser:
        return redirect('/admin/')
    
    if request.user.user_type != 'lecturer':
        return HttpResponse("Access Denied. Lecturer only area.")
    
    navbar = get_navbar(request, 'dashboard')
    
    lecturer = LecturerProfile.objects.get(user=request.user)
    assigned_courses = Course.objects.filter(lecturer_staff_id=lecturer.staff_id)
    course_codes = [c.code for c in assigned_courses]
    
    today = timezone.now().date()
    today_sessions = ClassSession.objects.filter(
        course_code__in=course_codes,
        start_time__date=today
    ).order_by('start_time') if course_codes else []
    
    ongoing_sessions = ClassSession.objects.filter(
        course_code__in=course_codes,
        status='ongoing'
    ).order_by('-start_time') if course_codes else []
    
    upcoming_sessions = ClassSession.objects.filter(
        course_code__in=course_codes,
        start_time__gt=timezone.now(),
        status='scheduled'
    ).order_by('start_time')[:10] if course_codes else []
    
    total_courses = assigned_courses.count()
    total_students = StudentProfile.objects.count()
    total_sessions = ClassSession.objects.filter(course_code__in=course_codes).count() if course_codes else 0
    total_attendance = AttendanceRecord.objects.filter(session__course_code__in=course_codes).count() if course_codes else 0
    
    # Get current recognition mode from session
    current_mode = request.session.get('recognition_type', 'original')
    mode_display = '🧠 CNN Recognition' if current_mode == 'cnn' else '📷 Original Recognition'
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lecturer Dashboard | Karatina University</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: white;
                padding: 25px;
                border-radius: 15px;
                text-align: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .stat-value {{ font-size: 2rem; font-weight: bold; color: #667eea; }}
            .card {{
                background: white;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 25px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .card-header {{
                border-bottom: 2px solid #667eea;
                padding-bottom: 12px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
            }}
            .btn {{
                display: inline-block;
                padding: 8px 15px;
                border-radius: 5px;
                text-decoration: none;
                margin: 5px;
            }}
            .btn-primary {{ background: #667eea; color: white; }}
            .btn-info {{ background: #17a2b8; color: white; }}
            .mode-indicator {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            }}
            .mode-original {{ background: #48bb78; color: white; }}
            .mode-cnn {{ background: #ed8936; color: white; }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-value">{total_courses}</div><div>My Courses</div></div>
                <div class="stat-card"><div class="stat-value">{total_students}</div><div>Total Students</div></div>
                <div class="stat-card"><div class="stat-value">{total_sessions}</div><div>Total Sessions</div></div>
                <div class="stat-card"><div class="stat-value">{total_attendance}</div><div>Attendance Records</div></div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h3>🤖 Recognition Mode</h3>
                </div>
                <div style="padding: 15px; text-align: center;">
                    <p style="margin-bottom: 15px;">
                        Current mode: <span class="mode-indicator mode-{current_mode}">{mode_display}</span>
                    </p>
                    <div style="display: flex; gap: 15px; justify-content: center;">
                        <a href="/lecturer/set-mode/original/" class="btn btn-primary">📷 Original Mode</a>
                        <a href="/lecturer/set-mode/cnn/" class="btn btn-info">🧠 CNN Mode (Test)</a>
                    </div>
                    <p style="font-size: 12px; color: #666; margin-top: 15px;">
                        CNN mode requires students to enroll via the "CNN Enroll" page first.
                    </p>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h3>🟢 Ongoing Sessions</h3>
                    <a href="/lecturer/session/create/" class="btn btn-success">+ Create New Session</a>
                </div>
                {render_sessions(ongoing_sessions, 'ongoing')}
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h3>📅 Today's Sessions</h3>
                </div>
                {render_sessions(today_sessions, 'today')}
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h3>📋 My Courses</h3>
                </div>
                {render_courses(assigned_courses)}
            </div>
        </div>
        
        <div class="footer">
            <p>Karatina University - Attendance System</p>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

@login_required
@login_required
def lecturer_sessions(request):
    """View all sessions for lecturer with full controls"""
    if request.user.user_type != 'lecturer':
        return HttpResponse("Access Denied")
    
    navbar = get_navbar(request, 'sessions')
    lecturer = LecturerProfile.objects.get(user=request.user)
    assigned_courses = Course.objects.filter(lecturer_staff_id=lecturer.staff_id)
    course_codes = [c.code for c in assigned_courses]
    
    all_sessions = ClassSession.objects.filter(
        course_code__in=course_codes
    ).order_by('-start_time') if course_codes else []
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Sessions | Lecturer Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .session-card {{
                background: white;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                transition: transform 0.3s;
            }}
            .session-card:hover {{ transform: translateY(-3px); }}
            .session-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }}
            .session-title {{
                font-size: 1.2rem;
                font-weight: bold;
                color: #333;
            }}
            .session-status {{
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            }}
            .status-scheduled {{ background: #ed8936; color: white; }}
            .status-ongoing {{ background: #48bb78; color: white; }}
            .status-completed {{ background: #a0aec0; color: white; }}
            .session-details {{
                margin: 15px 0;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
            }}
            .detail-item {{
                color: #4a5568;
                font-size: 14px;
            }}
            .session-actions {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid #eee;
            }}
            .btn-sm {{ padding: 8px 16px; font-size: 13px; }}
            .btn-success {{ background: #48bb78; color: white; }}
            .btn-primary {{ background: #667eea; color: white; }}
            .btn-danger {{ background: #f56565; color: white; }}
            .btn-info {{ background: #17a2b8; color: white; }}
            .btn-warning {{ background: #ed8936; color: white; }}
            .btn:hover {{ opacity: 0.9; transform: translateY(-1px); }}
            .stats-summary {{
                display: flex;
                gap: 20px;
                margin-bottom: 25px;
                flex-wrap: wrap;
            }}
            .stat-box {{
                background: white;
                padding: 15px 25px;
                border-radius: 10px;
                text-align: center;
                flex: 1;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .stat-number {{ font-size: 1.8rem; font-weight: bold; color: #667eea; }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="stats-summary">
                <div class="stat-box">
                    <div class="stat-number">{len([s for s in all_sessions if s.status == 'scheduled'])}</div>
                    <div>Scheduled</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{len([s for s in all_sessions if s.status == 'ongoing'])}</div>
                    <div>Ongoing</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{len([s for s in all_sessions if s.status == 'completed'])}</div>
                    <div>Completed</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{len(all_sessions)}</div>
                    <div>Total Sessions</div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h2>📅 My Sessions</h2>
                    <div>
                        <a href="/lecturer/dashboard/" class="btn btn-primary btn-sm">← Dashboard</a>
                        <a href="/lecturer/session/create/" class="btn btn-success btn-sm">+ Create Session</a>
                    </div>
                </div>
                
                {''.join([f'''
                <div class="session-card">
                    <div class="session-header">
                        <span class="session-title">{s.course_code} - {s.title}</span>
                        <span class="session-status status-{s.status}">{s.status.upper()}</span>
                    </div>
                    <div class="session-details">
                        <div class="detail-item">📅 Date: {s.start_time.strftime("%Y-%m-%d")}</div>
                        <div class="detail-item">🕐 Time: {s.start_time.strftime("%H:%M")} - {s.end_time.strftime("%H:%M")}</div>
                        <div class="detail-item">📍 Venue: {s.venue}</div>
                        <div class="detail-item">✅ Attendance: {AttendanceRecord.objects.filter(session=s).count()}</div>
                    </div>
                    <div class="session-actions">
                        {f'<a href="/lecturer/session/{s.id}/start/" class="btn btn-warning btn-sm" onclick="return confirm(\'Start this session?\')">▶️ Start Session</a>' if s.status == 'scheduled' else ''}
                        {f'<a href="/recognition/?session={s.id}" class="btn btn-success btn-sm">📸 Take Attendance</a>' if s.status == 'ongoing' else ''}
                        <a href="/lecturer/session/{s.id}/attendance/" class="btn btn-info btn-sm">📋 View Records</a>
                        {f'<a href="/lecturer/session/{s.id}/end/" class="btn btn-danger btn-sm" onclick="return confirm(\'End this session?\')">⏹️ End Session</a>' if s.status == 'ongoing' else ''}
                        {f'<a href="/lecturer/session/{s.id}/delete/" class="btn btn-danger btn-sm" onclick="return confirm(\'Delete this session?\')">🗑️ Delete</a>' if s.status == 'scheduled' else ''}
                    </div>
                </div>
                ''' for s in all_sessions]) or '<p>No sessions found. Create your first session!</p>'}
            </div>
        </div>
        
        <div class="footer">
            <p>Karatina University - Attendance System</p>
        </div>
            
        <script>
            // Display current recognition mode
            fetch('/lecturer/get-recognition-preference/')
                .then(response => response.json())
                .then(data => {
                    const modeElement = document.getElementById('currentMode');
                    if (modeElement) {
                        if (data.recognition_type === 'cnn') {
                            modeElement.innerHTML = '🧠 CNN Recognition (Test)';
                            modeElement.style.color = '#ed8936';
                        } else {
                            modeElement.innerHTML = '📷 Original Recognition';
                            modeElement.style.color = '#48bb78';
                        }
                    }
                })
                .catch(() => {
                    const modeElement = document.getElementById('currentMode');
                    if (modeElement) {
                        modeElement.innerHTML = '📷 Original Recognition';
                        modeElement.style.color = '#48bb78';
                    }
                });
        </script>
</body>
    </html>
    '''
    return HttpResponse(html)

@login_required
def create_session_form(request):
    """Form for lecturer to create a new session"""
    if request.user.user_type != 'lecturer':
        return HttpResponse("Access Denied")
    
    navbar = get_navbar(request, 'create_session')
    lecturer = LecturerProfile.objects.get(user=request.user)
    assigned_courses = Course.objects.filter(lecturer_staff_id=lecturer.staff_id)
    pre_selected_course = request.GET.get('course', '')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Create Session | Lecturer Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .form-container {{ max-width: 600px; margin: 0 auto; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; font-weight: 600; }}
            .form-group input, .form-group select {{ width: 100%; padding: 12px; border: 2px solid #e2e8f0; border-radius: 8px; }}
            .btn-submit {{ width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2>➕ Create New Session</h2>
                    <a href="/lecturer/dashboard/" class="btn btn-primary">← Back to Dashboard</a>
                </div>
                
                <div class="form-container">
                    <form method="post" action="/lecturer/session/create/submit/">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{request.COOKIES.get('csrftoken', '')}">
                        <div class="form-group">
                            <label>Select Course</label>
                            <select name="course_code" required>
                                <option value="">-- Select Course --</option>
                                {''.join([f'<option value="{c.code}" {"selected" if pre_selected_course == c.code else ""}>{c.code} - {c.name}</option>' for c in assigned_courses])}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Session Title</label>
                            <input type="text" name="title" placeholder="e.g., Week 1 - Introduction" required>
                        </div>
                        <div class="form-group">
                            <label>Start Date & Time</label>
                            <input type="datetime-local" name="start_time" required>
                        </div>
                        <div class="form-group">
                            <label>End Date & Time</label>
                            <input type="datetime-local" name="end_time" required>
                        </div>
                        <div class="form-group">
                            <label>Venue / Room</label>
                            <input type="text" name="venue" placeholder="e.g., Computer Lab 1" required>
                        </div>
                        <button type="submit" class="btn-submit">✨ Create Session</button>
                    </form>
                </div>
            </div>
        </div>
            
        <script>
            // Display current recognition mode
            fetch('/lecturer/get-recognition-preference/')
                .then(response => response.json())
                .then(data => {
                    const modeElement = document.getElementById('currentMode');
                    if (modeElement) {
                        if (data.recognition_type === 'cnn') {
                            modeElement.innerHTML = '🧠 CNN Recognition (Test)';
                            modeElement.style.color = '#ed8936';
                        } else {
                            modeElement.innerHTML = '📷 Original Recognition';
                            modeElement.style.color = '#48bb78';
                        }
                    }
                })
                .catch(() => {
                    const modeElement = document.getElementById('currentMode');
                    if (modeElement) {
                        modeElement.innerHTML = '📷 Original Recognition';
                        modeElement.style.color = '#48bb78';
                    }
                });
        </script>
</body>
    </html>
    '''
    return HttpResponse(html)

@csrf_exempt
@login_required
def create_session_submit(request):
    """Submit new session"""
    if request.method == 'POST' and request.user.user_type == 'lecturer':
        course_code = request.POST.get('course_code')
        title = request.POST.get('title')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        venue = request.POST.get('venue')
        lecturer = LecturerProfile.objects.get(user=request.user)
        
        course = Course.objects.filter(code=course_code).first()
        course_name = course.name if course else course_code
        
        ClassSession.objects.create(
            course_code=course_code,
            course_name=course_name,
            lecturer=lecturer,
            title=title,
            start_time=start_time,
            end_time=end_time,
            venue=venue,
            status='scheduled'
        )
        
        return HttpResponse('''
        
        ''')
    
    return redirect('/lecturer/dashboard/')

@login_required
def end_session(request, session_id):
    """End an ongoing session"""
    session = get_object_or_404(ClassSession, id=session_id)
    session.status = 'completed'
    session.save()
    
    return HttpResponse('''
    
    ''')

@login_required
@login_required
def session_attendance(request, session_id):
    """View attendance for a specific session with check-in/out details"""
    session = get_object_or_404(ClassSession, id=session_id)
    navbar = get_navbar(request, 'attendance')
    
    records = AttendanceRecord.objects.filter(session=session).select_related('student__user')
    enrolled_students = StudentProfile.objects.filter(enrolled_courses__code=session.course_code)
    marked_ids = [r.student.id for r in records]
    absent = [s for s in enrolled_students if s.id not in marked_ids]
    
    present_count = records.count()
    absent_count = len(absent)
    total_count = present_count + absent_count
    attendance_percentage = (present_count / total_count * 100) if total_count > 0 else 0
    
    # Calculate total class time from checked-out students
    total_duration = sum([r.duration_minutes for r in records if r.check_out_time]) or 0
    total_hours = total_duration // 60
    total_mins = total_duration % 60
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Session Attendance | {session.title}</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .stats-summary {{
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }}
            .stat-box {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                flex: 1;
                min-width: 120px;
            }}
            .stat-number {{
                font-size: 2rem;
                font-weight: bold;
                color: #667eea;
            }}
            .badge-present {{ background: #c6f6d5; color: #22543d; padding: 4px 12px; border-radius: 20px; }}
            .badge-late {{ background: #feebc8; color: #744210; padding: 4px 12px; border-radius: 20px; }}
            .badge-absent {{ background: #fed7d7; color: #742a2a; padding: 4px 12px; border-radius: 20px; }}
            .table-container {{ overflow-x: auto; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #667eea; color: white; }}
            tr:hover {{ background: #f5f5f5; }}
            .btn {{
                display: inline-block;
                padding: 8px 15px;
                border-radius: 5px;
                text-decoration: none;
                margin: 5px;
            }}
            .btn-primary {{ background: #667eea; color: white; }}
            .btn-success {{ background: #48bb78; color: white; }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2>{session.course_code} - {session.title}</h2>
                    <div>
                        <a href="/lecturer/dashboard/" class="btn btn-primary"> Back to Dashboard</a>
                        <a href="/recognition/?session={session.id}" class="btn btn-success"> Continue Marking</a>
                    </div>
                </div>
                <p>📅 {session.start_time.strftime('%Y-%m-%d %H:%M')} - {session.end_time.strftime('%H:%M')} | 📍 {session.venue}</p>
                
                <div class="stats-summary">
                    <div class="stat-box"><div class="stat-number">{present_count}</div><div>Present</div></div>
                    <div class="stat-box"><div class="stat-number">{absent_count}</div><div>Absent</div></div>
                    <div class="stat-box"><div class="stat-number">{total_count}</div><div>Total Enrolled</div></div>
                    <div class="stat-box"><div class="stat-number">{attendance_percentage:.1f}%</div><div>Attendance Rate</div></div>
                    <div class="stat-box"><div class="stat-number">{total_hours}h {total_mins}m</div><div>Total Class Time</div></div>
                </div>
                
                <h3>✅ Present Students ({present_count})</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Reg No</th>
                                <th>Student Name</th>
                                <th>Check In</th>
                                <th>Check Out</th>
                                <th>Duration</th>
                                <th>Status</th>
                                <th>Confidence</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td>{r.student.user.reg_no or "N/A"}</d>
                                <td>{r.student.user.get_full_name()}</d>
                                <td>{r.check_in_time.strftime("%H:%M:%S") if r.check_in_time else "-"}</d>
                                <td>{r.check_out_time.strftime("%H:%M:%S") if r.check_out_time else "-"}</d>
                                <td>{r.duration_minutes} min</d>
                                <td><span class="badge badge-{r.status}">{r.status.upper()}</span></d>
                                <td>{r.confidence:.0%}</d>
                             </d>
                            ''' for r in records]) or '<tr><td colspan="7">No attendance records</d'}
                        </tbody>
                    </table>
                </div>
                
                <h3>❌ Absent Students ({absent_count})</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Reg No</th>
                                <th>Student Name</th>
                                <th>Programme</th>
                                <th>Year</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td>{s.user.reg_no or "N/A"}</d>
                                <td>{s.user.get_full_name()}</d>
                                <td>{s.programme.name if s.programme else "N/A"}</d>
                                <td>Year {s.year_of_study}</d>
                             </d>
                            ''' for s in absent]) or '<tr><td colspan="4">All students present</d'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Karatina University - Attendance System</p>
        </div>
            
        <script>
            // Display current recognition mode
            fetch('/lecturer/get-recognition-preference/')
                .then(response => response.json())
                .then(data => {
                    const modeElement = document.getElementById('currentMode');
                    if (modeElement) {
                        if (data.recognition_type === 'cnn') {
                            modeElement.innerHTML = '🧠 CNN Recognition (Test)';
                            modeElement.style.color = '#ed8936';
                        } else {
                            modeElement.innerHTML = '📷 Original Recognition';
                            modeElement.style.color = '#48bb78';
                        }
                    }
                })
                .catch(() => {
                    const modeElement = document.getElementById('currentMode');
                    if (modeElement) {
                        modeElement.innerHTML = '📷 Original Recognition';
                        modeElement.style.color = '#48bb78';
                    }
                });
        </script>
</body>
    </html>
    '''
    return HttpResponse(html)

@login_required
def course_students(request, course_code):
    """Lecturer view - see students enrolled in their course"""
    if request.user.user_type != 'lecturer':
        return HttpResponse("Access Denied")
    
    navbar = get_navbar(request, 'course_students')
    lecturer = LecturerProfile.objects.get(user=request.user)
    
    # Verify this course belongs to the lecturer
    course = get_object_or_404(Course, code=course_code, lecturer_staff_id=lecturer.staff_id)
    
    # Get enrolled students
    students = StudentProfile.objects.filter(enrolled_courses__code=course.code).select_related('user')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Course Students | {course.code}</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 15px;
                text-align: center;
            }}
            .stat-value {{ font-size: 2rem; font-weight: bold; color: #667eea; }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Students Enrolled in {course.code} - {course.name}</h2>
                    <div>
                        <a href="/lecturer/dashboard/" class="btn btn-primary"> Back to Dashboard</a>
                    </div>
                </div>
                
                    <div class="stats-grid">
        <div class="stat-card"><div class="stat-value">{total_courses}</div><div>My Courses</div></div>
        <div class="stat-card"><div class="stat-value">{total_students}</div><div>Total Students</div></div>
        <div class="stat-card"><div class="stat-value">{total_sessions}</div><div>Total Sessions</div></div>
        <div class="stat-card"><div class="stat-value">{total_attendance}</div><div>Attendance Records</div></div>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h3>🤖 Recognition Mode</h3>
        </div>
        <div style="padding: 15px; text-align: center;">
            <p style="margin-bottom: 15px;">Current mode: <strong id="currentMode">Loading...</strong></p>
            <div style="display: flex; gap: 15px; justify-content: center;">
                <a href="/lecturer/set-mode/original/" class="btn btn-primary">📷 Original Mode</a>
                <a href="/lecturer/set-mode/cnn/" class="btn btn-info">🧠 CNN Mode (Test)</a>
            </div>
            <p style="font-size: 12px; color: #666; margin-top: 15px;">
                CNN mode requires students to enroll via the "CNN Enroll" page first.
            </p>
        </div>
    </div><div>Enrolled Students</div></div>
                    <div class="stat-card"><div class="stat-value">{course.max_students if course.max_students else "Not set"}</div><div>Course Capacity</div></div>
                </div>
                
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr><th>Reg No</th><th>Student Name</th><th>Email</th><th>Programme</th><th>Year</th></tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td>{s.user.reg_no or "N/A"}</d>
                                <td>{s.user.get_full_name()}</d>
                                <td>{s.user.email}</d>
                                <td>{s.programme.name if s.programme else "N/A"}</d>
                                <td>Year {s.year_of_study}</d>
                             </d>
                            ''' for s in students]) or '<tr><td colspan="5">No students enrolled in this course</d'}
                        </tbody>
                    ……>
                </div>
            </div>
        </div>
            
        <script>
            // Display current recognition mode
            fetch('/lecturer/get-recognition-preference/')
                .then(response => response.json())
                .then(data => {
                    const modeElement = document.getElementById('currentMode');
                    if (modeElement) {
                        if (data.recognition_type === 'cnn') {
                            modeElement.innerHTML = '🧠 CNN Recognition (Test)';
                            modeElement.style.color = '#ed8936';
                        } else {
                            modeElement.innerHTML = '📷 Original Recognition';
                            modeElement.style.color = '#48bb78';
                        }
                    }
                })
                .catch(() => {
                    const modeElement = document.getElementById('currentMode');
                    if (modeElement) {
                        modeElement.innerHTML = '📷 Original Recognition';
                        modeElement.style.color = '#48bb78';
                    }
                });
        </script>
</body>
    </html>
    '''
    return HttpResponse(html)

def _get_student_attendance_rate(student_id, course_code):
    """Calculate student's attendance rate for a specific course"""
    from apps.accounts.models import AttendanceRecord, ClassSession
    
    total_sessions = ClassSession.objects.filter(course_code=course_code).count()
    if total_sessions == 0:
        return 0
    
    present_count = AttendanceRecord.objects.filter(
        student_id=student_id,
        session__course_code=course_code,
        status='present'
    ).count()
    
    return int((present_count / total_sessions) * 100)

@login_required
def student_attendance_detail(request, student_id):
    """View detailed attendance for a specific student in lecturer's course"""
    if request.user.user_type != 'lecturer':
        return HttpResponse("Access Denied")
    
    navbar = get_navbar(request, 'student_attendance')
    student = get_object_or_404(StudentProfile, id=student_id)
    lecturer = LecturerProfile.objects.get(user=request.user)
    
    # Get courses taught by this lecturer
    lecturer_courses = Course.objects.filter(lecturer_staff_id=lecturer.staff_id).values_list('code', flat=True)
    
    # Get attendance records for this student in lecturer's courses
    records = AttendanceRecord.objects.filter(
        student=student,
        session__course_code__in=lecturer_courses
    ).select_related('session').order_by('-marked_at')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Student Attendance | {student.user.get_full_name()}</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Attendance Records for {student.user.get_full_name()}</h2>
                    <div>
                        <a href="javascript:history.back()" class="btn btn-primary"> Back</a>
                    </div>
                </div>
                
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr><th>Course</th><th>Session</th><th>Date</th><th>Time</th><th>Status</th><th>Confidence</th></tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td>{r.session.course_code}</d>
                                <td>{r.session.title}</d>
                                <td>{r.session.start_time.strftime("%Y-%m-%d")}</d>
                                <td>{r.marked_at.strftime("%H:%M:%S")}</d>
                                <td><span class="badge badge-{r.status}">{r.status.upper()}</span></d>
                                <td>{r.confidence:.0%}</d>
                             </d>
                            ''' for r in records]) or '<tr><td colspan="6">No attendance records found</d'}
                        </tbody>
                    ……>
                </div>
            </div>
        </div>
            
        <script>
            // Display current recognition mode
            fetch('/lecturer/get-recognition-preference/')
                .then(response => response.json())
                .then(data => {
                    const modeElement = document.getElementById('currentMode');
                    if (modeElement) {
                        if (data.recognition_type === 'cnn') {
                            modeElement.innerHTML = '🧠 CNN Recognition (Test)';
                            modeElement.style.color = '#ed8936';
                        } else {
                            modeElement.innerHTML = '📷 Original Recognition';
                            modeElement.style.color = '#48bb78';
                        }
                    }
                })
                .catch(() => {
                    const modeElement = document.getElementById('currentMode');
                    if (modeElement) {
                        modeElement.innerHTML = '📷 Original Recognition';
                        modeElement.style.color = '#48bb78';
                    }
                });
        </script>
</body>
    </html>
    '''
    return HttpResponse(html)






@login_required
def start_session(request, session_id):
    """Start a scheduled session (change status to ongoing)"""
    session = get_object_or_404(ClassSession, id=session_id)
    
    # Check if user owns this session
    if request.user.user_type != 'lecturer':
        return HttpResponse("Access Denied")
    
    lecturer = LecturerProfile.objects.get(user=request.user)
    if session.lecturer.id != lecturer.id:
        return HttpResponse("Access Denied - This session belongs to another lecturer")
    
    session.status = 'ongoing'
    session.save()
    
    return HttpResponse(f'''
    
    ''')


@login_required
def delete_session(request, session_id):
    """Delete a scheduled session"""
    session = get_object_or_404(ClassSession, id=session_id)
    
    if request.user.user_type != 'lecturer':
        return HttpResponse("Access Denied")
    
    lecturer = LecturerProfile.objects.get(user=request.user)
    if session.lecturer.id != lecturer.id:
        return HttpResponse("Access Denied")
    
    if session.status != 'scheduled':
        return HttpResponse('')
    
    session.delete()
    
    return HttpResponse(f'''
    
    ''')





@login_required
def set_recognition_preference(request):
    """Set lecturer's preferred recognition type (stores in session)"""
    if request.method == 'POST':
        rec_type = request.POST.get('recognition_type', 'original')
        request.session['recognition_type'] = rec_type
        return JsonResponse({'success': True, 'type': rec_type})
    return JsonResponse({'success': False})

@login_required
def get_recognition_preference(request):
    """Get lecturer's preferred recognition type"""
    rec_type = request.session.get('recognition_type', 'original')
    return JsonResponse({'recognition_type': rec_type})



@login_required
def set_mode_original(request):
    """Set recognition mode to original"""
    request.session['recognition_type'] = 'original'
    return HttpResponse('''
    <script>
        alert("Recognition mode set to ORIGINAL");
        window.location.href = "/lecturer/dashboard/";
    </script>
    ''')

@login_required
def set_mode_cnn(request):
    """Set recognition mode to CNN"""
    request.session['recognition_type'] = 'cnn'
    return HttpResponse('''
    <script>
        alert("Recognition mode set to CNN (Test)");
        window.location.href = "/lecturer/dashboard/";
    </script>
    ''')




@login_required
def set_mode_original(request):
    """Set recognition mode to original"""
    request.session['recognition_type'] = 'original'
    return HttpResponse('''
    <script>
        alert("Recognition mode set to ORIGINAL");
        window.location.href = "/lecturer/dashboard/";
    </script>
    ''')

@login_required
def set_mode_cnn(request):
    """Set recognition mode to CNN"""
    request.session['recognition_type'] = 'cnn'
    return HttpResponse('''
    <script>
        alert("Recognition mode set to CNN (Test)");
        window.location.href = "/lecturer/dashboard/";
    </script>
    ''')
