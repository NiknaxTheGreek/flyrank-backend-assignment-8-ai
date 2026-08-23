import { SourceSummaryView } from "@/components/source-summary-view";
import { SubmitReportForm } from "@/components/submit-report-form";
import { ReportJobsList } from "@/components/report-jobs-list";

export default function Dashboard() {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
      <div className="xl:col-span-8 space-y-8">
        <SourceSummaryView />
        <ReportJobsList />
      </div>
      <div className="xl:col-span-4 sticky top-8">
        <SubmitReportForm />
      </div>
    </div>
  );
}
