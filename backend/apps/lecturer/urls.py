from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Course Management
    path('my-courses/', views.my_courses, name='my_courses'),
    path('course/<str:course_code>/students/', views.course_students, name='course_students'),
    path('course/<str:course_code>/students/export/', views.export_course_students_csv, name='export_course_students'),
    
    # Reports
    path('reports/', views.attendance_report, name='attendance_report'),
    path('reports/session/<uuid:session_id>/', views.session_report, name='session_report'),
    path('reports/export/<uuid:session_id>/', views.export_report_csv, name='export_report'),
    path('reports/export/all/', views.overall_report_csv, name='export_all_report'),

    # Session Management
    path('sessions/', views.lecturer_sessions, name='sessions'),
    path('session/create/', views.create_session_form, name='create_session_form'),
    path('session/create/submit/', views.create_session_submit, name='create_session_submit'),
    path('session/<uuid:session_id>/attendance/', views.session_attendance, name='session_attendance'),
    path('session/<uuid:session_id>/start/', views.start_session, name='start_session'),
    path('session/<uuid:session_id>/end/', views.end_session, name='end_session'),
    path('session/<uuid:session_id>/delete/', views.delete_session, name='delete_session'),

    # Recognition Mode
    path('set-mode/original/', views.set_mode_original, name='set_mode_original'),
    path('set-mode/cnn/', views.set_mode_cnn, name='set_mode_cnn'),
    path('get-recognition-preference/', views.get_recognition_preference, name='get_recognition_preference'),
]
