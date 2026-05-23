from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Count, Sum
from django.views.decorators.csrf import csrf_exempt
from apps.accounts.models import AttendanceRecord, StudentProfile, ClassSession, Programme, Semester
from apps.courses.models import Course
from datetime import datetime
import csv
import json
import base64
import cv2
import numpy as np
from PIL import Image
from io import BytesIO, StringIO
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Count, Sum
from apps.accounts.models import AttendanceRecord, StudentProfile, ClassSession, Programme, Semester
from apps.courses.models import Course
from datetime import datetime
import csv
from io import StringIO

def get_navbar(request, active):
    user = request.user
    return f'''
    <div class="navbar">
        <div class="navbar-brand">
            <span>🎓</span>
            <span>Face Recognition Attendance System</span>
        </div>
        <div class="navbar-links">
            <a href="/student/dashboard/"> Dashboard</a>
            <a href="/student/available-courses/"> Enroll Courses</a>
            <a href="/student/my-courses/"> My Courses</a>
            <a href="/student/profile/"> Profile</a>
            <a href="/student/attendance/"> Attendance</a>
            <a href="/student/enroll-face/"> Enroll Face</a>
            <a href="/logout/" class="btn-danger"> Logout</a>
        </div>
        <div class="user-info">
            <div class="user-avatar">{user.get_full_name()[0] if user.get_full_name() else user.username[0]}</div>
            <span>{user.get_full_name() or user.username}</span>
        </div>
    </div>
    '''

