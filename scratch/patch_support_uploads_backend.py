import re

routes_data = [
    {"route": "admin/support", "prefix": "support", "model": "Support"},
    {"route": "admin/uploads", "prefix": "uploads", "model": "Uploads"}
]

views_content = ""
new_urls = ""

for item in routes_data:
    prefix = item["prefix"]
    model = item["model"]
    route = item["route"]
    
    views_content += f"""
@login_required
@require_POST
def {prefix}_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        {model}.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({{'success': True, 'message': f'Successfully deleted {{len(ids)}} items'}})
        messages.success(request, f'Successfully deleted {{len(ids)}} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({{'success': False, 'message': 'No items selected'}}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    
    return redirect('{prefix}_list')
"""

    new_urls += f"    path('{route}/bulk-delete/', views.{prefix}_bulk_delete, name='{prefix}_bulk_delete'),\n"

with open('menu/views.py', 'a') as f:
    f.write(views_content)

with open('menu/urls.py', 'r') as f:
    urls_content = f.read()

urls_content = re.sub(r'\]\s*$', new_urls + ']\n', urls_content)

with open('menu/urls.py', 'w') as f:
    f.write(urls_content)
