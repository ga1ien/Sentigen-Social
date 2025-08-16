# Chrome MCP Setup Guide

This guide will help you set up the Chrome MCP Server for social media intelligence monitoring.

## What is Chrome MCP?

The [Chrome MCP Server](https://github.com/hangwin/mcp-chrome) is a Chrome extension-based Model Context Protocol (MCP) server that exposes your Chrome browser functionality to AI assistants. It enables:

- **Browser Automation**: Navigate, click, fill forms, and interact with web pages
- **Content Extraction**: Get text, HTML, and interactive elements from any page
- **Network Monitoring**: Capture HTTP requests and responses
- **Screenshot Capture**: Take full-page or element-specific screenshots
- **Semantic Search**: AI-powered search across browser tabs
- **Session Persistence**: Use your existing browser sessions and logins

## Why Use Chrome MCP for Social Media Intelligence?

Traditional web scraping approaches have limitations:
- **Authentication Issues**: Hard to handle login-required platforms like LinkedIn
- **Rate Limiting**: APIs have strict limits and costs
- **Clean Environment**: Headless browsers lack user context and settings
- **Detection**: Automated browsers are often blocked

Chrome MCP solves these by:
- ✅ **Using Your Real Browser**: Leverages your existing sessions and cookies
- ✅ **No Authentication Hassles**: Already logged into LinkedIn, Twitter, etc.
- ✅ **Natural Browsing**: Appears as normal user activity
- ✅ **Full Context**: Access to all your browser data and settings

## Installation Steps

### 1. Download Chrome Extension

Download the latest Chrome extension from the [GitHub releases page](https://github.com/hangwin/mcp-chrome/releases).

### 2. Install Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked" and select the downloaded extension folder
4. The Chrome MCP extension should now appear in your extensions

### 3. Install MCP Bridge

Install the MCP bridge globally using npm or pnpm:

```bash
# Using npm
npm install -g mcp-chrome-bridge

# Using pnpm (recommended)
pnpm config set enable-pre-post-scripts true
pnpm install -g mcp-chrome-bridge

# If automatic registration fails with pnpm
mcp-chrome-bridge register
```

### 4. Connect Extension to Bridge

1. Click the Chrome MCP extension icon in your browser
2. Click "Connect" to establish connection with the bridge
3. You should see a "Connected" status

### 5. Verify Connection

The extension should show:
- ✅ **Status**: Connected
- ✅ **Bridge**: Running on `http://127.0.0.1:12306`
- ✅ **MCP Server**: Active

## Platform Authentication Setup

For optimal results, log into the social media platforms you want to monitor:

### Required Logins
- **LinkedIn**: Essential for professional content insights
- **Twitter/X**: For real-time trending topics
- **Reddit**: For community discussions and trends

### Optional Logins
- **Facebook**: For broader social media coverage
- **Instagram**: For visual content trends
- **YouTube**: For video content insights
- **Medium**: For long-form content analysis

### Login Tips
1. **Use Your Main Accounts**: Better content access and recommendations
2. **Stay Logged In**: Enable "Remember me" for persistent sessions
3. **Multiple Accounts**: You can switch accounts as needed
4. **Privacy Mode**: Use incognito for testing without affecting main accounts

## Configuration in AI Social Media Platform

### 1. Update Environment Variables

Add to your `.env` file:

```bash
# Chrome MCP Configuration
CHROME_MCP_URL=http://127.0.0.1:12306/mcp
CHROME_MCP_ENABLED=true

# Content Intelligence Settings
CONTENT_INTELLIGENCE_WORKERS=3
SCAN_RATE_LIMIT_DELAY=2.0
MAX_INSIGHTS_PER_SCAN=50
```

### 2. Platform Configuration

The system comes pre-configured for these platforms:

- **Reddit**: `/r/artificial`, `/r/MachineLearning`, `/r/programming`
- **LinkedIn**: AI and productivity content feeds
- **Twitter/X**: AI and tech hashtag searches
- **Hacker News**: Top stories and discussions
- **Product Hunt**: AI and productivity tools

### 3. Search Queries

Default search queries include:
- "AI", "artificial intelligence"
- "machine learning", "automation"
- "productivity", "remote work"
- "startup", "SaaS", "API"

You can customize these in the Intelligence dashboard.

## Using the Content Intelligence System

### 1. Access the Dashboard

Navigate to `/dashboard/intelligence` in your AI Social Media Platform.

### 2. Check Connection Status

Look for the Chrome MCP status badge:
- 🟢 **Connected**: Ready to scan
- 🔴 **Disconnected**: Check extension and bridge

### 3. Configure Scan Settings

1. **Select Platforms**: Choose which social media platforms to monitor
2. **Set Search Queries**: Add relevant keywords and topics
3. **Time Window**: How far back to look for content (default: 24 hours)
4. **Max Posts**: Limit per platform to avoid rate limiting

### 4. Run Your First Scan

1. Click "Scan Now" to start manual scan
2. Watch the progress bar as it scans each platform
3. Review the insights and trending topics
4. Check AI-generated content recommendations

### 5. Schedule Recurring Scans

1. Go to Settings tab in Intelligence dashboard
2. Configure scan frequency (recommended: every 6 hours)
3. Set up automated monitoring for continuous insights

## Troubleshooting

### Extension Not Connecting

1. **Check Bridge Status**:
   ```bash
   # Check if bridge is running
   curl http://127.0.0.1:12306/health
   ```

2. **Restart Bridge**:
   ```bash
   mcp-chrome-bridge register
   ```

3. **Reload Extension**: Go to `chrome://extensions/` and reload the Chrome MCP extension

### Scan Failures

1. **Platform Access**: Ensure you're logged into the platforms
2. **Rate Limiting**: Reduce scan frequency or max posts per platform
3. **Network Issues**: Check internet connection and firewall settings

### No Insights Found

1. **Login Status**: Verify you're logged into social media platforms
2. **Search Queries**: Try broader or more specific search terms
3. **Time Window**: Increase the time window for more content
4. **Platform Selection**: Ensure selected platforms have relevant content

### Performance Issues

1. **Reduce Workers**: Lower the number of parallel workers
2. **Increase Delays**: Add more delay between requests
3. **Limit Platforms**: Scan fewer platforms simultaneously
4. **Browser Resources**: Close unnecessary tabs and extensions

## Best Practices

### 1. Ethical Usage
- **Respect Rate Limits**: Don't overwhelm platforms with requests
- **Follow Terms of Service**: Comply with each platform's ToS
- **Personal Use**: Use your own accounts, not others'
- **Data Privacy**: Handle extracted data responsibly

### 2. Optimal Configuration
- **Start Small**: Begin with 2-3 platforms and expand gradually
- **Regular Monitoring**: Set up recurring scans every 6-12 hours
- **Relevant Queries**: Use specific, industry-relevant search terms
- **Quality Over Quantity**: Focus on high-engagement content

### 3. Content Strategy
- **Trend Analysis**: Use insights to identify emerging topics
- **Competitive Intelligence**: Monitor what's working for others
- **Content Gaps**: Find underserved topics and audiences
- **Timing Optimization**: Post when your audience is most active

## Advanced Features

### 1. Custom Platform Configurations

You can add new platforms by modifying the `PLATFORM_CONFIGS` in the backend:

```python
Platform.CUSTOM: PlatformConfig(
    url="https://example.com",
    selectors={
        "post_title": ".title-selector",
        "post_content": ".content-selector",
        "engagement": ".engagement-selector"
    },
    search_paths=["/trending", "/popular"],
    scroll_strategy="infinite"
)
```

### 2. Advanced Search Strategies

- **Boolean Queries**: Use AND, OR, NOT operators
- **Hashtag Tracking**: Monitor specific hashtags across platforms
- **User Monitoring**: Track specific influencers or competitors
- **Geographic Targeting**: Focus on location-specific content

### 3. Integration with Content Creation

The intelligence system integrates with the content creation workflow:

1. **Insight → Idea**: Convert insights into content recommendations
2. **Trend → Post**: Create posts based on trending topics
3. **Competitor → Strategy**: Adapt successful competitor content
4. **Timing → Schedule**: Post when engagement is highest

## Support and Resources

- **Chrome MCP GitHub**: [https://github.com/hangwin/mcp-chrome](https://github.com/hangwin/mcp-chrome)
- **Documentation**: Complete tool API documentation
- **Community**: Join the development community for support
- **Issues**: Report bugs and feature requests on GitHub

## Security Considerations

### 1. Browser Security
- **Keep Chrome Updated**: Use the latest version for security patches
- **Extension Permissions**: Review what permissions the extension requests
- **Network Security**: Ensure secure connection to MCP bridge

### 2. Data Protection
- **Local Processing**: Content analysis happens locally
- **No Data Sharing**: Your browser data stays on your machine
- **Secure Storage**: Insights stored in your private database

### 3. Account Safety
- **Use Strong Passwords**: Secure your social media accounts
- **Enable 2FA**: Add two-factor authentication where possible
- **Monitor Activity**: Check for unusual account activity

---

**Ready to unlock the power of AI-driven social media intelligence!** 🚀

With Chrome MCP, you'll have unprecedented access to real-time social media insights, enabling you to create content that resonates with your audience and stays ahead of trends.
