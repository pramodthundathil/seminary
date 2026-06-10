from django import template
from home.models import AdminPages

register = template.Library()

@register.simple_tag
def get_admin_pages(request):
    """
    Template tag to get admin pages with parent-child relationships,
    filtered by user permissions.
    Usage: {% get_admin_pages request as admin_pages %}
    """
    if not request or not request.user or not request.user.is_authenticated:
        return []

    try:
        role_user = request.user.user_roles.first()
        role = role_user.role if role_user else None
        role_name = role.name if role else None
    except Exception:
        role = None
        role_name = None

    admin_pages = AdminPages.objects.filter(parent__isnull=True).order_by('menu_order')
    
    if role_name != "Admin" and role_name is not None:
        from home.models import RoleHasPermissions
        allowed_permissions = set(
            RoleHasPermissions.objects.filter(role=role).values_list('permission__name', flat=True)
        )
        
        filtered_pages = []
        for page in admin_pages:
            # Check parent permission
            if page.permission and page.permission not in allowed_permissions:
                continue
            
            # Filter children based on child permissions
            children = AdminPages.objects.filter(parent=page).order_by('menu_order')
            filtered_children = []
            for child in children:
                if not child.permission or child.permission in allowed_permissions:
                    filtered_children.append(child)
            
            page.children = filtered_children
            filtered_pages.append(page)
            
        return filtered_pages
    elif role_name == "Admin":
        for page in admin_pages:
            page.children = AdminPages.objects.filter(parent=page).order_by('menu_order')
        return admin_pages
    else:
        return []

@register.inclusion_tag('admin/includes/admin_menu.html', takes_context=True)
def render_admin_menu(context):
    """
    Inclusion tag to render admin menu directly with parent-child relationships
    Usage: {% render_admin_menu %}
    """
    request = context.get('request')
    if not request or not request.user or not request.user.is_authenticated:
        return {'admin_pages': []}
        
    try:
        role_user = request.user.user_roles.first()
        role = role_user.role if role_user else None
        role_name = role.name if role else None
    except Exception:
        role = None
        role_name = None

    admin_pages = AdminPages.objects.filter(parent__isnull=True).order_by('menu_order')
    
    if role_name != "Admin" and role_name is not None:
        from home.models import RoleHasPermissions
        allowed_permissions = set(
            RoleHasPermissions.objects.filter(role=role).values_list('permission__name', flat=True)
        )
        
        filtered_pages = []
        for page in admin_pages:
            if page.permission and page.permission not in allowed_permissions:
                continue
            
            children = AdminPages.objects.filter(parent=page).order_by('menu_order')
            filtered_children = []
            for child in children:
                if not child.permission or child.permission in allowed_permissions:
                    filtered_children.append(child)
            
            page.children = filtered_children
            filtered_pages.append(page)
            
        return {'admin_pages': filtered_pages}
    elif role_name == "Admin":
        for page in admin_pages:
            page.children = AdminPages.objects.filter(parent=page).order_by('menu_order')
        return {'admin_pages': admin_pages}
    else:
        return {'admin_pages': []}

@register.filter
def has_permission(user, perm_name):
    """
    Check if a user has a specific permission.
    Usage: {% if request.user|has_permission:'manage-applications' %}
    """
    if not user or not user.is_authenticated:
        return False
    
    # Super Admin gets everything
    try:
        role_user = user.user_roles.first()
        role = role_user.role if role_user else None
        role_name = role.name if role else None
    except Exception:
        role = None
        role_name = None
        
    if role_name == "Admin":
        return True
        
    if role:
        from home.models import RoleHasPermissions
        return RoleHasPermissions.objects.filter(role=role, permission__name=perm_name).exists()
        
    return False