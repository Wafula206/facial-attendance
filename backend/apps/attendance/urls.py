from django.urls import path
from . import views

app_name = 'attendance'
urlpatterns = [
    # Lecturer URLs
    path('dashboard/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('session/create/', views.create_session, name='create_session'),
    path('session/<uuid:session_id>/attendance/', views.session_attendance, name='session_attendance'),
    
    # Student URLs
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('attendance/', views.student_attendance, name='student_attendance'),
    path('attendance/export/', views.export_attendance, name='export_attendance'),
]
