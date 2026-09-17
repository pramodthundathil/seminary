import re

with open('templates/admin/subjects/subjects_list.html', 'r') as f:
    content = f.read()

header_replacement = """<div class="page-header" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <h1>Subjects List</h1>
        <div>
            {% if request.user|has_permission:'delete-subjects' %}
            <button type="submit" form="bulkDeleteForm" class="btn btn-danger mr-2" id="bulkDeleteBtn" disabled onclick="return confirm('Are you sure you want to delete selected subjects?')">
                <i class="fas fa-trash"></i> Delete Selected
            </button>
            {% endif %}
            {% if request.user|has_permission:'create-subjects' %}
            <a href="{% url 'subjects_create' %}" class="btn btn-primary">
                <i class="fas fa-plus"></i> Add Subject
            </a>
            {% endif %}
            {% if request.user|has_permission:'list-subjects' %}
            <a href="{% url 'subjects_export' %}" class="btn btn-success">
                <i class="fas fa-file-excel"></i> Export to Excel
            </a>
            {% endif %}
        </div>
    </div>"""

content = re.sub(r'<div class="page-header">.*?</div>', header_replacement, content, flags=re.DOTALL)

table_replacement = """<form id="bulkDeleteForm" method="POST" action="{% url 'subjects_bulk_delete' %}">
            {% csrf_token %}
            <table id="subjectsTable" class="display" style="width:100%">
    <thead>
        <tr>
            <th class="text-center" style="width: 40px;"><input type="checkbox" id="selectAll"></th>"""

content = content.replace('<table id="subjectsTable" class="display" style="width:100%">\n    <thead>\n        <tr>', table_replacement)

tbody_replacement = """<tbody>
        {% for subject in subjects %}
        <tr>
            <td class="text-center">
                <input type="checkbox" name="ids" class="bulk-checkbox" value="{{ subject.id }}">
            </td>"""

content = content.replace('<tbody>\n        {% for subject in subjects %}\n        <tr>', tbody_replacement)

content = content.replace('</table>\n    </div>', '</table>\n        </form>\n    </div>')

js_replacement = """    $(document).ready(function () {
        var table = $('#subjectsTable').DataTable({
            pageLength: 12,
            lengthMenu: [[12, 24, 48, 96], [12, 24, 48, 96]],
            order: [[1, 'desc']],
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ subjects",
                info: "Showing _START_ to _END_ of _TOTAL_ subjects",
                infoEmpty: "Showing 0 to 0 of 0 subjects",
                infoFiltered: "(filtered from _MAX_ total subjects)",
                zeroRecords: "No matching subjects found",
                emptyTable: "No subjects available"
            },
            columnDefs: [
                { orderable: false, targets: [0, 10] },
                { width: '40px', targets: 0 },
                { width: '60px', targets: 1 },
                { width: '200px', targets: 2 },
                { width: '100px', targets: 3 },
                { width: '150px', targets: 4 },
                { width: '100px', targets: 5 },
                { width: '100px', targets: 6 },
                { width: '100px', targets: 7 },
                { width: '150px', targets: 8 },
                { width: '100px', targets: 9 },
                { width: '120px', targets: 10 }
            ]
        });

        $('#selectAll').on('click', function() {
            var rows = table.rows({ 'page': 'current' }).nodes();
            $('input[type="checkbox"].bulk-checkbox', rows).prop('checked', this.checked);
            updateBulkDeleteButton();
        });

        $('#subjectsTable tbody').on('change', 'input[type="checkbox"].bulk-checkbox', function() {
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

with open('templates/admin/subjects/subjects_list.html', 'w') as f:
    f.write(content)

