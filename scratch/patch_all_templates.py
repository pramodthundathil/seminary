import re
import os
from bs4 import BeautifulSoup

templates_data = [
    {"file": "admin/courses/list.html", "url": "course_bulk_delete"},
    {"file": "admin/students/books_list.html", "url": "student_books_bulk_delete"},
    {"file": "admin/students/subjects_list.html", "url": "student_subjects_bulk_delete"},
    {"file": "admin/students/instructors_list.html", "url": "student_instructors_bulk_delete"},
    {"file": "admin/students/uploads_list.html", "url": "student_uploads_bulk_delete"},
    {"file": "admin/students/exams_list.html", "url": "student_exams_bulk_delete"},
    {"file": "admin/students/student_assignment_list.html", "url": "student_assignment_bulk_delete"},
    {"file": "admin/students/list.html", "url": "student_bulk_delete"},
    {"file": "admin/staffs/staffs_list.html", "url": "staff_bulk_delete"},
    {"file": "admin/assignments/assignments_list.html", "url": "assignment_bulk_delete"},
    {"file": "admin/references/references_list.html", "url": "reference_bulk_delete"},
    {"file": "admin/payments/payments_list.html", "url": "payments_bulk_delete"},
    {"file": "admin/church_codes/list.html", "url": "church_codes_usage_bulk_delete"},
    {"file": "admin/users/church_students_list.html", "url": "users_bulk_delete"},
    {"file": "admin/church_codes/church_code_list.html", "url": "church_code_bulk_delete"}
]

for item in templates_data:
    filepath = os.path.join('templates', item['file'])
    bulk_url = item['url']
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue
        
    with open(filepath, 'r') as f:
        content = f.read()

    if "bulkDeleteForm" in content:
        print(f"Already patched: {filepath}")
        continue

    # Find table ID
    table_match = re.search(r'<table[^>]+id=[\'"]([^\'"]+)[\'"]', content)
    if not table_match:
        print(f"Table ID not found in {filepath}")
        continue
    table_id = table_match.group(1)

    # Find the variable name used in the template loop: {% for X in Y %}
    loop_match = re.search(r'\{%\s*for\s+([a-zA-Z0-9_]+)\s+in\s+[a-zA-Z0-9_]+\s*%\}', content)
    if not loop_match:
        print(f"Loop not found in {filepath}")
        continue
    item_var = loop_match.group(1)

    # 1. Add Bulk Delete Button near "Add" button or page-header
    # We'll just look for page-header and insert it inside it if there's a div.
    header_pattern = r'(<div[^>]*class=[\'"][^\'"]*page-header[^\'"]*[\'"][^>]*>.*?(?:<div[^>]*>|)(?:\s*<a[^>]*btn[^>]*>.*?</a>|\s*<button[^>]*btn[^>]*>.*?</button>)*)'
    
    def header_repl(m):
        original = m.group(1)
        btn = f'''
        <button type="submit" form="bulkDeleteForm" class="btn btn-danger mr-2" id="bulkDeleteBtn" disabled onclick="return confirm('Are you sure you want to delete selected items?')">
            <i class="fas fa-trash"></i> Delete Selected
        </button>'''
        # Let's just append it to the end of the matched group
        return original + btn

    # Wait, simple string replacement is safer if page-header is present.
    if '<div class="page-header' in content:
        content = re.sub(r'(<div class="page-header[^>]*>)(.*?)', r'\1\n        <button type="submit" form="bulkDeleteForm" class="btn btn-danger mr-2" id="bulkDeleteBtn" disabled onclick="return confirm(\'Are you sure you want to delete selected items?\')"><i class="fas fa-trash"></i> Delete Selected</button>\2', content, count=1, flags=re.DOTALL)
    elif '<h1>' in content:
        content = re.sub(r'(<h1>.*?</h1>)', r'\1\n        <button type="submit" form="bulkDeleteForm" class="btn btn-danger mr-2" id="bulkDeleteBtn" disabled onclick="return confirm(\'Are you sure you want to delete selected items?\')"><i class="fas fa-trash"></i> Delete Selected</button>', content, count=1, flags=re.DOTALL)

    # 2. Wrap Table in Form
    form_open = f'<form id="bulkDeleteForm" method="POST" action="{{% url \'{bulk_url}\' %}}">\n            {{% csrf_token %}}\n            <table'
    content = re.sub(r'<table', form_open, content, count=1)
    content = re.sub(r'</table>', '</table>\n        </form>', content, count=1)

    # 3. Add TH Checkbox
    content = re.sub(r'(<thead>\s*<tr>)', r'\1\n                    <th class="text-center" style="width: 40px;"><input type="checkbox" id="selectAll"></th>', content, count=1, flags=re.IGNORECASE)

    # 4. Add TD Checkbox
    td = f'<td class="text-center"><input type="checkbox" name="ids" class="bulk-checkbox" value="{{{{ {item_var}.id }}}}"></td>'
    # We must match the first <tr> after {% for ... %}
    # Look for {% for ... %} then <tr...
    pattern_for = r'(\{%\s*for\s+' + item_var + r'\s+in\s+[^%]+%\}\s*<tr[^>]*>)'
    content = re.sub(pattern_for, r'\1\n                    ' + td, content, count=1, flags=re.IGNORECASE)

    # 5. Append JS at the end of the file before {% endblock %}
    js_code = f"""
<script>
    $(document).ready(function() {{
        setTimeout(function() {{
            var dt_table = $('#{table_id}').DataTable();
            
            $('#selectAll').on('click', function() {{
                var rows = dt_table.rows({{ 'page': 'current' }}).nodes();
                $('input[type="checkbox"].bulk-checkbox', rows).prop('checked', this.checked);
                updateBulkDeleteButton();
            }});

            $('#{table_id} tbody').on('change', 'input[type="checkbox"].bulk-checkbox', function() {{
                updateSelectAllCheckbox();
                updateBulkDeleteButton();
            }});
            
            function updateSelectAllCheckbox() {{
                var currentRows = dt_table.rows({{ 'page': 'current' }}).nodes();
                var checkboxes = $('input[type="checkbox"].bulk-checkbox', currentRows);
                var el = $('#selectAll').get(0);
                if (el) {{
                    if (checkboxes.length === 0) {{
                        el.checked = false;
                        el.indeterminate = false;
                    }} else if (checkboxes.filter(':checked').length === checkboxes.length) {{
                        el.checked = true;
                        el.indeterminate = false;
                    }} else if (checkboxes.filter(':checked').length > 0) {{
                        el.checked = false;
                        el.indeterminate = true;
                    }} else {{
                        el.checked = false;
                        el.indeterminate = false;
                    }}
                }}
            }}

            function updateBulkDeleteButton() {{
                var anyChecked = dt_table.$('.bulk-checkbox:checked').length > 0;
                $('#bulkDeleteBtn').prop('disabled', !anyChecked);
            }}

            $('#bulkDeleteForm').on('submit', function(e) {{
                var form = this;
                dt_table.$('.bulk-checkbox:checked').each(function(){{
                    if(!$.contains(document, this)){{
                        $(form).append(
                            $('<input>').attr('type', 'hidden').attr('name', this.name).val(this.value)
                        );
                    }}
                }});
            }});

            dt_table.on('draw.dt', function() {{
                updateSelectAllCheckbox();
                updateBulkDeleteButton();
            }});
        }}, 500); // Wait for DataTables to fully initialize
    }});
</script>
"""
    content = content.replace('{% endblock %}', js_code + '\n{% endblock %}')

    with open(filepath, 'w') as f:
        f.write(content)
        
    print(f"Successfully patched {filepath}")
