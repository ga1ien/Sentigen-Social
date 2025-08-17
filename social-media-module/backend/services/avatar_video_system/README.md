# 🎬 Avatar Video Generation System

A comprehensive, production-ready system for creating professional avatar videos from research content using HeyGen's AI avatar technology. This system seamlessly integrates with all research tools (Reddit, Hacker News, GitHub, Google Trends) to automatically transform insights into engaging video content.

## 🎯 **Why Avatar Videos for Research Content?**

- **🎥 Professional Presentation**: Transform text insights into engaging video content
- **🤖 AI-Powered Avatars**: Realistic human presenters without filming costs
- **⚡ Automated Pipeline**: Research → Script → Video in minutes
- **📱 Multi-Format**: Portrait, landscape, square for all platforms
- **🌍 Scalable**: Generate hundreds of videos from research data
- **💰 Cost-Effective**: No video production team needed
- **🔄 Consistent Branding**: Same avatar across all content
- **📊 Data-Driven**: Content based on real research insights

## 🏗️ **System Architecture**

```
avatar-video-system/
├── 🤖 HeyGen API Integration     # Professional avatar video generation
├── 📊 Research Integration       # Automatic content extraction from all tools
├── 🎨 Avatar Management          # Multiple avatar profiles and styles
├── 🔄 Automated Campaigns        # Scheduled video generation from research
├── 🌐 REST API                   # Frontend integration endpoints
├── 📱 WebSocket Monitoring       # Real-time video generation status
├── 🎬 Video Templates            # Reusable video configurations
└── 📈 Analytics & Tracking       # Video performance metrics
```

## 🚀 **Key Features**

### **🤖 HeyGen Integration**
- **Professional Avatars**: Multiple avatar types (talking photos, 3D avatars)
- **Natural Voices**: High-quality text-to-speech with speed control
- **Multiple Formats**: Portrait (9:16), Landscape (16:9), Square (1:1)
- **Captions/Subtitles**: Automatic subtitle generation
- **Background Options**: Color, image, or video backgrounds
- **Real-time Status**: WebSocket monitoring of video generation

### **📊 Research Content Integration**
- **Automatic Extraction**: Smart content extraction from all research tools
- **Script Generation**: AI-powered script creation from research insights
- **Content Optimization**: Length and format optimization for video
- **Multi-Source Support**: Reddit, Hacker News, GitHub, Google Trends
- **Template System**: Customizable script templates per research tool
- **Quality Control**: Content validation and enhancement

### **🎨 Avatar Management**
- **Multiple Avatars**: Professional, casual, energetic styles
- **Subscription Tiers**: Free, Pro, Enterprise avatar access
- **Preview Videos**: See avatar in action before selection
- **Gender & Age Options**: Diverse avatar representation
- **Voice Matching**: Optimized voice-avatar combinations
- **Custom Branding**: Consistent avatar across campaigns

### **🔄 Automated Campaigns**
- **Research-Driven**: Automatically create videos from new research
- **Scheduling**: Daily, weekly, bi-weekly video generation
- **Content Filtering**: Quality thresholds and content rules
- **Multi-Platform**: Optimized for TikTok, Instagram, YouTube
- **Auto-Posting**: Direct publishing to social platforms (future)
- **Analytics Integration**: Track video performance

## 📋 **Database Schema**

### **Avatar Profiles**
```sql
CREATE TABLE avatar_profiles (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,           -- "Sarah", "Mike", "Emma"
    avatar_id VARCHAR(100) NOT NULL,      -- HeyGen avatar ID
    voice_id VARCHAR(100) NOT NULL,       -- HeyGen voice ID
    avatar_type VARCHAR(20),              -- 'talking_photo' or 'avatar'
    subscription_tier VARCHAR(20),        -- 'free', 'pro', 'enterprise'
    preview_url TEXT,                     -- Preview video URL
    is_active BOOLEAN DEFAULT TRUE
);
```

