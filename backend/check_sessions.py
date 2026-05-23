from apps.accounts.models import ClassSession, LecturerProfile
from apps.courses.models import Course

print("=== ALL SESSIONS IN DATABASE ===\n")

sessions = ClassSession.objects.all().order_by('-start_time')

if sessions.count() == 0:
    print("❌ NO SESSIONS FOUND IN DATABASE!")
    print("\nYou need to create a session first.")
else:
    for s in sessions:
        print(f"ID: {s.id}")
        print(f"Course: {s.course_code} - {s.course_name}")
        print(f"Title: {s.title}")
        print(f"Status: {s.status}")
        print(f"Start: {s.start_time}")
        print(f"End: {s.end_time}")
        print(f"Venue: {s.venue}")
        print(f"Lecturer: {s.lecturer.user.username if s.lecturer else 'None'}")
        print("-" * 50)

print(f"\nTotal sessions: {sessions.count()}")

# Check lecturer and courses
print("\n=== LECTURER INFO ===\n")
lecturer = LecturerProfile.objects.first()
if lecturer:
    print(f"Lecturer: {lecturer.user.username}")
    courses = Course.objects.filter(lecturer_staff_id=lecturer.staff_id)
    print(f"Courses assigned: {[c.code for c in courses]}")
else:
    print("No lecturer found")
