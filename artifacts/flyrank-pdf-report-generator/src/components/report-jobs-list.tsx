import { getListReportsQueryKey, useListReports } from "@workspace/api-client-react";
import { ReportJobRow } from "./report-job-row";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { FileText, Inbox } from "lucide-react";
import { useMemo } from "react";

export function ReportJobsList() {
  // Poll every 2 seconds to keep the list fresh while jobs might be running
  const { data: reports, isLoading } = useListReports({
    query: { queryKey: getListReportsQueryKey(), refetchInterval: 2000 }
  });

  const sortedReports = useMemo(() => {
    if (!reports) return [];
    return [...reports].sort((a, b) => {
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });
  }, [reports]);

  if (isLoading) {
    return (
      <Card className="border-border shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg">Recent Reports</CardTitle>
          <CardDescription>Loading historical jobs...</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-16 w-full rounded-md" />
          <Skeleton className="h-16 w-full rounded-md" />
          <Skeleton className="h-16 w-full rounded-md" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-border shadow-sm">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          Recent Reports
        </CardTitle>
        <CardDescription>
          Track execution state and download retained artifacts.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {sortedReports.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center border rounded-md border-dashed border-border bg-muted/20">
            <Inbox className="h-10 w-10 text-muted-foreground/50 mb-3" />
            <p className="text-sm font-medium text-foreground">No reports generated yet</p>
            <p className="text-xs text-muted-foreground mt-1 max-w-sm">
              Queue a new report generation job using the form above to see it appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {sortedReports.map((report) => (
              <ReportJobRow key={report.id} initialReport={report} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
