from django import template
from home.models import AdminPages  # Use relative import

register = template.Library()

@register.simple_tag
def get_admin_pages():
    """
    Template tag to get admin pages with parent-child relationships
    Usage: {% get_admin_pages as admin_pages %}
    """
    # Get parent pages
    admin_pages = AdminPages.objects.filter(parent__isnull=True).order_by('menu_order')
    
    # Get child pages for each parent
    for page in admin_pages:
        page.children = AdminPages.objects.filter(parent=page).order_by('menu_order')
    
    return admin_pages

@register.inclusion_tag('admin/includes/admin_menu.html')
def render_admin_menu():
    """
    Inclusion tag to render admin menu directly with parent-child relationships
    Usage: {% render_admin_menu %}
    """
    # Get parent pages
    admin_pages = AdminPages.objects.filter(parent__isnull=True).order_by('menu_order')
    
    # Get child pages for each parent
    for page in admin_pages:
        page.children = AdminPages.objects.filter(parent=page).order_by('menu_order')
    
    return {'admin_pages': admin_pages}