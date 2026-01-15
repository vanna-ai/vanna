/**
 * API type definitions for Tecknoworks AI Chat
 */

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Component types matching backend ComponentType enum
 */
export type RichComponentType =
  // Basic components
  | 'text'
  | 'card'
  | 'container'
  // Primitive UI components
  | 'status_card'
  | 'progress_display'
  | 'log_viewer'
  | 'badge'
  | 'icon_text'
  // Interactive components
  | 'task_list'
  | 'progress_bar'
  | 'button'
  | 'button_group'
  // Data components
  | 'table'
  | 'dataframe'
  | 'chart'
  | 'code_block'
  // Status components
  | 'status_indicator'
  | 'notification'
  | 'alert'
  // Artifact components
  | 'artifact'
  // UI state components
  | 'status_bar_update'
  | 'task_tracker_update'
  | 'chat_input_update'
  // Legacy/special
  | 'plotly_figure'
  | 'task_tracker'
  | 'component_update'
  | 'tool_execution';

export type ComponentLifecycle = 'create' | 'update' | 'replace' | 'remove';

export interface ChatStreamChunk {
  rich: {
    type: RichComponentType;
    id?: string;
    content?: string;
    data?: unknown;
    lifecycle?: ComponentLifecycle;
    visible?: boolean;
  };
  simple?: {
    content?: string;
  };
  conversation_id: string;
  request_id: string;
  timestamp?: number;
}

export interface ChatResponse {
  chunks: ChatStreamChunk[];
  conversation_id: string;
  request_id: string;
  total_chunks: number;
}

export interface ApiClientConfig {
  baseUrl?: string;
  sseEndpoint?: string;
  pollEndpoint?: string;
  headers?: Record<string, string>;
  timeout?: number;
}

// Rich component data types
export interface DataFrameData {
  columns: string[];
  // Backend can send data in two formats:
  data?: unknown[][] | Record<string, unknown>[]; // 2D array or array of objects
  rows?: Record<string, unknown>[]; // Alternative format from backend
  title?: string;
  description?: string;
  row_count?: number;
  column_count?: number;
}

export interface ChartData {
  type?: 'area' | 'line' | 'bar';
  chart_type?: 'area' | 'line' | 'bar';
  x?: string[];
  y?: number[];
  data?: Record<string, unknown>[];
  title?: string;
  x_axis?: string;
  y_axis?: string | string[];
}

export interface CardData {
  title?: string;
  content?: string;
  trend?: string;
  stats?: Array<{ label: string; value: string }>;
}

export interface ButtonGroupData {
  buttons: Array<{ label: string; action?: string }>;
}

export interface StatusIndicatorData {
  status: 'idle' | 'working' | 'success' | 'error';
  message?: string;
}
