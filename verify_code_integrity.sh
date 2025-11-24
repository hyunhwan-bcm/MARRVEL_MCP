#!/bin/bash
# Code Integrity Verification Script
# Run this script to check for potential issues in the codebase

set -e

echo "=================================="
echo "CODE INTEGRITY VERIFICATION"
echo "=================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS=0
WARNINGS=0
ERRORS=0

# 1. Check for merge conflict markers
echo "1. Checking for merge conflict markers..."
if grep -rn "^<<<<<<< \|^=======\$\|^>>>>>>> " --include="*.py" --include="*.md" . 2>/dev/null | grep -v "^Binary"; then
    echo -e "${RED}✗ FOUND merge conflict markers${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ No merge conflict markers found${NC}"
    SUCCESS=$((SUCCESS + 1))
fi
echo ""

# 2. Check Python syntax
echo "2. Checking Python syntax..."
if python -m py_compile marrvel_mcp/langchain_serialization.py 2>/dev/null; then
    echo -e "${GREEN}✓ Python syntax valid (langchain_serialization.py)${NC}"
    SUCCESS=$((SUCCESS + 1))
else
    echo -e "${RED}✗ Python syntax errors found${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 3. Check for duplicate function definitions
echo "3. Checking for duplicate function definitions..."
DUPLICATES=$(awk '/^def / {funcs[$2]++} END {for (f in funcs) if (funcs[f] > 1) print f, funcs[f]}' marrvel_mcp/langchain_serialization.py)
if [ -z "$DUPLICATES" ]; then
    echo -e "${GREEN}✓ No duplicate function definitions${NC}"
    SUCCESS=$((SUCCESS + 1))
else
    echo -e "${RED}✗ Found duplicate functions:${NC}"
    echo "$DUPLICATES"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 4. Check git status
echo "4. Checking git status..."
if git diff --quiet HEAD; then
    echo -e "${GREEN}✓ Working tree clean${NC}"
    SUCCESS=$((SUCCESS + 1))
else
    echo -e "${YELLOW}⚠ Uncommitted changes detected${NC}"
    WARNINGS=$((WARNINGS + 1))
    git status --short
fi
echo ""

# 5. Verify function exports
echo "5. Checking function exports in __init__.py..."
EXPORTED_FUNCS=("serialize_langchain_object" "serialize_messages_array" "print_serialized_messages"
                "save_serialized_messages" "compare_with_conversation" "print_information_loss_analysis"
                "extract_token_info")

for func in "${EXPORTED_FUNCS[@]}"; do
    if grep -q "\"$func\"" marrvel_mcp/__init__.py; then
        echo -e "${GREEN}✓ $func exported${NC}"
        SUCCESS=$((SUCCESS + 1))
    else
        echo -e "${RED}✗ $func NOT exported${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# 6. Count functions in serialization module
echo "6. Verifying function count..."
FUNC_COUNT=$(grep -c "^def " marrvel_mcp/langchain_serialization.py)
EXPECTED_COUNT=9
if [ "$FUNC_COUNT" -eq "$EXPECTED_COUNT" ]; then
    echo -e "${GREEN}✓ Expected $EXPECTED_COUNT functions, found $FUNC_COUNT${NC}"
    SUCCESS=$((SUCCESS + 1))
else
    echo -e "${YELLOW}⚠ Expected $EXPECTED_COUNT functions, found $FUNC_COUNT${NC}"
    WARNINGS=$((WARNINGS + 1))
    echo "Functions:"
    awk '/^def / {print "  - " NR": "$0}' marrvel_mcp/langchain_serialization.py
fi
echo ""

# 7. Check for common issues
echo "7. Checking for common Python issues..."

# Check for trailing whitespace (can cause issues)
if grep -n " $" marrvel_mcp/langchain_serialization.py > /dev/null; then
    echo -e "${YELLOW}⚠ Trailing whitespace found (minor issue)${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✓ No trailing whitespace${NC}"
    SUCCESS=$((SUCCESS + 1))
fi

# Check for tabs (should use spaces)
if grep -P "\t" marrvel_mcp/langchain_serialization.py > /dev/null; then
    echo -e "${YELLOW}⚠ Tabs found (should use spaces)${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✓ No tabs found (using spaces)${NC}"
    SUCCESS=$((SUCCESS + 1))
fi
echo ""

# Summary
echo "=================================="
echo "SUMMARY"
echo "=================================="
echo -e "${GREEN}✓ Success: $SUCCESS${NC}"
echo -e "${YELLOW}⚠ Warnings: $WARNINGS${NC}"
echo -e "${RED}✗ Errors: $ERRORS${NC}"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}FAILED: Please fix errors before proceeding${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}PASSED WITH WARNINGS: Review warnings${NC}"
    exit 0
else
    echo -e "${GREEN}ALL CHECKS PASSED!${NC}"
    exit 0
fi
