from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.files.storage import default_storage
from django.conf import settings
from PIL import Image
import os
import json
from pathlib import Path
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from seminary.utils import export_to_excel

from home.models import News, MediaLibrary
from home.models import *
from .forms import *
from home.decorators import role_redirection
from datetime import datetime, timedelta

from django.views.decorators.csrf import csrf_exempt

@role_redirection
@login_required
def admin_index(request):
    # Get total students
    total_students = Students.objects.filter(active=1).count()
    
    # Get dynamic admin pages for navigation - organized by parent
    admin_pages = AdminPages.objects.filter(parent__isnull=True).order_by('menu_order')
    
    # Get child pages for each parent
    for page in admin_pages:
        page.children = AdminPages.objects.filter(parent=page).order_by('menu_order')
    
    # Get new students (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    new_students = Students.objects.filter(
        created_at__gte=thirty_days_ago,
        active=1
    ).order_by('-created_at')[:10]
    
    # Gender statistics
    male_count = Students.objects.filter(gender='Male', active=1).count()
    female_count = Students.objects.filter(gender='Female', active=1).count()
    
    if total_students > 0:
        male_percentage = round((male_count / total_students) * 100)
        female_percentage = round((female_count / total_students) * 100)
        # Calculate SVG circle offsets (314 is circumference for r=50)
        male_offset = 314 - (314 * male_percentage / 100)
        female_offset = 314 - (314 * female_percentage / 100)
    else:
        male_percentage = female_percentage = 0
        male_offset = female_offset = 314
    
    # Get courses with student count using course_applied field
    courses_list = []
    for course in Courses.objects.filter(status=1, deleted_at__isnull=True)[:6]:
        # Count students who applied for this course
        student_count = Students.objects.filter(
            course_applied=course.id,
            active=1
        ).count()
        
        # Add student_count as an attribute to the course object
        course.student_count = student_count
        courses_list.append(course)
    
    # Get recent references
    references = ReferenceForm.objects.filter(deleted_at__isnull=True).order_by('-created_at')[:10]
    
    # Calculate assignments in progress
    total_assignments = Assignments.objects.filter(deleted_at__isnull=True).count()
    completed_assignments = StudentsAssignment.objects.filter(
        submitted_on__isnull=False,
        deleted_at__isnull=True
    ).count()
    
    if total_assignments > 0:
        tasks_in_progress = round(((total_assignments - completed_assignments) / total_assignments) * 100)
    else:
        tasks_in_progress = 0
    
    # Calculate total exams completed
    total_exams_completed = StudentsExams.objects.filter(
        is_exam_ended=1,
        deleted_at__isnull=True
    ).count()
    
    # Attendance calculation (example - customize based on your logic)
    total_classes = 100  # Example
    attended_classes = 80  # Example
    attendance_percentage = round((attended_classes / total_classes) * 100) if total_classes > 0 else 0
    
    # ---------------- DASHBOARD NEW METRICS ----------------
    new_students_count = Students.objects.filter(status=False, active = False).count()
    pending_subjects_count = StudentsSubjects.objects.filter(is_approved=False, deleted_at__isnull=True).count()
    pending_books_count = StudentsBooks.objects.filter(is_approved=False, deleted_at__isnull=True).count()
    # -------------------------------------------------------
    
    context = {
        'total_students': total_students,
        'new_students': new_students,
        'male_count': male_count,
        'female_count': female_count,
        'male_percentage': male_percentage,
        'female_percentage': female_percentage,
        'male_offset': male_offset,
        'female_offset': female_offset,
        'courses': courses_list,
        'references': references,
        'attendance_percentage': attendance_percentage,
        'tasks_in_progress': tasks_in_progress,
        'total_exams_completed': total_exams_completed,
        'students_start': 1,
        'students_end': min(10, len(new_students)),
        'admin_pages': admin_pages,  # Dynamic navigation pages
        'new_students_count': new_students_count,
        'pending_subjects_count': pending_subjects_count,
        'pending_books_count': pending_books_count,
        # Notifications Data
        'new_students_list': Students.objects.filter(status=False).order_by('-created_at')[:5],
        'pending_subjects': StudentsSubjects.objects.filter(is_approved=False, deleted_at__isnull=True).select_related('student', 'subject').order_by('-created_at')[:5],
        'pending_books': StudentsBooks.objects.filter(is_approved=False, deleted_at__isnull=True).select_related('student', 'book').order_by('-created_at')[:5],
        'pending_exams': StudentsExams.objects.filter(is_approved=False, deleted_at__isnull=True).select_related('student', 'exam').order_by('-created_at')[:5],
        
        # New Dashboard Tables Data
        'pending_applications': Students.objects.filter(status=False, active = False).order_by('-created_at')[:5],
        'contact_requests': Contacts.objects.filter(deleted_at__isnull=True).order_by('-created_at')[:5],
        'submitted_assignments': StudentsAssignment.objects.filter(submitted_on__isnull=False, deleted_at__isnull=True).select_related('student', 'assignment').order_by('-submitted_on')[:5],
        'support_requests': Support.objects.filter(deleted_at__isnull=True).select_related('student').order_by('-updated_at')[:5],
        'recent_payments': Payments.objects.filter(deleted_at__isnull=True).select_related('student').order_by('-created_at')[:5],
    }
    
    return render(request, "admin/index.html", context)

@login_required
def menu_list(request):
    """Display all menus"""
    context = {
        'page_title': 'Menu Management'
    }
    return render(request, 'admin/menus/menu_list.html', context)

@login_required
def menu_datatable(request):
    """DataTables server-side processing for menus"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    
    # Column mapping
    columns = ['id', 'name', 'code', 'menu_position', 'status', 'created_at']
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'desc')
    
    order_column = columns[order_column_index] if order_column_index < len(columns) else 'created_at'
    if order_direction == 'desc':
        order_column = f'-{order_column}'
    
    # Query
    menus_query = Menus.objects.filter(deleted_at__isnull=True)
    
    # Search
    if search_value:
        menus_query = menus_query.filter(
            Q(name__icontains=search_value) |
            Q(code__icontains=search_value) |
            Q(menu_position__icontains=search_value)
        )
    
    # Total records
    total_records = Menus.objects.filter(deleted_at__isnull=True).count()
    filtered_records = menus_query.count()
    
    # Order and paginate
    menus_query = menus_query.order_by(order_column)[start:start + length]
    
    # Prepare data
    data = []
    for menu in menus_query:
        status_badge = f'<span class="badge-enabled">Enabled</span>' if menu.status == 1 else f'<span class="badge-disabled">Disabled</span>'
        
        items_count = MenuItems.objects.filter(menus=menu, deleted_at__isnull=True).count()
        
        actions = f'''
            <div class="btn-group" role="group">
        
        <div class="btn-group" role="group">
            <button id="btnGroupDrop{menu.id}" type="button" class="btn btn-secondary btn-sm dropdown-toggle" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                Actions
            </button>
            <div class="dropdown-menu" aria-labelledby="btnGroupDrop{menu.id}">
                <a href="/menu/menus/engineer/{menu.id}/" class="dropdown-item" title="Edit">
                    <i class="fas fa-edit mr-2 text-primary"></i> Edit
                </a>
                <button class="dropdown-item dropdown-item" style="width:100%; text-align:left; background:none; border:none;" onclick="deleteMenu({menu.id}, '{menu.name}')" title="Delete">
                    <i class="fas fa-trash mr-2 text-danger"></i> <span class="text-danger">Delete</span>
                </button>
            </div>
        </div>
    </div>
        '''
        
        data.append({
            'id': menu.id,
            'name': f'<div class="menu-name">{menu.name}</div><div class="menu-code">{menu.code}</div>',
            'position': f'<span class="badge-position">{menu.menu_position}</span>',
            'items': items_count,
            'status': status_badge,
            'created_at': menu.created_at.strftime('%b %d, %Y') if menu.created_at else '',
            'actions': actions
        })
    
    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })

@login_required
def menu_engineer(request, menu_id=None):
    """Menu engineering page with Nestable2"""
    if menu_id:
        menu = get_object_or_404(Menus, id=menu_id, deleted_at__isnull=True)
    else:
        # Create a new menu if not exists, or redirect to list? 
        # User flow suggests creating menu first.
        # But for new implementation, let's assume menu exists or handle create separately.
        return redirect('menu_list')
    
    # Get items in hierarchical structure (recursive logic handled in template or helper)
    # We can fetch all items and build tree in Python or let template handle simple recursion
    items = MenuItems.objects.filter(menus_id=menu.id, deleted_at__isnull=True).order_by('menu_order')
    
    # Build Tree
    def build_tree(items, parent_id=None):
        tree = []
        for item in items:
            # Handle None vs 0 vs NULL for parent_id_id comparison
            # In DB parent_id is ForeignKey.
            item_parent_id = item.parent_id_id # access ID content directly
            
            # Treat None and 0 same? No. Treat None as root.
            if item_parent_id == parent_id:
                children = build_tree(items, item.id)
                item.children = children
                tree.append(item)
        return tree

    menu_tree = build_tree(items, None)
    
    form = MenuForm(instance=menu)
    item_form = MenuItemsForm()
    
    context = {
        'menu': menu,
        'menu_tree': menu_tree,
        'form': form,
        'item_form': item_form,
        'page_title': f'Edit Menu: {menu.name}'
    }
    return render(request, 'admin/menus/menu_engineer.html', context)

@login_required
@require_POST
def menu_item_create(request):
    menu_id = request.POST.get('menu_id')
    
    # We need to manually handle 'pages' and 'courses' field if empty string is sent
    post_data = request.POST.copy()
    if post_data.get('pages') == '':
        post_data['pages'] = None
    if post_data.get('courses') == '':
        post_data['courses'] = None
        
    form = MenuItemsForm(post_data)
    
    if form.is_valid():
        item = form.save(commit=False)
        item.menus_id = menu_id
        
        # Determine URL
        menu_type = item.menu_type
        if menu_type == 'page' and item.pages:
            item.url = f"/{item.pages.code.strip('/')}"
        elif menu_type == 'course':
            course_obj = form.cleaned_data.get('courses')
            if course_obj:
                item.url = f"courses/{course_obj.course_code}"
        elif menu_type == 'custom':
            if item.url and not (item.url.startswith('http://') or item.url.startswith('https://')):
                 item.url = 'http://' + item.url
        elif menu_type == 'internal':
             if item.url and not item.url.startswith('/'):
                 item.url = '/' + item.url
        elif menu_type == 'no_link':
            item.url = '#'
        
        # Set Order to last
        last_item = MenuItems.objects.filter(menus_id=menu_id).order_by('-menu_order').first()
        item.menu_order = (last_item.menu_order + 1) if last_item else 0
        
        item.created_by = request.user
        item.updated_by = request.user
        item.save()
        messages.success(request, 'Menu item added!')
    else:
        messages.error(request, 'Error adding item: ' + str(form.errors))
        
    return redirect('menu_engineer', menu_id=menu_id) # Using new named URL for engineer? Check urls.py

@login_required
@require_POST
def menu_item_update(request, pk):
    item = get_object_or_404(MenuItems, pk=pk)
    
    post_data = request.POST.copy()
    if post_data.get('pages') == '':
        post_data['pages'] = None
    if post_data.get('courses') == '':
        post_data['courses'] = None
        
    form = MenuItemsForm(post_data, instance=item)
    
    if form.is_valid():
        updated_item = form.save(commit=False)
        menu_type = updated_item.menu_type
        
        if menu_type == 'page' and updated_item.pages:
            updated_item.url = f"/{updated_item.pages.code.strip('/')}"
        elif menu_type == 'course':
             course_obj = form.cleaned_data.get('courses')
             if course_obj:
                 updated_item.url = f"courses/{course_obj.course_code}"
        elif menu_type == 'custom':
            if updated_item.url and not (updated_item.url.startswith('http://') or updated_item.url.startswith('https://')):
                 updated_item.url = 'http://' + updated_item.url
        elif menu_type == 'internal':
             if updated_item.url and not updated_item.url.startswith('/'):
                 updated_item.url = '' + updated_item.url # Logic check? User code used '' + url
        elif menu_type == 'no_link':
            updated_item.url = '#'
            
        updated_item.updated_by = request.user
        updated_item.save()
        messages.success(request, 'Item updated!')
    else:
        messages.error(request, 'Error updating item: ' + str(form.errors))
        
    return redirect('menu_engineer', menu_id=item.menus_id)

@login_required
def menu_item_delete(request, pk):
    item = get_object_or_404(MenuItems, pk=pk)
    menu_id = item.menus_id
    item.delete() # Hard delete or soft? User code implied delete()
    messages.success(request, 'Item removed!')
    return redirect('menu_engineer', menu_id=menu_id)

@csrf_exempt
@login_required
def update_menu_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            menu_data = data.get('menu_data')
            
            def update_items(items, parent_id=None):
                for index, item_data in enumerate(items):
                    item_id = item_data.get('id')
                    if not item_id: continue 
                    
                    # Update order and parent
                    MenuItems.objects.filter(id=item_id).update(
                        menu_order=index,
                        parent_id=parent_id
                    )
                    
                    if 'children' in item_data:
                        update_items(item_data['children'], parent_id=item_id)
            
            with transaction.atomic():
                update_items(menu_data)
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid request'}, status=400)

@login_required
def refresh_menu_urls(request, pk):
    menu = get_object_or_404(Menus, pk=pk)
    items = MenuItems.objects.filter(menus=menu)
    count = 0
    
    for item in items:
        changed = False
        new_url = item.url
        
        if item.menu_type == 'page' and item.pages:
            new_url = f"/{item.pages.code.strip('/')}"
        elif item.menu_type == 'course' and item.url.startswith('courses/'):
             # Try refreshing course link if pattern matches? 
             pass
        elif item.menu_type == 'custom' and item.url:
             if not (item.url.startswith('http://') or item.url.startswith('https://')):
                 new_url = 'http://' + item.url
        elif item.menu_type == 'internal' and item.url:
             if not item.url.startswith('/'):
                 new_url = '/' + item.url
        
        if new_url != item.url:
            item.url = new_url
            item.save()
            count += 1
            
    messages.success(request, f'Refreshed URLs for {count} items!')
    return redirect('menu_engineer', menu_id=pk)

@login_required
@require_POST
def save_menu(request):
    """Update general menu details"""
    menu_id = request.POST.get('menu_id')
    menu = get_object_or_404(Menus, id=menu_id)
    
    form = MenuForm(request.POST, instance=menu)
    if form.is_valid():
        form.save()
        messages.success(request, 'Menu details updated successfully')
    else:
        messages.error(request, 'Error updating menu: ' + str(form.errors))
        
    return redirect('menu_engineer', menu_id=menu.id)

# pages 

@login_required
def pages_list(request):
    """Display all pages"""
    pages = Pages.objects.filter(deleted_at__isnull=True).order_by('-created_at')
    context = {
        'pages': pages,
        'page_title': 'Pages Management'
    }
    return render(request, 'admin/pages/pages_list.html', context)

@login_required
def page_create(request):
    """Create new page"""
    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            page.created_by = request.user
            page.updated_by = request.user
            page.save()
            messages.success(request, 'Page created successfully!')
            return redirect('pages_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PageForm()
    
    context = {
        'form': form,
        'page_title': 'Create Page',
        'action': 'Create'
    }
    return render(request, 'admin/pages/page_form.html', context)

@login_required
def page_edit(request, pk):
    """Edit existing page"""
    page = get_object_or_404(Pages, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = PageForm(request.POST, instance=page)
        if form.is_valid():
            page = form.save(commit=False)
            page.updated_by = request.user
            page.save()
            messages.success(request, 'Page updated successfully!')
            return redirect('pages_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PageForm(instance=page)
    
    context = {
        'form': form,
        'page': page,
        'page_title': 'Edit Page',
        'action': 'Update'
    }
    return render(request, 'admin/pages/page_form.html', context)

@login_required
def page_view(request, pk):
    """View page details"""
    page = get_object_or_404(Pages, pk=pk, deleted_at__isnull=True)
    context = {
        'page': page,
        'page_title': 'View Page'
    }
    return render(request, 'admin/pages/page_view.html', context)

@login_required
def page_delete(request, pk):
    """Soft delete page"""
    page = get_object_or_404(Pages, pk=pk, deleted_at__isnull=True)
    page.deleted_at = timezone.now()
    page.save()
    messages.success(request, 'Page deleted successfully!')
    return redirect('pages_list')

@login_required
@require_POST
def save_menu(request):
    """Save or update menu"""
    try:
        menu_id = request.POST.get('menu_id')
        name = request.POST.get('name')
        code = request.POST.get('code')
        menu_position = request.POST.get('menu_position')
        status = int(request.POST.get('status', 1))
        
        if menu_id:
            menu = get_object_or_404(Menus, id=menu_id)
            menu.name = name
            menu.code = code
            menu.menu_position = menu_position
            menu.status = status
            menu.updated_by = request.user.id
        else:
            menu = Menus(
                name=name,
                code=code,
                menu_position=menu_position,
                status=status,
                created_by=request.user.id,
                updated_by=request.user.id,
                created_at=timezone.now()
            )
        
        menu.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Menu saved successfully',
            'menu_id': menu.id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def save_menu_items(request):
    """Save menu items with order"""
    try:
        menu_id = request.POST.get('menu_id')
        items_data = json.loads(request.POST.get('items', '[]'))
        
        menu = get_object_or_404(Menus, id=menu_id)
        
        with transaction.atomic():
            # Delete existing items
            MenuItems.objects.filter(menus_id=menu.id).update(deleted_at=timezone.now())
            
            # Map temp_id (from client) to new DB instance
            id_map = {}
            created_items = []
            
            # First pass: Create all items without parent
            for idx, item_data in enumerate(items_data):
                page_id = item_data.get('page_id')
                page = None
                if page_id:
                    page = Pages.objects.get(id=page_id)
                
                new_item = MenuItems.objects.create(
                    menus=menu,
                    title=item_data.get('title'),
                    url=item_data.get('url', ''),
                    pages=page,
                    menu_type=item_data.get('menu_type', 'page'),
                    menu_order=idx + 1,
                    parent_id=0, # Set temporarily to 0
                    target_blank=int(item_data.get('target_blank', 0)),
                    original_title=item_data.get('title', ''), # Use title as original if not provided
                    created_by=request.user.id,
                    updated_by=request.user.id,
                    created_at=timezone.now()
                )
                
                # key is the ID sent from client (temp or old ID)
                client_id = str(item_data.get('id', ''))  
                if client_id:
                    id_map[client_id] = new_item
                
                # Store data needed for second pass
                created_items.append({
                    'instance': new_item,
                    'parent_temp_id': str(item_data.get('parent_id', '0'))
                })
            
            # Second pass: Update parents
            for item_info in created_items:
                parent_temp_id = item_info['parent_temp_id']
                if parent_temp_id != '0' and parent_temp_id in id_map:
                    parent_instance = id_map[parent_temp_id]
                    item_info['instance'].parent_id = parent_instance.id
                    item_info['instance'].save()
                    
        return JsonResponse({
            'success': True,
            'message': 'Menu items saved successfully'
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def delete_menu(request, menu_id):
    """Soft delete menu"""
    try:
        menu = get_object_or_404(Menus, id=menu_id)
        menu.deleted_at = timezone.now()
        menu.save()
        
        # Also delete menu items
        MenuItems.objects.filter(menus_id=menu.id).update(deleted_at=timezone.now())
        
        return JsonResponse({
            'success': True,
            'message': 'Menu deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
def get_menu_items(request, menu_id):
    """Get menu items as JSON"""
    try:
        menu = get_object_or_404(Menus, id=menu_id)
        items = MenuItems.objects.filter(
            menus=menu, 
            deleted_at__isnull=True
        ).order_by('menu_order')
        
        items_list = []
        for item in items:
            items_list.append({
                'id': item.id,
                'title': item.title,
                'url': item.url,
                'page_id': item.pages.id if item.pages else None,
                'page_title': item.pages.title if item.pages else '',
                'menu_type': item.menu_type,
                'parent_id': item.parent_id,
                'target_blank': item.target_blank,
                'menu_order': item.menu_order
            })
        
        return JsonResponse({
            'success': True,
            'items': items_list
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

# news setting 

@login_required
def news_list(request):
    """Display news list with DataTables"""
    context = {
        'page_title': 'News & Press Release Management'
    }
    return render(request, 'admin/news/news_list.html', context)

@login_required
def news_datatable(request):
    """DataTables server-side processing for news"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'desc')
    
    # Column mapping
    columns = ['id', 'title', 'code', 'status', 'created_at']
    order_column = columns[order_column_index] if order_column_index < len(columns) else 'created_at'
    
    if order_direction == 'desc':
        order_column = f'-{order_column}'
    
    # Query
    news_query = News.objects.filter(deleted_at__isnull=True)
    
    # Search
    if search_value:
        news_query = news_query.filter(
            Q(title__icontains=search_value) |
            Q(code__icontains=search_value) |
            Q(description__icontains=search_value)
        )
    
    # Total records
    total_records = News.objects.filter(deleted_at__isnull=True).count()
    filtered_records = news_query.count()
    
    # Order and paginate
    news_query = news_query.order_by(order_column)[start:start + length]
    
    # Prepare data
    data = []
    for news in news_query:
        status_badge = f'<span class="badge-enabled">Active</span>' if news.status == 1 else f'<span class="badge-disabled">Inactive</span>'
        
        media_preview = ''
        if news.media:
            media_preview = f'<img src="{news.media.path}" alt="thumbnail" class="table-thumbnail">'
        else:
            media_preview = '<div class="no-image">No Image</div>'
        
        actions = f'''
            <div class="btn-group" role="group">
        
        <div class="btn-group" role="group">
            <button id="btnGroupDrop{news.id}" type="button" class="btn btn-secondary btn-sm dropdown-toggle" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                Actions
            </button>
            <div class="dropdown-menu" aria-labelledby="btnGroupDrop{news.id}">
                <button class="dropdown-item dropdown-item" style="width:100%; text-align:left; background:none; border:none;" onclick="editNews({news.id})" title="Edit">
                    <i class="fas fa-edit mr-2 text-primary"></i> Edit
                </button>
                <button class="dropdown-item dropdown-item" style="width:100%; text-align:left; background:none; border:none;" onclick="deleteNews({news.id}, '{news.title}')" title="Delete">
                    <i class="fas fa-trash mr-2 text-danger"></i> <span class="text-danger">Delete</span>
                </button>
            </div>
        </div>
    </div>
        '''
        
        data.append({
            'id': news.id,
            'media': media_preview,
            'title': f'<div class="news-title">{news.title}</div><div class="news-code">{news.code}</div>',
            'description': news.description[:100] + '...' if news.description and len(news.description) > 100 else (news.description or ''),
            'status': status_badge,
            'created_at': news.created_at.strftime('%b %d, %Y') if news.created_at else '',
            'actions': actions
        })
    
    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })

