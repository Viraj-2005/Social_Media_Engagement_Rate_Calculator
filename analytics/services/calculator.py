from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


def safe_divide(numerator: float, denominator: float) -> Decimal:
    """Safely divide two numbers, returning Decimal('0') if denominator is zero."""
    if denominator == 0:
        return Decimal('0')
    return Decimal(str(numerator / denominator)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)


def calculate_total_engagement(likes: int, comments: int) -> int:
    """Calculate total engagement (likes + comments)."""
    return (likes or 0) + (comments or 0)


def calculate_engagement_rate(views: int, likes: int, comments: int) -> Decimal:
    """
    Calculate engagement rate: (Likes + Comments) / Views * 100
    Returns percentage as Decimal with 4 decimal places.
    """
    total_engagement = calculate_total_engagement(likes, comments)
    if views == 0:
        return Decimal('0')
    rate = (Decimal(str(total_engagement)) / Decimal(str(views))) * Decimal('100')
    return rate.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)


def calculate_like_rate(views: int, likes: int) -> Decimal:
    """Calculate like rate: Likes / Views * 100"""
    if views == 0:
        return Decimal('0')
    rate = (Decimal(str(likes or 0)) / Decimal(str(views))) * Decimal('100')
    return rate.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)


def calculate_comment_rate(views: int, comments: int) -> Decimal:
    """Calculate comment rate: Comments / Views * 100"""
    if views == 0:
        return Decimal('0')
    rate = (Decimal(str(comments or 0)) / Decimal(str(views))) * Decimal('100')
    return rate.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)


def calculate_all_metrics(views: int, likes: int, comments: int) -> dict:
    """
    Calculate all engagement metrics at once.
    Returns dict with all calculated values.
    """
    views = views or 0
    likes = likes or 0
    comments = comments or 0

    total_engagement = calculate_total_engagement(likes, comments)
    engagement_rate = calculate_engagement_rate(views, likes, comments)
    like_rate = calculate_like_rate(views, likes)
    comment_rate = calculate_comment_rate(views, comments)

    return {
        'total_engagement': total_engagement,
        'engagement_rate': engagement_rate,
        'like_rate': like_rate,
        'comment_rate': comment_rate,
    }


def calculate_channel_metrics(videos: list) -> dict:
    """
    Calculate channel-level metrics from a list of videos.
    Each video should have: views, likes, comments, engagement_rate
    """
    if not videos:
        return {
            'total_videos': 0,
            'total_views': 0,
            'total_likes': 0,
            'total_comments': 0,
            'average_engagement_rate': Decimal('0'),
            'overall_engagement_rate': Decimal('0'),
            'highest_engagement_video': None,
            'lowest_engagement_video': None,
            'most_viewed_video': None,
        }

    total_views = sum(v.get('views', 0) for v in videos)
    total_likes = sum(v.get('likes', 0) for v in videos)
    total_comments = sum(v.get('comments', 0) for v in videos)

    engagement_rates = [v.get('engagement_rate', Decimal('0')) for v in videos]
    average_engagement_rate = sum(engagement_rates, Decimal('0')) / len(engagement_rates)

    overall_engagement_rate = Decimal('0')
    if total_views > 0:
        overall_engagement_rate = ((Decimal(str(total_likes + total_comments)) / Decimal(str(total_views))) * Decimal('100')).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

    highest = max(videos, key=lambda v: v.get('engagement_rate', Decimal('0')))
    lowest = min(videos, key=lambda v: v.get('engagement_rate', Decimal('0')))
    most_viewed = max(videos, key=lambda v: v.get('views', 0))

    return {
        'total_videos': len(videos),
        'total_views': total_views,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'average_engagement_rate': average_engagement_rate.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP),
        'overall_engagement_rate': overall_engagement_rate,
        'highest_engagement_video': highest,
        'lowest_engagement_video': lowest,
        'most_viewed_video': most_viewed,
    }