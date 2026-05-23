from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid

class Programme(models.Model):
    """Academic Programme/Course of Study"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    duration_years = models.IntegerField(default=4)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'programmes'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Semester(models.Model):
    """Academic Semester"""
    SEMESTER_CHOICES = (
        (1, 'Semester 1'),
        (2, 'Semester 2'),
    )
    
    number = models.IntegerField(choices=SEMESTER_CHOICES)
    academic_year = models.CharField(max_length=9)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'semesters'
        unique_together = ['number', 'academic_year']
    
    def __str__(self):
        return f"Semester {self.number} - {self.academic_year}"


class User(AbstractUser):
    """Custom User Model"""
    USER_TYPES = (
        ('admin', 'Administrator'),
        ('lecturer', 'Lecturer'),
        ('student', 'Student'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='student')
    reg_no = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    face_embedding = models.TextField(null=True, blank=True)
    is_face_registered = models.BooleanField(default=False)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"


class StudentProfile(models.Model):
    """Extended student information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    
    programme = models.ForeignKey(Programme, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    year_of_study = models.IntegerField(default=1)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    
    enrolled_courses = models.ManyToManyField('courses.Course', blank=True, related_name='enrolled_students')
    
    face_image = models.TextField(null=True, blank=True)
    cnn_embedding = models.TextField(null=True, blank=True)
    cnn_enrolled = models.BooleanField(default=False)
    
    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    guardian_name = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)
    
    class Meta:
        db_table = 'student_profiles'
    
    def __str__(self):
        programme_name = self.programme.name if self.programme else "No Programme"
        return f"{self.user.get_full_name()} - {programme_name}"


class LecturerProfile(models.Model):
    """Extended lecturer information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lecturer_profile')
    
    staff_id = models.CharField(max_length=20, unique=True)
    designation = models.CharField(max_length=100)
    office_location = models.CharField(max_length=100, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    
    class Meta:
        db_table = 'lecturer_profiles'
    
    def __str__(self):
        return f"Prof. {self.user.get_full_name()} - {self.staff_id}"


class ClassSession(models.Model):
    """Class session for attendance"""
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course_code = models.CharField(max_length=20)
    course_name = models.CharField(max_length=200)
    lecturer = models.ForeignKey(LecturerProfile, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    venue = models.CharField(max_length=100)
    
    qr_code = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'class_sessions'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.course_code} - {self.title}"
    
    def is_active(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.status == 'ongoing'


class AttendanceRecord(models.Model):
    """Attendance record for each student"""
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    )
    
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendances')
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name='attendances')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='absent')
    marked_at = models.DateTimeField(auto_now_add=True)
    
    confidence = models.FloatField(default=0.0)
    recognition_method = models.CharField(max_length=50, default='face_recognition')
    
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'attendance_records'
        unique_together = ['student', 'session']
        ordering = ['-marked_at']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.session.title}: {self.status}"
