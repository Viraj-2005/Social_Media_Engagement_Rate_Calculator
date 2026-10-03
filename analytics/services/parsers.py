import re
from urllib.parse import urlparse, parse_qs
from typing import Optional, Tuple


YOUTUBE_VIDEO_PATTERNS = [
    r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
    r'^([a-zA-Z0-9_-]{11})$',
]

YOUTUBE_CHANNEL_PATTERNS = [
    r'youtube\.com/@([a-zA-Z0-9_.-]+)',
    r'youtube\.com/c/([a-zA-Z0-9_.-]+)',
    r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
    r'youtube\.com/user/([a-zA-Z0-9_.-]+)',
]


def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats."""
    if not url:
        return None

    url = url.strip()

    for pattern in YOUTUBE_VIDEO_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    parsed = urlparse(url)
    if parsed.netloc in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
        if parsed.path == '/watch':
            qs = parse_qs(parsed.query)
            if 'v' in qs:
                return qs['v'][0]

    return None


def extract_channel_identifier(url: str) -> Optional[Tuple[str, str]]:
    """
    Extract channel identifier from URL.
    Returns tuple of (identifier_type, identifier_value) where type is one of:
    'handle', 'custom', 'channel_id', 'username'
    """
    if not url:
        return None

    url = url.strip()

    for pattern in YOUTUBE_CHANNEL_PATTERNS:
        match = re.search(pattern, url)
        if match:
            if '@' in pattern:
                return ('handle', match.group(1))
            elif '/c/' in pattern:
                return ('custom', match.group(1))
            elif '/channel/' in pattern:
                return ('channel_id', match.group(1))
            elif '/user/' in pattern:
                return ('username', match.group(1))

    return None


def is_valid_video_url(url: str) -> bool:
    """Check if URL is a valid YouTube video URL."""
    return extract_video_id(url) is not None


def is_valid_channel_url(url: str) -> bool:
    """Check if URL is a valid YouTube channel URL."""
    return extract_channel_identifier(url) is not None


def normalize_video_url(video_id: str) -> str:
    """Create canonical YouTube video URL from video ID."""
    return f'https://www.youtube.com/watch?v={video_id}'


def normalize_channel_url(channel_id: str) -> str:
    """Create canonical YouTube channel URL from channel ID."""
    return f'https://www.youtube.com/channel/{channel_id}'