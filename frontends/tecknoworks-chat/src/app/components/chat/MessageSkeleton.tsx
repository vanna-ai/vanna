import { Skeleton } from "@/app/components/ui/skeleton";

export function MessageSkeleton() {
  return (
    <div className="flex gap-3 mb-6">
      <div className="flex-shrink-0 size-8 rounded-full bg-chart-1/20 flex items-center justify-center">
        <div className="size-4 rounded-full bg-chart-1 animate-pulse" />
      </div>
      
      <div className="flex flex-col gap-3 max-w-[85%]">
        <div className="rounded-2xl px-4 py-3 bg-muted/50">
          <Skeleton className="h-4 w-64 mb-2" />
          <Skeleton className="h-4 w-48" />
        </div>
      </div>
    </div>
  );
}
