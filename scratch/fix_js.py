import os
import re

files = [
    'templates/admin/categories/category-list.html',
    'templates/admin/roles/roles.html',
    'templates/admin/languages/languages_list.html',
    'templates/admin/subjects/subjects_list.html',
    'templates/admin/branches/branches_list.html'
]

for filepath in files:
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
        
        # We know the issue is at the end of the script block:
        #     });
        #     });
        # </script>
        # Let's just fix it by replacing the double closure with a single one.
        
        new_content = re.sub(r'\}\);\n\s*\}\);\n\s*</script>', '});\n</script>', content)
        
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")
    else:
        print(f"File not found: {filepath}")

