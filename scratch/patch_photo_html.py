import re

with open('templates/admin/media/photo_gallery.html', 'r') as f:
    content = f.read()

header_replacement = """<div class="page-header" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <h1>Photo Gallery</h1>
        <div>
            <button class="btn btn-danger mr-2" id="bulkDeleteBtn" disabled onclick="executeBulkDelete()">
                <i class="fas fa-trash"></i> Delete Selected
            </button>
            <button class="btn btn-primary" onclick="openCreateModal()">Add Photo</button>
        </div>
    </div>"""

content = re.sub(r'<div class="page-header">.*?</div>', header_replacement, content, flags=re.DOTALL)

table_replacement = """<table id="photoTable" class="display" style="width:100%">
            <thead>
                <tr>
                    <th class="text-center" style="width: 40px;"><input type="checkbox" id="selectAll"></th>
                    <th>ID</th>"""

content = content.replace('<table id="photoTable" class="display" style="width:100%">\n            <thead>\n                <tr>\n                    <th>ID</th>', table_replacement)

with open('templates/admin/media/photo_gallery.html', 'w') as f:
    f.write(content)
