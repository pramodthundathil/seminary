import re
import os

routes = [
    "admin/categories", "admin/photos", "admin/videos", "admin/news", "admin/pages/",
    "admin/courses/", "admin/roles", "admin/languages", "admin/subjects", "admin/branches",
    "admin/exams", "admin/students/student-books/", "admin/students/student-subjects/",
    "admin/students/student-instructor/", "admin/students/student-uploads/",
    "admin/students/student-submitted-exams/", "admin/students/student-submitted-assignment/",
    "admin/students/student-exams", "admin/students/student-assignment/", "admin/students/",
    "admin/applications/", "admin/staffs", "admin/assignments", "admin/references",
    "admin/support", "admin/uploads/", "admin/payments/", "admin/church-codes",
    "admin/users/", "admin/codes/", "admin/church-admin-applications/"
]

with open('menu/urls.py', 'r') as f:
    urls_content = f.read()
    
for route in routes:
    # remove trailing slash for search
    r = route.rstrip('/')
    # search for path("route"
    pattern = r"path\(['\"]" + re.escape(r) + r"/?['\"],\s*([^,]+),\s*name=['\"]([^'\"]+)['\"]\)"
    match = re.search(pattern, urls_content)
    if match:
        view_func = match.group(1).replace('views.', '')
        name = match.group(2)
        print(f"Route: {route} -> View: {view_func}, Name: {name}")
    else:
        print(f"Route: {route} -> NOT FOUND")

