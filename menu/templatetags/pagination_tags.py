from django import template

register = template.Library()

@register.simple_tag
def get_page_range(page_obj, window=3):
    """
    Returns a compact pagination range for templates.
    - page_obj: Django Page instance (page_obj)
    - window: how many pages to show on each side of current page
    Example output:
      [1, '...', 6, 7, 8, 9, 10, '...', 50]
    """
    try:
        current = int(page_obj.number)
        total = int(page_obj.paginator.num_pages)
    except Exception:
        return []

    # Always include first and last pages
    left = max(1, current - window)
    right = min(total, current + window)

    pages = []

    if left > 1:
        pages.append(1)
    if left > 2:
        pages.append('...')  # gap between first and left

    for p in range(left, right + 1):
        pages.append(p)

    if right < total - 1:
        pages.append('...')
    if right < total:
        pages.append(total)

    return pages
