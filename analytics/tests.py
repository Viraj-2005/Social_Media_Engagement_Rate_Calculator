from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

from analytics.models import Channel, Video, EngagementAnalysis
from analytics.forms import VideoAnalysisForm, ChannelAnalysisForm
from analytics.services.parsers import (
    extract_video_id,
    extract_channel_identifier,
    is_valid_video_url,
    is_valid_channel_url,
)
from analytics.services.calculator import (
    calculate_total_engagement,
    calculate_engagement_rate,
    calculate_like_rate,
    calculate_comment_rate,
    calculate_all_metrics,
    calculate_channel_metrics,
)


class ParserTests(TestCase):
    """Tests for URL parsing functions."""

    def test_extract_video_id_standard(self):
        url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        self.assertEqual(extract_video_id(url), 'dQw4w9WgXcQ')

    def test_extract_video_id_short(self):
        url = 'https://youtu.be/dQw4w9WgXcQ'
        self.assertEqual(extract_video_id(url), 'dQw4w9WgXcQ')

    def test_extract_video_id_embed(self):
        url = 'https://www.youtube.com/embed/dQw4w9WgXcQ'
        self.assertEqual(extract_video_id(url), 'dQw4w9WgXcQ')

    def test_extract_video_id_just_id(self):
        self.assertEqual(extract_video_id('dQw4w9WgXcQ'), 'dQw4w9WgXcQ')

    def test_extract_video_id_invalid(self):
        self.assertIsNone(extract_video_id('https://example.com'))
        self.assertIsNone(extract_video_id(''))
        self.assertIsNone(extract_video_id(None))

    def test_extract_channel_handle(self):
        url = 'https://www.youtube.com/@channelname'
        result = extract_channel_identifier(url)
        self.assertEqual(result, ('handle', 'channelname'))

    def test_extract_channel_custom(self):
        url = 'https://www.youtube.com/c/customname'
        result = extract_channel_identifier(url)
        self.assertEqual(result, ('custom', 'customname'))

    def test_extract_channel_id(self):
        url = 'https://www.youtube.com/channel/UC1234567890'
        result = extract_channel_identifier(url)
        self.assertEqual(result, ('channel_id', 'UC1234567890'))

    def test_extract_channel_username(self):
        url = 'https://www.youtube.com/user/username'
        result = extract_channel_identifier(url)
        self.assertEqual(result, ('username', 'username'))

    def test_is_valid_video_url(self):
        self.assertTrue(is_valid_video_url('https://www.youtube.com/watch?v=dQw4w9WgXcQ'))
        self.assertTrue(is_valid_video_url('https://youtu.be/dQw4w9WgXcQ'))
        self.assertFalse(is_valid_video_url('https://example.com'))
        self.assertFalse(is_valid_video_url(''))

    def test_is_valid_channel_url(self):
        self.assertTrue(is_valid_channel_url('https://www.youtube.com/@channelname'))
        self.assertTrue(is_valid_channel_url('https://www.youtube.com/channel/UC123'))
        self.assertFalse(is_valid_channel_url('https://example.com'))
        self.assertFalse(is_valid_channel_url(''))


class CalculatorTests(TestCase):
    """Tests for engagement calculation functions."""

    def test_calculate_total_engagement(self):
        self.assertEqual(calculate_total_engagement(100, 50), 150)
        self.assertEqual(calculate_total_engagement(0, 0), 0)
        self.assertEqual(calculate_total_engagement(None, 10), 10)
        self.assertEqual(calculate_total_engagement(10, None), 10)

    def test_calculate_engagement_rate_normal(self):
        result = calculate_engagement_rate(100000, 8000, 1200)
        self.assertEqual(result, Decimal('9.2000'))

    def test_calculate_engagement_rate_zero_views(self):
        result = calculate_engagement_rate(0, 100, 50)
        self.assertEqual(result, Decimal('0'))

    def test_calculate_engagement_rate_zero_engagement(self):
        result = calculate_engagement_rate(10000, 0, 0)
        self.assertEqual(result, Decimal('0'))

    def test_calculate_like_rate(self):
        result = calculate_like_rate(100000, 8000)
        self.assertEqual(result, Decimal('8.0000'))

    def test_calculate_like_rate_zero_views(self):
        result = calculate_like_rate(0, 100)
        self.assertEqual(result, Decimal('0'))

    def test_calculate_comment_rate(self):
        result = calculate_comment_rate(100000, 1200)
        self.assertEqual(result, Decimal('1.2000'))

    def test_calculate_all_metrics(self):
        result = calculate_all_metrics(100000, 8000, 1200)
        self.assertEqual(result['total_engagement'], 9200)
        self.assertEqual(result['engagement_rate'], Decimal('9.2000'))
        self.assertEqual(result['like_rate'], Decimal('8.0000'))
        self.assertEqual(result['comment_rate'], Decimal('1.2000'))

    def test_calculate_channel_metrics_empty(self):
        result = calculate_channel_metrics([])
        self.assertEqual(result['total_videos'], 0)
        self.assertEqual(result['average_engagement_rate'], Decimal('0'))
        self.assertEqual(result['overall_engagement_rate'], Decimal('0'))

    def test_calculate_channel_metrics_multiple(self):
        videos = [
            {'views': 100000, 'likes': 8000, 'comments': 1200, 'engagement_rate': Decimal('9.2000')},
            {'views': 50000, 'likes': 3000, 'comments': 500, 'engagement_rate': Decimal('7.0000')},
            {'views': 200000, 'likes': 15000, 'comments': 2000, 'engagement_rate': Decimal('8.5000')},
        ]
        result = calculate_channel_metrics(videos)
        self.assertEqual(result['total_videos'], 3)
        self.assertEqual(result['total_views'], 350000)
        self.assertEqual(result['total_likes'], 26000)
        self.assertEqual(result['total_comments'], 3700)
        # Average of 9.2, 7.0, 8.5 = 8.2333
        self.assertEqual(result['average_engagement_rate'], Decimal('8.2333'))
        # Overall: (26000 + 3700) / 350000 * 100 = 8.4857%
        self.assertEqual(result['overall_engagement_rate'], Decimal('8.4857'))


