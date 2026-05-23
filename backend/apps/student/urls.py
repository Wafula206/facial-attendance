from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('attendance/', views.attendance_report, name='attendance_report'),
    path('attendance/export/', views.export_attendance, name='export_attendance'),
    path('enroll-face/', views.enroll_face, name='enroll_face'),
    path('enroll-face-cnn/', views.enroll_face_cnn, name='enroll_face_cnn'),
    path('enroll-face/submit/', views.enroll_face_submit, name='enroll_face_submit'),
    path('enrollment-status/', views.get_enrollment_status, name='enrollment_status'),
    
    # Course Enrollment
    path('my-courses/', views.my_courses, name='my_courses'),
    path('available-courses/', views.available_courses, name='available_courses'),
    path('course/<str:course_code>/', views.course_detail, name='course_detail'),
    path('enroll/', views.enroll_course, name='enroll_course'),
]
