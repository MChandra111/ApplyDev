export const PIPELINE_STEPS = [
  { id: 'scrape_jd', label: 'Scrape job posting' },
  { id: 'research_company', label: 'Research company', parallel: true },
  { id: 'parse_jd', label: 'Parse JD & match resume', parallel: true },
  { id: 'write_bullets', label: 'Write resume bullets' },
  { id: 'write_cover_letter', label: 'Draft cover letter' },
  { id: 'evaluate_opportunity', label: 'Score opportunity' },
] as const

export type TrackedStepId = (typeof PIPELINE_STEPS)[number]['id']

export const INITIAL_STEP_STATE = Object.fromEntries(
  PIPELINE_STEPS.map((step) => [step.id, 'pending']),
) as Record<TrackedStepId, import('../types/api').StepStatus>
