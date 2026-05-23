from django.urls import path
from . import admin_views

app_name = 'accounts_admin'

urlpatterns = [
    path('', admin_views.admin_dashboard, name='admin_dashboard'),
    
    # User Management
    path('users/', admin_views.manage_users, name='manage_users'),
    path('users/create/', admin_views.create_user, name='create_user'),
    path('users/edit/<int:user_id>/', admin_views.edit_user, name='edit_user'),
    path('users/delete/<int:user_id>/', admin_views.delete_user, name='delete_user'),
    path('users/promote/<int:student_id>/', admin_views.promote_student, name='promote_student'),
    
    # Programme Management
    path('programmes/', admin_views.manage_programmes, name='manage_programmes'),
    path('programmes/create/', admin_views.create_programme, name='create_programme'),
    path('programmes/edit/<int:programme_id>/', admin_views.edit_programme, name='edit_programme'),
    path('programmes/delete/<int:programme_id>/', admin_views.delete_programme, name='delete_programme'),
    
    # Course Management
    path('courses/', admin_views.manage_courses, name='manage_courses'),
    path('courses/create/', admin_views.create_course, name='create_course'),
    path('courses/edit/<int:course_id>/', admin_views.edit_course, name='edit_course'),
    
    # Semester Management
    path('semesters/', admin_views.manage_semesters, name='manage_semesters'),
    path('semesters/create/', admin_views.create_semester, name='create_semester'),
    path('semesters/activate/<int:semester_id>/', admin_views.activate_semester, name='activate_semester'),
    
    # Session Management
    path('sessions/', admin_views.manage_sessions, name='manage_sessions'),
    path('sessions/create/', admin_views.create_session, name='create_session'),
    path('sessions/edit/<uuid:session_id>/', admin_views.edit_session, name='edit_session'),
    path('sessions/delete/<uuid:session_id>/', admin_views.delete_session, name='delete_session'),
    path('sessions/start/<uuid:session_id>/', admin_views.start_session, name='start_session'),
    path('sessions/end/<uuid:session_id>/', admin_views.end_session, name='end_session'),
    path('sessions/<uuid:session_id>/attendance/', admin_views.view_session_attendance, name='session_attendance'),
    path('sessions/<uuid:session_id>/attendance/mark/<int:student_id>/', admin_views.mark_attendance_manual, name='mark_attendance'),
    path('sessions/<uuid:session_id>/attendance/export/', admin_views.export_attendance_csv, name='export_attendance'),
    
    # Reports & Analytics
    path('reports/', admin_views.admin_reports, name='admin_reports'),
    path('reports/export/full/', admin_views.export_full_report, name='export_full_report'),
    path('reports/export/course/<int:course_id>/', admin_views.export_course_report, name='export_course_report'),
]
