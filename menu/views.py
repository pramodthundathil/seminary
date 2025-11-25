from django.shortcuts import render, redirect, get_object_or_404
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
from django.db.models import Q, Count
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


from home.models import News, MediaLibrary
from home.models import *
from .forms import MediaLibraryForm, NewsForm
from home.decorators import role_redirection
from datetime import datetime, timedelta

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
    for course in Courses.objects.filter(status=1)[:6]:
        # Count students who applied for this course
        student_count = Students.objects.filter(
            course_applied=course.id,
            active=1
        ).count()
        
        # Add student_count as an attribute to the course object
        course.student_count = student_count
        courses_list.append(course)
    
    # Get recent references
    references = ReferenceForm.objects.order_by('-created_at')[:10]
    
    # Calculate assignments in progress
    total_assignments = Assignments.objects.count()
    completed_assignments = StudentsAssignment.objects.filter(
        submitted_on__isnull=False
    ).count()
    
    if total_assignments > 0:
        tasks_in_progress = round(((total_assignments - completed_assignments) / total_assignments) * 100)
    else:
        tasks_in_progress = 0
    
    # Calculate total exams completed
    total_exams_completed = StudentsExams.objects.filter(
        is_exam_ended=1
    ).count()
    
    # Attendance calculation (example - customize based on your logic)
    total_classes = 100  # Example
    attended_classes = 80  # Example
    attendance_percentage = round((attended_classes / total_classes) * 100) if total_classes > 0 else 0
    
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
    }
    
    return render(request, "admin/index.html", context)


@login_required
def menu_list(request):
    """Display all menus"""
    menus = Menus.objects.filter(deleted_at__isnull=True).order_by('-created_at')
    context = {
        'menus': menus,
        'page_title': 'Menu Management'
    }
    return render(request, 'admin/menus/menu_list.html', context)

@login_required
def menu_engineer(request, menu_id=None):
    """Menu engineering page with drag and drop"""
    if menu_id:
        menu = get_object_or_404(Menus, id=menu_id, deleted_at__isnull=True)
    else:
        menu = None
    
    # Get all available pages
    pages = Pages.objects.filter(deleted_at__isnull=True, status=1).order_by('title')
    
    # Get existing menu items if editing
    menu_items = []
    if menu:
        menu_items = MenuItems.objects.filter(
            # menus=menu, 
            # menus_id = models.IntegerField(db_column='menus_id'),
            menus_id=menu.id,

            deleted_at__isnull=True
        ).order_by('menu_order')
    
    # Get all menus for selection
    all_menus = Menus.objects.filter(deleted_at__isnull=True)
    
    context = {
        'menu': menu,
        'pages': pages,
        'menu_items': menu_items,
        'all_menus': all_menus,
        'page_title': 'Menu Engineer' if menu else 'Create Menu'
    }
    return render(request, 'admin/menus/menu_engineer.html', context)

@login_required
def pages_list(request):
    """Display all pages"""
    pages = Pages.objects.filter(deleted_at__isnull=True).order_by('-created_at')
    context = {
        'pages': pages,
        'page_title': 'Pages Management'
    }
    return render(request, 'admin/menus/pages_list.html', context)

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
            
            # Create new items
            for idx, item_data in enumerate(items_data):
                page_id = item_data.get('page_id')
                page = None
                if page_id:
                    page = Pages.objects.get(id=page_id)
                
                MenuItems.objects.create(
                    menus=menu,
                    title=item_data.get('title'),
                    url=item_data.get('url', ''),
                    pages=page,
                    menu_type=item_data.get('menu_type', 'page'),
                    menu_order=idx + 1,
                    parent_id=item_data.get('parent_id', 0),
                    target_blank=int(item_data.get('target_blank', 0)),
                    original_title=item_data.get('original_title', ''),
                    created_by=request.user.id,
                    updated_by=request.user.id,
                    created_at=timezone.now()
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Menu items saved successfully'
        })
    except Exception as e:
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
            <div class="action-buttons">
                <button class="btn-action btn-edit" onclick="editNews({news.id})" title="Edit">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn-action btn-delete" onclick="deleteNews({news.id}, '{news.title}')" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
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
    
    
@login_required
@require_POST
def media_delete(request, media_id):
    """Soft delete media"""
    try:
        media = get_object_or_404(MediaLibrary, id=media_id, deleted_at__isnull=True)
        media.deleted_at = timezone.now()
        media.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Media deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Delete failed: {str(e)}'
        }, status=400)


