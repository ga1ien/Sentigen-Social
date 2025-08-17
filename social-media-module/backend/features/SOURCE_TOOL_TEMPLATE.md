# Content Source Research Tool Template

This template provides the structure for creating dedicated research tools for different content sources (LinkedIn, Twitter, YouTube, etc.).

## 🏗️ **Architecture Pattern**

Each source tool should be **completely independent** with the following structure:

```
{source}-research-tool/
├── config/
│   ├── {source}_research_config.py      # Source-specific configuration
│   └── user_configs/                    # User configuration storage
├── scrapers/
│   ├── {source}_raw_scraper.py          # Raw data collection
│   └── {source}_analyzer.py             # AI analysis worker
├── api/
│   └── {source}_research_api.py         # REST API endpoints
├── scheduler/
│   └── {source}_scheduler.py            # Automated scheduling
├── cli/
│   ├── cli_{source}_scraper.py          # Command-line interface
│   └── run_{source}_background.sh       # Background execution
├── results/
│   ├── raw_data/                        # Raw collected data
│   ├── analyzed_data/                   # AI-analyzed results
│   └── scheduled_results/               # Automated job results
├── requirements.txt                     # Dependencies
├── Dockerfile                          # Container deployment
└── README.md                           # Tool documentation
```

## 📋 **Core Components Template**

