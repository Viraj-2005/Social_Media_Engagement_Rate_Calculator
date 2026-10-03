from django.contrib import admin
from .models import Channel, Video, EngagementAnalysis


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ['channel_name', 'channel_id', 'subscriber_count', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['channel_name', 'channel_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'channel', 'video_id', 'views', 'likes', 'comments', 'published_at', 'fetched_at']
    list_filter = ['channel', 'published_at', 'fetched_at', 'created_at']
    search_fields = ['title', 'video_id', 'channel__channel_name']
    readonly_fields = ['created_at', 'updated_at', 'fetched_at']
    ordering = ['-fetched_at']
    list_select_related = ['channel']


@admin.register(EngagementAnalysis)
class EngagementAnalysisAdmin(admin.ModelAdmin):
    list_display = ['video', 'total_engagement', 'engagement_rate', 'like_rate', 'comment_rate', 'analyzed_at']
    list_filter = ['analyzed_at']
    search_fields = ['video__title', 'video__video_id']
    readonly_fields = ['analyzed_at']
    ordering = ['-analyzed_at']
    list_select_related = ['video', 'video__channel']