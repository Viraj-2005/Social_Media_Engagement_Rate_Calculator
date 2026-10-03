from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from analytics.forms import VideoAnalysisForm, ChannelAnalysisForm
from analytics.models import Channel, Video, EngagementAnalysis
from analytics.services import youtube_api, calculator, analytics as analytics_service, insights
from analytics.services.parsers import extract_video_id, extract_channel_identifier
import logging

logger = logging.getLogger(__name__)


def home(request):
    """Home page with project introduction and analysis options."""
    return render(request, 'home.html')


def video_analysis(request):
    """Handle video URL submission and display results."""
    form = VideoAnalysisForm()

    if request.method == 'POST':
        form = VideoAnalysisForm(request.POST)
        if form.is_valid():
            video_url = form.cleaned_data['video_url']
            video_id = extract_video_id(video_url)

            try:
                video = analyze_video(video_id)
                return redirect('analytics:dashboard')
            except youtube_api.YouTubeAPIError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.exception("Error analyzing video")
                messages.error(request, 'An unexpected error occurred. Please try again.')

    return render(request, 'video_analysis.html', {'form': form})


def channel_analysis(request):
    """Handle channel URL submission and display results."""
    form = ChannelAnalysisForm()

    if request.method == 'POST':
        form = ChannelAnalysisForm(request.POST)
        if form.is_valid():
            channel_url = form.cleaned_data['channel_url']
            max_videos = form.cleaned_data['max_videos']
            identifier = extract_channel_identifier(channel_url)

            try:
                channel = analyze_channel(identifier, max_videos)
                return redirect('analytics:dashboard')
            except youtube_api.YouTubeAPIError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.exception("Error analyzing channel")
                messages.error(request, 'An unexpected error occurred. Please try again.')

    return render(request, 'channel_analysis.html', {'form': form})


def analyze_video(video_id: str) -> Video:
    """Fetch video data from YouTube API, store in DB, calculate metrics."""
    client = youtube_api.YouTubeAPIClient()
    raw_video = client.get_video(video_id)

    if not raw_video:
        raise youtube_api.YouTubeAPIError("Video not found or unavailable.")

    video_data = youtube_api.normalize_video_data(raw_video)

    with transaction.atomic():
        channel, _ = Channel.objects.update_or_create(
            channel_id=video_data['channel_id'],
            defaults={
                'channel_name': video_data['channel_name'],
            }
        )

        video, created = Video.objects.update_or_create(
            video_id=video_data['video_id'],
            defaults={
                'channel': channel,
                'title': video_data['title'],
                'description': video_data['description'],
                'published_at': video_data['published_at'],
                'views': video_data['views'],
                'likes': video_data['likes'],
                'comments': video_data['comments'],
                'duration': video_data['duration'],
                'category': video_data['category'],
            }
        )

        metrics = calculator.calculate_all_metrics(
            video.views, video.likes, video.comments
        )

        EngagementAnalysis.objects.update_or_create(
            video=video,
            defaults=metrics
        )

    return video