### 1. **Configuration System** (`{source}_research_config.py`)

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class AnalysisDepth(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"

class ResearchFrequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"

@dataclass
class {Source}Config:
    """Source-specific configuration"""
    # Define source-specific parameters
    search_topics: List[str]
    max_items_per_topic: int = 10
    # Add source-specific fields...

@dataclass
class {Source}ResearchConfig:
    """Complete research configuration for {Source}"""
    user_id: str
    workspace_id: str
    config_name: str
    description: str

    # Source configuration
    {source}_config: {Source}Config

    # Analysis settings
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD
    ai_model: str = "gpt-5-mini"
    focus_areas: List[str] = None

    # Scheduling
    schedule: Optional[ResearchSchedule] = None
    auto_run_enabled: bool = False

    # Output preferences
    generate_summary: bool = True
    generate_insights: bool = True
    generate_content_ideas: bool = True
    export_formats: List[str] = None

class {Source}ResearchConfigManager:
    """Manages {Source} research configurations"""

    def create_config(self, config: {Source}ResearchConfig) -> bool:
        # Implementation...
        pass

    def load_config(self, user_id: str, config_name: str) -> Optional[{Source}ResearchConfig]:
        # Implementation...
        pass

    def update_config(self, user_id: str, config_name: str, updates: Dict) -> bool:
        # Implementation...
        pass

    def delete_config(self, user_id: str, config_name: str) -> bool:
        # Implementation...
        pass
```

### 2. **Raw Data Scraper** (`{source}_raw_scraper.py`)

```python
import asyncio
from pathlib import Path
from datetime import datetime

class {Source}RawScraperCLI:
    """Fast raw data collection from {Source}"""

    def __init__(self):
        self.results_dir = Path(__file__).parent / "raw_data"
        self.results_dir.mkdir(exist_ok=True)

    async def initialize_workers(self):
        """Initialize {Source} API connections"""
        # Source-specific initialization
        pass

    async def scrape_{source}_raw(self, config, max_items=10):
        """Collect raw data from {Source}"""
        # Source-specific scraping logic
        # Return collected raw data
        pass

    async def run_raw_collection_session(self, config):
        """Run complete raw data collection"""
        # Orchestrate collection process
        # Save raw dataset
        pass
```

### 3. **AI Analysis Worker** (`{source}_analyzer.py`)

```python
import asyncio
from core.openai_client import GPT5MiniClient

class {Source}AIAnalyzer:
    """AI analysis worker for {Source} data"""

    def __init__(self):
        self.ai_client = None
        self.analyzed_data_dir = Path(__file__).parent / "analyzed_data"
        self.analyzed_data_dir.mkdir(exist_ok=True)

    async def initialize_ai_client(self):
        """Initialize GPT-5 Mini client"""
        self.ai_client = GPT5MiniClient()

    async def analyze_{source}_content(self, content_data):
        """Comprehensive AI analysis of {Source} content"""
        # Source-specific analysis prompts
        # Return structured analysis results
        pass

    async def analyze_dataset(self, raw_dataset):
        """Analyze entire raw dataset"""
        # Process all items in dataset
        # Generate comprehensive insights
        # Save analyzed results
        pass
```

### 4. **REST API** (`{source}_research_api.py`)

```python
from fastapi import FastAPI, HTTPException
from typing import Dict, List, Optional

app = FastAPI(title="{Source} Research API", version="1.0.0")

@app.post("/configs")
async def create_research_config(request: {Source}ResearchConfigRequest):
    """Create new {Source} research configuration"""
    pass

@app.get("/configs/{user_id}")
async def list_user_configs(user_id: str):
    """List user's {Source} configurations"""
    pass

@app.get("/configs/{user_id}/{config_name}")
async def get_research_config(user_id: str, config_name: str):
    """Get specific {Source} configuration"""
    pass

@app.put("/configs/{user_id}/{config_name}")
async def update_research_config(user_id: str, config_name: str, updates):
    """Update {Source} configuration"""
    pass

@app.delete("/configs/{user_id}/{config_name}")
async def delete_research_config(user_id: str, config_name: str):
    """Delete {Source} configuration"""
    pass

@app.post("/jobs/trigger/{user_id}/{config_name}")
async def trigger_research_job(user_id: str, config_name: str):
    """Manually trigger {Source} research job"""
    pass

@app.get("/jobs/status")
async def get_job_status(user_id: Optional[str] = None):
    """Get {Source} job status"""
    pass
```

### 5. **Scheduler** (`{source}_scheduler.py`)

```python
import schedule
import threading
from datetime import datetime

class {Source}Scheduler:
    """Automated scheduling for {Source} research"""

    def __init__(self):
        self.config_manager = {Source}ResearchConfigManager()
        self.running = False
        self.scheduler_thread = None

    def start(self):
        """Start scheduler in background thread"""
        pass

    def stop(self):
        """Stop scheduler"""
        pass

    def register_user_configs(self):
        """Register all user configurations"""
        pass

    def _execute_research_job(self, config):
        """Execute scheduled research job"""
        # Run raw collection
        # Run AI analysis
        # Save results
        pass
```

## 🔌 **Integration Pattern**

### **Orchestration API** (Separate Service)

```python
# orchestration_api.py
from fastapi import FastAPI
import httpx

app = FastAPI(title="Content Research Orchestration API")

# Service registry
RESEARCH_SERVICES = {
    "reddit": "http://reddit-research-api:8001",
    "linkedin": "http://linkedin-research-api:8002",
    "twitter": "http://twitter-research-api:8003",
    "youtube": "http://youtube-research-api:8004"
}

@app.post("/research/multi-source")
async def trigger_multi_source_research(request: MultiSourceRequest):
    """Trigger research across multiple sources"""

    results = {}

    # Trigger each enabled source in parallel
    async with httpx.AsyncClient() as client:
        tasks = []

        for source in request.enabled_sources:
            if source in RESEARCH_SERVICES:
                service_url = RESEARCH_SERVICES[source]
                task = client.post(
                    f"{service_url}/jobs/trigger/{request.user_id}/{request.config_name}"
                )
                tasks.append((source, task))

        # Wait for all to complete
        for source, task in tasks:
            try:
                response = await task
                results[source] = response.json()
            except Exception as e:
                results[source] = {"error": str(e)}

    return {
        "job_id": f"multi_{int(time.time())}",
        "source_results": results,
        "triggered_at": datetime.now().isoformat()
    }

@app.get("/research/status/{user_id}")
async def get_multi_source_status(user_id: str):
    """Get status across all sources for a user"""

    status = {}

    async with httpx.AsyncClient() as client:
        for source, service_url in RESEARCH_SERVICES.items():
            try:
                response = await client.get(f"{service_url}/jobs/status/{user_id}")
                status[source] = response.json()
            except Exception as e:
                status[source] = {"error": str(e)}

    return status
```

## 🚀 **Deployment Pattern**

### **Docker Compose** (All Services)

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Orchestration API
  orchestration-api:
    build: ./orchestration-api
    ports:
      - "8000:8000"
    environment:
      - REDDIT_SERVICE_URL=http://reddit-research:8001
      - LINKEDIN_SERVICE_URL=http://linkedin-research:8002

  # Reddit Research Tool
  reddit-research:
    build: ./reddit-research-tool
    ports:
      - "8001:8000"
    environment:
      - REDDIT_CLIENT_ID=${REDDIT_CLIENT_ID}
      - REDDIT_CLIENT_SECRET=${REDDIT_CLIENT_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - reddit_data:/app/results

  # LinkedIn Research Tool
  linkedin-research:
    build: ./linkedin-research-tool
    ports:
      - "8002:8000"
    environment:
      - LINKEDIN_API_KEY=${LINKEDIN_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - linkedin_data:/app/results

  # Twitter Research Tool
  twitter-research:
    build: ./twitter-research-tool
    ports:
      - "8003:8000"
    environment:
      - TWITTER_BEARER_TOKEN=${TWITTER_BEARER_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - twitter_data:/app/results

volumes:
  reddit_data:
  linkedin_data:
  twitter_data:
```

## 📊 **Benefits of This Architecture**

**✅ **Independent Development**: Each source team works independently
**✅ **Independent Scaling**: Scale Reddit differently than LinkedIn
**✅ **Independent Deployment**: Deploy updates without affecting other sources
**✅ **Fault Isolation**: One source failure doesn't break others
**✅ **Technology Flexibility**: Use different tech stacks per source
**✅ **Specialized Optimization**: Each tool optimized for its source
**✅ **Easy Testing**: Test each source tool independently
**✅ **Clear Ownership**: Different teams can own different sources

## 🎯 **Implementation Steps**

1. **Start with Reddit Tool** (Already built)
2. **Create LinkedIn Tool** using this template
3. **Create Twitter Tool** using this template
4. **Build Orchestration API** to coordinate multiple tools
5. **Create Frontend** that talks to orchestration API
6. **Add more sources** as needed (YouTube, Medium, etc.)

This pattern ensures each source tool is **focused, maintainable, and scalable** while still allowing coordinated multi-source research through the orchestration layer.
