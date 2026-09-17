import re

with open('menu/views.py', 'r') as f:
    content = f.read()

# Fix course_bulk_delete
pattern_course = r'(def course_bulk_delete.*?if ids:\s+)Courses\.objects\.filter\(id__in=ids\)\.update\(deleted_at=timezone\.now\(\)\)'
content = re.sub(pattern_course, r'\1Courses.objects.filter(id__in=ids).delete()', content, flags=re.DOTALL)

# Fix uploads_bulk_delete
pattern_uploads = r'(def uploads_bulk_delete.*?if ids:\s+)Uploads\.objects\.filter\(id__in=ids\)\.update\(deleted_at=timezone\.now\(\)\)'
content = re.sub(pattern_uploads, r'\1Uploads.objects.filter(id__in=ids).delete()', content, flags=re.DOTALL)

with open('menu/views.py', 'w') as f:
    f.write(content)
