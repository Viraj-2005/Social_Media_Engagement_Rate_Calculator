import os
import logging
from typing import Optional, List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings

logger = logging.getLogger(__name__)


class YouTubeAPIError(Exception):
    """Custom exception for YouTube API errors."""
    def __init__(self, message: str, code: Optional[int] = None, reason: Optional[str] = None):
        super().__init__(message)
        self.code = code
        self.reason = reason


class YouTubeAPIClient:
    """Client for YouTube Data API v3."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'YOUTUBE_API_KEY', None)
        if not self.api_key:
            raise YouTubeAPIError("YouTube API key not configured")
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def _handle_http_error(self, error: HttpError) -> YouTubeAPIError:
        """Convert HttpError to YouTubeAPIError with user-friendly message."""
        error_details = error.error_details
        reason = error_details[0].get('reason', 'unknown') if error_details else 'unknown'
        status_code = error.resp.status

        if status_code == 400:
            message = "Invalid request. Please check the URL and try again."
        elif status_code == 403:
            if reason == 'quotaExceeded':
                message = "YouTube API quota has been exceeded. Please try again later."
            elif reason == 'keyInvalid':
                message = "Invalid YouTube API key. Please check configuration."
            else:
                message = "Access denied. The video may be private or restricted."
        elif status_code == 404:
            message = "The requested video or channel was not found."
        elif status_code >= 500:
            message = "YouTube API is temporarily unavailable. Please try again later."
        else:
            message = f"YouTube API error: {reason}"

        logger.error(f"YouTube API error: {status_code} - {reason} - {message}")
        return YouTubeAPIError(message, code=status_code, reason=reason)

    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Fetch video details by video ID."""
        try:
            request = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            )
            response = request.execute()

            items = response.get('items', [])
            if not items:
                return None

            return items[0]

        except HttpError as e:
            raise self._handle_http_error(e)

    def get_videos_batch(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch multiple videos in a single request (max 50 IDs)."""
        if not video_ids:
            return []

        all_items = []
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i + 50]
            try:
                request = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(batch)
                )
                response = request.execute()
                all_items.extend(response.get('items', []))
            except HttpError as e:
                raise self._handle_http_error(e)

        return all_items

    def get_channel(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Fetch channel details by channel ID."""
        try:
            request = self.youtube.channels().list(
                part='snippet,statistics,contentDetails',
                id=channel_id
            )
            response = request.execute()

            items = response.get('items', [])
            if not items:
                return None

            return items[0]

        except HttpError as e:
            raise self._handle_http_error(e)

    def get_channel_by_handle(self, handle: str) -> Optional[Dict[str, Any]]:
        """Fetch channel by @handle using search."""
        try:
            request = self.youtube.search().list(
                part='snippet',
                q=handle,
                type='channel',
                maxResults=1
            )
            response = request.execute()

            items = response.get('items', [])
            if not items:
                return None

            channel_id = items[0]['id']['channelId']
            return self.get_channel(channel_id)

        except HttpError as e:
            raise self._handle_http_error(e)

    def get_uploads_playlist_id(self, channel_id: str) -> Optional[str]:
        """Get the uploads playlist ID for a channel."""
        channel = self.get_channel(channel_id)
        if not channel:
            return None
        return channel.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')

    def get_playlist_items(self, playlist_id: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Fetch video IDs from a playlist (e.g., uploads)."""
        try:
            all_items = []
            next_page_token = None

            while len(all_items) < max_results:
                request = self.youtube.playlistItems().list(
                    part='snippet,contentDetails',
                    playlistId=playlist_id,
                    maxResults=min(50, max_results - len(all_items)),
                    pageToken=next_page_token
                )
                response = request.execute()

                items = response.get('items', [])
                all_items.extend(items)

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            return all_items[:max_results]

        except HttpError as e:
            raise self._handle_http_error(e)

    def get_video_statistics(self, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch statistics for multiple videos, returns dict keyed by video_id."""
        videos = self.get_videos_batch(video_ids)
        return {v['id']: v for v in videos}


def parse_video_duration(duration: str) -> str:
    """Parse ISO 8601 duration (PT4M13S) to human readable format."""
    if not duration:
        return ''

    duration = duration.replace('PT', '')
    hours = ''
    minutes = ''
    seconds = ''

    if 'H' in duration:
        hours, duration = duration.split('H')
        hours = f"{hours}h "

    if 'M' in duration:
        minutes, duration = duration.split('M')
        minutes = f"{minutes}m "

    if 'S' in duration:
        seconds = duration.replace('S', '') + 's'

    return f"{hours}{minutes}{seconds}".strip()


def normalize_video_data(raw_video: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw YouTube API video response to our model fields."""
    snippet = raw_video.get('snippet', {})
    statistics = raw_video.get('statistics', {})
    content_details = raw_video.get('contentDetails', {})

    return {
        'video_id': raw_video.get('id'),
        'title': snippet.get('title', ''),
        'description': snippet.get('description', ''),
        'channel_id': snippet.get('channelId', ''),
        'channel_name': snippet.get('channelTitle', ''),
        'published_at': snippet.get('publishedAt'),
        'views': int(statistics.get('viewCount', 0)),
        'likes': int(statistics.get('likeCount', 0)),
        'comments': int(statistics.get('commentCount', 0)),
        'duration': parse_video_duration(content_details.get('duration', '')),
        'category': snippet.get('categoryId', ''),
    }


def normalize_channel_data(raw_channel: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw YouTube API channel response to our model fields."""
    snippet = raw_channel.get('snippet', {})
    statistics = raw_channel.get('statistics', {})

    return {
        'channel_id': raw_channel.get('id'),
        'channel_name': snippet.get('title', ''),
        'subscriber_count': int(statistics.get('subscriberCount', 0)) if statistics.get('subscriberCount') else None,
    }