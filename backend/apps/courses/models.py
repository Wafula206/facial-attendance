from django.db import models
from django.conf import settings


class Course(models.Model):
    """Course/Unit"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    credits = models.IntegerField(default=3)
    programme = models.ForeignKey('accounts.Programme', on_delete=models.CASCADE, null=True, blank=True)
    year = models.IntegerField(choices=[(1, 'Year 1'), (2, 'Year 2'), (3, 'Year 3'), (4, 'Year 4')], default=1)
    semester = models.IntegerField(choices=[(1, 'Semester 1'), (2, 'Semester 2')], default=1)
    lecturer = models.ForeignKey('accounts.LecturerProfile', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'courses'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code}: {self.name}"
