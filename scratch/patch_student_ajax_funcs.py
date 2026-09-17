import re
import os

templates_data = [
    {"file": "admin/students/books_list.html", "url": "student_books_bulk_delete"},
    {"file": "admin/students/subjects_list.html", "url": "student_subjects_bulk_delete"},
    {"file": "admin/students/instructors_list.html", "url": "student_instructors_bulk_delete"},
    {"file": "admin/students/uploads_list.html", "url": "student_uploads_bulk_delete"},
    {"file": "admin/students/exams_list.html", "url": "student_exams_bulk_delete"},
    {"file": "admin/students/student_submitted_exams.html", "url": "student_submitted_exams_bulk_delete"},
    {"file": "admin/students/student_assignment_list.html", "url": "student_assignment_bulk_delete"},
    {"file": "admin/students/list.html", "url": "student_bulk_delete"}
]

for item in templates_data:
    filepath = os.path.join('templates', item['file'])
    bulk_url = item['url']

    with open(filepath, 'r') as f:
        content = f.read()
        
    table_match = re.search(r'(var|let)\s+([a-zA-Z0-9_]+)\s*=\s*\$\([\'"]#([a-zA-Z0-9_]+)[\'"]\)\.DataTable\(\{', content)
    if not table_match:
        table_match = re.search(r'([a-zA-Z0-9_]+)\s*=\s*\$\([\'"]#([a-zA-Z0-9_]+)[\'"]\)\.DataTable\(\{', content)
        if not table_match: continue
        table_var = table_match.group(1)
        table_id = table_match.group(2)
    else:
        table_var = table_match.group(2)
        table_id = table_match.group(3)

    if f"updateBulkDeleteButton_{table_var}" in content:
        continue # Already patched successfully

    js_funcs = f"""
    $(document).ready(function() {{
        $('#selectAll').on('click', function() {{
            var isChecked = this.checked;
            $('input.bulk-checkbox', {table_var}.rows().nodes()).each(function() {{
                this.checked = isChecked;
                if (isChecked) {{
                    window.selected{table_var}Ids.add(this.value);
                }} else {{
                    window.selected{table_var}Ids.delete(this.value);
                }}
            }});
            updateBulkDeleteButton_{table_var}();
        }});

        $('#{table_id} tbody').on('change', 'input.bulk-checkbox', function() {{
            if (this.checked) {{
                window.selected{table_var}Ids.add(this.value);
            }} else {{
                window.selected{table_var}Ids.delete(this.value);
            }}
            updateSelectAllCheckbox_{table_var}();
            updateBulkDeleteButton_{table_var}();
        }});

        window.updateSelectAllCheckbox_{table_var} = function() {{
            var currentRows = {table_var}.rows().nodes();
            var checkboxes = $('input.bulk-checkbox', currentRows);
            var el = $('#selectAll').get(0);
            if (el && checkboxes.length > 0) {{
                var checkedCount = checkboxes.filter(':checked').length;
                if (checkedCount === 0) {{
                    el.checked = false;
                    el.indeterminate = false;
                }} else if (checkedCount === checkboxes.length) {{
                    el.checked = true;
                    el.indeterminate = false;
                }} else {{
                    el.checked = false;
                    el.indeterminate = true;
                }}
            }} else if (el) {{
                el.checked = false;
                el.indeterminate = false;
            }}
        }}

        window.updateBulkDeleteButton_{table_var} = function() {{
            $('#bulkDeleteBtn').prop('disabled', window.selected{table_var}Ids.size === 0);
        }}
    }});

    window.executeBulkDelete = function() {{
        if (window.selected{table_var}Ids.size === 0) return;
        if (!confirm(`Are you sure you want to delete ${{window.selected{table_var}Ids.size}} selected items?`)) return;

        $.ajax({{
            url: '{{% url "{bulk_url}" %}}',
            type: 'POST',
            data: JSON.stringify({{ ids: Array.from(window.selected{table_var}Ids) }}),
            contentType: 'application/json',
            headers: {{
                'X-CSRFToken': '{{{{ csrf_token }}}}'
            }},
            success: function(response) {{
                if (response.success) {{
                    window.selected{table_var}Ids.clear();
                    $('#selectAll').prop('checked', false).prop('indeterminate', false);
                    updateBulkDeleteButton_{table_var}();
                    {table_var}.ajax.reload();
                    alert(response.message);
                }} else {{
                    alert('Error: ' + response.message);
                }}
            }},
            error: function(xhr) {{
                alert('Error deleting items.');
            }}
        }});
    }};
"""
    content = content.replace('</script>\n{% endblock %}', js_funcs + '\n</script>\n{% endblock %}')

    with open(filepath, 'w') as f:
        f.write(content)
        
    print(f"Patched JS for {filepath}")

