from django.http import HttpResponse, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from apps.accounts.models import User, StudentProfile, LecturerProfile, Programme, Semester, ClassSession, AttendanceRecord
from apps.courses.models import Course
import csv
from io import StringIO

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
            <a href="/admin-dashboard/students/" class="btn btn-primary btn-sm"> Students</a><a href="/admin-dashboard/users/"> Users</a>
            <a href="/admin-dashboard/courses/"> Courses</a>
            <a href="/admin-dashboard/sessions/"> Sessions</a>\n            <a href="/admin-dashboard/all-attendance/"> Attendance Records</a>
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

# ==================== DASHBOARD ====================

@login_required
@staff_member_required
def admin_dashboard(request):
    """Main admin dashboard"""
    total_students = StudentProfile.objects.count()
    total_lecturers = LecturerProfile.objects.count()
    total_programmes = Programme.objects.count()
    total_courses = Course.objects.count()
    total_sessions = ClassSession.objects.count()
    total_attendance = AttendanceRecord.objects.count()\n    total_duration = AttendanceRecord.objects.aggregate(total=models.Sum(\"duration_minutes\"))[\"total\"] or 0\n    total_hours = total_duration // 60\n    total_mins = total_duration % 60
    
    navbar = get_navbar(request, 'dashboard')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Dashboard | Karatina University</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        {navbar}
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-value">{total_students}</div><div>Students</div></div>
                <div class="stat-card"><div class="stat-value">{total_lecturers}</div><div>Lecturers</div></div>
                <div class="stat-card"><div class="stat-value">{total_programmes}</div><div>Programmes</div></div>
                <div class="stat-card"><div class="stat-value">{total_courses}</div><div>Courses</div></div>
                <div class="stat-card"><div class="stat-value">{total_sessions}</div><div>Sessions</div></div>
                <div class="stat-card"><div class="stat-value">{total_attendance}</div><div>Attendance</div></div>
            </div>
        </div>
        <div class="footer"><p>Karatina University - Attendance System</p></div>
    </body>
    </html>
    '''
    return HttpResponse(html)

# ==================== PROGRAMME MANAGEMENT ====================

@login_required
@staff_member_required
def manage_programmes(request):
    """Manage academic programmes"""
    navbar = get_navbar(request, 'programmes')
    programmes = Programme.objects.all().order_by('code')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage Programmes | Admin Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        {navbar}
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Academic Programmes</h2>
                    <div>
                        <a href="/admin-dashboard/" class="btn btn-primary"> Back</a>
                        <a href="/admin-dashboard/programmes/add/" class="btn btn-success">+ Add Programme</a>
                    </div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr><th>Code</th><th>Programme Name</th><th>Department</th><th>Duration</th><th>Students</th><th>Status</th><th>Actions</th></tr>
                        </thead>
                        <tbody>
                            {''.join([f'<tr><td><strong>{p.code}</strong></td><td>{p.name}</td><td>{p.department}</td><td>{p.duration_years} years</td><td>{StudentProfile.objects.filter(programme=p).count()}</td><td><span class="badge badge-success">Active</span></td><td><a href="/admin-dashboard/programmes/{p.id}/edit/" class="btn btn-primary btn-sm">Edit</a></td></tr>' for p in programmes]) or '<tr><td colspan="7">No programmes found</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

@login_required
@staff_member_required
def add_programme_form(request):
    """Add new programme form"""
    navbar = get_navbar(request, 'programmes')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Add Programme | Admin Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .form-container {{ max-width: 600px; margin: 0 auto; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; font-weight: 600; }}
            .form-group input {{ width: 100%; padding: 12px; border: 2px solid #e2e8f0; border-radius: 8px; }}
            .btn-submit {{ width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; }}
        </style>
    </head>
    <body>
        {navbar}
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Add New Academic Programme</h2>
                    <a href="/admin-dashboard/programmes/" class="btn btn-primary"> Back</a>
                </div>
                <div class="form-container">
                    <form method="post" action="/admin-dashboard/programmes/add/submit/">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{request.COOKIES.get('csrftoken', '')}">
                        <div class="form-group">
                            <label>Programme Code</label>
                            <input type="text" name="code" placeholder="e.g., BSCS" required>
                        </div>
                        <div class="form-group">
                            <label>Programme Name</label>
                            <input type="text" name="name" placeholder="e.g., Bachelor of Science in Computer Science" required>
                        </div>
                        <div class="form-group">
                            <label>Department</label>
                            <input type="text" name="department" placeholder="e.g., Computing and Informatics" required>
                        </div>
                        <div class="form-group">
                            <label>Duration (Years)</label>
                            <input type="number" name="duration_years" value="4" min="1" max="6">
                        </div>
                        <button type="submit" class="btn-submit"> Create Programme</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

@csrf_exempt
@login_required
@staff_member_required
def add_programme_submit(request):
    """Submit new programme"""
    if request.method == 'POST':
        code = request.POST.get('code').upper()
        name = request.POST.get('name')
        department = request.POST.get('department')
        duration_years = request.POST.get('duration_years', 4)
        
        if Programme.objects.filter(code=code).exists():
            return HttpResponse('<script>alert("Programme code already exists!"); window.history.back();</script>')
        
        Programme.objects.create(
            code=code,
            name=name,
            department=department,
            duration_years=int(duration_years),
            is_active=True
        )
        
        return HttpResponse('<script>alert("Programme created successfully!"); window.location.href="/admin-dashboard/programmes/";</script>')
    
    return redirect('/admin-dashboard/programmes/')

# ==================== SEMESTER MANAGEMENT ====================

@login_required
@staff_member_required
def manage_semesters(request):
    """Manage academic semesters"""
    navbar = get_navbar(request, 'semesters')
    semesters = Semester.objects.all().order_by('-academic_year', '-number')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage Semesters | Admin Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        {navbar}
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Academic Semesters</h2>
                    <div>
                        <a href="/admin-dashboard/" class="btn btn-primary"> Back</a>
                        <a href="/admin-dashboard/semesters/add/" class="btn btn-success">+ Add Semester</a>
                    </div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr><th>Semester</th><th>Academic Year</th><th>Start Date</th><th>End Date</th><th>Current</th><th>Actions</th></tr>
                        </thead>
                        <tbody>
                            {''.join([f'<tr><td>Semester {s.number}</td><td>{s.academic_year}</td><td>{s.start_date}</td><td>{s.end_date}</td><td><span class="badge badge-success">Current</span></td><td><a href="/admin-dashboard/semesters/{s.id}/edit/" class="btn btn-primary btn-sm">Edit</a></td></tr>' for s in semesters]) or '<tr><td colspan="6">No semesters found</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

@login_required
@staff_member_required
def add_semester_form(request):
    """Add new semester form"""
    navbar = get_navbar(request, 'semesters')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Add Semester | Admin Dashboard</title>
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
                    <h2> Add New Academic Semester</h2>
                    <a href="/admin-dashboard/semesters/" class="btn btn-primary"> Back</a>
                </div>
                <div class="form-container">
                    <form method="post" action="/admin-dashboard/semesters/add/submit/">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{request.COOKIES.get('csrftoken', '')}">
                        <div class="form-group">
                            <label>Semester Number</label>
                            <select name="number" required>
                                <option value="1">Semester 1</option>
                                <option value="2">Semester 2</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Academic Year</label>
                            <input type="text" name="academic_year" placeholder="e.g., 2024/2025" required>
                        </div>
                        <div class="form-group">
                            <label>Start Date</label>
                            <input type="date" name="start_date" required>
                        </div>
                        <div class="form-group">
                            <label>End Date</label>
                            <input type="date" name="end_date" required>
                        </div>
                        <div class="form-group">
                            <label>Set as Current Semester?</label>
                            <select name="is_current">
                                <option value="False">No</option>
                                <option value="True">Yes</option>
                            </select>
                        </div>
                        <button type="submit" class="btn-submit"> Create Semester</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

@csrf_exempt
@login_required
@staff_member_required
def add_semester_submit(request):
    """Submit new semester"""
    if request.method == 'POST':
        number = int(request.POST.get('number'))
        academic_year = request.POST.get('academic_year')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_current = request.POST.get('is_current') == 'True'
        
        if is_current:
            Semester.objects.filter(is_current=True).update(is_current=False)
        
        Semester.objects.create(
            number=number,
            academic_year=academic_year,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current
        )
        
        return HttpResponse('<script>alert("Semester created successfully!"); window.location.href="/admin-dashboard/semesters/";</script>')
    
    return redirect('/admin-dashboard/semesters/')

# ==================== USER MANAGEMENT ====================

@login_required
@staff_member_required
def manage_users(request):
    """Manage users"""
    navbar = get_navbar(request, 'users')
    students = StudentProfile.objects.select_related('user').all()
    lecturers = LecturerProfile.objects.select_related('user').all()
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage Users | Admin Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        {navbar}
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> User Management</h2>
                    <div>
                        <a href="/admin-dashboard/" class="btn btn-primary"> Back</a>
                        <a href="/admin-dashboard/users/add/" class="btn btn-success">+ Add New User</a>
                    </div>
                </div>
                <h3>Students</h3>
                <div class="table-container">
                    <table>
                        <thead><tr><th>Reg No</th><th>Name</th><th>Email</th><th>Programme</th></tr></thead>
                        <tbody>
                            {''.join([f'<tr><td>{s.user.reg_no or "N/A"}</td><td>{s.user.get_full_name()}</td><td>{s.user.email}</td><td>{s.programme.name if s.programme else "Not Assigned"}</td></tr>' for s in students]) or '<tr><td colspan="4">No students</td></tr>'}
                        </tbody>
                    </table>
                </div>
                <h3>Lecturers</h3>
                <div class="table-container">
                    <table>
                        <thead><tr><th>Staff ID</th><th>Name</th><th>Email</th></tr></thead>
                        <tbody>
                            {''.join([f'<tr><td>{l.staff_id}</td><td>{l.user.get_full_name()}</td><td>{l.user.email}</td></tr>' for l in lecturers]) or '<tr><td colspan="3">No lecturers</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

@login_required
@staff_member_required
def add_user_form(request):
    """Add user form"""
    navbar = get_navbar(request, 'users')
    programmes = Programme.objects.filter(is_active=True)
    current_semester = Semester.objects.filter(is_current=True).first()
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Add User | Admin Dashboard</title>
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
                    <h2> Add New User</h2>
                    <a href="/admin-dashboard/students/" class="btn btn-primary btn-sm"> Students</a><a href="/admin-dashboard/users/" class="btn btn-primary"> Back</a>
                </div>
                <div class="form-container">
                    <form method="post" action="/admin-dashboard/users/add/submit/">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{request.COOKIES.get('csrftoken', '')}">
                        <div class="form-group">
                            <label>Username</label>
                            <input type="text" name="username" required>
                        </div>
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" name="email" required>
                        </div>
                        <div class="form-group">
                            <label>First Name</label>
                            <input type="text" name="first_name" required>
                        </div>
                        <div class="form-group">
                            <label>Last Name</label>
                            <input type="text" name="last_name" required>
                        </div>
                        <div class="form-group">
                            <label>User Type</label>
                            <select name="user_type" id="userType" onchange="toggleFields()">
                                <option value="student">Student</option>
                                <option value="lecturer">Lecturer</option>
                                <option value="admin">Admin</option>
                            </select>
                        </div>
                        <div class="form-group" id="regNoGroup">
                            <label>Registration Number</label>
                            <input type="text" name="reg_no" placeholder="e.g., CS/001/22">
                        </div>
                        <div class="form-group" id="programmeGroup">
                            <label>Programme</label>
                            <select name="programme_id">
                                <option value="">-- Select Programme --</option>
                                {''.join([f'<option value="{p.id}">{p.code} - {p.name}</option>' for p in programmes])}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Password</label>
                            <input type="password" name="password" required>
                        </div>
                        <button type="submit" class="btn-submit"> Create User</button>
                    </form>
                </div>
            </div>
        </div>
        <script>
            function toggleFields() {{
                var userType = document.getElementById('userType').value;
                var regNoGroup = document.getElementById('regNoGroup');
                var programmeGroup = document.getElementById('programmeGroup');
                if (userType === 'student') {{
                    regNoGroup.style.display = 'block';
                    programmeGroup.style.display = 'block';
                }} else {{
                    regNoGroup.style.display = 'none';
                    programmeGroup.style.display = 'none';
                }}
            }}
            toggleFields();
        </script>
    </body>
    </html>
    '''
    return HttpResponse(html)

@csrf_exempt
@login_required
@staff_member_required
def add_user_submit(request):
    """Submit new user"""
    if request.method == 'POST':
        from django.contrib.auth.hashers import make_password
        
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        user_type = request.POST.get('user_type')
        reg_no = request.POST.get('reg_no')
        programme_id = request.POST.get('programme_id')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            return HttpResponse('<script>alert("Username exists!"); window.history.back();</script>')
        
        current_semester = Semester.objects.filter(is_current=True).first()
        
        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            user_type=user_type,
            reg_no=reg_no if user_type == 'student' else None,
            password=make_password(password),
            is_staff=(user_type == 'lecturer' or user_type == 'admin'),
            is_superuser=(user_type == 'admin')
        )
        
        if user_type == 'student':
            programme = Programme.objects.filter(id=programme_id).first() if programme_id else None
            StudentProfile.objects.create(
                user=user,
                programme=programme,
                year_of_study=1,
                semester=current_semester
            )
        elif user_type == 'lecturer':
            LecturerProfile.objects.create(
                user=user,
                staff_id=f"LEC{user.id:03d}",
                designation='Lecturer',
                office_location='Main Building'
            )
        
        return HttpResponse('<script>alert("User created successfully!"); window.location.href="/admin-dashboard/users/";</script>')
    
    return redirect('/admin-dashboard/users/')

# ==================== COURSE MANAGEMENT ====================

@login_required
@staff_member_required
@login_required
@staff_member_required
@login_required
@staff_member_required
def manage_courses(request):
    """Manage courses with lecturer and enrollment info"""
    navbar = get_navbar(request, 'courses')
    courses = Course.objects.all().order_by('code')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage Courses | Admin Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .stats-badge {{
                display: inline-block;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            .stats-badge-full {{ background: #fed7d7; color: #742a2a; }}
            .stats-badge-available {{ background: #c6f6d5; color: #22543d; }}
            .enrollment-bar {{
                width: 100px;
                height: 6px;
                background: #e2e8f0;
                border-radius: 3px;
                overflow: hidden;
                display: inline-block;
                margin-left: 8px;
            }}
            .enrollment-fill {{
                height: 100%;
                background: #48bb78;
                width: 0%;
            }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Course Management</h2>
                    <div>
                        <a href="/admin-dashboard/" class="btn btn-primary"> Back</a>
                        <a href="/admin-dashboard/courses/add/" class="btn btn-success">+ Add Course</a>
                    </div>
                </div>
                
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Code</th>
                                <th>Course Name</th>
                                <th>Department</th>
                                <th>Credits</th>
                                <th>Lecturer</th>
                                <th>Enrollment</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td><strong>{c.code}</strong></td>
                                <td>{c.name}</td>
                                <td>{c.department}</td>
                                <td>{c.credits}</td>
                                <td>{c.get_lecturer_name()}</td>
                                <td>
                                    <span title="Enrolled: {c.get_enrolled_count()} / Max: {c.max_students}">
                                        {c.get_enrolled_count()} / {c.max_students}
                                        <div class="enrollment-bar">
                                            <div class="enrollment-fill" style="width: {(c.get_enrolled_count() / c.max_students * 100) if c.max_students > 0 else 0}%"></div>
                                        </div>
                                    </span>
                                </d>
                                <td>
                                    <span class="stats-badge {'stats-badge-full' if c.is_full() else 'stats-badge-available'}">
                                        {'Full' if c.is_full() else f'{c.get_available_seats()} seats left'}
                                    </span>
                                </d>
                                <td>
                                    <a href="/admin-dashboard/courses/{c.code}/edit/" class="btn btn-primary btn-sm"> Edit</a>`n                                    <a href="/admin-dashboard/courses/{c.code}/edit-capacity/" class="btn btn-warning btn-sm"> Capacity</a>
                                    <a href="/admin-dashboard/courses/{c.code}/assign/" class="btn btn-info btn-sm"> Assign</a>
                                    <a href="/admin-dashboard/courses/{c.code}/students/" class="btn btn-success btn-sm"> Students</a>
                                </d>
                             </d>
                            ''' for c in courses]) or '<tr><td colspan="8">No courses found</d'}
                        </tbody>
                    ……>
                </div>
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
@staff_member_required
@login_required
@staff_member_required
@login_required
@staff_member_required
def add_course_form(request):
    """Add course form - ADMIN must set ALL values"""
    navbar = get_navbar(request, 'courses')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Add Course | Admin Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .form-container {{ max-width: 600px; margin: 0 auto; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; font-weight: 600; color: #2d3748; }}
            .form-group input, .form-group select {{ width: 100%; padding: 12px; border: 2px solid #e2e8f0; border-radius: 8px; }}
            .form-group input:focus {{ outline: none; border-color: #667eea; }}
            .btn-submit {{ width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; }}
            .required:after {{ content: " *"; color: #f56565; }}
            .help-text {{ font-size: 12px; color: #718096; margin-top: 5px; }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Add New Course</h2>
                    <a href="/admin-dashboard/courses/" class="btn btn-primary"> Back to Courses</a>
                </div>
                
                <div class="form-container">
                    <form method="post" action="/admin-dashboard/courses/add/submit/">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{request.COOKIES.get('csrftoken', '')}">
                        <div class="form-group">
                            <label class="required">Course Code</label>
                            <input type="text" name="code" placeholder="e.g., CS001" required>
                            <div class="help-text">Unique identifier for the course</div>
                        </div>
                        <div class="form-group">
                            <label class="required">Course Name</label>
                            <input type="text" name="name" placeholder="e.g., Introduction to Computer Science" required>
                        </div>
                        <div class="form-group">
                            <label class="required">Department</label>
                            <input type="text" name="department" placeholder="e.g., Computing and Informatics" required>
                        </div>
                        <div class="form-group">
                            <label class="required">Credits</label>
                            <input type="number" name="credits" min="1" max="6" required>
                            <div class="help-text">Credit hours for this course</div>
                        </div>
                        <div class="form-group">
                            <label class="required">Maximum Capacity (Students)</label>
                            <input type="number" name="max_students" min="1" max="500" required>
                            <div class="help-text">Maximum number of students who can enroll in this course</div>
                        </div>
                        <div class="form-group">
                            <label class="required">Open for Enrollment?</label>
                            <select name="is_open_for_enrollment" required>
                                <option value="">-- Select --</option>
                                <option value="True">Yes - Students can enroll</option>
                                <option value="False">No - Enrollment closed</option>
                            </select>
                            <div class="help-text">Set to "Yes" to allow student enrollment</div>
                        </div>
                        <button type="submit" class="btn-submit"> Create Course</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

@csrf_exempt
@login_required
@staff_member_required
@csrf_exempt
@login_required
@staff_member_required
@csrf_exempt
@login_required
@staff_member_required
def add_course_submit(request):
    """Submit new course - ADMIN must provide ALL values"""
    if request.method == 'POST':
        code = request.POST.get('code').upper()
        name = request.POST.get('name')
        department = request.POST.get('department')
        credits = request.POST.get('credits')
        max_students = request.POST.get('max_students')
        is_open_for_enrollment = request.POST.get('is_open_for_enrollment') == 'True'
        
        # Validate required fields
        if not all([code, name, department, credits, max_students]):
            return HttpResponse('<script>alert("All fields are required!"); window.history.back();</script>')
        
        if Course.objects.filter(code=code).exists():
            return HttpResponse('<script>alert("Course code already exists!"); window.history.back();</script>')
        
        Course.objects.create(
            code=code,
            name=name,
            department=department,
            credits=int(credits),
            max_students=int(max_students),
            is_open_for_enrollment=is_open_for_enrollment
        )
        
        return HttpResponse('<script>alert("Course created successfully!"); window.location.href="/admin-dashboard/courses/";</script>')
    
    return redirect('/admin-dashboard/courses/')('/admin-dashboard/courses/')('/admin-dashboard/courses/')

# ==================== SESSION MANAGEMENT ====================

@login_required
@staff_member_required
def manage_sessions(request):
    """Manage sessions"""
    navbar = get_navbar(request, 'sessions')
    sessions = ClassSession.objects.select_related('lecturer__user').all().order_by('-start_time')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage Sessions | Admin Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        {navbar}
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Session Management</h2>
                    <div>
                        <a href="/admin-dashboard/" class="btn btn-primary"> Back</a>
                        <a href="/admin/accounts/classsession/add/" class="btn btn-success">+ Create Session</a>
                    </div>
                </div>
                <div class="table-container">
                    <table>
                        <thead><tr><th>Course</th><th>Title</th><th>Lecturer</th><th>Date</th><th>Status</th></tr></thead>
                        <tbody>
                            {''.join([f'<tr><td>{s.course_code}</td><td>{s.title}</td><td>{s.lecturer.user.get_full_name()}</td><td>{s.start_time.strftime("%Y-%m-%d %H:%M")}</td><td>{s.status}</td></tr>' for s in sessions]) or '<tr><td colspan="5">No sessions</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

# ==================== EXPORT ====================

@login_required
@staff_member_required
def export_report(request):
    """Export attendance report as CSV"""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Student Name', 'Reg No', 'Course', 'Session', 'Status', 'Confidence', 'Time'])
    
    records = AttendanceRecord.objects.select_related('student__user', 'session').order_by('-marked_at')
    
    for r in records:
        writer.writerow([
            r.marked_at.strftime('%Y-%m-%d'),
            r.student.user.get_full_name(),
            r.student.user.reg_no or 'N/A',
            r.session.course_code,
            r.session.title,
            r.status.upper(),
            f"{r.confidence:.0%}",
            r.marked_at.strftime('%H:%M:%S')
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename=attendance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return response

# ==================== ADDITIONAL FUNCTIONS ====================

@login_required
@staff_member_required
def edit_programme_form(request, programme_id):
    """Edit programme form"""
    navbar = get_navbar(request, 'programmes')
    programme = get_object_or_404(Programme, id=programme_id)
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit Programme | Admin Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .form-container {{ max-width: 600px; margin: 0 auto; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; font-weight: 600; }}
            .form-group input {{ width: 100%; padding: 12px; border: 2px solid #e2e8f0; border-radius: 8px; }}
            .btn-submit {{ width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; }}
        </style>
    </head>
    <body>
        {navbar}
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Edit Programme: {programme.code}</h2>
                    <a href="/admin-dashboard/programmes/" class="btn btn-primary"> Back</a>
                </div>
                <div class="form-container">
                    <form method="post" action="/admin-dashboard/programmes/{programme.id}/edit/submit/">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{request.COOKIES.get('csrftoken', '')}">
                        <div class="form-group">
                            <label>Programme Name</label>
                            <input type="text" name="name" value="{programme.name}" required>
                        </div>
                        <div class="form-group">
                            <label>Department</label>
                            <input type="text" name="department" value="{programme.department}" required>
                        </div>
                        <div class="form-group">
                            <label>Duration (Years)</label>
                            <input type="number" name="duration_years" value="{programme.duration_years}" min="1" max="6">
                        </div>
                        <button type="submit" class="btn-submit"> Save Changes</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

@csrf_exempt
@login_required
@staff_member_required
def edit_programme_submit(request, programme_id):
    """Submit programme edits"""
    if request.method == 'POST':
        programme = get_object_or_404(Programme, id=programme_id)
        programme.name = request.POST.get('name')
        programme.department = request.POST.get('department')
        programme.duration_years = int(request.POST.get('duration_years', 4))
        programme.save()
        
        return HttpResponse('<script>alert("Programme updated successfully!"); window.location.href="/admin-dashboard/programmes/";</script>')
    
    return redirect('/admin-dashboard/programmes/')

@login_required
@staff_member_required
def edit_semester_form(request, semester_id):
    """Edit semester form"""
    navbar = get_navbar(request, 'semesters')
    semester = get_object_or_404(Semester, id=semester_id)
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit Semester | Admin Dashboard</title>
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
                    <h2> Edit Semester</h2>
                    <a href="/admin-dashboard/semesters/" class="btn btn-primary"> Back</a>
                </div>
                <div class="form-container">
                    <form method="post" action="/admin-dashboard/semesters/{semester.id}/edit/submit/">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{request.COOKIES.get('csrftoken', '')}">
                        <div class="form-group">
                            <label>Semester Number</label>
                            <select name="number">
                                <option value="1" {'selected' if semester.number == 1 else ''}>Semester 1</option>
                                <option value="2" {'selected' if semester.number == 2 else ''}>Semester 2</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Academic Year</label>
                            <input type="text" name="academic_year" value="{semester.academic_year}" required>
                        </div>
                        <div class="form-group">
                            <label>Start Date</label>
                            <input type="date" name="start_date" value="{semester.start_date}" required>
                        </div>
                        <div class="form-group">
                            <label>End Date</label>
                            <input type="date" name="end_date" value="{semester.end_date}" required>
                        </div>
                        <div class="form-group">
                            <label>Set as Current Semester?</label>
                            <select name="is_current">
                                <option value="False" {'selected' if not semester.is_current else ''}>No</option>
                                <option value="True" {'selected' if semester.is_current else ''}>Yes</option>
                            </select>
                        </div>
                        <button type="submit" class="btn-submit"> Save Changes</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

@csrf_exempt
@login_required
@staff_member_required
def edit_semester_submit(request, semester_id):
    """Submit semester edits"""
    if request.method == 'POST':
        semester = get_object_or_404(Semester, id=semester_id)
        semester.number = int(request.POST.get('number'))
        semester.academic_year = request.POST.get('academic_year')
        semester.start_date = request.POST.get('start_date')
        semester.end_date = request.POST.get('end_date')
        semester.is_current = request.POST.get('is_current') == 'True'
        
        if semester.is_current:
            Semester.objects.filter(is_current=True).exclude(id=semester.id).update(is_current=False)
        
        semester.save()
        
        return HttpResponse('<script>alert("Semester updated successfully!"); window.location.href="/admin-dashboard/semesters/";</script>')
    
    return redirect('/admin-dashboard/semesters/')

@login_required
@staff_member_required
def set_current_semester(request, semester_id):
    """Set a semester as current"""
    Semester.objects.filter(is_current=True).update(is_current=False)
    semester = get_object_or_404(Semester, id=semester_id)
    semester.is_current = True
    semester.save()
    
    return HttpResponse('<script>alert("Current semester updated!"); window.location.href="/admin-dashboard/semesters/";</script>')

@login_required
@staff_member_required
@login_required
@staff_member_required
def edit_course_form(request, course_code):
    """Edit course form - ADMIN updates all course data"""
    navbar = get_navbar(request, 'courses')
    course = get_object_or_404(Course, code=course_code)
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit Course | Admin Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .form-container {{ max-width: 600px; margin: 0 auto; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; font-weight: 600; }}
            .form-group input, .form-group select {{ width: 100%; padding: 12px; border: 2px solid #e2e8f0; border-radius: 8px; }}
            .btn-submit {{ width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; }}
            .help-text {{ font-size: 12px; color: #718096; margin-top: 5px; }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Edit Course: {course.code}</h2>
                    <a href="/admin-dashboard/courses/" class="btn btn-primary"> Back to Courses</a>
                </div>
                
                <div class="form-container">
                    <form method="post" action="/admin-dashboard/courses/{course.code}/edit/submit/">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{request.COOKIES.get('csrftoken', '')}">
                        <div class="form-group">
                            <label>Course Code</label>
                            <input type="text" value="{course.code}" disabled style="background:#f0f0f0;">
                        </div>
                        <div class="form-group">
                            <label>Course Name</label>
                            <input type="text" name="name" value="{course.name}" required>
                        </div>
                        <div class="form-group">
                            <label>Department</label>
                            <input type="text" name="department" value="{course.department}" required>
                        </div>
                        <div class="form-group">
                            <label>Credits</label>
                            <input type="number" name="credits" value="{course.credits}" min="1" max="6">
                        </div>
                        <div class="form-group">
                            <label>Maximum Capacity (Students)</label>
                            <input type="number" name="max_students" value="{course.max_students}" min="1" max="500">
                            <div class="help-text">Current enrolled: {course.get_enrolled_count()} / {course.max_students}</div>
                        </div>
                        <div class="form-group">
                            <label>Open for Enrollment?</label>
                            <select name="is_open_for_enrollment">
                                <option value="True" {'selected' if course.is_open_for_enrollment else ''}>Yes - Students can enroll</option>
                                <option value="False" {'selected' if not course.is_open_for_enrollment else ''}>No - Enrollment closed</option>
                            </select>
                        </div>
                        <button type="submit" class="btn-submit"> Save Changes</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

@csrf_exempt
@login_required
@staff_member_required
@csrf_exempt
@login_required
@staff_member_required
def edit_course_submit(request, course_code):
    """Submit course edits - ADMIN updates capacity"""
    if request.method == 'POST':
        course = get_object_or_404(Course, code=course_code)
        course.name = request.POST.get('name')
        course.department = request.POST.get('department')
        course.credits = int(request.POST.get('credits', 3))
        course.max_students = int(request.POST.get('max_students', 100))
        course.is_open_for_enrollment = request.POST.get('is_open_for_enrollment') == 'True'
        course.save()
        
        return HttpResponse('<script>alert("Course updated successfully!"); window.location.href="/admin-dashboard/courses/";</script>')
    
    return redirect('/admin-dashboard/courses/')('/admin-dashboard/courses/')

@login_required
@staff_member_required
def assign_lecturer_form(request, course_code):
    """Assign lecturer to course"""
    navbar = get_navbar(request, 'courses')
    course = get_object_or_404(Course, code=course_code)
    lecturers = LecturerProfile.objects.select_related('user').all()
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Assign Lecturer | Admin Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .form-container {{ max-width: 600px; margin: 0 auto; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; font-weight: 600; }}
            .form-group select {{ width: 100%; padding: 12px; border: 2px solid #e2e8f0; border-radius: 8px; }}
            .btn-submit {{ width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; }}
        </style>
    </head>
    <body>
        {navbar}
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Assign Lecturer to {course.code}</h2>
                    <a href="/admin-dashboard/courses/" class="btn btn-primary"> Back</a>
                </div>
                <div class="form-container">
                    <form method="post" action="/admin-dashboard/courses/{course.code}/assign/submit/">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{request.COOKIES.get('csrftoken', '')}">
                        <div class="form-group">
                            <label>Select Lecturer</label>
                            <select name="lecturer_staff_id">
                                <option value="">-- None --</option>
                                {''.join([f'<option value="{l.staff_id}">{l.user.get_full_name()} ({l.staff_id})</option>' for l in lecturers])}
                            </select>
                        </div>
                        <button type="submit" class="btn-submit"> Assign Lecturer</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

@csrf_exempt
@login_required
@staff_member_required
def assign_lecturer_submit(request, course_code):
    """Submit lecturer assignment"""
    if request.method == 'POST':
        course = get_object_or_404(Course, code=course_code)
        course.lecturer_staff_id = request.POST.get('lecturer_staff_id') or None
        course.save()
        
        return HttpResponse('<script>alert("Lecturer assigned!"); window.location.href="/admin-dashboard/courses/";</script>')
    
    return redirect('/admin-dashboard/courses/')

# ==================== STUDENT YEAR MANAGEMENT ====================

@login_required
@staff_member_required
def manage_students(request):
    """Manage students - update years, programmes, semesters"""
    navbar = get_navbar(request, 'students')
    students = StudentProfile.objects.select_related('user', 'programme', 'semester').all()
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage Students | Admin Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .btn-sm {{ padding: 5px 10px; font-size: 12px; }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2>👨‍🎓 Student Management</h2>
                    <div>
                        <a href="/admin-dashboard/" class="btn btn-primary">← Back</a>
                        <a href="/admin-dashboard/users/add/" class="btn btn-success">+ Add Student</a>
                        <a href="/admin-dashboard/students/promote/" class="btn btn-warning">📈 Promote All Students</a>
                    </div>
                </div>
                
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Reg No</th>
                                <th>Student Name</th>
                                <th>Programme</th>
                                <th>Current Year</th>
                                <th>Semester</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td><strong>{s.user.reg_no or "N/A"}</strong></td>
                                <td>{s.user.get_full_name()}</d>
                                <td>{s.programme.name if s.programme else "Not Assigned"}</d>
                                <td>
                                    <select id="year_{s.id}" onchange="updateYear({s.id})">
                                        <option value="1" {'selected' if s.year_of_study == 1 else ''}>Year 1</option>
                                        <option value="2" {'selected' if s.year_of_study == 2 else ''}>Year 2</option>
                                        <option value="3" {'selected' if s.year_of_study == 3 else ''}>Year 3</option>
                                        <option value="4" {'selected' if s.year_of_study == 4 else ''}>Year 4</option>
                                    </select>
                                </d>
                                <td>{s.semester if s.semester else "Not Set"}</d>
                                <td>
                                    <button onclick="updateYear({s.id})" class="btn btn-primary btn-sm">Update Year</button>
                                    <a href="/admin/accounts/studentprofile/{s.id}/change/" class="btn btn-info btn-sm">Edit</a>
                                </d>
                             </d>
                            ''' for s in students]) or '<tr><td colspan="6">No students found</d'}
                        </tbody>
                    ……
                </div>
            </div>
        </div>
        
        <script>
            function updateYear(studentId) {{
                var select = document.getElementById('year_' + studentId);
                var year = select.value;
                fetch('/admin-dashboard/students/' + studentId + '/update-year/', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': '{request.COOKIES.get('csrftoken', '')}'
                    }},
                    body: 'year=' + year
                }}).then(response => response.json())
                  .then(data => {{
                      if(data.success) {{
                          alert('Year updated successfully!');
                          location.reload();
                      }} else {{
                          alert('Error: ' + data.error);
                      }}
                  }});
            }}
        </script>
    </body>
    </html>
    '''
    return HttpResponse(html)

@csrf_exempt
@login_required
@staff_member_required
def update_student_year(request, student_id):
    """Update a student's year of study"""
    if request.method == 'POST':
        try:
            student = get_object_or_404(StudentProfile, id=student_id)
            new_year = int(request.POST.get('year', 1))
            student.year_of_study = new_year
            student.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@staff_member_required
def promote_all_students(request):
    """Promote all students to next year"""
    navbar = get_navbar(request, 'students')
    
    if request.method == 'POST':
        # Get current year and promote
        students = StudentProfile.objects.all()
        for student in students:
            if student.year_of_study < 4:
                student.year_of_study += 1
                student.save()
        
        return HttpResponse('''
        <script>
            alert("All students promoted to the next year!");
            window.location.href = "/admin-dashboard/students/";
        </script>
        ''')
    
    # GET request - show confirmation page
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Promote Students | Admin Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .confirm-box {{
                text-align: center;
                padding: 40px;
                background: white;
                border-radius: 15px;
                max-width: 500px;
                margin: 0 auto;
            }}
            .warning {{
                background: #fff3cd;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                color: #856404;
            }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="confirm-box">
                <h2>📈 Promote All Students</h2>
                <div class="warning">
                    ⚠️ Warning: This will increment the year of study for ALL students.<br>
                    Year 4 students will remain in Year 4.
                </div>
                <form method="post">
                    <input type="hidden" name="csrfmiddlewaretoken" value="{request.COOKIES.get('csrftoken', '')}">
                    <button type="submit" class="btn btn-warning" style="padding:12px 30px;">Confirm Promotion</button>
                    <a href="/admin-dashboard/students/" class="btn btn-primary">Cancel</a>
                </form>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)



# ==================== COURSE ENROLLMENT MANAGEMENT ====================

@login_required
@staff_member_required
def manage_enrollments(request):
    """Manage student course enrollments"""
    navbar = get_navbar(request, 'enrollments')
    
    students = StudentProfile.objects.select_related('user', 'programme').all()
    courses = Course.objects.all().order_by('code')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage Enrollments | Admin Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .enrollment-card {{
                background: white;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            .student-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 15px;
                cursor: pointer;
            }}
            .course-list {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 10px;
                margin-top: 10px;
            }}
            .course-item {{
                background: #f8f9fa;
                padding: 10px;
                border-radius: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .checkbox {{
                width: 20px;
                height: 20px;
                cursor: pointer;
            }}
            .btn-enroll {{
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 10px;
            }}
            .search-box {{
                margin-bottom: 20px;
                padding: 10px;
                width: 100%;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
            }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Course Enrollment Management</h2>
                    <div>
                        <a href="/admin-dashboard/" class="btn btn-primary"> Back</a>
                        <a href="/admin-dashboard/enrollments/bulk/" class="btn btn-success"> Bulk Enroll by Programme</a>
                    </div>
                </div>
                
                <input type="text" id="searchInput" class="search-box" placeholder="Search student by name or registration number...">
                
                <div id="studentsList">
                    {''.join([f'''
                    <div class="enrollment-card" data-name="{s.user.get_full_name().lower()} {s.user.reg_no or ''}">
                        <div class="student-header" onclick="toggleCourses({s.id})">
                            <strong>{s.user.get_full_name()}</strong> - {s.user.reg_no or 'N/A'}
                            <span style="float:right">▼</span>
                        </div>
                        <div id="courses-{s.id}" style="display:none; padding:15px;">
                            <div class="course-list">
                                {''.join([f'''
                                <label class="course-item">
                                    <span><strong>{c.code}</strong> - {c.name}</span>
                                    <input type="checkbox" class="checkbox" data-student="{s.id}" data-course="{c.code}" 
                                           onchange="toggleCourse({s.id}, '{c.code}', this.checked)">
                                </label>
                                ''' for c in courses])}
                            </div>
                            <button class="btn-enroll" onclick="saveEnrollments({s.id})"> Save Enrollments</button>
                        </div>
                    </div>
                    ''' for s in students]) or '<p>No students found. Create students first.</p>'}
                </div>
            </div>
        </div>
        
        <script>
            function toggleCourses(studentId) {{
                var div = document.getElementById('courses-' + studentId);
                if (div.style.display === 'none') {{
                    div.style.display = 'block';
                }} else {{
                    div.style.display = 'none';
                }}
            }}
            
            function toggleCourse(studentId, courseCode, isChecked) {{
                // Store in localStorage temporary
                var key = 'enroll_' + studentId + '_' + courseCode;
                localStorage.setItem(key, isChecked);
            }}
            
            async function saveEnrollments(studentId) {{
                var courses = [];
                var checkboxes = document.querySelectorAll('.checkbox[data-student="' + studentId + '"]');
                checkboxes.forEach(cb => {{
                    if (cb.checked) {{
                        courses.push(cb.getAttribute('data-course'));
                    }}
                }});
                
                var response = await fetch('/admin-dashboard/enrollments/save/', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    }},
                    body: JSON.stringify({{ student_id: studentId, courses: courses }})
                }});
                
                var data = await response.json();
                if (data.success) {{
                    alert('Enrollments saved successfully!');
                }} else {{
                    alert('Error: ' + data.error);
                }}
            }}
            
            function getCookie(name) {{
                var cookieValue = null;
                if (document.cookie && document.cookie !== '') {{
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {{
                        var cookie = cookies[i].trim();
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {{
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }}
                    }}
                }}
                return cookieValue;
            }}
            
            // Search functionality
            document.getElementById('searchInput').addEventListener('keyup', function() {{
                var filter = this.value.toLowerCase();
                var cards = document.getElementsByClassName('enrollment-card');
                for (var i = 0; i < cards.length; i++) {{
                    var name = cards[i].getAttribute('data-name') || '';
                    if (name.includes(filter)) {{
                        cards[i].style.display = 'block';
                    }} else {{
                        cards[i].style.display = 'none';
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    '''
    return HttpResponse(html)

@csrf_exempt
@login_required
@staff_member_required
def save_enrollments(request):
    """Save student course enrollments"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            student_id = data.get('student_id')
            course_codes = data.get('courses', [])
            
            student = get_object_or_404(StudentProfile, id=student_id)
            courses = Course.objects.filter(code__in=course_codes)
            
            # Clear existing and add new
            student.enrolled_courses.clear()
            student.enrolled_courses.add(*courses)
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@staff_member_required
def bulk_enroll_by_programme(request):
    """Bulk enroll all students in a programme to courses"""
    navbar = get_navbar(request, 'enrollments')
    programmes = Programme.objects.filter(is_active=True)
    courses = Course.objects.all()
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bulk Enrollment | Admin Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .form-container {{ max-width: 600px; margin: 0 auto; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; font-weight: 600; }}
            .form-group select {{ width: 100%; padding: 12px; border: 2px solid #e2e8f0; border-radius: 8px; }}
            .btn-submit {{ width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Bulk Enroll Students by Programme</h2>
                    <a href="/admin-dashboard/enrollments/" class="btn btn-primary"> Back</a>
                </div>
                
                <div class="form-container">
                    <form method="post" action="/admin-dashboard/enrollments/bulk/submit/">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{{ request.COOKIES.csrftoken }}">
                        <div class="form-group">
                            <label>Select Programme</label>
                            <select name="programme_id" required>
                                <option value="">-- Select Programme --</option>
                                {''.join([f'<option value="{p.id}">{p.code} - {p.name}</option>' for p in programmes])}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Select Year of Study</label>
                            <select name="year_of_study">
                                <option value="0">All Years</option>
                                <option value="1">Year 1</option>
                                <option value="2">Year 2</option>
                                <option value="3">Year 3</option>
                                <option value="4">Year 4</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Select Courses to Enroll</label>
                            <div class="course-list">
                                {''.join([f'<label><input type="checkbox" name="courses" value="{c.code}"> {c.code} - {c.name}</label><br>' for c in courses])}
                            </div>
                        </div>
                        <button type="submit" class="btn-submit"> Bulk Enroll Students</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

@csrf_exempt
@login_required
@staff_member_required
def bulk_enroll_submit(request):
    """Process bulk enrollment"""
    if request.method == 'POST':
        programme_id = request.POST.get('programme_id')
        year_of_study = int(request.POST.get('year_of_study', 0))
        course_codes = request.POST.getlist('courses')
        
        students = StudentProfile.objects.filter(programme_id=programme_id)
        if year_of_study > 0:
            students = students.filter(year_of_study=year_of_study)
        
        courses = Course.objects.filter(code__in=course_codes)
        
        enrolled_count = 0
        for student in students:
            for course in courses:
                student.enrolled_courses.add(course)
                enrolled_count += 1
        
        return HttpResponse(f'''
        <script>
            alert("Successfully enrolled {enrolled_count} students!");
            window.location.href = "/admin-dashboard/enrollments/";
        </script>
        ''')
    
    return redirect('/admin-dashboard/enrollments/')


@login_required
@staff_member_required
def course_students(request, course_code):
    """View all students enrolled in a course"""
    navbar = get_navbar(request, 'courses')
    course = get_object_or_404(Course, code=course_code)
    students = StudentProfile.objects.filter(enrolled_courses__code=course.code).select_related("user")
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Course Students | {course.code}</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Students Enrolled in {course.code} - {course.name}</h2>
                    <div>
                        <a href="/admin-dashboard/courses/" class="btn btn-primary"> Back to Courses</a>
                    </div>
                </div>
                
                <div class="stats-grid" style="margin-bottom:20px;">
                    <div class="stat-card"><div class="stat-value">{students.count()}</div><div>Enrolled Students</div></div>
                    <div class="stat-card"><div class="stat-value">{course.max_students}</div><div>Max Capacity</div></div>
                    <div class="stat-card"><div class="stat-value">{course.get_available_seats()}</div><div>Available Seats</div></div>
                </div>
                
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr><th>Reg No</th><th>Student Name</th><th>Email</th><th>Programme</th><th>Year</th><th>Actions</th></tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td>{s.user.reg_no or "N/A"}</d>
                                <td>{s.user.get_full_name()}</d>
                                <td>{s.user.email}</d>
                                <td>{s.programme.name if s.programme else "N/A"}</d>
                                <td>Year {s.year_of_study}</d>
                                <td>
                                    <a href="/admin/accounts/studentprofile/{s.id}/change/" class="btn btn-primary btn-sm">Edit</a>
                                    <a href="/admin-dashboard/courses/{course.code}/remove-student/{s.id}/" class="btn btn-danger btn-sm">Remove</a>
                                </d>
                             </d>
                            ''' for s in students]) or '<tr><td colspan="6">No students enrolled in this course</d'}
                        </tbody>
                    ……>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

@login_required
@staff_member_required
def remove_student_from_course(request, course_code, student_id):
    """Remove a student from a course"""
    if request.method == 'POST':
        course = get_object_or_404(Course, code=course_code)
        student = get_object_or_404(StudentProfile, id=student_id)
        student.enrolled_courses.remove(course)
        return HttpResponse(f'''
        <script>
            alert("Student removed from course!");
            window.location.href = "/admin-dashboard/courses/{course_code}/students/";
        </script>
        ''')
    
    return redirect(f'/admin-dashboard/courses/{course_code}/students/')



@login_required
@staff_member_required
def edit_course_capacity(request, course_code):
    """Edit course capacity only - ADMIN sets capacity"""
    navbar = get_navbar(request, 'courses')
    course = get_object_or_404(Course, code=course_code)
    
    if request.method == 'POST':
        new_capacity = request.POST.get('max_students')
        if new_capacity and new_capacity.isdigit():
            course.max_students = int(new_capacity)
            course.save()
            return HttpResponse(f'''
            <script>
                alert("Capacity updated to {new_capacity}!");
                window.location.href = "/admin-dashboard/courses/";
            </script>
            ''')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit Capacity | {course.code}</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .form-container {{ max-width: 500px; margin: 0 auto; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; font-weight: 600; }}
            .form-group input {{ width: 100%; padding: 12px; border: 2px solid #e2e8f0; border-radius: 8px; }}
            .btn-submit {{ width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; }}
            .current-info {{ background: #e2e8f0; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Edit Course Capacity: {course.code}</h2>
                    <a href="/admin-dashboard/courses/" class="btn btn-primary"> Back to Courses</a>
                </div>
                
                <div class="form-container">
                    <div class="current-info">
                        <strong>Current Status:</strong><br>
                        Course: {course.name}<br>
                        Enrolled Students: {course.get_enrolled_count()}<br>
                        Current Capacity: {course.max_students if course.max_students else "Not set"}
                    </div>
                    
                    <form method="post">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{request.COOKIES.get('csrftoken', '')}">
                        <div class="form-group">
                            <label>Maximum Capacity (Students)</label>
                            <input type="number" name="max_students" value="{course.max_students if course.max_students else ''}" min="1" max="500" required>
                            <div class="help-text" style="font-size:12px; color:#666; margin-top:5px;">Set the maximum number of students for this course</div>
                        </div>
                        <button type="submit" class="btn-submit"> Update Capacity</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)







@login_required
@staff_member_required
def all_attendance(request):
    """View all attendance records with check-in/out details"""
    navbar = get_navbar(request, 'attendance')
    records = AttendanceRecord.objects.select_related('student__user', 'session__lecturer__user').order_by('-marked_at')
    
    total = records.count()
    present = records.filter(status='present').count()
    late = records.filter(status='late').count()
    absent = records.filter(status='absent').count()
    
    total_minutes = records.aggregate(total=models.Sum('duration_minutes'))['total'] or 0
    total_hours = total_minutes // 60
    total_mins = total_minutes % 60
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>All Attendance Records | Admin</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .summary-stats {{
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }}
            .stat-box {{
                background: white;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                flex: 1;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .stat-number {{ font-size: 1.5rem; font-weight: bold; color: #667eea; }}
            .badge-present {{ background: #c6f6d5; color: #22543d; padding: 4px 12px; border-radius: 20px; }}
            .badge-late {{ background: #feebc8; color: #744210; padding: 4px 12px; border-radius: 20px; }}
            .badge-absent {{ background: #fed7d7; color: #742a2a; padding: 4px 12px; border-radius: 20px; }}
            .table-container {{ overflow-x: auto; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #667eea; color: white; }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> All Attendance Records</h2>
                    <div>
                        <a href="/admin-dashboard/" class="btn btn-primary"> Back to Dashboard</a>
                        <a href="/admin-dashboard/export/" class="btn btn-success"> Export Report</a>
                    </div>
                </div>
                
                <div class="summary-stats">
                    <div class="stat-box"><div class="stat-number">{total}</div><div>Total Records</div></div>
                    <div class="stat-box"><div class="stat-number">{present}</div><div>Present</div></div>
                    <div class="stat-box"><div class="stat-number">{late}</div><div>Late</div></div>
                    <div class="stat-box"><div class="stat-number">{absent}</div><div>Absent</div></div>
                    <div class="stat-box"><div class="stat-number">{total_hours}h {total_mins}m</div><div>Total Class Time</div></div>
                </div>
                
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Student</th>
                                <th>Reg No</th>
                                <th>Course</th>
                                <th>Session</th>
                                <th>Lecturer</th>
                                <th>Check In</th>
                                <th>Check Out</th>
                                <th>Duration</th>
                                <th>Status</th>
                                <th>Confidence</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td>{r.student.user.get_full_name()}</d>
                                <td>{r.student.user.reg_no or "N/A"}</d>
                                <td>{r.session.course_code}</d>
                                <td>{r.session.title[:30]}</d>
                                <td>{r.session.lecturer.user.get_full_name() if r.session.lecturer else "N/A"}</d>
                                <td>{r.check_in_time.strftime("%H:%M:%S") if r.check_in_time else "-"}</d>
                                <td>{r.check_out_time.strftime("%H:%M:%S") if r.check_out_time else "-"}</d>
                                <td>{r.duration_minutes} min</d>
                                <td><span class="badge badge-{r.status}">{r.status.upper()}</span></d>
                                <td>{r.confidence:.0%}</d>
                                <td>{r.marked_at.strftime("%Y-%m-%d %H:%M")}</d>
                             </d>
                            ''' for r in records[:100]]) or '<tr><td colspan="11">No attendance records found</d'}
                        </tbody>
                    </table>
                </div>
                {f'<p>Showing last 100 records. Total: {total} records.</p>' if total > 100 else ''}
            </div>
        </div>
        
        <div class="footer">
            <p>Karatina University - Admin Attendance Report</p>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)



