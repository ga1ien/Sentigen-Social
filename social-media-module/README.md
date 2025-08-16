# Social Media Posting Module

A comprehensive AI-powered social media posting module built with **Pydantic AI** and **Ayrshare API**. This module follows the development standards for agentic RAG systems and provides a complete solution for automated social media content creation and posting.

## 🚀 Features

- **AI-Powered Content Creation**: Uses Pydantic AI agents for intelligent social media posting
- **Multi-Platform Support**: Post to Twitter, Facebook, Instagram, LinkedIn, Bluesky, Pinterest, TikTok
- **Smart Content Optimization**: Platform-specific content optimization and suggestions
- **Real-time Streaming**: Server-sent events for real-time posting updates
- **Modern UI**: Beautiful React frontend with Tailwind CSS
- **Comprehensive API**: RESTful API with OpenAPI documentation
- **Health Monitoring**: Built-in health checks and status monitoring
- **Scheduling Support**: Schedule posts for future publication
- **Media Support**: Images, videos, and media URL handling
- **Analytics Ready**: Built-in analytics endpoints (expandable)

## 🏗️ Architecture

### Backend Stack
- **Python 3.11+** with FastAPI
- **Pydantic AI** for intelligent agent workflows
- **Ayrshare API** for social media posting
- **Structured Logging** with structlog
- **Async/Await** throughout for performance

### Frontend Stack
- **React 18** with modern hooks
- **Tailwind CSS** for styling
- **React Hook Form** for form management
- **Lucide React** for icons
- **React Hot Toast** for notifications

### Standards Compliance
- Follows **Sentigen Development Standards v1.0**
- Compatible with agentic RAG systems
- Structured agents with typed dependencies
- Centralized model configuration
- Comprehensive error handling

## 📋 Prerequisites

1. **Python 3.11+** installed
2. **Node.js 18+** and npm
3. **Ayrshare Account** with API key
4. **LLM API Key** (OpenAI, Anthropic, etc.)

## 🛠️ Installation

### 1. Clone and Setup

```bash
cd /Users/galenoakes/Development/Sentigen-Social/social-media-module
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 3. Configure Environment

Edit `backend/.env` with your API keys:

```bash
# Ayrshare API Configuration (REQUIRED)
AYRSHARE_API_KEY=BDC23994-98314AAC-95C290B5-7D894A53
AYRSHARE_BASE_URL=https://api.ayrshare.com/api

# OpenAI Configuration (Latest: GPT-5 Mini - Released August 7, 2025)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-5-mini

# Anthropic Configuration (Latest: Claude 4 Sonnet - Released May 2025)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-4-sonnet

# HeyGen Configuration (for video generation)
HEYGEN_API_KEY=your_heygen_api_key_here
HEYGEN_BASE_URL=https://api.heygen.com/v1

# Midjourney Configuration (for artistic images and videos via CometAPI)
COMETAPI_KEY=your_cometapi_key_here
COMETAPI_BASE_URL=https://api.cometapi.com
MIDJOURNEY_MODE=fast
MIDJOURNEY_VERSION=6.1

# Perplexity Configuration
PERPLEXITY_API_KEY=your_perplexity_api_key_here
PERPLEXITY_BASE_URL=https://api.perplexity.ai
PERPLEXITY_MODEL=llama-3.1-sonar-small-128k-online

# Primary LLM Configuration (choose your preferred provider)
LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key_here
LLM_CHOICE=gpt-5-mini
LLM_BASE_URL=https://api.openai.com/v1

# Application Configuration
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
```

### 4. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm start
```

### 5. Start Backend

```bash
cd ../backend

# Activate virtual environment if not already active
source venv/bin/activate

# Start the FastAPI server
python main.py
```

## 🔧 Configuration

### Ayrshare Setup