@login_required
def news_create(request):
    """Create new news"""
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save(commit=False)
            news.created_by = request.user.id
            news.updated_by = request.user.id
            news.created_at = timezone.now()
            news.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'News created successfully'
                })
            return redirect('news:news_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    else:
        form = NewsForm()
    
    context = {
        'form': form,
        'page_title': 'Create News',
        'is_edit': False
    }
    return render(request, 'admin/news/news_form.html', context)

@login_required
def news_edit(request, news_id):
    """Edit existing news"""
    news = get_object_or_404(News, id=news_id, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news)
        if form.is_valid():
            news = form.save(commit=False)
            news.updated_by = request.user.id
            news.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'News updated successfully'
                })
            return redirect('news:news_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    else:
        form = NewsForm(instance=news)
    
    context = {
        'form': form,
        'news': news,
        'page_title': 'Edit News',
        'is_edit': True
    }
    return render(request, 'admin/news/news_form.html', context)

@login_required
def news_get(request, news_id):
    """Get news data as JSON"""
    try:
        news = get_object_or_404(News, id=news_id, deleted_at__isnull=True)
        
        data = {
            'id': news.id,
            'code': news.code,
            'title': news.title,
            'description': news.description,
            'browser_title': news.browser_title,
            'meta_description': news.meta_description,
            'meta_keywords': news.meta_keywords,
            'media_id': news.media.id if news.media else None,
            'media_url': news.media.path if news.media else None,
            'status': news.status
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def news_delete(request, news_id):
    """Soft delete news"""
    try:
        news = get_object_or_404(News, id=news_id)
        news.deleted_at = timezone.now()
        news.save()
        
        return JsonResponse({
            'success': True,
            'message': 'News deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def news_toggle_status(request, news_id):
    """Toggle news status"""
    try:
        news = get_object_or_404(News, id=news_id, deleted_at__isnull=True)
        news.status = 0 if news.status == 1 else 1
        news.updated_by = request.user.id
        news.save()
        
        return JsonResponse({
            'success': True,
            'status': news.status,
            'message': f'News {"activated" if news.status == 1 else "deactivated"} successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

# media library 

@login_required
def media_list(request):
    """Display media library with pagination"""
    # Get filter and search parameters
    media_type_filter = request.GET.get('type', '')
    search_query = request.GET.get('search', '')
    page = request.GET.get('page', 1)
    
    # Base query
    media_query = MediaLibrary.objects.filter(deleted_at__isnull=True)
    
    # Apply filters
    if media_type_filter:
        media_query = media_query.filter(media_type=media_type_filter)
    
    # Apply search
    if search_query:
        media_query = media_query.filter(
            Q(title__icontains=search_query) |
            Q(file_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(file_type__icontains=search_query)
        )
    
    # Order by newest first
    media_query = media_query.order_by('-created_at')
    
    # Paginate
    paginator = Paginator(media_query, 12)  # 12 items per page
    
    try:
        media_items = paginator.page(page)
    except PageNotAnInteger:
        media_items = paginator.page(1)
    except EmptyPage:
        media_items = paginator.page(paginator.num_pages)
    
    # Process media items for safe display
    processed_items = []
    for media in media_items:
        try:
            file_url = media.file_path.url if media.file_path else ''
        except:
            file_url = ''
        
        thumb_url = media.thumb_file_path if media.thumb_file_path else file_url
        
        processed_items.append({
            'id': media.id,
            'file_name': media.file_name,
            'file_url': file_url,
            'thumb_url': thumb_url,
            'file_type': media.file_type,
            'file_size': media.file_size,
            'dimensions': media.dimensions,
            'media_type': media.media_type,
            'title': media.title or media.file_name,
            'description': media.description or '',
            'alt_text': media.alt_text or '',
            'created_at': media.created_at
        })
    
    context = {
        'page_title': 'Media Library',
        'media_items': processed_items,
        'paginator': paginator,
        'page_obj': media_items,
        'current_type': media_type_filter,
        'current_search': search_query,
    }
    
    return render(request, 'admin/media/media_list.html', context)

@login_required
@require_POST
def media_upload(request):
    """Handle media file upload"""
    try:
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return JsonResponse({
                'success': False,
                'message': 'No file uploaded'
            }, status=400)
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024
        if uploaded_file.size > max_size:
            return JsonResponse({
                'success': False,
                'message': 'File size exceeds 10MB limit'
            }, status=400)
        
        # Get form data
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        alt_text = request.POST.get('alt_text', '').strip()
        
        # Determine media type
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        file_type = file_ext.replace('.', '')
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
        document_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
        
        if file_ext in image_extensions:
            media_type = 'image'
        elif file_ext in video_extensions:
            media_type = 'video'
        elif file_ext in document_extensions:
            media_type = 'document'
        else:
            media_type = 'other'
        
        # Calculate file size
        file_size_bytes = uploaded_file.size
        if file_size_bytes < 1024:
            file_size = f"{file_size_bytes} B"
        elif file_size_bytes < 1024 * 1024:
            file_size = f"{file_size_bytes / 1024:.2f} KB"
        else:
            file_size = f"{file_size_bytes / (1024 * 1024):.2f} MB"
        
        # Generate unique filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        clean_filename = uploaded_file.name.replace(' ', '_')
        filename = f"{timestamp}_{clean_filename}"
        
        # Process dimensions for images
        dimensions = None
        thumb_url = ''
        slider_url = ''
        
        if media_type == 'image':
            try:
                img = Image.open(uploaded_file)
                dimensions = f"{img.width}x{img.height}"
                
                # Convert RGBA to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                
                # Reset file pointer for saving
                uploaded_file.seek(0)
                
            except Exception as e:
                print(f"Error processing image: {e}")
        
        # Create media record
        media = MediaLibrary()
        media.file_name = uploaded_file.name
        media.file_path = uploaded_file
        media.thumb_file_path = thumb_url
        media.slider_file_path = slider_url if media_type == 'image' else None
        media.file_type = file_type
        media.file_size = file_size
        media.dimensions = dimensions
        media.media_type = media_type
        media.title = title or uploaded_file.name
        media.description = description
        media.alt_text = alt_text
        media.created_by = request.user
        media.updated_by = request.user
        media.save()
        
        return JsonResponse({
            'success': True,
            'message': 'File uploaded successfully',
            'media_id': media.id
        })
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Upload failed: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def media_get(request, media_id):
    """Get media data as JSON"""
    # Check authentication WITHOUT redirecting
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    try:
        media = get_object_or_404(MediaLibrary, id=media_id, deleted_at__isnull=True)
        
        try:
            file_url = media.file_path.url if media.file_path else ''
        except:
            file_url = ''
        
        thumb_url = media.thumb_file_path if media.thumb_file_path else file_url
        slider_url = media.slider_file_path if media.slider_file_path else file_url
        
        data = {
            'id': media.id,
            'file_name': media.file_name,
            'file_path': file_url,
            'thumb_file_path': thumb_url,
            'slider_file_path': slider_url,
            'file_type': media.file_type,
            'file_size': media.file_size,
            'dimensions': media.dimensions,
            'media_type': media.media_type,
            'title': media.title or '',
            'description': media.description or '',
            'alt_text': media.alt_text or '',
            'created_at': media.created_at.strftime('%b %d, %Y %I:%M %p') if media.created_at else ''
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except MediaLibrary.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Media not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to load media: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
def media_update(request, media_id):
    """Update media metadata"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    try:
        media = get_object_or_404(MediaLibrary, id=media_id, deleted_at__isnull=True)
        
        media.title = request.POST.get('title', '').strip() or media.title
        media.description = request.POST.get('description', '').strip()
        media.alt_text = request.POST.get('alt_text', '').strip()
        media.updated_by = request.user
        media.updated_at = timezone.now()
        media.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Media updated successfully'
        })
    except MediaLibrary.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Media not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Update failed: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
def media_delete(request, media_id):
    """Soft delete media"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    try:
        media = get_object_or_404(MediaLibrary, id=media_id, deleted_at__isnull=True)
        media.deleted_at = timezone.now()
        media.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Media deleted successfully'
        })
    except MediaLibrary.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Media not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Delete failed: {str(e)}'
        }, status=500)
    
# Photos Functionalities

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime
import json

@login_required
def photo_gallery(request):
    """Main photo gallery page"""
    categories = Categories.objects.filter(
        deleted_at__isnull=True,
        type='photo'
    ).order_by('name')
    
    context = {
        'categories': categories
    }
    return render(request, "admin/media/photo_gallery.html", context)

@login_required
def photo_datatable(request):
    """DataTable AJAX endpoint for photos"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 12))
    search_value = request.GET.get('search[value]', '')
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'desc')
    
    # Filters
    category_filter = request.GET.get('category', '')
    
    # Base query
    photos = Photos.objects.filter(deleted_at__isnull=True).select_related(
        'media', 'categories', 'created_by'
    )
    
    # Apply filters
    if category_filter:
        photos = photos.filter(categories_id=category_filter)
    
    # Apply search
    if search_value:
        photos = photos.filter(
            Q(title__icontains=search_value) |
            Q(description__icontains=search_value) |
            Q(media__file_name__icontains=search_value) |
            Q(alt_text__icontains=search_value)
        )
    
    # Total records
    total_records = Photos.objects.filter(deleted_at__isnull=True).count()
    filtered_records = photos.count()
    
    # Ordering
    order_columns = ['id', 'title', 'categories__name', 'created_at']
    if order_column_index < len(order_columns):
        order_by = order_columns[order_column_index]
        if order_direction == 'desc':
            order_by = f'-{order_by}'
        photos = photos.order_by(order_by)
    else:
        photos = photos.order_by('-created_at')
    
    # Pagination
    photos = photos[start:start + length]
    
    # Prepare data
    data = []
    for photo in photos:
        # Preview
        if photo.media and photo.media.file_path:
            preview = f'''
                <img src="{photo.media.file_path.url}" 
                     class="photo-preview-img" 
                     alt="{photo.alt_text or photo.title or 'Photo'}"
                     onclick="viewPhoto({photo.id})">
            '''
        else:
            preview = '<div class="no-preview">No Image</div>'
        
        # Info
        category_name = photo.categories.name if photo.categories else 'Uncategorized'
        info = f'''
            <div class="photo-info">
                <div class="photo-title">{photo.title or 'Untitled'}</div>
                <div class="photo-meta">
                    <span class="category-badge">{category_name}</span>
                </div>
            </div>
        '''
        
        # Description
        description = photo.description[:100] + '...' if photo.description and len(photo.description) > 100 else (photo.description or '-')
        
        # Actions
        actions = f'''
            <div class="photo-actions">
                <button class="btn-photo-action btn-view" onclick="viewPhoto({photo.id})" title="View">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn-photo-action btn-edit" onclick="editPhoto({photo.id})" title="Edit">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn-photo-action btn-delete" onclick="deletePhoto({photo.id}, '{photo.title or 'this photo'}')" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        '''
        
        data.append({
            'id': photo.id,
            'preview': preview,
            'info': info,
            'description': description,
            'created_at': photo.created_at.strftime('%Y-%m-%d'),
            'actions': actions
        })
    
    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })

@require_http_methods(["POST"])
def photo_create(request):
    """Create a new photo with media library upload"""
    try:
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        alt_text = request.POST.get('alt_text', '')
        category_id = request.POST.get('category_id')
        
        # Check if uploading new file or using existing media
        uploaded_file = request.FILES.get('file')
        media_id = request.POST.get('media_id')
        
        if not uploaded_file and not media_id:
            return JsonResponse({
                'success': False,
                'message': 'Please upload a file or select from media library'
            }, status=400)
        
        # If new file uploaded, create media library entry
        if uploaded_file:
            from PIL import Image
            import os
            
            # Get file info
            file_name = uploaded_file.name
            file_size = uploaded_file.size
            file_type = file_name.split('.')[-1].lower()
            
            # Determine media type
            image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']
            video_extensions = ['mp4', 'avi', 'mov', 'wmv', 'flv']
            document_extensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']
            
            if file_type in image_extensions:
                media_type = 'image'
            elif file_type in video_extensions:
                media_type = 'video'
            elif file_type in document_extensions:
                media_type = 'document'
            else:
                media_type = 'other'
            
            # Get dimensions for images
            dimensions = None
            if media_type == 'image':
                try:
                    img = Image.open(uploaded_file)
                    dimensions = f"{img.width}x{img.height}"
                    uploaded_file.seek(0)  # Reset file pointer
                except:
                    pass
            
            # Format file size
            if file_size < 1024:
                formatted_size = f"{file_size} B"
            elif file_size < 1024 * 1024:
                formatted_size = f"{file_size / 1024:.2f} KB"
            else:
                formatted_size = f"{file_size / (1024 * 1024):.2f} MB"
            
            # Create MediaLibrary entry
            media = MediaLibrary.objects.create(
                file_name=file_name,
                file_path=uploaded_file,
                thumb_file_path='',  # Can be generated separately
                slider_file_path='',
                file_type=file_type,
                file_size=formatted_size,
                dimensions=dimensions,
                media_type=media_type,
                title=title,
                description=description,
                alt_text=alt_text,
                created_by=request.user,
                updated_by=request.user
            )
        else:
            # Use existing media
            media = get_object_or_404(MediaLibrary, id=media_id, deleted_at__isnull=True)
        
        # Create Photo entry
        photo = Photos.objects.create(
            media=media,
            title=title,
            description=description,
            alt_text=alt_text,
            categories_id=category_id if category_id else None,
            created_by=request.user,
            updated_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Photo created successfully',
            'photo_id': photo.id
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'message': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

@login_required
def photo_get(request, photo_id):
    """Get photo details with full media library data"""
    try:
        photo = get_object_or_404(
            Photos.objects.select_related('media', 'categories', 'created_by'),
            id=photo_id,
            deleted_at__isnull=True
        )
        
        # Get media library data
        media_data = {}
        if photo.media:
            media_data = {
                'id': photo.media.id,
                'file_path': photo.media.file_path.url if photo.media.file_path else '',
                'file_name': photo.media.file_name,
                'file_size': photo.media.file_size,
                'file_type': photo.media.file_type,
                'dimensions': photo.media.dimensions or '',
                'media_type': photo.media.media_type,
                'thumb_path': photo.media.thumb_file_path or (photo.media.file_path.url if photo.media.file_path else ''),
                'slider_path': photo.media.slider_file_path or '',
            }
        
        data = {
            'id': photo.id,
            'title': photo.title or '',
            'description': photo.description or '',
            'alt_text': photo.alt_text or '',
            'category_id': photo.categories.id if photo.categories else None,
            'category_name': photo.categories.name if photo.categories else 'Uncategorized',
            'created_at': photo.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': photo.updated_at.strftime('%Y-%m-%d %H:%M'),
            'created_by': photo.created_by.username if photo.created_by else '',
            'media': media_data
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'message': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

@login_required
@require_http_methods(["POST"])
def photo_update(request, photo_id):
    """Update photo details"""
    try:
        photo = get_object_or_404(Photos, id=photo_id, deleted_at__isnull=True)
        
        photo.title = request.POST.get('title', photo.title)
        photo.description = request.POST.get('description', photo.description)
        photo.alt_text = request.POST.get('alt_text', photo.alt_text)
        
        category_id = request.POST.get('category_id')
        if category_id:
            photo.categories_id = category_id
        
        photo.updated_by = request.user
        photo.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Photo updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def photo_delete(request, photo_id):
    """Soft delete a photo"""
    try:
        photo = get_object_or_404(Photos, id=photo_id, deleted_at__isnull=True)
        
        photo.deleted_at = datetime.now()
        photo.updated_by = request.user
        photo.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Photo deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required
def media_library_list(request):
    """Get available media for photo selection"""
    try:
        search = request.GET.get('search', '')
        
        media_items = MediaLibrary.objects.filter(
            deleted_at__isnull=True,
            media_type='image'
        )
        
        if search:
            media_items = media_items.filter(
                Q(file_name__icontains=search) |
                Q(title__icontains=search)
            )
        
        media_items = media_items.order_by('-created_at')[:20]
        
        data = [{
            'id': item.id,
            'file_name': item.file_name,
            'file_path': item.file_path.url if item.file_path else '',
            'thumb_path': item.thumb_file_path or (item.file_path.url if item.file_path else ''),
            'title': item.title or item.file_name
        } for item in media_items]
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

# sliders and slider Photos.....

# Helper function to safely get media URL
def get_media_url(media_object, default='https://s3-alpha.figma.com/hub/file/4093188630/561dfe3e-e5f8-415c-9b26-fbdf94897722-cover.png'):
    """Safely extract URL from media object's file_path field"""
    if not media_object:
        return default
    
    try:
        file_path = media_object.file_path
        if not file_path:
            return default
        # Check if it's a FileField/ImageField with .url attribute
        if hasattr(file_path, 'url'):
            try:
                return file_path.url
            except ValueError:
                return default
        # If it's a CharField, convert to string
        return str(file_path)
    except (AttributeError, Exception) as e:
        print(f"Error getting media URL: {e}")
        return default

@login_required
def slider_list(request):
    """Main slider list view - renders the page with DataTables"""
    context = {
        "page_title": "Slider Management"
    }
    return render(request, 'admin/sliders/list.html', context)

@login_required
def slider_datatable(request):
    """DataTables server-side processing for sliders"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 12))
        search_value = request.GET.get('search[value]', '')
        order_column_index = int(request.GET.get('order[0][column]', 0))
        order_direction = request.GET.get('order[0][dir]', 'desc')

        # Define column mapping
        columns = ['id', 'slider_name', 'code', 'width', 'height', 'created_at']
        order_column = columns[order_column_index] if order_column_index < len(columns) else 'id'
        
        if order_direction == 'desc':
            order_column = f'-{order_column}'

        # Query sliders with photo count
        sliders = Sliders.objects.annotate(
            photo_count=Count('photos', filter=Q(photos__deleted_at__isnull=True))
        )
        
        # Apply search
        if search_value:
            sliders = sliders.filter(
                Q(slider_name__icontains=search_value) |
                Q(code__icontains=search_value)
            )

        # Get total count
        total_records = sliders.count()
        
        # Apply ordering and pagination
        sliders = sliders.order_by(order_column)[start:start + length]

        # Prepare data
        data = []
        for slider in sliders:
            data.append({
                'id': slider.id,
                'slider_info': f'''
                    <div class="slider-info">
                        <div class="slider-name">{slider.slider_name}</div>
                        <div class="slider-meta">
                            <span class="code-badge">{slider.code}</span>
                        </div>
                    </div>
                ''',
                'dimensions': f'''
                    <span class="dimension-badge">
                        <i class="fas fa-expand-arrows-alt"></i>
                        {slider.width}×{slider.height}
                    </span>
                ''',
                'photos': f'''
                    <span class="photo-count-badge">
                        <i class="fas fa-images"></i>
                        {slider.photo_count}
                    </span>
                ''',
                'created_at': slider.created_at.strftime('%b %d, %Y') if slider.created_at else '-',
                'actions': f'''
                    <div class="action-buttons">
                        <button class="btn-action btn-photos" onclick="managePhotos({slider.id})" title="Manage Photos">
                            <i class="fas fa-images"></i>
                        </button>
                        <button class="btn-action btn-edit" onclick="editSlider({slider.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-action btn-delete" 
                            onclick="deleteSlider({slider.id}, '{slider.slider_name.replace("'", "\\'")}')" 
                            title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                '''
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })

@login_required
@require_http_methods(["POST"])
def slider_create(request):
    """Create new slider"""
    try:
        slider_name = request.POST.get('slider_name', '').strip()
        code = request.POST.get('code', '').strip()
        width = int(request.POST.get('width', 0))
        height = int(request.POST.get('height', 0))

        # Validation
        if not slider_name or not code:
            return JsonResponse({
                'success': False,
                'message': 'Slider name and code are required'
            })

        if width <= 0 or height <= 0:
            return JsonResponse({
                'success': False,
                'message': 'Width and height must be positive numbers'
            })

        # Check if code already exists
        if Sliders.objects.filter(code=code).exists():
            return JsonResponse({
                'success': False,
                'message': 'Slider code already exists'
            })

        slider = Sliders.objects.create(
            slider_name=slider_name,
            code=code,
            width=width,
            height=height,
            created_by=request.user,
            updated_by=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'Slider created successfully',
            'slider_id': slider.id
        })
    except ValueError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid width or height value'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def slider_get(request, slider_id):
    """Get slider details"""
    try:
        slider = get_object_or_404(Sliders, id=slider_id)
        return JsonResponse({
            'success': True,
            'data': {
                'id': slider.id,
                'slider_name': slider.slider_name,
                'code': slider.code,
                'width': slider.width,
                'height': slider.height,
                'created_at': slider.created_at.strftime('%Y-%m-%d %H:%M') if slider.created_at else None
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
@require_http_methods(["POST"])
def slider_update(request, slider_id):
    """Update slider"""
    try:
        slider = get_object_or_404(Sliders, id=slider_id)
        
        slider_name = request.POST.get('slider_name', '').strip()
        code = request.POST.get('code', '').strip()
        width = int(request.POST.get('width', 0))
        height = int(request.POST.get('height', 0))

        # Validation
        if not slider_name or not code:
            return JsonResponse({
                'success': False,
                'message': 'Slider name and code are required'
            })

        if width <= 0 or height <= 0:
            return JsonResponse({
                'success': False,
                'message': 'Width and height must be positive numbers'
            })

        # Check if code exists for other sliders
        if Sliders.objects.filter(code=code).exclude(id=slider_id).exists():
            return JsonResponse({
                'success': False,
                'message': 'Slider code already exists'
            })

        slider.slider_name = slider_name
        slider.code = code
        slider.width = width
        slider.height = height
        slider.updated_by = request.user
        slider.save()

        return JsonResponse({
            'success': True,
            'message': 'Slider updated successfully'
        })
    except ValueError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid width or height value'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
@require_http_methods(["POST"])
def slider_delete(request, slider_id):
    """Delete slider and all associated photos"""
    try:
        slider = get_object_or_404(Sliders, id=slider_id)
        slider.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Slider deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# ============= SLIDER PHOTOS VIEWS =============

@login_required
def slider_photos_list(request, slider_id):
    """Slider photos management view"""
    slider = get_object_or_404(Sliders, id=slider_id)
    context = {
        'slider': slider,
        'page_title': f'Photos - {slider.slider_name}'
    }
    return render(request, 'admin/sliders/photos.html', context)

@login_required
def slider_photos_datatable(request, slider_id):
    """DataTables for slider photos"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 12))
        search_value = request.GET.get('search[value]', '')

        photos = SliderPhotos.objects.filter(
            sliders_id=slider_id,
            deleted_at__isnull=True
        ).select_related('media')

        # Apply search
        if search_value:
            photos = photos.filter(
                Q(title__icontains=search_value) |
                Q(button_text__icontains=search_value)
            )

        total_records = photos.count()
        photos = photos.order_by('-id')[start:start + length]

        data = []
        for photo in photos:
            # Use helper function to get media URL
            media_url = get_media_url(photo.media)
            title = photo.title or 'Untitled'
            
            data.append({
                'id': photo.id,
                'preview': f'<img src="{media_url}" class="photo-preview" alt="{photo.alt_text or title}">',
                'info': f'''
                    <div class="photo-info">
                        <div class="photo-title">{title}</div>
                        <div class="photo-button-info">
                            {f'<span class="button-badge">{photo.button_text}</span>' if photo.button_text else ''}
                        </div>
                    </div>
                ''',
                'created_at': photo.created_at.strftime('%b %d, %Y') if photo.created_at else '-',
                'actions': f'''
                    <div class="btn-group" role="group">
        <button class="btn btn-info btn-sm mr-1" onclick="viewPhoto({photo.id})" title="View">
                            <i class="fas fa-eye"></i>
                        </button>
        <div class="btn-group" role="group">
            <button id="btnGroupDrop{photo.id}" type="button" class="btn btn-secondary btn-sm dropdown-toggle" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                Actions
            </button>
            <div class="dropdown-menu" aria-labelledby="btnGroupDrop{photo.id}">
                <button class="dropdown-item dropdown-item" style="width:100%; text-align:left; background:none; border:none;" onclick="editPhoto({photo.id})" title="Edit">
                            <i class="fas fa-edit mr-2 text-primary"></i> Edit
                        </button>
                <button class="dropdown-item dropdown-item" style="width:100%; text-align:left; background:none; border:none;" onclick="deletePhoto({photo.id})" title="Delete">
                            <i class="fas fa-trash mr-2 text-danger"></i> <span class="text-danger">Delete</span>
                        </button>
            </div>
        </div>
    </div>
                '''
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })

@login_required
@require_http_methods(["POST"])
def slider_photo_create(request, slider_id):
    """Add photo to slider"""
    try:
        media_id = request.POST.get('media_id')
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        alt_text = request.POST.get('alt_text', '').strip()
        button_text = request.POST.get('button_text', '').strip()
        button_link = request.POST.get('button_link', '').strip()
        button_link_target = request.POST.get('button_link_target', '_self')

        # Validation
        if not media_id:
            return JsonResponse({
                'success': False,
                'message': 'Please select an image'
            })

        # Verify slider exists
        slider = get_object_or_404(Sliders, id=slider_id)

        # Verify media exists
        media = get_object_or_404(MediaLibrary, id=media_id)

        photo = SliderPhotos.objects.create(
            sliders=slider,
            media=media,
            title=title if title else None,
            description=description if description else None,
            alt_text=alt_text if alt_text else None,
            button_text=button_text if button_text else None,
            button_link=button_link if button_link else None,
            button_link_target=button_link_target,
            created_by=request.user,
            updated_by=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'Photo added successfully',
            'photo_id': photo.id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def slider_photo_get(request, photo_id):
    """Get slider photo details"""
    try:
        photo = get_object_or_404(SliderPhotos, id=photo_id, deleted_at__isnull=True)
        
        # Use helper function to get media URL
        media_url = get_media_url(photo.media)

        return JsonResponse({
            'success': True,
            'data': {
                'id': photo.id,
                'media_id': photo.media_id,
                'media_url': media_url,
                'title': photo.title or '',
                'description': photo.description or '',
                'alt_text': photo.alt_text or '',
                'button_text': photo.button_text or '',
                'button_link': photo.button_link or '',
                'button_link_target': photo.button_link_target or '_self'
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
@require_http_methods(["POST"])
def slider_photo_update(request, photo_id):
    """Update slider photo"""
    try:
        photo = get_object_or_404(SliderPhotos, id=photo_id, deleted_at__isnull=True)
        
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        alt_text = request.POST.get('alt_text', '').strip()
        button_text = request.POST.get('button_text', '').strip()
        button_link = request.POST.get('button_link', '').strip()
        button_link_target = request.POST.get('button_link_target', '_self')

        media_id = request.POST.get('media_id')  # Get media_id from form

        # Update media if provided
        if media_id:
            media = get_object_or_404(MediaLibrary, id=media_id)
            photo.media = media
            
        photo.title = title if title else None
        photo.description = description if description else None
        photo.alt_text = alt_text if alt_text else None
        photo.button_text = button_text if button_text else None
        photo.button_link = button_link if button_link else None
        photo.button_link_target = button_link_target
        photo.updated_by = request.user
        photo.save()

        return JsonResponse({
            'success': True,
            'message': 'Photo updated successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
@require_http_methods(["POST"])
def slider_photo_delete(request, photo_id):
    """Soft delete slider photo"""
    try:
        photo = get_object_or_404(SliderPhotos, id=photo_id, deleted_at__isnull=True)
        photo.deleted_at = timezone.now()
        photo.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Photo deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# slider photos end 

##@login_required
def course_list(request):
    """Main course list view"""
    return render(request, 'admin/courses/list.html')

##@login_required
def course_datatable(request):
    """DataTables server-side processing for courses"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 12))
        search_value = request.GET.get('search[value]', '')
        order_column_index = int(request.GET.get('order[0][column]', 0))
        order_direction = request.GET.get('order[0][dir]', 'desc')
        status_filter = request.GET.get('status', '')

        # Define column mapping
        columns = ['id', 'course_name', 'course_code', 'highest_qualification', 'credit_hours', 'status', 'created_at']
        order_column = columns[order_column_index] if order_column_index < len(columns) else 'id'
        
        if order_direction == 'desc':
            order_column = f'-{order_column}'

        # Query courses
        # courses = Courses.objects.select_related('media')
        courses = Courses.objects.select_related('highest_qualification').all()

        # Apply status filter
        if status_filter:
            courses = courses.filter(status=int(status_filter))
        
        # Apply search
        if search_value:
            courses = courses.filter(
                Q(course_name__icontains=search_value) |
                Q(course_code__icontains=search_value) |
                Q(description__icontains=search_value)
            )

        # Get total count
        total_records = courses.count()
        
        # Check for export
        if request.GET.get('export') == 'excel':
            return export_to_excel(
                queryset=courses,
                filename="courses_list",
                columns=['course_name', 'course_code', 'highest_qualification.qualification_name', 'credit_hours', 'status', 'created_at'],
                headers=['Course Name', 'Code', 'Qualification', 'Credit Hours', 'Status', 'Created At']
            )

        # Apply ordering and pagination
        courses = courses.order_by(order_column)[start:start + length]

        # Prepare data
        data = []
        for course in courses:
            # Get media thumbnail
            media_preview = ''
            if course.media:
                try:
                    media_url = course.media.file_path.url
                    media_preview = f'<img src="{media_url}" class="course-thumb" alt="{course.course_name}">'
                except:
                    media_preview = '<div class="course-thumb-placeholder"><i class="fas fa-graduation-cap"></i></div>'
            else:
                media_preview = '<div class="course-thumb-placeholder"><i class="fas fa-graduation-cap"></i></div>'
            
            # Status badge
            status_text = 'Active' if course.status == 1 else 'Inactive'
            status_class = 'status-active' if course.status == 1 else 'status-inactive'
            
            # Qualification levels - Dynamic
            qual_text = course.highest_qualification.qualification_name if course.highest_qualification else 'Unknown'
            
            data.append({
                'id': course.id,
                'preview': media_preview,
                'course_info': f'''<div class="course-info">
                    <div class="course-name">{course.course_name}</div>
                    <div class="course-meta">
                        <span class="code-badge">{course.course_code}</span>
                        <span class="qual-badge">{qual_text}</span>
                        <span class="credit-badge">{course.credit_hours} Credits</span>
                    </div>
                </div>''',
                'status': f'<span class="status-badge {status_class}">{status_text}</span>',
                'created_at': course.created_at.strftime('%Y-%m-%d') if course.created_at else '-',
                'actions': f'''<div class="btn-group" role="group">
        <button class="btn btn-info btn-sm mr-1" onclick="viewCourse({course.id})" title="View">
                        <i class="fas fa-eye"></i>
                    </button>
        <div class="btn-group" role="group">
            <button id="btnGroupDrop{course.id}" type="button" class="btn btn-secondary btn-sm dropdown-toggle" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                Actions
            </button>
            <div class="dropdown-menu" aria-labelledby="btnGroupDrop{course.id}">
                <a href="/menu/courses/update/{course.id}/" class="dropdown-item" title="Edit">
                        <i class="fas fa-edit mr-2 text-primary"></i> Edit
                    </a>
                <button class="dropdown-item dropdown-item" style="width:100%; text-align:left; background:none; border:none;" onclick="deleteCourse({course.id}, '{course.course_name}')" title="Delete">
                        <i class="fas fa-trash mr-2 text-danger"></i> <span class="text-danger">Delete</span>
                    </button>
            </div>
        </div>
    </div>'''
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data
        })
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'error': str(e),
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })

##@login_required
@login_required
def course_create(request):
    """Create new course"""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            try:
                course = form.save(commit=False)
                course.created_by = request.user
                course.updated_by = request.user
                course.created_at = timezone.now()
                
                # Check for existing course code
                if Courses.objects.filter(course_code=course.course_code).exists():
                    messages.error(request, 'Course code already exists')
                    return render(request, 'admin/courses/form.html', {'form': form})
                
                course.save()
                messages.success(request, 'Course created successfully')
                return redirect('course_list')
            except Exception as e:
                messages.error(request, f'Error creating course: {str(e)}')
        else:
             messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseForm()
    
    return render(request, 'admin/courses/form.html', {'form': form})

##@login_required
def course_get(request, course_id):
    """Get course details"""
    try:
        course = get_object_or_404(Courses, id=course_id)
        
        # Get media info
        media_data = None
        if course.media:
            try:
                media_data = {
                    'id': course.media.id,
                    'url': course.media.file_path.url,
                    'title': course.media.title or course.media.file_name
                }
            except:
                pass
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': course.id,
                'course_name': course.course_name,
                'course_code': course.course_code,
                'highest_qualification': course.highest_qualification_id,
                'credit_hours': str(course.credit_hours),
                'description': course.description or '',
                'browser_title': course.browser_title or '',
                'meta_description': course.meta_description or '',
                'meta_keywords': course.meta_keywords or '',
                'media_id': course.media_id,
                'media': media_data,
                'status': course.status,
                'apply_button_top': course.apply_button_top,
                'apply_button_bottom': course.apply_button_bottom,
                'qualification_name': course.highest_qualification.qualification_name if course.highest_qualification else 'N/A',
                'created_at': course.created_at.strftime('%Y-%m-%d %H:%M') if course.created_at else '-'
            }
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def course_update(request, course_id):
    """Update course"""
    course = get_object_or_404(Courses, id=course_id)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            try:
                course = form.save(commit=False)
                course.updated_by = request.user
                
                # Check for existing course code (excluding current)
                if Courses.objects.filter(course_code=course.course_code).exclude(id=course_id).exists():
                    messages.error(request, 'Course code already exists')
                    return render(request, 'admin/courses/form.html', {'form': form, 'course': course})
                
                course.save()
                messages.success(request, 'Course updated successfully')
                return redirect('course_list')
            except Exception as e:
                messages.error(request, f'Error updating course: {str(e)}')
        else:
             messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseForm(instance=course)
            
    context = {
        'form': form,
        'course': course
    }
    return render(request, 'admin/courses/form.html', context)

##@login_required
@login_required
def course_delete(request, course_id):
    """Delete course"""
    try:
        course = get_object_or_404(Courses, id=course_id)
        course.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Course deleted successfully'
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
import json

#@login_required
def student_list_view(request):
    """Render student management page"""
    context = {
        'countries': Countries.objects.all().order_by('name'),
        'languages': Languages.objects.filter(status=True).order_by('language_name'),
        'courses': Courses.objects.filter(status=1).order_by('course_name'),
    }
    return render(request, 'admin/students/list.html', context)

#@login_required
def student_datatable(request):
    """DataTables server-side processing for students"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        order_column_index = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'desc')
        
        # Filters
        status_filter = request.GET.get('status', '')
        active_filter = request.GET.get('active', '')
        course_filter = request.GET.get('course', '')
        list_type = request.GET.get('type', 'student') # 'student' or 'applicant'
        
        # Base queryset
        students = Students.objects.select_related('user', 'language').all()

        # Filter by Type (Student vs Applicant)
        if list_type == 'applicant':
            # Applicants are those with status=False and active=False
            students = students.filter(status=False, active=False)
        else:
            # Students list should show ALL records to allow filtering by Pending/Approved
            # Previously: students = students.filter(approve_date__isnull=False)
            pass
        
        # Apply filters
        # Note: status_filter might be redundant if using type, but keeping it for specific column filtering if needed
        if status_filter:
            students = students.filter(status=status_filter == '1')
        
        if active_filter:
            students = students.filter(active=active_filter == '1')
            
        if course_filter:
            students = students.filter(course_applied=course_filter)
        
        # Search
        if search_value:
            students = students.filter(
                Q(first_name__icontains=search_value) |
                Q(last_name__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(student_id__icontains=search_value) |
                Q(phone_number__icontains=search_value)
            )
        
        # Ordering
        order_columns = ['id', 'student_id', 'first_name', 'email', 'status', 'created_at', 'actions']
        
        # Default to created_at desc if no order received or id is defaults
        if not request.GET.get('order[0][column]'):
             order_column = '-created_at'
        else:
            order_column = order_columns[order_column_index] if order_column_index < len(order_columns) else 'created_at'
            if order_dir == 'desc':
                order_column = f'-{order_column}'
        
        students = students.order_by(order_column)
        
        # Total records
        total_records = Students.objects.count()
        filtered_records = students.count()
        
        # Check for export
        if request.GET.get('export') == 'excel':
            return export_to_excel(
                queryset=students,
                filename="students_list",
                columns=['student_id', 'first_name', 'last_name', 'email', 'phone_number', 'course_applied.course_name', 'status', 'active', 'created_at'],
                headers=['Student ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Course', 'Approved', 'Active', 'Joined Date']
            )

        # Pagination
        students = students[start:start + length]
        
        # Format data
        data = []
        for student in students:
            # Get full name
            full_name = f"{student.first_name or ''} {student.middle_name or ''} {student.last_name or ''}".strip()
            
            # Student info - responsive
            # Photo preview - responsive
            if student.photo:
                preview = f'<img src="{student.photo}" class="student-photo rounded-circle" alt="{full_name}" style="width: 40px; height: 40px; object-fit: cover;">'
            else:
                first_initial = student.first_name[0].upper() if student.first_name else ''
                # last_initial = student.last_name[0].upper() if student.last_name else ''
                # initials = f"{first_initial}{last_initial}"
                # User requested "first letter", sticking to just one can be cleaner for small circles, or keep two if fits.
                # "show the first letter of the page" -> assuming Name.
                preview = f'<div class="student-photo-placeholder rounded-circle d-flex align-items-center justify-content-center bg-primary text-white" style="width: 40px; height: 40px; font-weight: bold;">{first_initial}</div>'

            # Determine status based on list type (Applicant vs Student)
            is_approved = student.status # Default from DB
            if list_type == 'applicant':
                 is_approved = False
            elif list_type == 'student':
                 is_approved = True

            info_html = f'''
                <div class="student-info">
                    <div class="student-name">{full_name}</div>
                    <div class="student-meta">
                        <span class="student-badge"><i class="fas fa-id-card"></i> {student.student_id or 'N/A'}</span>
                    </div>
                </div>
            '''
            
            # Status badges - stacked for mobile
            status_html = f'''
                <div class="status-container">
                    <span class="status-badge status-{'approved' if is_approved else 'pending'}">
                        <i class="fas fa-{'check-circle' if is_approved else 'clock'}"></i>
                        {'Approved' if is_approved else 'Pending'}
                    </span>
                    <span class="status-badge status-{'active' if student.active else 'inactive'}">
                        <i class="fas fa-{'power-off' if student.active else 'ban'}"></i>
                        {'Active' if student.active else 'Inactive'}
                    </span>
                </div>
            '''
            safe_name=full_name.replace("'", "\\'")
            # Actions - responsive
            # Changed data-toggle to data-bs-toggle for Bootstrap 5
            # Generate detail URL
            detail_url = reverse('student_detail', kwargs={'student_id': student.id})
            
            actions_html = f'''
                <div class="btn-group" role="group">
                    <a href="{detail_url}" class="btn btn-info btn-sm view-btn mr-1" title="View Details">
                        <i class="fas fa-eye"></i>
                    </a>
                    <div class="btn-group" role="group">
                        <button id="btnGroupDrop{student.id}" type="button" class="btn btn-secondary btn-sm dropdown-toggle" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                            Actions
                        </button>
                        <div class="dropdown-menu" aria-labelledby="btnGroupDrop{student.id}">
                            <a class="dropdown-item" href="#" onclick="editStudent({student.id}); return false;">
                                <i class="fas fa-edit mr-2 text-primary"></i> Edit
                            </a>
                            <a class="dropdown-item" href="#" onclick="toggleActive({student.id}, {str(student.active).lower()}); return false;">
                                <i class="fas fa-{'toggle-on' if student.active else 'toggle-off'} mr-2 text-warning"></i> {'Deactivate' if student.active else 'Activate'}
                            </a>
                            <a class="dropdown-item" href="#" onclick="toggleApproval({student.id}, {str(student.status).lower()}); return false;">
                                <i class="fas fa-{'times-circle' if student.status else 'check-circle'} mr-2 text-success"></i> {'Reject' if student.status else 'Approve'}
                            </a>
                            <div class="dropdown-divider"></div>
                            <a class="dropdown-item" href="#" onclick="deleteStudent({student.id}, '{safe_name}'); return false;">
                                <i class="fas fa-trash mr-2 text-danger"></i> <span class="text-danger">Delete</span>
                            </a>
                        </div>
                    </div>
                </div>
            '''
            
            data.append({
                'id': student.id,
                'student_id': student.student_id or 'N/A',
                'preview': preview,
                'student_info': info_html,
                'email': student.email or '',
                'status': status_html,
                'created_at': student.created_at.strftime('%Y-%m-%d') if student.created_at else 'N/A',
                'actions': actions_html
            })
        
        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })
        
    except Exception as e:
        print(f"DataTable Error: {str(e)}")  # Debug logging
        return JsonResponse({
            'error': str(e),
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })

#@login_required
def student_create(request):
    """Create new student"""
    if request.method == 'POST':
        try:
            # Get form data
            data = request.POST
            
            # Create student
            student = Students.objects.create(
                student_id=data.get('student_id', ''),
                first_name=data.get('first_name'),
                middle_name=data.get('middle_name', ''),
                last_name=data.get('last_name', ''),
                email=data.get('email', ''),
                gender=data.get('gender', ''),
                citizenship=data.get('citizenship') or None,
                phone_code=data.get('phone_code') or None,
                phone_number=data.get('phone_number', ''),
                date_of_birth=data.get('date_of_birth') or None,
                mrital_status=data.get('mrital_status', ''),
                spouse_name=data.get('spouse_name', ''),
                children=data.get('children') or None,
                mailing_address=data.get('mailing_address', ''),
                city=data.get('city', ''),
                state=data.get('state', ''),
                country=data.get('country') or None,
                zip_code=data.get('zip_code', ''),
                timezone=data.get('timezone', 'UTC'),
                highest_education=data.get('highest_education', ''),
                course_applied=data.get('course_applied') or None,
                associate_degree=data.get('associate_degree') or None,
                language_id=data.get('language') or 1,
                starting_year=data.get('starting_year') or None,
                ministerial_status=data.get('ministerial_status', ''),
                church_affiliation=data.get('church_affiliation', ''),
                scholarship_needed=data.get('scholarship_needed', ''),
                currently_employed=data.get('currently_employed', ''),
                income=data.get('income', ''),
                affordable_amount=data.get('affordable_amount', ''),
                message=data.get('message', ''),
                status=data.get('status', '0') == '1',
                active=data.get('active', '0') == '1',
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Student created successfully',
                'student_id': student.id
            })
            
        except Exception as e:
            print(f"Create Error: {str(e)}")  # Debug logging
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

#@login_required
def student_get(request, student_id):
    """Get student details"""
    try:
        student = Students.objects.select_related('user', 'language').get(id=student_id)
        
        # Get language name safely
        language_name = 'N/A'
        if student.language:
            language_name = getattr(student.language, 'language_name', 'N/A')
        
        data = {
            'id': student.id,
            'student_id': student.student_id,
            'first_name': student.first_name,
            'middle_name': student.middle_name or '',
            'last_name': student.last_name or '',
            'email': student.email or '',
            'gender': student.gender or '',
            'citizenship': student.citizenship.id if student.citizenship else None,
            'citizenship_name': student.citizenship.name if student.citizenship else '',
            'phone_code': student.phone_code,
            'phone_number': student.phone_number or '',
            'date_of_birth': student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else '',
            'mrital_status': student.mrital_status or '',
            'spouse_name': student.spouse_name or '',
            'children': student.children,
            'mailing_address': student.mailing_address or '',
            'city': student.city or '',
            'state': student.state or '',
            'country': student.country.id if student.country else None,
            'country_name': student.country.name if student.country else '',
            'photo': f'/media/{student.photo}' if student.photo else '',
            'zip_code': student.zip_code or '',
            'timezone': student.timezone,
            'highest_education': student.highest_education or '',
            'course_applied': student.course_applied.id if student.course_applied else None,
            'course_applied_name': student.course_applied.course_name if student.course_applied else '',
            'associate_degree': student.associate_degree,
            'language': student.language.id if student.language else None,
            'language_name': language_name,
            'starting_year': student.starting_year,
            'ministerial_status': student.ministerial_status or '',
            'church_affiliation': student.church_affiliation or '',
            'scholarship_needed': student.scholarship_needed or '',
            'currently_employed': student.currently_employed or '',
            'income': student.income or '',
            'affordable_amount': student.affordable_amount or '',
            'message': student.message or '',
            'reference_name1': student.reference_name1 or '',
            'reference_email1': student.reference_email1 or '',
            'reference_phone1': student.reference_phone1 or '',
            'reference_name2': student.reference_name2 or '',
            'reference_email2': student.reference_email2 or '',
            'reference_phone2': student.reference_phone2 or '',
            'reference_name3': student.reference_name3 or '',
            'reference_email3': student.reference_email3 or '',
            'reference_phone3': student.reference_phone3 or '',
            'status': 1 if student.status else 0,
            'active': 1 if student.active else 0,
            'approve_date': student.approve_date.strftime('%Y-%m-%d %H:%M:%S') if student.approve_date else None,
            'created_at': student.created_at.strftime('%Y-%m-%d %H:%M:%S') if student.created_at else 'N/A',
            'updated_at': student.updated_at.strftime('%Y-%m-%d %H:%M:%S') if student.updated_at else 'N/A',
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Students.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Student not found'
        }, status=404)
    except Exception as e:
        print(f"Get Error: {str(e)}")  # Debug logging
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


def student_detail(request, student_id):
    """View to show full student details"""
    student = get_object_or_404(Students.objects.select_related('course_applied', 'language', 'country'), id=student_id)
    return render(request, 'admin/students/view.html', {'student': student})

@require_http_methods(["POST"])
def student_approve_action(request, student_id):
    try:
        student = get_object_or_404(Students, id=student_id)
        student.status = True
        student.active = True
        student.approve_date = timezone.now()
        
        # ----------------START APPROVAL LOGIC----------------
        # Check for linked User
        user = student.user
        password = 'password123' # Default password for new approvals

        if not user:
            # FALLBACK: Create user if it doesn't exist (Legacy compatibility)
            if student.email:
                existing_user = Users.objects.filter(email=student.email).first()
                if existing_user:
                    user = existing_user
                    student.user = user
                else:
                    # Create new user
                    user = Users()
                    user.name = f"{student.first_name} {student.last_name if student.last_name else ''}".strip()
                    user.email = student.email
                    user.username = student.email
                    user.created_at = timezone.now()
                    user.save()
                    
                    student_role = Roles.objects.filter(name__iexact='Student').first()
                    if student_role:
                        RoleUsers.objects.create(user=user, role=student_role)
                    student.user = user
        
        # Activate User and Set Password
        if user:
            user.is_active = True
            user.set_password(password)
            user.updated_at = timezone.now()
            user.save()

            # Send Approval Email with Credentials
            try:
                subject = 'Welcome to Trinity Seminary - Registration Approved'
                message = f'''Dear {student.first_name},

Your registration has been approved. You can now login to the portal.

Login Details:
URL: https://trinityseminary.in/login (or your login URL)
Username: {user.email}
Password: {password}

IMPORTANT: Please change your password immediately after your first login.

Best regards,
Administration'''
                from_email = 'contact@byteboot.in' # Request specific sender
                recipient_list = [user.email]
                send_mail(subject, message, from_email, recipient_list)
            except Exception as e:
                print(f"Email sending failed: {str(e)}")
        else:
            print(f"Warning: No user linked or created for student {student.id}")
        # ----------------END APPROVAL LOGIC----------------

        student.save()
        messages.success(request, f"Student {student.first_name} has been approved and activated. Credentials sent to email.")
    except Exception as e:
         messages.error(request, f"Error during approval: {str(e)}")
         
    return redirect('student_detail', student_id=student.id)

@require_http_methods(["POST"])
def student_disapprove_action(request, student_id):
    student = get_object_or_404(Students, id=student_id)
    student.status = False
    student.save()
    messages.warning(request, f"Student {student.first_name} approval revoked.")
    return redirect('student_detail', student_id=student.id)

@require_http_methods(["POST"])
def student_activate_action(request, student_id):
    student = get_object_or_404(Students, id=student_id)
    student.active = True
    student.save()
    messages.success(request, f"Student {student.first_name} activated.")
    return redirect('student_detail', student_id=student.id)

@require_http_methods(["POST"])
def student_deactivate_action(request, student_id):
    student = get_object_or_404(Students, id=student_id)
    student.active = False
    student.save()
    messages.warning(request, f"Student {student.first_name} deactivated.")
    return redirect('student_detail', student_id=student.id)

#@login_required
def student_update(request, student_id):
    """Update student"""
    if request.method == 'POST':
        try:
            student = Students.objects.get(id=student_id)
            data = request.POST
            
            # Update fields
            student.student_id = data.get('student_id', student.student_id)
            student.first_name = data.get('first_name', student.first_name)
            student.middle_name = data.get('middle_name', '')
            student.last_name = data.get('last_name', '')
            student.email = data.get('email', '')
            student.gender = data.get('gender', '')
            student.citizenship_id = data.get('citizenship') or None
            student.phone_code = data.get('phone_code') or None
            student.phone_number = data.get('phone_number', '')
            student.date_of_birth = data.get('date_of_birth') or None
            student.mrital_status = data.get('mrital_status', '')
            student.spouse_name = data.get('spouse_name', '')
            student.children = data.get('children') or None
            student.mailing_address = data.get('mailing_address', '')
            student.city = data.get('city', '')
            student.state = data.get('state', '')
            student.country_id = data.get('country') or None
            student.zip_code = data.get('zip_code', '')
            student.timezone = data.get('timezone', 'UTC')
            student.highest_education = data.get('highest_education', '')
            student.course_applied_id = data.get('course_applied') or None
            student.associate_degree = data.get('associate_degree') or None
            student.language_id = data.get('language') or student.language_id
            student.starting_year = data.get('starting_year') or None
            student.ministerial_status = data.get('ministerial_status', '')
            student.church_affiliation = data.get('church_affiliation', '')
            student.scholarship_needed = data.get('scholarship_needed', '')
            student.currently_employed = data.get('currently_employed', '')
            student.income = data.get('income', '')
            student.affordable_amount = data.get('affordable_amount', '')
            student.message = data.get('message', '')
            # Handle Approval Status and Date
            new_status = data.get('status', '0') == '1'
            if new_status and not student.status: # transitioning to approved
                if not student.approve_date:
                    student.approve_date = timezone.now()
            
            student.status = new_status
            student.active = data.get('active', '0') == '1'
            student.updated_at = timezone.now()
            
            student.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Student updated successfully'
            })
            
        except Students.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Student not found'
            }, status=404)
        except Exception as e:
            print(f"Update Error: {str(e)}")  # Debug logging
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

#@login_required
def student_delete(request, student_id):
    """Delete student"""
    if request.method == 'POST':
        try:
            student = Students.objects.get(id=student_id)
            student.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Student deleted successfully'
            })
            
        except Students.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Student not found'
            }, status=404)
        except Exception as e:
            print(f"Delete Error: {str(e)}")  # Debug logging
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

