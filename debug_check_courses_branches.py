
import os
import sys
from unittest.mock import MagicMock

# Mock `storages` to avoid import error
sys.modules['storages'] = MagicMock()
sys.modules['storages.backends'] = MagicMock()
sys.modules['storages.backends.s3boto3'] = MagicMock()

import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()

from home.models import Courses, Branches, Subjects

print("--- Courses (First 5) ---")
for c in Courses.objects.all()[:5]:
    status_str = f"Status: {c.status}"
    print(f"ID: {c.id}, Name: {c.course_name}, Code: {c.course_code}, {status_str}")

print("\n--- Branches (First 5) ---")
for b in Branches.objects.all()[:5]:
    status_str = f"Status: {b.status}"
    print(f"ID: {b.id}, Name: {b.branch_name}, Code: {b.branch_code}, {status_str}")

print("\n--- Subjects (First 5) ---")
for s in Subjects.objects.all()[:5]:
    branch_name = s.branches.branch_name if s.branches else "None"
    status_str = f"Status: {s.status} (del={s.deleted_at})"
    print(f"ID: {s.id}, Name: {s.subject_name}, Branch: {branch_name}, {status_str}")

print("\n--- All Course Names vs All Branch Names check ---")
all_courses = {c.course_name.lower() for c in Courses.objects.all()}
all_branches = {b.branch_name.lower() for b in Branches.objects.all()}

print(f"Unique Course Names: {all_courses}")
print(f"Unique Branch Names: {all_branches}")

intersection = all_courses.intersection(all_branches)
print(f"Intersection (Exact match): {intersection}")
