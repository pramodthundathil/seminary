import re

with open('menu/views.py', 'r') as f:
    content = f.read()

# We only want to patch the student_*_datatable functions.
# A function looks like: def student_something_datatable(request): ... return JsonResponse(...)
# Inside it, there is: data.append({ ... 'id': something.id, ... })

def patch_append(match):
    var_name = match.group(1)
    return f"data.append({{\n            'checkbox': f'<input type=\"checkbox\" name=\"ids\" class=\"bulk-checkbox\" value=\"{{{var_name}.id}}\">',\n            'id': {var_name}.id,"

# But wait, there are multiple data.append in the file.
# Let's only patch those inside the 9 target functions.
functions_to_patch = [
    "student_datatable",
    "student_books_datatable",
    "student_subjects_datatable",
    "student_instructors_datatable",
    "student_uploads_datatable",
    "student_exams_datatable",
    "student_submitted_exams_datatable",
    "student_assignment_datatable"
]

for func in functions_to_patch:
    # Find the function block. From `def {func}` to the first `return JsonResponse` with 'recordsFiltered'
    # Actually, just search for `data.append({ \n 'id': VAR.id` inside the file. 
    # But wait, we can just replace ALL `data.append({ \n 'id': var.id` globally, IF they are in those functions.
    # It's safer to just do a smart regex replace on the whole file, but check carefully.
    
    pattern = r'def\s+' + func + r'\s*\(.*?return\s+JsonResponse\(\{'
    match = re.search(pattern, content, flags=re.DOTALL)
    if not match:
        print(f"Could not find function {func}")
        continue
        
    func_content = match.group(0)
    
    # Check if already patched
    if "'checkbox':" in func_content:
        print(f"Already patched {func}")
        continue
        
    # Patch data.append
    new_func_content = re.sub(r'data\.append\(\{\s*[\'"]id[\'"]:\s*([a-zA-Z0-9_]+)\.id,', patch_append, func_content)
    
    content = content.replace(func_content, new_func_content)
    print(f"Patched {func}")

with open('menu/views.py', 'w') as f:
    f.write(content)
