import { API_URL } from '../api/analyze'

export type AppTab = 'analyze' | 'saved' | 'tracker'

interface AppHeaderProps {
  activeTab: AppTab
  onTabChange: (tab: AppTab) => void
  backendOk: boolean | null
  savedCount: number
  trackedCount: number
}

/** Top navigation between the live analyzer and saved job library. */
export function AppHeader({
  activeTab,
  onTabChange,
  backendOk,
  savedCount,
  trackedCount,
}: AppHeaderProps) {
  return (
    <header className="bg-background backdrop-blur">
      <div className="border-b-2 border-accent mx-auto flex max-w-7xl flex-col gap-4 px-4 py-5 sm:px-6 lg:px-10">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">ApplyDev</h1>
            <p className="text-sm text-muted">
              Multi-agent job application research
            </p>
          </div>
          <BackendStatus ok={backendOk} />
        </div>

        <nav className="flex gap-1 rounded-lg border border-border bg-surface p-1 shadow-sm">
          <TabButton
            active={activeTab === 'analyze'}
            onClick={() => onTabChange('analyze')}
            label="Analyze"
          />
          <TabButton
            active={activeTab === 'saved'}
            onClick={() => onTabChange('saved')}
            label="Saved Jobs"
            badge={savedCount > 0 ? String(savedCount) : undefined}
          />
          <TabButton
            active={activeTab === 'tracker'}
            onClick={() => onTabChange('tracker')}
            label="Application Tracker"
            badge={trackedCount > 0 ? String(trackedCount) : undefined}
          />
        </nav>
      </div>
    </header>
  )
}

function TabButton({
  active,
  onClick,
  label,
  badge,
}: {
  active: boolean
  onClick: () => void
  label: string
  badge?: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition ${
        active
          ? 'bg-accent text-on-accent shadow-sm'
          : 'text-muted hover:bg-surface-raised hover:text-foreground'
      }`}
    >
      {label}
      {badge && (
        <span
          className={`rounded-full px-2 py-0.5 text-xs ${
            active ? 'bg-accent-hover/50 text-on-accent' : 'bg-surface-raised text-muted'
          }`}
        >
          {badge}
        </span>
      )}
    </button>
  )
}

function BackendStatus({ ok }: { ok: boolean | null }) {
  const label =
    ok === null ? 'Checking…' : ok ? 'Backend connected' : 'Backend unreachable'
  const color =
    ok === true ? 'text-accent' : ok === false ? 'text-error' : 'text-muted'

  return (
    <div className="text-right text-sm">
      <p className={`font-medium ${color}`}>{label}</p>
      <p className="font-mono text-xs text-muted">{API_URL}</p>
    </div>
  )
}
