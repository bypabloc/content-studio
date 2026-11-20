
/**
 * Tabla de shadcn (HTML semántico con estilos). La envuelve `UITable`.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */
import * as React from "react"
import { cn } from "cn"

/**
 * Tabla con contenedor de scroll horizontal. Con `containerLabel` el
 * contenedor es una región enfocable: en pantallas angostas se desplaza con
 * el teclado (WCAG 2.1.1, regla axe `scrollable-region-focusable`).
 */
function Table({ className, containerLabel, ...props }: React.ComponentProps<"table"> & { containerLabel?: string }) {
  // shadcn-patch: contenedor enfocable y con nombre accesible cuando hay etiqueta.
  const region = containerLabel ? { role: "region", "aria-label": containerLabel, tabIndex: 0 } : {}
  return (
    <div
      data-slot="table-container"
      className="relative w-full overflow-x-auto focus-visible:ui-focus"
      {...region}
    >
      <table
        data-slot="table"
        className={cn("w-full caption-bottom text-sm", className)}
        {...props}
      />
    </div>
  )
}

/** Encabezado (`thead`). */
function TableHeader({ className, ...props }: React.ComponentProps<"thead">) {
  return (
    <thead
      data-slot="table-header"
      className={cn("[&_tr]:border-b", className)}
      {...props}
    />
  )
}

/** Cuerpo (`tbody`). */
function TableBody({ className, ...props }: React.ComponentProps<"tbody">) {
  return (
    <tbody
      data-slot="table-body"
      className={cn("[&_tr:last-child]:border-0", className)}
      {...props}
    />
  )
}

/** Pie (`tfoot`). */
function TableFooter({ className, ...props }: React.ComponentProps<"tfoot">) {
  return (
    <tfoot
      data-slot="table-footer"
      className={cn(
        "border-t bg-muted/50 font-medium [&>tr]:last:border-b-0",
        className
      )}
      {...props}
    />
  )
}

/** Fila. */
function TableRow({ className, ...props }: React.ComponentProps<"tr">) {
  return (
    <tr
      data-slot="table-row"
      className={cn(
        "border-b transition-colors hover:bg-muted/50 has-aria-expanded:bg-muted/50 data-[state=selected]:bg-muted",
        className
      )}
      {...props}
    />
  )
}

/** Celda de encabezado (`th`). */
function TableHead({ className, ...props }: React.ComponentProps<"th">) {
  return (
    <th
      data-slot="table-head"
      className={cn(
        "h-10 px-2 text-left align-middle font-medium whitespace-nowrap text-foreground [&:has([role=checkbox])]:pr-0",
        className
      )}
      {...props}
    />
  )
}

/** Celda de datos (`td`). */
function TableCell({ className, ...props }: React.ComponentProps<"td">) {
  return (
    <td
      data-slot="table-cell"
      className={cn(
        "p-2 align-middle whitespace-nowrap [&:has([role=checkbox])]:pr-0",
        className
      )}
      {...props}
    />
  )
}

/** Leyenda de la tabla (nombre accesible). */
function TableCaption({
  className,
  ...props
}: React.ComponentProps<"caption">) {
  return (
    <caption
      data-slot="table-caption"
      className={cn("mt-4 text-sm text-muted-foreground", className)}
      {...props}
    />
  )
}

export {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
}
