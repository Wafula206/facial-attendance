from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Course

def course_list(request):
    return HttpResponse('<h1>Courses</h1><p>Course management coming soon</p>')
