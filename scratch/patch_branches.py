import re

with open('templates/admin/branches/branches_list.html', 'r') as f:
    content = f.read()

header_replacement = """<div class="page-header" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <h1>Branches List</h1>
        <div>
            <button type="submit" form="bulkDeleteForm" class="btn btn-danger mr-2" id="bulkDeleteBtn" disabled onclick="return confirm('Are you sure you want to delete selected branches?')">
                <i class="fas fa-trash"></i> Delete Selected
            </button>
            <a href="{% url 'branches_create' %}" class="btn btn-primary">
                <i class="fas fa-plus"></i> Add Branch
            </a>
        </div>
    </div>"""

content = re.sub(r'<div class="page-header">.*?</div>', header_replacement, content, flags=re.DOTALL)

table_replacement = """<form id="bulkDeleteForm" method="POST" action="{% url 'branches_bulk_delete' %}">
            {% csrf_token %}
            <table id="branchesTable" class="display" style="width:100%">
            <thead>
                <tr>
                    <th class="text-center" style="width: 40px;"><input type="checkbox" id="selectAll"></th>"""

content = content.replace('<table id="branchesTable" class="display" style="width:100%">\n            <thead>\n                <tr>', table_replacement)

tbody_replacement = """<tbody>
                {% for branch in branches %}
                <tr>
                    <td class="text-center">
                        <input type="checkbox" name="ids" class="bulk-checkbox" value="{{ branch.id }}">
                    </td>"""

content = content.replace('<tbody>\n                {% for branch in branches %}\n                <tr>', tbody_replacement)

content = content.replace('</table>\n    </div>', '</table>\n        </form>\n    </div>')

js_replacement = """    $(document).ready(function () {
        var table = $('#branchesTable').DataTable({
            pageLength: 12,
            lengthMenu: [[12, 24, 48, 96], [12, 24, 48, 96]],
            order: [[1, 'desc']],
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ branches",
                info: "Showing _START_ to _END_ of _TOTAL_ branches",
                infoEmpty: "Showing 0 to 0 of 0 branches",
                infoFiltered: "(filtered from _MAX_ total branches)",
                zeroRecords: "No matching branches found",
                emptyTable: "No branches available"
            },
            columnDefs: [
                { orderable: false, targets: [0, 7] },
                { width: '40px', targets: 0 },
                { width: '60px', targets: 1 },
                { width: '200px', targets: 2 },
                { width: '150px', targets: 3 },
                { width: '150px', targets: 4 },
                { width: '150px', targets: 5 },
                { width: '100px', targets: 6 },
                { width: '120px', targets: 7 }
            ]
        });

        $('#selectAll').on('click', function() {
            var rows = table.rows({ 'page': 'current' }).nodes();
            $('input[type="checkbox"].bulk-checkbox', rows).prop('checked', this.checked);
            updateBulkDeleteButton();
        });

        $('#branchesTable tbody').on('change', 'input[type="checkbox"].bulk-checkbox', function() {
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

with open('templates/admin/branches/branches_list.html', 'w') as f:
    f.write(content)

