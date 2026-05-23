from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from apps.accounts.models import StudentProfile
from apps.courses.models import Course
from apps.attendance.models import AttendanceRecord, ClassSession
import json
import base64
import cv2
import numpy as np
from PIL import Image
from io import BytesIO


def decode_base64_image(image_data):
    if not image_data:
        return None
    if ',' in image_data:
        image_data = image_data.split(',')[1]
    image_data = image_data.strip()
    padding = len(image_data) % 4
    if padding:
        image_data += '=' * (4 - padding)
    try:
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return np.array(image)
    except Exception as e:
        print(f"Error decoding: {e}")
        return None


@login_required
def dashboard(request):
    student = request.user.student_profile
    enrolled_courses = student.enrolled_courses.all()
    available_courses = Course.objects.exclude(id__in=enrolled_courses.values_list('id', flat=True))
    total_attendance = AttendanceRecord.objects.filter(student=student).count()
    context = {
        'user': request.user,
        'student': student,
        'enrolled_courses': enrolled_courses,
        'available_courses': available_courses,
        'total_enrolled': enrolled_courses.count(),
        'total_attendance': total_attendance,
        'page_title': 'Student Dashboard'
    }
    return render(request, 'student/dashboard.html', context)


@login_required
def profile(request):
    context = {
        'user': request.user,
        'student': request.user.student_profile,
        'page_title': 'My Profile'
    }
    return render(request, 'student/profile.html', context)


@login_required
def attendance_report(request):
    student = request.user.student_profile
    records = AttendanceRecord.objects.filter(student=student).select_related('session').order_by('-timestamp')
    context = {
        'attendance_records': records,
        'page_title': 'My Attendance'
    }
    return render(request, 'student/attendance_report.html', context)


@login_required
def export_attendance(request):
    import csv
    from django.http import HttpResponse
    student = request.user.student_profile
    records = AttendanceRecord.objects.filter(student=student).select_related('session')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="my_attendance.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Time', 'Course', 'Status', 'Check In', 'Check Out', 'Duration'])
    for r in records:
        writer.writerow([
            r.timestamp.strftime('%Y-%m-%d'),
            r.timestamp.strftime('%H:%M:%S'),
            r.session.course_code,
            r.status,
            r.check_in_time.strftime('%H:%M:%S') if r.check_in_time else '-',
            r.check_out_time.strftime('%H:%M:%S') if r.check_out_time else '-',
            r.duration_minutes or '-'
        ])
    return response


@login_required
def enroll_face(request):
    context = {'user': request.user, 'page_title': 'Enroll Face'}
    return render(request, 'student/enroll_face.html', context)


@login_required
def enroll_face_cnn(request):
    context = {'user': request.user, 'page_title': 'Enroll Face CNN'}
    return render(request, 'student/enroll_face_cnn.html', context)


