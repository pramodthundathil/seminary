import re

with open('menu/views.py', 'r') as f:
    content = f.read()

functions = [
    "student_datatable",
    "student_books_datatable",
    "student_subjects_datatable",
    "student_instructors_datatable",
    "student_uploads_datatable",
    "student_exams_datatable",
    "student_submitted_exams_datatable",
    "student_assignment_datatable",
    "student_submitted_assignment_datatable"
]

for func in functions:
    pattern = r'def\s+' + func + r'\s*\(.*?return\s+JsonResponse\(\{'
    match = re.search(pattern, content, flags=re.DOTALL)
    if match:
        func_content = match.group(0)
        if "'checkbox'" not in func_content:
            print(f"MISSING checkbox in {func}")
    else:
        print(f"NOT FOUND: {func}")
