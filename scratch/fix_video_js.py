import re

with open('templates/admin/videos/video-list.html', 'r') as f:
    content = f.read()

new_content = re.sub(r'\}\);\n\s*\}\);\n\s*</script>', '});\n</script>', content)

with open('templates/admin/videos/video-list.html', 'w') as f:
    f.write(new_content)
