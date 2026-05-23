from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts.views import home, role_login, logout_view, dashboard_redirect, health_check

urlpatterns = [
    path('', home, name='home'),
    path('login/', role_login, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_redirect, name='dashboard_redirect'),
    path('admin/', admin.site.urls),
    path('admin-dashboard/', include('apps.accounts.admin_urls')),
    path('health/', health_check, name='health'),
    path('recognition/', include('apps.recognition.urls')),
    path('camera-test/', include('apps.recognition.urls')),
    path('lecturer/', include('apps.lecturer.urls')),
    path('student/', include('apps.student.urls')),
    path('api/', include('apps.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

