import { useState } from "react";
import { ReportJob, useGetReport, downloadReport, getGetReportQueryKey } from "@workspace/api-client-react";
import { Button } from "@/components/ui/button";
import { 
  FileText, 
  Loader2, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Download,
  AlertTriangle
} from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function ReportJobRow({ initialReport }: { initialReport: ReportJob }) {
  const [isDownloading, setIsDownloading] = useState(false);
  
  // If the job is pending or running, poll it frequently.
  const isPolling = initialReport.status === "pending" || initialReport.status === "running";
  
  const { data: liveReport } = useGetReport(initialReport.id, {
    query: {
      queryKey: getGetReportQueryKey(initialReport.id),
      initialData: initialReport,
      refetchInterval: isPolling ? 1000 : false,
    }
  });

  const report = liveReport || initialReport;

  const handleDownload = async () => {
    try {
      setIsDownloading(true);
      const blob = await downloadReport(report.id);
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `report-${report.id.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success("Download started");
    } catch (err) {
      toast.error("Failed to download PDF", {
        description: "The artifact might have expired or an error occurred."
      });
    } finally {
      setIsDownloading(false);
    }
  };

  const getStatusIcon = () => {
    switch (report.status) {
      case "pending": return <Clock className="h-5 w-5 text-muted-foreground" />;
      case "running": return <Loader2 className="h-5 w-5 text-primary animate-spin" />;
      case "completed": return <CheckCircle2 className="h-5 w-5 text-emerald-500" />;
      case "failed": return <XCircle className="h-5 w-5 text-destructive" />;
    }
  };

  const getStatusBadge = () => {
    switch (report.status) {
      case "pending": return <Badge variant="secondary">Queued</Badge>;
      case "running": return <Badge variant="default" className="bg-primary/20 text-primary hover:bg-primary/30">Processing</Badge>;
      case "completed": return <Badge variant="outline" className="text-emerald-600 border-emerald-200 bg-emerald-50">Completed</Badge>;
      case "failed": return <Badge variant="destructive">Failed</Badge>;
    }
  };

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-lg border border-border/60 bg-card hover:bg-muted/10 transition-colors gap-4">
      <div className="flex items-start gap-4">
        <div className="mt-1">
          {getStatusIcon()}
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h4 className="font-semibold text-foreground">{report.title}</h4>
            {getStatusBadge()}
          </div>
          <div className="text-xs text-muted-foreground flex items-center gap-3 flex-wrap">
            <span className="font-mono bg-muted px-1.5 py-0.5 rounded text-[10px]">
              {report.id.slice(0, 8)}
            </span>
            <span title={format(new Date(report.created_at), 'PPpp')}>
              Created {formatDistanceToNow(new Date(report.created_at), { addSuffix: true })}
            </span>
            {report.source_record_count > 0 && (
              <span className="flex items-center gap-1">
                <FileText className="w-3 h-3" />
                {report.source_record_count.toLocaleString()} records
              </span>
            )}
          </div>
          {report.error_message && (
            <div className="mt-2 text-xs text-destructive flex items-start gap-1.5 bg-destructive/10 p-2 rounded-md max-w-lg">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span className="font-mono break-all">{report.error_message}</span>
            </div>
          )}
        </div>
      </div>
      
      <div className="flex items-center self-end sm:self-auto ml-10 sm:ml-0">
        {report.status === "completed" && report.artifact_reference && (
          <Button 
            variant="secondary" 
            size="sm" 
            onClick={handleDownload}
            disabled={isDownloading}
            className="w-full sm:w-auto font-medium shadow-sm"
            data-testid={`button-download-${report.id}`}
          >
            {isDownloading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Download className="h-4 w-4 mr-2" />
            )}
            Download PDF
          </Button>
        )}
        
        {report.status === "failed" && (
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-help">
                <XCircle className="w-3.5 h-3.5" />
                Job Failed
              </div>
            </TooltipTrigger>
            <TooltipContent side="left">
              Retry by creating a new job
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </div>
  );
}
