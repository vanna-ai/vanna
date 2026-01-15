# Frontend-Backend Integration Plan

## Overview

This document outlines the plan to connect the new **Clean AI Chat Design** frontend to the existing **Tecknoworks AI** backend (FastAPI + SQLite + OpenAI).

---

## Current State Analysis

### New Frontend (Clean AI Chat Design)
| Aspect | Current State |
|--------|---------------|
| **Data Source** | Static mock data (`src/lib/mock-data.ts`) |
| **Response Handling** | `generateResponse()` function with pattern matching |
| **API Client** | None - all local |
| **Message Format** | `Message { id, role, content, data: { type, payload } }` |

### Existing Backend (FastAPI)
| Aspect | Current State |
|--------|---------------|
| **API Endpoint** | `POST /api/vanna/v2/chat_sse` |
| **Response Format** | Server-Sent Events (SSE) with JSON chunks |
| **Chunk Types** | `simple`, `rich`, `metadata` |
| **Rich Types** | `text`, `dataframe`, `chart`, `card`, `button_group`, `status_indicator` |

---

## Integration Steps

### Step 1: Port API Client

**Source:** `frontends/react-chat/src/services/api-client.ts`
**Destination:** `Create Clean AI Chat Design/src/services/api-client.ts`

```typescript
// Key functionality to port:
- streamChat() - SSE streaming
- sendPollMessage() - Fallback polling
- abort() - Cancel requests
```

**Changes needed:**
- Update import paths for types
- Ensure compatibility with new TypeScript config

---

### Step 2: Create Type Definitions

**Create:** `src/types/api.ts`

```typescript
export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatStreamChunk {
  simple?: {
    content?: string;
  };
  rich?: {
    type: 'text' | 'dataframe' | 'chart' | 'card' | 'button_group' | 'status_indicator';
    content?: string;
    data?: unknown;
  };
  metadata?: {
    conversation_id?: string;
    [key: string]: unknown;
  };
}

export interface ApiClientConfig {
  baseUrl?: string;
  sseEndpoint?: string;
  headers?: Record<string, string>;
  timeout?: number;
}
```

---

### Step 3: Map Backend Response to Frontend Message Format

**Backend sends:**
```json
{
  "rich": {
    "type": "dataframe",
    "data": {
      "columns": ["name", "revenue", "orders"],
      "data": [["Downtown", "$1.2M", 15234], ...]
    }
  }
}
```

**Frontend expects:**
```typescript
{
  id: "msg-123",
  role: "assistant",
  content: "Here are your top performing locations:",
  data: {
    type: "table",
    payload: [
      { name: "Downtown", revenue: "$1.2M", orders: 15234 },
      ...
    ]
  }
}
```

**Mapping function needed:**
```typescript
function mapBackendChunkToMessage(chunk: ChatStreamChunk): Partial<Message> {
  if (chunk.rich?.type === 'dataframe') {
    const { columns, data } = chunk.rich.data as { columns: string[], data: any[][] };
    const payload = data.map(row =>
      Object.fromEntries(columns.map((col, i) => [col, row[i]]))
    );
    return { data: { type: 'table', payload } };
  }

  if (chunk.rich?.type === 'chart') {
    return { data: { type: 'chart', payload: chunk.rich.data } };
  }

  // ... other mappings
}
```

---

### Step 4: Update TecknoworksChat Component

**File:** `src/app/components/chat/TecknoworksChat.tsx`

**Changes:**

1. **Add imports:**
```typescript
import { TecknoworksApiClient } from '@/services/api-client';
import type { ChatStreamChunk } from '@/types/api';
```

2. **Add state for API client:**
```typescript
const apiClientRef = useRef<TecknoworksApiClient | null>(null);
const [conversationId, setConversationId] = useState<string>('');

useEffect(() => {
  apiClientRef.current = new TecknoworksApiClient({ baseUrl: '' });
}, []);
```

3. **Replace `handleSendMessage`:**
```typescript
const handleSendMessage = async (text?: string) => {
  const messageText = text || input.trim();
  if (!messageText || isLoading || !apiClientRef.current) return;

  // Add user message
  const userMessage: Message = {
    id: Date.now().toString(),
    role: "user",
    content: messageText,
  };
  setMessages(prev => [...prev, userMessage]);
  setInput("");
  setIsLoading(true);

  // Create placeholder assistant message
  const assistantMessageId = (Date.now() + 1).toString();
  let accumulatedContent = '';
  let messageData: Message['data'] = undefined;

  setMessages(prev => [...prev, {
    id: assistantMessageId,
    role: "assistant",
    content: "", // Will be updated
  }]);

  try {
    for await (const chunk of apiClientRef.current.streamChat({
      message: messageText,
      conversation_id: conversationId || undefined,
    })) {
      // Update conversation ID
      if (chunk.metadata?.conversation_id && !conversationId) {
        setConversationId(chunk.metadata.conversation_id);
      }

      // Process chunk
      const { content, data } = processChunk(chunk);
      if (content) accumulatedContent += content;
      if (data) messageData = data;

      // Update message
      setMessages(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? { ...msg, content: accumulatedContent, data: messageData }
          : msg
      ));
    }
  } catch (error) {
    console.error('Chat error:', error);
    setMessages(prev => prev.map(msg =>
      msg.id === assistantMessageId
        ? { ...msg, content: "Sorry, something went wrong. Please try again." }
        : msg
    ));
  } finally {
    setIsLoading(false);
  }
};
```

