import json
import cv2
import numpy as np

# Load Sharon's stored features
from apps.accounts.models import StudentProfile
import django
django.setup()

student = StudentProfile.objects.get(user__username='sharon')
stored_data = json.loads(student.cnn_embedding)
print(f"Stored descriptors shape: {len(stored_data['descriptors'])}")
print(f"First few descriptor values: {stored_data['descriptors'][0][:10]}")
