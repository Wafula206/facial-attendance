import numpy as np
import pickle
import base64
import json
import cv2
from typing import List, Tuple, Optional, Union


def compare_orb_features(des1, des2, threshold=25):
    '''
    Compare ORB features using BFMatcher
    '''
    if des1 is None or des2 is None:
        return False, 0
    
    if not isinstance(des1, np.ndarray):
        des1 = np.array(des1)
    if not isinstance(des2, np.ndarray):
        des2 = np.array(des2)
    
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    
    try:
        matches = bf.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)
        good_matches = sum(1 for m in matches[:100] if m.distance < 50)
        return good_matches >= threshold, good_matches
    except Exception as e:
        print(f"ORB comparison error: {e}")
        return False, 0


def detect_face(image_cv):
    '''
    Detect face in image using Haar Cascade
    '''
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = cascade.detectMultiScale(gray, 1.1, 5)
    
    if len(faces) == 0:
        return None, None
    
    (x, y, w, h) = faces[0]
    face_roi = image_cv[y:y+h, x:x+w]
    return face_roi, {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)}


def extract_orb_features(image_roi, nfeatures=500):
    '''
    Extract ORB features from face ROI
    '''
    orb = cv2.ORB_create(nfeatures=nfeatures)
    keypoints, descriptors = orb.detectAndCompute(image_roi, None)
    return keypoints, descriptors


def parse_cnn_embedding(cnn_embedding_field):
    '''
    Parse cnn_embedding field from StudentProfile
    Handles string JSON, dict, or None
    '''
    if cnn_embedding_field is None:
        return None
    
    if isinstance(cnn_embedding_field, dict):
        return cnn_embedding_field
    
    if isinstance(cnn_embedding_field, str):
        try:
            return json.loads(cnn_embedding_field)
        except:
            return None
    
    return None
