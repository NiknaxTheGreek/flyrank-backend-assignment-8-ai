import { ReactNode } from "react";
import { Link, useLocation } from "wouter";
import { FileText, Info, BarChart2, CheckCircle2 } from "lucide-react";
import { getHealthCheckQueryKey, useHealthCheck } from "@workspace/api-client-react";

export function Layout({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  const { data: health } = useHealthCheck({
    query: { queryKey: getHealthCheckQueryKey(), refetchInterval: 30000 },
  });

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden selection:bg-primary selection:text-primary-foreground">
      <aside className="w-64 border-r bg-card flex flex-col justify-between shrink-0">
        <div>
          <div className="h-16 flex items-center px-6 border-b">
            <div className="flex items-center gap-2 text-primary">
              <BarChart2 className="w-5 h-5" />
              <span className="font-semibold tracking-tight text-foreground">
                Flyrank Reports
              </span>
            </div>
          </div>
          <nav className="p-4 space-y-1">
            <Link href="/" className="block">
              <span
                className={`flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  location === "/"
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
                data-testid="nav-dashboard"
              >
                <FileText className="w-4 h-4" />
                Dashboard
              </span>
            </Link>
            <Link href="/assumptions" className="block">
              <span
                className={`flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  location === "/assumptions"
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
                data-testid="nav-assumptions"
              >
                <Info className="w-4 h-4" />
                Assumptions
              </span>
            </Link>
          </nav>
        </div>
        <div className="p-4 border-t border-border/50">
          <div className="flex items-center gap-2 px-3 py-2 text-xs text-muted-foreground bg-muted/30 rounded-md">
            {health?.status === "ok" ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            ) : (
              <div className="w-3.5 h-3.5 rounded-full bg-destructive animate-pulse" />
            )}
            <span className="font-mono">
              API Status: {health?.status === "ok" ? "Connected" : "Offline"}
            </span>
          </div>
        </div>
      </aside>
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 flex items-center justify-between px-8 border-b bg-background/95 backdrop-blur shrink-0">
          <h1 className="text-sm font-medium text-muted-foreground">
            {location === "/" ? "Overview / Active Jobs" : location === "/assumptions" ? "Documentation / Assumptions" : ""}
          </h1>
        </header>
        <div className="flex-1 overflow-auto p-8">
          <div className="max-w-6xl mx-auto space-y-8">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
