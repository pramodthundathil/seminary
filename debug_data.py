from student.models import *
from home.models import *
from django.contrib.auth.models import User

# Assuming the user is logged in, let's find a test student user
# If I don't know the exact user, I'll list the first few students and their uploads
students = Students.objects.all()[:5]
print("--- Checking Students and Uploads ---")
for s in students:
    uploads = StudentsUploads.objects.filter(student=s)
    print(f"Student: {s.first_name} {s.last_name} (ID: {s.id}) - Uploads Count: {uploads.count()}")
    for u in uploads:
        print(f"  - Upload ID: {u.upload.id}, Name: {u.upload.upload_name}, Youtube: {u.upload.youtube}, Media: {u.upload.media}")

print("\n--- Checking References ---")
for s in students:
    # Check approved subjects
    approved_subjects = StudentsSubjects.objects.filter(student=s, is_approved=True)
    subject_ids = approved_subjects.values_list('subject_id', flat=True)
    print(f"Student: {s.first_name} (ID: {s.id}) - Approved Subject IDs: {list(subject_ids)}")
    
    # Check references for those subjects
    refs = BookReferences.objects.filter(subject_id__in=subject_ids, status=True)
    print(f"  - References Count: {refs.count()}")
    for r in refs:
        print(f"    - Ref ID: {r.id}, Title: {r.title}, File: {r.reference_file}")
