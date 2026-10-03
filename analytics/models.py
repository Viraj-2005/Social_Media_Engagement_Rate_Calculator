from django.db import models


class Channel(models.Model):
    channel_id = models.CharField(max_length=255, unique=True, db_index=True)
    channel_name = models.CharField(max_length=500)
    subscriber_count = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.channel_name


class Video(models.Model):
    video_id = models.CharField(max_length=255, unique=True, db_index=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, default='')
    published_at = models.DateTimeField(null=True, blank=True)
    views = models.BigIntegerField(default=0)
    likes = models.BigIntegerField(default=0)
    comments = models.BigIntegerField(default=0)
    duration = models.CharField(max_length=50, blank=True, default='')
    category = models.CharField(max_length=100, blank=True, default='')
    fetched_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['channel', 'published_at']),
        ]

    def __str__(self):
        return self.title


class EngagementAnalysis(models.Model):
    video = models.OneToOneField(Video, on_delete=models.CASCADE, related_name='engagement_analysis')
    total_engagement = models.BigIntegerField(default=0)
    engagement_rate = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    like_rate = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    comment_rate = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    analyzed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-analyzed_at']

    def __str__(self):
        return f"Analysis for {self.video.title}"