"""
CNN Face Recognition Module - Using OpenCV (Stable, No dependency issues)
"""

import cv2
import numpy as np
import json
import base64
from PIL import Image
from io import BytesIO

class CNNRecognizer:
    def __init__(self):
        self.threshold = 0.6
        # Load face detector
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    def extract_embedding_from_bytes(self, image_data):
        """Extract face features from base64 image string"""
        try:
            # Handle base64 string
            if isinstance(image_data, str):
                if 'base64,' in image_data:
                    image_data = image_data.split('base64,')[1]
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data
            
            # Convert to OpenCV image
            image = Image.open(BytesIO(image_bytes))
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
            
            if len(faces) == 0:
                return None
            
            # Get first face ROI
            (x, y, w, h) = faces[0]
            face_roi = gray[y:y+h, x:x+w]
            
            # Resize to standard size
            face_roi = cv2.resize(face_roi, (100, 100))
            
            # Return flattened array as "embedding"
            return face_roi.flatten()
            
        except Exception as e:
            print(f"OpenCV extract error: {e}")
            return None
    
    def compare_embeddings(self, emb1, emb2):
        """Calculate similarity between two face feature vectors"""
        if emb1 is None or emb2 is None:
            return 1.0
        distance = np.linalg.norm(emb1 - emb2)
        normalized = min(1.0, distance / 10000)
        return normalized
    
    def embedding_to_json(self, emb):
        if emb is None:
            return None
        return json.dumps(emb.tolist())
    
    def json_to_embedding(self, json_str):
        if not json_str:
            return None
        return np.array(json.loads(json_str))
