import { useState, useEffect, useRef } from "react";
import { cn } from "@/app/components/ui/utils";
import { Button } from "@/app/components/ui/button";
import { Card } from "@/app/components/ui/card";
import { ScrollArea } from "@/app/components/ui/scroll-area";
import { Input } from "@/app/components/ui/input";
import { Badge } from "@/app/components/ui/badge";
import { BarChart3, Minimize2, Send } from "lucide-react";
import { ChatMessage, Message } from "./ChatMessage";
import { StatusBar } from "./StatusBar";
import { TecknoworksApiClient } from "@/services/api-client";
import type { ChatStreamChunk, DataFrameData, ChartData, CardData, ButtonGroupData } from "@/types/api";
import {
  suggestedQuestions,
} from "@/lib/mock-data";

// Flag to use mock data (for offline demos)
const USE_MOCK_DATA = false;

export function TecknoworksChat({ isEmbedded = false }: { isEmbedded?: boolean }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [conversationId, setConversationId] = useState<string>("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const apiClientRef = useRef<TecknoworksApiClient | null>(null);

  // Initialize API client
  useEffect(() => {
    apiClientRef.current = new TecknoworksApiClient({ baseUrl: "" });
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      const viewport = scrollRef.current.closest('[data-slot="scroll-area"]')?.querySelector('[data-slot="scroll-area-viewport"]') as HTMLElement;
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      } else {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    }
  }, [messages]);

  /**
   * Process a backend chunk and convert to frontend Message data format
   */
  const processChunk = (chunk: ChatStreamChunk): { content?: string; data?: Message["data"] } => {
    const { rich, simple } = chunk;

    // Handle simple content (plain text)
    if (simple?.content) {
      return { content: simple.content };
    }

    if (!rich) return {};

    const { type, content, data } = rich;

    switch (type) {
      case "text":
        return { content: content || "" };

      case "status_indicator": {
        const statusData = data as { status?: string; message?: string };
        if (statusData?.message) {
          setStatusMessage(statusData.message);
        }
        if (statusData?.status === "idle") {
          setStatusMessage("");
        }
        return {};
      }

      case "dataframe": {
        const dfData = data as DataFrameData;
        if (!dfData?.columns) return {};

        // Backend can send data in multiple formats:
        // 1. rows: array of objects (preferred format from backend)
        // 2. data: array of objects (already in correct format)
        // 3. data: 2D array (columns + data[][] needs conversion)

        let payload: Record<string, unknown>[] | undefined;

        if (dfData.rows && Array.isArray(dfData.rows)) {
          // Format 1: rows array of objects - use directly
          payload = dfData.rows;
        } else if (dfData.data && Array.isArray(dfData.data)) {
          if (dfData.data.length > 0) {
            const firstItem = dfData.data[0];
            if (Array.isArray(firstItem)) {
              // Format 3: 2D array - convert to objects
              payload = (dfData.data as unknown[][]).map((row) =>
                Object.fromEntries(dfData.columns.map((col, i) => [col, row[i]]))
              );
            } else if (typeof firstItem === 'object' && firstItem !== null) {
              // Format 2: Already array of objects
              payload = dfData.data as Record<string, unknown>[];
            }
          }
        }

        if (payload) {
          return { data: { type: "table", payload: { data: payload, sql_query: dfData.sql_query } } };
        }
        return {};
      }

      case "chart":
      case "plotly_figure": {
        const chartData = data as ChartData;
        if (chartData) {
          // Map backend chart format to frontend format
          const mappedChart = mapChartData(chartData);
          return { data: { type: "chart", payload: mappedChart } };
        }
        return {};
      }

      case "card": {
        const cardData = data as CardData;
        if (cardData) {
          return { data: { type: "card", payload: cardData } };
        }
        return {};
      }

      case "button_group": {
        const buttonData = data as ButtonGroupData;
        if (buttonData?.buttons) {
          return { data: { type: "buttons", payload: buttonData.buttons } };
        }
        return {};
      }

      case "notification": {
        const notifData = data as { message?: string; level?: string };
        if (notifData?.message) {
          return { content: `[${notifData.level?.toUpperCase() || 'INFO'}] ${notifData.message}` };
        }
        return {};
      }

      case "task_tracker":
      case "component_update":
        // These are internal updates, don't render them
        return {};

      default:
        // For unknown types, try to show content
        if (content) {
          return { content };
        }
        return {};
    }
  };

  /**
   * Map backend chart data to Recharts format
   */
  const mapChartData = (backendChart: ChartData): any => {
    // If already in Recharts format (has data array), return as-is
    if (Array.isArray(backendChart?.data)) {
      return {
        type: backendChart.type || backendChart.chart_type || "area",
        data: backendChart.data,
        dataKeys: [{ key: backendChart.y_axis || "value", name: backendChart.title || "Value", color: "hsl(217, 91%, 60%)" }],
        xAxisKey: backendChart.x_axis || "label",
        title: backendChart.title,
      };
    }

    // Convert Plotly-style (x/y arrays) to Recharts format
    const { x, y, type, chart_type, title } = backendChart;

    if (x && y && Array.isArray(x) && Array.isArray(y)) {
      const data = x.map((label: string, i: number) => ({
        label,
        value: y[i],
      }));

      return {
        type: type || chart_type || "area",
        data,
        dataKeys: [{ key: "value", name: title || "Value", color: "hsl(217, 91%, 60%)" }],
        xAxisKey: "label",
        title,
      };
    }

    // Return as-is if we can't map it
    return backendChart;
  };

  /**
   * Handle sending a message - streams from real API
   */
  const handleSendMessage = async (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText || isLoading) return;

    // If using mock data (for demos), use the old logic
    if (USE_MOCK_DATA) {
      handleMockMessage(messageText);
      return;
    }

    if (!apiClientRef.current) {
      console.error("API client not initialized");
      return;
    }

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: messageText,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setStatusMessage("Understanding your question...");

    // Create placeholder assistant message
    const assistantMessageId = (Date.now() + 1).toString();
    let accumulatedContent = "";
    let messageData: Message["data"] = undefined;

    setMessages((prev) => [
      ...prev,
      {
        id: assistantMessageId,
        role: "assistant",
        content: "",
      },
    ]);

    try {
      for await (const chunk of apiClientRef.current.streamChat({
        message: messageText,
        conversation_id: conversationId || undefined,
      })) {
        // Update conversation ID from first chunk
        if (chunk.conversation_id && !conversationId) {
          setConversationId(chunk.conversation_id);
        }

        // Process the chunk
        const { content, data } = processChunk(chunk);

        if (content) {
          accumulatedContent += content;
        }
        if (data) {
          messageData = data;
        }

        // Update the assistant message
        if (accumulatedContent || messageData) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: accumulatedContent, data: messageData }
                : msg
            )
          );
        }
      }

      // If we got no content at all, show a fallback
      if (!accumulatedContent && !messageData) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: "I processed your request but didn't receive a displayable response. Please try rephrasing your question." }
              : msg
          )
        );
      }

      setStatusMessage("");
    } catch (error) {
      console.error("[TecknoworksChat] Error:", error);
      const errorMessage = error instanceof Error ? error.message : "Unknown error";

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: `Sorry, something went wrong: ${errorMessage}. Please try again.` }
            : msg
        )
      );
      setStatusMessage("");
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Mock message handler for offline demos
   */
  const handleMockMessage = async (messageText: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: messageText,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Import mock data dynamically to avoid circular deps
    const { generateMockResponse } = await import("@/lib/mock-data");

    setTimeout(() => {
      const response = generateMockResponse(messageText);
      setMessages((prev) => [...prev, response]);
      setIsLoading(false);
    }, 1500);
  };

  const handleSuggestionClick = (question: string) => {
    handleSendMessage(question);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (isMinimized && !isEmbedded) {
    return (
      <Button
        onClick={() => setIsMinimized(false)}
        className="fixed bottom-6 right-6 size-14 rounded-full shadow-lg bg-chart-1 hover:bg-chart-1/90 animate-pulse hover:animate-none"
      >
        <BarChart3 className="size-6" />
      </Button>
    );
  }

  return (
    <Card className={cn(
      "shadow-2xl flex flex-col bg-card/80 backdrop-blur-sm overflow-hidden",
      isEmbedded
        ? "w-full h-[750px] rounded-2xl border-2 border-chart-1/30"
        : "fixed bottom-6 right-6 w-[450px] h-[700px] max-w-[calc(100vw-3rem)] max-h-[calc(100vh-3rem)] border-border/50"
    )}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/50 bg-muted/30 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="size-8 rounded-lg bg-chart-1 flex items-center justify-center">
            <BarChart3 className="size-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold">Urban Eats AI</h3>
            <p className="text-xs text-muted-foreground">Restaurant Analytics</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs border-chart-1/50 text-chart-1">
            Live
          </Badge>
          {!isEmbedded && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMinimized(true)}
              className="size-8 p-0"
            >
              <Minimize2 className="size-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1">
        <div className="px-4 py-4" ref={scrollRef}>
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center px-6">
              <div className="size-16 rounded-2xl bg-chart-1/20 flex items-center justify-center mb-4">
                <BarChart3 className="size-8 text-chart-1" />
              </div>
              <h2 className="text-xl font-semibold mb-2">Welcome to Urban Eats AI</h2>
              <p className="text-sm text-muted-foreground mb-6">
                Ask questions about your restaurant data and get instant insights with tables, charts, and analytics.
              </p>
              <div className="w-full space-y-2">
                <p className="text-xs text-muted-foreground mb-3">Try asking:</p>
                <div className="grid grid-cols-2 gap-2">
                  {suggestedQuestions.map((suggestion, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      size="sm"
                      onClick={() => handleSuggestionClick(suggestion.question)}
                      className="h-auto py-2 px-3 text-xs text-left whitespace-normal border-border/50 hover:bg-chart-1/10 hover:border-chart-1/50"
                    >
                      {suggestion.label}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div>
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onSuggestionClick={handleSuggestionClick}
                />
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Status Bar */}
      {(isLoading || statusMessage) && <StatusBar status={statusMessage || "Analyzing your data..."} />}

      {/* Input Area */}
      <div className="p-4 border-t border-border/50 bg-muted/30">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your restaurant data..."
            className="flex-1 bg-background border-border/50"
            disabled={isLoading}
          />
          <Button
            onClick={() => handleSendMessage()}
            disabled={!input.trim() || isLoading}
            className="bg-chart-1 hover:bg-chart-1/90"
            size="icon"
          >
            <Send className="size-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
}
