import { cn } from 'cn'
import { useState } from 'react'

import { UIButton } from '../../atoms/UIButton'
import { UISkeleton } from '../../atoms/UISkeleton'
import { UIBox } from '../../atoms/UIBox'

type Props = {
  src?: string | null
  alt: string
  width: number
  height: number
  className?: string
  errorText: string
  retryLabel: string
  onRetry?: () => void
}

/**
 * Imagen remota para URLs prefirmadas: incluye alt obligatorio, dimensiones
 * explícitas para evitar layout shifts, estado de carga con UISkeleton y
 * manejo de error con opción de reintento.
 *
 * @author Pablo Contreras
 * @since 2026/09/30
 * @since 2026/11/19
 */
export function UIRemoteImage({
  src,
  alt,
  width,
  height,
  className,
  errorText,
  retryLabel,
  onRetry,
}: Props): React.JSX.Element {
  const [retryCount, setRetryCount] = useState(0)
  const [failedSrc, setFailedSrc] = useState<string | null | undefined>(null)
  const [loadedSrc, setLoadedSrc] = useState<string | null | undefined>(null)

  const isFailed = src === null || failedSrc === src
  const isLoading =
    (src === undefined || (Boolean(src) && loadedSrc !== src)) && !isFailed

  const handleRetry = (): void => {
    setFailedSrc(null)
    setLoadedSrc(null)
    setRetryCount((c) => c + 1)
    onRetry?.()
  }

  if (isFailed) {
    return (
      <UIBox
        className={cn(
          'flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-input bg-muted/40 p-4 text-center',
          className,
        )}
      >
        <UIBox as="span" className="ui-typography-caption text-destructive">
          {errorText}
        </UIBox>
        <UIButton
          variant="secondary"
          className="min-h-9 px-3 text-xs"
          onClick={handleRetry}
        >
          {retryLabel}
        </UIButton>
      </UIBox>
    )
  }

  return (
    <UIBox className={cn('relative inline-block overflow-hidden', className)}>
      {isLoading ? (
        <UIBox
          data-testid="remote-image-skeleton"
          className="absolute inset-0 size-full"
        >
          <UISkeleton className="size-full" />
        </UIBox>
      ) : null}
      <img
        key={`${src}-${retryCount}`}
        src={src}
        alt={alt}
        width={width}
        height={height}
        onLoad={() => setLoadedSrc(src)}
        onError={() => setFailedSrc(src)}
        className={cn(
          'rounded-xl object-contain transition-opacity duration-200',
          isLoading ? 'opacity-0' : 'opacity-100',
        )}
      />
    </UIBox>
  )
}