@csrf_exempt
@login_required
def enroll_face_submit(request):
    try:
        print("=" * 50)
        print("FACE ENROLLMENT REQUEST RECEIVED")
        print("=" * 50)
        
        data = json.loads(request.body)
        image_data = data.get('image', '')
        
        print(f"Image data length: {len(image_data) if image_data else 0}")
        
        if not image_data:
            return JsonResponse({'success': False, 'error': 'No image provided'})
        
        # Remove data URL prefix if present
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]
            print("Removed base64 prefix")
        
        # Decode base64
        try:
            image_bytes = base64.b64decode(image_data)
            print(f"Decoded image bytes: {len(image_bytes)}")
        except Exception as e:
            print(f"Base64 decode error: {e}")
            return JsonResponse({'success': False, 'error': 'Invalid image data'})
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        image_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image_cv is None:
            print("Failed to decode image with OpenCV")
            return JsonResponse({'success': False, 'error': 'Could not decode image'})
        
        print(f"Image shape: {image_cv.shape}")
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        print(f"Gray image shape: {gray.shape}")
        
        # Load cascade classifier
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if face_cascade.empty():
            print("Failed to load cascade classifier")
            return JsonResponse({'success': False, 'error': 'Face detector not loaded'})
        
        # Try multiple detection parameters
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(50, 50))
        print(f"First attempt - faces found: {len(faces)}")
        
        if len(faces) == 0:
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
            print(f"Second attempt - faces found: {len(faces)}")
        
        if len(faces) == 0:
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=3, minSize=(100, 100))
            print(f"Third attempt - faces found: {len(faces)}")
        
        if len(faces) == 0:
            print("No face detected in any attempt")
            return JsonResponse({'success': False, 'error': 'No face detected. Please ensure good lighting and face is clearly visible.'})
        
        (x, y, w, h) = faces[0]
        print(f"Face detected at x={x}, y={y}, w={w}, h={h}")
        
        # Extract face ROI
        detected_face = image_cv[y:y+h, x:x+w]
        
        # Extract ORB features
        orb = cv2.ORB_create(nfeatures=500)
        kp, des = orb.detectAndCompute(detected_face, None)
        
        if des is None:
            print("Failed to extract ORB features")
            return JsonResponse({'success': False, 'error': 'Could not extract face features'})
        
        print(f"Extracted {len(des)} features")
        
        # Save features
        if hasattr(request.user, 'student_profile'):
            student = request.user.student_profile
            features_data = {'descriptors': des.tolist(), 'keypoints_count': len(kp), 'descriptor_shape': list(des.shape)}
            student.cnn_embedding = json.dumps(features_data)
            student.save()
            request.user.is_face_registered = True
            request.user.save()
            print("Face enrolled successfully!")
            return JsonResponse({'success': True, 'message': 'Enrolled successfully', 'features': len(des)})
        else:
            return JsonResponse({'success': False, 'error': 'No student profile found'})
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
def get_enrollment_status(request):
    enrolled = getattr(request.user, 'is_face_registered', False)
    return JsonResponse({'enrolled': enrolled, 'authenticated': True, 'username': request.user.username})


@csrf_exempt
@login_required
def enroll_course(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_code = data.get('course_code')
            course = get_object_or_404(Course, code=course_code)
            student = request.user.student_profile
            if student.enrolled_courses.filter(id=course.id).exists():
                return JsonResponse({'success': False, 'error': 'Already enrolled'})
            student.enrolled_courses.add(course)
            return JsonResponse({'success': True, 'message': f'Enrolled in {course.code}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@login_required
def my_courses(request):
    student = request.user.student_profile
    enrolled_courses = student.enrolled_courses.all().select_related('programme', 'lecturer')
    for course in enrolled_courses:
        sessions = ClassSession.objects.filter(course_code=course.code)
        attended = AttendanceRecord.objects.filter(student=student, session__in=sessions).count()
        course.attended_count = attended
        course.total_sessions = sessions.count()
        course.attendance_rate = round((attended / sessions.count()) * 100, 1) if sessions.count() > 0 else 0
    context = {'courses': enrolled_courses, 'page_title': 'My Courses'}
    return render(request, 'student/my_courses.html', context)


@login_required
def available_courses(request):
    student = request.user.student_profile
    enrolled_ids = student.enrolled_courses.values_list('id', flat=True)
    available = Course.objects.exclude(id__in=enrolled_ids).select_related('programme', 'lecturer')
    context = {'courses': available, 'page_title': 'Available Courses'}
    return render(request, 'student/available_courses.html', context)


@login_required
def course_detail(request, course_code):
    course = get_object_or_404(Course, code=course_code)
    student = request.user.student_profile
    is_enrolled = student.enrolled_courses.filter(id=course.id).exists()
    sessions = ClassSession.objects.filter(course_code=course.code).order_by('-start_time')
    attendance_records = AttendanceRecord.objects.filter(student=student, session__in=sessions)
    attended_sessions = attendance_records.count()
    total_sessions = sessions.count()
    attendance_rate = round((attended_sessions / total_sessions) * 100, 1) if total_sessions > 0 else 0
    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'sessions': sessions,
        'attendance_records': attendance_records,
        'attended_sessions': attended_sessions,
        'total_sessions': total_sessions,
        'attendance_rate': attendance_rate,
        'page_title': f'Course: {course.code}'
    }
    return render(request, 'student/course_detail.html', context)
