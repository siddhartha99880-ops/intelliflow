import * as React from "react";

import { cn } from "@/app/lib/cn";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl", className)} {...props} />;
}

