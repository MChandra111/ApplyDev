interface CoverLetterTabProps {
  letter?: string
}

export function CoverLetterTab({ letter }: CoverLetterTabProps) {
  if (!letter?.trim()) {
    return <p className="text-sm text-muted">No cover letter generated.</p>
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted">Draft cover letter — edit before sending.</p>
      <div className="whitespace-pre-wrap rounded-lg border border-border bg-surface px-5 py-4 text-sm leading-7 text-foreground shadow-sm">
        {letter}
      </div>
    </div>
  )
}
