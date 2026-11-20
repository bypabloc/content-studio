import { t } from '@/shared/i18n/t';
import { navItems, type NavItem } from './nav';
import { useSectionId } from './routes';

/** El menú agrupado: un enlace por sección, y la sección activa según el hash. */
export function Sidebar({ items = navItems() }: { items?: readonly NavItem[] }) {
  const active = useSectionId();
  const groups = [...new Set(items.map((item) => item.group))];

  return (
    <nav aria-label={t('nav.label')} className="flex flex-col gap-4">
      {groups.map((group) => (
        <div key={group} className="flex flex-col gap-1">
          <h2 className="px-2 text-xs font-medium uppercase text-muted-foreground">{group}</h2>
          {items
            .filter((item) => item.group === group)
            .map((item) => (
              <a
                key={item.id}
                href={`#/${item.id}`}
                aria-current={item.id === active ? 'page' : undefined}
                className={`rounded-md px-2 py-1.5 text-sm ${item.id === active ? 'bg-accent font-medium' : 'hover:bg-accent/60'}`}
              >
                {item.label}
              </a>
            ))}
        </div>
      ))}
    </nav>
  );
}