def photo_gallery(request):
    return render(request,"admin/media/photo_gallery.html")







@login_required
def slider_list(request):
    """Main slider list view with pagination"""
    sliders_list = Sliders.objects.all().order_by('-id')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(sliders_list, 12)  # 12 items per page
    
    try:
        sliders = paginator.page(page)
    except PageNotAnInteger:
        sliders = paginator.page(1)
    except EmptyPage:
        sliders = paginator.page(paginator.num_pages)

    context = {
        "sliders": sliders,
        "total_sliders": sliders_list.count()
    }

    return render(request, 'admin/sliders/list.html', context)

####@login_required
def slider_datatable(request):
    """DataTables server-side processing for sliders"""
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

    # Query sliders
    # sliders = Sliders.objects.annotate(photo_count=Count('photos'))
    sliders = Sliders.objects.annotate(photo_count=Count('sliders_photos_slider'))

    
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
                        <span class="dimension-badge">{slider.width}x{slider.height}</span>
                        <span class="photo-count-badge">{slider.photo_count} photos</span>
                    </div>
                </div>
            ''',
            'dimensions': f'{slider.width} × {slider.height}',
            'photos': slider.photo_count,
            'created_at': slider.created_at.strftime('%Y-%m-%d'),
            'actions': f'''
                <div class="action-buttons">
                    <button class="btn-action btn-photos" onclick="managePhotos({slider.id})" title="Manage Photos">
                        <i class="fas fa-images"></i>
                    </button>
                    <button class="btn-action btn-edit" onclick="editSlider({slider.id})" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-action btn-delete" onclick="deleteSlider({slider.id}, '{slider.slider_name}')" title="Delete">
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

