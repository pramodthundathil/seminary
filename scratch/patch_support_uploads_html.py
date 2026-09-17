import re
import os

templates_data = [
    {"file": "admin/supports/support_list.html", "url": "support_bulk_delete"},
    {"file": "admin/uploads/uploads_list.html", "url": "uploads_bulk_delete"}
]

for item in templates_data:
    filepath = os.path.join('templates', item['file'])
    bulk_url = item['url']
    
    with open(filepath, 'r') as f:
        content = f.read()

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

    if '<div class="page-header' in content:
        content = re.sub(r'(<div class="page-header[^>]*>)(.*?)', r'\1\n        <button type="submit" form="bulkDeleteForm" class="btn btn-danger mr-2" id="bulkDeleteBtn" disabled onclick="return confirm(\'Are you sure you want to delete selected items?\')"><i class="fas fa-trash"></i> Delete Selected</button>\2', content, count=1, flags=re.DOTALL)
    elif '<h1>' in content:
        content = re.sub(r'(<h1>.*?</h1>)', r'\1\n        <button type="submit" form="bulkDeleteForm" class="btn btn-danger mr-2" id="bulkDeleteBtn" disabled onclick="return confirm(\'Are you sure you want to delete selected items?\')"><i class="fas fa-trash"></i> Delete Selected</button>', content, count=1, flags=re.DOTALL)

    form_open = f'<form id="bulkDeleteForm" method="POST" action="{{% url \'{bulk_url}\' %}}">\n            {{% csrf_token %}}\n            <table'
    content = re.sub(r'<table', form_open, content, count=1)
    content = re.sub(r'</table>', '</table>\n        </form>', content, count=1)

    content = re.sub(r'(<thead>\s*<tr>)', r'\1\n                    <th class="text-center" style="width: 40px;"><input type="checkbox" id="selectAll"></th>', content, count=1, flags=re.IGNORECASE)

    td = f'<td class="text-center"><input type="checkbox" name="ids" class="bulk-checkbox" value="{{{{ {item_var}.id }}}}"></td>'
    pattern_for = r'(\{%\s*for\s+' + item_var + r'\s+in\s+[^%]+%\}\s*<tr[^>]*>)'
    content = re.sub(pattern_for, r'\1\n                    ' + td, content, count=1, flags=re.IGNORECASE)

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
        }}, 500);
    }});
</script>
"""
    content = content.replace('{% endblock %}', js_code + '\n{% endblock %}')

    with open(filepath, 'w') as f:
        f.write(content)
        
    print(f"Successfully patched {filepath}")
