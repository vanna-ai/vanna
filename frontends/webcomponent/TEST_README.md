# Vanna Webcomponent Comprehensive Test Suite

This test suite validates all component types and update patterns in the vanna-webcomponent before pruning unused code.

## Overview

The test suite consists of:
- **`test_backend.py`**: Real Python backend that streams all component types
- **`test-comprehensive.html`**: Browser-based test interface with visual validation
- **Two test modes**: Rapid (stress test) and Realistic (with delays)

## Quick Start

### 1. Install Dependencies

```bash
cd submodule/vanna-webcomponent
pip install -r requirements-test.txt
```

### 2. Build the Webcomponent

```bash
npm run build
```

### 3. Start the Test Backend

```bash
# Realistic mode (with delays between components)
python test_backend.py --mode realistic

# Rapid mode (fast stress test)
python test_backend.py --mode rapid
```

The backend will start on `http://localhost:5555` and automatically serve the test page.

### 4. Open Test Interface

Simply open your browser to:
```
http://localhost:5555
```

The test page will load automatically!

### 5. Run the Test

1. Click **"Run Comprehensive Test"** button in the sidebar
2. Watch components render in real-time
3. Monitor the checklist - items check off as components render
4. Watch the console log for any errors

## Test Coverage

### Component Types Tested

The test exercises **all** rich component types with **19 different components**:

#### Primitive Components
- ✓ Text (with markdown)
- ✓ Badge
- ✓ Icon Text

#### Feedback Components
- ✓ Status Card (with all states: pending, running, completed, failed)
- ✓ Progress Display (0% → 50% → 100%)
- ✓ Progress Bar
- ✓ Status Indicator (with pulse animation)
- ✓ Notification (info, success, warning, error levels)
- ✓ Log Viewer (with info, warning, error logs)

#### Data Components
- ✓ Card (with buttons and actions)
- ✓ Task List (with status updates)
- ✓ **DataFrame** (tabular data with search/sort/filter/export)
- ✓ **Table** (structured data with explicit column definitions)
- ✓ **Chart** (Plotly charts: bar, line, scatter)
- ✓ **Code Block** (syntax highlighted code: Python, SQL, etc.)

#### Specialized Components
- ✓ **Artifact** (HTML/SVG interactive content)

#### Container Components
- ✓ **Container** (groups components in rows/columns)

#### Interactive Components
- ✓ Button (single)
- ✓ Button Group (horizontal/vertical)
- ✓ Button actions (click → backend response)

#### UI State Updates
- ✓ Status Bar Update (updates status bar above input)
- ✓ Task Tracker Update (adds/updates tasks in sidebar)
- ✓ Chat Input Update (changes placeholder/state)

### Update Operations Tested

For each component type, the test validates:

1. **Create** (`lifecycle: create`) - Initial component rendering
2. **Update** (`lifecycle: update`) - Incremental property updates
3. **Replace** - Full component replacement
4. **Remove** - Component removal from DOM

### Interactive Features Tested

- **Button Actions**: Clicking buttons sends actions to backend
- **Action Handling**: Backend receives actions and responds with new components
- **Round-trip Communication**: Full interaction loop validation

## Test Modes

### Realistic Mode (Default)

```bash
python test_backend.py --mode realistic
```

- Includes delays between component updates (0.2-0.5s)
- Simulates real conversation flow
- Easier to observe rendering behavior
- **Recommended for initial validation**

### Rapid Mode

```bash
python test_backend.py --mode rapid
```

- Minimal delays (0.05-0.1s)
- Stress tests rendering performance
- Validates no race conditions
- **Use for performance testing**

## Validation Checklist

The test interface provides real-time validation:

### ✅ Visual Checklist
- Automatically checks off components as they render
- Shows 19 component types
- Green checkmark = successfully rendered

### 📊 Metrics
- **Components Rendered**: Total unique component types
- **Updates Processed**: Total number of updates (create + update + replace)
- **Errors**: Console errors detected

### 🔴 Console Monitor
- Real-time console log display
- Errors highlighted in red
- Warnings in yellow
- Info messages in blue

### 🟢 Status Indicators
- **Backend Status**: Green = connected, Red = disconnected
- **Console Status**: Green = no errors, Red = errors detected

## Using for Webcomponent Pruning

The test suite is designed to validate that pruning doesn't break functionality:

### Pruning Workflow

1. **Run baseline test**:
   ```bash
   python test_backend.py --mode realistic

   # Browser: Open http://localhost:5555 and run test
   # Verify: All 19 components render, 0 errors
   ```

2. **Identify cruft to remove**:
   - Unused imports
   - Dead code paths
   - Deprecated components
   - Development-only utilities

3. **Remove one piece of cruft**:
   ```bash
   # Example: Remove unused import from vanna-chat.ts
   # or delete unused utility file
   ```

4. **Rebuild**:
   ```bash
   npm run build
   ```

5. **Refresh browser test**:
   - Press F5 to reload test page
   - Click "Run Comprehensive Test" again
   - Check console for errors
   - Verify all 12 components still render

6. **If green → continue; if red → investigate**:
   - Green (no errors): Commit the change, continue pruning
   - Red (errors): Revert change, that code was actually needed

7. **Repeat until clean**: Continue removing cruft until webcomponent is minimal

### What to Prune

Look for these common types of cruft:

