# EngageRate

A Django-based web application for analyzing YouTube video and channel engagement metrics using the YouTube Data API v3.

## Features

- **Video Analysis** — Enter a YouTube video URL to get detailed engagement metrics
- **Channel Analysis** — Analyze an entire channel's video performance
- **Interactive Dashboard** — Visualizations using Chart.js (bar, scatter, doughnut, line charts)
- **Engagement Metrics** — Calculates engagement rate, like rate, comment rate, and total engagement
- **Channel-Level Analytics** — Average video ER, overall channel ER, top/bottom performing videos
- **Analysis History** — View and revisit previous analyses
- **Rule-Based Insights** — Automatic observations based on calculated metrics
- **Dark/Light Theme** — User preference with localStorage persistence
- **Responsive Design** — Works on desktop and mobile

## Technology Stack

- **Backend:** Python 3.11+, Django 5.x
- **Database:** PostgreSQL
- **API:** YouTube Data API v3 (google-api-python-client)
- **Frontend:** HTML, CSS, Bootstrap 5, JavaScript
- **Visualization:** Chart.js
- **Configuration:** python-dotenv (.env files)

## Installation

```bash
# Clone repository
git clone <repository>
cd EngageRate

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE social_engagement_db;"
psql -U postgres -c "CREATE USER social_admin WITH PASSWORD 'your_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE social_engagement_db TO social_admin;"

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## YouTube API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **YouTube Data API v3**
4. Create credentials → **API Key**
5. Add the API key to `.env`:
   ```
   YOUTUBE_API_KEY=your_api_key_here
   ```

## Usage

### Analyze a Video
1. Navigate to `/video/`
2. Enter a YouTube video URL (supports `youtube.com/watch?v=...`, `youtu.be/...`, embed URLs, or just the video ID)
3. Click "Analyze Video"

### Analyze a Channel
1. Navigate to `/channel/`
2. Enter a YouTube channel URL (handles `@handle`, `/c/custom`, `/channel/ID`, `/user/username`)
3. Set maximum videos to analyze (1-100)
3. Click "Analyze Channel"

### View Dashboards
- **Video Dashboard** — `/dashboard/videos/` — Individual video performance
- **Channel Dashboard** — `/dashboard/channels/` — Channel-level analytics
- **Global Dashboard** — `/dashboard/` — Overall overview

## Engagement Formulas

### Video-Level
```
Total Engagement = Likes + Comments
Engagement Rate = (Total Engagement / Views) × 100
Like Rate = (Likes / Views) × 100
Comment Rate = (Comments / Views) × 100
```

### Channel-Level
```
Average Video ER = Σ(Individual Video ER) / Number of Videos
Overall Channel ER = (Total Likes + Total Comments) / Total Views × 100
```

## Project Structure

```
EngageRate/
├── config/                 # Django project settings
├── analytics/              # Main Django app
│   ├── models.py          # Channel, Video, EngagementAnalysis
├── templates/             # HTML templates
├── static/                # Static assets
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
└── manage.py
```

## Testing

```bash
python manage.py test analytics
```

## License

Academic project - educational use only.