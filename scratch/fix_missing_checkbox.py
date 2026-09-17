import re

with open('menu/views.py', 'r') as f:
    content = f.read()

def patch_datatable(func_name, item_var):
    global content
    pattern = r'(def\s+' + func_name + r'\s*\(.*?data\.append\(\{)'
    match = re.search(pattern, content, flags=re.DOTALL)
    if match:
        func_content = match.group(0)
        if "'checkbox':" not in func_content:
            new_append = f"data.append({{\n            'checkbox': f'<input type=\"checkbox\" name=\"ids\" class=\"bulk-checkbox\" value=\"{{{item_var}.id}}\">',\n            'id': {item_var}.id,"
            new_func_content = re.sub(r'data\.append\(\{', new_append, func_content)
            content = content.replace(func_content, new_func_content)
            print(f"Patched {func_name}")

patch_datatable("student_subjects_datatable", "item")
patch_datatable("student_submitted_exams_datatable", "item")
patch_datatable("student_assignment_datatable", "item")

with open('menu/views.py', 'w') as f:
    f.write(content)
