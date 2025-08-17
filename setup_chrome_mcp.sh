#!/bin/bash

# Chrome MCP Setup Script for Sentigen Social
# This script helps set up the Chrome MCP server for research automation

echo "🚀 Setting up Chrome MCP Server for Sentigen Social..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    echo "Visit: https://nodejs.org/"
    exit 1
fi

# Check if Chrome is installed
if ! command -v google-chrome &> /dev/null && ! command -v chromium-browser &> /dev/null; then
    echo "❌ Chrome/Chromium is not installed. Please install Chrome first."
    echo "Visit: https://www.google.com/chrome/"
    exit 1
fi

# Create Chrome MCP directory
CHROME_MCP_DIR="chrome-mcp-server"
if [ ! -d "$CHROME_MCP_DIR" ]; then
    echo "📁 Creating Chrome MCP directory..."
    mkdir -p "$CHROME_MCP_DIR"
fi

cd "$CHROME_MCP_DIR"

# Install Chrome MCP server (if not already installed)
if [ ! -f "package.json" ]; then
    echo "📦 Installing Chrome MCP server..."
    
    # Initialize npm project
    npm init -y
    
    # Install required packages
    npm install @modelcontextprotocol/server-chrome
    npm install puppeteer
    npm install express
    npm install cors
    
    echo "✅ Chrome MCP server installed successfully!"
else
    echo "✅ Chrome MCP server already installed"
fi

# Create Chrome MCP server script
cat > server.js << 'EOF'
const { ChromeServer } = require('@modelcontextprotocol/server-chrome');
const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.CHROME_MCP_PORT || 12306;

// Enable CORS for all routes
app.use(cors());
app.use(express.json());

// Initialize Chrome MCP server
const chromeServer = new ChromeServer({
    headless: process.env.CHROME_HEADLESS !== 'false',
    args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu'
    ]
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// MCP tool endpoints
app.post('/mcp/tools/:toolName', async (req, res) => {
    try {
        const { toolName } = req.params;
        const args = req.body;
        
        console.log(`Executing tool: ${toolName}`, args);
        
        const result = await chromeServer.executeTool(toolName, args);
        res.json(result);
    } catch (error) {
        console.error('Tool execution error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🌐 Chrome MCP Server running on http://localhost:${PORT}`);
    console.log(`📊 Health check: http://localhost:${PORT}/health`);
    console.log(`🔧 Tools endpoint: http://localhost:${PORT}/mcp/tools/:toolName`);
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down Chrome MCP server...');
    await chromeServer.close();
    process.exit(0);
});
EOF

# Create start script
cat > start.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Chrome MCP Server..."
echo "📊 Health check will be available at: http://localhost:12306/health"
echo "🔧 Tools endpoint: http://localhost:12306/mcp/tools/:toolName"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Set environment variables
export CHROME_HEADLESS=true
export CHROME_MCP_PORT=12306

# Start the server
node server.js
EOF

chmod +x start.sh

# Create package.json scripts
npm pkg set scripts.start="node server.js"
npm pkg set scripts.dev="CHROME_HEADLESS=false node server.js"

echo ""
echo "✅ Chrome MCP Server setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Start the Chrome MCP server:"
echo "   cd $CHROME_MCP_DIR && ./start.sh"
echo ""
echo "2. Test the server:"
echo "   curl http://localhost:12306/health"
echo ""
echo "3. The server will be available at: http://localhost:12306"
echo "4. Your Sentigen Social backend will connect to this server automatically"
echo ""
echo "🔧 Available tools:"
echo "   - chrome_navigate: Navigate to a URL"
echo "   - chrome_get_web_content: Get page content"
echo "   - chrome_get_interactive_elements: Get clickable elements"
echo "   - chrome_screenshot: Take a screenshot"
echo "   - chrome_keyboard: Send keyboard input"
echo "   - search_tabs_content: Search content in tabs"
echo ""
echo "🎯 Ready for research automation!"
