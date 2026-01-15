import { cn } from "@/app/components/ui/utils";

interface StatusBarProps {
  status: string;
  className?: string;
}

export function StatusBar({ status, className }: StatusBarProps) {
  return (
    <div className={cn("flex items-center gap-2 px-4 py-3 border-t border-border/50", className)}>
      <div className="flex items-center gap-2">
        <div className="size-2 rounded-full bg-chart-1 animate-pulse" />
        <span className="text-sm text-muted-foreground">{status}</span>
      </div>
    </div>
  );
}