### **Video Generations**
```sql
CREATE TABLE video_generations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    workspace_id UUID REFERENCES workspaces(id),
    research_job_id UUID REFERENCES research_jobs(id),

    -- Content
    script_title VARCHAR(200),
    script_content TEXT NOT NULL,
    original_content JSONB,              -- Original research data

    -- Avatar settings
    profile_id UUID REFERENCES avatar_profiles(id),
    heygen_video_id VARCHAR(100),        -- HeyGen's video ID
    video_url TEXT,                      -- Final video URL

    -- Status
    status VARCHAR(20) DEFAULT 'processing',
    aspect_ratio VARCHAR(20) DEFAULT 'portrait',
    duration_seconds INTEGER,

    -- Analytics
    view_count INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

### **Video Campaigns**
```sql
CREATE TABLE video_campaigns (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    research_config_id UUID REFERENCES research_configurations(id),

    -- Automation settings
    is_active BOOLEAN DEFAULT TRUE,
    frequency VARCHAR(20) DEFAULT 'daily',
    max_videos_per_day INTEGER DEFAULT 3,

    -- Auto-posting
    auto_post_enabled BOOLEAN DEFAULT FALSE,
    post_platforms TEXT[] DEFAULT '{}',

    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    total_videos_generated INTEGER DEFAULT 0
);
```

## 🛠️ **Installation & Setup**

### **1. Install Dependencies**
```bash
# Install required packages
pip install aiohttp fastapi uvicorn structlog

# HeyGen integration is built-in (no additional packages needed)
```

### **2. Environment Configuration**
```bash
# Required: HeyGen API Key
export HEYGEN_API_KEY="your_heygen_api_key_here"

# Optional: Custom settings
export AVATAR_VIDEO_PORT=8008
export AVATAR_VIDEO_HOST=0.0.0.0
```

### **3. Database Migration**
```bash
# Apply avatar video system schema
psql -d your_database -f database/migrations/006_avatar_video_system.sql
```

### **4. Initialize Avatar Profiles**
The system comes with pre-configured avatar profiles:
- **Free Tier**: Sarah, Mike, Emma
- **Pro Tier**: David, Lisa, James
- **Enterprise**: Sophia, Alexander

## 🖥️ **API Usage**

### **Start the API Server**
```bash
cd services/avatar_video_system/api
python avatar_video_api.py
# API available at http://localhost:8008
```

### **API Endpoints**

#### **Avatar Management**
```bash
# List available avatars
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8008/avatars"

# Get specific avatar
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8008/avatars/{avatar_id}"
```

#### **Video Generation**
```bash
# Create video from script
curl -X POST "http://localhost:8008/videos" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_title": "AI Trends Analysis",
    "script_content": "Based on our research...",
    "avatar_profile_id": "avatar_id",
    "aspect_ratio": "portrait",
    "voice_speed": 1.0,
    "enable_captions": true
  }'

# Create video from research job
curl -X POST "http://localhost:8008/videos/from-research" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "research_job_id": "job_id",
    "avatar_profile_id": "avatar_id",
    "aspect_ratio": "portrait"
  }'

# Get video status
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8008/videos/{video_id}/status"

# List user videos
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8008/videos"
```

#### **Campaign Management**
```bash
# Create automated campaign
curl -X POST "http://localhost:8008/campaigns" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily AI Trends Videos",
    "research_config_id": "config_id",
    "source_tools": ["google_trends", "reddit"],
    "frequency": "daily",
    "max_videos_per_day": 3,
    "auto_post_enabled": false
  }'
```

## 🔄 **Research Integration**

### **Automatic Content Extraction**
The system automatically extracts content from research tools:

```python
# Reddit Research → Video Script
reddit_insights = [
    "AI automation tools showing 300% growth",
    "ChatGPT discussions dominate productivity subreddits",
    "Remote work tools gaining massive traction"
]

