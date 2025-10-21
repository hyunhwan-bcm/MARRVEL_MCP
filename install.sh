#!/bin/bash

# MARRVEL-MCP Installation Script
# This script sets up the MARRVEL-MCP server for use with Claude Desktop

echo "================================================"
echo "MARRVEL-MCP Installation Script"
echo "================================================"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo "❌ Error: Python 3.10 or higher is required"
    echo "   Current version: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"
echo ""

# Get the absolute path of the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Installation directory: $SCRIPT_DIR"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"
echo ""

# Detect OS and set config path
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
    echo "Detected macOS"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    CONFIG_DIR="$APPDATA/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
    echo "Detected Windows"
else
    # Linux
    CONFIG_DIR="$HOME/.config/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
    echo "Detected Linux"
fi

echo ""
echo "Claude Desktop config location: $CONFIG_FILE"
echo ""

# Create config directory if it doesn't exist
if [ ! -d "$CONFIG_DIR" ]; then
    echo "Creating config directory..."
    mkdir -p "$CONFIG_DIR"
fi

# Backup existing config
if [ -f "$CONFIG_FILE" ]; then
    echo "Backing up existing config..."
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ Backup created"
fi

# Create or update config
echo ""
echo "Configuring MCP server..."

# Read existing config or create new one
if [ -f "$CONFIG_FILE" ]; then
    # Config exists, we should merge
    echo "⚠️  Existing config file found."
    echo "Please manually add the following to your $CONFIG_FILE:"
    echo ""
    echo '  "mcpServers": {'
    echo '    "marrvel": {'
    echo '      "command": "python3",'
    echo "      \"args\": [\"$SCRIPT_DIR/server.py\"]"
    echo '    }'
    echo '  }'
    echo ""
else
    # Create new config
    cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "marrvel": {
      "command": "python3",
      "args": ["$SCRIPT_DIR/server.py"]
    }
  }
}
EOF
    echo "✅ Config file created"
fi

echo ""
echo "================================================"
echo "Installation Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Restart Claude Desktop"
echo "2. Try a query like: 'Use MARRVEL to get information about TP53'"
echo ""
echo "Documentation:"
echo "  - Quick Start: $SCRIPT_DIR/QUICKSTART.md"
echo "  - API Docs: $SCRIPT_DIR/API_DOCUMENTATION.md"
echo "  - Examples: $SCRIPT_DIR/examples/example_queries.py"
echo ""
echo "To test the server directly:"
echo "  python3 $SCRIPT_DIR/server.py"
echo ""