- ❌ **Unused imports**: Components imported but never used
- ❌ **Development utilities**: Debug helpers, test mocks in production code
- ❌ **Deprecated components**: Old component versions no longer referenced
- ❌ **Unused CSS**: Styles for removed components
- ❌ **Dead code paths**: Conditional logic that's never executed
- ❌ **Commented code**: Old implementations that are commented out
- ❌ **Storybook-only code**: Utilities only used in stories, not production

### What NOT to Prune

Be careful with these:

- ✅ **Base component renderers**: Even if rarely used, may be needed
- ✅ **ComponentRegistry entries**: Needed for dynamic component lookup
- ✅ **Shadow DOM utilities**: Required for web components
- ✅ **Event handlers**: May be used by runtime events
- ✅ **Type definitions**: Used at compile time even if not runtime

## Customizing the Test

### Add More Component Tests

Edit `test_backend.py` and add new test functions:

```python
async def test_my_component(conversation_id: str, request_id: str, mode: str):
    """Test my custom component."""
    my_component = MyComponent(
        id=str(uuid.uuid4()),
        # ... component properties
    )
    yield await yield_chunk(my_component, conversation_id, request_id)
    await delay(mode)

# Then add to run_comprehensive_test():
async for chunk in test_my_component(conversation_id, request_id, mode):
    yield chunk
```

### Modify Test Delays

In `test_backend.py`, adjust the `delay()` function:

```python
async def delay(mode: str, short: float = 0.1, long: float = 0.5):
    if mode == "realistic":
        await asyncio.sleep(long)  # Adjust long delay here
    elif mode == "rapid":
        await asyncio.sleep(short)  # Adjust short delay here
```

### Add Custom Validation

Edit `test-comprehensive.html` and add custom validation logic:

```javascript
// Add to MutationObserver callback
const componentType = node.getAttribute('data-component-type');
if (componentType === 'my_component') {
    // Custom validation for my_component
    console.log('My component rendered!');
}
```

## Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'vanna'`

**Solution**: Make sure vanna is in the Python path:
```bash
cd submodule/vanna-webcomponent
python test_backend.py  # Already adds ../vanna/src to sys.path
```

### Frontend shows "Backend not responding"

**Solutions**:
1. Check backend is running: `curl http://localhost:5555/health`
2. Check CORS is enabled (should be by default)
3. Verify port 5555 is not in use: `lsof -i :5555`

### Components not rendering

**Check**:
1. Browser console for errors (F12)
2. Webcomponent is built: `ls dist/`
3. Test HTML is loading: `<script type="module" src="./dist/index.js"></script>`

### Test page is blank

**Solutions**:
1. Check you're serving from the right directory:
   ```bash
   cd submodule/vanna-webcomponent
   python -m http.server 8080
   ```
2. Open correct URL: `http://localhost:8080/test-comprehensive.html`
3. Check browser console for 404 errors

### Checklist not updating

The checklist tracks components by their `data-component-type` attribute. If components don't have this attribute, they won't be tracked.

**Verify**: Open browser DevTools and inspect rendered components for `data-component-type`.

## Advanced Usage

### Run Backend on Different Port

```bash
python test_backend.py --port 8000
```

Then update `test-comprehensive.html`:
```html
<vanna-chat
    api-url="http://localhost:8000"
    ...
></vanna-chat>
```

### Enable Debug Logging

Add to `test_backend.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Run Type Checking

Validate the backend code with mypy:

```bash
python -m mypy test_backend.py
```

This catches type errors before runtime (e.g., wrong field names in Pydantic models).

### Test Specific Component Only

Modify `run_comprehensive_test()` to only run specific tests:

```python
async def run_comprehensive_test(conversation_id, request_id, mode):
    # Comment out tests you don't want to run
    async for chunk in test_status_card(conversation_id, request_id, mode):
        yield chunk

    # async for chunk in test_progress_display(...):  # Disabled
    #     yield chunk
```

## Architecture

### Backend Flow

1. FastAPI receives POST to `/api/vanna/v2/chat_sse`
2. `chat_sse()` creates async generator
3. Generator yields components wrapped in `ChatStreamChunk`
4. Each chunk serialized to SSE format: `data: {json}\n\n`
5. Stream ends with `data: [DONE]\n\n`

### Frontend Flow

1. `<vanna-chat>` web component connects to backend
2. Opens SSE connection to `/api/vanna/v2/chat_sse`
3. Receives chunks, parses JSON
4. `ComponentManager` processes updates
5. `ComponentRegistry` renders HTML elements
6. Elements appended to shadow DOM container
7. MutationObserver detects new components
8. Checklist updates automatically

### Button Action Flow

1. User clicks button in frontend
2. Button's `action` property sent as new message
3. Backend receives message via `/api/vanna/v2/chat_sse` POST
4. `handle_action_message()` processes action
5. Response components streamed back
6. Frontend renders response

## Files

- **`test_backend.py`** - Python FastAPI backend (400 lines)
- **`test-comprehensive.html`** - Browser test interface (500 lines)
- **`requirements-test.txt`** - Python dependencies
- **`TEST_README.md`** - This documentation

## Next Steps

After validating the webcomponent with this test suite:

1. **Run baseline test** - Verify all components work before pruning
2. **Identify cruft** - Find unused code in the webcomponent
3. **Prune iteratively** - Remove one piece at a time, test after each change
4. **Commit clean code** - Once pruned, commit the cleaned webcomponent
5. **Copy to vanna package** - Integrate cleaned webcomponent into vanna Python package

## Support

If you encounter issues with the test suite:

1. Check this README's Troubleshooting section
2. Verify all dependencies are installed
3. Ensure you're in the correct directory
4. Check browser and terminal console output

---

**Happy Testing!** 🧪
