import { useState } from 'react'
import type { PipelineResult } from '../types/api'
import { ResearchTab } from './tabs/ResearchTab'
import { BulletsTab } from './tabs/BulletsTab'
import { CoverLetterTab } from './tabs/CoverLetterTab'
import { ScoreTab } from './tabs/ScoreTab'

const TABS = [
  { id: 'research', label: 'Research Summary' },
  { id: 'bullets', label: 'Resume Bullets' },
  { id: 'cover', label: 'Cover Letter' },
  { id: 'score', label: 'Opportunity Score' },
] as const

type TabId = (typeof TABS)[number]['id']

interface ResultsPanelProps {
  result: PipelineResult
}

/** Tabbed results view shown after the pipeline completes. */
export function ResultsPanel({ result }: ResultsPanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>('research')

  return (
    <section className="rounded-xl border border-border bg-surface">
      <div className="border-b border-border px-2 pt-2">
        <nav className="flex flex-wrap gap-1" aria-label="Analysis results">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-t-lg px-4 py-2.5 text-sm font-medium transition ${
                activeTab === tab.id
                  ? 'bg-background text-accent'
                  : 'text-muted hover:bg-surface-raised hover:text-foreground'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="p-6">
        {activeTab === 'research' && <ResearchTab research={result.research_summary} />}
        {activeTab === 'bullets' && <BulletsTab bullets={result.resume_bullets} />}
        {activeTab === 'cover' && <CoverLetterTab letter={result.cover_letter} />}
        {activeTab === 'score' && <ScoreTab score={result.opportunity_score} />}
      </div>
    </section>
  )
}
