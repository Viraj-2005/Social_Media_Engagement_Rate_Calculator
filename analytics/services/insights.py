from decimal import Decimal
from typing import List, Dict, Any
from analytics.models import Video, EngagementAnalysis


def generate_video_insights(video: Video) -> List[str]:
    """Generate rule-based insights for a single video."""
    insights = []

    try:
        analysis = video.engagement_analysis
        er = analysis.engagement_rate
        like_rate = analysis.like_rate
        comment_rate = analysis.comment_rate
        total_engagement = analysis.total_engagement
    except EngagementAnalysis.DoesNotExist:
        return ["No engagement analysis available for this video."]

    views = video.views or 0
    likes = video.likes or 0
    comments = video.comments or 0

    if views == 0:
        insights.append("This video has no views yet.")
        return insights

    if er >= Decimal('10'):
        insights.append("This video shows exceptional audience interaction relative to its number of views.")
    elif er >= Decimal('5'):
        insights.append("This video shows strong audience interaction relative to its number of views.")
    elif er >= Decimal('2'):
        insights.append("This video has a healthy engagement rate for its view count.")
    elif er > Decimal('0'):
        insights.append("The video has relatively low engagement compared to its views.")
    else:
        insights.append("This video has no measurable engagement yet.")

    if comment_rate >= Decimal('1'):
        insights.append("The video is generating significant discussion through comments.")
    elif comment_rate >= Decimal('0.5'):
        insights.append("The video is generating a moderate amount of discussion through comments.")
    elif comments > 0:
        insights.append("The video has some comments but discussion is limited.")

    if like_rate >= Decimal('10'):
        insights.append("Viewers are highly appreciative, with a very high like rate.")
    elif like_rate >= Decimal('4'):
        insights.append("The video has a good like-to-view ratio.")
    elif likes > 0:
        insights.append("The video receives likes but at a modest rate.")

    if views >= 100000 and er < Decimal('2'):
        insights.append("The video has high reach but comparatively lower audience interaction.")

    if comments > 0 and likes > 0:
        ratio = comments / likes
        if ratio > 0.5:
            insights.append("The video has an unusually high comment-to-like ratio, suggesting controversial or highly engaging content.")
        elif ratio < 0.05:
            insights.append("The video has a low comment-to-like ratio, typical for entertainment content.")

    return insights


def generate_channel_insights(channel_data: Dict[str, Any]) -> List[str]:
    """Generate rule-based insights for a channel."""
    insights = []

    total_videos = channel_data.get('total_videos', 0)
    avg_er = channel_data.get('average_engagement_rate', Decimal('0'))
    overall_er = channel_data.get('overall_engagement_rate', Decimal('0'))
    videos = channel_data.get('videos', [])

    if total_videos == 0:
        return ["No videos analyzed for this channel yet."]

    if total_videos < 5:
        insights.append(f"Analysis based on {total_videos} video(s). Results may not be representative of the full channel.")
    else:
        insights.append(f"Analysis based on {total_videos} videos.")

    if avg_er >= Decimal('5'):
        insights.append("The channel maintains consistently high engagement across its videos.")
    elif avg_er >= Decimal('2'):
        insights.append("The channel has a healthy average engagement rate.")
    elif avg_er > Decimal('0'):
        insights.append("The channel's average engagement rate is relatively low.")
    else:
        insights.append("No engagement data available for analyzed videos.")

    if overall_er >= Decimal('5'):
        insights.append("Overall, the channel's content generates strong audience interaction.")
    elif overall_er > Decimal('0'):
        insights.append("The channel has moderate overall engagement.")

    if len(videos) >= 2:
        ers = [v.get('engagement_rate', Decimal('0')) for v in videos if v.get('engagement_rate') is not None]
        if ers:
            max_er = max(ers)
            min_er = min(ers)
            if max_er - min_er > Decimal('5'):
                insights.append("The channel's engagement varies significantly across its analyzed videos.")
            elif max_er - min_er > Decimal('2'):
                insights.append("The channel shows moderate variation in engagement across videos.")
            else:
                insights.append("The channel maintains consistent engagement across its videos.")

    highest = channel_data.get('highest_engagement_video')
    lowest = channel_data.get('lowest_engagement_video')
    most_viewed = channel_data.get('most_viewed_video')

    if highest and lowest and highest.get('video_id') != lowest.get('video_id'):
        insights.append(
            f"Highest engagement: '{highest.get('title', 'Unknown')[:40]}' "
            f"({highest.get('engagement_rate', 0):.2f}%) — "
            f"Lowest: '{lowest.get('title', 'Unknown')[:40]}' "
            f"({lowest.get('engagement_rate', 0):.2f}%)"
        )

    if most_viewed:
        insights.append(
            f"Most viewed video: '{most_viewed.get('title', 'Unknown')[:40]}' "
            f"({most_viewed.get('views', 0):,} views)"
        )

    return insights


def generate_comparison_insights(video1: Video, video2: Video) -> List[str]:
    """Generate insights comparing two videos."""
    insights = []

    try:
        a1 = video1.engagement_analysis
        a2 = video2.engagement_analysis
    except EngagementAnalysis.DoesNotExist:
        return ["Cannot compare - missing engagement analysis for one or both videos."]

    er1 = a1.engagement_rate
    er2 = a2.engagement_rate

    if er1 > er2:
        diff = ((er1 - er2) / er2 * 100).quantize(Decimal('0.01')) if er2 > 0 else Decimal('0')
        insights.append(f"'{video1.title[:40]}' has {diff}% higher engagement rate than '{video2.title[:40]}'.")
    elif er2 > er1:
        diff = ((er2 - er1) / er1 * 100).quantize(Decimal('0.01')) if er1 > 0 else Decimal('0')
        insights.append(f"'{video2.title[:40]}' has {diff}% higher engagement rate than '{video1.title[:40]}'.")
    else:
        insights.append("Both videos have similar engagement rates.")

    return insights