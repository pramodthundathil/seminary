import re

with open('templates/admin/students/subjects_list.html', 'r') as f:
    content = f.read()

content = content.replace('<thead>\n                <tr>\n                    <th class="text-center" style="width: 40px;"><input type="checkbox" id="selectAll"></th>\n                <tr>', '<thead>\n                <tr>\n                    <th class="text-center" style="width: 40px;"><input type="checkbox" id="selectAll"></th>')

with open('templates/admin/students/subjects_list.html', 'w') as f:
    f.write(content)
