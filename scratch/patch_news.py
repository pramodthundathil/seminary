import re

with open('templates/admin/news/news_list.html', 'r') as f:
    content = f.read()

header_replacement = """<div class="news-header" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <h1>
            <i class="fas fa-newspaper" style="color: var(--primary-cyan);"></i>
            News & Press Release
        </h1>
        <div>
            <button class="btn btn-danger mr-2" id="bulkDeleteBtn" disabled onclick="executeBulkDelete()" style="background: var(--red); color: white; padding: 10px 20px; border-radius: 8px; border: none; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 8px;">
                <i class="fas fa-trash"></i> Delete Selected
            </button>
            <a href="{% url 'news_create' %}" class="btn-create">
                <i class="fas fa-plus"></i>
                Create News
            </a>
        </div>
    </div>"""

content = re.sub(r'<div class="news-header">.*?</div>', header_replacement, content, flags=re.DOTALL)

table_replacement = """<table id="newsTable" class="display" style="width:100%">
            <thead>
                <tr>
                    <th class="text-center" style="width: 40px;"><input type="checkbox" id="selectAll"></th>
                    <th>ID</th>"""

content = content.replace('<table id="newsTable" class="display" style="width:100%">\n            <thead>\n                <tr>\n                    <th>ID</th>', table_replacement)


# Now Javascript
# Let's see what the original JS is
import os
os.system('cat templates/admin/news/news_list.html | grep -n -B 5 -A 40 "var table = " > scratch/news_js.txt')
