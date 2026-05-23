from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import base64
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from apps.accounts.models import StudentProfile

@csrf_exempt
def test_face_recognition(request):
    """Simple face recognition test"""
    try:
        data = json.loads(request.body)
        image_data = data.get('image', '')
        
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Detect face
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)
        
        if len(faces) == 0:
            return JsonResponse({'recognized': False, 'message': 'No face detected'})
        
        (x, y, w, h) = faces[0]
        detected_face = image_cv[y:y+h, x:x+w]
        
        # Extract ORB features
        orb = cv2.ORB_create(nfeatures=500)
        kp, des = orb.detectAndCompute(detected_face, None)
        
        if des is None:
            return JsonResponse({'recognized': False, 'message': 'Could not extract features'})
        
        # Get all enrolled students
        students = StudentProfile.objects.filter(user__is_face_registered=True).select_related('user')
        
        best_match = None
        best_score = 0
        
        for student in students:
            if student.cnn_embedding:
                try:
                    stored_features = json.loads(student.cnn_embedding)
                    stored_des = np.array(stored_features['descriptors'], dtype=np.uint8)
                    
                    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                    matches = bf.match(des, stored_des)
                    matches = sorted(matches, key=lambda x: x.distance)
                    
                    good_matches = sum(1 for m in matches[:50] if m.distance < 50)
                    
                    if good_matches > best_score:
                        best_score = good_matches
                        best_match = student
                        
                except:
                    pass
        
        if best_match and best_score > 10:
            return JsonResponse({
                'recognized': True,
                'name': best_match.user.get_full_name(),
                'reg_no': best_match.user.reg_no,
                'match_score': best_score,
                'message': f'Recognized as {best_match.user.get_full_name()}'
            })
        else:
            return JsonResponse({
                'recognized': False,
                'message': 'Face not recognized. Please enroll first.'
            })
            
    except Exception as e:
        return JsonResponse({'recognized': False, 'message': str(e)})
