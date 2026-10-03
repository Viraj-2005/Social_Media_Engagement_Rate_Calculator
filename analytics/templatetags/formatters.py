from django import template

register = template.Library()


@register.filter
def abbreviate_number(value):
    """Abbreviate large numbers: 1822636408 -> 1.8B, 19456133 -> 19.5M"""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return value

    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B".rstrip('0').rstrip('.')
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M".rstrip('0').rstrip('.')
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K".rstrip('0').rstrip('.')
    else:
        return f"{num:,.0f}"


@register.filter
def abbreviate_number_full(value):
    """Abbreviate with more precision: 1822636408 -> 1.82B"""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return value

    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B".rstrip('0').rstrip('.')
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M".rstrip('0').rstrip('.')
    elif num >= 1_000:
        return f"{num / 1_000:.2f}K".rstrip('0').rstrip('.')
    else:
        return f"{num:,.0f}"


@register.filter
def divide(value, arg):
    """Divide value by arg: {{ value|divide:arg }}"""
    try:
        return float(value) / float(arg)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0


# Common YouTube categories (IDs from the YouTube Data API)
YOUTUBE_CATEGORY_NAMES = {
    '1': 'News & Politics', '2': 'Movies & Clips', '4': 'Music',
    '10': 'Science & Technology', '15': 'Travel & Events', '17': 'Sports',
    '19': 'People & Blogs', '20': 'Gaming', '23': 'Comedy',
    '24': 'Entertainment', '25': 'News & Politics', '26': 'How-to & Style',
    '27': 'Education', '28': 'Pets & Animals', '29': 'Film & Animation',
    '31': 'Gaming', '32': 'People & Blogs', '33': 'Comedy',
    '34': 'Entertainment', '35': 'News & Politics', '36': 'Science & Tech',
    '37': 'Travel & Events', '38': 'Food & Drink', '39': 'Autos & Vehicles',
    '40': 'Shows', '41': 'Animation & Manga', '42': 'Podcasts',
}


@register.filter
def category_name(value):
    """Map a raw YouTube category ID (e.g. '24') to a human readable name."""
    if not value:
        return ''
    return YOUTUBE_CATEGORY_NAMES.get(str(value).strip(), 'Other')