def analyze_channel(identifier: tuple, max_videos: int = 20) -> Channel:
    """Fetch channel data and videos from YouTube API, store in DB, calculate metrics."""
    client = youtube_api.YouTubeAPIClient()
    id_type, id_value = identifier

    if id_type == 'handle':
        raw_channel = client.get_channel_by_handle(id_value)
    elif id_type == 'channel_id':
        raw_channel = client.get_channel(id_value)
    elif id_type == 'custom':
        raw_channel = client.get_channel_by_handle(id_value)
    elif id_type == 'username':
        raw_channel = client.get_channel_by_handle(id_value)
    else:
        raise youtube_api.YouTubeAPIError("Unable to identify channel type.")

    if not raw_channel:
        raise youtube_api.YouTubeAPIError("Channel not found or unavailable.")

    channel_data = youtube_api.normalize_channel_data(raw_channel)
    channel_id = channel_data['channel_id']

    uploads_playlist_id = client.get_uploads_playlist_id(channel_id)
    if not uploads_playlist_id:
        raise youtube_api.YouTubeAPIError("Could not retrieve channel uploads playlist.")

    playlist_items = client.get_playlist_items(uploads_playlist_id, max_results=max_videos)
    video_ids = [item['contentDetails']['videoId'] for item in playlist_items]

    if not video_ids:
        raise youtube_api.YouTubeAPIError("No videos found in channel uploads.")

    video_stats = client.get_video_statistics(video_ids)

    with transaction.atomic():
        channel, _ = Channel.objects.update_or_create(
            channel_id=channel_data['channel_id'],
            defaults={
                'channel_name': channel_data['channel_name'],
                'subscriber_count': channel_data['subscriber_count'],
            }
        )

        for item in playlist_items:
            video_id = item['contentDetails']['videoId']
            snippet = item['snippet']
            raw_vid = video_stats.get(video_id)

            if not raw_vid:
                continue

            video_data = youtube_api.normalize_video_data(raw_vid)
            video_data['title'] = snippet.get('title', video_data['title'])
            video_data['description'] = snippet.get('description', video_data['description'])
            video_data['published_at'] = snippet.get('publishedAt', video_data['published_at'])

            video, _ = Video.objects.update_or_create(
                video_id=video_data['video_id'],
                defaults={
                    'channel': channel,
                    'title': video_data['title'],
                    'description': video_data['description'],
                    'published_at': video_data['published_at'],
                    'views': video_data['views'],
                    'likes': video_data['likes'],
                    'comments': video_data['comments'],
                    'duration': video_data['duration'],
                    'category': video_data['category'],
                }
            )

            metrics = calculator.calculate_all_metrics(
                video.views, video.likes, video.comments
            )

            EngagementAnalysis.objects.update_or_create(
                video=video,
                defaults=metrics
            )

    return channel


def dashboard(request):
    """Main dashboard with summary cards and charts."""
    dashboard_data = analytics_service.get_dashboard_data()

    recent_videos = dashboard_data.get('recent_videos', [])

    chart_engagement = analytics_service.get_chart_data_engagement_by_video(recent_videos)
    chart_views_vs_engagement = analytics_service.get_chart_data_views_vs_engagement(recent_videos)
    chart_composition = analytics_service.get_chart_data_engagement_composition(recent_videos)
    chart_trend = analytics_service.get_chart_data_engagement_trend(recent_videos)

    context = {
        'dashboard_data': dashboard_data,
        'chart_engagement': chart_engagement,
        'chart_views_vs_engagement': chart_views_vs_engagement,
        'chart_composition': chart_composition,
        'chart_trend': chart_trend,
    }
    return render(request, 'dashboard.html', context)


def history(request):
    """History page showing previously analyzed videos."""
    videos = Video.objects.select_related('channel', 'engagement_analysis').order_by('-fetched_at')

    channel_filter = request.GET.get('channel')
    if channel_filter:
        videos = videos.filter(channel__channel_id=channel_filter)

    channels = Channel.objects.all().order_by('channel_name')

    context = {
        'videos': videos,
        'channels': channels,
        'selected_channel': channel_filter,
    }
    return render(request, 'history.html', context)


def video_detail(request, video_id):
    """Detail view for a single video analysis."""
    video = get_object_or_404(Video.objects.select_related('channel', 'engagement_analysis'), video_id=video_id)
    video_analytics = analytics_service.get_video_analytics(video)
    video_insights = insights.generate_video_insights(video)

    context = {
        'video': video,
        'analytics': video_analytics,
        'insights': video_insights,
    }
    return render(request, 'video_detail.html', context)


def channel_detail(request, channel_id):
    """Detail view for a channel analysis."""
    channel = get_object_or_404(Channel, channel_id=channel_id)
    channel_analytics = analytics_service.get_channel_analytics(channel)
    channel_insights = insights.generate_channel_insights(channel_analytics)

    context = {
        'channel': channel,
        'analytics': channel_analytics,
        'insights': channel_insights,
    }
    return render(request, 'channel_detail.html', context)