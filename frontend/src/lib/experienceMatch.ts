import type { ExperienceMatch, PipelineResult } from '../types/api'

/** Read YoE comparison from parse_jd output on the pipeline result. */
export function getExperienceMatch(
  result: PipelineResult | null | undefined,
): ExperienceMatch | undefined {
  const raw = result?.matched_experience?.experience_match
  if (!raw || typeof raw !== 'object') return undefined
  const match = raw as ExperienceMatch
  if (!match.status || typeof match.summary !== 'string') return undefined
  return match
}
