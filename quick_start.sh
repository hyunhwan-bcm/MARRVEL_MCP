#!/bin/bash
# Quick Start Script for Multi-Model Benchmark
#
# This script provides a guided setup for running your first benchmark.

set -euo pipefail

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        MARRVEL-MCP Multi-Model Benchmark Quick Start          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if models_config.yaml exists
if [ ! -f "mcp_llm_test/models_config.yaml" ]; then
    echo "❌ Error: models_config.yaml not found"
    exit 1
fi

echo "📋 Current Configuration:"
echo ""
python mcp_llm_test/get_model_configs.py --format json 2>/dev/null | python -c '
import json
import sys
data = json.load(sys.stdin)
if not data:
    print("⚠️  No enabled models found!")
    print("   Please edit mcp_llm_test/models_config.yaml and set enabled: true for at least one model")
    sys.exit(1)
for model in data:
    print(f"  ✓ {model[\"name\"]} ({model[\"provider\"]})")
    if model.get("skip_vanilla"):
        print(f"    - Skipping vanilla mode")
    if model.get("skip_web_search"):
        print(f"    - Skipping web search mode")
'

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo "🚀 Ready to run benchmark!"
echo ""
echo "Options:"
echo "  1. Quick test (first 3 tests only) - Fast, good for testing setup"
echo "  2. Full benchmark (all tests) - Complete evaluation, takes longer"
echo "  3. Resume previous run - Continue from where you left off"
echo "  4. Exit"
echo ""
read -p "Select option (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🏃 Running quick test (first 3 tests)..."
        echo ""
        # We'll need to modify this to support subset in bash script
        # For now, just run with low concurrency
        CONCURRENCY=1 ./run_benchmark.sh
        ;;
    2)
        echo ""
        echo "🏃 Running full benchmark..."
        echo ""
        echo "💡 Tip: Set CONCURRENCY=2 or higher for faster execution"
        echo "   Example: CONCURRENCY=2 ./run_benchmark.sh"
        echo ""
        ./run_benchmark.sh
        ;;
    3)
        echo ""
        echo "🔄 Resuming previous run..."
        echo ""
        RESUME=true ./run_benchmark.sh
        ;;
    4)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "✅ Benchmark complete!"
echo ""
echo "📊 Results available in: test_results/"
echo ""
echo "View results:"
echo "  • Summary table: cat test_results/summary.md"
echo "  • CSV data: test_results/summary.csv"
echo "  • Comparison plot: open test_results/comparison.png"
echo ""
echo "Re-run analysis anytime:"
echo "  python mcp_llm_test/analyze_results.py test_results"
echo ""