#@login_required
def student_toggle_active(request, student_id):
    """Toggle student active status"""
    if request.method == 'POST':
        try:
            student = Students.objects.get(id=student_id)
            student.active = not student.active
            student.updated_at = timezone.now()
            student.save()
            
            return JsonResponse({
                'success': True,
                'message': f"Student {'activated' if student.active else 'deactivated'} successfully",
                'active': student.active
            })
            
        except Students.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Student not found'
            }, status=404)
        except Exception as e:
            print(f"Toggle Active Error: {str(e)}")  # Debug logging
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

@login_required
def student_toggle_approval(request, student_id):
    """Toggle student approval status"""
    if request.method == 'POST':
        try:
            student = Students.objects.get(id=student_id)
            student.status = not student.status
            
            # Set approve_date when approving
            if student.status:
                student.approve_date = timezone.now()
                student.active = True # Also set active status to True
                
                # Check for linked User
                user = student.user
                password = 'password123' # Default password for new approvals

                if not user:
                    # FALLBACK: Create user if it doesn't exist (Legacy compatibility)
                    if student.email:
                        existing_user = Users.objects.filter(email=student.email).first()
                        if existing_user:
                            user = existing_user
                            student.user = user
                        else:
                            # Create new user
                            user = Users()
                            user.name = f"{student.first_name} {student.last_name if student.last_name else ''}".strip()
                            user.email = student.email
                            user.username = student.email
                            user.created_at = timezone.now()
                            user.save()
                            
                            student_role = Roles.objects.filter(name__iexact='student').first()
                            if student_role:
                                RoleUsers.objects.create(user=user, role=student_role)
                            student.user = user
                
                # Activate User and Set Password
                if user:
                    user.is_active = True
                    user.set_password(password)
                    user.updated_at = timezone.now()
                    user.save()

                    # Send Approval Email with Credentials
                    try:
                        subject = 'Welcome to Trinity Seminary - Registration Approved'
                        message = f'''Dear {student.first_name},

Your registration has been approved. You can now login to the portal.

Login Details:
URL: https://trinityseminary.in/login (or your login URL)
Username: {user.email}
Password: {password}

IMPORTANT: Please change your password immediately after your first login.

Best regards,
Administration'''
                        from_email = 'contact@byteboot.in' # Request specific sender
                        recipient_list = [user.email]
                        send_mail(subject, message, from_email, recipient_list)
                    except Exception as e:
                        print(f"Email sending failed: {str(e)}")
                else:
                    print(f"Warning: No user linked or created for student {student.id}")

            else:
                # DISAPPROVE ACTION
                student.approve_date = None
                student.active = False
                
                # Deactivate User if linked
                if student.user:
                    student.user.is_active = False
                    student.user.save()
            
            student.updated_at = timezone.now()
            student.save()
            
            return JsonResponse({
                'success': True,
                'message': f"Student {'approved' if student.status else 'disapproved'} successfully",
                'status': student.status
            })
            
        except Students.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Student not found'
            }, status=404)
        except Exception as e:
            print(f"Toggle Approval Error: {str(e)}")  # Debug logging
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

