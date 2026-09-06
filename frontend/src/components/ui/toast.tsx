import { Toast as ToastPrimitive } from "@base-ui/react/toast"
import { XIcon } from "lucide-react"
import { cn } from "cn"

export const ToastProvider = ToastPrimitive.Provider

/** Renders whatever the manager currently holds; mount it once, next to the provider. */
export function Toaster({ className }: { className?: string }) {
  const { toasts } = ToastPrimitive.useToastManager()

  return (
    <ToastPrimitive.Portal>
      <ToastPrimitive.Viewport className={cn("toast-viewport", className)}>
        {toasts.map((toast) => (
          <ToastPrimitive.Root key={toast.id} toast={toast} className="toast" data-type={toast.type}>
            <ToastPrimitive.Title className="toast-title" />
            <ToastPrimitive.Description className="toast-description" />
            <ToastPrimitive.Close className="toast-close" aria-label="Закрыть">
              <XIcon size={14} />
            </ToastPrimitive.Close>
          </ToastPrimitive.Root>
        ))}
      </ToastPrimitive.Viewport>
    </ToastPrimitive.Portal>
  )
}
