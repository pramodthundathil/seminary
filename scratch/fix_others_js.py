import re

files = {
    'templates/admin/languages/languages_list.html': """    $(document).ready(function () {
        var table = $('#categoryTable').DataTable({
            pageLength: 12,
            lengthMenu: [[12, 24, 48, 96], [12, 24, 48, 96]],
            order: [[1, 'desc']],
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ languages",
                info: "Showing _START_ to _END_ of _TOTAL_ languages",
                infoEmpty: "Showing 0 to 0 of 0 languages",
                infoFiltered: "(filtered from _MAX_ total languages)",
                zeroRecords: "No matching languages found",
                emptyTable: "No languages available"
            },
            columnDefs: [
                { orderable: false, targets: [0, 5] },
                { width: '40px', targets: 0 },
                { width: '60px', targets: 1 },
                { width: '200px', targets: 2 },
                { width: '150px', targets: 3 },
                { width: '100px', targets: 4 },
                { width: '120px', targets: 5 }
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
    });""",
    
    'templates/admin/subjects/subjects_list.html': """    $(document).ready(function () {
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
    });""",
    
    'templates/admin/branches/branches_list.html': """    $(document).ready(function () {
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
}

pattern = r'\$\(document\)\.ready\(function\(\) \{.*?\}\);'

for filepath, js_replacement in files.items():
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if pattern matches
    if re.search(pattern, content, flags=re.DOTALL):
        content = re.sub(pattern, js_replacement, content, flags=re.DOTALL)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed {filepath}")
    else:
        print(f"Pattern not found in {filepath}. It might have space already.")

