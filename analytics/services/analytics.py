from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
from django.db.models import Avg, Sum, Max, Min, Count
from analytics.models import Video, EngagementAnalysis, Channel
from analytics.services.calculator import calculate_channel_metrics


def _published_at_key(video: Video) -> datetime:
    """Safe sort key for published_at (handles None / naive datetimes)."""
    ts = video.published_at
    if ts is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


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
    tooltips = []  # Full tooltip data for each bar

    for video in videos:
        try:
            er = video.engagement_analysis.engagement_rate
            views = video.views
            likes = video.likes
            comments = video.comments
            title = video.title
        except EngagementAnalysis.DoesNotExist:
            er = Decimal('0')
            views = video.views
            likes = video.likes
            comments = video.comments
            title = video.title
        
        # Short label for axis
        labels.append(video.title[:30] + ('...' if len(video.title) > 30 else ''))
        data.append(float(er))
        # Full tooltip data
        tooltips.append({
            'title': title,
            'engagement_rate': float(er),
            'views': views,
            'likes': likes,
            'comments': comments,
        })

    return {'labels': labels, 'data': data, 'tooltips': tooltips}


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
            'title': video.title,
            'views': video.views,
            'likes': video.likes,
            'comments': video.comments,
            'engagement_rate': er,
            'video_id': video.video_id,
        })
    return points


def get_chart_data_engagement_composition(videos: List[Video]) -> Dict[str, int]:
    """Prepare data for engagement composition doughnut chart (likes vs comments)."""
    total_likes = sum(v.likes for v in videos)
    total_comments = sum(v.comments for v in videos)
    total = total_likes + total_comments
    return {
        'labels': ['Likes', 'Comments'],
        'data': [total_likes, total_comments],
        'total': total,
    }


def get_chart_data_engagement_trend(videos: List[Video]) -> Dict[str, List]:
    """Prepare data for engagement trend line chart over time."""
    videos_sorted = sorted(videos, key=_published_at_key)
    labels = []
    data = []
    tooltips = []

    for video in videos_sorted:
        if video.published_at:
            labels.append(video.published_at.strftime('%Y-%m-%d'))
            try:
                er = float(video.engagement_analysis.engagement_rate)
                title = video.title
                views = video.views
            except EngagementAnalysis.DoesNotExist:
                er = 0
                title = video.title
                views = video.views
            data.append(er)
            tooltips.append({
                'title': title,
                'published_date': video.published_at.strftime('%Y-%m-%d'),
                'engagement_rate': er,
                'views': views,
            })

    return {'labels': labels, 'data': data, 'tooltips': tooltips}


def get_video_dashboard_data() -> Dict[str, Any]:
    """Get aggregated data for video-focused dashboard."""
    total_videos = Video.objects.count()
    
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
    
    # Top 5 videos by engagement rate
    top_videos = Video.objects.select_related('channel', 'engagement_analysis').order_by('-engagement_analysis__engagement_rate')[:5]
    top_videos_data = []
    for video in top_videos:
        try:
            er = float(video.engagement_analysis.engagement_rate)
        except EngagementAnalysis.DoesNotExist:
            er = 0
        top_videos_data.append({
            'video_id': video.video_id,
            'title': video.title,
            'channel_name': video.channel.channel_name,
            'channel_id': video.channel.channel_id,
            'views': video.views,
            'likes': video.likes,
            'comments': video.comments,
            'engagement_rate': er,
            'thumbnail_url': f"https://img.youtube.com/vi/{video.video_id}/mqdefault.jpg",
        })
    
    # Bottom 5 videos by engagement rate (minimum 100 views to filter noise)
    bottom_videos = Video.objects.select_related('channel', 'engagement_analysis').filter(views__gte=100).order_by('engagement_analysis__engagement_rate')[:5]
    bottom_videos_data = []
    for video in bottom_videos:
        try:
            er = float(video.engagement_analysis.engagement_rate)
        except EngagementAnalysis.DoesNotExist:
            er = 0
        bottom_videos_data.append({
            'video_id': video.video_id,
            'title': video.title,
            'channel_name': video.channel.channel_name,
            'channel_id': video.channel.channel_id,
            'views': video.views,
            'engagement_rate': er,
            'thumbnail_url': f"https://img.youtube.com/vi/{video.video_id}/mqdefault.jpg",
        })
    
    # Videos per category breakdown
    category_breakdown = Video.objects.exclude(category='').values('category').annotate(
        count=Count('id'),
        total_views=Sum('views'),
        avg_er=Avg('engagement_analysis__engagement_rate')
    ).order_by('-count')[:10]
    
    # Recent videos
    recent_videos = Video.objects.select_related('channel', 'engagement_analysis').order_by('-fetched_at')[:10]
    recent_videos_data = []
    for video in recent_videos:
        try:
            er = float(video.engagement_analysis.engagement_rate)
        except EngagementAnalysis.DoesNotExist:
            er = 0
        recent_videos_data.append({
            'video_id': video.video_id,
            'title': video.title,
            'channel_name': video.channel.channel_name,
            'channel_id': video.channel.channel_id,
            'views': video.views,
            'likes': video.likes,
            'comments': video.comments,
            'engagement_rate': er,
            'thumbnail_url': f"https://img.youtube.com/vi/{video.video_id}/mqdefault.jpg",
            'fetched_at': video.fetched_at,
        })
    
    total_views = agg['total_views'] or 0
    total_likes = agg['total_likes'] or 0
    total_comments = agg['total_comments'] or 0
    overall_er = Decimal('0')
    if total_views > 0:
        overall_er = (Decimal(str(total_likes + total_comments)) / Decimal(str(total_views)) * Decimal('100')).quantize(Decimal('0.0001'))
    
    return {
        'total_videos': Video.objects.count(),
        'total_views': total_views,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'average_engagement_rate': EngagementAnalysis.objects.aggregate(avg_er=Avg('engagement_rate'))['avg_er'] or Decimal('0'),
        'overall_engagement_rate': overall_er,
        'top_videos': top_videos_data,
        'bottom_videos': bottom_videos_data,
        'category_breakdown': list(category_breakdown),
        'recent_videos': recent_videos_data,
    }


