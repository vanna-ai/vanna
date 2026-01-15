import { cn } from "@/app/components/ui/utils";
import { DataTable } from "./DataTable";
import { ChartRenderer } from "./ChartRenderer";
import { Card } from "@/app/components/ui/card";
import { Button } from "@/app/components/ui/button";
import { TrendingUp } from "lucide-react";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  data?: {
    type: "table" | "chart" | "card" | "buttons";
    payload?: any;
  };
}

interface ChatMessageProps {
  message: Message;
  onSuggestionClick?: (question: string) => void;
}

export function ChatMessage({ message, onSuggestionClick }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3 mb-6 animate-in fade-in slide-in-from-bottom-2 duration-300", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="flex-shrink-0 size-8 rounded-full bg-chart-1/20 flex items-center justify-center">
          <div className="size-4 rounded-full bg-chart-1" />
        </div>
      )}
      
      <div className={cn("flex flex-col gap-3 max-w-[85%]", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3",
            isUser
              ? "bg-chart-1 text-white"
              : "bg-muted/50 text-foreground"
          )}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>

        {message.data && !isUser && (
          <div className="w-full">
            {message.data.type === "table" && (
              <DataTable data={message.data.payload} />
            )}

            {message.data.type === "chart" && (
              <ChartRenderer
                type={message.data.payload.type}
                data={message.data.payload.data}
                dataKeys={message.data.payload.dataKeys}
                xAxisKey={message.data.payload.xAxisKey}
                title={message.data.payload.title}
              />
            )}

            {message.data.type === "card" && (
              <Card className="p-6 bg-card/50 border-border/50">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg">{message.data.payload.title}</h3>
                    {message.data.payload.trend && (
                      <div className="flex items-center gap-1 text-sm text-chart-1">
                        <TrendingUp className="size-4" />
                        <span>{message.data.payload.trend}</span>
                      </div>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    {message.data.payload.stats?.map((stat: any, index: number) => (
                      <div key={index}>
                        <p className="text-sm text-muted-foreground">{stat.label}</p>
                        <p className="text-2xl font-semibold mt-1">{stat.value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            )}

            {message.data.type === "buttons" && (
              <div className="flex flex-wrap gap-2">
                {message.data.payload.map((button: any, index: number) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onClick={() => onSuggestionClick?.(button.action)}
                    className="border-border/50 hover:bg-chart-1/10 hover:border-chart-1/50"
                  >
                    {button.label}
                  </Button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex-shrink-0 size-8 rounded-full bg-muted flex items-center justify-center">
          <span className="text-xs font-medium">You</span>
        </div>
      )}
    </div>
  );
}