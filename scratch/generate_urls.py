import re

routes_data = [
    {"route": "admin/courses", "prefix": "course"},
    {"route": "students/books", "prefix": "student_books"},
    {"route": "students/subjects", "prefix": "student_subjects"},
    {"route": "students/instructor", "prefix": "student_instructors"},
    {"route": "students/uploads", "prefix": "student_uploads"},
    {"route": "students/exams", "prefix": "student_exams"},
    {"route": "students/assignment", "prefix": "student_assignment"},
    {"route": "admin/students", "prefix": "student"},
    {"route": "admin/staffs", "prefix": "staff"},
    {"route": "admin/assignments", "prefix": "assignment"},
    {"route": "admin/references", "prefix": "reference"},
    {"route": "admin/payments", "prefix": "payments"},
    {"route": "admin/church-codes", "prefix": "church_codes_usage"},
    {"route": "admin/users", "prefix": "users"},
    {"route": "admin/codes", "prefix": "church_code"}
]

with open('menu/urls.py', 'r') as f:
    urls_content = f.read()

# We will just append them at the end of the file.
new_urls = "\n    # --- BULK DELETE URLS --- \n"
for item in routes_data:
    route = item["route"]
    prefix = item["prefix"]
    new_urls += f"    path('{route}/bulk-delete/', views.{prefix}_bulk_delete, name='{prefix}_bulk_delete'),\n"

# Replace the closing `]` of urlpatterns
urls_content = re.sub(r'\]\s*$', new_urls + ']\n', urls_content)

with open('menu/urls.py', 'w') as f:
    f.write(urls_content)

