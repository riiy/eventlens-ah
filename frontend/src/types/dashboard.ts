export interface DashboardSummary {
  total_documents: number;
  total_events: number;
  high_score_events: number;
  pending_events: number;
  event_type_distribution: Record<string, number>;
}

export interface TopEventItem {
  id: string;
  event_type: string;
  event_summary: string;
  market_scope: string;
  direction: string;
  event_alpha_score: number;
  created_at: string;
}

export interface RecentDocumentItem {
  id: string;
  source: string;
  title: string;
  published_at: string | null;
  crawled_at: string | null;
}