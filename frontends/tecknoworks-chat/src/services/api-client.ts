/**
 * Tecknoworks API Client
 * Handles communication with the FastAPI backend via SSE or Polling
 */

import type {
  ChatRequest,
  ChatStreamChunk,
  ChatResponse,
  ApiClientConfig,
} from '@/types/api';

const DEFAULT_CONFIG: Required<ApiClientConfig> = {
  baseUrl: '',
  sseEndpoint: '/api/vanna/v2/chat_sse',
  pollEndpoint: '/api/vanna/v2/chat_poll',
  headers: {},
  timeout: 60000,
};

export class TecknoworksApiClient {
  private config: Required<ApiClientConfig>;
  private abortController: AbortController | null = null;

  constructor(config: ApiClientConfig = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Get the full URL for an endpoint
   */
  private getUrl(endpoint: string): string {
    return `${this.config.baseUrl}${endpoint}`;
  }

  /**
   * Stream chat responses using Server-Sent Events
   */
  async *streamChat(request: ChatRequest): AsyncGenerator<ChatStreamChunk> {
    this.abortController = new AbortController();
    const url = this.getUrl(this.config.sseEndpoint);

    try {
      console.log('[TecknoworksApiClient] Sending request to:', url);
      console.log('[TecknoworksApiClient] Request body:', request);

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.config.headers,
        },
        body: JSON.stringify(request),
        signal: this.abortController.signal,
      });

      console.log('[TecknoworksApiClient] Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('[TecknoworksApiClient] Error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Response body is not readable');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data && data !== '[DONE]') {
              try {
                const chunk: ChatStreamChunk = JSON.parse(data);
                console.log('[TecknoworksApiClient] Parsed chunk:', chunk.rich?.type);
                yield chunk;
              } catch (e) {
                console.warn('[TecknoworksApiClient] Failed to parse SSE data:', e);
              }
            }
          }
        }
      }

      // Process any remaining buffer
      if (buffer.startsWith('data: ')) {
        const data = buffer.slice(6).trim();
        if (data && data !== '[DONE]') {
          try {
            const chunk: ChatStreamChunk = JSON.parse(data);
            yield chunk;
          } catch (e) {
            console.warn('[TecknoworksApiClient] Failed to parse final buffer:', e);
          }
        }
      }

      console.log('[TecknoworksApiClient] Stream completed');
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        console.log('[TecknoworksApiClient] Request aborted');
        return;
      }
      console.error('[TecknoworksApiClient] Stream error:', error);
      throw error;
    } finally {
      this.abortController = null;
    }
  }

  /**
   * Send a chat message using polling (fallback)
   */
  async sendPollMessage(request: ChatRequest): Promise<ChatResponse> {
    const url = this.getUrl(this.config.pollEndpoint);

    console.log('[TecknoworksApiClient] Polling:', url);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.config.headers,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[TecknoworksApiClient] Poll error:', errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Abort any ongoing request
   */
  abort(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<ApiClientConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Check if the API is reachable
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.config.baseUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

// Export a singleton instance
export const apiClient = new TecknoworksApiClient();
