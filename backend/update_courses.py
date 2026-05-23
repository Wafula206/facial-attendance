from apps.courses.models import Course

# Update courses that have NULL max_students
updated = Course.objects.filter(max_students__isnull=True).update(max_students=100)
print(f"✓ Updated {updated} courses with default capacity 100")
print("  Admin can edit each course to change capacity")
