import re

with open('templates/admin/categories/category-list.html', 'r') as f:
    content = f.read()

# 1. Page header
header_replacement = """<div class="page-header" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <h1>Category List</h1>
        <div>
            {% if request.user|has_permission:'delete-category' %}
            <button type="submit" form="bulkDeleteForm" class="btn btn-danger mr-2" id="bulkDeleteBtn" disabled onclick="return confirm('Are you sure you want to delete selected categories?')">
                <i class="fas fa-trash"></i> Delete Selected
            </button>
            {% endif %}
            {% if request.user|has_permission:'create-category' %}
            <a href="{% url 'category_create' %}" class="btn btn-primary">
                <i class="fas fa-plus"></i> Add Category
            </a>
            {% endif %}
        </div>
    </div>"""

content = re.sub(r'<div class="page-header">.*?</div>', header_replacement, content, flags=re.DOTALL)

# 2. Form wrap and thead
table_replacement = """<form id="bulkDeleteForm" method="POST" action="{% url 'category_bulk_delete' %}">
            {% csrf_token %}
            <table id="categoryTable" class="display" style="width:100%">
                <thead>
                    <tr>
                        <th class="text-center" style="width: 40px;"><input type="checkbox" id="selectAll"></th>"""

content = content.replace('<table id="categoryTable" class="display" style="width:100%">\n            <thead>\n                <tr>', table_replacement)

# 3. tbody row
tbody_replacement = """<tbody>
                {% for category in categories %}
                <tr>
                    <td class="text-center">
                        <input type="checkbox" name="ids" class="bulk-checkbox" value="{{ category.id }}">
                    </td>"""

content = content.replace('<tbody>\n                {% for category in categories %}\n                <tr>', tbody_replacement)

# 4. table close
content = content.replace('</table>\n    </div>', '</table>\n        </form>\n    </div>')

# 5. JS
js_replacement = """    $(document).ready(function () {
        var table = $('#categoryTable').DataTable({
            pageLength: 12,
            lengthMenu: [[12, 24, 48, 96], [12, 24, 48, 96]],
            order: [[1, 'desc']],
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ categories",
                info: "Showing _START_ to _END_ of _TOTAL_ categories",
                infoEmpty: "Showing 0 to 0 of 0 categories",
                infoFiltered: "(filtered from _MAX_ total categories)",
                zeroRecords: "No matching categories found",
                emptyTable: "No categories available"
            },
            columnDefs: [
                { orderable: false, targets: [0, 2, 6] },
                { width: '40px', targets: 0 },
                { width: '60px', targets: 1 },
                { width: '100px', targets: 2 },
                { width: '200px', targets: 3 },
                { width: '100px', targets: 5 },
                { width: '150px', targets: 6 }
            ]
        });

        $('#selectAll').on('click', function() {
            var rows = table.rows({ 'page': 'current' }).nodes();
            $('input[type="checkbox"].bulk-checkbox', rows).prop('checked', this.checked);
            updateBulkDeleteButton();
        });

        $('#categoryTable tbody').on('change', 'input[type="checkbox"].bulk-checkbox', function() {
            updateSelectAllCheckbox();
            updateBulkDeleteButton();
        });
        
        function updateSelectAllCheckbox() {
            var currentRows = table.rows({ 'page': 'current' }).nodes();
            var checkboxes = $('input[type="checkbox"].bulk-checkbox', currentRows);
            var el = $('#selectAll').get(0);
            if (el) {
                if (checkboxes.length === 0) {
                    el.checked = false;
                    el.indeterminate = false;
                } else if (checkboxes.filter(':checked').length === checkboxes.length) {
                    el.checked = true;
                    el.indeterminate = false;
                } else if (checkboxes.filter(':checked').length > 0) {
                    el.checked = false;
                    el.indeterminate = true;
                } else {
                    el.checked = false;
                    el.indeterminate = false;
                }
            }
        }

        function updateBulkDeleteButton() {
            var anyChecked = table.$('.bulk-checkbox:checked').length > 0;
            $('#bulkDeleteBtn').prop('disabled', !anyChecked);
        }

        $('#bulkDeleteForm').on('submit', function(e) {
            var form = this;
            table.$('.bulk-checkbox:checked').each(function(){
                if(!$.contains(document, this)){
                    $(form).append(
                        $('<input>').attr('type', 'hidden').attr('name', this.name).val(this.value)
                    );
                }
            });
        });

        table.on('draw.dt', function() {
            updateSelectAllCheckbox();
            updateBulkDeleteButton();
        });
    });"""

content = re.sub(r'\$\(document\)\.ready\(function \(\) \{.*?\}\);', js_replacement, content, flags=re.DOTALL)

with open('templates/admin/categories/category-list.html', 'w') as f:
    f.write(content)

