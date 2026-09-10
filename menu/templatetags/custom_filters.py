from django import template
from django.conf import settings
import os
import re
from urllib.parse import urlparse, parse_qs

register = template.Library()

@register.filter(name='youtube_id')
def youtube_id(url):
    """
    Extract YouTube video ID from various URL formats
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - Plain video ID (11 characters)
    """
    if not url:
        return ''

    url_str = str(url).strip()

    # If it's already just a video ID (11 alphanumeric characters with - or _)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_str):
        return url_str
    
    # Try multiple regex patterns
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})',  # watch?v=
        r'(?:youtu\.be\/)([a-zA-Z0-9_-]{11})',              # youtu.be/
        r'(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',    # embed/
        r'(?:youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',        # v/
        r'(?:m\.youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})', # mobile
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_str)
        if match:
            return match.group(1)
    
    # Try parsing as URL with query parameters
    try:
        parsed_url = urlparse(url_str)
        if 'youtube.com' in parsed_url.netloc or 'youtu.be' in parsed_url.netloc:
            # Check query parameters for v=
            query_params = parse_qs(parsed_url.query)
            if 'v' in query_params:
                video_id = query_params['v'][0]
                if re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
                    return video_id
    except Exception:
        pass
    
    return ''


@register.filter(name='media_url')
def media_url(val):
    """
    Resolves file paths or legacy MediaLibrary IDs to a full S3 media URL.
    """
    if not val:
        return ''
    val_str = str(val).strip()
    if 'homesreekanthkylmpublic' in val_str or 'cwamp64wwwtrinity' in val_str:
        return ''
    if val_str.isdigit():
        try:
            from home.models import MediaLibrary
            ml = MediaLibrary.objects.filter(id=int(val_str)).first()
            if ml and ml.file_path:
                val_str = str(ml.file_path)
        except Exception:
            pass
    if val_str.startswith('http://') or val_str.startswith('https://'):
        return val_str
    clean_path = val_str.lstrip('/')
    if clean_path.startswith('media/'):
        clean_path = clean_path[6:]
    import os
    from django.conf import settings

    prefixes = [
        '',
        'uploads/students/',
        'uploads/certificates/1/',
        'uploads/certificates/2/',
        'uploads/certificates/3/',
        'uploads/certificates/4/',
        'uploads/certificates/5/',
        'uploads/',
        'student_photos/',
        'student_certificates/'
    ]
    
    media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(getattr(settings, 'BASE_DIR', ''), 'media'))
    matched_path = clean_path
    for p in prefixes:
        candidate = p + clean_path
        if os.path.exists(os.path.join(media_root, candidate)):
            matched_path = candidate
            break

    media_url_setting = getattr(settings, 'MEDIA_URL', '/media/')
    base_url = media_url_setting if media_url_setting.endswith('/') else media_url_setting + '/'
    return base_url + matched_path


@register.filter(name='is_video')
def is_video(val):
    """
    Checks if a given file path or URL string corresponds to a video file.
    """
    if not val:
        return False
    val_str = str(val).lower()
    video_extensions = ('.mp4', '.webm', '.mov', '.avi', '.m4v', '.mkv', '.flv', '.ogv', '.3gp')
    return val_str.endswith(video_extensions) or 'video' in val_str