interface JobActionButtonsProps {
  isSaved: boolean
  isTracked: boolean
  disabled?: boolean
  onSaveJob: () => void
  onMarkApplied: () => void
}

/** Save analysis for later, or mark as submitted and open the Application Tracker. */
export function JobActionButtons({
  isSaved,
  isTracked,
  disabled,
  onSaveJob,
  onMarkApplied,
}: JobActionButtonsProps) {
  return (
    <div className="rounded-xl border border-border bg-surface px-5 py-4 shadow-sm">
      <p className="text-sm font-medium text-foreground">Save this analysis</p>
      <p className="mt-0.5 text-xs text-muted">
        Save to revisit bullets before applying, or mark as applied to track in your pipeline.
      </p>
      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onSaveJob}
          disabled={disabled}
          className="inline-flex items-center gap-2 rounded-lg border border-border bg-surface-raised px-4 py-2.5 text-sm font-semibold text-foreground transition hover:bg-surface disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSaved && !isTracked ? (
            <>
              <CheckIcon className="h-4 w-4 text-accent" />
              Saved
            </>
          ) : (
            'Save job'
          )}
        </button>
        <button
          type="button"
          onClick={onMarkApplied}
          disabled={disabled || isTracked}
          className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-on-accent transition hover:bg-accent-hover disabled:cursor-default disabled:opacity-60"
        >
          {isTracked ? (
            <>
              <CheckIcon className="h-4 w-4" />
              In tracker
            </>
          ) : (
            'I applied'
          )}
        </button>
      </div>
    </div>
  )
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="currentColor" aria-hidden>
      <path
        fillRule="evenodd"
        d="M16.704 5.29a1 1 0 010 1.42l-7.25 7.25a1 1 0 01-1.42 0l-3.25-3.25a1 1 0 111.42-1.42l2.54 2.54 6.54-6.54a1 1 0 011.42 0z"
        clipRule="evenodd"
      />
    </svg>
  )
}
