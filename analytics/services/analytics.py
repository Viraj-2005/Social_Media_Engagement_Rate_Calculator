from decimal import Decimal
from typing import List, Dict, Any, Optional
from django.db.models import Avg, Sum, Max, Min, Count
from analytics.models import Video, EngagementAnalysis, Channel
from analytics.services.calculator import calculate_channel_metrics


def get_video_analytics(video: Video) -> Dict[str, Any]:
    """Get analytics data for a single video."""
    try:
        analysis = video.engagement_analysis
        return {
            'video': video,
            'total_engagement': analysis.total_engagement,
            'engagement_rate': analysis.engagement_rate,
            'like_rate': analysis.like_rate,
            'comment_rate': analysis.comment_rate,
        }
    except EngagementAnalysis.DoesNotExist:
        return {
            'video': video,
            'total_engagement': 0,
            'engagement_rate': Decimal('0'),
            'like_rate': Decimal('0'),
            'comment_rate': Decimal('0'),
        }


def get_channel_analytics(channel: Channel, limit: Optional[int] = None) -> Dict[str, Any]:
    """Get aggregated analytics for a channel."""
    videos_qs = channel.videos.all().order_by('-published_at')
    if limit:
        videos_qs = videos_qs[:limit]

    videos_data = []
    for video in videos_qs:
        video_analytics = get_video_analytics(video)
        videos_data.append({
            'id': video.id,
            'video_id': video.video_id,
            'title': video.title,
            'published_at': video.published_at,
            'views': video.views,
            'likes': video.likes,
            'comments': video.comments,
            'engagement_rate': video_analytics['engagement_rate'],
            'thumbnail_url': f"https://img.youtube.com/vi/{video.video_id}/mqdefault.jpg",
        })

    metrics = calculate_channel_metrics(videos_data)

    return {
        'channel': channel,
        'videos': videos_data,
        **metrics,
    }


def get_dashboard_data() -> Dict[str, Any]:
    """Get aggregated data for the main dashboard."""
    total_videos = Video.objects.count()
    total_channels = Channel.objects.count()

    agg = Video.objects.aggregate(
        total_views=Sum('views'),
        total_likes=Sum('likes'),
        total_comments=Sum('comments'),
    )

    avg_er = EngagementAnalysis.objects.aggregate(avg_er=Avg('engagement_rate'))['avg_er'] or Decimal('0')

    total_views = agg['total_views'] or 0
    total_likes = agg['total_likes'] or 0
    total_comments = agg['total_comments'] or 0

    overall_er = Decimal('0')
    if total_views > 0:
        overall_er = (Decimal(str(total_likes + total_comments)) / Decimal(str(total_views)) * Decimal('100')).quantize(Decimal('0.0001'))

    recent_videos = Video.objects.select_related('channel', 'engagement_analysis').order_by('-fetched_at')[:10]

    return {
        'total_videos': total_videos,
        'total_channels': total_channels,
        'total_views': total_views,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'average_engagement_rate': avg_er,
        'overall_engagement_rate': overall_er,
        'recent_videos': recent_videos,
    }


def get_chart_data_engagement_by_video(videos: List[Video]) -> Dict[str, List]:
    """Prepare data for engagement rate by video bar chart."""
    labels = []
    data = []

    for video in videos:
        try:
            er = video.engagement_analysis.engagement_rate
        except EngagementAnalysis.DoesNotExist:
            er = Decimal('0')
        labels.append(video.title[:30] + ('...' if len(video.title) > 30 else ''))
        data.append(float(er))

    return {'labels': labels, 'data': data}


def get_chart_data_views_vs_engagement(videos: List[Video]) -> List[Dict[str, Any]]:
    """Prepare data for views vs engagement scatter plot."""
    points = []
    for video in videos:
        try:
            er = float(video.engagement_analysis.engagement_rate)
        except EngagementAnalysis.DoesNotExist:
            er = 0
        points.append({
            'x': video.views,
            'y': er,
            'label': video.title[:50],
            'video_id': video.video_id,
        })
    return points


def get_chart_data_engagement_composition(videos: List[Video]) -> Dict[str, int]:
    """Prepare data for engagement composition doughnut chart (likes vs comments)."""
    total_likes = sum(v.likes for v in videos)
    total_comments = sum(v.comments for v in videos)
    return {
        'labels': ['Likes', 'Comments'],
        'data': [total_likes, total_comments],
    }


def get_chart_data_engagement_trend(videos: List[Video]) -> Dict[str, List]:
    """Prepare data for engagement trend line chart over time."""
    videos_sorted = sorted(videos, key=lambda v: v.published_at or '')
    labels = []
    data = []

    for video in videos_sorted:
        if video.published_at:
            labels.append(video.published_at.strftime('%Y-%m-%d'))
            try:
                er = float(video.engagement_analysis.engagement_rate)
            except EngagementAnalysis.DoesNotExist:
                er = 0
            data.append(er)

    return {'labels': labels, 'data': data}