class ModelTests(TestCase):
    """Tests for database models."""

    def setUp(self):
        self.channel = Channel.objects.create(
            channel_id='UC1234567890',
            channel_name='Test Channel',
            subscriber_count=100000
        )
        self.video = Video.objects.create(
            video_id='dQw4w9WgXcQ',
            channel=self.channel,
            title='Test Video',
            views=100000,
            likes=8000,
            comments=1200
        )

    def test_channel_creation(self):
        self.assertEqual(self.channel.channel_name, 'Test Channel')
        self.assertEqual(self.channel.subscriber_count, 100000)
        self.assertTrue(self.channel.created_at)
        self.assertTrue(self.channel.updated_at)

    def test_video_creation(self):
        self.assertEqual(self.video.title, 'Test Video')
        self.assertEqual(self.video.channel, self.channel)
        self.assertEqual(self.video.views, 100000)

    def test_engagement_analysis_creation(self):
        analysis = EngagementAnalysis.objects.create(
            video=self.video,
            total_engagement=9200,
            engagement_rate=Decimal('9.2000'),
            like_rate=Decimal('8.0000'),
            comment_rate=Decimal('1.2000')
        )
        self.assertEqual(analysis.video, self.video)
        self.assertEqual(analysis.total_engagement, 9200)

    def test_video_channel_relationship(self):
        self.assertEqual(self.video.channel.channel_name, 'Test Channel')
        self.assertIn(self.video, self.channel.videos.all())


class ViewTests(TestCase):
    """Tests for Django views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_home_view(self):
        response = self.client.get(reverse('analytics:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EngageRate')

    def test_video_analysis_get(self):
        response = self.client.get(reverse('analytics:video_analysis'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analyze YouTube Video')

    def test_channel_analysis_get(self):
        response = self.client.get(reverse('analytics:channel_analysis'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analyze YouTube Channel')

    def test_dashboard_view(self):
        response = self.client.get(reverse('analytics:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_history_view(self):
        response = self.client.get(reverse('analytics:history'))
        self.assertEqual(response.status_code, 200)

    def test_video_analysis_post_invalid_url(self):
        response = self.client.post(reverse('analytics:video_analysis'), {'video_url': 'invalid'})
        self.assertEqual(response.status_code, 200)
        # Form should show error

    def test_unauthenticated_redirect(self):
        """Test that unauthenticated users are redirected to login."""
        self.client.logout()
        urls = [
            'analytics:video_analysis',
            'analytics:channel_analysis',
            'analytics:dashboard',
            'analytics:history',
        ]
        for url_name in urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login/', response.url)


class YouTubeAPIMockTests(TestCase):
    """Tests with mocked YouTube API."""

    @patch('analytics.views.youtube_api.YouTubeAPIClient')
    def test_analyze_video_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_video.return_value = {
            'id': 'dQw4w9WgXcQ',
            'snippet': {
                'title': 'Test Video',
                'description': 'Test description',
                'channelId': 'UC123',
                'channelTitle': 'Test Channel',
                'publishedAt': '2024-01-01T00:00:00Z',
                'categoryId': '24'
            },
            'statistics': {
                'viewCount': '100000',
                'likeCount': '8000',
                'commentCount': '1200'
            },
            'contentDetails': {
                'duration': 'PT4M13S'
            }
        }

        from analytics.views import analyze_video
        video = analyze_video('dQw4w9WgXcQ')

        self.assertEqual(video.video_id, 'dQw4w9WgXcQ')
        self.assertEqual(video.title, 'Test Video')
        self.assertEqual(video.views, 100000)
        self.assertEqual(video.likes, 8000)
        self.assertEqual(video.comments, 1200)

        # Check engagement analysis was created
        analysis = video.engagement_analysis
        self.assertEqual(analysis.total_engagement, 9200)
        self.assertEqual(analysis.engagement_rate, Decimal('9.2000'))


class FormTests(TestCase):
    """Tests for Django forms."""

    def test_video_form_valid(self):
        form = VideoAnalysisForm(data={'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'})
        self.assertTrue(form.is_valid())

    def test_video_form_invalid(self):
        form = VideoAnalysisForm(data={'video_url': 'https://example.com'})
        self.assertFalse(form.is_valid())

    def test_channel_form_valid(self):
        form = ChannelAnalysisForm(data={'channel_url': 'https://www.youtube.com/@channelname', 'max_videos': 20})
        self.assertTrue(form.is_valid())

    def test_channel_form_invalid(self):
        form = ChannelAnalysisForm(data={'channel_url': 'https://example.com', 'max_videos': 20})
        self.assertFalse(form.is_valid())