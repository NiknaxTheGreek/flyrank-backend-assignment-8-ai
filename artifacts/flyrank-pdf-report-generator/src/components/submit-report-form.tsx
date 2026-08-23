import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useCreateReport, getListReportsQueryKey } from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Plus } from "lucide-react";
import { toast } from "sonner";

const reportSchema = z.object({
  title: z.string().min(3, "Title must be at least 3 characters").max(100, "Title is too long"),
  delay_seconds: z.number().min(0).max(10).default(0),
  simulate_failure: z.boolean().default(false),
});

type ReportFormValues = z.infer<typeof reportSchema>;

export function SubmitReportForm() {
  const queryClient = useQueryClient();
  const createReport = useCreateReport();

  const form = useForm<ReportFormValues>({
    resolver: zodResolver(reportSchema),
    defaultValues: {
      title: "",
      delay_seconds: 0,
      simulate_failure: false,
    },
  });

  function onSubmit(data: ReportFormValues) {
    createReport.mutate(
      { data },
      {
        onSuccess: () => {
          form.reset();
          queryClient.invalidateQueries({ queryKey: getListReportsQueryKey() });
          toast.success("Report job queued successfully", {
            description: "Your report is now pending processing.",
          });
        },
        onError: () => {
          toast.error("Failed to queue report", {
            description: "Please check your network and try again.",
          });
        },
      }
    );
  }

  return (
    <Card className="border-border shadow-sm bg-card/50">
      <CardHeader>
        <CardTitle className="text-lg">Generate Report</CardTitle>
        <CardDescription>
          Submit a new asynchronous report generation job.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Report Title</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g. Q3 Financial Aggregate" {...field} data-testid="input-report-title" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-6">
              <FormField
                control={form.control}
                name="delay_seconds"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Artificial Delay ({field.value}s)</FormLabel>
                    <FormControl>
                      <Slider
                        min={0}
                        max={10}
                        step={1}
                        value={[field.value]}
                        onValueChange={(vals) => field.onChange(vals[0])}
                        className="py-2"
                        data-testid="slider-delay"
                      />
                    </FormControl>
                    <FormDescription>
                      Simulate processing time.
                    </FormDescription>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="simulate_failure"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3 shadow-sm">
                    <div className="space-y-0.5">
                      <FormLabel>Simulate Failure</FormLabel>
                      <FormDescription>
                        Force the job to fail for testing.
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                        data-testid="switch-simulate-failure"
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
            </div>

            <Button 
              type="submit" 
              className="w-full font-medium"
              disabled={createReport.isPending}
              data-testid="button-submit-report"
            >
              {createReport.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Queueing...
                </>
              ) : (
                <>
                  <Plus className="mr-2 h-4 w-4" />
                  Queue Job
                </>
              )}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
