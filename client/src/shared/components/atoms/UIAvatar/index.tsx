import { Avatar, AvatarFallback } from '../../shadcn/avatar'

/**
 * Avatar con las iniciales del nombre (máximo dos). Es decorativo: el nombre
 * completo debe mostrarse junto a él.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */
export function UIAvatar({ name }: { name: string }): React.JSX.Element {
  const initials = name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('')
  return (
    <Avatar aria-hidden="true" className="size-10 ring-2 ring-card after:hidden">
      <AvatarFallback className="ui-typography-caption bg-accent font-bold text-accent-foreground">{initials}</AvatarFallback>
    </Avatar>
  )
}
