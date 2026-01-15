import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/app/components/ui/table";
import { cn } from "@/app/components/ui/utils";

interface DataTableProps {
  data: Record<string, any>[];
  className?: string;
  maxRows?: number;
}

export function DataTable({ data, className, maxRows = 10 }: DataTableProps) {
  if (!data || data.length === 0) return null;

  const columns = Object.keys(data[0]);
  const displayData = data.slice(0, maxRows);
  const hasMore = data.length > maxRows;

  return (
    <div className={cn("rounded-lg border border-border/50 overflow-hidden", className)}>
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
