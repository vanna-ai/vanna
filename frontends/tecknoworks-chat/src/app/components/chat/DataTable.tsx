import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/app/components/ui/table";
import { cn } from "@/app/components/ui/utils";

import {
  Code,
  Database,
  ChevronDown,
  ChevronRight
} from "lucide-react";
import { useState } from "react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/app/components/ui/collapsible";
import { Button } from "@/app/components/ui/button";

interface DataTableProps {
  data: Record<string, any>[];
  className?: string;
  maxRows?: number;
  sqlQuery?: string;
}

export function DataTable({ data, className, maxRows = 10, sqlQuery }: DataTableProps) {
  const [isSqlOpen, setIsSqlOpen] = useState(false);

  if (!data || data.length === 0) return null;

  const columns = Object.keys(data[0]);
  const displayData = data.slice(0, maxRows);
  const hasMore = data.length > maxRows;

  return (
    <div className={cn("rounded-lg border border-border/50 overflow-hidden", className)}>
      {sqlQuery && (
        <Collapsible
          open={isSqlOpen}
          onOpenChange={setIsSqlOpen}
          className="border-b border-border/50 bg-muted/30"
        >
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="w-full flex items-center justify-between px-4 py-2 hover:bg-muted/50 h-9"
            >
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Database className="size-3.5" />
                <span>Generated SQL</span>
              </div>
              {isSqlOpen ? (
                <ChevronDown className="size-3.5 text-muted-foreground" />
              ) : (
                <ChevronRight className="size-3.5 text-muted-foreground" />
              )}
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="px-4 py-3 bg-muted/20 overflow-x-auto">
              <pre className="text-xs font-mono text-muted-foreground leading-relaxed whitespace-pre-wrap">
                {sqlQuery}
              </pre>
            </div>
          </CollapsibleContent>
        </Collapsible>
      )}
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/30">
              {columns.map((column) => (
                <TableHead key={column} className="font-medium">
                  {column.charAt(0).toUpperCase() + column.slice(1).replace(/([A-Z])/g, ' $1')}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {displayData.map((row, i) => (
              <TableRow key={i} className="hover:bg-muted/20">
                {columns.map((column) => (
                  <TableCell key={column}>
                    {typeof row[column] === 'number' && column.toLowerCase().includes('revenue')
                      ? `$${row[column].toLocaleString()}`
                      : typeof row[column] === 'number'
                      ? row[column].toLocaleString()
                      : row[column]}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      {hasMore && (
        <div className="px-4 py-2 text-xs text-muted-foreground bg-muted/20 text-center border-t border-border/50">
          Showing {displayData.length} of {data.length} rows
        </div>
      )}
    </div>
  );
}
