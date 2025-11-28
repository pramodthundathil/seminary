from django import template
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
    
    # If it's already just a video ID (11 alphanumeric characters with - or _)
    if re.match(r'^[a-zA-Z0-9_-]{11}', url.strip()):
        return url.strip()
    
    # Try multiple regex patterns
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})',  # watch?v=
        r'(?:youtu\.be\/)([a-zA-Z0-9_-]{11})',              # youtu.be/
        r'(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',    # embed/
        r'(?:youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',        # v/
        r'(?:m\.youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})', # mobile
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # Try parsing as URL with query parameters
    try:
        parsed_url = urlparse(url)
        if 'youtube.com' in parsed_url.netloc or 'youtu.be' in parsed_url.netloc:
            # Check query parameters for v=
            query_params = parse_qs(parsed_url.query)
            if 'v' in query_params:
                video_id = query_params['v'][0]
                if re.match(r'^[a-zA-Z0-9_-]{11}', video_id):
                    return video_id
    except:
        pass
    
    return ''