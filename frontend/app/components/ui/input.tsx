import * as React from "react";

import { cn } from "@/app/lib/cn";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export function Input({ className, ...props }: InputProps) {
  return <input className={cn("h-10 w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/60", className)} {...props} />;
}

