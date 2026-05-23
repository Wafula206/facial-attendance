import json
import base64
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone


face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


@csrf_exempt
@require_http_methods(["POST"])
def api_recognize_face(request):
    try:
        data = json.loads(request.body)
        image_data = data.get('image', '')
        session_id = data.get('session_id', '')
        mode = data.get('mode', 'checkin')
        
        if not image_data or not session_id:
            return JsonResponse({'success': False, 'error': 'Missing data'}, status=400)
        
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(80, 80))
        
        if len(faces) == 0:
            return JsonResponse({'success': False, 'recognized': False, 'message': 'No face detected'})
        
        from uuid import UUID
        from apps.attendance.models import ClassSession, AttendanceRecord
        from apps.accounts.models import StudentProfile
        
        session = ClassSession.objects.get(id=UUID(session_id))
        
        if session.status != 'ongoing':
            return JsonResponse({'success': False, 'recognized': False, 'message': 'Session not active'})
        
        orb = cv2.ORB_create(nfeatures=500)
        MATCH_THRESHOLD = 5
        enrolled = StudentProfile.objects.filter(user__is_face_registered=True).select_related('user')
        
        results = []
        
        for (x, y, w, h) in faces:
            detected_face = image_cv[y:y+h, x:x+w]
            kp1, des1 = orb.detectAndCompute(detected_face, None)
            
            if des1 is None:
                continue
            
            best_match = None
            best_match_score = 0
            
            for student in enrolled:
                if not student.cnn_embedding:
                    continue
                    
                try:
                    if isinstance(student.cnn_embedding, str):
                        stored_features = json.loads(student.cnn_embedding)
                    else:
                        stored_features = student.cnn_embedding
                    
                    stored_des = np.array(stored_features['descriptors'], dtype=np.uint8)
                    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                    matches = bf.match(des1, stored_des)
                    matches = sorted(matches, key=lambda x: x.distance)
                    good_matches = sum(1 for m in matches[:100] if m.distance < 50)
                    
                    if good_matches > best_match_score:
                        best_match_score = good_matches
                        best_match = student
                        
                except Exception as e:
                    continue
            
            if best_match and best_match_score >= MATCH_THRESHOLD:
                # Process attendance
                record, created = AttendanceRecord.objects.get_or_create(
                    student=best_match,
                    session=session,
                    defaults={'status': 'present', 'recognition_method': 'face_recognition', 'confidence': best_match_score / 100}
                )
                
                now = timezone.now()
                result = {
                    'name': best_match.user.get_full_name(),
                    'username': best_match.user.username,
                    'reg_no': best_match.user.reg_no,
                    'confidence': best_match_score / 100,
                    'face_location': {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)}
                }
                
                if mode == 'checkin':
                    if record.check_in_time:
                        result['status'] = 'already_checked_in'
                        result['message'] = f'Already checked in at {record.check_in_time.strftime("%H:%M:%S")}'
                    else:
                        record.check_in_time = now
                        record.status = 'present'
                        record.save()
                        result['status'] = 'checked_in'
                        result['message'] = f'Checked in at {now.strftime("%H:%M:%S")}'
                        result['attendance_marked'] = True
                        
                elif mode == 'checkout':
                    if not record.check_in_time:
                        result['status'] = 'not_checked_in'
                        result['message'] = 'Need to check in first'
                    elif record.check_out_time:
                        result['status'] = 'already_checked_out'
                        result['message'] = f'Already checked out at {record.check_out_time.strftime("%H:%M:%S")}'
                    else:
                        record.check_out_time = now
                        duration = (now - record.check_in_time).total_seconds() / 60
                        record.duration_minutes = int(duration)
                        record.save()
                        result['status'] = 'checked_out'
                        result['message'] = f'Checked out - Duration: {int(duration)} minutes'
                        result['attendance_marked'] = True
                        result['duration'] = int(duration)
                
                results.append(result)
        
        if len(results) > 0:
            # Return the first recognized face with full info including face_location
            first_result = results[0]
            return JsonResponse({
                'recognized': True,
                'name': first_result['name'],
                'username': first_result['username'],
                'reg_no': first_result['reg_no'],
                'confidence': first_result['confidence'],
                'face_location': first_result['face_location'],
                'attendance_marked': first_result.get('attendance_marked', False),
                'already_checked_in': first_result.get('status') == 'already_checked_in',
                'already_checked_out': first_result.get('status') == 'already_checked_out',
                'message': first_result['message'],
                'total_faces': len(faces),
                'total_recognized': len(results)
            })
        else:
            return JsonResponse({
                'recognized': False,
                'message': 'No matching face found',
                'total_faces': len(faces)
            })
            
    except Exception as e:
        print(f"API error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
