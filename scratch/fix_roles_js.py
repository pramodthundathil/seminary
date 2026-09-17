import re

with open('templates/admin/roles/roles.html', 'r') as f:
    content = f.read()

js_replacement = """    $(document).ready(function () {
        var table = $('#rolesTable').DataTable({
            pageLength: 12,
            lengthMenu: [[12, 24, 48, 96], [12, 24, 48, 96]],
            order: [[1, 'desc']],
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ roles",
                info: "Showing _START_ to _END_ of _TOTAL_ roles",
                infoEmpty: "Showing 0 to 0 of 0 roles",
                infoFiltered: "(filtered from _MAX_ total roles)",
                zeroRecords: "No matching roles found",
                emptyTable: "No roles available"
            },
            columnDefs: [
                { orderable: false, targets: [0, 6] },
                { width: '40px', targets: 0 },
                { width: '60px', targets: 1 },
                { width: '200px', targets: 2 },
                { width: '150px', targets: 3 },
                { width: '100px', targets: 4 },
                { width: '150px', targets: 5 },
                { width: '120px', targets: 6 }
            ]
        });

        $('#selectAll').on('click', function() {
            var rows = table.rows({ 'page': 'current' }).nodes();
            $('input[type="checkbox"].bulk-checkbox', rows).prop('checked', this.checked);
            updateBulkDeleteButton();
        });

        $('#rolesTable tbody').on('change', 'input[type="checkbox"].bulk-checkbox', function() {
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

# Because the script is currently:
# <script>
#     $(document).ready(function() {
#         $('#rolesTable').DataTable({
# ...
#         });
# </script>
# We can replace everything inside <script> after jQuery DataTables include

pattern = r'\$\(document\)\.ready\(function\(\) \{.*?\}\);'
content = re.sub(pattern, js_replacement, content, flags=re.DOTALL)

with open('templates/admin/roles/roles.html', 'w') as f:
    f.write(content)
