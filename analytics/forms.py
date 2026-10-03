from django import forms
from analytics.services.parsers import is_valid_video_url, is_valid_channel_url


class VideoAnalysisForm(forms.Form):
    video_url = forms.URLField(
        label='YouTube Video URL',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.youtube.com/watch?v=VIDEO_ID',
            'autocomplete': 'off',
        }),
        help_text='Enter a YouTube video URL (e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ)'
    )

    def clean_video_url(self):
        url = self.cleaned_data['video_url']
        if not is_valid_video_url(url):
            raise forms.ValidationError('Please enter a valid YouTube video URL.')
        return url


class ChannelAnalysisForm(forms.Form):
    channel_url = forms.URLField(
        label='YouTube Channel URL',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.youtube.com/@channelname or https://www.youtube.com/channel/CHANNEL_ID',
            'autocomplete': 'off',
        }),
        help_text='Enter a YouTube channel URL (e.g., https://www.youtube.com/@channelname)'
    )

    max_videos = forms.IntegerField(
        label='Maximum videos to analyze',
        initial=20,
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
        }),
        help_text='Limit the number of videos to analyze (1-100). Higher values use more API quota.'
    )

    def clean_channel_url(self):
        url = self.cleaned_data['channel_url']
        if not is_valid_channel_url(url):
            raise forms.ValidationError('Please enter a valid YouTube channel URL.')
        return url