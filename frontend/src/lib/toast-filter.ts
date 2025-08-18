/**
 * Toast notification filter
 * Only show warnings and errors, suppress success and info messages
 */

import { toast as originalToast } from "@/hooks/use-toast"

type ToastOptions = Parameters<typeof originalToast>[0]

export const toast = (options: ToastOptions) => {
  // Only show warnings and errors
  if (options.variant === "destructive" ||
      options.title?.toLowerCase().includes("error") ||
      options.title?.toLowerCase().includes("warning") ||
      options.title?.toLowerCase().includes("failed") ||
      options.title?.toLowerCase().includes("required") ||
      options.title?.toLowerCase().includes("missing")) {
    return originalToast(options)
  }

  // Suppress success and info toasts
  return {
    id: "",
    dismiss: () => {},
    update: () => {}
  }
}

// Export the original toast for cases where we explicitly need it
export { originalToast }
