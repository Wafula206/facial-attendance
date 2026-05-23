from django.contrib import admin
from .models import User, StudentProfile, LecturerProfile, Programme, Semester


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'reg_no', 'user_type', 'is_face_registered', 'is_staff')
    list_filter = ('user_type', 'is_face_registered', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'reg_no', 'first_name', 'last_name')
    readonly_fields = ('last_login', 'date_joined')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'reg_no', 'get_programme', 'current_year', 'current_semester')
    list_filter = ('current_year', 'current_semester', 'programme')
    search_fields = ('user__username', 'reg_no')
    
    def get_programme(self, obj):
        return obj.programme.code if obj.programme else '-'
    get_programme.short_description = 'Programme'


@admin.register(LecturerProfile)
class LecturerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'staff_id', 'department')
    search_fields = ('user__username', 'staff_id', 'department')


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'duration_years')
    search_fields = ('code', 'name')


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