# Generated Script:
"""
Based on our latest Reddit research, here are the key insights:

1. AI automation tools showing 300% growth
2. ChatGPT discussions dominate productivity subreddits
3. Remote work tools gaining massive traction

These trends represent significant opportunities for content creators...
"""
```

### **Multi-Source Content**
```python
# Create video from any research tool
video_id = await create_video_from_research_job(
    research_job_id="job_123",
    avatar_profile_id="sarah_avatar",
    aspect_ratio=AspectRatio.PORTRAIT
)
```

### **Batch Processing**
```python
# Process all recent research jobs
results = await batch_create_videos_from_research(
    hours_back=24,
    avatar_profile_id="default_avatar"
)

print(f"Created {results['videos_created']} videos from {results['total_jobs_processed']} research jobs")
```

## 🎨 **Frontend Integration**

### **Avatar Selection UI**
The system includes a complete frontend interface:

- **Avatar Carousel**: Visual avatar selection with previews
- **Script Editor**: Rich text editor with character counting
- **Video Settings**: Aspect ratio, voice speed, captions
- **Real-time Status**: WebSocket-powered progress updates
- **Video Player**: Embedded player with download/share options

### **WebSocket Integration**
```javascript
// Real-time video status updates
const ws = new WebSocket(`ws://localhost:8008/videos/${videoId}/status-ws`);

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.status === 'completed') {
        displayVideo(data.video_url);
    } else if (data.status === 'failed') {
        showError(data.error_message);
    }
};
```

### **Research Integration UI**
```javascript
// Load recent research jobs for video creation
async function loadResearchJobs() {
    const response = await fetch('/api/research/jobs?status=completed');
    const jobs = await response.json();

    // Display jobs for selection
    renderResearchJobs(jobs);
}

// Create video from selected research
async function createVideoFromResearch(jobId) {
    const response = await fetch('/api/avatar-video/videos/from-research', {
        method: 'POST',
        body: JSON.stringify({
            research_job_id: jobId,
            avatar_profile_id: selectedAvatarId
        })
    });

    const result = await response.json();
    monitorVideoStatus(result.video_id);
}
```

## 🔄 **Automated Campaigns**

### **Campaign Configuration**
```python
# Create campaign that generates videos from Google Trends research
campaign_config = {
    "name": "Daily Trends Videos",
    "research_config_id": "trends_config_123",
    "source_tools": ["google_trends"],
    "avatar_profile_id": "sarah_avatar",
    "frequency": "daily",
    "max_videos_per_day": 2,
    "auto_post_enabled": True,
    "post_platforms": ["tiktok", "instagram"]
}

campaign_id = await avatar_video_service.create_automated_video_campaign(
    user_id, workspace_id, campaign_config
)
```

### **Campaign Processing**
```python
# Process all active campaigns (run by scheduler)
await avatar_video_service.process_video_campaigns()

# This will:
# 1. Find campaigns ready to run
# 2. Get recent research results
# 3. Create videos from top insights
# 4. Schedule next run
# 5. Optionally auto-post to social platforms
```

## 📊 **Content Extraction Rules**

### **Customizable Extraction**
Each research tool has specific extraction rules:

```python
reddit_rule = ContentExtractionRule(
    source_tool="reddit",
    content_paths=[
        "analysis.actionable_recommendations",
        "analysis.key_insights",
        "analysis.trending_topics"
    ],
    title_template="Reddit Research Insights - {topic}",
    script_template="""
    Based on our latest Reddit research, here are the key insights:

    {content}

    These trends represent significant opportunities...
    """,
    min_content_length=150,
    max_content_length=1800
)
```

### **Smart Content Formatting**
```python
# Automatically formats research data into video scripts
extracted_content = [
    "AI automation tools showing 300% growth",
    "ChatGPT discussions dominate productivity subreddits",
    "Remote work tools gaining massive traction"
]

