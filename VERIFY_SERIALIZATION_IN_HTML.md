# Verifying LangChain Object Serialization in HTML Reports

## Issue: "I don't see serialized objects in HTML"

If you're not seeing the LangChain Objects tab with full serialization data, it's likely due to **cached results** from before the feature was added.

## Solution: Clear Cache and Re-run

### Step 1: Clear the cache

```bash
cd /home/user/MARRVEL_MCP
python mcp_llm_test/evaluate_mcp.py --clear
```

Or manually delete the cache:
```bash
rm -rf ~/.cache/marrvel-mcp/evaluations/*
```

### Step 2: Run a fresh test

Run with `--subset` to test just one case:

```bash
python mcp_llm_test/evaluate_mcp.py --subset 1
```

This will run ONLY the first test case and generate fresh results with serialization.

### Step 3: Check the HTML Report

When the HTML opens:
1. **Click "View JSON"** on any test result
2. You should see **TWO tabs**:
   - **"Conversation (Legacy)"** - Your existing simple format
   - **"LangChain Objects (Full)"** - Complete serialization

### What You Should See in "LangChain Objects (Full)" Tab:

```json
[
  {
    "_object_type": "SystemMessage",
    "_module": "langchain_core.messages.system",
    "type": "system",
    "content": "You are a helpful genetics research assistant...",
    "id": "...",
    "example": false
  },
  {
    "_object_type": "HumanMessage",
    "_module": "langchain_core.messages.human",
    "type": "human",
    "content": "What is the function of the BRCA1 gene?",
    "id": "...",
    "example": false
  },
  {
    "_object_type": "AIMessage",
    "_module": "langchain_core.messages.ai",
    "type": "ai",
    "content": "Let me search for information...",
    "tool_calls": [...],
    "usage_metadata": {
      "input_tokens": 245,
      "output_tokens": 87,
      "total_tokens": 332
    },
    "response_metadata": {
      "model_name": "gpt-4-turbo",
      "finish_reason": "tool_calls",
      "token_usage": {
        "prompt_tokens": 245,
        "completion_tokens": 87,
        "total_tokens": 332
      }
    },
    "additional_kwargs": {...},
    "id": "..."
  },
  ...
]
```

### If You See "No LangChain objects available"

This message appears when:
1. **Cached result** - Result is from cache before serialization was added
2. **Vanilla/Web mode** - LangChain messages only available in tool mode (not vanilla/web)
3. **Old version** - Running old code before the feature

**Solution:** Clear cache and re-run (Steps 1-2 above)

## Quick Test Command

Run this single command to clear cache and run one test:

```bash
cd /home/user/MARRVEL_MCP && \
python mcp_llm_test/evaluate_mcp.py --clear && \
python mcp_llm_test/evaluate_mcp.py --subset 1
```

## Verification Checklist

✅ Cache cleared
✅ Fresh test run (not cached)
✅ HTML report opened
✅ Clicked "View JSON"
✅ See two tabs: "Conversation (Legacy)" and "LangChain Objects (Full)"
✅ Second tab shows complete message array with usage_metadata, response_metadata, etc.

## Debug: Check the Result Dict

If you want to manually verify the data is there, check the cache file:

```bash
# Find the latest cache file
ls -lht ~/.cache/marrvel-mcp/evaluations/*/*.pkl | head -1

# Or check the run directory
ls ~/.cache/marrvel-mcp/evaluations/
```

Then in Python:
```python
import pickle
with open('/path/to/cache.pkl', 'rb') as f:
    result = pickle.load(f)
    print('Has serialized_messages:', 'serialized_messages' in result)
    if 'serialized_messages' in result:
        print('Number of messages:', len(result['serialized_messages']))
        print('First message keys:', list(result['serialized_messages'][0].keys()))
```

## Expected Attributes in Serialized Messages

Each AIMessage should have ~11+ attributes:
- `_object_type`, `_module` - Object metadata
- `type`, `content`, `id`, `example` - Basic message info
- `tool_calls`, `tool_calls_detail` - Tool calling info
- `usage_metadata` - Token usage (input, output, total)
- `response_metadata` - Full response metadata (model_name, finish_reason, token_usage)
- `additional_kwargs` - Provider-specific data

## Still Not Working?

If after clearing cache and re-running you still don't see it:

1. **Check you're on the right branch:**
   ```bash
   git branch
   # Should show: claude/serialize-langchain-objects-011rCD75dYvwpYr3kndwGTAW
   ```

2. **Check the files were updated:**
   ```bash
   git log --oneline -3
   # Should show: 49799d4 feat: add serialized LangChain objects to HTML reports with tabs
   ```

3. **Verify the code changes:**
   ```bash
   grep -n "serialized_messages" mcp_llm_test/evaluation_modules/test_execution.py
   # Should show line 197
   ```

4. **Run without cache at all:**
   ```bash
   python mcp_llm_test/evaluate_mcp.py --subset 1 --no-cache
   # Note: --no-cache flag may not exist, just delete cache manually
   ```

## Contact

If it's still not working, please share:
- Output of: `git log --oneline -3`
- Are you seeing the yellow "No LangChain objects available" message?
- Or is the second tab missing entirely?
- Screenshot of the modal would help!
