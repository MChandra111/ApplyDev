import type { ResearchSummary } from '../../types/api'

interface ResearchTabProps {
  research?: ResearchSummary
}

export function ResearchTab({ research }: ResearchTabProps) {
  if (!research) {
    return <EmptyState message="No research summary in this run." />
  }

  return (
    <div className="space-y-6">
      <header>
        <h3 className="text-xl font-semibold text-foreground">{research.company_name}</h3>
        <p className="mt-1 text-sm text-muted">Size: {research.company_size}</p>
      </header>

      <Section title="Recent news" items={research.recent_news} />
      <Section title="Tech stack mentions" items={research.tech_stack_mentions} chip />
      <Section
        title="Red flags"
        items={research.red_flags}
        emptyText="None flagged"
        variant="warning"
      />
    </div>
  )
}

function Section({
  title,
  items,
  emptyText = 'Nothing listed',
  chip = false,
  variant = 'default',
}: {
  title: string
  items: string[]
  emptyText?: string
  chip?: boolean
  variant?: 'default' | 'warning'
}) {
  const hasItems = items.length > 0

  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted">
        {title}
      </h4>
      {!hasItems ? (
        <p className="text-sm text-muted">{emptyText}</p>
      ) : chip ? (
        <div className="flex flex-wrap gap-2">
          {items.map((item) => (
            <span
              key={item}
              className="rounded-full bg-surface-raised px-3 py-1 text-sm text-foreground"
            >
              {item}
            </span>
          ))}
        </div>
      ) : (
        <ul className={`space-y-2 ${variant === 'warning' ? 'text-error' : 'text-foreground/90'}`}>
          {items.map((item) => (
            <li key={item} className="flex gap-2 text-sm leading-relaxed">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-current opacity-60" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function EmptyState({ message }: { message: string }) {
  return <p className="text-sm text-muted">{message}</p>
}
