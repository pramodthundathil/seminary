import re

with open('templates/admin/news/news_list.html', 'r') as f:
    content = f.read()

# Add set
content = content.replace("$(document).ready(function() {", "$(document).ready(function() {\n    window.selectedNewsIds = new Set();\n    window.newsTable = $('#newsTable').DataTable({")
content = content.replace("$('#newsTable').DataTable({", "") # We already added it above

# Update columns
dt_columns_search = """        columns: [
            { data: 'id', width: '50px' },"""
dt_columns_replace = """        columns: [
            { data: 'checkbox', orderable: false, searchable: false, width: '40px', className: 'text-center' },
            { data: 'id', width: '50px' },"""
content = content.replace(dt_columns_search, dt_columns_replace)

# Update order
content = content.replace("order: [[0, 'desc']],", "order: [[1, 'desc']],")

dt_callbacks = """
        rowCallback: function(row, data) {
            if (window.selectedNewsIds.has(data.id.toString())) {
                $('input.bulk-checkbox', row).prop('checked', true);
            }
        },
        drawCallback: function() {
            updateSelectAllCheckbox();
        }
    });

    $('#selectAll').on('click', function() {
        var isChecked = this.checked;
        $('input.bulk-checkbox', window.newsTable.rows().nodes()).each(function() {
            this.checked = isChecked;
            if (isChecked) {
                window.selectedNewsIds.add(this.value);
            } else {
                window.selectedNewsIds.delete(this.value);
            }
        });
        updateBulkDeleteButton();
    });

    $('#newsTable tbody').on('change', 'input.bulk-checkbox', function() {
        if (this.checked) {
            window.selectedNewsIds.add(this.value);
        } else {
            window.selectedNewsIds.delete(this.value);
        }
        updateSelectAllCheckbox();
        updateBulkDeleteButton();
    });

    function updateSelectAllCheckbox() {
        var currentRows = window.newsTable.rows().nodes();
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
        $('#bulkDeleteBtn').prop('disabled', window.selectedNewsIds.size === 0);
    }

    window.executeBulkDelete = function() {
        if (window.selectedNewsIds.size === 0) return;
        if (!confirm(`Are you sure you want to delete ${window.selectedNewsIds.size} selected news?`)) return;

        $.ajax({
            url: '{% url "news_bulk_delete" %}',
            type: 'POST',
            data: JSON.stringify({ ids: Array.from(window.selectedNewsIds) }),
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}'
            },
            success: function(response) {
                if (response.success) {
                    window.selectedNewsIds.clear();
                    $('#selectAll').prop('checked', false).prop('indeterminate', false);
                    updateBulkDeleteButton();
                    window.newsTable.ajax.reload();
                    alert(response.message);
                } else {
                    alert('Error: ' + response.message);
                }
            },
            error: function(xhr) {
                alert('Error deleting news.');
            }
        });
    };
"""

content = content.replace("""        }
    });
});""", dt_callbacks + "\n});")

with open('templates/admin/news/news_list.html', 'w') as f:
    f.write(content)

