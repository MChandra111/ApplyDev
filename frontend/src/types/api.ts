/** Mirrors backend PipelineEvent and pipeline state shapes. */

export type StepStatus = 'pending' | 'running' | 'done' | 'error'

export type PipelineNode =
  | 'scrape_jd'
  | 'research_company'
  | 'parse_jd'
  | 'write_bullets'
  | 'write_cover_letter'
  | 'evaluate_opportunity'
  | 'pipeline'

export interface PipelineEvent {
  job_id: string
  node: string
  status: 'running' | 'done' | 'error'
  output?: Record<string, unknown> | null
  error?: string | null
}

export interface ResearchSummary {
  company_name: string
  company_size: string
  recent_news: string[]
  tech_stack_mentions: string[]
  red_flags: string[]
}

export type ExperienceMatchStatus = 'not_specified' | 'meets' | 'short'

export interface SkillExperienceCheck {
  skill: string
  status: ExperienceMatchStatus
  required_min_years?: number | null
  candidate_years?: number | null
  gap_years?: number | null
  raw_text?: string
  summary: string
}

export interface ExperienceMatch {
  status: ExperienceMatchStatus
  required_min_years?: number | null
  candidate_years: number
  gap_years?: number | null
  summary: string
  skill_checks?: SkillExperienceCheck[]
}

export interface OpportunityScore {
  score: number
  fit_summary: string
  growth_summary: string
  red_flags_summary: string
  recommendation: 'apply' | 'maybe' | 'pass' | string
}

export interface PipelineResult {
  job_url?: string
  company_name?: string
  jd_text?: string
  research_summary?: ResearchSummary
  matched_experience?: Record<string, unknown>
  resume_bullets?: string[]
  cover_letter?: string
  opportunity_score?: OpportunityScore
  agent_logs?: string[]
}

export type ApplicationStage = 'applied' | 'interviewing' | 'hired' | 'rejected'

export interface JobHistoryEntry {
  job_id: string
  job_url: string
  company_name?: string
  job_title?: string
  application_stage?: ApplicationStage
  status: 'completed' | 'failed'
  created_at: string
  result?: PipelineResult
  error?: string
}

export interface AnalyzeOptions {
  jdText?: string
  companyName?: string
  signal?: AbortSignal
}
