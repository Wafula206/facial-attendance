import json
import base64
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

# Face detection cascade
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


def get_navbar(request, active):
    user = request.user if request.user.is_authenticated else None
    navbar = f'<div class="navbar"><div class="navbar-brand">Face Recognition System</div><div class="navbar-links">'
    if not user:
        navbar += '<a href="/">Login</a>'
    else:
        navbar += '<a href="/dashboard/">Dashboard</a>'
        navbar += '<a href="/recognition/">Take Attendance</a>'
        navbar += f'<a href="/logout/">Logout</a>'
        navbar += f'</div><div class="user-info"><span>{user.get_full_name() or user.username}</span></div>'
    navbar += '</div>'
    return navbar


@login_required
def face_recognition_page(request):
    # Correct import - use apps.attendance
    from apps.attendance.models import ClassSession
    sessions = ClassSession.objects.filter(status='ongoing').order_by('start_time')
    navbar = get_navbar(request, 'recognition')
    return render(request, 'recognition/live_camera.html', {'navbar': navbar, 'sessions': sessions})


@csrf_exempt
def recognize_face(request):
    try:
        data = json.loads(request.body)
        image_data = data.get('image', '')
        session_id = data.get('session_id', '')
        mode = data.get('mode', 'checkin')

        if not image_data or not session_id:
            return JsonResponse({'success': False, 'message': 'Missing data', 'face_detected': False})

        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]

        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)

        if len(faces) == 0:
            return JsonResponse({'success': False, 'message': 'No face detected', 'face_detected': False})

        from uuid import UUID
        # Correct imports
        from apps.attendance.models import ClassSession, AttendanceRecord
        from apps.accounts.models import StudentProfile

        session = ClassSession.objects.get(id=UUID(session_id))

        if session.status != 'ongoing':
            return JsonResponse({'success': False, 'message': 'Session not active', 'face_detected': True})

        (x, y, w, h) = faces[0]
        detected_face = image_cv[y:y+h, x:x+w]

        orb = cv2.ORB_create(nfeatures=500)
        kp1, des1 = orb.detectAndCompute(detected_face, None)

        if des1 is None:
            return JsonResponse({'success': False, 'message': 'Could not extract face features', 'face_detected': True})

        enrolled = StudentProfile.objects.filter(user__is_face_registered=True).select_related('user')

        if enrolled.count() == 0:
            return JsonResponse({'success': False, 'message': 'No students have enrolled their faces', 'face_detected': True})

        best_match = None
        best_match_score = 0
        MATCH_THRESHOLD = 25

        for student in enrolled:
            stored_des = None
            
            if student.cnn_embedding:
                try:
                    if isinstance(student.cnn_embedding, str):
                        import json as json_lib
                        stored_features = json_lib.loads(student.cnn_embedding)
                    else:
                        stored_features = student.cnn_embedding
                    
                    if isinstance(stored_features, dict):
                        stored_des = np.array(stored_features['descriptors'], dtype=np.uint8)
                    elif isinstance(stored_features, list):
                        stored_des = np.array(stored_features, dtype=np.uint8)
                except Exception as e:
                    print(f"Error parsing embedding for {student.user.username}: {e}")
                    continue
            
            if stored_des is not None:
                try:
                    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                    matches = bf.match(des1, stored_des)
                    matches = sorted(matches, key=lambda x: x.distance)
                    good_matches = sum(1 for m in matches[:100] if m.distance < 50)
                    
                    print(f"Comparing {student.user.get_full_name()}: {good_matches} good matches")
                    
                    if good_matches > best_match_score:
                        best_match_score = good_matches
                        best_match = student
                except Exception as e:
                    print(f"Error comparing {student.user.get_full_name()}: {e}")
                    continue

        if best_match and best_match_score >= MATCH_THRESHOLD:
            face_location = {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)}
            existing = AttendanceRecord.objects.filter(student=best_match, session=session).first()
            now = timezone.now()
            confidence = min(0.95, best_match_score / 100)

            if mode == 'checkin':
                if existing and existing.check_in_time:
                    return JsonResponse({
                        'success': True,
                        'name': best_match.user.get_full_name(),
                        'reg_no': best_match.user.reg_no,
                        'message': f'Already checked in at {existing.check_in_time.strftime("%H:%M:%S")}',
                        'face_detected': True,
                        'face_location': face_location,
                        'already_checked_in': True
                    })

                if existing:
                    existing.check_in_time = now
                    existing.status = 'present'
                    existing.confidence = confidence
                    existing.save()
                else:
                    AttendanceRecord.objects.create(
                        student=best_match,
                        session=session,
                        status='present',
                        confidence=confidence,
                        recognition_method='face_recognition',
                        check_in_time=now
                    )

                return JsonResponse({
                    'success': True,
                    'name': best_match.user.get_full_name(),
                    'reg_no': best_match.user.reg_no,
                    'message': f'Checked in at {now.strftime("%H:%M:%S")}',
                    'face_detected': True,
                    'face_location': face_location,
                    'confidence': confidence,
                    'is_checkin': True
                })

            else:
                if not existing or not existing.check_in_time:
                    return JsonResponse({
                        'success': False,
                        'name': best_match.user.get_full_name(),
                        'message': 'You need to check in first!',
                        'face_detected': True,
                        'face_location': face_location
                    })

                if existing.check_out_time:
                    return JsonResponse({
                        'success': True,
                        'name': best_match.user.get_full_name(),
                        'message': 'Already checked out',
                        'face_detected': True,
                        'already_checked_out': True
                    })

                existing.check_out_time = now
                duration = (now - existing.check_in_time).total_seconds() / 60
                existing.duration_minutes = int(duration)
                existing.save()

                return JsonResponse({
                    'success': True,
                    'name': best_match.user.get_full_name(),
                    'reg_no': best_match.user.reg_no,
                    'message': f'Checked out - Duration: {int(duration)} minutes',
                    'face_detected': True,
                    'face_location': face_location,
                    'is_checkout': True,
                    'duration': int(duration)
                })
        else:
            return JsonResponse({
                'success': False,
                'message': f'Face not recognized. Match score: {best_match_score} (need > {MATCH_THRESHOLD})',
                'face_detected': True,
                'match_score': best_match_score
            })

    except Exception as e:
        print(f"Error in recognize_face: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e), 'face_detected': False})


@csrf_exempt
def register_face(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Login first'})
    try:
        request.user.is_face_registered = True
        request.user.save()
        return JsonResponse({'success': True, 'message': 'Face registered'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


