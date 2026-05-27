import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/app/lib/cn";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/60 disabled:opacity-60 disabled:pointer-events-none",
  {
    variants: {
      variant: {
        default: "bg-indigo-600 hover:bg-indigo-500 text-white shadow-glow",
        secondary: "bg-white/5 hover:bg-white/10 text-slate-100 border border-white/10",
        ghost: "bg-transparent hover:bg-white/5 text-slate-200",
      },
      size: {
        default: "h-10",
        sm: "h-9 px-3",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof buttonVariants>;

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return <button className={cn(buttonVariants({ variant, size, className }))} {...props} />;
}

