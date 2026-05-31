interface BulletsTabProps {
  bullets?: string[]
}

export function BulletsTab({ bullets }: BulletsTabProps) {
  if (!bullets?.length) {
    return <p className="text-sm text-muted">No resume bullets generated.</p>
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted">
        Tailored bullets you can paste into your resume for this role:
      </p>
      <ul className="space-y-3">
        {bullets.map((bullet, index) => (
          <li
            key={`${index}-${bullet.slice(0, 24)}`}
            className="rounded-lg border border-border bg-surface px-4 py-3 text-sm leading-relaxed text-foreground shadow-sm"
          >
            {bullet}
          </li>
        ))}
      </ul>
    </div>
  )
}
