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
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue

    with open(filepath, 'r') as f:
        content = f.read()
        
    if "bulkDeleteForm" in content:
        print(f"Already patched {filepath}")
        continue

    # 1. Add Delete Button
    if '<div class="page-header' in content:
        content = re.sub(r'(<div class="page-header[^>]*>)(.*?)', r'\1\n        <button class="btn btn-danger mr-2" id="bulkDeleteBtn" disabled onclick="executeBulkDelete()" style="float:left; margin-top:5px;"><i class="fas fa-trash"></i> Delete Selected</button>\2', content, count=1, flags=re.DOTALL)
    elif '<h1>' in content:
        content = re.sub(r'(<h1>.*?</h1>)', r'\1\n        <button class="btn btn-danger mr-2" id="bulkDeleteBtn" disabled onclick="executeBulkDelete()"><i class="fas fa-trash"></i> Delete Selected</button>', content, count=1, flags=re.DOTALL)

    # 2. Add TH Checkbox
    content = re.sub(r'(<thead>\s*<tr>)', r'\1\n                    <th class="text-center" style="width: 40px;"><input type="checkbox" id="selectAll"></th>', content, count=1, flags=re.IGNORECASE)

    # 3. JS Set and DataTable modifications
    # Find table initialization
    table_match = re.search(r'(var|let)\s+([a-zA-Z0-9_]+)\s*=\s*\$\([\'"]#([a-zA-Z0-9_]+)[\'"]\)\.DataTable\(\{', content)
    if not table_match:
        # Maybe without var?
        table_match = re.search(r'([a-zA-Z0-9_]+)\s*=\s*\$\([\'"]#([a-zA-Z0-9_]+)[\'"]\)\.DataTable\(\{', content)
        if not table_match:
            print(f"DataTable init not found in {filepath}")
            continue
        table_var = table_match.group(1)
        table_id = table_match.group(2)
    else:
        table_var = table_match.group(2)
        table_id = table_match.group(3)

    # Inject Set before Document Ready
    content = content.replace("$(document).ready(function() {", f"window.selected{table_var}Ids = new Set();\n$(document).ready(function() {{")
    content = content.replace("$(document).ready(function () {", f"window.selected{table_var}Ids = new Set();\n$(document).ready(function () {{")

    # Inject JS Columns
    # Look for `columns: [`
    content = re.sub(r'columns:\s*\[', r'columns: [\n                { data: "checkbox", orderable: false, searchable: false, width: "40px", className: "text-center" },', content, count=1)
    
    # Update order
    content = re.sub(r'order:\s*\[\[0,\s*[\'"]desc[\'"]\]\]', r'order: [[1, "desc"]]', content)

    # Add rowCallback and drawCallback to DataTable
    # The safest way is to insert it before the closing `});` of the DataTable initialization.
    # A bit risky, but we can look for `language: { ... }` or `order:` and put it after.
    # Actually, if we just find the end of DataTable `\n        });` we can replace it.
    
    # This regex finds the DataTable block by balancing braces? No.
    # Let's insert the callbacks right after `columns:` or `order:`.
    
    callbacks = f"""
            rowCallback: function(row, data) {{
                if (window.selected{table_var}Ids.has(data.id.toString())) {{
                    $('input.bulk-checkbox', row).prop('checked', true);
                }}
            }},
            drawCallback: function() {{
                updateSelectAllCheckbox_{table_var}();
            }},
"""
    content = re.sub(r'(order:\s*\[\[[0-9]+,\s*[\'"]desc[\'"]\]\],?)', r'\1' + callbacks, content, count=1)

    # Add generic JS functions outside DataTable init, before </script>
    js_funcs = f"""
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

        function updateSelectAllCheckbox_{table_var}() {{
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

        function updateBulkDeleteButton_{table_var}() {{
            $('#bulkDeleteBtn').prop('disabled', window.selected{table_var}Ids.size === 0);
        }}

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
    # Append right before closing document ready `});` -> `</script>`
    content = re.sub(r'\}\);\s*</script>', js_funcs + '\n});\n</script>', content)

    with open(filepath, 'w') as f:
        f.write(content)
        
    print(f"Patched {filepath}")

