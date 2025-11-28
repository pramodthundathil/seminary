# context_processors.py
from django.urls import reverse
from .models import Menus, MenuItems, Pages  

def get_menu_item_url(menu_item):
    """
    Get the URL for a menu item with proper priority logic
    Priority: pages (if exists) > url > #
    """
    # First check if pages foreign key exists
    if menu_item.pages:
        try:
            # Use page id for the URL (or use code if that's your URL pattern)
            return reverse('page_detail', kwargs={'slug': menu_item.pages.code})
            # If your URL pattern uses 'code' instead, use:
            # return reverse('page_detail', kwargs={'code': menu_item.pages.code})
        except Exception as e:
            print(f"Error generating page URL: {e}")
    
    # Second, check if url field has a value
    elif menu_item.url:
        return f"/{menu_item.url}"
    
    # Third, check if url field has a '' it will redirect to Home
    elif menu_item.url == '':
        return reverse('index')
    
    # Last resort - return placeholder
    return '#'

def process_menu_items(items):
    """
    Process menu items recursively and add computed URL to each item
    """
    processed_items = []
    
    for item in items:
        # Create a dictionary with item data
        item_data = {
            'id': item.id,
            'title': item.title,
            'computed_url': get_menu_item_url(item),  # Computed in backend
            'target_blank': item.target_blank,
            'menu_order': item.menu_order,
            'has_children': False,
            'children': []
        }
        
        # Get children if they exist
        children = item.sub_menu.filter(deleted_at__isnull=True).order_by('menu_order')
        
        if children.exists():
            item_data['has_children'] = True
            item_data['children'] = process_menu_items(children)  # Recursive call
        
        processed_items.append(item_data)
    
    return processed_items

def menu_context(request):
    """
    Context processor to make header and footer menus available in all templates
    """
    try:
        # Get header menu with all related items
        header_menu = Menus.objects.prefetch_related('items').filter(
            menu_position='header',
            status=True,
            deleted_at__isnull=True
        ).first()
        
        # Get footer menu with all related items
        footer_menu = Menus.objects.prefetch_related('items').filter(
            menu_position='footer',
            status=True,
            deleted_at__isnull=True
        ).first()
        
        # Get header menu items (only parent items, ordered)
        header_items = []
        if header_menu:
            parent_items = MenuItems.objects.filter(
                menus=header_menu,
                parent_id__isnull=True,
                deleted_at__isnull=True
            ).select_related('pages').prefetch_related('sub_menu').order_by('menu_order')
            
            # Process items and compute URLs in backend
            header_items = process_menu_items(parent_items)
        
        # Get footer menu items
        footer_items = []
        if footer_menu:
            parent_items = MenuItems.objects.filter(
                menus=footer_menu,
                parent_id__isnull=True,
                deleted_at__isnull=True
            ).select_related('pages').prefetch_related('sub_menu').order_by('menu_order')
            
            footer_items = process_menu_items(parent_items)
        # Add pages_data for footer
        pages_data = Pages.objects.filter(
            status=1,  # Assuming 1 means active
            deleted_at__isnull=True
        ).order_by('id')
        
        return {
            'header_menu': header_menu,
            'header_menu_items': header_items,
            'footer_menu': footer_menu,
            'footer_menu_items': footer_items,
            'pages_data': pages_data,
        }
    except Exception as e:
        print(f"Error loading menus: {e}")
        import traceback
        traceback.print_exc()
        return {
            'header_menu': None,
            'header_menu_items': [],
            'footer_menu': None,
            'footer_menu_items': [],
            'pages_data': [],
        }