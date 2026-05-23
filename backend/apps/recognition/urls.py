from django.urls import path
from . import views

app_name = 'recognition'

urlpatterns = [
    path('', views.face_recognition_page, name='face_recognition_page'),
    path('recognize/', views.recognize_face, name='recognize'),
    path('register/', views.register_face, name='register_face'),
]
