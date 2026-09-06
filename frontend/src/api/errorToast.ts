import { Toast } from "@base-ui/react/toast"

import { errorMessage } from "./client"

/** Every failed mutation says so out loud — a row has no room for an inline message. */
export function useErrorToast(): (error: unknown) => void {
  const toasts = Toast.useToastManager()

  return (error: unknown) => {
    toasts.add({ title: errorMessage(error), type: "error", priority: "high" })
  }
}
