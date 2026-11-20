
/**
 * Avisos (toasts) de shadcn sobre sonner, con el tema de content-studio (`shared/theme`).
 * Lo envuelve `UIToaster`. Parche `shadcn-patch`: variables de color por
 * clase en vez de `style`.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */
import { useTheme } from "@/shared/theme/useTheme"
import { Toaster as Sonner, type ToasterProps } from "sonner"
import { CircleCheckIcon, InfoIcon, TriangleAlertIcon, OctagonXIcon, Loader2Icon } from "lucide-react"

/** Región de avisos con íconos de lucide y colores del sistema de diseño. */
const Toaster = ({ ...props }: ToasterProps) => {
  const [theme] = useTheme()

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      // shadcn-patch: variables de color por clase (sin prop style).
      className="toaster group [--border-radius:var(--radius)] [--normal-bg:var(--popover)] [--normal-border:var(--border)] [--normal-text:var(--popover-foreground)] dark:[--normal-bg:var(--muted)]"
      icons={{
        success: (
          <CircleCheckIcon className="size-4" />
        ),
        info: (
          <InfoIcon className="size-4" />
        ),
        warning: (
          <TriangleAlertIcon className="size-4" />
        ),
        error: (
          <OctagonXIcon className="size-4" />
        ),
        loading: (
          <Loader2Icon className="size-4 animate-spin" />
        ),
      }}
      toastOptions={{
        classNames: {
          toast: "cn-toast bg-popover! text-popover-foreground!",
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
