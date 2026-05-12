export interface MarketEvent {
  id: string;
  raw_document_id: string;
  event_type: string;
  event_summary: string;
  primary_entity: string | null;
  related_entities: string[];
  market_scope: string;
  direction: string;
  materiality_score: number;
  novelty_score: number;
  urgency_score: number;
  credibility_score: number;
  confidence_score: number;
  risk_score: number;
  event_alpha_score: number;
  first_seen_at: string;
  status: string;
  created_at: string;
}

export interface MarketEventListParams {
  offset?: number;
  limit?: number;
  event_type?: string;
  market_scope?: string;
  direction?: string;
  status?: string;
  min_score?: number;
  max_score?: number;
  date_from?: string;
  date_to?: string;
  sort_by?: string;
  sort_order?: string;
}