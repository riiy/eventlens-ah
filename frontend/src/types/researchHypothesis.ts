export interface ResearchHypothesis {
  id: string;
  event_id: string;
  hypothesis_text: string;
  impact_chain: string[] | null;
  supporting_evidence: string[];
  counter_evidence: string[];
  trigger_conditions: string[];
  invalidation_conditions: string[];
  time_horizon: string;
  risk_notes: string | null;
  model_used: string;
  status: string;
  created_at: string;
}