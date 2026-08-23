import { Link } from "wouter";
import { FileQuestion } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-[60vh] text-center space-y-6">
      <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center">
        <FileQuestion className="w-8 h-8 text-muted-foreground" />
      </div>
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">404 - Page Not Found</h1>
        <p className="text-muted-foreground max-w-md mx-auto">
          The view you are looking for does not exist in the reporting application.
        </p>
      </div>
      <Link 
        href="/"
        className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50"
      >
        Return to Dashboard
      </Link>
    </div>
  );
}