# Becomes:
formatted_script = """
1. AI automation tools showing 300% growth.

2. ChatGPT discussions dominate productivity subreddits.

3. Remote work tools gaining massive traction.
"""
```

## 🎬 **Video Templates**

### **Template System**
```sql
-- Reusable video configurations
INSERT INTO video_templates (name, description, aspect_ratio, background_settings) VALUES
('Social Media Portrait', 'Optimized for TikTok/Instagram', 'portrait', '{"type": "color", "value": "#ffffff"}'),
('YouTube Landscape', 'Professional YouTube format', 'landscape', '{"type": "gradient", "colors": ["#667eea", "#764ba2"]}'),
('Square Social', 'Instagram/Facebook square format', 'square', '{"type": "color", "value": "#f8f9fa"}');
```

### **Template Usage**
```python
# Apply template to video generation
config = VideoGenerationConfig(
    avatar_profile_id="sarah_avatar",
    template_id="social_media_portrait",
    voice_speed=1.1,
    enable_captions=True
)
```

## 📈 **Analytics & Monitoring**

### **Video Analytics**
```sql
-- Track video performance
CREATE TABLE video_analytics (
    id UUID PRIMARY KEY,
    video_id UUID REFERENCES video_generations(id),
    event_type VARCHAR(50),  -- 'view', 'download', 'share'
    platform VARCHAR(50),    -- 'tiktok', 'instagram', 'youtube'
    event_timestamp TIMESTAMP DEFAULT NOW()
);
```

### **Performance Tracking**
```python
# Track video events
await track_video_event(
    video_id="video_123",
    event_type="view",
    platform="tiktok",
    user_id="user_456"
)

# Get video analytics
analytics = await get_video_analytics(video_id)
print(f"Views: {analytics['views']}, Downloads: {analytics['downloads']}")
```

## 🔒 **Security & Permissions**

### **Row Level Security**
```sql
-- Users can only access their own videos
CREATE POLICY video_generations_user ON video_generations FOR ALL USING (
    user_id = auth.uid() OR
    EXISTS (
        SELECT 1 FROM workspace_members
        WHERE workspace_members.workspace_id = video_generations.workspace_id
        AND workspace_members.user_id = auth.uid()
    )
);
```

### **Subscription-Based Access**
```python
# Avatar access based on subscription tier
def get_available_avatars(user_subscription_tier):
    if user_subscription_tier == "free":
        return avatars.filter(subscription_tier="free")
    elif user_subscription_tier == "pro":
        return avatars.filter(subscription_tier__in=["free", "pro"])
    else:  # enterprise
        return avatars.all()
```

## 🚨 **Error Handling & Recovery**

### **Robust Error Handling**
```python
try:
    video_id = await create_video_from_research(request)
except HeyGenAPIError as e:
    if e.status_code == 429:  # Rate limit
        await asyncio.sleep(60)  # Wait and retry
        video_id = await create_video_from_research(request)
    else:
        raise HTTPException(status_code=500, detail=f"HeyGen API error: {e.message}")
except Exception as e:
    logger.error("Video creation failed", error=str(e))
    raise HTTPException(status_code=500, detail="Video creation failed")
```

### **Status Monitoring**
```python
# Automatic status polling with timeout
async def monitor_video_status(video_id: str):
    max_attempts = 120  # 10 minutes max
    attempt = 0

    while attempt < max_attempts:
        status = await get_video_status(video_id)

        if status in ["completed", "failed"]:
            break

        await asyncio.sleep(5)
        attempt += 1

    if attempt >= max_attempts:
        await update_video_status(video_id, "timeout")
```

## 🎯 **Use Cases**

### **1. Daily Content Creation**
```python
# Automated daily videos from trending topics
campaign = await create_campaign({
    "name": "Daily AI Trends",
    "research_config_id": "google_trends_ai",
    "frequency": "daily",
    "max_videos_per_day": 3,
    "avatar_profile_id": "professional_sarah"
})
```

### **2. Research Summaries**
```python
# Convert research reports into video summaries
video_id = await create_video_from_research_job(
    research_job_id="reddit_analysis_123",
    custom_title="Weekly Reddit AI Discussions",
    aspect_ratio=AspectRatio.LANDSCAPE  # For YouTube
)
```

### **3. Multi-Platform Content**
```python
# Create videos optimized for different platforms
platforms = [
    {"name": "TikTok", "ratio": AspectRatio.PORTRAIT, "speed": 1.2},
    {"name": "YouTube", "ratio": AspectRatio.LANDSCAPE, "speed": 1.0},
    {"name": "Instagram", "ratio": AspectRatio.SQUARE, "speed": 1.1}
]

