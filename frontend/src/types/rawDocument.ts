export interface RawDocument {
  id: string;
  source: string;
  source_type: string;
  url: string | null;
  title: string;
  content: string;
  language: string;
  published_at: string | null;
  crawled_at: string | null;
  first_seen_at: string;
  content_hash: string;
  duplicate_group_id: string | null;
  credibility_score: number;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
}

export interface RawDocumentCreate {
  source: string;
  source_type?: string;
  url?: string;
  title: string;
  content: string;
  language?: string;
  published_at?: string;
}

export interface RawDocumentListParams {
  offset?: number;
  limit?: number;
  source?: string;
  date_from?: string;
  date_to?: string;
}