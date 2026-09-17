import re
import os

routes = [
    "admin/pages/", "admin/courses/", "admin/exams", 
    "admin/students/student-books/", "admin/students/student-subjects/",
    "admin/students/student-instructor/", "admin/students/student-uploads/",
    "admin/students/student-submitted-exams/", "admin/students/student-submitted-assignment/",
    "admin/students/student-exams", "admin/students/student-assignment/",
    "admin/students/", "admin/applications/", "admin/staffs", "admin/assignments",
    "admin/references", "admin/support", "admin/uploads/", "admin/payments/",
    "admin/church-codes", "admin/users/", "admin/codes/", "admin/church-admin-applications/"
]

with open('menu/urls.py', 'r') as f:
    urls_content = f.read()

with open('menu/views.py', 'r') as f:
    views_content = f.read()

for route in routes:
    r = route.rstrip('/')
    
    # Try to find list route
    pattern = r"path\(['\"]" + re.escape(r) + r"/?['\"],\s*([^,]+),\s*name=['\"]([^'\"]+)['\"]\)"
    match = re.search(pattern, urls_content)
    if not match:
        # Some are just slightly different, like 'admin/support' etc. We found them earlier:
        # admin/support -> support_list
        # admin/categories -> category_list
        print(f"Route: {route} -> NOT FOUND in urls")
        continue
    
    view_path = match.group(1).replace('views.', '')
    list_name = match.group(2)
    
    # Try to find delete route associated with this
    # e.g. path('pages/delete/<int:id>/', views.pages_delete, name='pages_delete')
    # We will search urls_content for views.*delete
    # Wait, we can just look for the list name's prefix: e.g. 'pages_list' -> 'pages_delete'
    prefix = list_name.replace('_list', '').replace('_view', '')
    
    delete_view = None
    delete_pattern = r"path\(['\"].*?delete.*?['\"],\s*views\.([^,]+),\s*name=['\"]([^'\"]+)['\"]\)"
    
    # Find all delete routes
    all_deletes = re.findall(delete_pattern, urls_content)
    for view_func, name in all_deletes:
        if prefix in name or name in prefix:
            delete_view = view_func
            break
            
    # Find template
    view_def = re.search(r"def " + re.escape(view_path) + r"\(.*?\):.*?(?:return render\(request,\s*['\"]([^'\"]+)['\"]).*?", views_content, flags=re.DOTALL)
    template = view_def.group(1) if view_def else "NOT FOUND"
    
    print(f"Route: {route}\n  List View: {view_path}\n  Delete View: {delete_view}\n  Template: {template}\n")

