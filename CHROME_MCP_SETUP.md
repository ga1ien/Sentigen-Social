# Chrome MCP Setup Guide

## ✅ Status: Ready for Testing

### 1. Chrome Extension Installation

The Chrome MCP extension is ready at: `/Users/galenoakes/Development/chrome-mcp-extension`

**To install:**
1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select folder: `/Users/galenoakes/Development/chrome-mcp-extension`
5. The extension should appear in your Chrome toolbar

### 2. Chrome MCP Bridge Configuration

✅ **Native Messaging Host**: Registered successfully
✅ **Extension ID**: `hbdgbgagpkpjffpklnamcljpakneikee`
✅ **MCP Configuration**: Added to `/Users/galenoakes/.cursor/mcp.json`

### 3. Available Chrome MCP Tools

Based on the [mcp-chrome documentation](https://github.com/hangwin/mcp-chrome), you now have access to:

#### 🌐 Browser Management (6 tools)
- `get_windows_and_tabs` - List all browser windows and tabs
- `chrome_navigate` - Navigate to URLs and control viewport
- `chrome_close_tabs` - Close specific tabs or windows
- `chrome_go_back_or_forward` - Browser navigation control
- `chrome_inject_script` - Inject content scripts into web pages
- `chrome_send_command_to_inject_script` - Send commands to injected content scripts

#### 🔍 Content Analysis (4 tools)
- `search_tabs_content` - AI-powered semantic search across browser tabs
- `chrome_get_web_content` - Extract HTML/text content from pages
- `chrome_get_interactive_elements` - Find clickable elements
- `chrome_console` - Capture and retrieve console output from browser tabs

#### 🎯 Interaction (3 tools)
- `chrome_click_element` - Click elements using CSS selectors
- `chrome_fill_or_select` - Fill forms and select options
- `chrome_keyboard` - Simulate keyboard input and shortcuts

#### 🌐 Network Monitoring (4 tools)
- `chrome_network_capture_start/stop` - webRequest API network capture
- `chrome_network_debugger_start/stop` - Debugger API with response bodies
- `chrome_network_request` - Send custom HTTP requests

### 4. Research-to-Video Workflow

**Frontend**: ✅ Working at http://localhost:3000/dashboard/research-video
**Backend API**: ✅ Working (Railway deployment)
**Chrome MCP**: ✅ Ready for browser automation

#### How it works:
1. **User Input**: Research topics, target audience, video style
2. **Chrome Automation**: Opens multiple tabs (Reddit, LinkedIn, Substack, etc.)
3. **Content Extraction**: Uses `chrome_get_web_content` and `search_tabs_content`
4. **Data Processing**: Stores insights in Supabase
5. **Script Generation**: AI creates video script from research
6. **Avatar Selection**: User chooses avatar style
7. **Video Generation**: HeyGen creates AI video
8. **Approval & Publishing**: Manual approval → Auto-post to TikTok, IG, YouTube

### 5. Testing the Complete Workflow

1. **Install Chrome Extension** (see step 1 above)
2. **Open Research Page**: http://localhost:3000/dashboard/research-video
3. **Start Research**:
   - Topics: "AI automation", "productivity tools"
   - Audience: "tech entrepreneurs"
   - Style: "professional"
4. **Watch Chrome Automation**: Multiple tabs will open automatically
5. **Review Results**: See extracted insights and generated script

### 6. Troubleshooting

If Chrome MCP isn't working:
1. Check extension is installed and enabled
2. Click the extension icon → "Connect"
3. Restart Cursor to refresh MCP connections
4. Check Chrome console for any errors

### 7. Next Steps

- [ ] Test multi-tab research automation
- [ ] Integrate with HeyGen API for video generation
- [ ] Set up TikTok auto-posting
- [ ] Add Instagram Reels and YouTube Shorts support

---

**🎉 You're ready to test the complete Research-to-Video workflow!**
