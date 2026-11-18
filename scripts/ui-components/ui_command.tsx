import * as React from "react";
import { ChevronDown, ChevronsUpDown, X } from "lucide-react";
import * as Command from "cmdk";
import { cn } from "@/lib/utils";

const CommandList = React.forwardRef<
  React.ElementRef<typeof Command.List>,
  React.ComponentPropsWithoutRef<typeof Command.List>
>(({ className, ...props }, ref) => (
  <Command.List
    ref={ref}
    className={cn("max-h-[300px] overflow-y-auto overflow-x-hidden", className)}
    {...props}
  />
));
CommandList.displayName = Command.List.displayName;

const CommandEmpty = React.forwardRef<
  React.ElementRef<typeof Command.Empty>,
  React.ComponentPropsWithoutRef<typeof Command.Empty>
>(({ className, ...props }, ref) => (
  <Command.Empty
    ref={ref}
    className={cn("py-6 text-center text-sm", className)}
    {...props}
  />
));
CommandEmpty.displayName = Command.Empty.displayName;

const CommandGroup = React.forwardRef<
  React.ElementRef<typeof Command.Group>,
  React.ComponentPropsWithoutRef<typeof Command.Group>
>(({ className, ...props }, ref) => (
  <Command.Group
    ref={ref}
    className={cn(
      "overflow-hidden p-1 text-foreground [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground",
      className,
    )}
    {...props}
  />
));
CommandGroup.displayName = Command.Group.displayName;

const CommandSeparator = React.forwardRef<
  React.ElementRef<typeof Command.Separator>,
  React.ComponentPropsWithoutRef<typeof Command.Separator>
>(({ className, ...props }, ref) => (
  <Command.Separator
    ref={ref}
    className={cn("-mx-1 h-px bg-border", className)}
    {...props}
  />
));
CommandSeparator.displayName = Command.Separator.displayName;

const CommandItem = React.forwardRef<
  React.ElementRef<typeof Command.Item>,
  React.ComponentPropsWithoutRef<typeof Command.Item>
>(({ className, ...props }, ref) => (
  <Command.Item
    ref={ref}
    className={cn(
      "relative flex cursor-default gap-2 select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none data-[disabled=true]:pointer-events-none data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground data-[disabled=true]:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
      className,
    )}
    {...props}
  />
));
CommandItem.displayName = Command.Item.displayName;

const CommandShortcut = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement>) => {
  return (
    <span
      className={cn(
        "ml-auto text-xs tracking-widest text-muted-foreground",
        className,
      )}
      {...props}
    />
  );
};
CommandShortcut.displayName = "CommandShortcut";

const Command = React.forwardRef<
  React.ElementRef<typeof Command.Root>,
  React.ComponentPropsWithoutRef<typeof Command.Root>
>(({ className, ...props }, ref) => {
  return (
    <Command.Root
      ref={ref}
      className={cn(
        "flex h-full w-full flex-col overflow-hidden rounded-md bg-popover text-popover-foreground",
        className,
      )}
      {...props}
    />
  );
});
Command.displayName = Command.Root.displayName;

const CommandInput = React.forwardRef<
  React.ElementRef<typeof Command.Input>,
  React.ComponentPropsWithoutRef<typeof Command.Input>
>(({ className, ...props }, ref) => (
  <div className="flex items-center border-b px-3" cmdk-input-wrapper="">
    <ChevronsUpDown className="mr-2 h-4 w-4 shrink-0 opacity-50" />
    <Command.Input
      ref={ref}
      className={cn(
        "flex h-10 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  </div>
));
CommandInput.displayName = Command.Input.displayName;

const CommandDialog = ({
  children,
  ...props
}: {
  children: React.ReactNode;
}) => {
  return (
    <Command {...props}>
      <div className="fixed inset-0 z-50 flex items-start justify-center sm:items-center p-4">
        <div className="fixed inset-0 bg-black/80" />
        <div className="relative z-50 w-full max-w-lg bg-background rounded-lg shadow-2xl overflow-hidden">
          {children}
        </div>
      </div>
    </Command>
  );
};

export {
  Command,
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandShortcut,
  CommandSeparator,
};