@login_required
def dashboard(request):
    if request.user.user_type != 'student':
        return HttpResponse("Access Denied")
    
    navbar = get_navbar(request, 'dashboard')
    student = StudentProfile.objects.get(user=request.user)
    
    total = AttendanceRecord.objects.filter(student=student).count()
    present = AttendanceRecord.objects.filter(student=student, status='present').count()
    late = AttendanceRecord.objects.filter(student=student, status='late').count()
    absent = AttendanceRecord.objects.filter(student=student, status='absent').count()
    percentage = (present / total * 100) if total > 0 else 0
    
    total_minutes = AttendanceRecord.objects.filter(student=student).aggregate(total=Sum('duration_minutes'))['total'] or 0
    total_hours = total_minutes // 60
    total_remain = total_minutes % 60
    
    recent = AttendanceRecord.objects.filter(student=student).select_related('session').order_by('-marked_at')[:10]
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head><title>Student Dashboard</title><link rel="stylesheet" href="/static/css/style.css"></head>
    <body>
        {navbar}
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-value">{total}</div><div>Total</div></div>
                <div class="stat-card"><div class="stat-value">{present}</div><div>Present</div></div>
                <div class="stat-card"><div class="stat-value">{late}</div><div>Late</div></div>
                <div class="stat-card"><div class="stat-value">{absent}</div><div>Absent</div></div>
                <div class="stat-card"><div class="stat-value">{percentage:.1f}%</div><div>Rate</div></div>
                <div class="stat-card"><div class="stat-value">{total_hours}h {total_remain}m</div><div>Total Time</div></div>
            </div>
            <div class="card">
                <div class="card-header"><h3>Recent Attendance</h3><a href="/student/attendance/">View All</a></div>
                <div class="table-container">
                    <table>
                        <thead><tr><th>Course</th><th>Session</th><th>Date</th><th>Check In</th><th>Check Out</th><th>Duration</th><th>Status</th></tr></thead>
                        <tbody>
                            {''.join([f'<tr><td>{r.session.course_code}</td><td>{r.session.title}</td><td>{r.session.start_time.strftime("%Y-%m-%d")}</td><td>{r.check_in_time.strftime("%H:%M:%S") if r.check_in_time else "-"}</td><td>{r.check_out_time.strftime("%H:%M:%S") if r.check_out_time else "-"}</td><td>{r.duration_minutes} min</td><td><span class="badge badge-{r.status}">{r.status.upper()}</span></td></tr>' for r in recent]) or '<tr><td colspan="7">No records</td></tr>'}
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
def attendance_report(request):
    navbar = get_navbar(request, 'attendance')
    student = StudentProfile.objects.get(user=request.user)
    records = AttendanceRecord.objects.filter(student=student).select_related('session').order_by('-marked_at')
    
    total = records.count()
    present = records.filter(status='present').count()
    late = records.filter(status='late').count()
    absent = records.filter(status='absent').count()
    percentage = (present / total * 100) if total > 0 else 0
    total_minutes = records.aggregate(total=Sum('duration_minutes'))['total'] or 0
    total_hours = total_minutes // 60
    total_remain = total_minutes % 60
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head><title>Attendance Report</title><link rel="stylesheet" href="/static/css/style.css"></head>
    <body>
        {navbar}
        <div class="container">
            <div class="summary-box"><h2>Summary</h2>
                <div class="summary-stats">
                    <div><div class="summary-number">{total}</div><div>Total</div></div>
                    <div><div class="summary-number">{present}</div><div>Present</div></div>
                    <div><div class="summary-number">{late}</div><div>Late</div></div>
                    <div><div class="summary-number">{absent}</div><div>Absent</div></div>
                    <div><div class="summary-number">{percentage:.1f}%</div><div>Rate</div></div>
                    <div><div class="summary-number">{total_hours}h {total_remain}m</div><div>Time</div></div>
                </div>
            </div>
            <div class="card">
                <div class="card-header"><h2>Details</h2><div><a href="/student/dashboard/">Back</a><a href="/student/attendance/export/">Export CSV</a></div></div>
                <div class="table-container">
                    <table>
                        <thead><tr><th>Course</th><th>Session</th><th>Date</th><th>Check In</th><th>Check Out</th><th>Duration</th><th>Status</th><th>Confidence</th></tr></thead>
                        <tbody>
                            {''.join([f'<tr><td>{r.session.course_code}</td><td>{r.session.title}</td><td>{r.session.start_time.strftime("%Y-%m-%d")}</td><td>{r.check_in_time.strftime("%H:%M:%S") if r.check_in_time else "-"}</td><td>{r.check_out_time.strftime("%H:%M:%S") if r.check_out_time else "-"}</td><td>{r.duration_minutes} min</td><td><span class="badge badge-{r.status}">{r.status.upper()}</span></td><td>{r.confidence:.0%}</td></tr>' for r in records]) or '<tr><td colspan="8">No records</td></tr>'}
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
def export_attendance(request):
    student = StudentProfile.objects.get(user=request.user)
    records = AttendanceRecord.objects.filter(student=student).select_related('session')
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Course', 'Session', 'Date', 'Check In', 'Check Out', 'Duration', 'Status', 'Confidence'])
    
    for r in records:
        writer.writerow([
            r.session.course_code,
            r.session.title,
            r.session.start_time.strftime('%Y-%m-%d'),
            r.check_in_time.strftime('%H:%M:%S') if r.check_in_time else '',
            r.check_out_time.strftime('%H:%M:%S') if r.check_out_time else '',
            r.duration_minutes,
            r.status.upper(),
            f"{r.confidence:.0%}"
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename=attendance_{request.user.username}.csv'
    return response

# Placeholder functions
def profile(request): return HttpResponse("Profile")
def available_courses(request): return HttpResponse("Available Courses")
def my_courses(request): return HttpResponse("My Courses")
def enroll_course(request): return JsonResponse({'success': False})
def drop_course(request): return JsonResponse({'success': False})
def enroll_face(request):
    """Original face enrollment page"""
    navbar = get_navbar(request, 'enroll')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enroll Face | Student Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <style>
            .camera-container {{
                position: relative;
                background: #000;
                border-radius: 15px;
                overflow: hidden;
                aspect-ratio: 4/3;
                margin-bottom: 20px;
            }}
            #video {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                transform: scaleX(-1);
            }}
            #canvas {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
            }}
            .btn-capture {{ background: #48bb78; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; }}
            .processing {{ background: #ed8936; color: white; animation: pulse 1s infinite; }}
            @keyframes pulse {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.7; }} }}
            .success {{ background: #48bb78; color: white; }}
            .error {{ background: #f56565; color: white; }}
            .info {{ background: #4299e1; color: white; }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2> Face Enrollment</h2>
                    <a href="/student/dashboard/" class="btn btn-primary"> Back to Dashboard</a>
                </div>
                
                <div class="camera-container">
                    <video id="video" autoplay playsinline></video>
                    <canvas id="canvas"></canvas>
                </div>
                
                <div style="text-align: center;">
                    <button id="startCameraBtn" class="btn btn-primary"> Start Camera</button>
                    <button id="captureBtn" class="btn-capture" style="display:none;"> Capture & Enroll Face</button>
                    <button id="stopCameraBtn" class="btn btn-danger" style="display:none;"> Stop Camera</button>
                </div>
                
                <div id="resultArea" style="margin-top:20px; padding:15px; border-radius:10px; text-align:center;" class="info">
                    Click "Start Camera" to begin enrollment
                </div>
            </div>
        </div>
        
        <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const startCameraBtn = document.getElementById('startCameraBtn');
            const captureBtn = document.getElementById('captureBtn');
            const stopCameraBtn = document.getElementById('stopCameraBtn');
            const resultArea = document.getElementById('resultArea');
            
            let stream = null;
            let isProcessing = false;
            
            async function startCamera() {{
                resultArea.innerHTML = ' Starting camera...';
                resultArea.className = 'processing';
                try {{
                    stream = await navigator.mediaDevices.getUserMedia({{ video: true }});
                    video.srcObject = stream;
                    startCameraBtn.style.display = 'none';
                    captureBtn.style.display = 'inline-block';
                    stopCameraBtn.style.display = 'inline-block';
                    resultArea.innerHTML = ' Camera ready. Click Capture to enroll.';
                    resultArea.className = 'success';
                }} catch(err) {{
                    resultArea.innerHTML = ' Camera error: ' + err.message;
                    resultArea.className = 'error';
                }}
            }}
            
            function stopCamera() {{
                if (stream) {{
                    stream.getTracks().forEach(track => track.stop());
                    video.srcObject = null;
                }}
                startCameraBtn.style.display = 'inline-block';
                captureBtn.style.display = 'none';
                stopCameraBtn.style.display = 'none';
                resultArea.innerHTML = ' Camera stopped';
                resultArea.className = 'info';
            }}
            
            async function captureAndEnroll() {{
                if (isProcessing) return;
                isProcessing = true;
                resultArea.innerHTML = ' Processing...';
                resultArea.className = 'processing';
                captureBtn.disabled = true;
                
                const ctx = canvas.getContext('2d');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.save();
                ctx.scale(-1, 1);
                ctx.drawImage(video, -canvas.width, 0, canvas.width, canvas.height);
                ctx.restore();
                
                const imageData = canvas.toDataURL('image/jpeg');
                
                try {{
                    const response = await fetch('/student/enroll-face/submit/', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') }},
                        body: JSON.stringify({{ image: imageData }})
                    }});
                    const data = await response.json();
                    if (data.success) {{
                        resultArea.innerHTML = ' ' + data.message;
                        resultArea.className = 'success';
                        setTimeout(() => window.location.href = '/student/profile/', 2000);
                    }} else {{
                        resultArea.innerHTML = ' ' + data.message;
                        resultArea.className = 'error';
                    }}
                }} catch(err) {{
                    resultArea.innerHTML = ' Error: ' + err.message;
                    resultArea.className = 'error';
                }} finally {{
                    isProcessing = false;
                    captureBtn.disabled = false;
                }}
            }}
            
            function getCookie(name) {{
                let value = null;
                if (document.cookie && document.cookie !== '') {{
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {{
                        const cookie = cookies[i].trim();
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {{
                            value = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }}
                    }}
                }}
                return value;
            }}
            
            startCameraBtn.onclick = startCamera;
            captureBtn.onclick = captureAndEnroll;
            stopCameraBtn.onclick = stopCamera;
        </script>
    </body>
    </html>
    '''
    return HttpResponse(html)
def enroll_face_submit(request): return JsonResponse({'success': False})

@csrf_exempt
@login_required
@csrf_exempt
@login_required
@csrf_exempt
@login_required
def enroll_face_cnn(request):
    """CNN-based face enrollment"""
    from django.shortcuts import render
    
    # Handle GET request - show the enrollment page
    if request.method == 'GET':
        return render(request, 'cnn_test/test.html')
    
    import json
    import base64
    import sys
    sys.path.append('C:/Users/DOMMY/attendance_system')
    from ai_engine.cnn_recognizer import CNNRecognizer
    
    print(f"Request method: {request.method}")
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method required'})
    
    try:
        data = json.loads(request.body)
        image_data = data.get('image', '')
        
        print(f"Image data length: {len(image_data)}")
        
        if not image_data:
            return JsonResponse({'success': False, 'message': 'No image provided'})
        
        recognizer = CNNRecognizer()
        embedding = recognizer.extract_embedding_from_bytes(image_data)
        
        if embedding is None:
            return JsonResponse({'success': False, 'message': 'No face detected. Please face the camera.'})
        
        student = request.user.student_profile
        student.cnn_embedding = recognizer.embedding_to_json(embedding)
        student.cnn_enrolled = True
        student.save()
        
        request.user.is_face_registered = True
        request.user.save()
        
        print("CNN enrollment successful")
        
        return JsonResponse({'success': True, 'message': 'CNN face enrolled successfully!'})
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return JsonResponse({'success': False, 'message': f'Invalid JSON: {e}'})
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'success': False, 'message': str(e)})
    
    try:
        data = json.loads(request.body)
        image_data = data.get('image', '')
        
        print(f"Image data length: {len(image_data)}")  # Debug
        
        if not image_data:
            return JsonResponse({'success': False, 'message': 'No image provided'})
        
        recognizer = CNNRecognizer()
        embedding = recognizer.extract_embedding_from_bytes(image_data)
        
        if embedding is None:
            return JsonResponse({'success': False, 'message': 'No face detected. Please face the camera.'})
        
        student = request.user.student_profile
        student.cnn_embedding = recognizer.embedding_to_json(embedding)
        student.cnn_enrolled = True
        student.save()
        
        request.user.is_face_registered = True
        request.user.save()
        
        print("CNN enrollment successful")  # Debug
        
        return JsonResponse({'success': True, 'message': 'CNN face enrolled successfully!'})
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return JsonResponse({'success': False, 'message': f'Invalid JSON: {e}'})
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'success': False, 'message': str(e)})
    
    try:
        data = json.loads(request.body)
        image_data = data.get('image', '')
        
        if not image_data:
            return JsonResponse({'success': False, 'message': 'No image provided'})
        
        recognizer = CNNRecognizer()
        embedding = recognizer.extract_embedding_from_bytes(image_data)
        
        if embedding is None:
            return JsonResponse({'success': False, 'message': 'No face detected. Please face the camera.'})
        
        # Save CNN embedding to student profile
        student = request.user.student_profile
        student.cnn_embedding = recognizer.embedding_to_json(embedding)
        student.cnn_enrolled = True
        student.save()
        
        # Also mark face registered in user model
        request.user.is_face_registered = True
        request.user.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'CNN face enrollment successful!',
            'embedding_saved': True
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def cnn_test_page(request):
    """CNN test page"""
    from django.shortcuts import render
    from django.template import TemplateDoesNotExist
    import os
    
    # Check if template exists
    template_path = os.path.join('C:/Users/DOMMY/attendance_system/templates/cnn_test/test.html')
    print(f"Looking for template at: {template_path}")
    print(f"Template exists: {os.path.exists(template_path)}")
    
    try:
        return render(request, 'cnn_test/test.html')
    except TemplateDoesNotExist as e:
        print(f"Template error: {e}")
        return HttpResponse(f'<h1>Template not found</h1><p>Looking for: cnn_test/test.html</p><p>Error: {e}</p>')





