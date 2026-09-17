import re

with open('templates/admin/media/photo_gallery.html', 'r') as f:
    content = f.read()

# 1. Add global Set to store selected IDs, right below variable declarations
vars_replacement = """    let selectedMediaId = null;
    let uploadedFile = null;
    let mediaSource = 'library'; // 'library' or 'upload'
    let selectedPhotoIds = new Set();"""
content = content.replace("    let mediaSource = 'library'; // 'library' or 'upload'", "    let mediaSource = 'library'; // 'library' or 'upload'\n    let selectedPhotoIds = new Set();")


# 2. Update columns in DataTable
dt_columns_search = """            columns: [
                { data: 'id', width: '60px' },
                { data: 'preview', orderable: false, searchable: false, width: '100px' },"""
dt_columns_replace = """            columns: [
                { data: 'checkbox', orderable: false, searchable: false, width: '40px', className: 'text-center' },
                { data: 'id', width: '60px' },
                { data: 'preview', orderable: false, searchable: false, width: '100px' },"""
content = content.replace(dt_columns_search, dt_columns_replace)


# 3. Update order column index because column 0 is now checkbox
order_search = "order: [[0, 'desc']],"
order_replace = "order: [[1, 'desc']],"
content = content.replace(order_search, order_replace)


# 4. Add rowCallback and drawCallback to the DataTable config, and add the JS functions for bulk delete
dt_callbacks = """
            rowCallback: function(row, data) {
                if (selectedPhotoIds.has(data.id.toString())) {
                    $('input.bulk-checkbox', row).prop('checked', true);
                }
            },
            drawCallback: function() {
                updateSelectAllCheckbox();
            }
        });

        $('#selectAll').on('click', function() {
            var isChecked = this.checked;
            $('input.bulk-checkbox', photoTable.rows().nodes()).each(function() {
                this.checked = isChecked;
                if (isChecked) {
                    selectedPhotoIds.add(this.value);
                } else {
                    selectedPhotoIds.delete(this.value);
                }
            });
            updateBulkDeleteButton();
        });

        $('#photoTable tbody').on('change', 'input.bulk-checkbox', function() {
            if (this.checked) {
                selectedPhotoIds.add(this.value);
            } else {
                selectedPhotoIds.delete(this.value);
            }
            updateSelectAllCheckbox();
            updateBulkDeleteButton();
        });

        function updateSelectAllCheckbox() {
            var currentRows = photoTable.rows().nodes();
            var checkboxes = $('input.bulk-checkbox', currentRows);
            var el = $('#selectAll').get(0);
            if (el && checkboxes.length > 0) {
                var checkedCount = checkboxes.filter(':checked').length;
                if (checkedCount === 0) {
                    el.checked = false;
                    el.indeterminate = false;
                } else if (checkedCount === checkboxes.length) {
                    el.checked = true;
                    el.indeterminate = false;
                } else {
                    el.checked = false;
                    el.indeterminate = true;
                }
            } else if (el) {
                el.checked = false;
                el.indeterminate = false;
            }
        }

        function updateBulkDeleteButton() {
            $('#bulkDeleteBtn').prop('disabled', selectedPhotoIds.size === 0);
        }

        window.executeBulkDelete = function() {
            if (selectedPhotoIds.size === 0) return;
            if (!confirm(`Are you sure you want to delete ${selectedPhotoIds.size} selected photos?`)) return;

            $.ajax({
                url: '{% url "photo_bulk_delete" %}',
                type: 'POST',
                data: JSON.stringify({ ids: Array.from(selectedPhotoIds) }),
                contentType: 'application/json',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}'
                },
                success: function(response) {
                    if (response.success) {
                        selectedPhotoIds.clear();
                        $('#selectAll').prop('checked', false).prop('indeterminate', false);
                        updateBulkDeleteButton();
                        photoTable.ajax.reload();
                        alert(response.message);
                    } else {
                        alert('Error: ' + response.message);
                    }
                },
                error: function(xhr) {
                    alert('Error deleting photos.');
                }
            });
        };
"""

# We need to insert this right after the DataTable initialization.
# In photo_gallery.html:
#             language: {
#                 ...
#             }
#         });
# 
#         // Gallery filters
#         $('#categoryFilter').on('change', function () {

content = content.replace("        });\n\n        // Gallery filters", dt_callbacks + "\n\n        // Gallery filters")

with open('templates/admin/media/photo_gallery.html', 'w') as f:
    f.write(content)