#categories update delete and edit 

@login_required
def category_list(request):
    """List all categories with DataTables"""
    categories = Categories.objects.filter(
        deleted_at__isnull=True
    ).select_related('media', 'created_by').order_by('-id')
    
    return render(request, 'admin/categories/category-list.html', {
        'categories': categories
    })

@login_required
def category_create(request):
    """Create new category"""
    if request.method == 'POST':
        category_form = CategoryForm(request.POST)
        media_form = MediaLibraryForm(request.POST, request.FILES, prefix='media')
        
        if category_form.is_valid():
            category = category_form.save(commit=False)
            category.created_by = request.user
            category.updated_by = request.user
            category.created_at = timezone.now()
            
            # Handle new file upload
            if request.FILES.get('media-file'):
                if media_form.is_valid():
                    media = media_form.save(commit=False)
                    media.created_by = request.user
                    media.updated_by = request.user
                    
                    # Process the uploaded file
                    uploaded_file = request.FILES['media-file']
                    media.file_name = uploaded_file.name
                    media.file_path = uploaded_file
                    media.file_type = uploaded_file.name.split('.')[-1].lower()
                    media.file_size = f"{uploaded_file.size / 1024:.2f} KB"
                    
                    # Get dimensions for images
                    if media.file_type in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        try:
                            img = Image.open(uploaded_file)
                            media.dimensions = f"{img.width}x{img.height}"
                            media.media_type = 'image'
                        except:
                            media.media_type = 'file'
                    else:
                        media.media_type = 'file'
                    
                    # Set thumbnail path (same as file for now)
                    media.thumb_file_path = media.file_path.url
                    media.slider_file_path = media.file_path.url
                    
                    media.save()
                    category.media = media
            
            category.save()
            messages.success(request, 'Category created successfully!')
            return redirect('category_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        category_form = CategoryForm()
        media_form = MediaLibraryForm(prefix='media')
    
    return render(request, 'admin/categories/category_form.html', {
        'form': category_form,
        'media_form': media_form
    })

@login_required
def category_edit(request, category_id):
    """Edit existing category"""
    category = get_object_or_404(Categories, id=category_id, deleted_at__isnull=True)
    
    if request.method == 'POST':
        category_form = CategoryForm(request.POST, instance=category)
        media_form = MediaLibraryForm(request.POST, request.FILES, prefix='media')
        
        if category_form.is_valid():
            category = category_form.save(commit=False)
            category.updated_by = request.user
            
            # Handle new file upload
            if request.FILES.get('media-file'):
                if media_form.is_valid():
                    media = media_form.save(commit=False)
                    media.created_by = request.user
                    media.updated_by = request.user
                    
                    uploaded_file = request.FILES['media-file']
                    media.file_name = uploaded_file.name
                    media.file_path = uploaded_file
                    media.file_type = uploaded_file.name.split('.')[-1].lower()
                    media.file_size = f"{uploaded_file.size / 1024:.2f} KB"
                    
                    if media.file_type in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        try:
                            img = Image.open(uploaded_file)
                            media.dimensions = f"{img.width}x{img.height}"
                            media.media_type = 'image'
                        except:
                            media.media_type = 'file'
                    else:
                        media.media_type = 'file'
                    
                    media.thumb_file_path = media.file_path.url
                    media.slider_file_path = media.file_path.url
                    media.save()
                    category.media = media
            
            category.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('category_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        category_form = CategoryForm(instance=category)
        media_form = MediaLibraryForm(prefix='media')
    
    return render(request, 'admin/categories/category_form.html', {
        'form': category_form,
        'media_form': media_form
    })

@login_required
def category_view(request, category_id):
    """View category details"""
    category = get_object_or_404(
        Categories.objects.select_related('media', 'created_by', 'updated_by'),
        id=category_id,
        deleted_at__isnull=True
    )
    
    return render(request, 'admin/categories/category_view.html', {
        'category': category
    })

@login_required
def category_delete(request, category_id):
    """Soft delete category"""
    category = get_object_or_404(Categories, id=category_id, deleted_at__isnull=True)
    category.deleted_at = timezone.now()
    category.save()
    messages.success(request, 'Category deleted successfully!')
    return redirect('category_list')

# videos

@login_required
def video_list(request):
    """List all videos with DataTables"""
    videos = Videos.objects.filter(
        deleted_at__isnull=True
    ).select_related('media', 'youtube', 'categories', 'created_by').order_by('-id')
    
    return render(request, 'admin/videos/video-list.html', {
        'videos': videos
    })

@login_required
def video_create(request):
    """Create new video"""
    if request.method == 'POST':
        video_form = VideoForm(request.POST)
        media_form = MediaLibraryForm(request.POST, request.FILES, prefix='media')
        youtube_form = YoutubeVideoForm(request.POST, prefix='youtube')
        
        if video_form.is_valid():
            video = video_form.save(commit=False)
            video.created_by = request.user
            video.updated_by = request.user
            video.created_at = timezone.now()
            
            # Determine upload type: media file or YouTube
            upload_type = request.POST.get('upload_type', 'media')
            
            if upload_type == 'media' and request.FILES.get('media-file'):
                # Handle media file upload
                if media_form.is_valid():
                    media = media_form.save(commit=False)
                    media.created_by = request.user
                    media.updated_by = request.user
                    
                    uploaded_file = request.FILES['media-file']
                    media.file_name = uploaded_file.name
                    media.file_path = uploaded_file
                    media.file_type = uploaded_file.name.split('.')[-1].lower()
                    media.file_size = f"{uploaded_file.size / 1024:.2f} KB"
                    
                    # Check if it's a video file
                    video_extensions = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm']
                    if media.file_type in video_extensions:
                        media.media_type = 'video'
                    elif media.file_type in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        try:
                            img = Image.open(uploaded_file)
                            media.dimensions = f"{img.width}x{img.height}"
                            media.media_type = 'image'
                        except:
                            media.media_type = 'file'
                    else:
                        media.media_type = 'file'
                    
                    media.thumb_file_path = media.file_path.url
                    media.slider_file_path = media.file_path.url
                    
                    media.save()
                    video.media = media
                    video.youtube = None
            
            elif upload_type == 'youtube':
                # Handle YouTube video
                if youtube_form.is_valid():
                    youtube = youtube_form.save(commit=False)
                    youtube.created_by = request.user
                    youtube.updated_by = request.user
                    youtube.save()
                    video.youtube = youtube
                    video.media = None
            
            video.save()
            messages.success(request, 'Video created successfully!')
            return redirect('video_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        video_form = VideoForm()
        media_form = MediaLibraryForm(prefix='media')
        youtube_form = YoutubeVideoForm(prefix='youtube')
    
    # Get all categories for dropdown
    categories = Categories.objects.filter(deleted_at__isnull=True, status=True)
    
    return render(request, 'admin/videos/video_form.html', {
        'form': video_form,
        'media_form': media_form,
        'youtube_form': youtube_form,
        'categories': categories
    })

@login_required
def video_edit(request, video_id):
    """Edit existing video"""
    video = get_object_or_404(Videos, id=video_id, deleted_at__isnull=True)
    
    if request.method == 'POST':
        video_form = VideoForm(request.POST, instance=video)
        media_form = MediaLibraryForm(request.POST, request.FILES, prefix='media')
        youtube_form = YoutubeVideoForm(request.POST, prefix='youtube')
        
        if video_form.is_valid():
            video = video_form.save(commit=False)
            video.updated_by = request.user
            
            upload_type = request.POST.get('upload_type', 'media')
            
            if upload_type == 'media' and request.FILES.get('media-file'):
                if media_form.is_valid():
                    media = media_form.save(commit=False)
                    media.created_by = request.user
                    media.updated_by = request.user
                    
                    uploaded_file = request.FILES['media-file']
                    media.file_name = uploaded_file.name
                    media.file_path = uploaded_file
                    media.file_type = uploaded_file.name.split('.')[-1].lower()
                    media.file_size = f"{uploaded_file.size / 1024:.2f} KB"
                    
                    video_extensions = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm']
                    if media.file_type in video_extensions:
                        media.media_type = 'video'
                    elif media.file_type in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        try:
                            img = Image.open(uploaded_file)
                            media.dimensions = f"{img.width}x{img.height}"
                            media.media_type = 'image'
                        except:
                            media.media_type = 'file'
                    else:
                        media.media_type = 'file'
                    
                    media.thumb_file_path = media.file_path.url
                    media.slider_file_path = media.file_path.url
                    media.save()
                    video.media = media
                    video.youtube = None
            
            elif upload_type == 'youtube':
                if youtube_form.is_valid():
                    youtube = youtube_form.save(commit=False)
                    youtube.created_by = request.user
                    youtube.updated_by = request.user
                    youtube.save()
                    video.youtube = youtube
                    video.media = None
            
            video.save()
            messages.success(request, 'Video updated successfully!')
            return redirect('video_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        video_form = VideoForm(instance=video)
        media_form = MediaLibraryForm(prefix='media')
        youtube_form = YoutubeVideoForm(prefix='youtube')
    
    categories = Categories.objects.filter(deleted_at__isnull=True, status=True)
    
    return render(request, 'admin/videos/video_form.html', {
        'form': video_form,
        'media_form': media_form,
        'youtube_form': youtube_form,
        'categories': categories,
        'video': video
    })

@login_required
def video_view(request, video_id):
    """View video details"""
    video = get_object_or_404(
        Videos.objects.select_related('media', 'youtube', 'categories', 'created_by', 'updated_by'),
        id=video_id,
        deleted_at__isnull=True
    )
    
    return render(request, 'admin/videos/video_view.html', {
        'video': video
    })

@login_required
def video_delete(request, video_id):
    """Soft delete video"""
    video = get_object_or_404(Videos, id=video_id, deleted_at__isnull=True)
    video.deleted_at = timezone.now()
    video.save()
    messages.success(request, 'Video deleted successfully!')
    return redirect('video_list')

# roles and permissions 
@login_required
def roles(request):
    roles = Roles.objects.filter(
        deleted_at__isnull=True
    ).order_by('-id')

    context = {
        "roles":roles
    }
    return render(request,"admin/roles/roles.html",context)

@login_required
def roles_create(request):
    """Create new role"""
    # Fetch all permissions
    all_permissions = Permissions.objects.all().order_by('group_name', 'name')
    
    # Group permissions by group_name
    permissions_by_group = {}
    for perm in all_permissions:
        group = perm.group_name if perm.group_name else 'Other'
        if group not in permissions_by_group:
            permissions_by_group[group] = []
        permissions_by_group[group].append(perm)

    if request.method == 'POST':
        form = RolesForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    role = form.save(commit=False)
                    role.created_by = request.user
                    role.updated_by = request.user
                    role.created_at = timezone.now()
                    role.save()
                    
                    # Save selected permissions
                    selected_permissions = request.POST.getlist('permissions')
                    for perm_id in selected_permissions:
                        RoleHasPermissions.objects.create(
                            role=role,
                            permission_id=perm_id
                        )
                    
                    messages.success(request, 'Role created successfully!')
                    return redirect('roles')
            except Exception as e:
                messages.error(request, f'Error creating role: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RolesForm()
    
    return render(request, 'admin/roles/roles_form.html', {
        'form': form,
        'action': 'Create',
        'permissions_by_group': permissions_by_group
    })

@login_required
def roles_view(request, id):
    """View role details"""
    role = get_object_or_404(
        Roles,
        id=id,
        deleted_at__isnull=True)
    
    return render(request, 'admin/roles/roles_view.html', {
        'role': role
    })

from django.db import transaction

@login_required
def roles_edit(request, id):
    """Edit existing role and its permissions"""
    role = get_object_or_404(Roles, id=id, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = RolesForm(request.POST, instance=role)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save the role
                    role = form.save(commit=False)
                    role.updated_by = request.user
                    role.save()
                    
                    # Get selected permissions from POST data
                    selected_permissions = request.POST.getlist('permissions')
                    
                    # Delete existing permissions for this role
                    RoleHasPermissions.objects.filter(role=role).delete()
                    
                    # Create new permissions
                    for permission_id in selected_permissions:
                        RoleHasPermissions.objects.create(
                            role=role,
                            permission_id=permission_id
                        )
                    
                    messages.success(request, 'Role and permissions updated successfully!')
                    return redirect('roles')
            except Exception as e:
                messages.error(request, f'Error updating role: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RolesForm(instance=role)
    
    # Get all permissions grouped by group_name
    all_permissions = Permissions.objects.all().order_by('group_name', 'name')
    
    # Get current permissions for this role
    current_permissions = RoleHasPermissions.objects.filter(
        role=role
    ).values_list('permission_id', flat=True)
    
    # Group permissions by group_name
    permissions_by_group = {}
    for permission in all_permissions:
        if permission.group_name not in permissions_by_group:
            permissions_by_group[permission.group_name] = []
        permissions_by_group[permission.group_name].append(permission)
    
    return render(request, 'admin/roles/roles_form.html', {
        'form': form,
        'action': 'Update',
        'role': role,
        'permissions_by_group': permissions_by_group,
        'current_permissions': list(current_permissions)
    })

@login_required
def roles_delete(request, id):
    """Soft delete role"""
    role = get_object_or_404(Roles, id=id, deleted_at__isnull=True)
    role.deleted_at = timezone.now()
    role.save()
    messages.success(request, 'Role deleted successfully!')
    return redirect('roles')

# languages
@login_required
def languages(request):
    languages = Languages.objects.filter(
        deleted_at__isnull=True
    ).select_related('created_by').order_by('-id')
    return render(request,"admin/languages/languages_list.html",{"languages":languages})

@login_required
def language_create(request):
    form = LanguageForm()
    if request.method == "POST":
        form = LanguageForm(request.POST)
        if form.is_valid():
            language  = form.save(commit=False)
            language.created_by = request.user
            language.updated_by = request.user
            language.save()
        messages.success(request, "Language saved success...")
        return redirect("languages_list")
    context = {
        "form":form,
        'action': 'Create'
    }
    return render(request,"admin/languages/languages_form.html",context)

@login_required
def language_view(request, language_id):
    """View language details"""
    language = get_object_or_404(Languages, id=language_id, deleted_at__isnull=True)
    return render(request, 'admin/languages/language_view.html', {
        'language': language
    })

@login_required
def language_edit(request, language_id):
    """Edit existing language"""
    language = get_object_or_404(Languages, id=language_id, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = LanguageForm(request.POST, instance=language)
        if form.is_valid():
            form.save()
            messages.success(request, 'Language updated successfully!')
            return redirect('languages_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LanguageForm(instance=language)
    
    return render(request, 'admin/languages/languages_form.html', {
        'form': form,
        'action': 'Update'
    })

@login_required
def language_delete(request, language_id):
    """Soft delete language"""
    language = get_object_or_404(Languages, id=language_id, deleted_at__isnull=True)
    language.deleted_at = timezone.now()
    language.save()
    messages.success(request, 'Language deleted successfully!')
    return redirect('languages_list')

#subjects 

# subjects

@login_required
def subjects(request):
    """List all subjects with DataTables"""
    subjects_list = Subjects.objects.filter(
        deleted_at__isnull=True
    ).select_related('created_by').order_by('-id')
    
    return render(request, 'admin/subjects/subjects_list.html', {
        'subjects': subjects_list
    })

@login_required
def subjects_export(request):
    """Export subjects to Excel"""
    subjects_list = Subjects.objects.filter(
        deleted_at__isnull=True
    ).order_by('-id')
    
    return export_to_excel(
        queryset=subjects_list,
        filename="subjects_list",
        columns=['subject_name', 'subject_code', 'subject_type', 'credit_hours', 'status', 'created_at'],
        headers=['Subject Name', 'Code', 'Type', 'Credit Hours', 'Status', 'Created At']
    )

@login_required
def subjects_create(request):
    """Create new subject"""
    if request.method == 'POST':
        form = SubjectsForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.created_by = request.user
            subject.updated_by = request.user
            subject.created_at = timezone.now()
            subject.save()
            messages.success(request, 'Subject created successfully!')
            return redirect('subjects_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SubjectsForm()
    
    return render(request, 'admin/subjects/subjects_form.html', {
        'form': form,
        'action': 'Create'
    })

@login_required
def subjects_view(request, subjects_id):
    """View subject details"""
    subject = get_object_or_404(
        Subjects.objects.select_related('created_by', 'updated_by'),
        id=subjects_id,
        deleted_at__isnull=True
    )
    
    return render(request, 'admin/subjects/subjects_view.html', {
        'subject': subject
    })

@login_required
def subjects_edit(request, subjects_id):
    """Edit existing subject"""
    subject = get_object_or_404(Subjects, id=subjects_id, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = SubjectsForm(request.POST, instance=subject)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.updated_by = request.user
            subject.save()
            messages.success(request, 'Subject updated successfully!')
            return redirect('subjects_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SubjectsForm(instance=subject)
    
    return render(request, 'admin/subjects/subjects_form.html', {
        'form': form,
        'action': 'Update',
        'subject': subject
    })

@login_required
def subjects_delete(request, subjects_id):
    """Soft delete subject"""
    subject = get_object_or_404(Subjects, id=subjects_id, deleted_at__isnull=True)
    subject.deleted_at = timezone.now()
    subject.save()
    messages.success(request, 'Subject deleted successfully!')
    return redirect('subjects_list')

# branches 

@login_required
def branches_list(request):
    branches = Branches.objects.filter(
        deleted_at__isnull=True
    ).select_related('created_by').order_by('-id')
    return render(request, "admin/branches/branches_list.html",{"branches":branches})

@login_required
def branches_view(request, branch_id):
    """View branch details"""
    branch = get_object_or_404(
        Branches.objects.select_related('created_by', 'updated_by'),
        id=branch_id,
        deleted_at__isnull=True
    )
    
    return render(request, 'admin/branches/branches_view.html', {
        'branch': branch
    })

@login_required
def branches_create(request):
    """Create new branch"""
    if request.method == 'POST':
        form = BranchesForm(request.POST)
        if form.is_valid():
            branch = form.save(commit=False)
            branch.created_by = request.user
            branch.updated_by = request.user
            branch.created_at = timezone.now()
            branch.save()
            messages.success(request, 'Branch created successfully!')
            return redirect('branches_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BranchesForm()
    
    return render(request, 'admin/branches/branches_form.html', {
        'form': form,
        'action': 'Create'
    })

@login_required
def branches_edit(request, branch_id):
    """Edit existing branch"""
    branch = get_object_or_404(Branches, id=branch_id, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = BranchesForm(request.POST, instance=branch)
        if form.is_valid():
            branch = form.save(commit=False)
            branch.updated_by = request.user
            branch.save()
            messages.success(request, 'Branch updated successfully!')
            return redirect('branches_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BranchesForm(instance=branch)
    
    return render(request, 'admin/branches/branches_form.html', {
        'form': form,
        'action': 'Update',
        'branch': branch
    })

@login_required
def branches_delete(request, branch_id):
    """Soft delete branch"""
    branch = get_object_or_404(Branches, id=branch_id, deleted_at__isnull=True)
    branch.deleted_at = timezone.now()
    branch.save()
    messages.success(request, 'Branch deleted successfully!')
    return redirect('branches_list')

#contact requests 

@login_required
def contact_list(request):
    """
    Display all contact requests
    """
    contacts = Contacts.objects.filter(deleted_at__isnull=True).order_by('-created_at')
    
    context = {
        'contacts': contacts,
    }
    
    return render(request, 'admin/contacts/contact_requests.html', context)

@login_required
def contact_view(request, contact_id):
    """
    View contact request details
    """
    contact = get_object_or_404(Contacts, id=contact_id, deleted_at__isnull=True)
    
    context = {
        'contact': contact,
        'page_title': 'View Contact Request'
    }
    return render(request, 'admin/contacts/contact_view.html', context)

@login_required
def contact_delete(request, id):
    """
    Soft delete a contact request by setting deleted_at timestamp
    """
    contact = get_object_or_404(Contacts, id=id)
    
    # Soft delete - set deleted_at timestamp
    contact.deleted_at = timezone.now()
    contact.save()
    
    messages.success(request, 'Contact request deleted successfully!')
    return redirect('contact_list')

@login_required
def contact_permanent_delete(request, id):
    """
    Permanently delete a contact request from database
    """
    contact = get_object_or_404(Contacts, id=id)
    
    # Hard delete - remove from database
    contact.delete()
    
    messages.success(request, 'Contact request permanently deleted!')
    return redirect('contact_list')

#exams 
@login_required
def exams_list(request):
    """Display all exams"""
    exams = Exams.objects.filter(deleted_at__isnull=True).order_by('-created_at')
    context = {
        'exams': exams,
        'page_title': 'Exams Management'
    }
    return render(request, "admin/exams/exam_list.html", context)

@login_required
def exam_create(request):
    """Create new exam"""
    if request.method == 'POST':
        form = ExamsForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.updated_by = request.user
            exam.created_at = timezone.now()
            exam.save()
            messages.success(request, 'Exam created successfully!')
            return redirect('exams_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ExamsForm()
    
    context = {
        'form': form,
        'page_title': 'Create Exam',
        'action': 'Create'
    }
    return render(request, 'admin/exams/exam_form.html', context)

@login_required
def exam_view(request, exam_id):
    """View exam details"""
    exam = get_object_or_404(
        Exams.objects.select_related('created_by', 'updated_by'),
        id=exam_id,
        deleted_at__isnull=True
    )
    
    # Fetch questions
    descriptive_questions = exam.descriptive_questions.all().order_by('id')
    objective_questions = exam.objective_questions.all().order_by('id')

    context = {
        'exam': exam,
        'descriptive_questions': descriptive_questions,
        'objective_questions': objective_questions,
        'page_title': 'View Exam'
    }
    return render(request, 'admin/exams/exam_view.html', context)

@login_required
def exam_edit(request, exam_id):
    """Edit existing exam"""
    exam = get_object_or_404(Exams, id=exam_id, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = ExamsForm(request.POST, instance=exam)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.updated_by = request.user
            exam.save()
            messages.success(request, 'Exam updated successfully!')
            return redirect('exams_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ExamsForm(instance=exam)
    
    # Fetch questions
    descriptive_questions = exam.descriptive_questions.all().order_by('id')
    objective_questions = exam.objective_questions.all().order_by('id')

    context = {
        'form': form,
        'exam': exam,
        'descriptive_questions': descriptive_questions,
        'objective_questions': objective_questions,
        'descriptive_form': DescriptiveQuestionsForm(),
        'objective_form': ObjectiveQuestionsForm(),
        'page_title': 'Edit Exam',
        'action': 'Update'
    }
    return render(request, 'admin/exams/exam_form.html', context)

@login_required
def exam_delete(request, exam_id):
    """Soft delete exam"""
    exam = get_object_or_404(Exams, id=exam_id, deleted_at__isnull=True)
    exam.deleted_at = timezone.now()
    exam.save()
    messages.success(request, 'Exam deleted successfully!')
    return redirect('exams_list')

#staffs 

# staffs

@login_required
def staffs_list(request):
    """List all staffs with DataTables"""
    staffs = Staffs.objects.filter(
        deleted_at__isnull=True
    ).select_related('created_by').order_by('-id')
    
    return render(request, 'admin/staffs/staffs_list.html', {
        'staffs': staffs
    })

@login_required
def staff_create(request):
    """Create new staff with user account and send credentials via email"""
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            # Check if email already exists
            email = form.cleaned_data.get('email')
            if Users.objects.filter(email=email).exists():
                messages.error(request, f'A user with email {email} already exists!')
                return render(request, 'admin/staffs/staffs_form.html', {
                    'form': form,
                    'action': 'Create'
                })
            
            try:
                with transaction.atomic():
                    # Create User account
                    default_password = 'teacher123'
                    staff_name = form.cleaned_data.get('staff_name')
                    
                    # Generate username from email (before @ symbol)
                    username = email.split('@')[0]
                    
                    # Check if username exists, if so, append a number
                    base_username = username
                    counter = 1
                    while Users.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                    
                    # Create the user
                    user = Users.objects.create_user(
                        email=email,
                        username=username,
                        name=staff_name,
                        password=default_password,
                        is_active=True,
                        created_at=timezone.now(),
                        updated_at=timezone.now()
                    )
                    
                    # Assign Teacher role
                    try:
                        teacher_role = Roles.objects.get(name='Teacher')
                        RoleUsers.objects.create(
                            user=user,
                            role=teacher_role
                        )
                    except Roles.DoesNotExist:
                        messages.warning(request, 'Teacher role not found. Please create it first.')
                        raise Exception('Teacher role does not exist')
                    
                    # Create Staff record
                    staff = form.save(commit=False)
                    staff.user = user
                    staff.created_by = request.user
                    staff.updated_by = request.user
                    staff.created_at = timezone.now()
                    staff.updated_at = timezone.now()
                    # staff_id will be auto-generated in the model's save method
                    staff.save()
                    
                    # Send email with credentials
                    send_staff_credentials_email(
                        staff_email=email,
                        staff_name=staff_name,
                        staff_id=staff.staff_id,
                        username=username,
                        password=default_password
                    )
                    
                    messages.success(
                        request, 
                        f'Staff created successfully! Staff ID: {staff.staff_id}. Credentials sent to {email}.'
                    )
                    return redirect('staffs_list')
                    
            except Exception as e:
                messages.error(request, f'Error creating staff: {str(e)}')
                return render(request, 'admin/staffs/staffs_form.html', {
                    'form': form,
                    'action': 'Create'
                })
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StaffForm()
    
    return render(request, 'admin/staffs/staffs_form.html', {
        'form': form,
        'action': 'Create'
    })

def send_staff_credentials_email(staff_email, staff_name, staff_id, username, password):
    """Send email with staff credentials"""
    subject = 'Welcome to TTSTECH - Your Staff Account Credentials'
    
    message = f"""
            Dear {staff_name},

            Welcome to TTSTECH! Your staff account has been successfully created.

            Here are your login credentials:

            Staff ID: {staff_id}
            Username: {username}
            Email: {staff_email}
            Password: {password}

            Please login to the system using your email and password. We recommend changing your password after your first login for security purposes.

            Login URL: {settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'Your website URL'}

            If you have any questions or need assistance, please contact the administration.

            Best regards,
            TTSTECH Administration Team
                """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[staff_email],
            fail_silently=False,
        )
    except Exception as e:
        # Log the error but don't fail the staff creation
        print(f"Error sending email: {str(e)}")
        # You might want to use proper logging here
        # import logging
        # logger = logging.getLogger(__name__)
        # logger.error(f"Failed to send credentials email to {staff_email}: {str(e)}")

@login_required
def staff_view(request, staff_id):
    """View staff details"""
    staff = get_object_or_404(
        Staffs.objects.select_related('created_by', 'updated_by'),
        id=staff_id,
        deleted_at__isnull=True
    )
    
    return render(request, 'admin/staffs/staffs_view.html', {
        'staff': staff
    })

@login_required
def staff_edit(request, staff_id):
    """Edit existing staff"""
    staff = get_object_or_404(Staffs, id=staff_id, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = StaffForm(request.POST, instance=staff)
        if form.is_valid():
            staff = form.save(commit=False)
            staff.updated_by = request.user
            staff.save()
            messages.success(request, 'Staff updated successfully!')
            return redirect('staffs_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StaffForm(instance=staff)
    
    return render(request, 'admin/staffs/staffs_form.html', {
        'form': form,
        'action': 'Update',
        'staff': staff
    })

@login_required
def staff_delete(request, staff_id):
    """Soft delete staff"""
    staff = get_object_or_404(Staffs, id=staff_id, deleted_at__isnull=True)
    staff.deleted_at = timezone.now()
    staff.save()
    messages.success(request, 'Staff deleted successfully!')
    return redirect('staffs_list')

# assignments 

@login_required
def assignments_list(request):
    """List all assignments with DataTables"""
    assignments = Assignments.objects.filter(
        deleted_at__isnull=True
    ).select_related('created_by').order_by('-id')
    
    return render(request, 'admin/assignments/assignments_list.html', {
        'assignments': assignments
    })

@login_required
def assignment_create(request):
    """Create new assignment"""
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            assignment.updated_by = request.user
            assignment.created_at = timezone.now()
            assignment.save()
            messages.success(request, 'Assignment created successfully!')
            return redirect('assignments_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AssignmentForm()
    
    return render(request, 'admin/assignments/assignment_form.html', {
        'form': form,
        'action': 'Create'
    })

@login_required
def assignment_view(request, assignment_id):
    """View assignment details"""
    assignment = get_object_or_404(
        Assignments.objects.select_related('created_by', 'updated_by'),
        id=assignment_id,
        deleted_at__isnull=True
    )
    
    return render(request, 'admin/assignments/assignment_view.html', {
        'assignment': assignment
    })

@login_required
def assignment_edit(request, assignment_id):
    """Edit existing assignment"""
    assignment = get_object_or_404(Assignments, id=assignment_id, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.updated_by = request.user
            assignment.save()
            messages.success(request, 'Assignment updated successfully!')
            return redirect('assignments_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AssignmentForm(instance=assignment)
    
    return render(request, 'admin/assignments/assignment_form.html', {
        'form': form,
        'action': 'Update',
        'assignment': assignment
    })

@login_required
def assignment_delete(request, assignment_id):
    """Soft delete assignment"""
    assignment = get_object_or_404(Assignments, id=assignment_id, deleted_at__isnull=True)
    assignment.deleted_at = timezone.now()
    assignment.save()
    messages.success(request, 'Assignment deleted successfully!')
    return redirect('assignments_list')

# book references

@login_required
def reference_list(request):
    """List all book references with DataTables"""
    references = BookReferences.objects.filter(
        deleted_at__isnull=True
    ).select_related('created_by').order_by('-id')
    
    return render(request, 'admin/references/references_list.html', {
        'book_references': references
    })

from django.utils.text import slugify
from django.http import JsonResponse

@login_required
def reference_create(request):
    """Create new book reference"""
    if request.method == 'POST':
        form = BookReferenceForm(request.POST, request.FILES)
        if form.is_valid():
            reference = form.save(commit=False)
            
            # Auto-generate code from title
            reference.code = slugify(form.cleaned_data['title'])
            
            # Set user and timestamps
            reference.created_by = request.user
            reference.updated_by = request.user
            reference.created_at = timezone.now()
            reference.updated_at = timezone.now()
            
            # Handle PDF upload based on format
            if reference.format == 'PDF':
                new_file = request.FILES.get('new_pdf_file')
                selected_media_id = request.POST.get('selected_media_id')
                
                if new_file:
                    # Upload new PDF to MediaLibrary
                    media = MediaLibrary()
                    media.file_name = new_file.name
                    media.file_path = new_file
                    media.file_type = new_file.content_type
                    media.file_size = str(new_file.size)
                    media.media_type = 'document'
                    media.title = form.cleaned_data['title']
                    media.created_by = request.user
                    media.updated_by = request.user
                    media.thumb_file_path = 'uploads/thumbs/pdf-thumb.png'
                    media.slider_file_path = ''
                    media.save()
                    
                    reference.reference_file = media
                    
                elif selected_media_id:
                    # Link existing media
                    reference.reference_file_id = int(selected_media_id)
                
                # Clear reference_note for PDF format
                reference.reference_note = None
                
            elif reference.format == 'note':
                # Clear reference_file for note format
                reference.reference_file = None
            
            reference.save()
            messages.success(request, 'Reference created successfully!')
            return redirect('reference_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookReferenceForm()
    
    return render(request, 'admin/references/reference_form.html', {
        'form': form,
        'action': 'Create'
    })

@login_required
def reference_edit(request, reference_id):
    """Edit existing reference"""
    reference = get_object_or_404(
        BookReferences, 
        id=reference_id, 
        deleted_at__isnull=True
    )
    
    if request.method == 'POST':
        form = BookReferenceForm(request.POST, request.FILES, instance=reference)
        if form.is_valid():
            reference = form.save(commit=False)
            
            # Auto-generate code from title
            reference.code = slugify(form.cleaned_data['title'])
            
            # Update user and timestamp
            reference.updated_by = request.user
            reference.updated_at = timezone.now()
            
            # Handle PDF upload based on format
            if reference.format == 'PDF':
                new_file = request.FILES.get('new_pdf_file')
                selected_media_id = request.POST.get('selected_media_id')
                
                if new_file:
                    # Upload new PDF to MediaLibrary
                    media = MediaLibrary()
                    media.file_name = new_file.name
                    media.file_path = new_file
                    media.file_type = new_file.content_type
                    media.file_size = str(new_file.size)
                    media.media_type = 'document'
                    media.title = form.cleaned_data['title']
                    media.created_by = request.user
                    media.updated_by = request.user
                    media.thumb_file_path = 'uploads/thumbs/pdf-thumb.png'
                    media.slider_file_path = ''
                    media.save()
                    
                    reference.reference_file = media
                    
                elif selected_media_id:
                    # Link existing media
                    reference.reference_file_id = int(selected_media_id)
                
                # Clear reference_note for PDF format
                reference.reference_note = None
                
            elif reference.format == 'note':
                # Clear reference_file for note format
                reference.reference_file = None
            
            reference.save()
            messages.success(request, 'Reference updated successfully!')
            return redirect('reference_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookReferenceForm(instance=reference)
    
    return render(request, 'admin/references/reference_form.html', {
        'form': form,
        'action': 'Update',
        'reference': reference
    })

@login_required
def reference_view(request, reference_id):
    """View reference details"""
    reference = get_object_or_404(
        BookReferences.objects.select_related(
            'created_by', 
            'updated_by', 
            'reference_file',
            'subject'
        ),
        id=reference_id,
        deleted_at__isnull=True
    )
    
    return render(request, 'admin/references/reference_view.html', {
        'reference': reference
    })

def get_media_library_pdfs(request):
    """AJAX endpoint to get all PDFs from media library"""
    pdfs = MediaLibrary.objects.filter(
        file_type='application/pdf',
        deleted_at__isnull=True
    ).values('id', 'file_name', 'title', 'file_size', 'created_at')
    
    return JsonResponse({
        'pdfs': list(pdfs)
    })

@login_required
def reference_delete(request, reference_id):
    """Soft delete reference"""
    reference = get_object_or_404(BookReferences, id=reference_id, deleted_at__isnull=True)
    reference.deleted_at = timezone.now()
    reference.save()
    messages.success(request, 'Reference deleted successfully!')
    return redirect('reference_list')

# supports 

@login_required
def support_list(request):
    """List all support tickets"""
    support = Support.objects.filter(
        deleted_at__isnull=True
    ).select_related('created_by').order_by('-id')
    
    return render(request, 'admin/supports/support_list.html', {
        'support': support
    })

@login_required
def support_view(request, support_id):
    """View support ticket details"""
    support = get_object_or_404(Support, id=support_id)
    replies = support.replies.filter(deleted_at__isnull=True).order_by('created_at')
    
    if request.method == 'POST':
        doubt_answer = request.POST.get('doubt_answer')
        if doubt_answer:
            SupportReplies.objects.create(
                support=support,
                doubt_answer=doubt_answer,
                created_by=request.user,
                updated_by=request.user
            )
            
            # Update status to in_progress if it's currently open or pending
            if support.status in ['open', 'pending']:
                support.status = 'in_progress'
                support.save()
                
            messages.success(request, 'Reply added successfully!')
            return redirect('support_view', support_id=support_id)
    
    context = {
        'support': support,
        'replies': replies,
    }
    return render(request, 'admin/supports/support_view.html', context)

@login_required
def support_reply_delete(request, pk):
    reply = get_object_or_404(SupportReplies, id=pk)
    support_id = reply.support.id
    
    if request.method == 'POST':
        from django.utils import timezone
        reply.deleted_at = timezone.now()
        reply.save()
        messages.success(request, 'Reply deleted successfully!')
    
    return redirect('support_view', support_id=support_id)

@login_required
def support_delete(request, support_id):
    """Soft delete support ticket"""
    try:
        support = get_object_or_404(Support, id=support_id, deleted_at__isnull=True)
        support.deleted_at = timezone.now()
        support.save()
        
        messages.success(request, 'Support ticket deleted successfully!')
        return redirect('support_list')
    except Exception as e:
        messages.error(request, f'Error deleting support ticket: {str(e)}')
        return redirect('support_list')
    
#uploads

@login_required
def uploads_list(request):
    uploads = Uploads.objects.select_related(
        "subject", "video_id", "youtube", "media", "created_by"
    ).order_by("-id")

    context = {"uploads": uploads}
    return render(request, "admin/uploads/uploads_list.html", context)

@login_required
def uploads_create(request):
    if request.method == "POST":
        form = UploadForm(request.POST)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.created_by = request.user
            upload.updated_by = request.user
            upload.save()
            messages.success(request, "Upload created successfully.")
            return redirect("uploads_list")
        else:
             messages.error(request, "Please correct the errors below.")
    else:
        form = UploadForm()

    return render(request, "admin/uploads/uploads_form.html", {
        "form": form,
        "title": "Add Upload",
    })

@login_required
def uploads_edit(request, id):
    upload = get_object_or_404(Uploads, id=id)

    if request.method == "POST":
        form = UploadForm(request.POST, instance=upload)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.updated_by = request.user
            upload.save()
            messages.success(request, "Upload updated successfully.")
            return redirect("uploads_list")
    else:
        form = UploadForm(instance=upload)

    return render(request, "admin/uploads/uploads_form.html", {
        "form": form,
        "title": "Edit Upload",
        "upload": upload,
    })

@login_required
def uploads_view(request, id):
    upload = get_object_or_404(Uploads, id=id)
    return render(request, "admin/uploads/uploads_view.html", {
        "upload": upload
    })

@login_required
def uploads_delete(request, id):
    upload = get_object_or_404(Uploads, id=id)
    upload.delete()
    messages.success(request, "Upload deleted successfully.")
    return redirect("uploads_list")

# payments 

@login_required
def payments_list(request):
    payments = Payments.objects.filter(deleted_at__isnull=True).order_by("-id")
    return render(request, "admin/payments/payments_list.html", {"payments": payments})

@login_required
def payments_view(request, id):
    payment = get_object_or_404(Payments, id=id, deleted_at__isnull=True)
    # determine a sensible "paid date" — we use updated_at if the record is marked paid, otherwise -
    paid_date = payment.updated_at if payment.is_paid else None
    return render(request, "admin/payments/payments_view.html", {
        "payment": payment,
        "paid_date": paid_date
    })

@login_required
def payments_delete(request, id):
    payment = get_object_or_404(Payments, id=id, deleted_at__isnull=True)
    # soft-delete: set deleted_at so other parts of app that check deleted_at stay consistent
    payment.deleted_at = timezone.now()
    payment.save()
    messages.success(request, "Payment deleted successfully.")
    return redirect("payments_list")

@login_required
def users_list(request):
    # Queryset (filter as needed)
    qs = Users.objects.filter(deleted_at__isnull=True).order_by("-id")

    # get page size from query param (with sensible defaults)
    try:
        per_page = int(request.GET.get("per_page", 25))
    except ValueError:
        per_page = 25
    if per_page <= 0:
        per_page = 25

    paginator = Paginator(qs, per_page)

    page = request.GET.get("page", 1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # optional: preserve GET params for pagination links
    get_params = request.GET.copy()
    if "page" in get_params:
        del get_params["page"]
    querystring = get_params.urlencode()

    context = {
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "per_page": per_page,
        "querystring": querystring,
    }
    return render(request, "admin/users/users_list.html", context)

@login_required
def users_create(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            role_id = request.POST.get('role')

            if not all([name, username, email, password, role_id]):
                messages.error(request, 'All fields are required.')
                return redirect('users_create')

            if Users.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return redirect('users_create')

            if Users.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('users_create')

            with transaction.atomic():
                user = Users.objects.create_user(
                    email=email,
                    username=username,
                    password=password,
                    name=name,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                    is_active=True
                )
                
                role = Roles.objects.get(id=role_id)
                RoleUsers.objects.create(user=user, role=role)

            messages.success(request, 'User created successfully.')
            return redirect('users_list')

        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
            return redirect('users_create')

    roles = Roles.objects.filter(deleted_at__isnull=True)
    return render(request, "admin/users/users_create.html", {'roles': roles})

@login_required
def users_view(request, id):
    user = get_object_or_404(Users, id=id, deleted_at__isnull=True)
    return render(request, "admin/users/users_view.html", {
        "user": user,
        "now": timezone.now(),
    })

@login_required
def users_delete(request, id):
    user = get_object_or_404(Users, id=id, deleted_at__isnull=True)
    user.deleted_at = timezone.now()  # Soft delete
    user.is_active = False
    user.save()
    messages.success(request, "User deleted successfully.")
    return redirect("users_list")

# Church Login Codes

@login_required
def church_code_list(request):
    """List all church login codes"""
    codes = ChurchLoginCodeSettings.objects.filter(deleted_at__isnull=True).order_by('-id')
    return render(request, 'admin/church_codes/church_code_list.html', {
        'codes': codes,
        'page_title': 'Church Login Codes'
    })

@login_required
def church_code_create(request):
    """Create new church login code"""
    if request.method == 'POST':
        form = ChurchLoginCodeSettingsForm(request.POST)
        if form.is_valid():
            code = form.save(commit=False)
            code.created_at = timezone.now()
            # code.created_by = request.user # If model has this field
            # code.updated_by = request.user
            code.save()
            messages.success(request, 'Church Login Code created successfully!')
            return redirect('church_code_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ChurchLoginCodeSettingsForm()
    
    return render(request, 'admin/church_codes/church_code_form.html', {
        'form': form,
        'page_title': 'Create Church Login Code',
        'action': 'Create'
    })

@login_required
def church_code_edit(request, code_id):
    """Edit church login code"""
    code = get_object_or_404(ChurchLoginCodeSettings, id=code_id, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = ChurchLoginCodeSettingsForm(request.POST, instance=code)
        if form.is_valid():
            code = form.save(commit=False)
            code.updated_at = timezone.now()
            # code.updated_by = request.user
            code.save()
            messages.success(request, 'Church Login Code updated successfully!')
            return redirect('church_code_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ChurchLoginCodeSettingsForm(instance=code)
    
    return render(request, 'admin/church_codes/church_code_form.html', {
        'form': form,
        'page_title': 'Edit Church Login Code',
        'code': code,
        'action': 'Update'
    })

@login_required
def church_code_delete(request, code_id):
    """Soft delete church login code"""
    code = get_object_or_404(ChurchLoginCodeSettings, id=code_id, deleted_at__isnull=True)
    code.deleted_at = timezone.now()
    code.save()
    messages.success(request, 'Church Login Code deleted successfully!')
    return redirect('church_code_list')

# Church Admins

@login_required
def church_admin_list(request):
    """List all church admins"""
    admins = ChurchAdmins.objects.filter(deleted_at__isnull=True).order_by('-id')
    return render(request, 'admin/church_admins/church_admin_list.html', {
        'admins': admins,
        'page_title': 'Church Admins'
    })

@login_required
def church_admin_create(request):
    """Create new church admin"""
    if request.method == 'POST':
        form = ChurchAdminForm(request.POST)
        if form.is_valid():
            admin = form.save(commit=False)
            admin.created_at = timezone.now()
            
            # Auto-generate code
            # Format: CH-TIMESTAMP-RANDOM
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            admin.code = f"CH-{timestamp}"
            
            admin.save()
            messages.success(request, 'Church Admin created successfully!')
            return redirect('church_admin_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ChurchAdminForm()
    
    return render(request, 'admin/church_admins/church_admin_form.html', {
        'form': form,
        'page_title': 'Create Church Admin',
        'action': 'Create'
    })

@login_required
def church_admin_delete(request, admin_id):
    """Soft delete church admin"""
    admin = get_object_or_404(ChurchAdmins, id=admin_id, deleted_at__isnull=True)
    admin.deleted_at = timezone.now()
    admin.save()
    messages.success(request, 'Church Admin deleted successfully!')
    return redirect('church_admin_list')

# ============= CHURCH CODES USAGE VIEWS =============

@login_required

def church_codes_usage_list(request):

    """List of Church Admins using codes"""

    per_page = int(request.GET.get('per_page', 10))

    page_number = request.GET.get('page')

    # Filter for active records

    admins = ChurchAdmins.objects.filter(deleted_at__isnull=True).select_related(

        'church_code', 

        'church_code__branches',

        'student'

    ).order_by('-created_at')

    paginator = Paginator(admins, per_page)

    page_obj = paginator.get_page(page_number)

    context = {

        'page_obj': page_obj,

        'per_page': per_page,

        'page_title': 'Church Admins'

    }

    return render(request, "admin/church_codes/list.html", context)

@login_required
def church_codes_usage_view(request, admin_id):
    """Detailed view for a single Church Admin"""
    
    admin = get_object_or_404(
        ChurchAdmins.objects.select_related('church_code', 'church_code__branches', 'student'), 
        id=admin_id, 
        deleted_at__isnull=True
    )
    
    # Attempt to fetch the associated user login info
    user_info = Users.objects.filter(church_admin=admin, deleted_at__isnull=True).first()
    
    context = {
        'admin': admin,
        'user_info': user_info,
        'page_title': 'View Church Admin'
    }
    
    return render(request, "admin/church_codes/view.html", context)


@login_required

def church_codes_usage_delete(request, admin_id):

    """Soft delete church admin usage"""

    try:

        admin = get_object_or_404(ChurchAdmins, id=admin_id, deleted_at__isnull=True)

        admin.deleted_at = timezone.now()

        admin.save()

        messages.success(request, "Church Admin deleted successfully.")

    except Exception as e:

        messages.error(request, f"Error deleting Church Admin: {str(e)}")

    return redirect('church_codes_usage_list')

#@login_required

def application_list_view(request):
    """Render application management page (Applicants)"""
    context = {
        'countries': Countries.objects.all().order_by('name'),
        'languages': Languages.objects.filter(status=True).order_by('language_name'),
        'courses': Courses.objects.filter(status=1).order_by('course_name'),
    }
    return render(request, 'admin/applications/list.html', context)

# Student Books Refined Workflow
@login_required
def student_books_list(request):
    """Render student books management page"""
    courses = Courses.objects.filter(status=1).order_by('course_name')
    context = {
        'page_title': 'Student Books Management',
        'courses': courses,
    }
    return render(request, 'admin/students/books_list.html', context)

@login_required
def student_books_datatable(request):
    """DataTables server-side processing for student books"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        order_column_index = int(request.GET.get('order[0][column]', 0))
        order_direction = request.GET.get('order[0][dir]', 'desc')
        
        books_query = StudentsBooks.objects.filter(deleted_at__isnull=True).select_related('student', 'book') # Removed updated_by to prevent INNER JOIN exclusion

        # Status Filter
        status_filter = request.GET.get('status', '')
        if status_filter == 'pending':
            books_query = books_query.filter(is_approved=False)
        elif status_filter == 'approved':
            books_query = books_query.filter(is_approved=True)

        if search_value:
            books_query = books_query.filter(
                Q(student__first_name__icontains=search_value) |
                Q(student__last_name__icontains=search_value) |
                Q(book__title__icontains=search_value) | 
                Q(student__student_id__icontains=search_value)
            )
        
        if order_column_index == 0:
            order_col = 'id'
        elif order_column_index == 1:
            order_col = 'student__first_name'
        elif order_column_index == 2:
            order_col = 'book__title'
        elif order_column_index == 3:
            order_col = 'updated_by__username'
        else:
            order_col = '-created_at'

        if order_direction == 'desc' and not order_col.startswith('-'):
            order_col = '-' + order_col
        
        total_records = StudentsBooks.objects.filter(deleted_at__isnull=True).count()
        filtered_records = books_query.count()
        data_list = books_query.order_by(order_col)[start:start+length]
        
        data = []
        for item in data_list:
            student_name = f"{item.student.first_name} {item.student.last_name or ''}"
            if item.student.student_id:
                 student_name += f" ({item.student.student_id})"
            
            # Safely get updated_by
            updated_by_name = '-'
            if item.updated_by_id:
                try:
                    updated_by_name = item.updated_by.username
                except:
                    pass
                 
            updated_date = item.updated_at.strftime('%Y-%m-%d') if item.updated_at else ''
            updated_info = f"{updated_by_name}<br><small>{updated_date}</small>"
            
            # Status Badge
            if item.is_approved:
                status_badge = '<span class="badge bg-success">Approved</span>'
            else:
                status_badge = '<span class="badge bg-warning text-dark">Pending</span>'

            actions = '<div class="action-buttons">'
            
            # Approve Button (only if pending)
            if not item.is_approved:
                actions += f'''
                    <button class="btn-action btn-success" onclick="toggleApproval({item.id})" title="Approve">
                        <i class="fas fa-check"></i>
                    </button>
                '''
            else:
                actions += f'''
                    <button class="btn-action btn-warning" onclick="toggleApproval({item.id})" title="Revoke Approval">
                        <i class="fas fa-times"></i>
                    </button>
                '''

            actions += f'''
                    <button class="btn-action btn-delete" onclick="deleteStudentBook({item.id})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            '''
            
            data.append({
                'id': item.id,
                'student_name': student_name,
                'book_title': item.book.title if item.book else 'Unknown Book',
                'status': status_badge,
                'updated_by': updated_info,
                'actions': actions
            })
            
        return JsonResponse({'draw': draw, 'recordsTotal': total_records, 'recordsFiltered': filtered_records, 'data': data})
        
    except Exception as e:
        with open('debug_tables_log.txt', 'a') as f:
            f.write(f"Error: {str(e)}\n")
        print(f"DataTables Error: {str(e)}")
        return JsonResponse({'error': str(e), 'data': []})

@login_required
def ajax_get_students_by_course(request, course_id):
    """Fetch students for a specific course"""
    students = Students.objects.filter(course_applied_id=course_id, active=1, status=1).values('id', 'first_name', 'last_name', 'student_id')
    return JsonResponse({'success': True, 'students': list(students)})


@login_required
def ajax_get_books_by_subject(request, subject_id):
    """Fetch books for a specific subject"""
    books = BookReferences.objects.filter(subject_id=subject_id, deleted_at__isnull=True).values('id', 'title', 'auther_name')
    return JsonResponse({'success': True, 'books': list(books)})

@login_required
@require_POST
def student_books_bulk_assign(request):
    """Bulk assign books to a student"""
    try:
        student_id = request.POST.get('student')
        book_ids = request.POST.getlist('books[]')
        
        if not student_id or not book_ids:
            return JsonResponse({'success': False, 'message': 'Student and Books are required'}, status=400)
            
        student = get_object_or_404(Students, id=student_id)
        
        created_count = 0
        skipped_count = 0
        
        with transaction.atomic():
            for book_id in book_ids:
                if StudentsBooks.objects.filter(student=student, book_id=book_id, deleted_at__isnull=True).exists():
                    skipped_count += 1
                    continue
                
                StudentsBooks.objects.create(
                    student=student,
                    book_id=book_id,
                    created_by=request.user,
                    updated_by=request.user,
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
                created_count += 1
                
        message = f'Successfully assigned {created_count} books.'
        if skipped_count > 0:
            message += f' ({skipped_count} were already assigned and skipped).'
            
        return JsonResponse({'success': True, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
@require_POST
def student_books_delete(request, id):
    """Soft delete student book assignment"""
    try:
        sb = get_object_or_404(StudentsBooks, id=id)
        sb.deleted_at = timezone.now()
        sb.updated_by = request.user
        sb.save()
        return JsonResponse({'success': True, 'message': 'Assignment deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
def student_books_toggle_approval(request, id):
    try:
        book = StudentsBooks.objects.get(id=id)
        book.is_approved = not book.is_approved
        book.save()
        return JsonResponse({'success': True, 'message': 'Status updated successfully'})
    except StudentsBooks.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Book assignment not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# Student Subjects Workflow
@login_required
def student_subjects_list(request):
    """Render student subjects management page"""
    courses = Courses.objects.filter(status=1).order_by('course_name')
    context = {
        'page_title': 'Student Subjects Management',
        'courses': courses,
    }
    return render(request, 'admin/students/subjects_list.html', context)

@login_required
def student_subjects_datatable(request):
    """DataTables server-side processing for student subjects"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'desc')
    
    query = StudentsSubjects.objects.filter(deleted_at__isnull=True).select_related('student', 'subject', 'updated_by')

    # Status Filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'pending':
        query = query.filter(is_approved=False)
    elif status_filter == 'approved':
        query = query.filter(is_approved=True)

    if search_value:
        query = query.filter(
            Q(student__first_name__icontains=search_value) |
            Q(student__last_name__icontains=search_value) |
            Q(subject__subject_name__icontains=search_value) | 
            Q(student__student_id__icontains=search_value)
        )
    
    # Adjust column ordering index because of S.No column at 0
    # 0: S.No (not sortable usually, or map to id)
    # 1: Student Name
    # 2: Subject Name
    # 3: Status
    # 4: Updated By
    
    if order_column_index == 1:
        order_col = 'student__first_name'
    elif order_column_index == 2:
        order_col = 'subject__subject_name'
    elif order_column_index == 3:
        order_col = 'is_approved'
    elif order_column_index == 4:
        order_col = 'updated_by__username'
    else:
        order_col = '-created_at'

    if order_direction == 'desc' and not order_col.startswith('-'):
        order_col = '-' + order_col
    
    total_records = StudentsSubjects.objects.filter(deleted_at__isnull=True).count()
    filtered_records = query.count()
    data_list = query.order_by(order_col)[start:start+length]
    
    data = []
    for i, item in enumerate(data_list):
        student_name = f"{item.student.first_name} {item.student.last_name or ''}"
        if item.student.student_id:
             student_name += f" ({item.student.student_id})"
             
        updated_by = item.updated_by.username if item.updated_by else '-'
        updated_date = item.updated_at.strftime('%Y-%m-%d') if item.updated_at else ''
        updated_info = f"{updated_by}<br><small>{updated_date}</small>"
        
        # Status Badge
        if item.is_approved:
            status_badge = '<span class="badge bg-success">Approved</span>'
        else:
            status_badge = '<span class="badge bg-warning text-dark">Pending</span>'

        # Actions
        actions = '<div class="action-buttons">'
        
        # Approve Button (only if pending)
        if not item.is_approved:
            actions += f'''
                <button class="btn-action btn-success" onclick="toggleApproval({item.id})" title="Approve">
                    <i class="fas fa-check"></i>
                </button>
            '''
        else:
             # Optionally allow un-approve? User said "if approved show approved other wise pending and an option to approve"
             # So maybe only need button for pending. But ability to toggle back is usually good.
             # I'll stick to toggle logic but icon might differ. For now, let's allow toggle back to pending with a different icon or just keep it simple.
             # User specifically asked: "if approved show approved other wise pending and an option to approve".
             # So maybe once approved, just show "Approved" status, or maybe allow Unapprove?
             # I will implement toggle.
             actions += f'''
                <button class="btn-action btn-warning" onclick="toggleApproval({item.id})" title="Revoke Approval">
                    <i class="fas fa-times"></i>
                </button>
            '''

        actions += f'''
                <button class="btn-action btn-delete" onclick="deleteStudentSubject({item.id})" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        '''
        
        data.append({
            'sno': start + i + 1,
            'student_name': student_name,
            'subject_name': item.subject.subject_name if item.subject else 'Unknown Subject',
            'status': status_badge,
            'updated_by': updated_info,
            'actions': actions
        })
        
    return JsonResponse({'draw': draw, 'recordsTotal': total_records, 'recordsFiltered': filtered_records, 'data': data})

@login_required
def student_subjects_toggle_approval(request, id):
    try:
        subject = StudentsSubjects.objects.get(id=id)
        subject.is_approved = not subject.is_approved
        subject.save()
        return JsonResponse({'success': True, 'message': 'Status updated successfully'})
    except StudentsSubjects.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Subject assignment not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def ajax_get_available_subjects(request, student_id):
    """Fetch subjects NOT yet assigned to this student, but available in their course's branch"""
    try:
        student = get_object_or_404(Students, id=student_id)
        
        assigned_subject_ids = StudentsSubjects.objects.filter(student=student, deleted_at__isnull=True).values_list('subject_id', flat=True)
        
        # Get all available subjects that are not assigned to the student
        # Filtering by course removed as no direct link found between Course and Subject/Branch
        available_subjects = Subjects.objects.filter(
            deleted_at__isnull=True
        ).exclude(id__in=assigned_subject_ids).values('id', 'subject_name', 'subject_code').distinct().order_by('subject_name')
        
        return JsonResponse({'success': True, 'subjects': list(available_subjects)}, safe=False)
    except Exception as e:
        print(f"Error in ajax_get_available_subjects: {e}")
        return JsonResponse({'success': False, 'message': str(e), 'subjects': []})

@login_required
@require_POST
def student_subjects_bulk_assign(request):
    """Bulk assign subjects to a student"""
    try:
        student_id = request.POST.get('student')
        subject_ids = request.POST.getlist('subjects[]')
        
        if not student_id or not subject_ids:
            return JsonResponse({'success': False, 'message': 'Student and Subjects are required'}, status=400)
            
        student = get_object_or_404(Students, id=student_id)
        
        created_count = 0
        skipped_count = 0
        
        with transaction.atomic():
            for subject_id in subject_ids:
                if StudentsSubjects.objects.filter(student=student, subject_id=subject_id, deleted_at__isnull=True).exists():
                    skipped_count += 1
                    continue
                
                StudentsSubjects.objects.create(
                    student=student,
                    subject_id=subject_id,
                    created_by=request.user,
                    updated_by=request.user,
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
                created_count += 1
                
        message = f'Successfully assigned {created_count} subjects.'
        if skipped_count > 0:
            message += f' ({skipped_count} were already assigned and skipped).'
            
        return JsonResponse({'success': True, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
@require_POST
def student_subjects_delete(request, id):
    """Soft delete student subject assignment"""
    try:
        ss = get_object_or_404(StudentsSubjects, id=id)
        ss.deleted_at = timezone.now()
        ss.updated_by = request.user
        ss.save()
        return JsonResponse({'success': True, 'message': 'Subject assignment deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
def application_list_view(request):
    """Render application management page (Applicants)"""
    context = {
        'countries': Countries.objects.all().order_by('name'),
        'languages': Languages.objects.filter(status=True).order_by('language_name'),
        'courses': Courses.objects.filter(status=1).order_by('course_name'),
    }
    return render(request, 'admin/applications/list.html', context)

# Student Instructors Workflow
@login_required
def student_instructors_list(request):
    """Render student instructors management page"""
    courses = Courses.objects.filter(status=1).order_by('course_name')
    context = {
        'page_title': 'Student Instructors Management',
        'courses': courses,
    }
    return render(request, 'admin/students/instructors_list.html', context)

@login_required
def student_instructors_datatable(request):
    """DataTables server-side processing for student instructors"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'desc')
    
    query = StudentsInstructor.objects.filter(deleted_at__isnull=True).select_related('student', 'instructor', 'subject', 'updated_by')

    if search_value:
        query = query.filter(
            Q(student__first_name__icontains=search_value) |
            Q(student__last_name__icontains=search_value) |
            Q(instructor__staff_name__icontains=search_value) | 
            Q(subject__subject_name__icontains=search_value) | 
            Q(student__student_id__icontains=search_value)
        )
    
    order_col = '-created_at'
    if order_column_index == 0:
        order_col = 'id'
    elif order_column_index == 1:
        order_col = 'student__first_name'
    elif order_column_index == 2:
        order_col = 'subject__subject_name'
    elif order_column_index == 3:
        order_col = 'instructor__staff_name'
    elif order_column_index == 4:
        order_col = 'updated_by__username'

    if order_direction == 'desc' and not order_col.startswith('-'):
        order_col = '-' + order_col
    
    total_records = StudentsInstructor.objects.filter(deleted_at__isnull=True).count()
    filtered_records = query.count()
    data_list = query.order_by(order_col)[start:start+length]
    
    data = []
    for item in data_list:
        student_name = f"{item.student.first_name} {item.student.last_name or ''}"
        if item.student.student_id:
             student_name += f" ({item.student.student_id})"
             
        updated_by = item.updated_by.username if item.updated_by else '-'
        updated_date = item.updated_at.strftime('%Y-%m-%d') if item.updated_at else ''
        updated_info = f"{updated_by}<br><small>{updated_date}</small>"
        
        actions = f'''
            <div class="btn-group" role="group">
        
        <div class="btn-group" role="group">
            <button id="btnGroupDrop{item.id}" type="button" class="btn btn-secondary btn-sm dropdown-toggle" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                Actions
            </button>
            <div class="dropdown-menu" aria-labelledby="btnGroupDrop{item.id}">
                <button class="dropdown-item dropdown-item" style="width:100%; text-align:left; background:none; border:none;" onclick="deleteStudentInstructor({item.id})" title="Delete">
                    <i class="fas fa-trash mr-2 text-danger"></i> <span class="text-danger">Delete</span>
                </button>
            </div>
        </div>
    </div>
        '''
        
        data.append({
            'id': item.id,
            'student_name': student_name,
            'subject_name': item.subject.subject_name if item.subject else 'General / No Subject',
            'instructor_name': item.instructor.staff_name if item.instructor else 'Unknown Instructor',
            'updated_by': updated_info,
            'actions': actions
        })
        
    return JsonResponse({'draw': draw, 'recordsTotal': total_records, 'recordsFiltered': filtered_records, 'data': data})

@login_required
def ajax_get_assigned_subjects_by_student(request, student_id):
    """Fetch subjects assigned to a specific student from StudentsSubjects"""
    student = get_object_or_404(Students, id=student_id)
    # Get subjects from StudentsSubjects model for this student
    subjects = StudentsSubjects.objects.filter(
        student=student, 
        deleted_at__isnull=True
    ).select_related('subject').values(
        'subject__id', 
        'subject__subject_name', 
        'subject__subject_code'
    ).distinct()
    
    # Format for JSON
    subject_list = [{
        'id': s['subject__id'],
        'name': f"{s['subject__subject_name']} ({s['subject__subject_code']})"
    } for s in subjects]
    
    return JsonResponse({'success': True, 'subjects': subject_list})

@login_required
def ajax_get_available_instructors(request, student_id, subject_id):
    """Fetch instructors assigned to a specific subject (via StaffsSubjects) 
    and NOT yet assigned to this student for THIS subject"""
    student = get_object_or_404(Students, id=student_id)
    subject = get_object_or_404(Subjects, id=subject_id)
    
    # Get IDs of instructors already assigned to this student for this subject
    assigned_instructor_ids = StudentsInstructor.objects.filter(
        student=student, 
        subject=subject,
        deleted_at__isnull=True
    ).values_list('instructor_id', flat=True)
    
    # Get staff linked to this subject via StaffsSubjects
    subject_staff_ids = StaffsSubjects.objects.filter(
        subject=subject,
        deleted_at__isnull=True
    ).values_list('staff_id', flat=True)
    
    # Filter active staff who are linked to the subject and not yet assigned to the student for it
    available_instructors = Staffs.objects.filter(
        id__in=subject_staff_ids,
        status=True, 
        deleted_at__isnull=True
    ).exclude(id__in=assigned_instructor_ids).values('id', 'staff_name', 'staff_id', 'title').distinct()
    
    return JsonResponse({'success': True, 'instructors': list(available_instructors)})

@login_required
@require_POST
def student_instructors_bulk_assign(request):
    """Bulk assign instructors to a student for a specific subject"""
    try:
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        instructor_ids = request.POST.getlist('instructors[]')
        
        if not student_id or not subject_id or not instructor_ids:
            return JsonResponse({'success': False, 'message': 'Student, Subject and Instructors are required'}, status=400)
            
        student = get_object_or_404(Students, id=student_id)
        subject = get_object_or_404(Subjects, id=subject_id)
        
        created_count = 0
        skipped_count = 0
        
        with transaction.atomic():
            for instructor_id in instructor_ids:
                if StudentsInstructor.objects.filter(student=student, subject=subject, instructor_id=instructor_id, deleted_at__isnull=True).exists():
                    skipped_count += 1
                    continue
                
                StudentsInstructor.objects.create(
                    student=student,
                    subject=subject,
                    instructor_id=instructor_id,
                    created_by=request.user,
                    updated_by=request.user
                )
                created_count += 1
                
        message = f'Successfully assigned {created_count} instructors for {subject.subject_name}.'
        if skipped_count > 0:
            message += f' ({skipped_count} were already assigned and skipped).'
            
        return JsonResponse({'success': True, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
@require_POST
def student_instructors_delete(request, id):
    """Soft delete student instructor assignment"""
    try:
        si = get_object_or_404(StudentsInstructor, id=id)
        si.deleted_at = timezone.now()
        si.updated_by = request.user
        si.save()
        return JsonResponse({'success': True, 'message': 'Instructor assignment deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

# Student Uploads Workflow
@login_required
def student_uploads_list(request):
    """Render student uploads management page"""
    courses = Courses.objects.filter(status=1).order_by('course_name')
    context = {
        'page_title': 'Student Uploads Management',
        'courses': courses,
    }
    return render(request, 'admin/students/uploads_list.html', context)

@login_required
def student_uploads_datatable(request):
    """DataTables server-side processing for student uploads"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'desc')
    
    query = StudentsUploads.objects.filter(deleted_at__isnull=True).select_related(
        'student', 'upload', 'upload__subject', 'updated_by'
    )

    if search_value:
        query = query.filter(
            Q(student__first_name__icontains=search_value) |
            Q(student__last_name__icontains=search_value) |
            Q(upload__upload_name__icontains=search_value) | 
            Q(upload__subject__subject_name__icontains=search_value) | 
            Q(student__student_id__icontains=search_value)
        )
    
    order_col = '-created_at'
    if order_column_index == 0:
        order_col = 'id'
    elif order_column_index == 1:
        order_col = 'student__first_name'
    elif order_column_index == 2:
        order_col = 'upload__subject__subject_name'
    elif order_column_index == 3:
        order_col = 'upload__upload_name'
    elif order_column_index == 4:
        order_col = 'updated_by__username'

    if order_direction == 'desc' and not order_col.startswith('-'):
        order_col = '-' + order_col
    
    total_records = StudentsUploads.objects.filter(deleted_at__isnull=True).count()
    filtered_records = query.count()
    data_list = query.order_by(order_col)[start:start+length]
    
    data = []
    for item in data_list:
        student_name = f"{item.student.first_name} {item.student.last_name or ''}"
        if item.student.student_id:
             student_name += f" ({item.student.student_id})"
             
        updated_by = item.updated_by.username if item.updated_by else '-'
        updated_date = item.updated_at.strftime('%Y-%m-%d') if item.updated_at else ''
        updated_info = f"{updated_by}<br><small>{updated_date}</small>"
        
        upload_type = 'Other'
        if item.upload:
            if item.upload.media:
                upload_type = 'Media'
            elif item.upload.video_id:
                upload_type = 'Video'
            elif item.upload.youtube:
                upload_type = 'YouTube'

        actions = f'''
            <div class="btn-group" role="group">
        
        <div class="btn-group" role="group">
            <button id="btnGroupDrop{item.id}" type="button" class="btn btn-secondary btn-sm dropdown-toggle" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                Actions
            </button>
            <div class="dropdown-menu" aria-labelledby="btnGroupDrop{item.id}">
                <button class="dropdown-item dropdown-item" style="width:100%; text-align:left; background:none; border:none;" onclick="deleteStudentUpload({item.id})" title="Delete">
                    <i class="fas fa-trash mr-2 text-danger"></i> <span class="text-danger">Delete</span>
                </button>
            </div>
        </div>
    </div>
        '''
        
        data.append({
            'id': item.id,
            'student_name': student_name,
            'subject_name': item.upload.subject.subject_name if item.upload and item.upload.subject else 'General',
            'upload_name': f'<div><strong>{item.upload.upload_name if item.upload else "Unknown"}</strong><div class="small text-muted">{item.upload.code if item.upload else ""}</div></div>',
            'type': upload_type,
            'updated_by': updated_info,
            'actions': actions
        })
        
    return JsonResponse({'draw': draw, 'recordsTotal': total_records, 'recordsFiltered': filtered_records, 'data': data})

@login_required
def ajax_get_available_uploads(request, student_id, subject_id):
    """Fetch uploads linked to a subject and NOT yet assigned to this student"""
    student = get_object_or_404(Students, id=student_id)
    subject = get_object_or_404(Subjects, id=subject_id)
    
    # Get IDs of uploads already assigned to this student
    assigned_upload_ids = StudentsUploads.objects.filter(
        student=student, 
        deleted_at__isnull=True
    ).values_list('upload_id', flat=True)
    
    # Get uploads linked to this subject
    available_uploads = Uploads.objects.filter(
        subject=subject,
        status=True
    ).exclude(id__in=assigned_upload_ids).values('id', 'upload_name', 'code', 'format').distinct()
    
    return JsonResponse({'success': True, 'uploads': list(available_uploads)})

@login_required
@require_POST
def student_uploads_bulk_assign(request):
    """Bulk assign uploads to a student"""
    try:
        student_id = request.POST.get('student')
        upload_ids = request.POST.getlist('uploads[]')
        
        if not student_id or not upload_ids:
            return JsonResponse({'success': False, 'message': 'Student and Uploads are required'}, status=400)
            
        student = get_object_or_404(Students, id=student_id)
        
        created_count = 0
        skipped_count = 0
        
        with transaction.atomic():
            for upload_id in upload_ids:
                if StudentsUploads.objects.filter(student=student, upload_id=upload_id, deleted_at__isnull=True).exists():
                    skipped_count += 1
                    continue
                
                StudentsUploads.objects.create(
                    student=student,
                    upload_id=upload_id,
                    created_by=request.user,
                    updated_by=request.user
                )
                created_count += 1
                
        message = f'Successfully assigned {created_count} uploads.'
        if skipped_count > 0:
            message += f' ({skipped_count} were already assigned and skipped).'
            
        return JsonResponse({'success': True, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
@require_POST
def student_uploads_delete(request, id):
    """Soft delete student upload assignment"""
    try:
        su = get_object_or_404(StudentsUploads, id=id)
        su.deleted_at = timezone.now()
        return JsonResponse({'success': True, 'message': 'Upload assignment deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

# Student Exams Workflow
@login_required
def student_exams_list(request):
    """Render student exams management page"""
    courses = Courses.objects.filter(status=1).order_by('course_name')
    
    # Get all available timezones
    try:
        import zoneinfo
        common_timezones = sorted(zoneinfo.available_timezones())
    except ImportError:
        try:
            import pytz
            common_timezones = pytz.all_timezones
        except ImportError:
            common_timezones = ['UTC', 'America/New_York', 'Europe/London', 'Asia/Kolkata', 'Asia/Dubai', 'Asia/Singapore']

    context = {
        'page_title': 'Student Submitted Exams Management',
        'courses': courses,
        'timezones': common_timezones,
    }
    return render(request, 'admin/students/exams_list.html', context)

@login_required
def student_exams_datatable(request):
    """DataTables server-side processing for student exams"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'desc')
    
    query = StudentsExams.objects.filter(deleted_at__isnull=True).select_related(
        'student', 'course', 'subject', 'exam', 'updated_by'
    )

    if search_value:
        query = query.filter(
            Q(student__first_name__icontains=search_value) |
            Q(student__last_name__icontains=search_value) |
            Q(exam__exam_name__icontains=search_value) | 
            Q(subject__subject_name__icontains=search_value) | 
            Q(course__course_name__icontains=search_value) |
            Q(student__student_id__icontains=search_value)
        )
    
    order_col = '-created_at'
    if order_column_index == 0:
        order_col = 'id'
    elif order_column_index == 1:
        order_col = 'student__first_name'
    elif order_column_index == 2:
        order_col = 'course__course_name'
    elif order_column_index == 3:
        order_col = 'subject__subject_name'
    elif order_column_index == 4:
        order_col = 'exam__exam_name'
    elif order_column_index == 5:
        order_col = 'start_time'
    elif order_column_index == 6:
        order_col = 'is_approved'
    elif order_column_index == 7:
        order_col = 'updated_by__username'

    if order_direction == 'desc' and not order_col.startswith('-'):
        order_col = '-' + order_col
    
    total_records = StudentsExams.objects.filter(deleted_at__isnull=True).count()
    filtered_records = query.count()
    data_list = query.order_by(order_col)[start:start+length]
    
    data = []
    for item in data_list:
        student_name = f"{item.student.first_name} {item.student.last_name or ''}"
        if item.student.student_id:
             student_name += f" ({item.student.student_id})"
             
        updated_by = item.updated_by.username if item.updated_by else '-'
        updated_date = item.updated_at.strftime('%Y-%m-%d') if item.updated_at else ''
        updated_info = f"{updated_by}<br><small>{updated_date}</small>"
        
        start_time = f"{item.start_time.strftime('%Y-%m-%d %H:%M')} ({item.timezone})" if item.start_time else '-'
        
        # Status Badge
        if item.is_approved:
            status = '<span class="badge bg-success">Approved</span>'
        else:
            status = '<span class="badge bg-warning">Pending</span>'

        # Conditional action buttons based on approval status
        primary_btn = ''
        dropdown_items = ''
        
        # Primary Button Logic
        if item.is_approved:
            primary_btn = f'''
                <button class="btn btn-info btn-sm view-btn mr-1" onclick="viewAnswerSheet({item.id})" title="View Answer Sheet">
                    <i class="fas fa-eye"></i>
                </button>
            '''
        else:
             primary_btn = f'''
                <button class="btn btn-info btn-sm view-btn mr-1" onclick="editExam({item.id})" title="Edit Exam">
                    <i class="fas fa-edit"></i>
                </button>
            '''
            
        # Dropdown Items Logic
        # Toggle Approval
        approval_icon = 'times-circle' if item.is_approved else 'check-circle'
        approval_color = 'text-warning' if item.is_approved else 'text-success'
        approval_text = 'Revoke Approval' if item.is_approved else 'Approve'
        
        dropdown_items += f'''
            <a class="dropdown-item" href="#" onclick="toggleApproval({item.id}); return false;">
                <i class="fas fa-{approval_icon} mr-2 {approval_color}"></i> {approval_text}
            </a>
        '''
        
        # Delete Item
        dropdown_items += f'''
            <div class="dropdown-divider"></div>
            <a class="dropdown-item" href="#" onclick="deleteStudentExam({item.id}); return false;">
                <i class="fas fa-trash mr-2 text-danger"></i> <span class="text-danger">Delete</span>
            </a>
        '''

        actions = f'''
            <div class="btn-group" role="group">
                {primary_btn}
                <div class="btn-group" role="group">
                    <button id="btnGroupDrop{item.id}" type="button" class="btn btn-secondary btn-sm dropdown-toggle" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                        Actions
                    </button>
                    <div class="dropdown-menu" aria-labelledby="btnGroupDrop{item.id}">
                        {dropdown_items}
                    </div>
                </div>
            </div>
        '''
        
        # Calculate total marks if exam is approved
        marks_display = '-'
        if item.is_approved:
            total_obtained = 0
            total_possible = 0
            
            if item.exam.exam_type == 'objective' or item.exam.exam_type == 'both':
                # Obtained
                objective_answers = ObjectiveAnswers.objects.filter(assignment=item)
                for ans in objective_answers:
                    if ans.mark:
                        total_obtained += ans.mark
                # Possible
                total_possible += item.exam.objective_questions.aggregate(total=Sum('marks'))['total'] or 0
                
            if item.exam.exam_type == 'descriptive' or item.exam.exam_type == 'both':
                # Obtained
                descriptive_answers = DescriptiveAnswers.objects.filter(assignment=item)
                for ans in descriptive_answers:
                    if ans.mark: 
                        total_obtained += ans.mark
                # Possible
                total_possible += item.exam.descriptive_questions.aggregate(total=Sum('mark'))['total'] or 0
                
            marks_display = f'{total_obtained}/{total_possible}'

        data.append({
            'id': item.id,
            'student_name': student_name,
            'course_name': item.course.course_name if item.course else '-',
            'subject_name': item.subject.subject_name if item.subject else '-',
            'exam_name': item.exam.exam_name if item.exam else 'Unknown Exam',
            'start_time': start_time,
            'duration': f'{item.exam_duration} min',
            'status': status,
            'marks': marks_display,
            'updated_by': updated_info,
            'actions': actions
        })
        
    return JsonResponse({'draw': draw, 'recordsTotal': total_records, 'recordsFiltered': filtered_records, 'data': data})

@login_required
def ajax_get_available_exams(request, student_id, subject_id):
    """Fetch exams linked to a subject and NOT yet assigned to this student"""
    student = get_object_or_404(Students, id=student_id)
    subject = get_object_or_404(Subjects, id=subject_id)
    
    # Get IDs of exams already assigned to this student
    assigned_exam_ids = StudentsExams.objects.filter(
        student=student, 
        deleted_at__isnull=True
    ).values_list('exam_id', flat=True)
    
    # Get exams linked to this subject
    available_exams = Exams.objects.filter(
        subject=subject,
        deleted_at__isnull=True
    ).exclude(id__in=assigned_exam_ids).values('id', 'exam_name', 'code').distinct()
    
    return JsonResponse({'success': True, 'exams': list(available_exams)})

@login_required
@require_POST
def student_exams_bulk_assign(request):
    """Assign an exam to a student with date and time"""
    try:
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        exam_id = request.POST.get('exam')
        exam_date = request.POST.get('exam_date')
        start_time_str = request.POST.get('start_time')
        timezone_val = request.POST.get('timezone', 'UTC')
        duration = int(request.POST.get('duration', 60))
        
        if not student_id or not exam_id or not exam_date or not start_time_str:
            return JsonResponse({'success': False, 'message': 'All fields are required'}, status=400)
            
        student = get_object_or_404(Students, id=student_id)
        subject = get_object_or_404(Subjects, id=subject_id) if subject_id else None
        course = student.course_applied if hasattr(student, 'course_applied') else None
        
        # Parse start_time
        try:
            start_time_combined_str = f"{exam_date} {start_time_str}"
            start_time_obj = datetime.strptime(start_time_combined_str, '%Y-%m-%d %H:%M')
        except ValueError as ve:
             return JsonResponse({'success': False, 'message': f'Invalid date or time format: {str(ve)}'}, status=400)
        
        # Calculate end_time
        end_time_obj = start_time_obj + timedelta(minutes=duration)
        
        if StudentsExams.objects.filter(student=student, exam_id=exam_id, deleted_at__isnull=True).exists():
            return JsonResponse({'success': False, 'message': 'This exam is already assigned to the student.'}, status=400)
        
        with transaction.atomic():
            StudentsExams.objects.create(
                student=student,
                course=course,
                subject=subject,
                exam_id=exam_id,
                start_time=start_time_obj,
                end_time=end_time_obj,
                timezone=timezone_val,
                exam_duration=duration,
                show_on_score=1,
                created_by=request.user,
                updated_by=request.user
            )
                
        return JsonResponse({'success': True, 'message': 'Exam assigned successfully.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
@require_POST
def student_exams_delete(request, id):
    """Soft delete student exam assignment"""
    try:
        se = get_object_or_404(StudentsExams, id=id)
        se.deleted_at = timezone.now()
        se.updated_by = request.user
        se.save()
        return JsonResponse({'success': True, 'message': 'Exam assignment deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
def view_answer_sheet(request, exam_id):

    """Display answer sheet for a specific student exam"""

    student_exam = get_object_or_404(StudentsExams, id=exam_id, deleted_at__isnull=True)
    exam = student_exam.exam
    # Get all questions for this exam
    objective_questions = []
    descriptive_questions = []

    if exam.exam_type == 'objective' or exam.exam_type == 'both':
        # Get objective questions
        obj_questions = ObjectiveQuestions.objects.filter(exam=exam).order_by('id')

        for question in obj_questions:
            # Get student's answer for this question
            answer = ObjectiveAnswers.objects.filter(

                assignment=student_exam,

                question=question

            ).first()
            
            objective_questions.append({

                'question': question,

                'answer': answer

            })

    

    if exam.exam_type == 'descriptive' or exam.exam_type == 'both':

        # Get descriptive questions

        desc_questions = DescriptiveQuestions.objects.filter(exam=exam).order_by('id')

        for question in desc_questions:

            # Get student's answer for this question

            answer = DescriptiveAnswers.objects.filter(

                assignment=student_exam,

                question=question

            ).first()

            

            descriptive_questions.append({

                'question': question,

                'answer': answer

            })

    

    context = {

        'student_exam': student_exam,

        'objective_questions': objective_questions,

        'descriptive_questions': descriptive_questions,

    }

    

    return render(request, 'admin/students/answer_sheet.html', context)



@login_required
@require_POST
def update_answer_marks(request):

    """Update marks for a student's answer"""

    try:

        answer_id = request.POST.get('answer_id')

        answer_type = request.POST.get('answer_type')  # 'objective' or 'descriptive'

        marks = request.POST.get('marks')

        

        if not answer_id or not answer_type or marks is None:

            return JsonResponse({'success': False, 'message': 'Missing required fields'}, status=400)

        

        marks = float(marks)

        

        if answer_type == 'objective':

            answer = get_object_or_404(ObjectiveAnswers, id=answer_id)

            # Validate marks don't exceed question marks

            if marks > float(answer.question.marks):

                return JsonResponse({

                    'success': False, 

                    'message': f'Marks cannot exceed {answer.question.marks}'

                }, status=400)

            answer.mark = marks

            answer.save()

        elif answer_type == 'descriptive':

            answer = get_object_or_404(DescriptiveAnswers, id=answer_id)

            # Validate marks don't exceed question marks

            if marks > float(answer.question.mark):

                return JsonResponse({

                    'success': False, 

                    'message': f'Marks cannot exceed {answer.question.mark}'

                }, status=400)

            answer.mark = marks

            answer.save()

        else:

            return JsonResponse({'success': False, 'message': 'Invalid answer type'}, status=400)

        # Signal will handle score calculation
        
        return JsonResponse({'success': True, 'message': 'Marks updated successfully'})

    except Exception as e:

        return JsonResponse({'success': False, 'message': str(e)}, status=400)


# Student Submitted Exams Views

@login_required
def student_submitted_exams_datatable(request):
    """DataTables server-side processing for student's submitted exams"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'desc')
    # Get current student
    try:
        student = Students.objects.get(user=request.user, deleted_at__isnull=True)
    except Students.DoesNotExist:
        return JsonResponse({'draw': draw, 'recordsTotal': 0, 'recordsFiltered': 0, 'data': []})
    # Query exams for this student
    query = StudentsExams.objects.filter(
        student=student,
        deleted_at__isnull=True

    ).select_related('exam', 'course', 'subject')
    if search_value:
        query = query.filter(
            Q(exam__exam_name__icontains=search_value) |

            Q(subject__subject_name__icontains=search_value) |

            Q(course__course_name__icontains=search_value)

        )

    # Ordering
    order_col = '-created_at'

    if order_column_index == 0:

        order_col = 'exam__exam_name'

    elif order_column_index == 1:

        order_col = 'subject__subject_name'

    elif order_column_index == 2:

        order_col = 'course__course_name'

    elif order_column_index == 3:

        order_col = 'start_time'



    if order_direction == 'desc' and not order_col.startswith('-'):

        order_col = '-' + order_col

    total_records = StudentsExams.objects.filter(student=student, deleted_at__isnull=True).count()
    filtered_records = query.count()
    data_list = query.order_by(order_col)[start:start+length]
    data = []
    for item in data_list:
        start_time = item.start_time.strftime('%Y-%m-%d %H:%M') if item.start_time else '-'
        # Determine status
        if item.is_exam_ended:
            status = '<span class="status-badge status-ended">Ended</span>'
        elif item.is_exam_started:
            status = '<span class="status-badge status-started">In Progress</span>'
        elif item.is_approved:
            status = '<span class="status-badge status-approved">Approved</span>'
        else:
            status = '<span class="status-badge status-pending">Pending</span>'
        # Calculate total marks if available
        from django.db.models import Sum

        obj_marks = ObjectiveAnswers.objects.filter(assignment=item).aggregate(total=Sum('mark'))['total'] or 0
        desc_marks = DescriptiveAnswers.objects.filter(assignment=item).aggregate(total=Sum('mark'))['total'] or 0
        total_marks = float(obj_marks) + float(desc_marks)
        marks_display = f'{total_marks:.1f}' if total_marks > 0 else '-'
        # Actions - always show view answer sheet button
        actions = f'''

            <div class="btn-group" role="group">
        <button class="btn btn-info btn-sm mr-1" onclick="viewAnswerSheet({item.id})" title="View Answer Sheet">
                    <i class="bi bi-eye"></i>
                </button>
        <div class="btn-group" role="group">
            <button id="btnGroupDrop{item.id}" type="button" class="btn btn-secondary btn-sm dropdown-toggle" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                Actions
            </button>
            <div class="dropdown-menu" aria-labelledby="btnGroupDrop{item.id}">
                
            </div>
        </div>
    </div>

        '''
        data.append({
        
            'exam_name': item.exam.exam_name if item.exam else 'Unknown Exam',
            'subject_name': item.subject.subject_name if item.subject else '-',
            'course_name': item.course.course_name if item.course else '-',
            'start_time': start_time,
            'duration': f'{item.exam_duration} min',
            'status': status,
            'marks': marks_display,
            'actions': actions

        })
    return JsonResponse({'draw': draw, 'recordsTotal': total_records, 'recordsFiltered': filtered_records, 'data': data})

# Student Submitted Exams Views
@login_required
def student_submitted_exams_list(request):
    """Render student submitted exams page for admin"""
    context = {
        'page_title': 'Student Submitted Exams',
    }
    return render(request, 'admin/students/student_submitted_exams.html', context)

@login_required
def student_submitted_exams_datatable(request):
    """DataTables server-side processing for all students' submitted exams"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'desc')
    
    # Query all exams
    query = StudentsExams.objects.filter(
        deleted_at__isnull=True
    ).select_related('student', 'exam', 'course', 'subject')

    if search_value:
        query = query.filter(
            Q(student__first_name__icontains=search_value) |
            Q(student__last_name__icontains=search_value) |
            Q(exam__exam_name__icontains=search_value) |
            Q(subject__subject_name__icontains=search_value) |
            Q(course__course_name__icontains=search_value)
        )
    
    # Ordering
    order_col = '-created_at'
    if order_column_index == 0:
        order_col = 'student__first_name'
    elif order_column_index == 1:
        order_col = 'exam__exam_name'
    elif order_column_index == 2:
        order_col = 'subject__subject_name'
    elif order_column_index == 3:
        order_col = 'course__course_name'
    elif order_column_index == 4:
        order_col = 'start_time'

    if order_direction == 'desc' and not order_col.startswith('-'):
        order_col = '-' + order_col
    
    total_records = StudentsExams.objects.filter(deleted_at__isnull=True).count()
    filtered_records = query.count()
    data_list = query.order_by(order_col)[start:start+length]
    
    data = []
    for item in data_list:
        student_name = f"{item.student.first_name} {item.student.last_name}" if item.student else "Unknown Student"
        start_time = item.start_time.strftime('%Y-%m-%d %H:%M') if item.start_time else '-'
        
        # Determine status
        if item.is_exam_ended:
            status = '<span class="status-badge status-ended">Ended</span>'
        elif item.is_exam_started:
            status = '<span class="status-badge status-started">In Progress</span>'
        elif item.is_approved:
            status = '<span class="status-badge status-approved">Approved</span>'
        else:
            status = '<span class="status-badge status-pending">Pending</span>'
        
        # Calculate total marks if available
        from django.db.models import Sum
        obj_marks = ObjectiveAnswers.objects.filter(assignment=item).aggregate(total=Sum('mark'))['total'] or 0
        desc_marks = DescriptiveAnswers.objects.filter(assignment=item).aggregate(total=Sum('mark'))['total'] or 0
        total_marks = float(obj_marks) + float(desc_marks)
        
        marks_display = f'{total_marks:.1f}' if total_marks > 0 else '-'
        
        # Actions - view answer sheet button
        actions = f'''
            <div class="btn-group" role="group">
        <button class="btn btn-info btn-sm mr-1" onclick="viewAnswerSheet({item.id})" title="View Answer Sheet">
                    <i class="bi bi-eye"></i> 
                </button>
        <div class="btn-group" role="group">
            <button id="btnGroupDrop{item.id}" type="button" class="btn btn-secondary btn-sm dropdown-toggle" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                Actions
            </button>
            <div class="dropdown-menu" aria-labelledby="btnGroupDrop{item.id}">
                
            </div>
        </div>
    </div>
        '''   
        data.append({
            'student_name': student_name,
            'exam_name': item.exam.exam_name if item.exam else 'Unknown Exam',
            'subject_name': item.subject.subject_name if item.subject else '-',
            'course_name': item.course.course_name if item.course else '-',
            'start_time': start_time,
            'duration': f'{item.exam_duration} min',
            'status': status,
            'marks': marks_display,
            'actions': actions
        })
        
    return JsonResponse({'draw': draw, 'recordsTotal': total_records, 'recordsFiltered': filtered_records, 'data': data})


@login_required
def student_assignment_list(request, submitted_only=False):
    """Render student assignment list page for Admin"""
    courses = Courses.objects.filter(status=1).order_by('course_name')
    page_title = 'Student Submitted Assignments' if submitted_only else 'Student Assignments'
    context = {
        'page_title': page_title,
        'courses': courses,
        'submitted_only': submitted_only,
    }
    return render(request, 'admin/students/student_assignment_list.html', context)

@login_required
def student_assignment_datatable(request):
    """DataTables server-side processing for all student assignments (Admin)"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    
    # Query ALL assignments
    query = StudentsAssignment.objects.filter(
        deleted_at__isnull=True
    ).select_related('student', 'assignment', 'assignment__subject')

    submitted_only = request.GET.get('submitted_only') == 'true'
    
    if submitted_only:
        query = query.filter(submitted_on__isnull=False)

    if search_value:
        query = query.filter(
            Q(student__first_name__icontains=search_value) |
            Q(student__last_name__icontains=search_value) |
            Q(assignment__assignment_name__icontains=search_value) |
            Q(assignment__subject__subject_name__icontains=search_value)
        )

    # Ordering
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'desc')
    
    order_col = '-created_at' # Default
    if order_column_index == 0:
        order_col = 'student__first_name'
    elif order_column_index == 1:
        order_col = 'assignment__assignment_name'
    elif order_column_index == 2:
        order_col = 'assignment__subject__subject_name'

    if order_direction == 'desc' and not order_col.startswith('-'):
        order_col = '-' + order_col
    
    total_records = StudentsAssignment.objects.filter(deleted_at__isnull=True).count()
    filtered_records = query.count()
    data_list = query.order_by(order_col)[start:start+length]

    data = []
    data = []
    for index, item in enumerate(data_list):
        student_name = f"{item.student.first_name} {item.student.last_name}" if item.student else "Unknown"
        action_btn = ''
        delete_btn = ''
        status = ''

        # Determine status
        if item.submitted_on:
            status = '<span class="status-badge status-approved">Submitted</span>'
            # View Button
            action_btn = f'''
                <button class="btn-action btn-view" onclick="viewAnswerSheet({item.id})" title="View Answer Sheet">
                    <i class="bi bi-eye"></i> 
                </button>
            '''
        else:
            status = '<span class="status-badge status-pending">Pending</span>'
        
        # Delete Button (Now available for ALL assignments as per request)
        delete_btn = f'''<button class="btn-action btn-delete" onclick="deleteAssignment({item.id})" title="Delete Assignment">
                <i class="bi bi-trash"></i>
            </button>
        '''

        # Serial Number Calculation
        sno = start + index + 1

        data.append({
            'sno': sno,
            'student_name': student_name,
            'assignment_name': item.assignment.assignment_name if item.assignment else 'Unknown',
            'subject_name': item.assignment.subject.subject_name if (item.assignment and item.assignment.subject) else '-',
            'status': status,
            'actions': f'<div class="action-buttons">{action_btn} {delete_btn}</div>'
        })
        
    return JsonResponse({'draw': draw, 'recordsTotal': total_records, 'recordsFiltered': filtered_records, 'data': data})

@login_required
def view_assignment_answer_sheet(request, id):
    """Display answer sheet for a student assignment"""
    student_assignment = get_object_or_404(StudentsAssignment, id=id, deleted_at__isnull=True)
    
    # Get answers
    answers = AssignmentAnswers.objects.filter(
        assignment=student_assignment.assignment, 
        student=student_assignment.student
    ).order_by('id')
    
    context = {
        'student_assignment': student_assignment,
        'answers': answers,
    }
    return render(request, 'admin/students/assignment_answer_sheet.html', context)

@login_required
def student_assignment_edit(request, id):
    """Placeholder for editing student assignment"""
    return HttpResponse("Edit functionality to be implemented.")

@csrf_exempt
@login_required
def student_assignment_delete(request, id):
    """Soft delete student assignment"""
    if request.method == 'POST':
        try:
            assignment = StudentsAssignment.objects.get(id=id)
            assignment.deleted_at = timezone.now()
            assignment.save()
            return JsonResponse({'success': True, 'message': 'Assignment deleted successfully.'})
        except StudentsAssignment.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Assignment not found.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@login_required
def update_assignment_marks(request):
    """Update marks for specific answer or total marks"""
    if request.method == 'POST':
        answer_id = request.POST.get('answer_id')
        marks = request.POST.get('marks')
        
        try:
            answer = AssignmentAnswers.objects.get(id=answer_id)
            answer.marks_optained = float(marks)
            answer.save()
            
            # Recalculate total for student assignment
            student_assignment = StudentsAssignment.objects.filter(
                student=answer.student, 
                assignment=answer.assignment
            ).first()
            
            if student_assignment:
                total = AssignmentAnswers.objects.filter(
                    assignment=answer.assignment,
                    student=answer.student
                ).aggregate(Sum('marks_optained'))['marks_optained__sum'] or 0
                student_assignment.total_marks = total
                student_assignment.save()
                
            return JsonResponse({'success': True, 'message': 'Marks updated successfully.'})
        except (AssignmentAnswers.DoesNotExist, ValueError):
            return JsonResponse({'success': False, 'message': 'Error updating marks.'})
            
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

@login_required
@require_POST
def student_assignments_assign(request):
    """Assign an assignment to a student"""
    try:
        student_id = request.POST.get('student_id')
        assignment_id = request.POST.get('assignment_id')
        submission_date = request.POST.get('submission_date') # Due date
        
        if not all([student_id, assignment_id, submission_date]):
             return JsonResponse({'success': False, 'message': 'Missing required fields.'})
             
        student = Students.objects.get(id=student_id)
        assignment = Assignments.objects.get(id=assignment_id)
        
        # Check if already assigned (optional, but good practice)
        # Using submitted_on to track completion, so duplicate assignment might be weird if not completed.
        # But let's allow re-assignment or check existence.
        
        # Create assignment record
        StudentsAssignment.objects.create(
            student=student,
            assignment=assignment,
            submission_date=submission_date, # This is the "Submit on or before"
            created_by=request.user,
            updated_by=request.user # Assuming model might use these or just ignore if not in model
        )
        
        return JsonResponse({'success': True, 'message': 'Assignment assigned successfully.'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def ajax_get_students_by_course(request, course_id=None):
    """Get active students for a course"""
    try:
        # If course_id is passed as arg (from url), use it. Else try GET param.
        if course_id is None:
            course_id = request.GET.get('course_id')
            
        # Students model does NOT have deleted_at. Use active=True.
        students = Students.objects.filter(course_applied_id=course_id, active=True).order_by('first_name', 'last_name').values('id', 'first_name', 'last_name', 'student_id')
        return JsonResponse({'students': list(students)})
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def ajax_get_subjects_by_student(request, student_id=None):
    """Get subjects for a student"""
    try:
        if student_id is None:
            student_id = request.GET.get('student_id')

        # Use StudentsSubjects to find subjects assigned to the student
        # StudentsSubjects HAS deleted_at
        student_subjects = StudentsSubjects.objects.filter(
            student_id=student_id, 
            deleted_at__isnull=True
        ).select_related('subject')
        
        subjects = []
        for ss in student_subjects:
            if ss.subject:
                subjects.append({
                    'id': ss.subject.id, 
                    'name': ss.subject.subject_name,
                    'subject_name': ss.subject.subject_name,
                    'subject_code': ss.subject.subject_code
                })
                
        return JsonResponse({'subjects': subjects})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def ajax_get_assignments_by_subject(request):
    """Get assignments for a subject"""
    subject_id = request.GET.get('subject_id')
    # Assignments HAS deleted_at
    assignments = Assignments.objects.filter(subject_id=subject_id, deleted_at__isnull=True).values('id', 'assignment_name')
    return JsonResponse({'assignments': list(assignments)})

@login_required
def media_library_json(request):
    """
    Returns a JSON list of media files for the media selector.
    Supports pagination and search.
    """
    page_number = request.GET.get('page', 1)
    search_query = request.GET.get('search', '')
    
    media_list = MediaLibrary.objects.all().order_by('-created_at')
    
    if search_query:
        media_list = media_list.filter(file_name__icontains=search_query)
        
    per_page = 18 # 6x3 grid
    paginator = Paginator(media_list, per_page)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        # If page is out of range, return empty list (for infinite scroll/load more)
        page_obj = []

    data = []
    has_next = False
    next_page_number = None

    if hasattr(page_obj, 'has_next'):
        has_next = page_obj.has_next()
        if has_next:
            next_page_number = page_obj.next_page_number()

    if page_obj:
        for media in page_obj:
            # Determine thumbnail URL
            thumb_url = ''
            if media.media_type == 'image' and media.file_path:
                try:
                    thumb_url = media.file_path.url
                except:
                    thumb_url = ''
            elif media.media_type == 'video':
                 thumb_url = '/static/admin/img/video-icon.png' # Placeholder
            else:
                 thumb_url = '/static/admin/img/file-icon.png' # Placeholder

            data.append({
                'id': media.id,
                'name': media.file_name,
                'url': media.file_path.url if media.file_path else '',
                'thumb': thumb_url,
                'type': media.media_type,
                'dimensions': media.dimensions,
                'size': media.file_size
            })
            
    return JsonResponse({
        'success': True,
        'data': data,
        'has_next': has_next,
        'next_page': next_page_number
    })

@login_required
@require_POST
def media_library_upload_json(request):
    """
    Handles AJAX file uploads for the media library selector.
    """
    if 'file' in request.FILES:
        try:
            uploaded_file = request.FILES['file']
            
            media = MediaLibrary()
            media.file_name = uploaded_file.name
            media.file_path = uploaded_file
            media.file_type = uploaded_file.name.split('.')[-1].lower()
            media.file_size = f"{uploaded_file.size / 1024:.2f} KB"
            media.created_by = request.user
            media.updated_by = request.user
            media.created_at = timezone.now()
            
            # Dimension check for images
            if media.file_type in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                try:
                    img = Image.open(uploaded_file)
                    media.dimensions = f"{img.width}x{img.height}"
                    media.media_type = 'image'
                except:
                    media.media_type = 'file'
            elif media.file_type in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm']:
                 media.media_type = 'video'
            else:
                media.media_type = 'file'
                
            media.save()
            
            # Return the new media object data
            return JsonResponse({
                'success': True,
                'media': {
                    'id': media.id,
                    'name': media.file_name,
                    'url': media.file_path.url,
                    'thumb': media.file_path.url if media.media_type == 'image' else '/static/admin/img/file-icon.png'
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
            
    return JsonResponse({'success': False, 'message': 'No file provided'})

# --- Video Library JSON API ---

@login_required
def video_library_json(request):
    """
    Returns a JSON list of videos for the selector.
    """
    page_number = request.GET.get('page', 1)
    search_query = request.GET.get('search', '')
    
    videos_list = Videos.objects.filter(deleted_at__isnull=True).order_by('-created_at')
    
    if search_query:
        videos_list = videos_list.filter(title__icontains=search_query)
        
    per_page = 12
    paginator = Paginator(videos_list, per_page)
    
    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = []

    data = []
    has_next = False
    next_page_number = None

    if hasattr(page_obj, 'has_next'):
        has_next = page_obj.has_next()
        if has_next:
            next_page_number = page_obj.next_page_number()

    if page_obj:
        for video in page_obj:
            thumb_url = '/static/admin/img/video-icon.png'
            video_url = '#'
            
            if video.media:
                 if video.media.thumb_file_path:
                    thumb_url = video.media.thumb_file_path
                 if video.media.file_path:
                    try:
                        video_url = video.media.file_path.url
                    except:
                        pass
            elif video.youtube:
                 thumb_url = video.youtube.thumb_file_path or '/static/admin/img/youtube-icon.png'
                 video_url = video.youtube.file_path

            data.append({
                'id': video.id,
                'title': video.title,
                'thumb': thumb_url,
                'url': video_url,
                'description': video.description or ''
            })
            
    return JsonResponse({
        'success': True,
        'data': data,
        'has_next': has_next,
        'next_page': next_page_number
    })

@login_required
@require_POST
def video_library_create_json(request):
    """
    Handles AJAX creation of a new Video.
    """
    try:
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        upload_type = request.POST.get('upload_type', 'media')
        
        if not title:
            return JsonResponse({'success': False, 'message': 'Title is required'})

        video = Videos(
            title=title,
            description=description,
            created_by=request.user,
            updated_by=request.user,
            created_at=timezone.now()
        )
        
        with transaction.atomic():
            if upload_type == 'media':
                if 'video_file' in request.FILES:
                    uploaded_file = request.FILES['video_file']
                    media = MediaLibrary(
                        file_name=uploaded_file.name,
                        file_path=uploaded_file,
                        file_type=uploaded_file.name.split('.')[-1].lower(),
                        file_size=f"{uploaded_file.size / 1024:.2f} KB",
                        created_by=request.user,
                        updated_by=request.user,
                        created_at=timezone.now(),
                        media_type='video'
                    )
                    media.thumb_file_path = media.file_path.url if hasattr(media.file_path, 'url') else ''
                    media.save()
                    video.media = media
                else:
                    return JsonResponse({'success': False, 'message': 'Video file is required'})
            
            elif upload_type == 'youtube':
                youtube_url = request.POST.get('youtube_url')
                if youtube_url:
                    yt = YoutubeVideos(
                        file_path=youtube_url,
                        created_by=request.user,
                        updated_by=request.user,
                        created_at=timezone.now()
                    )
                    # Extract ID and Thumb
                    import re
                    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', youtube_url)
                    if video_id_match:
                        vid_id = video_id_match.group(1)
                        yt.thumb_file_path = f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg"
                    else:
                        yt.thumb_file_path = '/static/admin/img/youtube-icon.png'
                    
                    yt.save()
                    video.youtube = yt
                else:
                     return JsonResponse({'success': False, 'message': 'YouTube URL is required'})

            video.save()
        
        thumb_url = '/static/admin/img/video-icon.png'
        if video.media: thumb_url = video.media.thumb_file_path
        elif video.youtube: thumb_url = video.youtube.thumb_file_path

        return JsonResponse({
            'success': True,
            'video': {
                'id': video.id,
                'title': video.title,
                'thumb': thumb_url
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# --- YouTube Library JSON API ---

@login_required
def youtube_library_json(request):
    """
    Returns a JSON list of YouTube videos.
    """
    page_number = request.GET.get('page', 1)
    search_query = request.GET.get('search', '')
    
    yt_list = YoutubeVideos.objects.filter(deleted_at__isnull=True).order_by('-created_at')
    
    if search_query:
        yt_list = yt_list.filter(file_path__icontains=search_query)
        
    per_page = 12
    paginator = Paginator(yt_list, per_page)
    
    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = []

    data = []
    has_next = False
    next_page_number = None

    if hasattr(page_obj, 'has_next'):
        has_next = page_obj.has_next()
        if has_next:
            next_page_number = page_obj.next_page_number()

    if page_obj:
        for yt in page_obj:
            data.append({
                'id': yt.id,
                'url': yt.file_path,
                'thumb': yt.thumb_file_path or '/static/admin/img/youtube-icon.png',
                'name': yt.file_path
            })
            
    return JsonResponse({
        'success': True,
        'data': data,
        'has_next': has_next,
        'next_page': next_page_number
    })

@login_required
@require_POST
def youtube_library_create_json(request):
    """
    Handles AJAX creation of a new YouTube video.
    """
    try:
        url = request.POST.get('url')
        if not url:
            return JsonResponse({'success': False, 'message': 'URL is required'})
            
        yt = YoutubeVideos(
            file_path=url,
            created_by=request.user,
            updated_by=request.user,
            created_at=timezone.now()
        )
        
        # Extract ID and Thumb
        import re
        video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
        if video_id_match:
            vid_id = video_id_match.group(1)
            yt.thumb_file_path = f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg"
        else:
             yt.thumb_file_path = '/static/admin/img/youtube-icon.png'
            
        yt.save()
        
        return JsonResponse({
            'success': True,
            'youtube': {
                'id': yt.id,
                'url': yt.file_path,
                'thumb': yt.thumb_file_path,
                'name': yt.file_path
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# Question Management Views

@login_required
def question_descriptive_create(request, exam_id):
    """Create descriptive question"""
    exam = get_object_or_404(Exams, id=exam_id)
    
    if request.method == 'POST':
        form = DescriptiveQuestionsForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            question.created_by = request.user
            question.updated_by = request.user
            question.created_at = timezone.now()
            question.save()
            messages.success(request, 'Question added successfully!')
            return redirect('exams_edit', exam_id=exam_id)
        else:
            messages.error(request, 'Please correct the errors below.')
            return redirect('exams_edit', exam_id=exam_id) # Redirect back to edit page with errors (ideally handle errors better but for modal simplified)
    
    return redirect('exams_edit', exam_id=exam_id)

@login_required
def question_descriptive_edit(request, question_id):
    """Edit descriptive question"""
    question = get_object_or_404(DescriptiveQuestions, id=question_id)
    
    if request.method == 'POST':
        form = DescriptiveQuestionsForm(request.POST, instance=question)
        if form.is_valid():
            question = form.save(commit=False)
            question.updated_by = request.user
            question.updated_at = timezone.now()
            question.save()
            messages.success(request, 'Question updated successfully!')
            return redirect('exams_edit', exam_id=question.exam.id)
    
    return redirect('exams_edit', exam_id=question.exam.id)

@login_required
def question_descriptive_delete(request, question_id):
    """Delete descriptive question"""
    question = get_object_or_404(DescriptiveQuestions, id=question_id)
    exam_id = question.exam.id
    question.delete() # Hard delete as per model (no deleted_at in DescriptiveQuestions model view earlier, let's check)
    # Checking model: DescriptiveQuestions does NOT have deleted_at field in my previous read (Wait, let me double check).
    # Model definition:
    # class DescriptiveQuestions(models.Model):
    #     ...
    #     updated_at = ...
    #     created_at = ...
    # No deleted_at. So hard delete.
    messages.success(request, 'Question deleted successfully!')
    return redirect('exams_edit', exam_id=exam_id)

@login_required
def question_objective_create(request, exam_id):
    """Create objective question"""
    exam = get_object_or_404(Exams, id=exam_id)
    
    if request.method == 'POST':
        form = ObjectiveQuestionsForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            question.created_by = request.user
            question.updated_by = request.user
            question.created_at = timezone.now()
            question.save()
            messages.success(request, 'Question added successfully!')
            return redirect('exams_edit', exam_id=exam_id)
        else:
            messages.error(request, 'Please correct the errors below.')
            return redirect('exams_edit', exam_id=exam_id)
            
    return redirect('exams_edit', exam_id=exam_id)

@login_required
def question_objective_edit(request, question_id):
    """Edit objective question"""
    question = get_object_or_404(ObjectiveQuestions, id=question_id)
    
    if request.method == 'POST':
        form = ObjectiveQuestionsForm(request.POST, instance=question)
        if form.is_valid():
            question = form.save(commit=False)
            question.updated_by = request.user
            question.updated_at = timezone.now()
            question.save()
            messages.success(request, 'Question updated successfully!')
            return redirect('exams_edit', exam_id=question.exam.id)
            
    return redirect('exams_edit', exam_id=question.exam.id)

@login_required
def question_objective_delete(request, question_id):
    """Delete objective question"""
    question = get_object_or_404(ObjectiveQuestions, id=question_id)
    exam_id = question.exam.id
    question.delete() # Hard delete
    messages.success(request, 'Question deleted successfully!')
    return redirect('exams_edit', exam_id=exam_id)



@login_required
def student_exams_toggle_approval(request, id):
    if request.method == 'POST':
        try:
            student_exam = StudentsExams.objects.get(id=id)
            student_exam.is_approved = not student_exam.is_approved
            student_exam.updated_by = request.user
            student_exam.save()
            
            status = 'approved' if student_exam.is_approved else 'revoked'
            return JsonResponse({'success': True, 'message': f'Exam approval {status} successfully'})
        except StudentsExams.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Exam not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def student_exams_get(request, id):
    try:
        student_exam = StudentsExams.objects.get(id=id)
        
        exam_date = ''
        start_time = ''
        if student_exam.start_time:
            exam_date = student_exam.start_time.strftime('%Y-%m-%d')
            start_time = student_exam.start_time.strftime('%H:%M')

        data = {
            'id': student_exam.id,
            'exam_date': exam_date,
            'start_time': start_time,
            'duration': student_exam.exam_duration,
            'timezone': student_exam.timezone
        }
        return JsonResponse({'success': True, 'data': data})
    except StudentsExams.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Exam not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def student_exams_update(request, id):
    if request.method == 'POST':
        try:
            student_exam = StudentsExams.objects.get(id=id)
            
            exam_date = request.POST.get('exam_date')
            start_time = request.POST.get('start_time')
            duration = request.POST.get('duration')
            timezone = request.POST.get('timezone')
            
            if start_time and exam_date:
                # Combine date and time
                combined_dt_str = f"{exam_date} {start_time}"
                student_exam.start_time = datetime.strptime(combined_dt_str, '%Y-%m-%d %H:%M')
            
            if duration:
                student_exam.exam_duration = int(duration)
                
            if timezone:
                student_exam.timezone = timezone
            
            student_exam.updated_by = request.user
            student_exam.save()
            
            return JsonResponse({'success': True, 'message': 'Exam updated successfully'})
        except StudentsExams.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Exam not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def student_subjects_update(request, id):
    if request.method == 'POST':
        try:
            student_subject = StudentsSubjects.objects.get(id=id)
            
            subject_id = request.POST.get('subject_id')
            
            if subject_id:
                subject = get_object_or_404(Subjects, id=subject_id)
                student_subject.subject = subject
            
            student_subject.updated_by = request.user
            student_subject.save()
            
            return JsonResponse({'success': True, 'message': 'Subject updated successfully'})
        except StudentsSubjects.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Subject assignment not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
