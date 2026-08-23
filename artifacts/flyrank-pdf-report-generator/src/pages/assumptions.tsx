import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ShieldAlert, ServerCog, HardDrive, CheckCircle2 } from "lucide-react";

export default function AssumptionsPage() {
  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2 text-foreground">Implementation Assumptions</h1>
        <p className="text-muted-foreground">
          Context on the missing source brief and the technical decisions made to verify the PDF Report Generator API.
        </p>
      </div>

      <Card className="border-border/60">
        <CardHeader className="bg-muted/20 border-b border-border/40 pb-4">
          <CardTitle className="flex items-center gap-2 text-lg">
            <ShieldAlert className="w-5 h-5 text-amber-500" />
            Unavailable Source Brief
          </CardTitle>
          <CardDescription>
            The original design brief was not provided in the context window.
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6 prose prose-slate dark:prose-invert max-w-none">
          <p>
            Due to the missing brief, I inferred the core purpose of this interface directly from the provided OpenAPI specification and domain requirements. The primary goal is to serve as a robust, technical operations dashboard for managing asynchronous report generation jobs.
          </p>
          <p>
            The design deliberately avoids marketing flair in favor of a high-density, high-trust "Financial/Technical Operations" aesthetic, relying on a crisp slate-and-indigo palette to emphasize clarity and state visibility.
          </p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="border-border/60">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <ServerCog className="w-4 h-4 text-primary" />
              State Management & Polling
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <p>
              The API processes reports asynchronously. To provide a seamless user experience, the interface implements smart polling:
            </p>
            <ul className="list-disc pl-4 space-y-1">
              <li>The main list polls every 2 seconds to capture newly enqueued or completed jobs across the system.</li>
              <li>Individual job rows intelligently increase their polling frequency (1s) when they are in a <code>pending</code> or <code>running</code> state, stopping once a terminal state (<code>completed</code> or <code>failed</code>) is reached.</li>
            </ul>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <HardDrive className="w-4 h-4 text-primary" />
              Artifact Retrieval
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <p>
              PDFs are generated and retained server-side. The download functionality relies on the browser's native Blob handling capabilities. 
            </p>
            <ul className="list-disc pl-4 space-y-1">
              <li>The fetch client correctly requests and receives Blob data.</li>
              <li>Object URLs are temporarily minted in memory to trigger a standard save dialog.</li>
              <li>Object URLs are immediately revoked to prevent memory leaks in long-running tabs.</li>
            </ul>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border/60 bg-primary/5 border-primary/20">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base text-primary">
            <CheckCircle2 className="w-4 h-4" />
            Verification Boundary
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          <p>
            This interface strictly consumes the provided <code>@workspace/api-client-react</code> SDK. No manual <code>fetch</code> calls are made. 
            The source summary data is assumed to represent the true state of the database seeding, and failure simulation explicitly maps to the backend's <code>simulate_failure</code> toggle to verify error handling without requiring actual service degradation.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
