import { useGetSourceSummary } from "@workspace/api-client-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Database, AlertCircle } from "lucide-react";

export function SourceSummaryView() {
  const { data: summary, isLoading, isError } = useGetSourceSummary();

  if (isLoading) {
    return (
      <Card className="border-border shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg">Source Data Aggregate</CardTitle>
          <CardDescription>Fetching statistics...</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <Skeleton className="h-20 w-full rounded-md" />
            <Skeleton className="h-20 w-full rounded-md" />
            <Skeleton className="h-20 w-full rounded-md" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isError || !summary) {
    return (
      <Card className="border-border shadow-sm border-destructive/20 bg-destructive/5">
        <CardContent className="flex flex-col items-center justify-center p-6 text-center">
          <AlertCircle className="h-8 w-8 text-destructive mb-2" />
          <p className="text-sm font-medium text-destructive">Failed to load source summary</p>
          <p className="text-xs text-muted-foreground mt-1">Make sure the API server is running.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-border shadow-sm relative overflow-hidden">
      <div className="absolute top-0 right-0 p-6 opacity-5 pointer-events-none">
        <Database className="w-32 h-32" />
      </div>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          Source Data Aggregate
        </CardTitle>
        <CardDescription>
          Read-only aggregate of seeded records used for report generation.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-muted/40 p-4 rounded-lg border border-border/50">
            <p className="text-sm text-muted-foreground font-medium mb-1">Total Records</p>
            <p className="text-2xl font-semibold font-mono tracking-tight" data-testid="text-record-count">
              {summary.record_count.toLocaleString()}
            </p>
          </div>
          <div className="bg-muted/40 p-4 rounded-lg border border-border/50">
            <p className="text-sm text-muted-foreground font-medium mb-1">Total Amount</p>
            <p className="text-2xl font-semibold font-mono tracking-tight" data-testid="text-total-amount">
              ${summary.total_amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
          <div className="bg-muted/40 p-4 rounded-lg border border-border/50">
            <p className="text-sm text-muted-foreground font-medium mb-1">Average Amount</p>
            <p className="text-2xl font-semibold font-mono tracking-tight" data-testid="text-avg-amount">
              ${summary.average_amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
        
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-foreground">Category Distribution</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {Object.entries(summary.category_totals).map(([category, total]) => (
              <div key={category} className="flex justify-between items-center p-2 rounded border bg-card text-sm">
                <span className="text-muted-foreground capitalize">{category}</span>
                <span className="font-mono font-medium">${total.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
