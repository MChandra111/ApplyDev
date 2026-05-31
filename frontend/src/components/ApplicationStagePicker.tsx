import type { ApplicationStage } from '../types/api'
import { APPLICATION_STAGES, STAGE_META } from '../lib/applicationStage'

interface ApplicationStagePickerProps {
  value?: ApplicationStage
  onChange: (stage: ApplicationStage | undefined) => void
  size?: 'sm' | 'md'
}

/** Segmented control for Applied / Interviewing / Hired tags. */
export function ApplicationStagePicker({
  value,
  onChange,
  size = 'md',
}: ApplicationStagePickerProps) {
  const padding = size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-sm'

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div
        className="inline-flex flex-wrap gap-1 rounded-lg border border-border bg-background/80 p-1"
        role="group"
        aria-label="Application stage"
      >
        {APPLICATION_STAGES.map((stage) => {
          const active = value === stage
          const meta = STAGE_META[stage]

          return (
            <button
              key={stage}
              type="button"
              aria-pressed={active}
              onClick={() => onChange(active ? undefined : stage)}
              className={`rounded-md font-medium transition ${padding} ${
                active
                  ? `${meta.tagClass} ring-1`
                  : 'text-muted hover:bg-surface-raised hover:text-foreground'
              }`}
            >
              {meta.label}
            </button>
          )
        })}
      </div>
      {value && size === 'md' && (
        <button
          type="button"
          onClick={() => onChange(undefined)}
          className="text-xs text-muted underline-offset-2 hover:text-foreground hover:underline"
        >
          Clear tag
        </button>
      )}
    </div>
  )
}

/** Compact read-only stage pill for list rows and cards. */
export function ApplicationStageTag({ stage }: { stage: ApplicationStage }) {
  const meta = STAGE_META[stage]

  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${meta.tagClass}`}
    >
      {meta.label}
    </span>
  )
}
