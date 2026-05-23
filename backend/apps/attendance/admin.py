from django.contrib import admin
from .models import ClassSession, AttendanceRecord


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'course_name', 'start_time', 'end_time', 'status', 'venue')
    list_filter = ('status', 'course_code')
    search_fields = ('course_code', 'course_name')
    date_hierarchy = 'start_time'


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'status', 'timestamp', 'check_in_time', 'check_out_time')
    list_filter = ('status', 'recognition_method')
    search_fields = ('student__user__username', 'session__course_code')
    readonly_fields = ('timestamp',)