1. **Sign up** at [Ayrshare](https://ayrshare.com)
2. **Connect your social accounts** in the dashboard
3. **Get your API key** from the API Key page
4. **Add the API key** to your `.env` file

### LLM Provider Setup

The module supports multiple LLM providers. Set `LLM_PROVIDER` to choose your preferred provider:

#### OpenAI (Default) - GPT-5 Mini (Latest)
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-5-mini
```
*GPT-5 Mini released August 7, 2025 - Faster, cost-effective version with excellent performance for most tasks*

#### Anthropic - Claude 4 Sonnet (Latest)
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
ANTHROPIC_MODEL=claude-4-sonnet
```
*Claude 4 Sonnet released May 2025 - Balanced model with strong reasoning capabilities and faster response times*

#### Perplexity
```bash
LLM_PROVIDER=perplexity
PERPLEXITY_API_KEY=pplx-your-perplexity-key
PERPLEXITY_MODEL=llama-3.1-sonar-small-128k-online
```

#### HeyGen (Video Generation)
```bash
HEYGEN_API_KEY=your-heygen-api-key
```

#### Midjourney (Images & Videos via CometAPI)
```bash
COMETAPI_KEY=your-cometapi-key
MIDJOURNEY_MODE=fast
MIDJOURNEY_VERSION=6.1
```
*Get your CometAPI key from [CometAPI Dashboard](https://api.cometapi.com) - Provides access to Midjourney for both artistic images and image-to-video generation*

The system will automatically detect and use the appropriate provider based on your configuration.

## 🚀 Usage

### Web Interface

1. **Open your browser** to `http://localhost:3000`
2. **Check the status** in the Status tab to ensure Ayrshare is connected
3. **Create a post** in the Create Post tab:
   - Enter your content
   - Select target platforms
   - Add media URLs (optional)
   - Configure advanced options
   - Click "Create Post"

### API Usage

#### Create a Post

```bash
curl -X POST "http://localhost:8000/api/post" \
  -H "Content-Type: application/json" \
  -d '{
    "post": "Hello from the Social Media Module! 🚀",
    "platforms": ["twitter", "linkedin"],
    "mediaUrls": ["https://example.com/image.jpg"]
  }'
```

#### Health Check

```bash
curl "http://localhost:8000/health"
```

#### Get Connected Accounts

```bash
curl "http://localhost:8000/api/accounts"
```

### Python SDK Usage

```python
import asyncio
from agents.social_media_agent import SocialMediaAgent

async def main():
    # Initialize the agent
    agent = SocialMediaAgent(ayrshare_api_key="your-api-key")
    
    # Create a post
    result = await agent.post_content(
        prompt="Post 'Hello World!' to Twitter and LinkedIn",
        context="You are helping with a test post"
    )
    
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    print(f"Platform Results: {result.platform_results}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📚 API Documentation

### Endpoints

#### Social Media Posting
- **POST** `/api/post` - Create a social media post
- **POST** `/api/post/stream` - Create post with streaming response
- **GET** `/api/analytics/{post_id}` - Get post analytics
- **GET** `/api/accounts` - Get connected social media accounts
- **POST** `/api/optimize` - Optimize content for platforms

#### HeyGen Video Generation
- **POST** `/api/heygen/video` - Create a video with HeyGen
- **GET** `/api/heygen/video/{video_id}` - Get video generation status
- **GET** `/api/heygen/avatars` - List available avatars
- **GET** `/api/heygen/voices` - List available voices

#### Midjourney Image & Video Generation
- **POST** `/api/midjourney/image` - Generate artistic images with Midjourney
- **POST** `/api/midjourney/video` - Generate videos from images with Midjourney
- **GET** `/api/midjourney/task/{task_id}` - Get Midjourney task status
- **POST** `/api/midjourney/upscale/{task_id}` - Upscale a specific image (index 1-4)

#### System
- **GET** `/health` - Health check endpoint

### Interactive Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🧪 Testing

### Test with Random Content

Use the built-in test features:

```bash
curl -X POST "http://localhost:8000/api/post" \
  -H "Content-Type: application/json" \
  -d '{
    "randomPost": true,
    "randomMediaUrl": true,
    "platforms": ["twitter"]
  }'
```

### Frontend Testing

1. Check the "Use random test content" option
2. Check the "Use random test media" option
3. Select your connected platforms
4. Click "Create Post"

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Copy environment file
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Individual Containers

```bash
# Build and run backend
cd backend
docker build -t social-media-backend .
docker run -p 8000:8000 --env-file .env social-media-backend

# Build and run frontend
cd ../frontend
docker build -t social-media-frontend .
docker run -p 3000:3000 social-media-frontend
```

## 🔍 Monitoring and Debugging

### Health Checks

The application provides comprehensive health monitoring:

- **API Health**: `/health` endpoint
- **Ayrshare Connection**: Automatic connection testing
- **Frontend Status**: Real-time status display

### Logging

Structured logging is enabled by default:

```bash
# View backend logs
tail -f backend/logs/app.log

# View with Docker
docker-compose logs -f backend
```

### Debug Mode

Enable debug mode for development:

```bash
# In backend/.env
APP_ENV=development
LOG_LEVEL=DEBUG
```

## 🔧 Customization

### Adding New Platforms

1. **Update the model** in `models/social_media.py`:
```python
class SupportedPlatform(str, Enum):
    # ... existing platforms
    NEW_PLATFORM = "new_platform"
```

2. **Update the frontend** in `components/PostForm.js`:
```javascript
const SUPPORTED_PLATFORMS = [
  // ... existing platforms
  { id: 'new_platform', name: 'New Platform', color: 'bg-purple-500' },
];
```

### Custom Agent Tools

Add new tools to the social media agent:

```python
@social_media_agent.tool
async def custom_tool(
    ctx: RunContext[SocialMediaAgentDeps],
    parameter: str
) -> str:
    """Custom tool description."""
    # Your implementation
    return "Tool result"
```

### Extending the API

Add new endpoints to `main.py`:

```python
@app.post("/api/custom")
async def custom_endpoint(request: CustomRequest):
    """Custom endpoint implementation."""
    return {"status": "success"}
```

## 🚨 Troubleshooting

### Common Issues

#### Ayrshare Connection Failed
- Verify your API key in `.env`
- Check that social accounts are connected in Ayrshare dashboard
- Ensure API key has proper permissions

#### LLM API Errors
- Verify your LLM API key
- Check API quota and limits
- Ensure the model name is correct

#### Frontend Not Loading
- Check that backend is running on port 8000
- Verify CORS settings in `main.py`
- Check browser console for errors

#### Import Errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version (3.11+ required)

### Debug Commands

```bash
# Test Ayrshare connection
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.ayrshare.com/api/profiles

# Test backend health
curl http://localhost:8000/health

# Check backend logs
tail -f backend/logs/app.log

# Test frontend build
cd frontend && npm run build
```

## 🤝 Integration with Main App

This module is designed to integrate seamlessly with your main agentic RAG system:

### 1. Import the Agent

```python
from social_media_module.agents import SocialMediaAgent

# In your main application
social_agent = SocialMediaAgent()
```

### 2. Use in Workflows

```python
# In your LangGraph workflow
async def social_media_node(state):
    agent = SocialMediaAgent()
    result = await agent.post_content(
        prompt=state["social_content"],
        context=state["context"]
    )
    return {"social_result": result}
```

### 3. API Integration

```python
# Call the API from your main app
import httpx

async def post_to_social(content, platforms):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/post",
            json={
                "post": content,
                "platforms": platforms
            }
        )
        return response.json()
```

## 📝 Development Standards Compliance

This module follows the **Sentigen Development Standards v1.0**:

- ✅ **Python 3.11+** with proper virtual environment management
- ✅ **Pydantic AI** for structured agent workflows
- ✅ **FastAPI** with async/await patterns
- ✅ **Structured logging** with contextual information
- ✅ **Environment-based configuration** with `.env` files
- ✅ **Typed dependencies** and return values
- ✅ **Centralized model configuration** via `get_smart_model()`
- ✅ **Comprehensive error handling** and user feedback
- ✅ **Docker support** for containerized deployment
- ✅ **Health checks** and monitoring endpoints

## 📄 License

This project is part of the Sentigen ecosystem and follows the company's licensing terms.

## 🆘 Support

For support and questions:

1. **Check the troubleshooting section** above
2. **Review the API documentation** at `/docs`
3. **Check Ayrshare documentation** at [docs.ayrshare.com](https://docs.ayrshare.com)
4. **Contact the development team** for integration support

---

**Happy Posting!** 🚀📱✨