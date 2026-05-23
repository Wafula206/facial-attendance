from django.db import models
import uuid


class ClassSession(models.Model):
    """Class session for attendance tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course_code = models.CharField(max_length=20)
    course_name = models.CharField(max_length=200)
    topic = models.CharField(max_length=200, blank=True, null=True, help_text="e.g., Week 1: Introduction to Computing")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    venue = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, default='scheduled', choices=[
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'class_sessions'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.course_code} - {self.topic or 'No topic'} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"


class AttendanceRecord(models.Model):
    """Individual attendance record"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=20, default='present')
    timestamp = models.DateTimeField(auto_now_add=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    confidence = models.FloatField(default=0.0)
    recognition_method = models.CharField(max_length=50, default='face_recognition')
    
    class Meta:
        db_table = 'attendance_records'
        ordering = ['-timestamp']
    
    def __str__(self):
        student_name = self.student.user.get_full_name() if self.student else 'Unknown'
        return f"{student_name} - {self.session.course_code} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