####@login_required
@require_http_methods(["POST"])
def slider_create(request):
    """Create new slider"""
    try:
        slider_name = request.POST.get('slider_name')
        code = request.POST.get('code')
        width = int(request.POST.get('width'))
        height = int(request.POST.get('height'))

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
            created_by=request.user.id,
            updated_by=request.user.id,
            created_at=timezone.now()
        )

        return JsonResponse({
            'success': True,
            'message': 'Slider created successfully',
            'slider_id': slider.id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

####@login_required
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
                'created_at': slider.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

####@login_required
@require_http_methods(["POST"])
def slider_update(request, slider_id):
    """Update slider"""
    try:
        slider = get_object_or_404(Sliders, id=slider_id)
        
        slider_name = request.POST.get('slider_name')
        code = request.POST.get('code')
        width = int(request.POST.get('width'))
        height = int(request.POST.get('height'))

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
        slider.updated_by = request.user.id
        slider.save()

        return JsonResponse({
            'success': True,
            'message': 'Slider updated successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

####@login_required
@require_http_methods(["POST"])
def slider_delete(request, slider_id):
    """Delete slider"""
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

####@login_required
###@login_required
def slider_photos_list(request, slider_id):
    """Slider photos management view"""
    slider = get_object_or_404(Sliders, id=slider_id)
    return render(request, 'admin/sliders/photos.html', {'slider': slider})

###@login_required
def slider_photos_datatable(request, slider_id):
    """DataTables for slider photos"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 12))

        photos = SliderPhotos.objects.filter(
            sliders_id=slider_id,
            deleted_at__isnull=True
        ).select_related('media')

        total_records = photos.count()
        photos = photos.order_by('id')[start:start + length]

        data = []
        for photo in photos:
            # Safely get media URL
            media_url = ''
            try:
                media_url = photo.media.file_path if photo.media else ''
            except:
                media_url = '/static/placeholder.jpg'
            
            # Safely format title and alt text
            title = photo.title or 'Untitled'
            alt_text = photo.alt_text or title
            
            data.append({
                'id': photo.id,
                'preview': f'<img src="{media_url}" class="photo-preview" alt="{alt_text}">',
                'info': f'''<div class="photo-info">
                    <div class="photo-title">{title}</div>
                    <div class="photo-button-info">
                        {f'<span class="button-badge">{photo.button_text}</span>' if photo.button_text else ''}
                    </div>
                </div>''',
                'created_at': photo.created_at.strftime('%Y-%m-%d') if photo.created_at else '-',
                'actions': f'''<div class="action-buttons">
                    <button class="btn-action btn-view" onclick="viewPhoto({photo.id})" title="View">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn-action btn-edit" onclick="editPhoto({photo.id})" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-action btn-delete" onclick="deletePhoto({photo.id})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>'''
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

###@login_required
@require_http_methods(["POST"])
def slider_photo_create(request, slider_id):
    """Add photo to slider"""
    try:
        media_id = request.POST.get('media_id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        alt_text = request.POST.get('alt_text')
        button_text = request.POST.get('button_text')
        button_link = request.POST.get('button_link')
        button_link_target = request.POST.get('button_link_target', '_self')

        photo = SliderPhotos.objects.create(
            sliders_id=slider_id,
            media_id=media_id,
            title=title,
            description=description,
            alt_text=alt_text,
            button_text=button_text,
            button_link=button_link,
            button_link_target=button_link_target,
            created_by=request.user.id,
            updated_by=request.user.id,
            created_at=timezone.now()
        )

        return JsonResponse({
            'success': True,
            'message': 'Photo added successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

###@login_required
def slider_photo_get(request, photo_id):
    """Get slider photo details"""
    try:
        photo = get_object_or_404(SliderPhotos, id=photo_id, deleted_at__isnull=True)
        return JsonResponse({
            'success': True,
            'data': {
                'id': photo.id,
                'media_id': photo.media_id,
                'media_url': photo.media.file_path,
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

###@login_required
@require_http_methods(["POST"])
def slider_photo_update(request, photo_id):
    """Update slider photo"""
    try:
        photo = get_object_or_404(SliderPhotos, id=photo_id, deleted_at__isnull=True)
        
        photo.title = request.POST.get('title')
        photo.description = request.POST.get('description')
        photo.alt_text = request.POST.get('alt_text')
        photo.button_text = request.POST.get('button_text')
        photo.button_link = request.POST.get('button_link')
        photo.button_link_target = request.POST.get('button_link_target', '_self')
        photo.updated_by = request.user.id
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

###@login_required
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
        courses = Courses.objects.all()

        
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
        
        # Apply ordering and pagination
        courses = courses.order_by(order_column)[start:start + length]

        # Prepare data
        data = []
        for course in courses:
            # Get media thumbnail
            media_preview = ''
            if course.media:
                try:
                    media_url = course.media.file_path
                    media_preview = f'<img src="{media_url}" class="course-thumb" alt="{course.course_name}">'
                except:
                    media_preview = '<div class="course-thumb-placeholder"><i class="fas fa-graduation-cap"></i></div>'
            else:
                media_preview = '<div class="course-thumb-placeholder"><i class="fas fa-graduation-cap"></i></div>'
            
            # Status badge
            status_text = 'Active' if course.status == 1 else 'Inactive'
            status_class = 'status-active' if course.status == 1 else 'status-inactive'
            
            # Qualification levels
            qual_levels = {
                1: 'Certificate',
                2: 'Diploma',
                3: 'Bachelor',
                4: 'Master',
                5: 'PhD'
            }
            qual_text = qual_levels.get(course.highest_qualification, 'Unknown')
            
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
                'actions': f'''<div class="action-buttons">
                    <button class="btn-action btn-view" onclick="viewCourse({course.id})" title="View">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn-action btn-edit" onclick="editCourse({course.id})" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-action btn-delete" onclick="deleteCourse({course.id}, '{course.course_name}')" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
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
@require_http_methods(["POST"])
def course_create(request):
    """Create new course"""
    try:
        course_name = request.POST.get('course_name')
        course_code = request.POST.get('course_code')
        highest_qualification_id = request.POST.get('highest_qualification')
        credit_hours = float(request.POST.get('credit_hours'))
        description = request.POST.get('description', '')
        browser_title = request.POST.get('browser_title', '')
        meta_description = request.POST.get('meta_description', '')
        meta_keywords = request.POST.get('meta_keywords', '')
        media_id = request.POST.get('media_id') or None
        status = int(request.POST.get('status', 1))
        apply_button_top = int(request.POST.get('apply_button_top', 0))
        apply_button_bottom = int(request.POST.get('apply_button_bottom', 0))
        print("*********",request.POST.get)


        # Check if course code already exists
        if Courses.objects.filter(course_code=course_code).exists():
            return JsonResponse({
                'success': False,
                'message': 'Course code already exists'
            })
        if not highest_qualification_id:
            return JsonResponse({
                'success': False,
                'message': 'Please select a highest qualification'
            })
       
        # Safely fetch qualification
        try:
            highest_qualification_obj = Qualifications.objects.get(id=highest_qualification_id)
        except Qualifications.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Selected qualification does not exist'
            })

        course = Courses.objects.create(
            course_name=course_name,
            course_code=course_code,
            highest_qualification=highest_qualification_obj,
            credit_hours=credit_hours,
            description=description,
            browser_title=browser_title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            media_id=media_id,
            status=status,
            apply_button_top=apply_button_top,
            apply_button_bottom=apply_button_bottom,
            created_by=request.user,   
            updated_by=request.user, 
            created_at=timezone.now()
        )

        return JsonResponse({
            'success': True,
            'message': 'Course created successfully',
            'course_id': course.id
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

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
                    'url': course.media.file_path,
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
                'highest_qualification': course.highest_qualification,
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

##@login_required
@require_http_methods(["POST"])
def course_update(request, course_id):
    """Update course"""
    try:
        course = get_object_or_404(Courses, id=course_id)
        
        course_name = request.POST.get('course_name')
        course_code = request.POST.get('course_code')
        highest_qualification = int(request.POST.get('highest_qualification'))
        credit_hours = float(request.POST.get('credit_hours'))
        description = request.POST.get('description', '')
        browser_title = request.POST.get('browser_title', '')
        meta_description = request.POST.get('meta_description', '')
        meta_keywords = request.POST.get('meta_keywords', '')
        media_id = request.POST.get('media_id') or None
        status = int(request.POST.get('status', 1))
        apply_button_top = int(request.POST.get('apply_button_top', 0))
        apply_button_bottom = int(request.POST.get('apply_button_bottom', 0))

        # Check if course code exists for other courses
        if Courses.objects.filter(course_code=course_code).exclude(id=course_id).exists():
            return JsonResponse({
                'success': False,
                'message': 'Course code already exists'
            })

        course.course_name = course_name
        course.course_code = course_code
        course.highest_qualification = highest_qualification
        course.credit_hours = credit_hours
        course.description = description
        course.browser_title = browser_title
        course.meta_description = meta_description
        course.meta_keywords = meta_keywords
        course.media_id = media_id
        course.status = status
        course.apply_button_top = apply_button_top
        course.apply_button_bottom = apply_button_bottom
        course.updated_by = request.user.id
        course.save()

        return JsonResponse({
            'success': True,
            'message': 'Course updated successfully'
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

##@login_required
@require_http_methods(["POST"])
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
    return render(request, 'admin/students/list.html')

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
        
        # Base queryset
        students = Students.objects.select_related('user_id', 'language_id').all()
        
        # Apply filters
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
        order_columns = ['id', 'student_id', 'first_name', 'email', 'status', 'created_at']
        order_column = order_columns[order_column_index] if order_column_index < len(order_columns) else 'id'
        
        if order_dir == 'desc':
            order_column = f'-{order_column}'
        
        students = students.order_by(order_column)
        
        # Total records
        total_records = Students.objects.count()
        filtered_records = students.count()
        
        # Pagination
        students = students[start:start + length]
        
        # Format data
        data = []
        for student in students:
            # Get full name
            full_name = f"{student.first_name or ''} {student.middle_name or ''} {student.last_name or ''}".strip()
            
            # Photo preview - responsive
            if student.photo:
                preview = f'<img src="{student.photo}" class="student-photo" alt="{full_name}">'
            else:
                initials = ''.join([n[0].upper() for n in full_name.split() if n])[:2]
                preview = f'<div class="student-photo-placeholder">{initials or "ST"}</div>'
            
            # Student info - responsive
            info_html = f'''
                <div class="student-info">
                    <div class="student-name">{full_name}</div>
                    <div class="student-meta">
                        <span class="student-badge"><i class="fas fa-id-card"></i> {student.student_id or 'N/A'}</span>
                        <span class="email-badge"><i class="fas fa-envelope"></i> {student.email or 'No Email'}</span>
                    </div>
                </div>
            '''
            
            # Status badges - stacked for mobile
            status_html = f'''
                <div class="status-container">
                    <span class="status-badge status-{'approved' if student.status else 'pending'}">
                        <i class="fas fa-{'check-circle' if student.status else 'clock'}"></i>
                        {'Approved' if student.status else 'Pending'}
                    </span>
                    <span class="status-badge status-{'active' if student.active else 'inactive'}">
                        <i class="fas fa-{'power-off' if student.active else 'ban'}"></i>
                        {'Active' if student.active else 'Inactive'}
                    </span>
                </div>
            '''
            safe_name=full_name.replace("'", "\\'")
            # Actions - responsive
            actions_html = f'''
                <div class="action-buttons">
                    <button class="btn-action btn-view" onclick="viewStudent({student.id})" title="View Details">
                        <i class="fas fa-eye"></i>
                        <span class="btn-text">View</span>
                    </button>
                    <button class="btn-action btn-edit" onclick="editStudent({student.id})" title="Edit Student">
                        <i class="fas fa-edit"></i>
                        <span class="btn-text">Edit</span>
                    </button>
                    <button class="btn-action btn-toggle" onclick="toggleActive({student.id}, {str(student.active).lower()})" 
                            title="Toggle Active Status">
                        <i class="fas fa-{'toggle-on' if student.active else 'toggle-off'}"></i>
                        <span class="btn-text">{'Deactivate' if student.active else 'Activate'}</span>
                    </button>
                    <button class="btn-action btn-{'success' if not student.status else 'warning'}" 
                            onclick="toggleApproval({student.id}, {str(student.status).lower()})" 
                            title="Toggle Approval Status">
                        <i class="fas fa-{'times-circle' if student.status else 'check-circle'}"></i>
                        <span class="btn-text">{'Disapprove' if student.status else 'Approve'}</span>
                    </button>
                    <button class="btn-action btn-delete" onclick="deleteStudent({student.id}, '{safe_name}  ')" title="Delete Student">
                        <i class="fas fa-trash"></i>
                        <span class="btn-text">Delete</span>
                    </button>
                </div>
            '''
            
            data.append({
                'id': student.id,
                'student_id': student.student_id or 'N/A',
                'preview': preview,
                'student_info': info_html,
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
            'citizenship': student.citizenship,
            'phone_code': student.phone_code,
            'phone_number': student.phone_number or '',
            'date_of_birth': student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else '',
            'mrital_status': student.mrital_status or '',
            'spouse_name': student.spouse_name or '',
            'children': student.children,
            'mailing_address': student.mailing_address or '',
            'city': student.city or '',
            'state': student.state or '',
            'country': student.country,
            'photo': student.photo or '',
            'zip_code': student.zip_code or '',
            'timezone': student.timezone,
            'highest_education': student.highest_education or '',
            'course_applied': student.course_applied,
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
            student.citizenship = data.get('citizenship') or None
            student.phone_code = data.get('phone_code') or None
            student.phone_number = data.get('phone_number', '')
            student.date_of_birth = data.get('date_of_birth') or None
            student.mrital_status = data.get('mrital_status', '')
            student.spouse_name = data.get('spouse_name', '')
            student.children = data.get('children') or None
            student.mailing_address = data.get('mailing_address', '')
            student.city = data.get('city', '')
            student.state = data.get('state', '')
            student.country = data.get('country') or None
            student.zip_code = data.get('zip_code', '')
            student.timezone = data.get('timezone', 'UTC')
            student.highest_education = data.get('highest_education', '')
            student.course_applied = data.get('course_applied') or None
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
            student.status = data.get('status', '0') == '1'
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

#@login_required
def student_toggle_approval(request, student_id):
    """Toggle student approval status"""
    if request.method == 'POST':
        try:
            student = Students.objects.get(id=student_id)
            student.status = not student.status
            
            # Set approve_date when approving
            if student.status:
                student.approve_date = timezone.now()
            else:
                student.approve_date = None
                
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