def get_channel_dashboard_data() -> Dict[str, Any]:
    """Get aggregated data for channel-focused dashboard."""
    total_channels = Channel.objects.count()
    
    # Channels with subscriber count
    channels_with_subs = Channel.objects.exclude(subscriber_count__isnull=True).exclude(subscriber_count=0)
    total_subscribers = channels_with_subs.aggregate(total=Sum('subscriber_count'))['total'] or 0
    
    # Aggregate video stats across all channels
    video_agg = Video.objects.aggregate(
        total_views=Sum('views'),
        total_likes=Sum('likes'),
        total_comments=Sum('comments'),
    )
    
    total_views = video_agg['total_views'] or 0
    total_likes = video_agg['total_likes'] or 0
    total_comments = video_agg['total_comments'] or 0
    
    overall_er = Decimal('0')
    total_engagement = total_likes + total_comments
    if total_views > 0:
        overall_er = (Decimal(str(total_engagement)) / Decimal(str(total_views)) * Decimal('100')).quantize(Decimal('0.0001'))
    
    # Channel-level metrics
    channels_data = []
    for channel in Channel.objects.all():
        videos = channel.videos.all()
        video_count = videos.count()
        if video_count == 0:
            continue
            
        ch_agg = videos.aggregate(
            total_views=Sum('views'),
            total_likes=Sum('likes'),
            total_comments=Sum('comments'),
        )
        ch_views = ch_agg['total_views'] or 0
        ch_likes = ch_agg['total_likes'] or 0
        ch_comments = ch_agg['total_comments'] or 0
        
        ch_er = Decimal('0')
        if ch_views > 0:
            ch_er = (Decimal(str(ch_likes + ch_comments)) / Decimal(str(ch_views)) * Decimal('100')).quantize(Decimal('0.0001'))
        
        # Average video ER for this channel
        avg_video_er = videos.filter(engagement_analysis__isnull=False).aggregate(
            avg_er=Avg('engagement_analysis__engagement_rate')
        )['avg_er'] or Decimal('0')
        
        channels_data.append({
            'channel_id': channel.channel_id,
            'channel_name': channel.channel_name,
            'subscriber_count': channel.subscriber_count,
            'video_count': video_count,
            'total_views': ch_views,
            'total_likes': ch_likes,
            'total_comments': ch_comments,
            'overall_engagement_rate': ch_er,
            'average_video_engagement_rate': avg_video_er,
        })
    
    # Sort channels by subscriber count (descending)
    channels_data.sort(key=lambda x: x['subscriber_count'] or 0, reverse=True)
    
    # Top 5 channels by engagement rate
    top_channels_by_er = sorted(
        [c for c in channels_data if c['video_count'] > 0],
        key=lambda x: x['overall_engagement_rate'],
        reverse=True
    )[:5]
    
    # Top 5 channels by subscriber count
    top_channels_by_subs = sorted(
        [c for c in channels_data if c['subscriber_count']],
        key=lambda x: x['subscriber_count'] or 0,
        reverse=True
    )[:5]
    
    # Videos per channel breakdown
    videos_per_channel = []
    for channel in channels_data:
        if channel['video_count'] > 0:
            videos_per_channel.append({
                'channel_name': channel['channel_name'],
                'video_count': channel['video_count'],
            })
    videos_per_channel.sort(key=lambda x: x['video_count'], reverse=True)
    
    return {
        'total_channels': total_channels,
        'total_subscribers': total_subscribers,
        'total_videos': Video.objects.count(),
        'total_views': total_views,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'overall_engagement_rate': overall_er,
        'channels': channels_data,
        'top_channels_by_er': top_channels_by_er,
        'top_channels_by_subs': top_channels_by_subs,
        'videos_per_channel': videos_per_channel[:10],
    }