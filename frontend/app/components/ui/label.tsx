import * as React from "react";

import { cn } from "@/app/lib/cn";

export type LabelProps = React.LabelHTMLAttributes<HTMLLabelElement>;

export function Label({ className, ...props }: LabelProps) {
  return <label className={cn("text-sm font-medium text-slate-200", className)} {...props} />;
}

