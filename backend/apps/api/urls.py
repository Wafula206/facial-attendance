from django.urls import path
from apps.api import views as api_views

app_name = 'api'

urlpatterns = [
    path('recognition/recognize/', api_views.api_recognize_face, name='api_recognize'),
]