for platform in platforms:
    video_id = await create_video_from_research(
        research_job_id="job_123",
        aspect_ratio=platform["ratio"],
        voice_speed=platform["speed"],
        title=f"{platform['name']} - AI Trends Analysis"
    )
```

### **4. Branded Content Series**
```python
# Consistent avatar across content series
series_config = VideoGenerationConfig(
    avatar_profile_id="brand_spokesperson",
    background_type="image",
    background_url="https://brand.com/background.jpg",
    enable_captions=True,
    voice_speed=1.0
)

# Generate series from multiple research sources
for source in ["reddit", "hackernews", "google_trends"]:
    video_id = await create_video_from_latest_research(
        user_id="brand_user",
        source_tool=source,
        config=series_config
    )
```

## 🔗 **Integration Examples**

### **Frontend Integration**
```html
<!-- Avatar Video Creation Component -->
<div id="avatar-video-creator">
    <div class="avatar-selection">
        <!-- Avatar carousel loaded via API -->
    </div>

    <div class="research-integration">
        <!-- Recent research jobs for video creation -->
    </div>

    <div class="video-settings">
        <!-- Aspect ratio, voice speed, captions -->
    </div>

    <div class="video-status">
        <!-- Real-time status via WebSocket -->
    </div>
</div>
```

### **Webhook Integration**
```python
# Webhook for video completion
@app.post("/webhooks/video-completed")
async def video_completed_webhook(video_data: dict):
    video_id = video_data["video_id"]
    video_url = video_data["video_url"]

    # Auto-post to social platforms
    if video_data.get("auto_post_enabled"):
        await post_to_social_platforms(video_url, video_data["platforms"])

    # Send notification to user
    await notify_user_video_ready(video_data["user_id"], video_id)

    return {"status": "processed"}
```

### **Scheduler Integration**
```python
# Daily campaign processing
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Process campaigns every hour
scheduler.add_job(
    avatar_video_service.process_video_campaigns,
    'interval',
    hours=1,
    id='process_video_campaigns'
)

# Cleanup old videos weekly
scheduler.add_job(
    cleanup_old_videos,
    'cron',
    day_of_week='sun',
    hour=2,
    id='cleanup_videos'
)

scheduler.start()
```

## 🎉 **Getting Started Checklist**

- [ ] **Environment Setup**: Set `HEYGEN_API_KEY` environment variable
- [ ] **Database Migration**: Apply `006_avatar_video_system.sql`
- [ ] **API Server**: Start avatar video API on port 8008
- [ ] **Test Avatar Access**: Verify avatar profiles are loaded
- [ ] **Test Video Creation**: Create test video from script
- [ ] **Research Integration**: Test video creation from research job
- [ ] **WebSocket Testing**: Verify real-time status updates
- [ ] **Campaign Setup**: Create automated video campaign
- [ ] **Frontend Integration**: Integrate avatar selection UI
- [ ] **Analytics Setup**: Configure video performance tracking

## 📚 **Additional Resources**

- **HeyGen API Documentation**: https://docs.heygen.com/
- **Avatar Management Guide**: `/docs/avatar-management.md`
- **Campaign Configuration**: `/docs/campaign-setup.md`
- **Frontend Integration**: `/docs/frontend-integration.md`
- **API Reference**: Available at `http://localhost:8008/docs` when server is running

---

**The Avatar Video Generation System transforms research insights into professional video content, enabling scalable, automated content creation with AI-powered avatars!** 🎬🚀
