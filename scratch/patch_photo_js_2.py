import re

with open('templates/admin/media/photo_gallery.html', 'r') as f:
    content = f.read()

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

content = content.replace("        });\n\n        // Setup drag and drop", dt_callbacks + "\n\n        // Setup drag and drop")

with open('templates/admin/media/photo_gallery.html', 'w') as f:
    f.write(content)