4. **Add chunk processor:**
```typescript
function processChunk(chunk: ChatStreamChunk): { content?: string, data?: Message['data'] } {
  // Handle simple text
  if (chunk.simple?.content) {
    return { content: chunk.simple.content };
  }

  // Handle rich components
  if (chunk.rich) {
    const { type, content, data } = chunk.rich;

    switch (type) {
      case 'text':
        return { content: content || '' };

      case 'dataframe': {
        const df = data as { columns?: string[], data?: unknown[][] };
        if (df?.columns && df?.data) {
          const payload = df.data.map(row =>
            Object.fromEntries(df.columns!.map((col, i) => [col, row[i]]))
          );
          return { data: { type: 'table', payload } };
        }
        break;
      }

      case 'chart':
        // Map backend chart format to frontend format
        return {
          data: {
            type: 'chart',
            payload: mapChartData(data)
          }
        };

      case 'card':
        return { data: { type: 'card', payload: data } };

      case 'button_group':
        return { data: { type: 'buttons', payload: (data as any)?.buttons } };

      case 'status_indicator':
        // Handle status updates (optional: update StatusBar)
        return {};
    }
  }

  return {};
}
```

---

### Step 5: Add Vite Proxy Configuration

**File:** `vite.config.ts`

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

---

### Step 6: Chart Data Mapping

**Backend format (Plotly-style):**
```json
{
  "type": "area",
  "x": ["Jul", "Aug", "Sep"],
  "y": [2350000, 2420000, 2510000],
  "title": "Revenue Trend"
}
```

**Frontend format (Recharts):**
```typescript
{
  type: "area",
  data: [
    { month: "Jul", revenue: 2350000 },
    { month: "Aug", revenue: 2420000 },
    { month: "Sep", revenue: 2510000 },
  ],
  dataKeys: [{ key: "revenue", name: "Revenue", color: "hsl(217, 91%, 60%)" }],
  xAxisKey: "month",
  title: "Revenue Trend"
}
```

**Mapping function:**
```typescript
function mapChartData(backendChart: any): any {
  // If already in Recharts format, return as-is
  if (Array.isArray(backendChart?.data)) {
    return backendChart;
  }

  // Convert Plotly-style to Recharts format
  const { x, y, type = 'area', title } = backendChart;

  if (x && y) {
    const data = x.map((label: string, i: number) => ({
      label,
      value: y[i],
    }));

    return {
      type,
      data,
      dataKeys: [{ key: 'value', name: title || 'Value', color: 'hsl(217, 91%, 60%)' }],
      xAxisKey: 'label',
      title,
    };
  }

  return backendChart;
}
```

---

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `src/services/api-client.ts` | CREATE | Port from react-chat, SSE streaming |
| `src/types/api.ts` | CREATE | Type definitions for API |
| `src/app/components/chat/TecknoworksChat.tsx` | MODIFY | Replace mock with real API |
| `vite.config.ts` | MODIFY | Add proxy configuration |
| `src/lib/mock-data.ts` | KEEP | Can be used as fallback |

---

## Testing Checklist

- [ ] Backend starts on port 8000
- [ ] Frontend starts on port 3000
- [ ] Vite proxy routes `/api/*` to backend
- [ ] User messages send successfully
- [ ] SSE streaming works
- [ ] Text responses render correctly
- [ ] Tables render with proper formatting
- [ ] Charts render with Recharts
- [ ] Cards render with stats
- [ ] Error handling works gracefully
- [ ] Status indicators update during loading

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     NEW FRONTEND (Port 3000)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    TecknoworksChat.tsx                     │  │
│  │  ┌─────────────────┐    ┌─────────────────────────────┐   │  │
│  │  │   User Input    │───▶│   apiClient.streamChat()    │   │  │
│  │  └─────────────────┘    └──────────────┬──────────────┘   │  │
│  │                                        │                   │  │
│  │  ┌─────────────────┐    ┌─────────────▼──────────────┐   │  │
│  │  │  ChatMessage    │◀───│   processChunk()            │   │  │
│  │  │  - DataTable    │    │   - Map dataframe → table   │   │  │
│  │  │  - ChartRenderer│    │   - Map chart → recharts    │   │  │
│  │  │  - Card         │    │   - Map card → stats        │   │  │
│  │  └─────────────────┘    └─────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                        Vite Proxy │ /api/* → :8000
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (Port 8000)                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Server                          │  │
│  │  POST /api/vanna/v2/chat_sse                              │  │
│  │       │                                                    │  │
│  │       ▼                                                    │  │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐  │  │
│  │  │ OpenAI LLM  │──▶│ SQL Gen     │──▶│ SQLite Query    │  │  │
│  │  │ (or Azure)  │   │             │   │ urban_eats.db   │  │  │
│  │  └─────────────┘   └─────────────┘   └────────┬────────┘  │  │
│  │                                               │            │  │
│  │                                               ▼            │  │
│  │                                   SSE Stream Response      │  │
│  │                                   - status_indicator       │  │
│  │                                   - text                   │  │
│  │                                   - dataframe              │  │
│  │                                   - chart                  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Estimated Timeline

| Task | Effort |
|------|--------|
| Port API client + types | 30 min |
| Update TecknoworksChat | 1-2 hours |
| Chart data mapping | 30 min |
| Vite proxy config | 10 min |
| Testing & debugging | 1-2 hours |
| **Total** | **3-5 hours** |

---

## Questions to Resolve

1. **Should we keep mock data as fallback?** (Recommended: Yes, for offline demos)
2. **Do we need WebSocket support?** (Backend supports it, but SSE is simpler)
3. **Should status indicators update the StatusBar?** (Recommended: Yes)

---

## Next Steps

1. Start backend: `python quickstart.py`
2. Copy API client to new frontend
3. Update TecknoworksChat.tsx
4. Test locally
5. Build and deploy
