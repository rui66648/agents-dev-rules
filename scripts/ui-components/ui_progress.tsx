import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const progressVariants = cva(
  "relative h-2 w-full overflow-hidden rounded-full bg-primary/20",
  {
    variants: {
      variant: {
        default: "bg-primary/20",
        secondary: "bg-secondary/20",
        destructive: "bg-destructive/20",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

const progressIndicatorVariants = cva(
  "h-full w-full flex-1 bg-primary transition-all",
  {
    variants: {
      variant: {
        default: "bg-primary",
        secondary: "bg-secondary",
        destructive: "bg-destructive",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface ProgressProps
  extends
    React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof progressVariants> {
  value?: number;
}

const Progress = React.forwardRef<
  React.ElementRef<typeof progressVariants>,
  ProgressProps
>(({ className, variant, value = 0, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(progressVariants({ variant }), className)}
    {...props}
  >
    <div
      className={cn(progressIndicatorVariants({ variant }))}
      style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
    />
  </div>
));
Progress.displayName = progressVariants.displayName;

export { Progress };
