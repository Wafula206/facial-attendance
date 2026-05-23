from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom User Model"""
    reg_no = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    user_type = models.CharField(max_length=20, default='student', choices=[
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('admin', 'Admin')
    ])
    is_face_registered = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"{self.username} ({self.user_type})"


class Programme(models.Model):
    """Academic Programme"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    duration_years = models.IntegerField(default=4)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'programmes'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Semester(models.Model):
    """Academic Semester"""
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'semesters'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"


class StudentProfile(models.Model):
    """Student profile with academic info"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    reg_no = models.CharField(max_length=20, unique=True)
    programme = models.ForeignKey(Programme, on_delete=models.PROTECT, null=True, blank=True)
    current_year = models.IntegerField(default=1)
    current_semester = models.IntegerField(default=1)
    cnn_embedding = models.TextField(null=True, blank=True)
    enrolled_courses = models.ManyToManyField('courses.Course', blank=True, related_name='enrolled_students')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.reg_no}"


class LecturerProfile(models.Model):
    """Lecturer profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lecturer_profile')
    staff_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'lecturer_profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.staff_id}"
